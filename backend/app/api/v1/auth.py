from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi import Cookie
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_db
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMe

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/api/v1/auth",
    )


def _issue_tokens(db: Session, response: Response, user: User) -> TokenResponse:
    """Emite un access token y un refresh token nuevo, fijando la cookie."""
    # Multi-dispositivo: si el usuario no lo permite, revoca sus sesiones anteriores.
    if not user.allow_multi_device:
        existing = db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
            )
        ).all()
        for rt in existing:
            rt.revoked_at = datetime.now(UTC)

    raw = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw),
            expires_at=refresh_token_expiry(),
        )
    )
    db.commit()

    _set_refresh_cookie(response, raw)
    return TokenResponse(
        access_token=create_access_token(
            subject=str(user.id), tenant_id=user.tenant_id, role=user.role
        ),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalars(select(User).where(User.username == body.username)).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cuenta desactivada")
    return _issue_tokens(db, response, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> TokenResponse:
    if refresh_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sin refresh token")

    rt = db.scalars(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token))
    ).first()
    if rt is None or rt.revoked_at is not None or rt.expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido o expirado")

    user = db.get(User, rt.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inexistente o inactivo")

    # Rotación: invalida el token usado y emite uno nuevo.
    rt.revoked_at = datetime.now(UTC)
    rt.last_used_at = datetime.now(UTC)
    return _issue_tokens(db, response, user)


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> dict:
    if refresh_token is not None:
        rt = db.scalars(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token))
        ).first()
        if rt is not None and rt.revoked_at is None:
            rt.revoked_at = datetime.now(UTC)
            db.commit()
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    return {"detail": "Sesión cerrada"}


@router.get("/me", response_model=UserMe)
def me(current: User = Depends(get_current_user)) -> UserMe:
    return UserMe(
        id=current.id,
        username=current.username,
        role=current.role,
        tenant_id=current.tenant_id,
        tenant_name=current.tenant.name,
        allow_multi_device=current.allow_multi_device,
    )

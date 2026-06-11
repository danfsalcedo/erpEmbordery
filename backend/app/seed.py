"""Seed idempotente: crea el tenant inicial y un usuario dueño si aún no existen.

Se ejecuta en cada arranque (entrypoint). Si ya existen, no hace nada.
"""

from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User


def run() -> None:
    db = SessionLocal()
    try:
        tenant = db.scalars(select(Tenant)).first()
        if tenant is None:
            tenant = Tenant(name=settings.seed_tenant_name, base_currency="COP", locale="es-CO")
            db.add(tenant)
            db.flush()
            print(f"[seed] Tenant creado: {tenant.name} (id={tenant.id})")
        else:
            print(f"[seed] Tenant ya existe: {tenant.name} (id={tenant.id})")

        owner = db.scalars(
            select(User).where(User.username == settings.seed_owner_username)
        ).first()
        if owner is None:
            owner = User(
                tenant_id=tenant.id,
                username=settings.seed_owner_username,
                email=None,
                password_hash=hash_password(settings.seed_owner_password),
                role="owner",
                is_active=True,
                allow_multi_device=True,  # el dueño puede tener varias sesiones
            )
            db.add(owner)
            print(f"[seed] Usuario dueño creado: {owner.username}")
        else:
            print(f"[seed] Usuario dueño ya existe: {owner.username}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()

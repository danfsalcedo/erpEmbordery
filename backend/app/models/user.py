from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class User(Base):
    """Usuario del sistema. Roles: admin | owner | operator."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)

    username: Mapped[str] = mapped_column(String(60))
    email: Mapped[str | None] = mapped_column(String(180), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="operator")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Solo el dueño puede tener varias sesiones activas a la vez
    allow_multi_device: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    tenant: Mapped["Tenant"] = relationship()  # noqa: F821

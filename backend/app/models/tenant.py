from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Tenant(Base):
    """Empresa-inquilino. En Fase 1 hay un solo tenant; el modelo ya soporta varios."""

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    base_currency: Mapped[str] = mapped_column(String(3), default="COP")
    locale: Mapped[str] = mapped_column(String(10), default="es-CO")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

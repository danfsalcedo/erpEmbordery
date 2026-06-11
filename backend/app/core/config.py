from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación, leída de variables de entorno (.env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos
    database_url: str = "postgresql+psycopg://erp:erp_dev_password@db:5432/erp_bordados"

    # Seguridad / JWT
    secret_key: str = "dev-secret-change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14

    # Multi-tenant: single | shared
    tenant_mode: str = "single"

    # Seed inicial (solo desarrollo)
    seed_tenant_name: str = "Bordados Familia"
    seed_owner_username: str = "dueno"
    seed_owner_password: str = "cambiar123"

    # CORS — orígenes permitidos del frontend
    cors_origins: list[str] = ["http://localhost:5173"]

    # Cookie del refresh token. En producción (HTTPS) debe ser True.
    cookie_secure: bool = False


settings = Settings()

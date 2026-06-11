# Backend — ERP Bordados

API REST en **FastAPI** (monolito modular). Se comunica con el frontend solo por HTTP/JSON.
El "por qué" de cada decisión está en
[`../docs/arquitectura-tecnica.md`](../docs/arquitectura-tecnica.md).

## Cómo correr

Lo normal es levantarlo con el stack completo desde la raíz:

```bash
docker compose up -d        # db + backend + frontend
```

- API: http://localhost:8000
- Docs OpenAPI (Swagger): http://localhost:8000/docs

Al arrancar, el contenedor aplica migraciones (`alembic upgrade head`) y corre el seed
idempotente. Ver `entrypoint.sh`.

## Estructura

```
backend/
├── app/
│   ├── main.py            # crea la app FastAPI, CORS, routers, /health
│   ├── core/
│   │   ├── config.py      # settings desde .env (pydantic-settings)
│   │   ├── db.py          # engine, SessionLocal, Base, get_db
│   │   └── security.py    # hash de contraseñas (bcrypt) y tokens (JWT + refresh)
│   ├── models/            # tablas SQLAlchemy (tenants, users, refresh_tokens, …)
│   ├── schemas/           # modelos Pydantic de entrada/salida
│   ├── api/
│   │   ├── deps.py        # dependencias (usuario actual desde el token)
│   │   └── v1/            # routers por módulo (auth, …)
│   └── seed.py            # tenant + usuario inicial (idempotente)
├── alembic/               # migraciones de esquema
└── pyproject.toml         # dependencias y config de herramientas
```

## Migraciones (Alembic)

```bash
# Generar una migración tras cambiar modelos
docker compose run --rm backend alembic revision --autogenerate -m "descripcion"
# Aplicar (también ocurre solo al arrancar)
docker compose run --rm backend alembic upgrade head
```

## Convenciones

- Gestor de paquetes Python: `uv` en Docker. Dinero siempre `NUMERIC`, nunca `float`.
- Toda tabla lleva `tenant_id` (ver multi-tenant en el doc de arquitectura).
- Commits: ver [`../CONTRIBUTING.md`](../CONTRIBUTING.md). Scope backend: `model`, `migration`,
  `api`, `auth`, `core`, `seed`, `service`.

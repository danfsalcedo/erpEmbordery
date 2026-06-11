# ERP Bordados

Plataforma de gestión para empresa de bordados. Monorepo con backend (FastAPI) y
frontend (React PWA) que se comunican por API REST. Ver
[`docs/arquitectura-tecnica.md`](docs/arquitectura-tecnica.md) para la arquitectura completa
y [`docs/roadmap.md`](docs/roadmap.md) para la hoja de ruta por fases.

## Estructura

```
erpEmbordery/
├── docker-compose.yml      # db + backend + frontend
├── docs/                   # documentación (roadmap, arquitectura, specs por fase)
│   ├── roadmap.md
│   ├── arquitectura-tecnica.md
│   └── fase-1/             # specs de módulos de la Fase 1
├── backend/                # FastAPI + SQLAlchemy + Alembic (monolito modular)
└── frontend/               # Vite + React + Tailwind + PWA
```

Front y back son **independientes en ejecución** (dos contenedores que hablan por HTTP);
viven en el mismo repo por comodidad (monorepo). El backend es un **monolito modular**.

## Requisitos

- Docker + Docker Compose
- (Para desarrollo fuera de Docker) Python 3.12, Node 22, **pnpm** (no npm)

## Puesta en marcha (desarrollo)

Backend + base de datos en Docker; frontend nativo con `pnpm dev` (HMR más rápido).

```bash
cp .env.example .env             # ajusta secretos si quieres
docker compose up -d --build     # levanta SOLO db + backend

cd frontend
pnpm install                     # la 1ª vez: si pnpm bloquea esbuild, corre `pnpm approve-builds`
pnpm dev                         # frontend en http://localhost:5173
```

- Frontend (dev): http://localhost:5173
- Backend (API + docs OpenAPI): http://localhost:8000/docs
- El backend corre migraciones (Alembic) y el seed inicial al arrancar.

Usuario inicial de prueba (definido en `.env`): `dueno` / `cambiar123`.

### Prueba integrada en contenedor (opcional)

Para levantar también el frontend en Docker (dev server en contenedor):

```bash
docker compose --profile full up --build
```

> En producción el frontend **no** usa el dev server: se compila (`vite build`) y se
> sirve como estático con Nginx. Esa imagen se añade en el hito de despliegue.

## Hito actual

Hito 1 — Andamiaje: stack vivo con login → JWT → página protegida (`/auth/me`).

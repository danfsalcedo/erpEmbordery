#!/usr/bin/env bash
set -e

echo "==> Esperando a la base de datos..."
# La dependencia service_healthy de compose ya garantiza que Postgres responde,
# pero corremos migraciones de forma idempotente por si acaso.

echo "==> Aplicando migraciones (alembic upgrade head)..."
alembic upgrade head

echo "==> Ejecutando seed inicial (idempotente)..."
python -m app.seed

echo "==> Arrancando Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# uv: instalador de paquetes rápido y reproducible (equivalente moderno de pip)
COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /bin/uv

WORKDIR /app

# Instala solo las dependencias primero (capa cacheable: no se reconstruye si cambia el código)
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

# El código se monta como volumen en desarrollo; se copia para builds de producción
COPY . .

RUN chmod +x ./entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]

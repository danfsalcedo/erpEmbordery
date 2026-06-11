FROM node:22-slim

# Habilita pnpm vía corepack (NO se usa npm en este proyecto)
RUN corepack enable && corepack prepare pnpm@11.1.1 --activate

WORKDIR /app

# Instala dependencias primero (capa cacheable).
# pnpm 11 bloquea los scripts de build por seguridad; instalamos sin scripts y luego
# reconstruimos explícitamente los binarios nativos (esbuild, etc.) de forma determinista.
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --ignore-scripts
RUN pnpm rebuild

COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0"]

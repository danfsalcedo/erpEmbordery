FROM node:22-slim

# Habilita pnpm vía corepack (NO se usa npm en este proyecto)
RUN corepack enable && corepack prepare pnpm@11.1.1 --activate

WORKDIR /app

# Instala dependencias (capa cacheable). pnpm-workspace.yaml lleva la aprobación del
# build-script de esbuild (allowBuilds), así que pnpm instala normalmente sin bloquearse.
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 5173

# Se invoca Vite directamente (no `pnpm dev`) para que pnpm no verifique/reinstale
# dependencias al arrancar; ya vienen listas en la imagen.
CMD ["node_modules/.bin/vite", "--host", "0.0.0.0", "--port", "5173"]

# Frontend — ERP Bordados

PWA en **Vite + React + TypeScript**, estilos con **Tailwind CSS**, estado con **Zustand**.
Consume el backend solo por HTTP/JSON. El "por qué" de cada decisión está en
[`../docs/arquitectura-tecnica.md`](../docs/arquitectura-tecnica.md).

> **Gestor de paquetes: pnpm, nunca npm.** Si escribes `npm`, un alias lo redirige a pnpm.

## Cómo correr

En desarrollo el frontend se corre **nativo con `pnpm dev`** (HMR más rápido que en
Docker, que en Windows requiere polling). El backend y la base de datos sí van en Docker.

```bash
# 1) Desde la raíz: levanta solo db + backend
docker compose up -d

# 2) En esta carpeta: frontend nativo
pnpm install     # 1ª vez: si pnpm bloquea esbuild, corre `pnpm approve-builds`
pnpm dev         # http://localhost:5173
```

### En Docker (opcional, prueba integrada)

```bash
docker compose --profile full up --build   # incluye el dev server del front en contenedor
```

> En producción el front se compila (`vite build`) y se sirve estático con Nginx,
> no con el dev server. Esa imagen se añade en el hito de despliegue.

## Estructura

```
frontend/
├── index.html
├── src/
│   ├── main.tsx           # punto de entrada, monta <App/>
│   ├── App.tsx            # enruta: sin sesión → Login, con sesión → Home
│   ├── index.css          # @import "tailwindcss"
│   ├── lib/
│   │   └── api.ts         # cliente del backend (login, getMe, logout)
│   ├── stores/
│   │   └── auth.ts        # estado de sesión (access token en memoria)
│   └── pages/
│       ├── Login.tsx      # formulario de login
│       └── Home.tsx       # página protegida (consume /auth/me)
├── vite.config.ts         # plugins: react, tailwindcss, PWA
└── package.json
```

## Notas

- El **access token** vive en memoria (Zustand); el **refresh token** va en cookie HttpOnly
  gestionada por el backend (no accesible por JS).
- `VITE_API_URL` define la URL del backend (en Docker: `http://localhost:8000`).
- Commits: ver [`../CONTRIBUTING.md`](../CONTRIBUTING.md). Scope frontend: `ui`, `store`,
  `api-client`, `pwa`, `routing`, `styles`.

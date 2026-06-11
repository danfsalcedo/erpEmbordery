# Frontend — ERP Bordados

PWA en **Vite + React + TypeScript**, estilos con **Tailwind CSS**, estado con **Zustand**.
Consume el backend solo por HTTP/JSON. El "por qué" de cada decisión está en
[`../docs/arquitectura-tecnica.md`](../docs/arquitectura-tecnica.md).

> **Gestor de paquetes: pnpm, nunca npm.** Si escribes `npm`, un alias lo redirige a pnpm.

## Cómo correr

Lo normal es levantarlo con el stack completo desde la raíz:

```bash
docker compose up -d        # db + backend + frontend
```

- App: http://localhost:5173

Fuera de Docker (desarrollo local directo):

```bash
pnpm install
pnpm dev
```

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

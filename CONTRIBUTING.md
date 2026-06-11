# Convenciones de contribución — ERP Bordados

Reglas para mantener el historial limpio y permitir **separar backend y frontend en repos
distintos sin dolor** el día que crezcan. Aplican desde el primer commit.

---

## 1. Regla de oro: un commit = un solo lado

La migración futura (`git filter-repo --path backend/`, `git subtree split`) corta el
historial por **rutas de archivos**. Por eso:

> **Ningún commit mezcla `backend/` y `frontend/`.** Si un cambio toca ambos lados, se parte
> en dos commits ordenados: primero el backend (el contrato), luego el frontend (quien lo consume).

Los archivos de raíz/compartidos (`docker-compose.yml`, `.env.example`, docs, CI) van en sus
propios commits con scope `infra`, `compose`, `ci` o `docs`.

---

## 2. Mensajes — Conventional Commits

Formato:

```
<tipo>(<scope>): <resumen en imperativo, minúscula, sin punto final>

<cuerpo: QUÉ se hizo y POR QUÉ. Decisiones notables. Pendientes si los hay.>
```

**Tipos:** `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `build`, `ci`

**Scopes por lado** (el scope ya delata el lado):

| Lado | Scopes |
|---|---|
| Backend | `model`, `migration`, `api`, `auth`, `core`, `seed`, `service` |
| Frontend | `ui`, `store`, `api-client`, `pwa`, `routing`, `styles` |
| Raíz / compartido | `infra`, `compose`, `deps`, `ci`, `docs` |

El cuerpo es **obligatorio** salvo en cambios triviales: explica en profundidad, no repitas el
resumen. Ejemplo:

```
feat(model): add required phone field to clients table

El teléfono es obligatorio desde Fase 1 porque la automatización de WhatsApp de Fase 2
no puede operar sin él. Se añade como NOT NULL en la tabla clients y se crea la migración
correspondiente. No se permite registrar un cliente sin este campo.
```

```
feat(ui): add phone input to client registration form

Campo de teléfono obligatorio en el formulario de alta de cliente, validado en cliente
con el mismo criterio que el backend (no vacío). Muestra error inline si falta.
Consume el contrato definido en feat(model): add required phone field.
```

---

## 3. Ramas y PRs

- Trabajo en **ramas de feature**, nunca commits directos a `main`.
- Nomenclatura: `feat/<feature>`, `fix/<feature>`, `chore/<asunto>` (ej. `feat/client-phone`).
  **No se marca el lado en el nombre de la rama:** el lado ya se infiere de cada commit
  (regla §1, que es lo que importa para migrar), y una rama puede contener commits de ambos
  lados como commits separados.
- Se integra a `main` vía **Pull Request**. `main` siempre desplegable.

---

## 4. Documentación — tres capas, sin duplicar

| Capa | Dónde | Responde |
|---|---|---|
| Cómo correr / dónde vive cada cosa | `backend/README.md`, `frontend/README.md` | "¿cómo lo levanto y dónde están las cosas?" |
| Por qué se eligió cada tecnología | `docs/arquitectura-tecnica.md` | "¿por qué FastAPI, por qué Zustand?" |
| Qué hace cada función | Docstrings en el código | "¿qué hace este endpoint?" |

Los README **enlazan** al doc de arquitectura en vez de copiarlo. Documentar función por
función en un README está prohibido (crece sin control y se desactualiza): eso va en docstrings.

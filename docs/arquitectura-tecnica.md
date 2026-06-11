# Arquitectura Técnica — ERP Bordados (Fase 1)

> Documento de referencia consolidado. Reúne todas las decisiones tomadas en las
> sesiones de definición (respuestas V1 y V2) y las convierte en especificaciones
> concretas: stack, despliegue, modelo de datos, autenticación, reglas de negocio
> codificadas, API, moneda, offline, CI/CD y backups.
>
> Regla rectora del proyecto: **no dejar nada al azar**. Donde una decisión todavía
> requiere confirmación del dueño, está marcada en la sección final *Puntos a confirmar*.

---

## 0. Conceptos explicados (lo que se pidió aclarar "de una vez")

Antes de la arquitectura, se resuelven los términos que quedaron como duda en las respuestas.

### Tenant (multi-tenant)
Un **tenant** es una empresa-inquilino dentro del sistema. Multi-tenant significa que una
sola base de datos y un solo backend atienden a varias empresas, con sus datos **aislados**
entre sí mediante una columna `tenant_id` presente en todas las tablas.

En Fase 1 solo existe **un tenant** (esta empresa). Pero como cada tabla ya nace con
`tenant_id`, cuando en Fase 3 entren más empresas no hay que rediseñar ni migrar nada:
se inserta un nuevo tenant y sus filas simplemente llevan otro `tenant_id`. Toda consulta
filtra siempre por `tenant_id`, así que una empresa nunca ve datos de otra.

### Refresh token (vs access token)
Son **dos tokens** con propósitos distintos:

- **Access token (JWT):** vida corta (15 min). Acompaña cada petición a la API y prueba
  quién eres. Si se filtra, expira solo en minutos.
- **Refresh token:** vida larga (14 días). No se usa para pedir datos; solo sirve para
  **obtener un access token nuevo** cuando el anterior expira, sin volver a pedir
  contraseña. Se guarda como hash en la base de datos y puede revocarse (logout, cuenta
  comprometida).

Resultado: la sesión "dura 2 semanas" (lo solicitado) pero las credenciales que viajan en
cada petición se renuevan cada 15 minutos. Larga comodidad + corta exposición.

### Read replica (réplica de lectura)
Una copia de la base de datos que solo atiende lecturas, para repartir carga cuando hay
mucho tráfico. **No se usa en Fase 1**: 150–200 producciones/mes no generan carga que lo
justifique. Es una optimización de escala que se evalúa en Fase 3 si llega a hacer falta.

### CI/CD
- **CI (Integración Continua):** cada vez que subes código, un robot corre las pruebas y
  construye la app automáticamente. Si algo se rompe, te avisa antes de desplegar.
- **CD (Despliegue Continuo):** si las pruebas pasan, ese mismo robot publica la versión
  nueva en el servidor sin que tengas que hacerlo a mano.

Herramienta elegida: **GitHub Actions** (ver §11).

---

## 1. Decisiones consolidadas (tabla maestra)

| Tema | Decisión final |
|---|---|
| Tipo de app | PWA (instalable, una base para móvil y escritorio) |
| Frontend | **Vite + React (SPA, sin SSR)** |
| Estilos | **Tailwind CSS** |
| Estado global | **Zustand** |
| Backend | **Python + FastAPI** |
| Base de datos | **PostgreSQL** |
| ORM | **SQLAlchemy** |
| Migraciones | **Alembic** |
| Multi-tenant | `tenant_id` en todas las tablas + **RLS** desde el inicio |
| Modelo de despliegue | Código multi-tenant-capaz; `TENANT_MODE=single` por cliente → SaaS al madurar (ver §3) |
| Read replica | No en Fase 1 |
| Auth | **JWT (15 min) + refresh token (14 días)** |
| Multi-dispositivo | Solo el dueño |
| Reset de contraseña | Lo hace el admin desde la app, sin email |
| Roles | admin, dueño, operador |
| Despliegue | **Railway + Cloudflare Access** (cloud cerrado) |
| Contenedores | **Docker desde el inicio** |
| CI/CD | **GitHub Actions** |
| Backups | **`pg_dump` diario → almacenamiento externo (Backblaze B2)** |
| Moneda base | **COP** (se guarda siempre en COP) |
| Conversión USD | Solo visual, tasa auto-actualizada con fallback |
| Formato fecha | DD/MM/YYYY |
| Separador miles | Punto (`$1.250.000`) |
| Offline | **Bloqueo total + banner** |
| Exportación | **Excel (.xlsx)** |
| Cierre de período | Reversible solo vía override del dueño con recálculo |
| V/U | Editable manualmente sobre el sugerido del catálogo |
| Migración Excel | No en Fase 1, se empieza desde cero |

---

## 2. Stack tecnológico — justificación

### Frontend: Vite + React (SPA) — sin SSR
El SSR (Server-Side Rendering, estilo Next.js) sirve para SEO y primera carga rápida en
sitios públicos. Este ERP es **interno, detrás de login, sin SEO**: el SSR solo añadiría
complejidad de servidor sin beneficio. Una SPA con Vite es más simple, más rápida de
desarrollar y encaja perfecto con la PWA.

- **Build/dev:** Vite (HMR instantáneo, build optimizado)
- **Router:** React Router
- **Estado servidor:** TanStack Query (cache de datos del API, reintentos, invalidación)
- **Estado UI global:** Zustand (sesión, moneda activa, estado de conexión)
- **Estilos:** Tailwind CSS
- **Gráficas:** Recharts (dashboard del dueño)
- **Tablas:** TanStack Table (datos detallados, ordenamiento, filtros)
- **Formularios:** React Hook Form + Zod (validación en cliente, espejo de la del backend)
- **PWA:** `vite-plugin-pwa` (service worker, instalable, detección de offline)
- **Excel:** generación en backend (ver §9), el front solo descarga

### Backend: Python + FastAPI
Decisión estratégica ya tomada en los docs base: en Fase 2 el ML (scikit-learn / Prophet)
se importa como librería **dentro del mismo proyecto**, sin microservicios. FastAPI aporta
tipado, validación con Pydantic y documentación OpenAPI automática.

- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.x (estilo declarativo + tipado)
- **Migraciones:** Alembic
- **Validación:** Pydantic v2
- **Auth:** `python-jose` (JWT) + `passlib[bcrypt]` (hash de contraseñas)
- **Tareas programadas:** APScheduler (tasa de cambio horaria, backup diario)
- **Excel:** `openpyxl`
- **Servidor:** Uvicorn

### Base de datos: PostgreSQL
Relacional, robusto para agregaciones financieras, soporta `NUMERIC` exacto (crítico para
dinero — nunca `float`), y escala a multi-tenant sin reemplazo.

---

## 3. Arquitectura de despliegue

### El dilema planteado y su solución
Se quería un sistema **cerrado** (que un externo que encuentre la URL no pueda entrar) y se
temía perder datos por cortes de luz si corría en una PC local. Un servidor físico dedicado
resuelve la luz pero complica el acceso seguro y el mantenimiento.

**Solución: Railway (cloud) + Cloudflare Access por delante.**

- **Railway** corre los contenedores Docker y el PostgreSQL gestionado. Sin cortes de luz,
  sin mantener hardware, con backups del propio Postgres + los nuestros externos. Gratis al
  inicio, escala pagando solo lo usado.
- **Cloudflare Access (Zero Trust)** se pone delante de la app: nadie llega al login sin
  pasar primero por una compuerta de Cloudflare que solo admite a las personas autorizadas
  (lista de correos de la empresa). Quien encuentre la URL ni siquiera ve la pantalla de
  inicio — Cloudflare lo bloquea antes. Esto da el "sistema cerrado" pedido **sin** servidor
  físico.

```
Usuario autorizado ──► Cloudflare Access (compuerta) ──► Railway
                          │                                ├── Frontend (PWA, contenedor)
                          │ rechaza a todo el que           ├── Backend FastAPI (contenedor)
                          │ no esté en la lista             └── PostgreSQL (gestionado)
                          ▼
                       Externo ✗ (nunca ve el login)
```

### Docker desde el inicio
Tres servicios orquestados con `docker-compose` en desarrollo, replicados en Railway:

```
docker-compose.yml
├── frontend   (Node build → Nginx sirviendo la PWA)
├── backend    (Python FastAPI + Uvicorn)
└── db         (PostgreSQL 16)   ← en Railway es el Postgres gestionado
```

Beneficio: el entorno de tu máquina y el de producción son idénticos. "En mi máquina
funciona" deja de ser un problema.

### Capas de seguridad de acceso
1. **Cloudflare Access** — compuerta de identidad antes de la app.
2. **HTTPS obligatorio** — todo cifrado, sin excepción (Railway + Cloudflare lo dan).
3. **Sin endpoint de registro público** — las cuentas solo las crea el admin.
4. **Rate limiting** en `/auth/login` — frena intentos de fuerza bruta.
5. **JWT + refresh** con revocación — sesiones controlables.
6. **Base de datos nunca expuesta** — solo el backend la toca.

---

### Estrategia de multi-tenant y modelo de despliegue

El sistema separa **dos decisiones** que suelen confundirse:

1. **Modelo comercial** — cómo se vende y quién hostea.
2. **Topología técnica** — cómo se aíslan los datos de cada empresa.

La regla de diseño es: **construir el código como multi-tenant-capaz desde el inicio, y
dejar la topología de despliegue como una decisión por-cliente que se toma sobre la marcha.**
El mismo esquema de tablas sirve para ambos modelos comerciales; lo único que cambia es
operativo, no de diseño.

#### Modelos comerciales (ambos soportados por el mismo código)

| | **Camino A — Licencia (el cliente hostea)** | **Camino B — SaaS (tú hosteas todo)** |
|---|---|---|
| Hosting | Lo paga el cliente | Lo pagas tú (en la suscripción) |
| Mantenimiento | Tú, por contrato/retainer de soporte | Tú |
| Ingreso | Pago único + setup + retainer | Suscripción recurrente (MRR) |
| Aislamiento de datos | Físico (servidores/BD separados) | Lógico (`tenant_id` + RLS) |
| Arreglar un bug | Desplegar a cada instancia | Se arregla una vez, todos lo reciben |
| Carga operativa para ti | Baja | Alta (uptime, soporte, costos de todos) |
| Valor del negocio | Menor, fragmentado | Mayor, recurrente y escalable |

#### Ruta recomendada (evolutiva)

- **Primeros clientes externos:** una **instancia dedicada por cliente** (base de datos
  propia), mantenida por ti bajo retainer. Bajo riesgo, aislamiento perfecto. Es el mismo
  código corriendo en `TENANT_MODE=single`.
- **Cuando el producto madure:** migrar hacia **SaaS compartido** (varios tenants en una
  instancia, `TENANT_MODE=shared`) para ganar la economía de "arreglar una vez" e ingreso
  recurrente. El código ya está listo porque se construyó con `tenant_id` + RLS desde el día 1.

#### Topología técnica: pool compartido + RLS (el superconjunto que sirve para todo)

Se diseña para el modelo **más estricto** (varios tenants en una base, discriminados por
`tenant_id`), porque ese diseño **también funciona** en modo base-por-cliente sin cambios.
Diseñar al revés cerraría la puerta al SaaS sin un rediseño costoso.

- **`tenant_id` en todas las tablas** (ya definido en §4).
- **Row-Level Security (RLS) de PostgreSQL:** políticas en la base que **rechazan devolver
  filas de otro tenant** aunque una consulta olvide filtrar. Es la red de seguridad que hace
  seguro el modo compartido. El backend fija el tenant activo por sesión/conexión desde el
  contexto de autenticación (`SET app.current_tenant = ...`), y las políticas RLS lo aplican
  automáticamente. En modo single-tenant es inofensiva: solo hay un tenant y la política
  siempre pasa.
- **`TENANT_MODE = single | shared`:** variable de entorno que decide en el arranque cómo se
  resuelve el tenant. **No toca el esquema** — el mismo artefacto Docker sirve para ambos.

#### Disciplina crítica: un solo código fuente, sin forks

La reutilización del 80–90% para el siguiente cliente **solo funciona si NO se bifurca el
código**. Si cada cliente tuviera su propia copia modificada por separado, mantenerlas
divergiendo consumiría todo el tiempo (un bug = arreglarlo N veces). La regla:

- **Un solo repositorio, un solo artefacto** desplegado en todos lados.
- Las diferencias entre clientes van en **configuración por tenant** (feature flags,
  parámetros en base de datos), **nunca en ramas de código**.

#### Derechos de distribución (IP)

Es un asunto de **contrato/licencia**, independiente de la topología técnica. En ambos
caminos **el desarrollador conserva el IP**: en el Camino A se vende una *licencia de uso*
(el código sigue siendo del autor); en el Camino B ni siquiera se entrega el código, solo el
acceso. En los dos casos queda libre la reutilización de la base para el siguiente cliente.

---

## 4. Modelo de datos completo

Convenciones: toda tabla incluye `id` (PK) y `tenant_id` (FK, índice). El dinero se guarda
como `NUMERIC(14,2)` en COP. Las fechas de evento como `DATE`; los timestamps de auditoría
como `TIMESTAMPTZ`. Nada se borra físicamente salvo donde se indique explícitamente.

**Row-Level Security (RLS):** todas las tablas con `tenant_id` llevan una política RLS que
filtra automáticamente por el tenant activo de la sesión (ver §3 · Topología técnica). Es la
red de seguridad que impide fugas entre empresas en modo compartido, e inofensiva en modo
single-tenant.

**Columnas de auditoría (`created_by`, `created_at`):** presentes en las tablas
operativas/financieras a propósito. Su costo de espacio es insignificante (~12 bytes por
fila; menos de 0,3 MB en 10 años al volumen de esta empresa) y aportan trazabilidad
irrecuperable si no se captura en el momento: `created_by` identifica quién registró cada
dato (responsabilidad entre operadores) y `created_at` —distinto de la fecha de negocio—
es lo que prueba, por ejemplo, que una producción con `production_date` del 28/feb se
insertó realmente el 3/mar (registro tardío auditado, ver §6.1).

### Diagrama de relaciones (alto nivel)

```
tenants ──< users ──< refresh_tokens
   │
   ├──< clients ──< productions ──< production_machines >── machines
   │       │            │                                      │
   │       │            ├──< production_status_history         ├──< machine_partners >── partners
   │       │            ├──< production_edits                  └──< operating_costs
   │       │            └──< payments
   │       └──< services >── service_types ──< service_prices
   │
   ├──< embroideries ──< embroidery_prices
   ├──< articles
   ├──< periods ──< partner_settlements
   ├──< partner_advances
   ├──< exchange_rates
   └──< audit_log
```

### 4.1 `tenants`
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| name | text | Nombre de la empresa |
| base_currency | char(3) | `'COP'` — moneda en que se guarda todo |
| locale | text | `'es-CO'` — formato fecha/número |
| created_at | timestamptz | |

### 4.2 `users`
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| username | text | Único por tenant |
| email | text | Usado por el admin; opcional para operadores |
| password_hash | text | bcrypt — nunca texto plano |
| role | enum | `admin` \| `owner` \| `operator` |
| is_active | bool | Desactivación = bloqueo inmediato de acceso |
| allow_multi_device | bool | `true` solo para el dueño |
| created_at / created_by | | |

### 4.3 `refresh_tokens` (sesiones)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| user_id | FK | |
| token_hash | text | Solo el hash, nunca el token |
| device_label | text | Identifica el dispositivo |
| issued_at | timestamptz | |
| expires_at | timestamptz | `issued_at + 14 días` |
| revoked_at | timestamptz \| null | Logout o revocación de emergencia |
| last_used_at | timestamptz | |

> Multi-dispositivo: para operadores y admin se permite **una** sesión activa (al iniciar
> en otro lado se revoca la anterior). Para el dueño (`allow_multi_device = true`) coexisten
> varias filas activas.

### 4.4 `clients`
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| name | text | |
| phone | text **NOT NULL** | Obligatorio — requerido para WhatsApp en Fase 2 |
| registered_at | date | |
| created_by | FK users | |

> Saldo del cliente = **calculado**, no almacenado (ver §6.6).

### 4.5 `embroideries` (bordados base)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| code | text | Único por tenant (ej: `1105`, `prom26`) |
| description | text | |
| is_active | bool | Inactivo = no aparece en formularios, historial intacto |
| created_by | FK | |

### 4.6 `embroidery_prices` (historial de precios)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| embroidery_id | FK | |
| unit_price | numeric(14,2) | V/U vigente en el período |
| start_date | date | Desde cuándo aplica |
| end_date | date \| null | **null = precio vigente** |
| created_by | FK | |

> Regla: nunca se borra un precio ya usado. Al cambiar precio, se cierra el anterior
> (`end_date`) y se inserta el nuevo (`start_date`, `end_date = null`).

### 4.7 `articles` (artículos de trazabilidad)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| name | text | CAMISETA, GORRA, FRENTE DE MALETA, CARTUCHERA… |
| is_active | bool | |
| created_by | FK | |

> **Decisión de diseño (revisar en §13):** los docs base ataban cada artículo a un bordado
> específico. Dado que el dueño los agrega libremente y son muy variables, se
> modela como **catálogo global por tenant** referenciado opcionalmente desde la producción.
> Evita tener que registrar "CAMISETA" en cada bordado. No afecta precio (solo trazabilidad).

### 4.8 `machines`
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| name | text | SWF, HAPPY, Abotonadora, Ojaladora… |
| start_date | date | |
| status | enum | `active` \| `inactive` (baja sin perder historial) |
| created_by | FK | |

### 4.9 `partners` (socios)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| name | text | |
| is_owner | bool | Marca al dueño (socio en todas las máquinas) |
| user_id | FK \| null | Enlace opcional al usuario dueño |
| created_by | FK | |

### 4.10 `machine_partners` (participación por máquina)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| machine_id | FK | |
| partner_id | FK | |
| percentage | numeric(5,2) | 0–100 |
| start_date | date | |
| end_date | date \| null | Salida del socio, historial intacto |

> Validación de aplicación: la suma de `percentage` de los socios **activos** de una máquina
> debe ser exactamente 100. Datos iniciales:
> HAPPY → A 20%, B 35%, Dueño 45%. SWF → C 30%, D 10%, Dueño 60%.
> Abotonadora y Ojaladora → Dueño 100%.

### 4.11 `productions`
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| client_id | FK | |
| sequence_number | int | **Secuencial por cliente** (cliente A: 1,2,3…; cliente B: 1,2,3…) |
| production_date | date | |
| embroidery_id | FK | Define el V/U sugerido |
| article_id | FK \| null | Solo trazabilidad |
| total_quantity | int | |
| unit_price | numeric(14,2) | V/U — copiado del historial, **editable manualmente** |
| unit_price_source | enum | `catalog` \| `manual_override` |
| total_value | numeric(14,2) | V/T = `unit_price × total_quantity` (almacenado) |
| status | enum | Default `Registrado` |
| currency | char(3) | `COP` (reservado para multi-moneda futura) |
| created_by | FK | |
| created_at | timestamptz | |

> `sequence_number` se asigna de forma atómica al insertar (`MAX(sequence_number)+1` por
> cliente, dentro de transacción/lock para evitar duplicados).
> V/A (acumulado del cliente) **no se almacena**: se calcula al consultar.

### 4.12 `production_machines` (reparto por máquina)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| production_id | FK | |
| machine_id | FK | |
| quantity | int | Parcial producido en esa máquina |
| subtotal | numeric(14,2) | `quantity × production.unit_price` |

> Validación: `SUM(quantity) = production.total_quantity`. Ej: 200 uds → HAPPY 130 + SWF 70.
> El reparto por máquina es la base para costos y liquidación de socios.

### 4.13 `production_status_history`
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| production_id | FK | |
| previous_status | enum \| null | null en el primer registro |
| new_status | enum | |
| changed_at | timestamptz | **Timestamp exacto — combustible del ML de Fase 2** |
| changed_by | FK users | |

> Al crear una producción se inserta automáticamente la primera fila
> (`previous = null`, `new = Registrado`). Cada día sin estos timestamps es dato perdido
> para el modelo de predicción de Fase 2.

### 4.14 `production_edits` (auditoría de ediciones del dueño)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| production_id | FK | |
| field_changed | text | Qué campo cambió |
| old_value / new_value | text | |
| reason | text **NOT NULL** | Justificación obligatoria |
| edited_by | FK users | Debe ser rol `owner` |
| edited_at | timestamptz | |
| triggered_recalculation | bool | `true` si tocó un período cerrado |

> Una producción **nunca se borra**. Solo el dueño la edita, siempre con motivo
> escrito. Cada edición queda registrada aquí de forma inmutable.

### 4.15 `payments` (abonos de clientes)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| client_id | FK | |
| production_id | FK \| null | Si aplica a una producción específica |
| service_id | FK \| null | Si aplica a un servicio externo |
| amount | numeric(14,2) | |
| payment_date | date | |
| type | enum | `completo` \| `parcial` \| `anticipo` |
| note | text | |
| created_by | FK | |

> Check: `production_id` y `service_id` no pueden estar ambos llenos. Unifica el saldo del
> cliente sin importar si pagó una producción o un servicio.

### 4.16 `service_types`
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| name | text | Ojalado, abotonado… (extensible) |
| is_active | bool | |

### 4.17 `service_prices` (historial de precios de servicios)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| service_type_id | FK | |
| unit_price | numeric(14,2) | |
| start_date | date | |
| end_date | date \| null | null = vigente |

> Ojalado y abotonado también tienen su propio historial de precios, con la misma
> mecánica de cierre/apertura que los bordados.

### 4.18 `services` (servicios externos registrados)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| client_id | FK | |
| service_type_id | FK | |
| service_date | date | |
| quantity | int | |
| unit_price | numeric(14,2) | Tomado del historial vigente |
| total_value | numeric(14,2) | `unit_price × quantity` |
| currency | char(3) | `COP` |
| created_by | FK | |

> Suma al saldo del cliente igual que una producción. **No** genera socios ni costos:
> ganancia 100% del dueño.

### 4.19 `operating_costs` (costos operativos)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| machine_id | FK | A qué máquina pertenece (filtrable) |
| type | enum | `hilos` \| `bobinas` \| `mantenimiento` \| `operario` \| `luz` \| `otro` |
| amount | numeric(14,2) | |
| cost_date | date | |
| period_id | FK | Período al que aplica |
| description | text | |
| hours_worked | numeric \| null | Solo si `type = operario` (calculadora) |
| hourly_rate | numeric \| null | Solo si `type = operario` |
| created_by | FK | |

> Costo de operario: si `type = operario`, `amount = hours_worked × hourly_rate`.
> La UI muestra una calculadora horas × tarifa. Editable/borrable **solo si el período no
> está cerrado** (ver §6).
> Costos con dos máquinas: cada máquina lleva sus costos por separado; la
> asignación a una producción multi-máquina es proporcional a lo que produjo cada una
> (vía `production_machines.quantity`).

### 4.20 `periods` (períodos de liquidación)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| period_type | enum | `monthly` \| `annual` |
| year | int | |
| month | int \| null | null para anual |
| status | enum | `open` \| `closed` |
| closed_at / closed_by | | |
| recalculation_count | int | Incrementa con cada override del dueño |

### 4.21 `partner_settlements` (liquidación calculada)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| period_id | FK | |
| machine_id | FK | |
| partner_id | FK | |
| machine_gross | numeric(14,2) | Total producido por la máquina en el período |
| machine_costs | numeric(14,2) | Suma de costos del período |
| machine_net | numeric(14,2) | gross − costs |
| partner_percentage | numeric(5,2) | Snapshot del % al cerrar |
| partner_share | numeric(14,2) | net × percentage |
| version | int | Sube si se recalcula el cierre |
| calculated_at | timestamptz | |

### 4.22 `partner_advances` (abonos a socios)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| partner_id | FK | |
| machine_id | FK \| null | |
| period_id | FK \| null | |
| amount | numeric(14,2) | |
| advance_date | date | |
| note | text | |
| created_by | FK | |

> Los abonos a socios son egresos de su ganancia; se descuentan del pago
> acumulado actual del socio. Saldo del socio = `SUM(partner_share) − SUM(advances)`.

### 4.23 `exchange_rates`
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| base_currency | char(3) | `COP` |
| quote_currency | char(3) | `USD` |
| rate | numeric(14,6) | |
| fetched_at | timestamptz | |
| source | text | API de origen |

### 4.24 `audit_log` (registro general de actividad)
| Columna | Tipo | Notas |
|---|---|---|
| id | PK | |
| tenant_id | FK | |
| user_id | FK | |
| action | text | login, crear_produccion, cerrar_periodo, reset_password… |
| entity_type / entity_id | | |
| details | jsonb | |
| created_at | timestamptz | |

---

## 5. Autenticación y autorización

### Flujo de login
1. Usuario envía `username` + `password` a `POST /auth/login`.
2. Backend verifica el hash bcrypt y que `is_active = true`.
3. Devuelve **access token** (JWT, 15 min) + **refresh token** (14 días, guardado como hash).
4. El front guarda el access token en memoria y el refresh token en cookie `HttpOnly`
   `Secure` `SameSite=Strict` (no accesible por JavaScript → resistente a XSS).

### Renovación
- Cuando el access token expira, el front llama `POST /auth/refresh` con la cookie.
- Backend valida el refresh token contra la BD (no revocado, no expirado) y emite uno nuevo.
- Si el refresh token no vale → se fuerza login. En la práctica el usuario no vuelve a
  escribir contraseña hasta pasados ~14 días de inactividad.

### Roles y permisos

| Acción | admin | dueño | operador |
|---|:---:|:---:|:---:|
| Registrar producción (form móvil) | — | ✓ | ✓ |
| Ver dashboard / finanzas / socios / costos | — | ✓ | — |
| Editar producción (con motivo) | — | ✓ | — |
| Cerrar / recalcular período | — | ✓ | — |
| Gestionar bordados, artículos, máquinas, precios | — | ✓ | — |
| Listar usuarios (sin datos financieros) | ✓ | ✓ | — |
| Activar / desactivar cuentas | ✓ (todas) | ✓ (operadores y admin) | — |
| Resetear contraseñas | ✓ | ✓ | — |
| Ver producciones, saldos, datos del negocio | **✗** | ✓ | parcial |

### Rol admin — alcance acotado
El admin (el desarrollador, como **auditor de emergencia**) **solo** puede:
- Listar usuarios (nombre, rol, estado — sin un solo dato financiero).
- Activar/desactivar cuentas.
- Resetear contraseñas.

No accede a producciones, saldos, socios ni costos. Si su cuenta se compromete, no hay nada
de valor que robar: solo podría bloquear usuarios, lo cual el dueño nota de inmediato.

### Cuenta comprometida — respuesta rápida
Tanto **admin como dueño** pueden desactivar cuentas, con alcance cruzado:
- Si el dueño sospecha que la cuenta del admin fue comprometida → **el dueño la desactiva**
  sin depender del admin.
- Si una cuenta de operador se compromete → cualquiera de los dos la desactiva.
- Desactivar una cuenta **revoca todos sus refresh tokens** → cierra todas sus sesiones al
  instante.
- Escenario extremo (admin + dueño comprometidos a la vez): último recurso vía acceso
  directo controlado a la base de datos.

### Reset de contraseña
Sin flujo de email. El admin (o el dueño) genera una contraseña temporal desde la app; el
usuario la cambia en su primer ingreso. Simple y suficiente para 4 usuarios internos.

### Aislamiento entre empresas (RLS)
Más allá del filtrado por `tenant_id` en cada consulta, PostgreSQL aplica **Row-Level
Security**: el backend fija el tenant activo por sesión y la base de datos rechaza por sí
misma cualquier fila de otro tenant, aunque una consulta olvide filtrar. Doble candado que
hace seguro el modo SaaS compartido (ver §3 · Topología técnica).

---

## 6. Reglas de negocio codificadas

### 6.1 Cierre de período y recálculo
**Qué congela un cierre:** únicamente las **producciones contabilizadas** del período y la
**distribución de socios** (`partner_settlements`). El resto del sistema sigue operando
normalmente — por ejemplo, una producción que entra el 30 y se termina el 1–2 del mes
siguiente no se ve bloqueada.

**Override del dueño:** si tras cerrar Febrero aparece una producción del
28/feb no registrada, el dueño **puede forzar el registro con la fecha del período cerrado**,
dejando justificación obligatoria. El sistema entonces:
1. Inserta la producción con `production_date` real (28/feb).
2. Registra el motivo en `production_edits` con `triggered_recalculation = true`.
3. **Recalcula** `partner_settlements` de ese período (nueva `version`,
   `recalculation_count++`).
4. Deja traza completa de quién, cuándo y por qué.

Así el cierre es "irreversible" para el flujo normal pero el dueño tiene una válvula
auditada para correcciones legítimas.

### 6.2 V/U editable
Al elegir un bordado, el formulario autocompleta el V/U vigente del historial
(`unit_price_source = catalog`). El dueño puede **sobrescribirlo manualmente**
(`manual_override`) — caso típico: traen 2 prendas y encender la máquina solo para eso sube
el precio de $1.000 a $1.500. No hay tabla de rangos; es manual porque es muy variable
entre bordados.

### 6.3 Edición de producciones
- Nunca se borran (no hay endpoint DELETE de producciones).
- Solo el dueño edita.
- `reason` obligatorio en cada edición → `production_edits`.

### 6.4 Secuencial por cliente
`sequence_number` reinicia por cliente. Filtro por fecha disponible para saber cuánto se
produjo un día dado, sin mezclar la numeración entre clientes.

### 6.5 Liquidación de socios
Por máquina y período:
```
machine_net = machine_gross − Σ(operating_costs del período de esa máquina)
partner_share = machine_net × (percentage / 100)
saldo_socio = Σ(partner_share) − Σ(partner_advances)
```
Servicios externos no entran aquí (100% dueño).

### 6.6 Saldos calculados (no almacenados)
```
saldo_cliente = Σ(productions.total_value) + Σ(services.total_value) − Σ(payments.amount)
estado_cliente = 🔴 Debe (saldo > 0) | 🟢 Saldado (saldo = 0)
```
Se calculan al consultar para evitar inconsistencias por desincronización.

---

## 7. Estructura de la API (REST)

Prefijo `/api/v1`. Toda respuesta filtra por `tenant_id` derivado del token.

```
Auth
  POST   /auth/login
  POST   /auth/refresh
  POST   /auth/logout
  GET    /auth/me

Admin (rol admin/owner)
  GET    /admin/users
  POST   /admin/users
  PATCH  /admin/users/{id}/activate
  PATCH  /admin/users/{id}/deactivate
  POST   /admin/users/{id}/reset-password

Clientes
  GET    /clients            (filtros: estado pago, búsqueda)
  POST   /clients
  GET    /clients/{id}
  GET    /clients/{id}/balance
  GET    /clients/{id}/productions

Bordados y precios
  GET    /embroideries
  POST   /embroideries
  PATCH  /embroideries/{id}
  GET    /embroideries/{id}/prices
  POST   /embroideries/{id}/prices      (cierra el anterior, abre el nuevo)

Artículos
  GET    /articles
  POST   /articles
  PATCH  /articles/{id}

Máquinas y socios
  GET    /machines
  POST   /machines
  PATCH  /machines/{id}
  GET    /machines/{id}/partners
  POST   /machines/{id}/partners

Producciones
  GET    /productions        (filtros: fecha, máquina, estado, bordado, artículo, cliente)
  POST   /productions
  GET    /productions/{id}
  PATCH  /productions/{id}    (solo dueño, reason obligatorio)
  GET    /productions/{id}/history

Abonos
  GET    /payments
  POST   /payments

Servicios externos
  GET    /service-types
  POST   /service-types
  GET    /service-types/{id}/prices
  POST   /service-types/{id}/prices
  GET    /services
  POST   /services

Costos operativos
  GET    /costs              (filtros: máquina, tipo, período)
  POST   /costs
  PATCH  /costs/{id}         (bloqueado si período cerrado)
  DELETE /costs/{id}         (bloqueado si período cerrado)

Períodos y liquidación
  GET    /periods
  POST   /periods/{id}/close
  POST   /periods/{id}/recalculate
  GET    /periods/{id}/settlement
  GET    /partners/{id}/balance
  POST   /partner-advances

Dashboard
  GET    /dashboard/summary       (resumen financiero del dueño)
  GET    /dashboard/clients
  GET    /dashboard/machines
  GET    /dashboard/services
  GET    /dashboard/partners
  GET    /dashboard/export        (.xlsx)

Moneda
  GET    /exchange-rate            (tasa COP→USD vigente)
```

---

## 8. Moneda y localización

### Regla de oro
**Todo se guarda en COP.** Es la moneda en que ocurren las transacciones. Guardar en USD
implicaría convertir con flotantes y romper la contabilidad exacta.

### Conversión a USD
- Es **solo de visualización**. El usuario alterna COP/USD y **toda** la interfaz muestra los
  valores en la moneda elegida (dashboard, tablas, exportaciones).
- La tasa se **auto-actualiza** cada hora vía APScheduler desde **open.er-api.com** (pública,
  sin API key, HTTPS), y se guarda en `exchange_rates`.
- **Fallback:** si la API falla, se usa la última tasa conocida (la fila más reciente). El
  sistema nunca se cae por falta de tasa.

### Multi-moneda futura
No se complica Fase 1. El diseño ya lo deja preparado: `tenants.base_currency` y la columna
`currency` en entidades monetarias. En Fase 3, cada empresa (tenant) configura su moneda
base y guarda en ella. Esta empresa nace con historial limpio en COP, sin migración futura.

### Formato
- Fecha: `DD/MM/YYYY`.
- Miles: punto (`$1.250.000`). Decimales: coma.
- Centralizado en utilidades de formato del front (según `locale` del tenant).

---

## 9. Exportación a Excel

Generación en **backend** con `openpyxl` (datos ya formateados, una sola fuente de verdad).
`GET /dashboard/export` produce un `.xlsx` con hojas: Clientes/saldos, Producciones,
Costos por máquina, Liquidación de socios, Servicios. Respeta el período y los filtros
activos y la moneda seleccionada.

---

## 10. Comportamiento offline

Decisión: **bloqueo total con banner**, no operación parcial (evita errores y flujos a medias).

- El service worker de la PWA detecta pérdida de conexión.
- Se muestra un **banner persistente** "Sin conexión - Revisa tu red y refresca la pagina".
- Los formularios de escritura se deshabilitan; no se encola nada para enviar después.
- Al volver la conexión, el banner desaparece y la operación se reanuda.
- TanStack Query reintenta automáticamente las lecturas al recuperar red.

La PWA sigue siendo instalable y abre, pero deja claro que requiere conexión activa para
operar (los estados cambian constantemente y necesitan el servidor como única verdad).

---

## 11. CI/CD con GitHub Actions

```
Push / PR a main
   │
   ├─ Job test
   │    ├─ Backend: pytest + ruff (lint) + mypy (tipos)
   │    └─ Frontend: vitest + eslint + tsc
   │
   ├─ Job build  (solo si test pasa)
   │    └─ docker build de frontend y backend
   │
   └─ Job deploy (solo en main, si build pasa)
        └─ Railway deploy automático
```

GitHub Actions es la opción más simple para un desarrollador solo y se integra nativamente
con el repo. (GitLab CI ofrece lo equivalente si se migrara a GitLab; no es necesario.)

---

## 12. Backups

| Tipo | Frecuencia | Destino |
|---|---|---|
| `pg_dump` completo | Diario (APScheduler o cron de Railway) | **Backblaze B2** — externo al servidor |
| Snapshot del Postgres gestionado | Según Railway | Railway |
| Retención | 30 días rotativos | |

Backblaze B2 es notablemente más barato que S3 con API compatible. Lo crítico: el backup
vive **fuera** del servidor principal, de modo que un fallo de Railway no se lleva los datos.

---

## 13. Estructura del proyecto

```
erpEmbordery/
├── docker-compose.yml
├── .github/workflows/ci.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/                 # migraciones
│   └── app/
│       ├── main.py
│       ├── core/                # config, seguridad, JWT, dependencias
│       ├── models/              # SQLAlchemy
│       ├── schemas/             # Pydantic
│       ├── api/v1/              # routers por módulo
│       ├── services/            # lógica de negocio (liquidación, cierre, tasa)
│       └── tasks/               # APScheduler (tasa de cambio, backup)
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts           # + vite-plugin-pwa
    └── src/
        ├── lib/                 # api client, formato moneda/fecha
        ├── stores/              # Zustand (sesión, moneda, conexión)
        ├── features/            # clientes, producciones, dashboard, etc.
        ├── components/          # UI reutilizable (Tailwind)
        └── routes/
```

---

## 14. Roadmap de implementación — Fase 1

| # | Hito | Entrega |
|---|---|---|
| 1 | Andamiaje | Docker compose, FastAPI + Postgres + React vivos, "hello world" autenticado |
| 2 | Auth completa | login/refresh/logout, roles, gestión de usuarios del admin, reset |
| 3 | Catálogos | bordados + historial de precios, artículos, máquinas, socios |
| 4 | Producciones | formulario móvil, multi-máquina, secuencial por cliente, estado + timestamp |
| 5 | Abonos y servicios | pagos de clientes, servicios externos con su historial de precios |
| 6 | Costos y liquidación | costos por máquina, calculadora operario, cierre + recálculo de período |
| 7 | Dashboard | secciones 1–5, gráficas + tablas, filtros, exportación Excel |
| 8 | Moneda y PWA | toggle COP/USD, tasa horaria + fallback, offline bloqueante, instalable |
| 9 | CI/CD + backups + Cloudflare | pipeline, `pg_dump` a B2, compuerta de acceso, despliegue |

> Sección 6 del dashboard (estado de producciones en tiempo real) queda **reservada** para
> Fase 2; su espacio existe desde ya y los timestamps de estado se recolectan desde el día 1.

---

## 15. Puntos resueltos (cerrados en sesión)

1. **Modelo de artículos (§4.7):** ✅ **Catálogo global por tenant**, confirmado. El
   artículo en la producción es solo trazabilidad y no afecta precio.
2. **API de tipo de cambio:** ✅ **open.er-api.com** (gratuita, sin API key, HTTPS, sin
   límite de uso razonable) con **fallback a la última tasa guardada** en `exchange_rates`.
3. **Cloudflare Access / dominio:** ✅ Por ahora se usa el **subdominio que entrega Railway**,
   con autenticación fuerte (JWT + refresh, rate limiting, sin registro público) como capa de
   cierre. Cloudflare Access se añade cuando se disponga de un dominio propio.
4. **Almacenamiento de backups:** ✅ **Backblaze B2** (más barato, API compatible con S3).

### Corrección de producción olvidada (aclaración del punto 1)
Caso extremo esperado ~1 de cada 1000 registros: por circunstancias se olvidó registrar una
producción. **Debe existir la oportunidad de corregirlo.** Esto ya está cubierto por el
**override del dueño (§6.1)**: puede registrar la producción con su fecha real aunque el
período esté cerrado, dejando justificación obligatoria, y el sistema recalcula la
liquidación de ese período con traza completa. No es un borrado ni una edición silenciosa:
es una corrección auditada.

Todo está cerrado y listo para empezar el Hito 1.
```
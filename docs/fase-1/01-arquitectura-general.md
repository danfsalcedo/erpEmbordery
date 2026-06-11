# Arquitectura General — Dashboard Empresa de Bordados

## Descripción del negocio

Empresa de bordados que opera con máquinas bordadoras (actualmente **SWF** y **HAPPY**) y ofrece servicios adicionales como ojalado y abotonado. El sistema gestiona clientes, producciones, precios por bordado, abonos, costos operativos y distribución de ganancias entre socios.

---

## Tipo de aplicación — PWA (Progressive Web App)

El sistema se construye como una **PWA**: una aplicación web que se instala directamente desde el navegador sin pasar por Play Store ni App Store. Se accede desde un link, se instala en la pantalla de inicio del celular como si fuera una app nativa, y la misma base de código funciona en celular y computador.

### Por qué PWA para este proyecto

| Razón | Detalle |
|---|---|
| Un solo desarrollador | Una sola base de código para móvil y escritorio |
| Usuarios internos | No se necesita distribución pública en tiendas |
| Instalación simple | El operario abre el link en Chrome y da "Instalar en pantalla de inicio" |
| Actualizaciones inmediatas | Al corregir algo, todos los usuarios lo ven de inmediato |
| Costo de desarrollo menor | Comparado con una app nativa para Android o iOS |

### Limitaciones a tener en cuenta

- Requiere conexión a internet para sincronizar datos con el servidor
- En iPhone hay algunas restricciones menores, pero no afectan formularios ni dashboards

---

## Plataforma modular — tres fases activables

La plataforma es un único sistema con módulos que se activan por fase. Comparten la misma base de datos y el mismo backend — no hay sincronización entre sistemas separados.

```
Plataforma única
├── Fase 1 — Gestión del negocio        (activa desde el inicio)
├── Fase 2 — Kanban + ML + WhatsApp     (se activa al terminar Fase 1)
└── Fase 3 — Automatización de bordado  (se activa al terminar Fase 2)
```

Cuando una fase termina, su módulo aparece en la navegación del dueño sin migraciones ni reconexiones.

---

## Plataforma por vista

| Vista | Dispositivo | Propósito |
|---|---|---|
| Entrada rápida de producciones | Celular (móvil) | Digitalizar producciones en campo de forma ágil |
| Dashboard completo | Computador (escritorio) | Análisis y visualización financiera del negocio |

---

## Módulos del sistema (Fase 1)

1. **Gestión de clientes y producciones** — Registro de pedidos con cálculos automáticos y trazabilidad de estados
2. **Catálogo de bordados y precios** — Diseños con historial de precios y artículos de trazabilidad
3. **Máquinas** — Catálogo dinámico de bordadoras con socios y costos asociados
4. **Costos operativos** — Registro de gastos por máquina en tabla única filtrable por ID
5. **Socios de máquina** — Porcentajes de participación y retribución sobre ganancia neta
6. **Servicios externos** — Ojalado, abotonado y futuros servicios; ganancia 100% del dueño
7. **Consolidado / Dashboard** — Vista financiera global del negocio para el dueño

---

## Fuentes de ingreso y su distribución

| Fuente | Base de distribución |
|---|---|
| Producción en bordadora | Costos descontados → ganancia neta repartida entre socios según % |
| Servicios externos (ojalado, abotonado, etc.) | 100% para el dueño, sin distribución |

---

## Stack tecnológico

Decisiones tomadas para toda la plataforma antes de escribir la primera línea de código. Estas elecciones están pensadas para soportar las tres fases sin reconstrucciones.

| Capa | Tecnología | Razón |
|---|---|---|
| Frontend | React + PWA | Una base de código para móvil y escritorio |
| Backend | Python (FastAPI) | Integración nativa con librerías ML en Fase 2 sin microservicios adicionales |
| Base de datos | PostgreSQL | Robusto para consultas financieras complejas y escalable a multi-tenant en Fase 3 |
| Autenticación | JWT + HTTPS obligatorio | Estándar seguro, compatible con roles múltiples |
| WhatsApp (Fase 2) | Meta Cloud API oficial | Estable, sin riesgo de baneo, costo marginal (~$0.02 USD por conversación) |
| ML (Fase 2) | scikit-learn / Prophet | Maduros y bien documentados para predicción de series de tiempo |
| Hosting | Railway, Render o VPS propio | Accesible para un desarrollador solo con presupuesto controlado |
| Backups | Automáticos diarios en almacenamiento externo | Crítico desde el primer día en producción |

### Por qué Python como backend es la decisión más importante

Si se usara Node.js en Fase 1 y se integrara ML en Fase 2, habría que añadir un microservicio Python aparte y conectarlos, duplicando la complejidad para un desarrollador solo. Con FastAPI desde Fase 1, integrar scikit-learn o Prophet en Fase 2 es simplemente importar una librería dentro del mismo proyecto.

---

## Seguridad del sistema

### Autenticación y sesiones

| Mecanismo | Detalle |
|---|---|
| Login con usuario y contraseña | Credenciales únicas por usuario |
| Token JWT | Cada sesión genera un token firmado con fecha de expiración |
| HTTPS obligatorio | Toda comunicación cifrada. Sin HTTPS el sistema no opera |

### Roles de usuario

| Rol | Acceso |
|---|---|
| Dueño | Total: dashboard, socios, costos, liquidaciones, configuración, todos los módulos |
| Operador / digitador | Solo formulario de entrada de producciones (vista móvil) |

Un operador no puede ver información financiera, saldos de clientes, datos de socios ni ninguna sección del dashboard.

### Base de datos

| Regla | Detalle |
|---|---|
| Nunca expuesta directamente | Solo accesible desde el servidor, nunca desde el navegador |
| Acceso por API | La app se comunica mediante endpoints controlados |
| Contraseñas con hash | Nunca almacenadas en texto plano |
| Campo tenant_id reservado | Todas las tablas incluyen este campo desde Fase 1 aunque solo haya un tenant — prepara la base para la comercialización de Fase 3 sin migraciones dolorosas |

### Backups automáticos

| Tipo | Frecuencia | Detalle |
|---|---|---|
| Backup completo | Diario | Copia total de la base de datos |
| Backup incremental | Por operación crítica | Producciones, liquidaciones, cambios de precio |
| Almacenamiento | Externo al servidor principal | Si el servidor falla, el backup debe estar en otro lugar |

### Otras consideraciones

- Cierre de sesión automático tras inactividad prolongada
- Log de actividad: quién registró qué y cuándo
- Validación en servidor de todos los datos, no solo en el formulario del navegador

---

## Moneda y localización

- **Moneda base: COP.** Todos los valores se **guardan siempre en pesos colombianos** (la moneda en que ocurren las transacciones). Nunca se almacena en otra moneda para preservar la contabilidad exacta.
- **Conversión a USD: solo visual.** El usuario puede alternar la vista entre COP y USD y **toda** la interfaz (dashboard, tablas, exportaciones) muestra los valores en la moneda elegida. La tasa se actualiza automáticamente desde internet, con respaldo a la última tasa conocida si la fuente falla.
- **Formato:** fecha `DD/MM/YYYY`; separador de miles con punto (`$1.250.000`). Estándar colombiano.
- **Multimoneda futura:** queda preparado para que, al escalar a otras empresas, cada una configure su propia moneda base sin migraciones.

---

## Mejoras respecto al sistema Excel actual

| Problema actual | Solución propuesta |
|---|---|
| Una hoja de Excel por cliente — no escala | Base de datos relacional centralizada |
| Columnas SWF / HAPPY fijas | Máquinas como entidades dinámicas |
| "OTROS" como columna rígida | Módulo de Servicios extensible |
| Costos de socios no integrados | Costos descontados antes de distribuir ganancia neta |
| Acumulados y saldos manuales | Cálculos automáticos en tiempo real |
| Sin historial de precios | Tabla de historial de precios inmutable por bordado |
| Sin control de acceso | Roles diferenciados con autenticación segura |
| Sin respaldo automático | Backups diarios en almacenamiento externo |
| Sin trazabilidad de estados | Campo de estado + timestamps desde el primer día — combustible para el ML de Fase 2 |

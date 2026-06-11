# Hoja de Ruta — Plataforma de Gestión de Bordados

## Visión general

Plataforma única con módulos activables por fase. Los tres módulos comparten la misma base de datos y el mismo backend — no hay sincronización entre sistemas separados. Cuando una fase termina, su módulo aparece en la navegación del dueño sin migraciones ni reconexiones.

```
Plataforma única
├── Fase 1 — Gestión del negocio        (activa desde el inicio)
├── Fase 2 — Kanban + ML + WhatsApp     (se activa al terminar Fase 1)
└── Fase 3 — Automatización de bordado  (se activa al terminar Fase 2)
```

---

## Fase 1 — Gestión del negocio
**Audiencia:** Esta empresa de bordados exclusivamente
**Estimado:** 9 a 10 semanas a 15 horas semanales

### Módulos
- Gestión de clientes y producciones
- Catálogo de bordados con historial de precios
- Máquinas dinámicas, costos operativos y socios
- Servicios externos (ojalado, abotonado)
- Dashboard consolidado con roles (dueño / operador)

### Decisiones que se toman en Fase 1 pensando en Fase 2 y 3

Estas no son trabajo adicional — son pequeños ajustes de diseño que evitan reconstrucciones costosas después:

| Decisión | Por qué importa ahora |
|---|---|
| Teléfono del cliente obligatorio | La Fase 2 envía avisos por WhatsApp — sin teléfono no hay automatización |
| Campo de estado en cada producción | El kanban de Fase 2 mueve producciones entre estados — el campo debe existir desde el inicio con valor por defecto "Registrado" |
| Timestamp en cada cambio de estado | El ML de Fase 2 aprende de estos tiempos — cada día sin registrarlos es dato perdido para el modelo |
| Configuraciones parametrizables | Nada específico de esta empresa hardcodeado en el código — prepara la base para que Fase 3 sea multi-tenant |

---

## Fase 2 — Kanban + Predicción ML + Automatización WhatsApp
**Audiencia:** Esta empresa de bordados exclusivamente
**Estimado:** 10 a 14 semanas a 15 horas semanales (después de terminar Fase 1)

### Qué resuelve
Actualmente no hay visibilidad del estado interno de cada producción ni estimación de tiempos para el cliente. Todo depende de que el dueño recuerde hacer seguimiento manualmente.

### Tablero Kanban — dos niveles

**Nivel producción:** cada tarjeta es una producción completa moviéndose entre columnas de estado.

```
Pendiente → En máquina → Control de calidad → Listo → Entregado
```

**Nivel tareas internas:** al abrir una tarjeta de producción se ven sus pasos internos con su propio estado (ej: preparación, enhebrado, bordado, revisión, empaque). Cada paso registra automáticamente su timestamp al cambiar de estado.

### Modelo de predicción ML

**Qué aprende:** los patrones de tiempo entre cada estado de cada tipo de producción. Variables que considera:

- Tipo de bordado y artículo
- Cantidad de unidades
- Máquina asignada
- Carga de trabajo actual (cuántas producciones hay en curso)
- Histórico de tiempos reales de producciones similares

**Qué predice:** tiempo estimado de entrega para una nueva producción, con un rango de confianza (ej: "entre 3 y 5 días hábiles").

**Cuándo estará listo el modelo:** necesita mínimo 3 a 6 meses de datos reales de la Fase 1 para hacer predicciones confiables. Por eso es crítico empezar a registrar timestamps desde el primer día de la Fase 1.

### Automatización WhatsApp

**Canal:** API oficial de WhatsApp Business (Meta). Costo aproximado $0.02 USD por conversación iniciada por el negocio — marginal para el volumen de esta empresa.

**Mensajes automatizados:**

| Evento | Mensaje automático |
|---|---|
| Producción registrada | "Hola [cliente], recibimos tu pedido de [bordado]. Te avisamos cuando entre a máquina." |
| Entra a máquina | "Tu pedido está en producción. Estimado de entrega: [fecha predicha por ML]." |
| Lista para recoger | "Tu producción está lista. Puedes pasar a recogerla." |
| Recordatorio si no recoge | "Recuerda que tu pedido lleva [X] días listo. ¿Cuándo puedes pasar?" |

**Intervención del dueño:** casi nula en el flujo estándar. Solo interviene si hay una situación excepcional (retraso inesperado, reclamo, etc.).

### Asignación automática de producciones

El sistema sugiere en qué máquina y en qué franja horaria entra cada producción según:
- Carga actual de cada máquina
- Tipo de bordado (algunos solo van en una máquina específica)
- Prioridad del cliente o fecha límite

El dueño confirma o ajusta la sugerencia — no es completamente autónomo pero reduce drásticamente el tiempo de planificación.

---

## Fase 3 — Automatización de programa de bordado
**Audiencia:** Múltiples empresas (producto comercializable)
**Estimado:** A definir cuando se tenga más contexto

### Lo que se sabe hasta ahora
- Es el módulo más complejo técnicamente
- Tiene potencial de comercialización a otras empresas del sector
- Requiere arquitectura multi-tenant desde el inicio

### Implicación de ser multi-tenant

Multi-tenant significa que múltiples empresas usan la misma plataforma con sus datos completamente aislados entre sí. Esto requiere:

- Cada empresa tiene su propio espacio de datos (por ID de tenant)
- Un superadmin que gestiona qué empresas tienen acceso
- Facturación y planes por empresa
- La configuración de cada empresa es independiente

### Lo que hay que evitar en Fases 1 y 2 para no bloquear la Fase 3

- No hardcodear nombres de máquinas, estados, ni ningún valor específico de esta empresa en el código
- Mantener toda configuración en base de datos, no en archivos de código
- Diseñar las tablas con un campo `tenant_id` reservado desde el inicio, aunque en Fase 1 y 2 solo haya un tenant

---

## Decisiones tecnológicas recomendadas

Estas aplican a toda la plataforma y deben elegirse antes de escribir la primera línea de código:

| Capa | Recomendación | Razón |
|---|---|---|
| Frontend | React + PWA | Una base de código para móvil y escritorio, ecosistema amplio para ML en cliente |
| Backend | Node.js o Python (FastAPI) | Python facilita enormemente la integración con librerías de ML en Fase 2 |
| Base de datos | PostgreSQL | Relacional, robusto, soporta bien consultas complejas de agregación financiera |
| Autenticación | JWT + HTTPS obligatorio | Estándar seguro, compatible con roles múltiples |
| WhatsApp | Meta Cloud API (oficial) | Estable, sin riesgo de baneo, costo marginal |
| ML (Fase 2) | scikit-learn o Prophet | Maduros, bien documentados, adecuados para predicción de series de tiempo |
| Hosting | Railway, Render o VPS propio | Opciones accesibles para un desarrollador solo con presupuesto controlado |
| Backups | Automáticos diarios en almacenamiento externo | Crítico desde el primer día en producción |

---

## Resumen de hitos

| Hito | Fase | Qué marca |
|---|---|---|
| Sistema en producción | Fase 1 | El negocio empieza a operar con la plataforma y acumula datos |
| 3 meses de datos | Fase 1 → 2 | Mínimo de datos para empezar a entrenar el modelo ML |
| Kanban activo | Fase 2 | El dueño gestiona producciones visualmente |
| Primer mensaje automático | Fase 2 | WhatsApp integrado y funcionando |
| Modelo ML en producción | Fase 2 | Las predicciones de tiempo llegan a los clientes automáticamente |
| Primer tenant externo | Fase 3 | La plataforma se vende a otra empresa |

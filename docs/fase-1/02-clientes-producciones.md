# Módulo 2 — Gestión de Clientes y Producciones

## Descripción

Núcleo operativo del negocio. Reemplaza el modelo de "una hoja por cliente" del Excel por una tabla centralizada de producciones. Cada producción referencia un cliente, un bordado base, un artículo de referencia y una o más máquinas.

---

## Estructura de un Cliente

| Campo | Tipo | Descripción |
|---|---|---|
| ID | Auto | Identificador único |
| Nombre | Texto | Nombre del cliente |
| Teléfono | Texto | **Obligatorio** — requerido para automatización de WhatsApp en Fase 2 |
| Fecha de registro | Fecha | Cuándo se creó el cliente |
| Saldo actual | Calculado | Total producido − total abonado |

> El teléfono es obligatorio desde Fase 1. Sin él no es posible automatizar los avisos de WhatsApp en Fase 2. No se puede registrar un cliente sin este campo.

---

## Cómo funciona la selección de bordado

El bordado se selecciona en dos niveles:

### Nivel 1 — Bordado Base
Es el diseño con su precio. Ejemplo: "Bordado Piloto 10 cm" tiene un único V/U sin importar en qué prenda se borde. El precio se **sugiere** automáticamente desde el historial de precios del catálogo (el vigente a la fecha de la producción), pero **es editable manualmente** en casos puntuales. Ejemplo: si solo trajeron 2 prendas, encender la máquina únicamente para eso no justifica el precio base, y el dueño sube ese V/U para esa producción específica. No hay tabla de rangos: el ajuste es manual porque es muy variable entre bordados.

### Nivel 2 — Artículo (solo trazabilidad)
Es la prenda donde se aplicó el bordado. Ejemplo: CAMISETA, CHAQUETA, ESPALDA, MANGA. **No afecta el precio** — su único propósito es dejar registro claro de dónde fue el bordado en caso de reclamos o consultas del cliente.

### Flujo de selección en el formulario
```
1. Seleccionar bordado base (por código o nombre)
   → El V/U se autocompleta desde el historial de precios vigente (editable manualmente)
2. Seleccionar artículo (referencia de trazabilidad)
3. Ingresar cantidad total producida
   → El V/T se calcula automáticamente
```

---

## Producción con una o más máquinas

Una sola producción puede haberse ejecutado en más de una máquina. Ejemplo: 200 bordados del mismo diseño, 130 en HAPPY y 70 en SWF.

### Flujo cuando hay más de una máquina

```
Total de la producción: 200 unidades × V/U
  ├── HAPPY: 130 unidades → subtotal HAPPY
  └── SWF:   70 unidades → subtotal SWF

V/T total = suma de todos los subtotales
```

Cada fracción se registra internamente por máquina para que los cálculos de socios y costos sean correctos por bordadora.

---

## Estructura de una Producción

| Campo | Tipo | Descripción |
|---|---|---|
| ID | Auto | Identificador único |
| # | Auto | Número secuencial por cliente |
| Fecha | Fecha | Fecha de la producción |
| Cliente | Referencia | Cliente al que pertenece |
| Bordado base | Referencia | Diseño del catálogo — define el V/U |
| Artículo | Texto | Prenda de referencia (solo trazabilidad, no afecta precio) |
| Cantidad total | Número | Total de unidades producidas |
| Máquinas | Lista | Una o más máquinas con su cantidad parcial |
| V/U | Sugerido / editable | Se sugiere el precio vigente del bordado base a la fecha; el dueño puede ajustarlo manualmente en casos puntuales |
| V/T | Calculado | V/U × cantidad total |
| V/A | Calculado | Acumulado del cliente hasta esta producción |
| **Estado** | Selección | Estado actual de la producción — ver tabla de estados |
| **Historial de estados** | Lista | Registro automático de cada cambio de estado con timestamp |

---

## Estados de una Producción

El campo estado existe desde Fase 1 aunque en esta fase solo se use "Registrado". En Fase 2 el kanban moverá las producciones entre todos los estados.

| Estado | Descripción | Cuándo aplica |
|---|---|---|
| Registrado | Producción ingresada al sistema | Fase 1 — valor por defecto al crear |
| Pendiente | En cola, aún no entra a máquina | Fase 2 |
| En máquina | Siendo bordada actualmente | Fase 2 |
| Control de calidad | Revisión antes de entregar | Fase 2 |
| Listo | Producción terminada | Fase 2 |
| Entregado | Recogido por el cliente | Fase 2 |

### Historial de estados — timestamps

Cada vez que una producción cambia de estado, el sistema guarda automáticamente:

| Campo | Descripción |
|---|---|
| Estado anterior | De dónde venía |
| Estado nuevo | A dónde pasó |
| Fecha y hora exacta | Timestamp del cambio |
| Usuario | Quién realizó el cambio |

> Estos timestamps son el dato más valioso para el modelo ML de Fase 2. El modelo aprende cuánto tiempo pasa realmente entre cada estado según el tipo de bordado, cantidad y máquina. Cada día que el sistema opere en Fase 1 acumula datos de entrenamiento. No registrarlos desde el inicio es perder ese histórico para siempre.

---

## Edición y eliminación de producciones

La trazabilidad y la contabilidad son pilares del sistema, por eso:

- **Nunca se elimina una producción registrada.** No existe la opción de borrar — es fundamental para la trazabilidad y la contabilidad.
- **Solo el dueño puede editar** una producción, y únicamente en ocasiones muy específicas. Ejemplo: se ingresaron 19 prendas en lugar de 10, se cobró sobre 19 y el cliente reclamó.
- Toda edición exige un **motivo escrito obligatorio** y queda registrada de forma inmutable (quién, cuándo, qué cambió y por qué).
- Si la edición afecta un **período ya cerrado**, el dueño puede forzarla con justificación y el sistema **recalcula** la liquidación de ese período (ver módulo de máquinas/socios). No es un borrado ni un cambio silencioso: es una corrección auditada.

---

## Abonos — Registro por partes

Los abonos son registros independientes. Esto permite pagar completo, en partes o después de la entrega, y mantener trazabilidad clara por producción y por cliente.

### Estructura de un Abono

| Campo | Tipo | Descripción |
|---|---|---|
| ID | Auto | Identificador único |
| Cliente | Referencia | A qué cliente pertenece |
| Producción | Referencia (opcional) | Si aplica a una producción específica |
| Monto | Número | Valor del pago |
| Fecha | Fecha | Cuándo se realizó |
| Tipo | Selección | Completo, parcial, anticipo |
| Nota | Texto | Observación opcional |

### Estados de pago de una producción

| Estado | Descripción |
|---|---|
| Sin abono | No se ha recibido ningún pago |
| Abono parcial | Se ha pagado una parte del V/T |
| Pagado completo | El total del V/T fue cubierto |

### Trazabilidad en el dashboard

Para cada cliente se puede ver:
- Total producido (V/A acumulado)
- Total abonado (suma de todos sus abonos)
- Saldo pendiente global
- Detalle producción por producción: cuánto se pagó y cuánto falta de cada una

---

## Vista móvil — Formulario de entrada rápida

1. Seleccionar cliente
2. Seleccionar bordado base por código o nombre (autocompletado)
   → El V/U aparece automáticamente
3. Seleccionar artículo (campo de referencia — ej: CAMISETA, CHAQUETA)
4. Ingresar cantidad total
5. Seleccionar máquina(s):
   - **Una máquina:** la cantidad total va a esa máquina
   - **Dos o más máquinas:** el formulario despliega un campo de cantidad por cada máquina seleccionada — la suma debe coincidir con el total
6. Registrar abono inicial si lo hay (completo, parcial o ninguno)
7. Confirmar — el sistema calcula V/T, actualiza V/A, asigna estado "Registrado" y guarda el primer timestamp

---

## Vista escritorio

- Tabla completa por cliente con todos los campos
- Columna de estado visible con color (🔴 Debe / 🟢 Saldado)
- Historial de abonos con fechas, montos y tipo
- Trazabilidad de pago por producción
- Filtros por fecha, máquina, estado de producción, bordado, artículo
- Registro de abonos independientes del formulario de producción

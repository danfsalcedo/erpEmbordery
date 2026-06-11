# Módulo 5 — Dashboard Consolidado

## Descripción

Vista financiera global del negocio, diseñada principalmente para el dueño en escritorio. Centraliza el estado de clientes, rendimiento por máquina, costos y saldos de socios. En Fase 2 se añade la sección de estado de producciones en tiempo real.

---

## Sección 1: Estado de Clientes

Resumen de todos los clientes con su situación financiera actual.

| Columna | Descripción |
|---|---|
| Cliente | Nombre |
| Total bordadoras | Suma de todo lo producido en bordadoras |
| Total servicios | Suma de ojalado, abotonado y otros servicios |
| Total general | Bordadoras + servicios |
| Total abonado | Suma de todos los pagos recibidos |
| Saldo | Total general − total abonado |

### Estados de cliente — Solo dos

| Estado | Condición | Color |
|---|---|---|
| 🔴 Debe | Saldo > 0 (tiene deuda pendiente) | Rojo |
| 🟢 Saldado | Saldo = 0 (no debe nada) | Verde |

### Trazabilidad por producción

Al ingresar al detalle de un cliente se puede ver producción por producción:
- V/T de cada producción
- Estado actual de la producción
- Abonos aplicados y cuánto falta por pagar
- Historial completo de abonos con fechas y montos

---

## Sección 2: Rendimiento por Máquina

Para cada bordadora activa en el período seleccionado:

| Métrica | Descripción |
|---|---|
| Total producido | Suma de V/T de todas sus producciones |
| Total costos | Suma de costos operativos del período |
| Ganancia neta | Total producido − total costos |
| Distribución | Desglose por socio según su % |

---

## Sección 3: Servicios Externos

| Métrica | Descripción |
|---|---|
| Total por tipo | Ojalado, abotonado, otros — por separado |
| Total servicios | Suma de todos los servicios |
| Ingreso neto dueño | = Total servicios (100% del dueño) |

---

## Sección 4: Saldos de Socios

| Socio | Máquina | Le corresponde (período) | Abonado | Saldo pendiente |
|---|---|---|---|---|
| Socio A | SWF | $X | $Y | $Z |

---

## Sección 5: Resumen financiero del dueño

| Concepto | Monto |
|---|---|
| % del dueño en cada bordadora (sobre neto) | Por máquina |
| Ingresos por servicios externos | Total |
| **Total ingresos del dueño** | Suma |
| Total cartera pendiente de cobro | Clientes en rojo |
| Saldo pendiente a pagar a socios | Total socios |

---

## Sección 6: Estado de producciones en tiempo real *(reservada para Fase 2)*

Esta sección existe en la arquitectura desde Fase 1 pero se activa con el módulo Kanban de Fase 2. Mostrará:

- Producciones activas agrupadas por estado (Pendiente, En máquina, Control de calidad, Listo)
- Tiempo transcurrido en el estado actual
- Tiempo estimado de entrega predicho por el modelo ML
- Alertas de producciones que llevan más tiempo del esperado en un estado

> El espacio está reservado en el dashboard desde el inicio. Los datos de estado y timestamps que se recolectan en Fase 1 alimentan directamente esta sección cuando se active.

---

## Filtros del dashboard

- Por período: día, semana, mes, año y total (por defecto: **mes actual**)
- Por máquina: una bordadora específica o todas
- Por cliente: búsqueda directa
- Por estado de pago: solo los que deben (🔴) o solo los saldados (🟢)

> **Moneda:** un selector COP/USD afecta a **todo** el dashboard y a las exportaciones. Los datos se guardan en COP; el USD es solo de visualización con tasa auto-actualizada (ver módulo de arquitectura general).

---

## Vista móvil del dashboard

En celular el dashboard se reduce a lo esencial:

- Total cartera pendiente de cobro
- Últimas 5 producciones registradas con su estado actual
- Acceso directo al formulario de nueva producción

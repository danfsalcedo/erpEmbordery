# Módulo 3 — Máquinas, Costos Operativos y Socios

## Descripción

Sistema dinámico donde cada máquina es una entidad independiente con sus propios socios y costos. La ganancia distribuida entre socios es siempre la **ganancia neta**: total producido menos todos los costos operativos del período.

---

## Catálogo de Máquinas


| Campo           | Tipo              | Descripción                             |
| --------------- | ----------------- | --------------------------------------- |
| ID              | Auto              | Identificador único                     |
| Nombre          | Texto             | Ej: SWF, HAPPY, futura máquina          |
| Fecha de inicio | Fecha             | Cuándo entró en operación               |
| Estado          | Activa / Inactiva | Para dar de baja sin eliminar historial |


> Al agregar una nueva máquina queda disponible de inmediato en producciones, costos y socios sin modificar nada más del sistema.

---

## Costos Operativos

### Estructura — Una sola tabla con ID de máquina

Todos los costos viven en una única tabla. El campo **ID máquina** permite filtrar por bordadora o sumar el total general del negocio sin tablas separadas.


| Campo       | Tipo       | Descripción                                        |
| ----------- | ---------- | -------------------------------------------------- |
| ID          | Auto       | Identificador del costo                            |
| ID máquina  | Referencia | A qué bordadora pertenece                          |
| Tipo        | Selección  | Hilos, bobinas, mantenimiento, operario, luz, otro |
| Monto       | Número     | Valor del costo                                    |
| Fecha       | Fecha      | Cuándo se incurrió                                 |
| Período     | Referencia | Mes o año al que aplica                            |
| Descripción | Texto      | Detalle adicional opcional                         |


### Consultas que habilita esta estructura

- **Por máquina:** filtrar por ID máquina → costos solo de SWF o solo de HAPPY
- **Total negocio:** sin filtro → suma de costos de todas las máquinas
- **Por período:** filtrar por mes o año
- **Por tipo:** ver solo lo que se gasta en hilos, o solo en operario, etc.

### Tipos de costo


| Tipo            | Naturaleza                | Descripción                               |
| --------------- | ------------------------- | ----------------------------------------- |
| Hilos           | Variable                  | Específico de cada bordadora              |
| Caja de bobinas | Variable                  | Insumo propio de cada máquina             |
| Mantenimiento   | Variable                  | Reparaciones o revisiones                 |
| Operario        | Variable                  | Calculado con horas trabajadas × precio por hora |
| Luz             | Variable / proporcional   | Costo energético asignado a la máquina    |


> **Costo de operario.** Hoy se calcula por horas trabajadas al día a un precio por hora (mayor al salario mínimo). El sistema ofrece una **calculadora**: horas trabajadas × precio por hora = monto del costo. A futuro podría contemplarse también el salario mínimo como base.

---

## Modelo de Ganancia Neta

```
Total producido por la máquina en el período
  − Costo de hilos
  − Costo de bobinas
  − Mantenimiento
  − Operario (variable según producción)
  − Costo de luz
= GANANCIA NETA DISTRIBUIBLE

  × % Dueño     = Retribución del dueño
  × % Socio A   = Retribución de Socio A
  × % Socio B   = Retribución de Socio B
```

> Los porcentajes de todos los socios de una misma máquina deben sumar 100%.

---

## Socios por Máquina


| Campo           | Tipo         | Descripción                               |
| --------------- | ------------ | ----------------------------------------- |
| Socio           | Referencia   | Nombre del socio                          |
| ID máquina      | Referencia   | A qué bordadora pertenece                 |
| Porcentaje      | Número (%)   | Su participación en esa máquina           |
| Fecha de inicio | Fecha        | Desde cuándo participa                    |
| Fecha de salida | Fecha / nulo | Si ya no participa — historial conservado |


### Reglas de socios

- El **dueño** es socio en todas las máquinas con porcentaje variable por máquina
- Un socio puede participar en **una o más máquinas** con porcentajes independientes
- Si un socio sale, se registra fecha de salida — el historial queda intacto
- Los **Servicios externos** (ojalado, abotonado) no tienen socios — son 100% del dueño

---

## Liquidación por Período

El sistema permite cerrar un período y calcular automáticamente la distribución. Los períodos disponibles son:


| Período | Descripción                       |
| ------- | --------------------------------- |
| Mensual | Cierre mes a mes                  |
| Anual   | Resumen y cierre del año completo |


### Qué calcula el cierre de período

1. Total producido por cada máquina en el período
2. Suma de costos operativos del período por máquina
3. Ganancia neta por máquina
4. Monto a retribuir a cada socio según su %
5. Abonos ya entregados a cada socio en ese período
6. Saldo pendiente por socio

### Resumen de saldo de un socio


| Campo            | Descripción                             |
| ---------------- | --------------------------------------- |
| Total a recibir  | Su % sobre la ganancia neta del período |
| Abonos recibidos | Pagos ya entregados                     |
| Saldo pendiente  | Lo que aún se le debe                   |


### Qué congela un cierre (y qué no)

Cerrar un período **no congela todo el sistema**, solo lo necesario para la contabilidad:

- **Se congelan:** las producciones ya contabilizadas del período y la **distribución de socios** (`partner_settlements`).
- **Sigue operando normalmente** todo lo demás. Ejemplo: una producción que entra el 30 y se termina de sacar el 1 o 2 del mes siguiente no queda bloqueada.

### Corrección de un período cerrado (override del dueño)

El cierre es irreversible para el flujo normal, pero el dueño tiene una **válvula auditada** para corregir olvidos legítimos (≈1 de cada 1000 registros). Si tras cerrar aparece una producción no registrada de ese período:

1. El dueño la registra con su **fecha real** aunque el período esté cerrado, dejando justificación obligatoria.
2. El sistema **recalcula** la liquidación de socios de ese período (nueva versión, contador de recálculos).
3. Queda traza completa de quién, cuándo y por qué. No es un borrado ni una edición silenciosa.

### Abonos parciales a socios

Pueden existir abonos parciales a un socio antes del cierre: se registran como egresos de su ganancia y se **descuentan del pago acumulado actual** del socio (saldo pendiente = total a recibir − abonos entregados).



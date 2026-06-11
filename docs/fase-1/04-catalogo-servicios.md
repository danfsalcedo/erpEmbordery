# Módulo 4 — Catálogo de Bordados y Servicios Externos

---

## Parte A: Catálogo de Bordados

### Descripción

Tabla maestra de todos los diseños disponibles. Organizada en tres niveles: **bordado base** (el diseño), **historial de precios** (tabla separada vinculada al bordado) y **artículos** (prendas donde aplica, solo trazabilidad).

---

### Nivel 1 — Bordado Base

Un único registro por diseño. El precio no vive aquí sino en su propia tabla de historial.

| Campo | Tipo | Descripción |
|---|---|---|
| ID | Auto | Identificador único |
| Código | Texto único | Identificador corto del bordado (ej: 1105, prom26, INEN4) |
| Descripción | Texto | Nombre del diseño (ej: "Bordado Piloto 10 cm", "INEN UNICOLOR") |
| Estado | Activo / Inactivo | Desactivado = no aparece en formularios, pero su historial se conserva intacto |

---

### Nivel 2 — Historial de Precios

Tabla separada vinculada al bordado base. Cada vez que el precio cambia se agrega un nuevo registro con su fecha de inicio, y el registro anterior recibe una fecha de fin. El bordado base no se duplica.

| Campo | Tipo | Descripción |
|---|---|---|
| ID precio | Auto | Identificador único |
| ID bordado | Referencia | A qué diseño pertenece |
| V/U | Número | Precio unitario vigente en ese período |
| Fecha inicio | Fecha | Desde cuándo aplica este precio |
| Fecha fin | Fecha / nulo | Hasta cuándo aplica. **Nulo = precio actual vigente** |

### Ejemplo

```
Bordado base: "Bordado Piloto 10 cm" (código: prom26) — Estado: Activo

  Historial de precios:
  ├── V/U: $7.700 | inicio: 01/01/2025 | fin: 31/12/2025
  └── V/U: $8.500 | inicio: 01/01/2026 | fin: null ← precio vigente
```

Cuando el sistema registra una producción, busca automáticamente el precio cuya fecha inicio sea menor o igual a la fecha de la producción y cuya fecha fin sea nula o mayor. Siempre obtiene el precio correcto para esa fecha sin importar cuántos cambios haya habido.

### Reglas de precios

- **Nunca se elimina un precio** si ya fue usado en al menos una producción. Hacerlo rompería el historial de cálculos
- El precio vigente siempre tiene fecha fin = null
- Al registrar un cambio de precio, el sistema cierra el registro anterior (asigna fecha fin) y crea el nuevo con fecha inicio
- Las producciones pasadas siempre conservan el precio que tenían en su fecha — el historial es inmutable

---

### Nivel 3 — Artículos (catálogo global, solo trazabilidad)

Catálogo **global** de prendas, gestionado por el dueño. **No están atados a un bordado específico**: cualquier producción puede referenciar cualquier artículo para dejar trazabilidad de en qué prenda se ejecutó el bordado. No afectan el precio. Su único propósito es identificar claramente la prenda, útil para reclamos y consultas del cliente.

Se modela como catálogo global (no por bordado) porque el dueño los agrega libremente según lo que envíen los clientes, y son muy variables: camisetas, gorras, frentes de maleta, cartucheras, etc. Atarlos a cada bordado obligaría a recrear "CAMISETA" en cada diseño.

| Campo | Tipo | Descripción |
|---|---|---|
| ID | Auto | Identificador |
| Nombre | Texto | CAMISETA, GORRA, FRENTE DE MALETA, CARTUCHERA, CHAQUETA, etc. |
| Estado | Activo / Inactivo | Inactivo = no aparece en formularios, historial intacto |

### Ejemplo completo

```
Bordado base: "Bordado Piloto 10 cm" (prom26) → precio vigente: $8.500

Catálogo global de artículos (referencia, compartido por todos los bordados):
  ├── CAMISETA
  ├── GORRA
  └── FRENTE DE MALETA

→ El precio del bordado es $8.500 sin importar el artículo
→ El artículo elegido queda registrado en la producción solo para trazabilidad
```

### Política de eliminación y desactivación

| Acción | Cuándo aplica | Efecto |
|---|---|---|
| Desactivar bordado | El diseño ya no se usa | No aparece en formularios, historial intacto |
| Reactivar bordado | Se vuelve a necesitar | Vuelve a aparecer en formularios |
| Eliminar bordado | Solo si nunca tuvo producciones | Permitido únicamente en ese caso |
| Eliminar precio | Nunca si ya fue usado | Prohibido — los precios son inmutables una vez aplicados |

---

## Parte B: Servicios Externos

### Descripción

Módulo extensible para servicios que no pasan por las bordadoras. La ganancia corresponde **100% al dueño**, sin distribución entre socios de máquina.

### Tipos de servicio (extensibles)

| Servicio | Descripción |
|---|---|
| Ojalado | Servicio de ojales en prendas |
| Abotonado | Pegado de botones |
| (Futuro) | Nuevos servicios se agregan sin cambiar la estructura |

### Historial de precios de servicios

Cada tipo de servicio (ojalado, abotonado, etc.) tiene su **propio historial de precios**, con la misma mecánica que los bordados: cada cambio cierra el precio anterior (fecha fin) y abre uno nuevo (fecha inicio; `null` = vigente). Al registrar un servicio, el sistema toma automáticamente el V/U vigente a la fecha. Los precios ya usados son inmutables.

| Campo | Tipo | Descripción |
|---|---|---|
| ID precio | Auto | Identificador único |
| Tipo de servicio | Referencia | A qué servicio pertenece |
| V/U | Número | Precio unitario vigente en ese período |
| Fecha inicio | Fecha | Desde cuándo aplica |
| Fecha fin | Fecha / nulo | Hasta cuándo. **Nulo = vigente** |

### Estructura de un Servicio Registrado

| Campo | Tipo | Descripción |
|---|---|---|
| Fecha | Fecha | Fecha del servicio |
| Cliente | Referencia | A quién se le prestó |
| Tipo de servicio | Selección | Ojalado, abotonado, otro |
| Cantidad | Número | Unidades trabajadas |
| V/U | Sugerido | Tomado del historial de precios del servicio vigente a la fecha |
| V/T | Calculado | V/U × cantidad |
| Abono | Número | Pago recibido en ese momento |

### Integración con el consolidado

- Los servicios suman al saldo del cliente igual que las producciones
- En el dashboard aparecen como categoría separada de las bordadoras
- No generan cálculo de socios ni costos operativos

---

## Parte C: Costos Operativos — Una sola tabla con ID de máquina

Todos los costos viven en una única tabla. El campo **ID máquina** permite consultar por bordadora independiente o sumar el total del negocio, sin tablas separadas por máquina.

```
TABLA COSTOS
├── ID costo (auto)
├── ID máquina  ← clave de filtrado
├── Tipo: hilos | bobinas | mantenimiento | operario | luz | otro
├── Monto
├── Fecha
├── Período (mes / año)
└── Descripción opcional
```

### Consultas que habilita

- **Por máquina:** filtrar por ID → costos solo de SWF o solo de HAPPY
- **Total negocio:** sin filtro → suma de todas las máquinas
- **Por tipo:** ver solo gasto en hilos, o solo en operario, etc.
- **Por período:** mes o año específico

### Política de eliminación de costos

| Acción | Cuándo aplica |
|---|---|
| Editar costo | Permitido si el período aún no ha sido liquidado |
| Eliminar costo | Permitido si el período aún no ha sido liquidado |
| Modificar costo de período cerrado | Prohibido — requiere abrir una corrección como nuevo registro |

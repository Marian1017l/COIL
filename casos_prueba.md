# Casos de prueba — gestionar_despacho

Estos casos los diseñé para verificar que la función gestionar_despacho se comporte bien en diferentes situaciones. La idea es cubrir los casos más importantes: que salga primero lo que vence antes (FEFO), que no se despache nada que esté a punto de vencerse (bloqueo de seguridad), y que el sistema avise cuando no hay suficiente stock.

---

## Reglas que tuve en cuenta

Antes de armar los casos, revisé las reglas principales del sistema:

- **R1 – FEFO:** lo primero que vence es lo primero que sale.
- **R2 – Bloqueo de seguridad:** si un lote vence en 3 días o menos, no se puede usar.
- **R3 – Stock insuficiente:** si no hay suficientes unidades disponibles, el sistema debe avisar con un error.
- **R4 – Filtrado combinado:** solo se usan lotes que pasen tanto R1 como R2 al mismo tiempo.

---

## Escenarios

---

### TC-01 — Lo más básico: despacho normal con FEFO

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 5
- **inventario:**
  - Lote A: 10 unidades, vence el 2025-06-20
  - Lote B: 10 unidades, vence el 2025-07-10
- **qué debería pasar:**
  - Lote A → cantidad_utilizada: 5, saldo_restante: 5, fecha_vencimiento: 2025-06-20

Acá solo quería confirmar que el sistema sí respeta el orden FEFO en el caso más simple posible.

---

### TC-02 — Cuando un solo lote no alcanza

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 10
- **inventario:**
  - Lote A: 5 unidades, vence el 2025-06-15
  - Lote B: 10 unidades, vence el 2025-07-01
- **qué debería pasar:**
  - Lote A → cantidad_utilizada: 5, saldo_restante: 0, fecha_vencimiento: 2025-06-15
  - Lote B → cantidad_utilizada: 5, saldo_restante: 5, fecha_vencimiento: 2025-07-01

Este caso lo pensé para ver si el sistema es capaz de repartir el pedido entre dos lotes cuando uno solo no es suficiente.

---

### TC-03 — Bloqueo exacto en 3 días

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 5
- **inventario:**
  - Lote A: 10 unidades, vence el 2025-06-04 (bloqueado)
  - Lote B: 10 unidades, vence el 2025-06-20
- **qué debería pasar:**
  - Lote B → cantidad_utilizada: 5, saldo_restante: 5, fecha_vencimiento: 2025-06-20

Quería probar específicamente el límite de los 3 días, porque es fácil que ese borde falle.

---

### TC-04 — Lote que vence mañana

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 3
- **inventario:**
  - Lote A: 8 unidades, vence el 2025-06-02 (bloqueado)
  - Lote B: 8 unidades, vence el 2025-06-25
- **qué debería pasar:**
  - Lote B → cantidad_utilizada: 3, saldo_restante: 5, fecha_vencimiento: 2025-06-25

Similar al anterior pero más extremo. Si vence mañana, definitivamente no debería salir.

---

### TC-05 — No hay suficiente stock

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 20
- **inventario:**
  - Lote A: 5 unidades, vence el 2025-06-20
  - Lote B: 5 unidades, vence el 2025-07-10
- **qué debería pasar:** error `"Stock Insuficiente"`

Solo hay 10 unidades aptas en total y el pedido es de 20. El sistema tiene que detectar eso y avisar.

---

### TC-06 — Todo bloqueado, nada disponible (R2 + R3 combinados)

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 5
- **inventario:**
  - Lote A: 10 unidades, vence el 2025-06-02 (bloqueado)
  - Lote B: 10 unidades, vence el 2025-06-03 (bloqueado)
- **qué debería pasar:** error `"Stock Insuficiente"`

Aunque hay unidades en bodega, ninguna está apta. El sistema no debería despachar nada.

---

### TC-07 — Un lote bloqueado, uno apto, stock justo

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 10
- **inventario:**
  - Lote A: 10 unidades, vence el 2025-06-03 (bloqueado)
  - Lote B: 10 unidades, vence el 2025-06-30
- **qué debería pasar:**
  - Lote B → cantidad_utilizada: 10, saldo_restante: 0, fecha_vencimiento: 2025-06-30

El único lote que sirve cubre exactamente el pedido. Lo puse para confirmar que el sistema no intenta mezclar con el bloqueado.

---

### TC-08 — Tres lotes, reparto entre todos

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 12
- **inventario:**
  - Lote A: 3 unidades, vence el 2025-06-10
  - Lote B: 4 unidades, vence el 2025-06-18
  - Lote C: 10 unidades, vence el 2025-07-05
- **qué debería pasar:**
  - Lote A → cantidad_utilizada: 3, saldo_restante: 0, fecha_vencimiento: 2025-06-10
  - Lote B → cantidad_utilizada: 4, saldo_restante: 0, fecha_vencimiento: 2025-06-18
  - Lote C → cantidad_utilizada: 5, saldo_restante: 5, fecha_vencimiento: 2025-07-05

Acá quería ver si el sistema maneja bien el reparto entre tres lotes distintos siguiendo el orden correcto.

---

### TC-09 — Sin inventario registrado

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 5
- **inventario:** ninguno
- **qué debería pasar:** error `"Stock Insuficiente"`

Si no hay nada en bodega, el sistema debe responder limpio con el error, sin colgarse.

---

### TC-10 — El lote más viejo está bloqueado (R1 + R2 juntos)

- **fecha_sistema:** 2025-06-01
- **pedido_cliente:** 6
- **inventario:**
  - Lote A: 10 unidades, vence el 2025-06-04 (bloqueado)
  - Lote B: 4 unidades, vence el 2025-06-15
  - Lote C: 10 unidades, vence el 2025-06-28
- **qué debería pasar:**
  - Lote B → cantidad_utilizada: 4, saldo_restante: 0, fecha_vencimiento: 2025-06-15
  - Lote C → cantidad_utilizada: 2, saldo_restante: 8, fecha_vencimiento: 2025-06-28

Este fue uno de los que más me interesaba probar: que el sistema salte el lote bloqueado aunque sea el más próximo a vencer, y que luego reparta bien entre los siguientes.

---

## Resumen de cobertura

| Regla | Casos |
|-------|-------|
| R1 — FEFO | TC-01, TC-02, TC-08 |
| R2 — Bloqueo de seguridad | TC-03, TC-04, TC-06, TC-07 |
| R3 — Stock insuficiente | TC-05, TC-06, TC-09 |
| R2 + R3 combinados | TC-06 |
| R4 — R1 + R2 combinados | TC-10 |
| Casos propios del QA | TC-10 (R1+R2) |

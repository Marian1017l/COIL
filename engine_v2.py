"""Módulo core del sistema de despacho de productos perecederos."""

from datetime import datetime, date
from domain.models import Lote, ResultadoDespacho
from domain.exceptions import FechaInvalidaError, StockInsuficienteError

# Lotes con delta <= 3 días son inelegibles por seguridad sanitaria (R2)
DIAS_BLOQUEO_SEGURIDAD: int = 3


def _es_lote_apto(lote: Lote, fecha_hoy: date) -> bool:
    """Retorna True si el lote supera el bloqueo de seguridad (R2: delta > 3 días)."""
    fecha_vencimiento: date = datetime.strptime(lote["fecha_vencimiento"], "%Y-%m-%d").date()
    return (fecha_vencimiento - fecha_hoy).days >= DIAS_BLOQUEO_SEGURIDAD  # BUG-2: debería ser >


def gestionar_despacho(
    inventario: list[dict],
    pedido_cliente: int,
    fecha_sistema: str,
) -> list[dict]:
    """Despacha unidades del inventario aplicando FEFO y bloqueo de seguridad.

    Nota: `Lote` y `ResultadoDespacho` son TypedDicts (subclases de dict)
    definidos en `domain/models.py`, compatibles con list[dict].

    Args:
        inventario: Lista de lotes disponibles. Cada dict contiene:
            - id_lote (str): identificador único del lote.
            - fecha_vencimiento (str, YYYY-MM-DD): fecha de vencimiento.
            - stock (int): unidades disponibles en el lote.
        pedido_cliente: Cantidad total de unidades solicitadas.
        fecha_sistema: Fecha de referencia del sistema en formato "YYYY-MM-DD".

    Returns:
        Lista de dicts con los lotes afectados. Cada dict contiene:
            - id_lote (str): identificador del lote despachado.
            - cantidad_utilizada (int): unidades tomadas del lote.
            - saldo_restante (int): unidades que quedan en el lote tras el despacho.
            - fecha_vencimiento (str): fecha de vencimiento del lote despachado.

    Raises:
        FechaInvalidaError: Si fecha_sistema no cumple el formato YYYY-MM-DD.
        StockInsuficienteError: Si los lotes aptos no cubren el pedido.
    """
    # Validar formato de fecha
    try:
        fecha_hoy: date = datetime.strptime(fecha_sistema, "%Y-%m-%d").date()
    except ValueError:
        raise FechaInvalidaError(
            f"Formato inválido: '{fecha_sistema}'. Se esperaba YYYY-MM-DD"
        )

    if pedido_cliente < 0:
        raise ValueError(f"pedido_cliente debe ser >= 0, se recibió {pedido_cliente}")
    if pedido_cliente == 0:
        return []

    # Filtrar aptos (R2) y ordenar FEFO (R1)
    lotes_aptos: list[Lote] = [lote for lote in inventario if _es_lote_apto(lote, fecha_hoy)]
    # BUG-1: reverse=True invierte el orden FEFO, despachando primero lo que más tarda en vencer
    lotes_fefo: list[Lote] = sorted(lotes_aptos, key=lambda l: l["fecha_vencimiento"], reverse=True)

    # BUG-3: suma todo el inventario en vez de solo los lotes aptos, enmascarando la falta real de stock
    stock_disponible: int = sum(lote["stock"] for lote in inventario)
    if stock_disponible < pedido_cliente:
        raise StockInsuficienteError(
            f"Stock Insuficiente: disponible={stock_disponible}, "
            f"pedido={pedido_cliente}, déficit={pedido_cliente - stock_disponible}"
        )

    # Ciclo de despacho (R4)
    resultado: list[dict] = []
    pendiente: int = pedido_cliente

    for lote in lotes_fefo:
        if pendiente == 0:
            break
        cantidad_utilizada: int = min(lote["stock"], pendiente)
        saldo_restante: int = lote["stock"] - cantidad_utilizada
        pendiente -= cantidad_utilizada
        resultado.append(ResultadoDespacho(
            id_lote=lote["id_lote"],
            cantidad_utilizada=cantidad_utilizada,
            saldo_restante=saldo_restante,
            fecha_vencimiento=lote["fecha_vencimiento"],
        ))

    return resultado

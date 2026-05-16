"""Modelos de dominio del sistema de despacho de perecederos.

Define las estructuras de datos principales usando TypedDict para mantener
compatibilidad natural con el LLM y con los reportes JSON.
"""

from typing import TypedDict


class Lote(TypedDict):
    """Estructura de entrada — un lote del inventario.
    
    Atributos:
        id_lote: Identificador único del lote en el inventario.
        fecha_vencimiento: Fecha de vencimiento del lote en formato "YYYY-MM-DD".
        stock: Cantidad disponible de unidades del lote.
    """
    id_lote: str
    fecha_vencimiento: str  # formato "YYYY-MM-DD"
    stock: int


class ResultadoDespacho(TypedDict):
    """Estructura de salida — resultado por lote despachado.
    
    Atributos:
        id_lote: Identificador único del lote que fue despachado.
        cantidad_utilizada: Cantidad de unidades que se consumieron del lote.
        saldo_restante: Cantidad de unidades que permanecen en el lote tras el despacho.
        fecha_vencimiento: Fecha de vencimiento del lote despachado.
    """
    id_lote: str
    cantidad_utilizada: int
    saldo_restante: int
    fecha_vencimiento: str

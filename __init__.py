"""Agente Guardian - Sistema de despacho de productos perecederos.

Módulo principal que expone la funcionalidad de gestión de despacho
con validaciones, FEFO, bloqueo de seguridad y auditoría automática.
"""

from engine import gestionar_despacho, DIAS_BLOQUEO_SEGURIDAD
from domain import (
    Lote,
    ResultadoDespacho,
    FechaInvalidaError,
    StockInsuficienteError,
    LoteInvalidoError,
)

__all__ = [
    # Engine
    "gestionar_despacho",
    "DIAS_BLOQUEO_SEGURIDAD",
    # Domain models
    "Lote",
    "ResultadoDespacho",
    # Domain exceptions
    "FechaInvalidaError",
    "StockInsuficienteError",
    "LoteInvalidoError",
]

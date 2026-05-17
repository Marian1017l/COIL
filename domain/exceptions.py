"""Excepciones tipadas del dominio del sistema de despacho.

Define las excepciones específicas del negocio que pueden ser capturadas
y manejadas en el pipeline de despacho.
"""


class FechaInvalidaError(ValueError):
    """Se lanza cuando fecha_sistema no cumple el formato YYYY-MM-DD.
    
    Atributos:
        mensaje: Descripción detallada del error de formato.
    """
    
    def __init__(self, mensaje: str):
        """Inicializa la excepción con un mensaje descriptivo.
        
        Args:
            mensaje: Descripción del error ocurrido.
        """
        self.mensaje = mensaje
        super().__init__(self.mensaje)
    
    def __str__(self) -> str:
        """Retorna el mensaje con prefijo del nombre de la excepción."""
        return f"[FechaInvalidaError] {self.mensaje}"


class StockInsuficienteError(RuntimeError):
    """Se lanza cuando el stock apto acumulado no alcanza el pedido.
    
    Atributos:
        mensaje: Descripción del déficit de stock.
    """
    
    def __init__(self, mensaje: str):
        """Inicializa la excepción con un mensaje descriptivo.
        
        Args:
            mensaje: Descripción del error de stock.
        """
        self.mensaje = mensaje
        super().__init__(self.mensaje)
    
    def __str__(self) -> str:
        """Retorna el mensaje con prefijo del nombre de la excepción."""
        return f"[StockInsuficienteError] {self.mensaje}"


class LoteInvalidoError(ValueError):
    """Se lanza si un lote del inventario tiene estructura o tipos incorrectos.
    
    Atributos:
        mensaje: Descripción del problema en la estructura del lote.
    """
    
    def __init__(self, mensaje: str):
        """Inicializa la excepción con un mensaje descriptivo.
        
        Args:
            mensaje: Descripción del error en el lote.
        """
        self.mensaje = mensaje
        super().__init__(self.mensaje)
    
    def __str__(self) -> str:
        """Retorna el mensaje con prefijo del nombre de la excepción."""
        return f"[LoteInvalidoError] {self.mensaje}"

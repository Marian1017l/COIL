import pytest
from engine import gestionar_despacho
from domain.exceptions import StockInsuficienteError, FechaInvalidaError

def test_TC_01():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-20', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-07-10', 'stock': 10}]
    pedido = 5
    fecha = '2025-06-01'
    resultado = gestionar_despacho(inventario, pedido, fecha)
    assert len(resultado) == 1
    assert resultado[0]['id_lote'] == 'A'
    assert resultado[0]['cantidad_utilizada'] == 5
    assert resultado[0]['saldo_restante'] == 5

def test_TC_02():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-15', 'stock': 5}, {'id_lote': 'B', 'fecha_vencimiento': '2025-07-01', 'stock': 10}]
    pedido = 10
    fecha = '2025-06-01'
    resultado = gestionar_despacho(inventario, pedido, fecha)
    assert len(resultado) == 2
    assert resultado[0]['id_lote'] == 'A'
    assert resultado[0]['cantidad_utilizada'] == 5
    assert resultado[0]['saldo_restante'] == 0
    assert resultado[1]['id_lote'] == 'B'
    assert resultado[1]['cantidad_utilizada'] == 5
    assert resultado[1]['saldo_restante'] == 5

def test_TC_03():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-04', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-20', 'stock': 10}]
    pedido = 5
    fecha = '2025-06-01'
    resultado = gestionar_despacho(inventario, pedido, fecha)
    assert len(resultado) == 1
    assert resultado[0]['id_lote'] == 'B'
    assert resultado[0]['cantidad_utilizada'] == 5
    assert resultado[0]['saldo_restante'] == 5

def test_TC_04():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-02', 'stock': 8}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-25', 'stock': 8}]
    pedido = 3
    fecha = '2025-06-01'
    resultado = gestionar_despacho(inventario, pedido, fecha)
    assert len(resultado) == 1
    assert resultado[0]['id_lote'] == 'B'
    assert resultado[0]['cantidad_utilizada'] == 3
    assert resultado[0]['saldo_restante'] == 5

def test_TC_05():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-20', 'stock': 5}, {'id_lote': 'B', 'fecha_vencimiento': '2025-07-10', 'stock': 5}]
    pedido = 20
    fecha = '2025-06-01'
    with pytest.raises(StockInsuficienteError) as exc_info:
        gestionar_despacho(inventario, pedido, fecha)
    assert 'Stock Insuficiente' in str(exc_info.value)

def test_TC_06():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-02', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-03', 'stock': 10}]
    pedido = 5
    fecha = '2025-06-01'
    with pytest.raises(StockInsuficienteError) as exc_info:
        gestionar_despacho(inventario, pedido, fecha)
    assert 'Stock Insuficiente' in str(exc_info.value)

def test_TC_07():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-03', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-30', 'stock': 10}]
    pedido = 10
    fecha = '2025-06-01'
    resultado = gestionar_despacho(inventario, pedido, fecha)
    assert len(resultado) == 1
    assert resultado[0]['id_lote'] == 'B'
    assert resultado[0]['cantidad_utilizada'] == 10
    assert resultado[0]['saldo_restante'] == 0

def test_TC_08():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-10', 'stock': 3}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-18', 'stock': 4}, {'id_lote': 'C', 'fecha_vencimiento': '2025-07-05', 'stock': 10}]
    pedido = 12
    fecha = '2025-06-01'
    resultado = gestionar_despacho(inventario, pedido, fecha)
    assert len(resultado) == 3
    assert resultado[0]['id_lote'] == 'A'
    assert resultado[0]['cantidad_utilizada'] == 3
    assert resultado[0]['saldo_restante'] == 0
    assert resultado[1]['id_lote'] == 'B'
    assert resultado[1]['cantidad_utilizada'] == 4
    assert resultado[1]['saldo_restante'] == 0
    assert resultado[2]['id_lote'] == 'C'
    assert resultado[2]['cantidad_utilizada'] == 5
    assert resultado[2]['saldo_restante'] == 5

def test_TC_09():
    inventario = []
    pedido = 5
    fecha = '2025-06-01'
    with pytest.raises(StockInsuficienteError) as exc_info:
        gestionar_despacho(inventario, pedido, fecha)
    assert 'Stock Insuficiente' in str(exc_info.value)

def test_TC_10():
    inventario = [{'id_lote': 'A', 'fecha_vencimiento': '2025-06-04', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-15', 'stock': 4}, {'id_lote': 'C', 'fecha_vencimiento': '2025-06-28', 'stock': 10}]
    pedido = 6
    fecha = '2025-06-01'
    resultado = gestionar_despacho(inventario, pedido, fecha)
    assert len(resultado) == 2
    assert resultado[0]['id_lote'] == 'B'
    assert resultado[0]['cantidad_utilizada'] == 4
    assert resultado[0]['saldo_restante'] == 0
    assert resultado[1]['id_lote'] == 'C'
    assert resultado[1]['cantidad_utilizada'] == 2
    assert resultado[1]['saldo_restante'] == 8
import pytest
from engine import gestionar_despacho
from domain.exceptions import StockInsuficienteError, FechaInvalidaError

def test_TC_01():
    resultado = gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-20', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-07-10', 'stock': 10}], 5, '2025-06-01')
    assert len(resultado) == 1
    assert resultado[0]['id_lote'] == 'A'
    assert resultado[0]['cantidad_utilizada'] == 5
    assert resultado[0]['saldo_restante'] == 5

def test_TC_02():
    resultado = gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-15', 'stock': 5}, {'id_lote': 'B', 'fecha_vencimiento': '2025-07-01', 'stock': 10}], 10, '2025-06-01')
    assert len(resultado) == 2
    assert resultado[0]['id_lote'] == 'A'
    assert resultado[0]['cantidad_utilizada'] == 5
    assert resultado[0]['saldo_restante'] == 0
    assert resultado[1]['id_lote'] == 'B'
    assert resultado[1]['cantidad_utilizada'] == 5
    assert resultado[1]['saldo_restante'] == 5

def test_TC_03():
    resultado = gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-04', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-20', 'stock': 10}], 5, '2025-06-01')
    assert len(resultado) == 1
    assert resultado[0]['id_lote'] == 'B'
    assert resultado[0]['cantidad_utilizada'] == 5
    assert resultado[0]['saldo_restante'] == 5

def test_TC_04():
    resultado = gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-02', 'stock': 8}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-25', 'stock': 8}], 3, '2025-06-01')
    assert len(resultado) == 1
    assert resultado[0]['id_lote'] == 'B'
    assert resultado[0]['cantidad_utilizada'] == 3
    assert resultado[0]['saldo_restante'] == 5

def test_TC_05():
    with pytest.raises(StockInsuficienteError) as exc_info:
        gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-20', 'stock': 5}, {'id_lote': 'B', 'fecha_vencimiento': '2025-07-10', 'stock': 5}], 20, '2025-06-01')
    assert 'Stock Insuficiente' in str(exc_info.value)

def test_TC_06():
    with pytest.raises(StockInsuficienteError) as exc_info:
        gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-02', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-03', 'stock': 10}], 5, '2025-06-01')
    assert 'Stock Insuficiente' in str(exc_info.value)

def test_TC_07():
    resultado = gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-03', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-30', 'stock': 10}], 10, '2025-06-01')
    assert len(resultado) == 1
    assert resultado[0]['id_lote'] == 'B'
    assert resultado[0]['cantidad_utilizada'] == 10
    assert resultado[0]['saldo_restante'] == 0

def test_TC_08():
    resultado = gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-10', 'stock': 3}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-18', 'stock': 4}, {'id_lote': 'C', 'fecha_vencimiento': '2025-07-05', 'stock': 10}], 12, '2025-06-01')
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
    with pytest.raises(StockInsuficienteError) as exc_info:
        gestionar_despacho([], 5, '2025-06-01')
    assert 'Stock Insuficiente' in str(exc_info.value)

def test_TC_10():
    resultado = gestionar_despacho([{'id_lote': 'A', 'fecha_vencimiento': '2025-06-04', 'stock': 10}, {'id_lote': 'B', 'fecha_vencimiento': '2025-06-15', 'stock': 4}, {'id_lote': 'C', 'fecha_vencimiento': '2025-06-28', 'stock': 10}], 6, '2025-06-01')
    assert len(resultado) == 2
    assert resultado[0]['id_lote'] == 'B'
    assert resultado[0]['cantidad_utilizada'] == 4
    assert resultado[0]['saldo_restante'] == 0
    assert resultado[1]['id_lote'] == 'C'
    assert resultado[1]['cantidad_utilizada'] == 2
    assert resultado[1]['saldo_restante'] == 8
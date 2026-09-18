# tests/test_validators.py
# tests/test_validators.py

from utils.validators import validar_inteiro, validar_valor

def test_validar_inteiro():
    # válidos
    assert validar_inteiro("123") is True
    assert validar_inteiro("0") is True
    assert validar_inteiro("") is True

    # inválidos
    assert validar_inteiro("-123") is False
    assert validar_inteiro(" 42 ") is False
    assert validar_inteiro("12.3") is False
    assert validar_inteiro("1e5") is False
    assert validar_inteiro("abc") is False


def test_validar_valor():
    # válidos
    assert validar_valor("123") is True
    assert validar_valor("0") is True
    assert validar_valor("0.0") is True
    assert validar_valor("-12") is True
    assert validar_valor("-12.5") is True
    assert validar_valor(".5") is True
    assert validar_valor("-0.5") is True
    assert validar_valor("") is True

    # inválidos
    assert validar_valor("12,5") is False
    assert validar_valor(" 42.0 ") is False
    assert validar_valor("1e5") is False
    assert validar_valor("abc") is False

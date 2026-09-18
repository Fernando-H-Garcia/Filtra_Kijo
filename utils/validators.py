# utils/validators.py

import re

def validar_inteiro(valor):
    """Valida se o valor é um inteiro positivo (>0) ou vazio."""
    if valor == "": return True
    if not valor.isdigit(): return False
    return int(valor) > 0

def validar_valor(valor):
    """Valida se o valor é numérico (inteiro ou decimal, positivo ou negativo)."""
    return bool(re.fullmatch(r"^-?\d*\.?\d*$", valor)) or valor == ""
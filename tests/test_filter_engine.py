# tests/test_filter_engine.py
import pandas as pd
from core.filter_engine import FilterEngine
from unittest.mock import MagicMock

# ============ TESTES PARA OPERAÇÃO "=" ============

def test_filtro_igual():
    df = pd.DataFrame([
        ["KIJO75", "00", "33"],
        ["KIJO71", "45", "102698"],
        ["KIJO64", "00", "33"]
    ])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "3"),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "33")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert resultado.iloc[0, 2] == "33"
    assert resultado.iloc[1, 2] == "33"


# ============ TESTES PARA OPERAÇÃO ">" ============

def test_filtro_maior_que():
    df = pd.DataFrame([
        ["KIJO75", "00", "50"],
        ["KIJO71", "45", "20"],
        ["KIJO64", "00", "100"]
    ])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "3"),
        "operacao": MagicMock(get=lambda: ">"),
        "valor": MagicMock(get=lambda: "40")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert float(resultado.iloc[0, 2]) > 40
    assert float(resultado.iloc[1, 2]) > 40


# ============ TESTES PARA OPERAÇÃO "Contém" ============

def test_filtro_contem_ponto():
    df = pd.DataFrame([
        ["KIJO75", "00", "2136.09136"],
        ["KIJO71", "45", "2111.0"],
        ["KIJO64", "00", "102324"]
    ])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "3"),
        "operacao": MagicMock(get=lambda: "Contém"),
        "valor": MagicMock(get=lambda: ".")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert "." in resultado.iloc[0, 2]
    assert "." in resultado.iloc[1, 2]


def test_filtro_contem_m3():
    df = pd.DataFrame([
        ["KIJO75", "00", "M3-2024"],
        ["KIJO71", "45", "MODEL-X"],
        ["KIJO64", "00", "M3_SPECIAL"]
    ])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "3"),
        "operacao": MagicMock(get=lambda: "Contém"),
        "valor": MagicMock(get=lambda: "M3")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert "M3" in resultado.iloc[0, 2]
    assert "M3" in resultado.iloc[1, 2]


def test_filtro_contem_inexistente():
    df = pd.DataFrame([
        ["KIJO75", "00", "102833"],
        ["KIJO71", "45", "999999"],
        ["KIJO64", "00", "102334"]
    ])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "3"),
        "operacao": MagicMock(get=lambda: "Contém"),
        "valor": MagicMock(get=lambda: "XYZ")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 0


# ============ TESTES DE COMPORTAMENTO ESPECIAL ============

def test_filtro_contem_vazio():
    df = pd.DataFrame([
        ["KIJO75", "00", "102833"],
        ["KIJO71", "45", "999999"],
        ["KIJO64", "00", "102334"]
    ])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "3"),
        "operacao": MagicMock(get=lambda: "Contém"),
        "valor": MagicMock(get=lambda: "")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 3


# ============ TESTES PARA MÚLTIPLAS CONDIÇÕES (AND) ============

def test_filtro_multiplas_condicoes():
    df = pd.DataFrame([
        ["KIJO75", "00", "33", "VC"],
        ["KIJO71", "45", "102698", "V4"],
        ["KIJO64", "00", "33", "VC"]
    ])
    
    cond1 = {
        "posicao": MagicMock(get=lambda: "3"),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "33")
    }
    
    cond2 = {
        "posicao": MagicMock(get=lambda: "4"),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "VC")
    }
    
    filtros = {"Filtro_1": [cond1, cond2]}
    
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert resultado.iloc[0, 2] == "33" and resultado.iloc[0, 3] == "VC"
    assert resultado.iloc[1, 2] == "33" and resultado.iloc[1, 3] == "VC"


# ============ NOVOS TESTES (COBERTURA EXTRA) ============

def test_filtro_diferente():
    df = pd.DataFrame([
        ["A", "10"],
        ["B", "20"],
        ["C", "30"]
    ])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "2"),
        "operacao": MagicMock(get=lambda: "!="),
        "valor": MagicMock(get=lambda: "20")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert all(resultado.iloc[:, 1] != "20")


def test_filtro_maior_ou_igual():
    df = pd.DataFrame([["A", "5"], ["B", "10"], ["C", "15"]])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "2"),
        "operacao": MagicMock(get=lambda: ">="),
        "valor": MagicMock(get=lambda: "10")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert all(resultado.iloc[:, 1].astype(int) >= 10)


def test_filtro_menor_ou_igual():
    df = pd.DataFrame([["A", "5"], ["B", "10"], ["C", "15"]])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "2"),
        "operacao": MagicMock(get=lambda: "<="),
        "valor": MagicMock(get=lambda: "10")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert all(resultado.iloc[:, 1].astype(int) <= 10)


def test_filtro_posicao_invalida():
    """Testa comportamento quando filtro referencia posição de coluna inexistente.
    Condições com posições inválidas devem falhar (mask=False), não devem quebrar.
    Se todas as condições falharem, nenhuma linha deve ser retornada.
    """

    # ===== Caso 1: 1 linha, 1 filtro com posição inválida =====
    df1 = pd.DataFrame([["KIJO75", "00", "33"]])
    condicao_mock1 = {
        "posicao": MagicMock(get=lambda: "999"),  # inexistente
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "33")
    }
    filtros1 = {"Filtro_1": [condicao_mock1]}
    resultado1 = FilterEngine.aplicar_filtros_com_validacao(df1, filtros1)
    assert len(resultado1) == 0, "Filtro com posição inválida deve retornar 0 linhas"

    # ===== Caso 2: múltiplas linhas, 1 filtro com posição inválida =====
    df2 = pd.DataFrame([["A", "1"], ["B", "2"]])
    condicao_mock2 = {
        "posicao": MagicMock(get=lambda: "5"),  # inexistente
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "X")
    }
    filtros2 = {"Filtro_1": [condicao_mock2]}
    resultado2 = FilterEngine.aplicar_filtros_com_validacao(df2, filtros2)
    assert len(resultado2) == 0, "Mesmo com múltiplas linhas, filtro inválido deve retornar 0 linhas"

    # ===== Caso 3: múltiplos filtros — um válido, um inválido (OR) =====
    df3 = pd.DataFrame([["KIJO75", "00", "33"], ["KIJO76", "01", "44"]])
    condicao_valida = {
        "posicao": MagicMock(get=lambda: "2"),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "00")
    }
    condicao_invalida = {
        "posicao": MagicMock(get=lambda: "999"),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "XYZ")
    }
    filtros3 = {
        "Filtro_Valido": [condicao_valida],
        "Filtro_Invalido": [condicao_invalida]
    }
    resultado3 = FilterEngine.aplicar_filtros_com_validacao(df3, filtros3)
    assert len(resultado3) == 1, "Deve retornar linhas do filtro válido (OR entre filtros)"
    assert resultado3.iloc[0, 1] == "00"



def test_sem_filtros_retorna_tudo():
    df = pd.DataFrame([["A", "1"], ["B", "2"]])
    filtros = {}
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    assert len(resultado) == len(df)


def test_valor_nao_numerico_em_comparacao():
    df = pd.DataFrame([["A", "X"], ["B", "Y"]])
    
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "2"),
        "operacao": MagicMock(get=lambda: ">"),
        "valor": MagicMock(get=lambda: "10")
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    # Nenhum valor é numérico → resultado deve ser vazio
    assert len(resultado) == 0

def test_excecao_em_condicao():
    df = pd.DataFrame([["A", "1"], ["B", "2"]])

    condicao_mock = {
        "posicao": MagicMock(get=lambda: iter(()).throw(Exception("erro"))),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "1"),
    }

    filtros = {"Filtro_1": [condicao_mock]}
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)

    # Deve engolir exceção e não quebrar
    assert isinstance(resultado, pd.DataFrame)


def test_multiplos_filtros_or():
    df = pd.DataFrame([
        ["A", "10"],
        ["B", "20"],
        ["C", "30"]
    ])
    
    cond1 = {
        "posicao": MagicMock(get=lambda: "2"),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "10")
    }
    
    cond2 = {
        "posicao": MagicMock(get=lambda: "2"),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: "30")
    }
    
    filtros = {"Filtro_1": [cond1], "Filtro_2": [cond2]}  # OR
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    assert len(resultado) == 2
    assert set(resultado.iloc[:, 1]) == {"10", "30"}

    
def test_filtro_erro_na_condicao():
    df = pd.DataFrame([["KIJO75", "00", "33"]])
    
    # Mock que lança exceção
    condicao_mock = {
        "posicao": MagicMock(get=lambda: "3"),
        "operacao": MagicMock(get=lambda: "="),
        "valor": MagicMock(get=lambda: None)  # None causa erro em .str.contains
    }
    
    filtros = {"Filtro_1": [condicao_mock]}
    
    resultado = FilterEngine.aplicar_filtros_com_validacao(df, filtros)
    
    # Deve ignorar a condição com erro e continuar
    assert len(resultado) == 0  # ou 1, dependendo da lógica
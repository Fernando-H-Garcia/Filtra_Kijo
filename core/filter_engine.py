# core/filter_engine.py  —  Filtra_KIJO_V_4_3_0
# Migração para Polars para Alta Performance

import polars as pl


class FilterEngine:

    @staticmethod
    def compilar_filtros(filtros):
        """Pré-processa filtros para otimizar execução por chunk."""
        filtros_compilados = {}
        for f_id, f_data in (filtros or {}).items():
            # Suporta tanto o formato novo {"condicoes": [...], "colunas_saida": [...]}
            # quanto o formato legado de lista direta [...]
            if isinstance(f_data, dict):
                condicoes = f_data.get("condicoes", [])
                colunas_saida = f_data.get("colunas_saida", None)
            else:
                condicoes = f_data
                colunas_saida = None

            condicoes_compiladas = []
            for c in condicoes:
                try:
                    pos = int(c["posicao"]) - 1
                    op = c["operacao"]
                    val = str(c["valor"]).strip()

                    # Permite buscar por vazio ("") apenas para igualdade e diferença
                    if val == "" and op not in ["=", "!="]:
                        continue

                    val_num = None
                    try:
                        val_num = float(val)
                    except ValueError:
                        pass

                    condicoes_compiladas.append({
                        "pos": pos,
                        "op": op,
                        "val": val,
                        "val_num": val_num
                    })
                except Exception:
                    pass
            if condicoes_compiladas:
                filtros_compilados[f_id] = {
                    "condicoes": condicoes_compiladas,
                    "colunas_saida": colunas_saida
                }
        return filtros_compilados

    @staticmethod
    def aplicar_filtros_compilados(df, filtros_compilados):
        """Aplica filtros previamente compilados usando Polars com limite fixo de 100 colunas."""
        if not filtros_compilados:
            return df

        # Se o DataFrame estiver vazio, retorna ele mesmo
        if df.height == 0:
            return df

        lista_expressoes_filtros = []

        for f_id, f_info in filtros_compilados.items():
            condicoes = f_info["condicoes"]
            expr_filtro = None
            
            for c in condicoes:
                pos = c["pos"]
                op = c["op"]
                val = c["val"]
                val_num = c["val_num"]
                
                # Mapeia diretamente usando o prefixo 'field_' de 0 a 99 (evita conflito com raw_kijo)
                if pos < 0 or pos >= 100:
                    cond_expr = pl.lit(False)
                else:
                    col_name = f"field_{pos}"
                    col_expr = pl.col(col_name)
                    
                    if op == "=":
                        if val_num is not None:
                            # Tenta comparar numericamente ou como string
                            cond_expr = (col_expr.cast(pl.Float64, strict=False) == val_num) | (col_expr == val)
                        else:
                            cond_expr = (col_expr == val)
                    elif op == "!=":
                        cond_expr = (col_expr != val)
                    elif op in [">", "<", ">=", "<="]:
                        col_num = col_expr.cast(pl.Float64, strict=False)
                        if val_num is None:
                            cond_expr = pl.lit(False)
                        elif op == ">": cond_expr = (col_num > val_num)
                        elif op == "<": cond_expr = (col_num < val_num)
                        elif op == ">=": cond_expr = (col_num >= val_num)
                        elif op == "<=": cond_expr = (col_num <= val_num)
                    elif op == "Contém":
                        cond_expr = col_expr.str.contains(val, literal=True)
                    else:
                        cond_expr = pl.lit(False)
                
                if expr_filtro is None:
                    expr_filtro = cond_expr
                else:
                    expr_filtro &= cond_expr
            
            if expr_filtro is not None:
                lista_expressoes_filtros.append(expr_filtro)
        
        if not lista_expressoes_filtros:
            return df.filter(pl.lit(False))

        # Une todos os filtros com OR
        expr_final = lista_expressoes_filtros[0]
        for e in lista_expressoes_filtros[1:]:
            expr_final |= e
            
        return df.filter(expr_final)
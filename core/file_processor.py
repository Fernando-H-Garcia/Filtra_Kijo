# core/file_processor.py  —  Filtra_KIJO_V_4_3_0
# Performance Extrema: Polars Batched Processing (Streaming)
# + Deduplicação Inteligente
# + Auditoria de Duplicatas

import logging
import os
import time
import gc

import polars as pl
import xxhash

from core.filter_engine import FilterEngine


class FileProcessor:

    def __init__(
        self,
        arquivos_selecionados,
        progress_callback=None,
        status_callback=None,
        filtros=None
    ):
        self.arquivos_selecionados = arquivos_selecionados
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.filtros = filtros or {}

        self.tamanho_total = 0
        self.tamanho_processado = 0
        self.ultima_atualizacao = time.time()

    # ==========================================================
    # PROCESSAMENTO NORMAL
    # ==========================================================

    def processar_e_exportar_em_chunks(
        self,
        formato,
        caminho_saida,
        chunksize=50000,
        max_workers=None,
        deduplicar=True,
        separar_arquivos=False
    ):

        import re
        def limpar_nome(nome):
            return re.sub(r'[\\/*?:"<>|]', "", nome)

        temp_csv_final = None
        temp_files_por_regra = {}

        try:

            inicio = time.time()

            total_linhas_processadas = 0
            total_linhas_filtradas = 0
            linhas_duplicadas = 0

            total_arquivos = len(self.arquivos_selecionados)

            hashes_vistos = set()

            if self.status_callback:
                self.status_callback(
                    "Iniciando motor Polars V3..."
                )

            self.tamanho_total = sum(
                os.path.getsize(a)
                for a in self.arquivos_selecionados
            )

            filtros_compilados = (
                FilterEngine.compilar_filtros(
                    self.filtros
                )
            )

            if separar_arquivos:
                dir_out = os.path.dirname(caminho_saida)
                ext = "." + formato.lower().replace(".", "")
                
                mapa_nomes = separar_arquivos if isinstance(separar_arquivos, dict) else {}
                nomes_vistos = set()
                paths_cleared = set()

                for f_id in self.filtros:
                    if f_id in mapa_nomes:
                        nome_regra = limpar_nome(mapa_nomes[f_id])
                    else:
                        nome_base = limpar_nome(self.filtros[f_id].get("nome", f_id))
                        nome_regra = nome_base
                        
                        contador = 2
                        while nome_regra in nomes_vistos:
                            nome_regra = f"{nome_base}_{contador}"
                            contador += 1
                            
                        nomes_vistos.add(nome_regra)

                    path_final = os.path.join(dir_out, f"{nome_regra}{ext}")
                    temp_path = path_final + ".temp.csv"
                    
                    temp_files_por_regra[f_id] = {
                        "final": path_final,
                        "temp": temp_path
                    }
                    
                    if temp_path not in paths_cleared:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                        paths_cleared.add(temp_path)
            else:
                temp_csv_final = caminho_saida + ".temp.csv"
                if os.path.exists(temp_csv_final):
                    os.remove(temp_csv_final)

            # ==================================================
            # LOOP ARQUIVOS
            # ==================================================

            for idx, arquivo in enumerate(
                self.arquivos_selecionados
            ):

                if self.status_callback:
                    self.status_callback(
                        f"Processando "
                        f"{os.path.basename(arquivo)} "
                        f"({idx+1}/{total_arquivos})..."
                    )

                tamanho_arquivo = os.path.getsize(
                    arquivo
                )

                try:

                    reader = pl.read_csv_batched(
                        arquivo,
                        has_header=False,
                        new_columns=["line"],
                        separator="\x01",
                        truncate_ragged_lines=True,
                        encoding="utf8-lossy",
                        low_memory=True,
                        quote_char=None,
                        batch_size=chunksize
                    )

                    while True:

                        batches = reader.next_batches(1)

                        if not batches:
                            break

                        df = batches[0]

                        if df.height == 0:
                            continue

                        # ======================================
                        # FILTRA KIJO
                        # ======================================

                        df_kijo_base = df.filter(
                            pl.col("line")
                            .str.contains("KIJO")
                        )

                        if df_kijo_base.height == 0:
                            continue

                        # ======================================
                        # EXTRAI KIJO
                        # ======================================

                        df_base = (
                            df_kijo_base.with_columns([
                                pl.col("line")
                                .str.extract(
                                    r"(KIJO.*)",
                                    1
                                )
                                .alias("raw_kijo"),
                                pl.col("line")
                                .str.extract(
                                    r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
                                    1
                                )
                                .fill_null("")
                                .alias("timestamp")
                            ])
                        )

                        # ======================================
                        # SPLIT
                        # ======================================

                        max_cols = 100 # caso exista algum KIJO com mais de 100 colunas isso deverá ser alterado, nesse momento esse valor é muito supeiror ao maior kijo da documentação 

                        df_cols = (
                            df_base.select(
                                pl.col("raw_kijo")
                                .str.split(",")
                                .list.eval(
                                    pl.element()
                                    .str.strip_chars()
                                )
                                .alias("parts")
                            )
                            .select(
                                pl.col("parts")
                                .list.to_struct(
                                    upper_bound=max_cols
                                )
                            )
                            .unnest("parts")
                        )

                        rename_map = {}

                        for i, col in enumerate(
                            df_cols.columns
                        ):
                            rename_map[col] = (
                                f"field_{i}"
                            )

                        df_cols = df_cols.rename(
                            rename_map
                        )

                        # ======================================
                        # CONCAT
                        # ======================================

                        df_temp = pl.concat(
                            [
                                df_cols,
                                df_base.select(
                                    "raw_kijo",
                                    "timestamp"
                                )
                            ],
                            how="horizontal"
                        )

                        batch_processadas = (
                            df_temp.height
                        )

                        if batch_processadas == 0:
                            continue

                        total_linhas_processadas += (
                            batch_processadas
                        )

                        # ======================================
                        # FILTROS E FORMATAÇÃO DINÂMICA DE COLUNAS
                        # ======================================

                        linhas_filtradas_por_regra = {f_id: [] for f_id in filtros_compilados}

                        for f_id, f_info in filtros_compilados.items():
                            filtro_singular = {f_id: f_info}
                            df_regra = FilterEngine.aplicar_filtros_compilados(df_temp, filtro_singular)
                            
                            if df_regra.height == 0:
                                continue
                            
                            colunas_saida = f_info.get("colunas_saida", None)
                            timestamps_regra = df_regra["timestamp"].to_list()
                            
                            if colunas_saida is not None:
                                for ts, kijo_original in zip(timestamps_regra, df_regra["raw_kijo"].to_list()):
                                    parts = [p.strip() for p in kijo_original.split(",")]
                                    parts_filtradas = [parts[i] for i in colunas_saida if i >= 0 and i < len(parts)]
                                    linhas_filtradas_por_regra[f_id].append((ts, ",".join(parts_filtradas)))
                            else:
                                for ts, kijo in zip(timestamps_regra, df_regra["raw_kijo"].to_list()):
                                    linhas_filtradas_por_regra[f_id].append((ts, kijo))

                        # ======================================
                        # DEDUPLICAÇÃO E SALVAMENTO
                        # ======================================

                        if separar_arquivos:
                            for f_id, linhas_regra in linhas_filtradas_por_regra.items():
                                if not linhas_regra:
                                    continue
                                
                                temp_file = temp_files_por_regra[f_id]["temp"]
                                linhas_out = []
                                
                                if deduplicar:
                                    for ts, linha in linhas_regra:
                                        h = xxhash.xxh64(linha).intdigest()
                                        if h not in hashes_vistos:
                                            hashes_vistos.add(h)
                                            linhas_out.append((ts, linha))
                                        else:
                                            linhas_duplicadas += 1
                                else:
                                    linhas_out = linhas_regra
                                
                                if not linhas_out:
                                    continue
                                    
                                total_linhas_filtradas += len(linhas_out)
                                timestamps_out = [t[0] for t in linhas_out]
                                dados_out = [t[1] for t in linhas_out]
                                df_out = pl.DataFrame({"timestamp": timestamps_out, "raw_kijo": dados_out})
                                with open(temp_file, "ab") as f_out:
                                    df_out.write_csv(f_out, include_header=False, separator="\x01", quote_style="never")
                        else:
                            linhas_filtradas_no_batch = []
                            for linhas in linhas_filtradas_por_regra.values():
                                linhas_filtradas_no_batch.extend(linhas)
                            
                            if not linhas_filtradas_no_batch:
                                continue
                                
                            linhas_out = []
                            if deduplicar:
                                for ts, linha in linhas_filtradas_no_batch:
                                    h = xxhash.xxh64(linha).intdigest()
                                    if h not in hashes_vistos:
                                        hashes_vistos.add(h)
                                        linhas_out.append((ts, linha))
                                    else:
                                        linhas_duplicadas += 1
                            else:
                                linhas_out = linhas_filtradas_no_batch
                                
                            if not linhas_out:
                                continue
                                
                            total_linhas_filtradas += len(linhas_out)
                            timestamps_out = [t[0] for t in linhas_out]
                            dados_out = [t[1] for t in linhas_out]
                            df_out = pl.DataFrame({"timestamp": timestamps_out, "raw_kijo": dados_out})
                            with open(temp_csv_final, "ab") as f_out:
                                df_out.write_csv(f_out, include_header=False, separator="\x01", quote_style="never")

                except Exception as e:

                    logging.error(
                        f"Falha no arquivo "
                        f"{arquivo}: {e}"
                    )

                self.tamanho_processado += (
                    tamanho_arquivo
                )

                self.atualizar_progresso()

            # ==================================================
            # FINALIZAÇÃO
            # ==================================================

            if total_linhas_filtradas == 0:
                raise ValueError(
                    "Nenhum dado encontrado."
                )

            if self.status_callback:
                self.status_callback(
                    "Finalizando exportação..."
                )

            if separar_arquivos:
                for f_id, paths in temp_files_por_regra.items():
                    t_file = paths["temp"]
                    f_file = paths["final"]
                    if os.path.exists(t_file):
                        # Ordena por data/hora do cabeçalho original
                        if self.status_callback:
                            self.status_callback("Ordenando por data/hora...")
                        df_sort = pl.read_csv(
                            t_file,
                            has_header=False,
                            new_columns=["timestamp", "raw_kijo"],
                            separator="\x01",
                            truncate_ragged_lines=True,
                            quote_char=None
                        )
                        df_sort = df_sort.sort("timestamp")
                        df_sorted = df_sort.select("raw_kijo")
                        df_sorted.write_csv(t_file, include_header=False, quote_style="never")

                        if "TXT" in formato or "CSV" in formato:
                            os.replace(t_file, f_file)
                        elif "Excel" in formato:
                            self._converter_csv_para_excel(f_file, t_file)
                            os.remove(t_file)
            else:
                if not temp_csv_final or not os.path.exists(temp_csv_final):
                    raise ValueError("Nenhum dado encontrado.")

                # Ordena por data/hora do cabeçalho original
                if self.status_callback:
                    self.status_callback("Ordenando por data/hora...")
                df_sort = pl.read_csv(
                    temp_csv_final,
                    has_header=False,
                    new_columns=["timestamp", "raw_kijo"],
                    separator="\x01",
                    truncate_ragged_lines=True,
                    quote_char=None
                )
                df_sort = df_sort.sort("timestamp")
                df_sorted = df_sort.select("raw_kijo")
                df_sorted.write_csv(temp_csv_final, include_header=False, quote_style="never")

                if (
                    "TXT" in formato
                    or "CSV" in formato
                ):
                    os.replace(
                        temp_csv_final,
                        caminho_saida
                    )
                    temp_csv_final = None
                elif "Excel" in formato:
                    self._converter_csv_para_excel(
                        caminho_saida,
                        temp_csv_final
                    )

            duracao = time.time() - inicio

            print("\n========== RESUMO ==========")
            print(
                f"Linhas encontradas........: "
                f"{total_linhas_processadas}"
            )
            print(
                f"Linhas duplicadas removidas: "
                f"{linhas_duplicadas}"
            )
            print(
                f"Linhas finais exportadas..: "
                f"{total_linhas_filtradas}"
            )
            print("============================\n")

            return {
                "sucesso": True,
                "linhas_filtradas":
                    total_linhas_filtradas,
                "linhas_processadas":
                    total_linhas_processadas,
                "linhas_duplicadas":
                    linhas_duplicadas,
                "total_arquivos":
                    total_arquivos,
                "duracao":
                    duracao,
            }

        except Exception as e:

            logging.error(
                f"Erro na exportação V3: {e}"
            )

            raise

        finally:

            if separar_arquivos:
                for paths in temp_files_por_regra.values():
                    if os.path.exists(paths["temp"]):
                        try:
                            os.remove(paths["temp"])
                        except:
                            pass
            else:
                if (
                    temp_csv_final
                    and os.path.exists(
                        temp_csv_final
                    )
                ):
                    try:
                        os.remove(temp_csv_final)
                    except:
                        pass
            
            # Forçar liberação de memória RAM para o SO
            gc.collect()

    # ==========================================================
    # ANALISADOR DE DUPLICADAS
    # ==========================================================

    def processar_apenas_duplicadas(
        self,
        formato,
        caminho_saida,
        chunksize=50000
    ):

        temp_csv_final = caminho_saida + ".temp.csv"

        try:

            inicio = time.time()

            total_arquivos = len(
                self.arquivos_selecionados
            )

            total_linhas = 0

            contagem_hashes = {}

            # ==============================================
            # PASSAGEM 1
            # CONTA HASHES
            # ==============================================

            if self.status_callback:
                self.status_callback(
                    "Analisando duplicadas "
                    "(Passagem 1/2)..."
                )

            self.tamanho_total = sum(
                os.path.getsize(a)
                for a in self.arquivos_selecionados
            )

            self.tamanho_processado = 0

            for idx, arquivo in enumerate(
                self.arquivos_selecionados
            ):

                tamanho_arquivo = os.path.getsize(
                    arquivo
                )

                reader = pl.read_csv_batched(
                    arquivo,
                    has_header=False,
                    new_columns=["line"],
                    separator="\x01",
                    truncate_ragged_lines=True,
                    encoding="utf8-lossy",
                    low_memory=True,
                    quote_char=None,
                    batch_size=chunksize
                )

                while True:

                    batches = reader.next_batches(1)

                    if not batches:
                        break

                    df = batches[0]

                    if df.height == 0:
                        continue

                    df_kijo = df.filter(
                        pl.col("line")
                        .str.contains("KIJO")
                    ).with_columns(
                        pl.col("line")
                        .str.extract(r"(KIJO.*)", 1)
                        .alias("raw_kijo")
                    )

                    if df_kijo.height == 0:
                        continue

                    linhas = (
                        df_kijo["raw_kijo"]
                        .to_list()
                    )

                    total_linhas += len(linhas)

                    for linha in linhas:

                        h = (
                            xxhash
                            .xxh64(linha)
                            .intdigest()
                        )

                        contagem_hashes[h] = (
                            contagem_hashes.get(h, 0)
                            + 1
                        )

                self.tamanho_processado += (
                    tamanho_arquivo
                )

                self.atualizar_progresso()

            # ==============================================
            # HASHES DUPLICADOS
            # ==============================================

            hashes_duplicados = {
                h for h, c
                in contagem_hashes.items()
                if c > 1
            }

            total_duplicadas = len(
                hashes_duplicados
            )

            if total_duplicadas == 0:
                raise ValueError(
                    "Nenhuma duplicata encontrada."
                )

            # ==============================================
            # PASSAGEM 2
            # EXPORTA DUPLICADAS
            # ==============================================

            if self.status_callback:
                self.status_callback(
                    "Exportando duplicadas "
                    "(Passagem 2/2)..."
                )

            self.tamanho_processado = 0

            if os.path.exists(temp_csv_final):
                os.remove(temp_csv_final)

            linhas_exportadas = 0

            for idx, arquivo in enumerate(
                self.arquivos_selecionados
            ):

                tamanho_arquivo = os.path.getsize(
                    arquivo
                )

                reader = pl.read_csv_batched(
                    arquivo,
                    has_header=False,
                    new_columns=["line"],
                    separator="\x01",
                    truncate_ragged_lines=True,
                    encoding="utf8-lossy",
                    low_memory=True,
                    quote_char=None,
                    batch_size=chunksize
                )

                while True:

                    batches = reader.next_batches(1)

                    if not batches:
                        break

                    df = batches[0]

                    if df.height == 0:
                        continue

                    df_kijo = df.filter(
                        pl.col("line")
                        .str.contains("KIJO")
                    ).with_columns(
                        pl.col("line")
                        .str.extract(r"(KIJO.*)", 1)
                        .alias("raw_kijo")
                    )

                    if df_kijo.height == 0:
                        continue

                    linhas_originais = []
                    kijo_para_ordem = []

                    for original_line, kijo_str in zip(
                        df_kijo["line"].to_list(),
                        df_kijo["raw_kijo"].to_list()
                    ):

                        h = (
                            xxhash
                            .xxh64(kijo_str)
                            .intdigest()
                        )

                        if h in hashes_duplicados:

                            linhas_originais.append(
                                original_line
                            )
                            kijo_para_ordem.append(
                                kijo_str
                            )

                    if linhas_originais:

                        linhas_exportadas += len(
                            linhas_originais
                        )

                        nome_arquivo = os.path.basename(arquivo)

                        df_out = pl.DataFrame({
                            "filename": [nome_arquivo] * len(linhas_originais),
                            "raw_kijo": kijo_para_ordem,
                            "original_line": linhas_originais
                        })

                        with open(
                            temp_csv_final,
                            "ab"
                        ) as f_out:

                            df_out.write_csv(
                                f_out,
                                include_header=False,
                                separator="\x01",
                                quote_style="never"
                            )

                self.tamanho_processado += (
                    tamanho_arquivo
                )

                self.atualizar_progresso()

            # ==============================================
            # FINALIZAÇÃO
            # ==============================================

            if self.status_callback:
                self.status_callback("Ordenando duplicadas para agrupamento...")

            try:
                df_out = pl.read_csv(
                    temp_csv_final,
                    has_header=False,
                    new_columns=["filename", "raw_kijo", "original_line"],
                    separator="\x01",
                    truncate_ragged_lines=True,
                    quote_char=None
                )
                
                # Ordena primeiro pelo KIJO para manter as duplicadas juntas,
                # e depois pelo arquivo/linha
                df_out = df_out.sort(["raw_kijo", "filename", "original_line"])
                
                # Concatena organizando os espaços (Nome do arquivo e a linha original)
                df_final = df_out.select(
                    (pl.col("filename") + " " + pl.col("original_line")).alias("out")
                )
                
                df_final.write_csv(
                    temp_csv_final,
                    include_header=False,
                    quote_style="never"
                )
            except Exception as e:
                logging.warning(f"Falha ao ordenar duplicadas: {e}")

            os.replace(
                temp_csv_final,
                caminho_saida
            )

            temp_csv_final = None

            duracao = time.time() - inicio

            print("\n====== DUPLICADAS ======")
            print(
                f"Linhas analisadas.....: "
                f"{total_linhas}"
            )
            print(
                f"Tipos duplicados......: "
                f"{total_duplicadas}"
            )
            print(
                f"Ocorrências exportadas: "
                f"{linhas_exportadas}"
            )
            print("========================\n")

            return {
                "sucesso": True,
                "linhas_processadas":
                    total_linhas,
                "tipos_duplicados":
                    total_duplicadas,
                "linhas_exportadas":
                    linhas_exportadas,
                "duracao":
                    duracao,
            }

        except Exception as e:

            logging.error(
                f"Erro na análise de duplicadas: {e}"
            )

            raise

        finally:

            if (
                temp_csv_final
                and os.path.exists(
                    temp_csv_final
                )
            ):
                try:
                    os.remove(temp_csv_final)
                except:
                    pass

            gc.collect()

    # ==========================================================
    # EXCEL
    # ==========================================================

    def _converter_csv_para_excel(
        self,
        caminho_saida,
        temp_csv
    ):

        if self.status_callback:
            self.status_callback(
                "Convertendo para Excel..."
            )

        df_raw = pl.read_csv(
            temp_csv,
            has_header=False,
            new_columns=["line"],
            separator="\x01",
            truncate_ragged_lines=True,
            quote_char=None
        )

        if df_raw.height == 0:

            df_empty = pl.DataFrame()
            df_empty.write_excel(
                caminho_saida
            )

            return

        max_cols = (
            df_raw.select(
                pl.col("line")
                .str.count_matches(",")
                .max()
            )
            .to_series()[0]
        )

        if max_cols is None:
            max_cols = 0

        max_cols += 1

        df_excel = (
            df_raw.select(
                pl.col("line")
                .str.split(",")
                .list.eval(
                    pl.element()
                    .str.strip_chars()
                )
                .alias("parts")
            )
            .select(
                pl.col("parts")
                .list.to_struct(
                    upper_bound=max_cols
                )
            )
            .unnest("parts")
        )

        df_excel.columns = [
            str(i + 1)
            for i in range(
                len(df_excel.columns)
            )
        ]

        df_excel.write_excel(
            caminho_saida
        )

    # ==========================================================
    # PROGRESSO
    # ==========================================================

    def atualizar_progresso(self):

        if (
            self.tamanho_total > 0
            and self.progress_callback
        ):

            progresso = (
                5
                + (
                    (
                        self.tamanho_processado
                        / self.tamanho_total
                    ) * 90
                )
            )

            self.progress_callback(
                min(progresso, 100)
            )
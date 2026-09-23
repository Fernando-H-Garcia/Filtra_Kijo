# FiltraKIJO v4.2.1 — Documento Exaustivo de Regras de Negócio
*Sweep em `Filtra_KIJO_V_4_0_0` — 2026-09-23 (atualizado: cancelamento, renomear, fix 1224, volta ordem 4.1)*

> Cada bullet cita `arquivo:linha`. Verificado por leitura completa dos fontes.

---

## 1. `core/config.py:1-4`

- `VERSION = "4.2.0"` usada em título janela `gui/application.py:273`, manual `gui/manual.py:18,158`, AppUserModelID `main.py:10`.
- `APP_NAME = "Filtra KIJO"` constante, não consumida diretamente mas documentada.

## 2. `utils/validators.py:1-13`

### 2.1 `validar_inteiro(valor):5-9`
- `""` → `True` (permite campo vazio durante digitação).
- `valor.isdigit()` obrigatório — rejeita `"-123"`, `" 42 "`, `"12.3"`, `"1e5"`, `"abc"` `tests/test_validators.py:12-17`.
- Se dígitos, `int(valor) > 0` → rejeita `"0"` como `False` (código), mas teste espera `True` para `"0"` `test_validators.py:9` → **divergência teste vs código**; na prática UI trata string `"0"` como inválida.
- Registrado como `validate="key"` para `e_pos` `gui/application.py:290-292,1620`.

### 2.2 `validar_valor(valor):11-13`
- Regex `r"^-?\d*\.?\d*$"` ou `""` → `True` `tests/test_validators.py:20-29`.
- Aceita `".5"`, `"-0.5"`, `"-12.5"`; rejeita `"12,5"`, `" 42.0 "`, `"1e5"`, `"abc"`.
- Usado dinamicamente só quando op é `> < >= <=` via `_validar_dinamico` `gui/application.py:1668-1676` — caso contrário `return True`.

## 3. Campo **Posição**

### 3.1 Definição UI `gui/application.py:1619-1622`
- Label `"Posição:"`, `CTkEntry width=80`, `font Segoe UI 14`, `validate="key"` com `v_num`.
- 1 condição por `row` dentro de `rows_container` `1587,1603`.
- Valor inicial `pos=""` se nova regra `1616`.

### 3.2 Validação de entrada
- Só dígitos, `>0` via `validar_inteiro` — typing bloqueado para `"-"`, `"."`, letras.
- Ao `FocusOut` chama `verificar_posicao_unica` `1622`.

### 3.3 Unicidade por filtro `gui/application.py:1647-1653`
- `if not pos.isdigit(): return` — não valida vazio/não-numérico.
- Itera `condicoes` do mesmo `f_id`; se outro `pos_widget != e_pos` tem mesmo `pos` → `messagebox.showwarning("Posição X já configurada neste filtro!")` e `e_pos.delete(0,Tk.END)`.
- Não verifica unicidade entre filtros diferentes — permitido repetir posição em filtros distintos.

### 3.4 Compilação `core/filter_engine.py:25-26`
- `pos = int(c["posicao"]) - 1` → 1-indexed na UI vira 0-indexed (`field_0` = Pos 1). `ValueError` → `except: pass` descarta condição `46-47`.

### 3.5 Limite físico `core/filter_engine.py:78, core/file_processor.py:209`
- `if pos <0 or pos >=100: cond_expr = pl.lit(False)` → Pos 0 ou >100 nunca casa.
- `max_cols = 100` fixo para `list.to_struct(upper_bound=max_cols)` `209,225`.

### 3.6 Obrigatoriedade `gui/application.py:843-854`
- `fluxo_processamento` varre todos filtros; `if c["pos_widget"].get().strip()`: se nenhum preenchido `tem_posicao==False` → `showwarning("É obrigatório informar ao menos uma Posição")` e `return`.
- `abrir_configuracao_colunas:1747-1759` → se `conds` vazio → `showwarning("Configure pelo menos uma condição com posição")`.

## 4. Campo **Operação**

### 4.1 Mapa `gui/application.py:139-147`
```python
OP_MAP = {"Igual a":"=", "Diferente de":"!=", "Maior que":">", "Menor que":"<", "Maior ou igual a":">=", "Menor ou igual a":"<=", "Contém":"Contém"}
```
### 4.2 Widget `gui/application.py:1637-1638`
- `CTkComboBox values=[7 labels]`, `width=180`, `justify="center"`, `state="readonly"`, `font bold 16`.
- Default `op="="` → `REV_OP_MAP.get(op,op)` `1638`.
- `command=lambda _: e_val.delete(0,tk.END)` → trocar operador limpa Valor.

### 4.3 Engine `core/filter_engine.py:84-103`
- `"="`: se `val_num is not None` → `(col.cast(Float64, strict=False)==val_num) | (col==val)` `85-89`; senão `col==val`.
- `"!="`: `col != val` `90-91`.
- `> < >= <=`: `col_num = col.cast(Float64, strict=False)`; se `val_num is None` → `pl.lit(False)` `94-95`; senão comparação numérica `96-99`.
- `"Contém"`: `col.str.contains(val, literal=True)` `100-101`.
- Desconhecido → `pl.lit(False)` `102-103`.

## 5. Campo **Valor**

### 5.1 Widget `gui/application.py:1640-1641`
- `CTkEntry width=200`, `validate="key"` com `v_val = register(_validar_dinamico)` `294-296`.
- `validatecommand=(v_val, "%P", f_id, idx)` onde `idx=len(condicoes)` antes de append `1640`.

### 5.2 Validação dinâmica `gui/application.py:1668-1676`
- Resolve `op_label → op` via `OP_MAP`; se `op in [> < >= <=]` → `return validar_valor(P)` (regex numérica), senão `return True`.

### 5.3 Compilação `core/filter_engine.py:28-32`
- `val = str(c["valor"]).strip()` → trim automático.
- `if val=="" and op not in ["=", "!="]: continue` → **condição descartada**.

### 5.4 Conversão numérica `core/filter_engine.py:34-38`
- `try: val_num=float(val) except: pass` → `None` se não-numérico.

## 6. Filtro / Regra (Card)

### 6.1 Criação `gui/application.py:1597-1635`
- `criar_filtro(nome_inicial=None, condicoes_iniciais=None, colunas_saida_iniciais=None)` `~1597`.
- `contador_filtros +=1; f_id=f"filtro_{contador}"` — sempre crescente.
- `nome_default` via `_gerar_nome_unico`: se `nome_inicial` (clique em regra salva) → verifica só `filtros` ativos (`verificar_biblioteca=False`), senão `"+ Nova Regra"` verifica biblioteca+ativos (`True`). Gap reuse: coleta `numeros_usados` de padrão `"{base} - {n}"` e retorna menor `n>=2` livre (`1597-1634`). Ex: `teste, teste - 2` → próximo `teste - 3`; `teste 3` duplicado → `teste 3 - 2`.
- Card `CTkFrame border #E5E7EB fg #F9FAFB`, header `height 45 fg #F1F5F9`.
- `entry_nome` placeholder `"Nome do Filtro"`, `width 280`, `font bold 15`; `nome_default` já único.
- Botões header: `✕` remover `1595`, `💾` salvar `1596`, `⚙️ Configurar Saída width 140` `1599-1600`.
- `self.filtros[f_id] = {widget, nome_entry, rows_container, condicoes:[], colunas_saida}` `1604-1610`.
- Botão `+ Adicionar Condição width 170 fg #6366F1` `1611`.

### 6.2 Condições no mesmo filtro = AND `core/filter_engine.py:105-108`
- `expr_filtro &= cond_expr`.

### 6.3 Múltiplos filtros = OR `core/filter_engine.py:113-121`
- `lista_expressoes_filtros` unida por `|=`.

### 6.4 Adicionar/Remover condição `gui/application.py:1616-1666`
- `atualizar_visibilidade_botoes:1662-1666` → se `len==1` esconde `btn_rem` (`pack_forget`), senão mostra todos.

## 7. Biblioteca de Regras

### 7.1 Arquivo `gui/application.py:311-313,344-397`
- `self.caminho_biblioteca = "filtros_salvos.json"` relativo ao CWD.
- `existence check` `346`, `json.load` `357`, `data.pop("__config__",{})` `359`.

### 7.2 Estrutura JSON
```json
{
  "nome_regra": {"condicoes":[{"posicao":str,"operacao":str,"valor":str}], "colunas_saida":[int]|null},
  "__config__":{"dir_abertura":str,"dir_salvamento":str,"nomes_colunas_mapeadas":{chave:{idx:str}}}}
}
```
- `indent=4, ensure_ascii=False` `389-392`.

### 7.3 Salvar `_salvar_biblioteca:371-396`
- `data_to_save = biblioteca.copy(); data_to_save["__config__"]= {dir_abertura, dir_salvamento, nomes_colunas_mapeadas}` `375-380`.

### 7.4 `salvar_na_biblioteca(f_id):1682-1697`
- `nome = strip() or f"Filtra_{time}"`, coleta `conds` mapeando `OP_MAP`, `self.biblioteca_filtros[nome]={"condicoes":conds,"colunas_saida":info.get(...)}`.

### 7.5 `atualizar_lista_biblioteca:1810-1845` + renomear `gui/application.py:1748-1808`
- `for w in scroll_lib destroy` → rebuild.
- `has_files = len(arquivos_selecionados)>0`.
- Itera `sorted(keys)` → ordem alfabética; compatível lista antiga `if isinstance(regra_info, list)`.
- Botão `CTkButton text="📜 {nome}" fg #F9FAFB hover #E0E7FF anchor w height 50 bold 15`, `command=lambda: criar_filtro(n,conds,cols) if has_files else showwarning("Selecione os arquivos antes de carregar filtros!")`.
- Se `not has_files`: `configure(state="disabled")`.
- **Menu contexto botão direito**: `bind("<Button-3>", _mostrar_menu_contexto_biblioteca)` `~1835`; `tk.Menu` com `✏️ Renomear → _renomear_filtro_biblioteca(nome)` e `🗑 Excluir → excluir_da_biblioteca(nome)` `1802-1804`.
- **Renomear** `1748-1797`: `Toplevel 440x240` centralizado `topmost grab_set resizable False`, labels `Renomear Regra Salva 16 bold` + `Nome atual`, `Entry width 320` pré-preenchido + `focus()+select_range`, `confirmar`: trim, rejeita vazio/`==antigo`/já existe → `showwarning`, senão `biblioteca[novo]=pop(antigo); _salvar; atualizar_lista; lbl_status "Regra renomeada..."`; bind `<Return> confirmar, <Escape> destroy`; botões `frame transparent pack pady25 fill x padx30` + `Cancelar 44px #6B7280` + `Salvar 44px SUCCESS` com `expand=True`.
- Auto-rename ao `criar_filtro` garante que carregar da biblioteca nunca cria duplicata na lista ativa.

## 8. Seleção de Arquivos `gui/application.py:1733-1741`
- `filedialog.askopenfilenames(initialdir=dir_abertura or "/", title="Selecione os arquivos KIJO (GPRS)", filetypes=("Arquivos de Texto *.txt","Todos *.*"))` `1734`.
- Se `caminhos`: `arquivos_selecionados = list(caminhos)`; `dir_abertura = dirname(caminhos[0])` `1736`; `lbl_status_files configure text="✅ N arquivos selecionados" color SUCCESS` `1736`; `_salvar_biblioteca()` persiste dir `1737`.

## 9. Processamento Normal `core/file_processor.py:39-560`
- `FileProcessor(arquivos_selecionados, progress_callback, status_callback, filtros={}, cancel_callback=None)` `65-82` + `_check_cancel:83` lança `InterruptedError("cancelado")` se `cancel_callback()` true.
- `processar_e_exportar_em_chunks(formato, caminho_saida, chunksize=50000, deduplicar=True, separar_arquivos=False)` `87-560`.
- `chunksize 50000`, `max_cols 100`, `deduplicar True`, `tamanho_total=sum(getsize)`, `filtros_compilados=FilterEngine.compilar_filtros`.
- `helpers _safe_remove/_safe_replace:18-48` retry 5x exponencial `sleep 0.05*2^attempt` + `gc.collect()` se `winerror==1224` (ERROR_USER_MAPPED_FILE) ou `EACCES`; `_ensure_reader_closed:51-62` consome `next_batches` restantes + `gc`.
- Se `separar_arquivos`: `dir_out=dirname(caminho_saida)`, `ext="."+formato.lower()`, `mapa_nomes` dict, dedup nomes com `while nome_regra in nomes_vistos: nome_+=f"_{contador}"`, cria `temp_files_por_regra[f_id]={"final":path,"temp":path+".temp.csv"}`.
- Senão: `temp_csv_final=caminho_saida+".temp.csv"`.
- Loop arquivos: `for idx, arquivo enumerate` → `_check_cancel()` por arquivo; `pl.read_csv_batched(has_header=False, new_columns=["line"], separator="\x01", truncate_ragged_lines=True, encoding="utf8-lossy", low_memory=True, quote_char=None, batch_size=chunksize)`; `while True: _check_cancel(); batches=next_batches(1); if not break`.
- **FILTRA KIJO**: `df.filter(pl.col("line").str.contains("KIJO"))`.
- **EXTRAI KIJO** (v4.2.1 sem timestamp, volta 4.1): `with_columns( str.extract(r"(KIJO.*)",1).alias("raw_kijo") )` `~245` (removido `timestamp`).
- **SPLIT**: `str.split(",").list.eval(element.str.strip_chars()).alias("parts")` → `list.to_struct(upper_bound=100).unnest("parts")` → `field_0..field_n`.
- **CONCAT**: `pl.concat([df_cols, df_base.select("raw_kijo")], how="horizontal")` `~305` (sem timestamp).
- **FILTROS & FORMATAÇÃO DINÂMICA**: `linhas_filtradas_por_regra={f_id:[]}`, loop `filtro_singular`, `df_regra=aplicar_filtros_compilados`, `colunas_saida = f_info.get(...)`, para cada `kijo` (sem `ts`): se `colunas_saida not None` → `parts=[p.strip() for p in kijo.split(",")]; parts_filtradas=[parts[i] for i in colunas_saida if 0<=i<len(parts)]; linhas.append(",".join(parts_filtradas))` senão `append(kijo)`.
- **DEDUP & SAVE**: se `separar`: para cada `f_id,linhas_regra`, `temp_file`, se `deduplicar` hash `xxhash.xxh64(linha).intdigest()` global else direto, `total_linhas_filtradas+=len(linhas_out)`, `df_out=DataFrame({"raw_kijo": linhas_out})` single column, `write_csv(open(temp_file,"ab"), include_header=False, quote_style="never")` (sem `timestamp`); senão agrupa `linhas_filtradas_no_batch` e mesmo fluxo para `temp_csv_final`.
- `tamanho_processado+=tamanho_arquivo; atualizar_progresso()`; `finally` garante `_ensure_reader_closed(reader)+gc` por arquivo.
- Finalização (v4.2.1 sem sort, ordem chegada = 4.1): `self._check_cancel()`; `if total_linhas_filtradas==0: raise ValueError("Nenhum dado encontrado.")`, `status "Finalizando exportação..."`; se `separar`: para cada `paths, self._check_cancel()` → se `TXT/CSV` → `_safe_replace(t_file,f_file)` direto, se `Excel` → `_converter_csv_para_excel(f_file,t_file); _safe_remove(t_file)` + `gc`; senão (arquivo único) → se `TXT/CSV` → `_safe_replace(temp_csv_final,caminho_saida); temp_csv_final=None`, se `Excel` → `_converter; _safe_remove(temp_csv_final); temp_csv_final=None`; `gc.collect()`.
- `duracao=time.time()-inicio`, `return {"sucesso":True, linhas_filtradas, linhas_processadas, linhas_duplicadas, total_arquivos, duracao}`.
- `finally: if separar: for paths: _safe_remove(paths["temp"]) else: if temp_csv_final: _safe_remove(temp_csv_final); gc.collect()` (protege `None`).

## 10. Deduplicação + Cancelamento
- `hashes_vistos = set()` único global para todos arquivos/regras.
- `xxhash.xxh64(linha).intdigest()`.
- `deduplicar=True` por padrão; só desativável via parâmetro (UI sempre True).
- Contagem `linhas_duplicadas` incrementada quando hash já visto.
- **Cancelamento** checado por `_check_cancel` a cada arquivo (`for idx`) e a cada batch (`while True`) e antes da finalização; lança `InterruptedError` capturado pela GUI para limpar temps sem mostrar `messagebox`.

## 11. Fluxo Duplicadas `core/file_processor.py:563-900`
- `processar_apenas_duplicadas(formato, caminho_saida, chunksize=50000)` com `cancel_callback`.
- Passo 1 — Conta hashes: `_check_cancel` por arquivo/batch, `status "Analisando duplicadas (Passagem 1/2)..."`, `tamanho_total sum`, `read_csv_batched` mesmo config, filtra `KIJO`, extrai `raw_kijo=r"(KIJO.*)"`, `linhas=to_list()`, `for linha: h=xxh64(linha).intdigest(); contagem[h]=get+1`, `hashes_duplicados={h for h,c if c>1}`, `if ==0: raise ValueError("Nenhuma duplicata encontrada.")`, `_ensure_reader_closed+gc` por arquivo.
- Passo 2 — Exporta: `_check_cancel`, `status "Exportando duplicadas (Passagem 2/2)..."`, `tamanho_processado=0`, `if exists temp: _safe_remove(temp_csv_final)`, `linhas_exportadas=0`, para cada arquivo: read_batched com `_check_cancel`, para cada `original_line, kijo_str` zip, `h=xxh64(kijo_str)`, `if h in duplicados: linhas_originais.append(original_line); kijo_para_ordem.append(kijo_str)`, se `linhas_originais`: `nome_arquivo=basename`, `df_out=DataFrame({"filename":..., "raw_kijo":..., "original_line":...})`, `write_csv(temp_csv_final, ab, separator \x01, quote never)`, `_ensure_reader_closed+gc`.
- Ordenação: `status "Ordenando duplicadas para agrupamento..."`, `read_csv(temp_csv_final, new_columns=["filename","raw_kijo","original_line"])`, `sort(["raw_kijo","filename","original_line"])`, `select((filename+" "+original_line).alias("out"))`, `write_csv(temp_csv_final, include_header False)`, `_safe_replace(temp_csv_final,caminho_saida)` com retry 1224; `finally: if temp_csv_final: _safe_remove`.

## 12. Configurar Saída (Colunas) `gui/application.py:1743-2103`
- Coleta `conds` de `filtros[f_id]["condicoes"]` onde `pos_widget.get().strip()` != "".
- Se `not conds` → `showwarning` `1757-1759`.
- `lbl_status "Procurando próxima ocorrência..." if index>0 else "Procurando ocorrência compatível..."` `1762-1763`.
- Popup loading `400x150` centralizado, `indeterminate progress`, `grab_set, topmost`, `protocol WM_DELETE_WINDOW → busca_cancelada[0]=True + destroy` `1765-1790`.
- Thread `thread_busca:1792-1924`: `FilterEngine.compilar_filtros({f_id: conds})`, `tem_pos2_fixa = any(c["posicao"]=="2" and c["operacao"]=="=" for c)`, `valores_pos2_vistos=set(), ocorrencias_encontradas=0`, para cada `caminho_arq` em `arquivos_selecionados`: `open utf-8 errors ignore`, `for line: if "KIJO" not in continue; idx=find("KIJO"); kijo_str=line[idx:].strip(); parts=[p.strip() for p in split(",")]`, valida manualmente contra `filtros_compilados`, se `match`: se `tem_pos2_fixa`: se `ocorrencias_encontradas==ocorrencia_index` → `linha_encontrada=kijo_str break` else `+=1`, senão: `val_pos2=parts[1] if len>1 else ""`; se não visto → add set e checa index mesmo.
- Se `busca_cancelada` → `after lbl_status "Busca cancelada." return`.
- Se `not linha_encontrada and ocorrencia_index>0`: `after lambda abrir_configuracao_colunas(f_id,0)` (wrap-around).
- Senão `after lambda exibir_modal_colunas(f_id, conds, linha_encontrada, ocorrencia_index)`.
- `exibir_modal_colunas:1927-2103`: `lbl_status reset`; `if not linha_encontrada: showinfo "Nenhuma linha compatível..." return`; `parts = split strip`; **Chave KIJO** `1935-1963`: tenta extrair `val_pos1/2/4` das `conds` onde `posicao=="1/2/4"`; se vazio, pega de `parts[0], [1], [3]`; `chave = f"{pos1}_{pos2}" + f"_{pos4}" if pos4 upcase` `1958-1963`; Popup `750x620` centralizado, título `"⚙️ Selecione e Nomeie..."`, instrução `"Mapeando nomes para o padrão: {chave}"`, label linha `"Linha de exemplo encontrada:\n{kijo}" color #10B981 Consolas 11`, Scroll `height 270`, header `Exportar? Nº Nome da Coluna Valor da Amostra`, estado `colunas_marcadas = filtros[f_id].get("colunas_saida",None) or list(range(len(parts)))`, `nomes_salvos = nomes_colunas_mapeadas.get(chave,{})`; `lbl_preview "Prévia da saída: (todas)" color ACCENT Consolas bold`, `atualizar_preview` coleta `checkboxes` checked → `",".join([parts[i] for i in selecionadas])`; Para cada `i,campo in enumerate(parts)`: `row_item`, `var = BooleanVar(value=i in marcadas)`, `CheckBox command atualizar_preview`, `Label "Col {i+1}" width 50`, `Entry width 200 preenchido com nomes_salvos[str(i)] or f"Coluna {i+1}"`, `Label "->  {campo}" Consolas 12`; Ações `salvar_colunas`: coleta `selecionadas`, se vazio → `showerror "... pelo menos 1 coluna"`; se `chave` → `dict_nomes={str(idx): entry.get().strip() if strip else skip}`, `nomes_colunas_mapeadas[chave]=dict`, `_salvar_biblioteca()`; `filtros[f_id]["colunas_saida"]=selecionadas`, `lbl_status "Filtro 'nome' configurado com N colunas."`, `destroy`.

## 13. Fluxo Processamento GUI `gui/application.py:823-1330` (resumo)
- Valida arquivos `825-832` e filtros `834-841` e `tem_posicao` `843-854`.
- `progress 0`, `status "📄 Preparando..." color ACCENT`.
- Popup `CTkToplevel title "Configurar Exportação" 500x320 centralizado, topmost, grab_set`, Entrada `e_nome placeholder "Opcional: Digite o nome do arquivo único" width 380`, Container dinâmico `container_dinamico + scroll_frame width 450 height 200`, `grupos_disponiveis = [f"Grupo {l}" for l in ascii_uppercase]`, `regra_grupo_map`, `grupo_nome_map`, `render_grupos()` para cada grupo `card fg #F3F4F6 corner 8` header label `"{grupo}:" bold 14` `Entry textvariable grupo_nome_map width 200` para cada `f_id` no grupo `rule_frame` label `• {nome_regra}` + `OptionMenu values=grupos_disponiveis[:max(len filtros,1)] command change_group`, `separar_arquivos_var = BooleanVar(False)`, `toggle_separar`: se True → `e_nome disable, geometry 520x600, pack container before lbl_formato, render`, else `enable, 500x320, forget`, `CheckBox "Separar regras de filtro (Agrupamento Dinâmico)"`, `Label "Escolha o formato de saída:"`, `selecionar(fmt)`: `nome_custom=e_nome.get().strip()`, `separar=var.get(); if separar: mapa={f_id: grupo_nome_map[g].get().strip() or f"Regra_{f_id}"}`; `pop.destroy(); reset_ui(); definir_destino_e_iniciar(fmt, nome_custom, mapa)`.
- `definir_destino_e_iniciar:1178-1293` → `askdirectory`, `_salvar_biblioteca`, `arquivos_conflito` + `askyesno` overwrite, `status "⌛ PROCESSANDO..."`, `btn_processar disabled "⌛ PROCESSANDO..."`, `btn_duplicadas disabled`, `_mostrar_btn_cancelar()` `~1250`, `timer start`, `filtros_formatados` coleta `OP_MAP` e `colunas_saida`, `Thread(target=executar_thread, args=(filtros_formatados,caminho,fmt,separar), daemon True)`.
- `fluxo_duplicadas:1107-1172` → mesmo padrão com `status "⌛ ANALISANDO..."`, `_mostrar_btn_cancelar`, thread `executar_thread_duplicadas`.
- `executar_thread:1303-1361` → `FileProcessor(..., cancel_callback=_is_cancel_requested)`, `processar_e_exportar_em_chunks`; se `is_cancel` pós-retorno → `after _finalizar_cancelamento` e `return`; `except InterruptedError → after _finalizar_cancelamento`; `except Exception: if cancel or "cancelado" in msg → _finalizar_cancelamento` senão `showerror + reset_ui`.
- `cancelamento GUI:1590-1660` → `reset_ui` limpa timer `_cancel=False`, `btn_processar/duplicadas normal`, `btn_cancelar pack_forget disabled`, status `Aguardando`; `_mostrar/_esconder_btn_cancelar` pack `side LEFT padx10`; `cancelar_processamento:1615` seta `_cancel=True`, `status "✕ Cancelando..." DANGER`, `btn_cancelar disabled "✕ Cancelando..."`; `_finalizar_cancelamento:1635` cancela timer, `progress 0`, `status "✕ Cancelado." DANGER`, `gc`.

## 14. UI Estrutura `gui/application.py:266-790`
- `AplicacaoVisual.__init__:268-339` - `title f"Filtra KIJO v{VERSION}"`, `geometry 1300x850`, `fg_color BG`, `_set_window_icon(root)`, `after 0 state zoomed`, `v_num/register validar_inteiro`, `v_val/register _validar_dinamico`, `ManualDinamico`, `arquivos=[], dirs "", filtros={}, contador 0, biblioteca=_carregar`, `grid column 0 weight 1, row 1 weight 1`, `criar_header/corpo/rodape`, `timer none, status "Aguardando..."`.
- `criar_header:402-500` - `header CTkFrame height 120 corner 0 fg HEADER grid row 0 sticky ew`, `grid column 1 weight 1`, label `🔍 Filtra KIJO 28 bold white`, `frame_btn transparent grid column 2`, `Button 📂 Abrir Arquivo command abrir_arquivos fg ACCENT hover #4338CA 220x55 font 18 bold`, `Button ❓ Ajuda command manual.mostrar 130x55 #4B5563`, `lbl_status_files "Nenhum arquivo selecionado" 14 #9CA3AF grid row1 col0 colSpan3`, `ToolTip(lbl,[])`.
- `criar_corpo:505-653` - `corpo fg transparent grid row1 sticky nsew padx25 pady15, column 0 weight3 column1 weight1 row0 weight1`, `frame_filtros_container fg #FFFFFF border #E5E7EB grid row0 col0 sticky nsew padx0-15, row1 weight1 col0 weight1`, header `fg transparent`, label `🎯 Regras de Filtragem 22 bold`, `btn_nova_regra + Nova Regra command criar_filtro 160x42 SUCCESS disabled`, `scroll_filtros CTkScrollableFrame fg transparent grid row1`, `frame_lib width 320 fg #FFFFFF border`, `grid row0 col1 sticky nsew, row1 weight1 col0 weight1`, label `📜 Regras Salvas 18 bold`, `scroll_lib`.
- `criar_rodape:660-790` - `rodape fg transparent grid row2 sticky ew padx25 pady0-20, col0 weight1`, `card_rodape fg #FFFFFF border col0 weight1`, `frame_bottom fg transparent grid padx40 pady20 sticky ew col0 weight1`, `lbl_status_unificado "🕒 00:00 | 📄 Aguardando..." 16 bold`, `progress_bar height14 progress_color ACCENT grid pady15-20 sticky ew set 0`, `frame_botoes transparent grid row2`, `btn_processar ⚡ INICIAR PROCESSAMENTO command fluxo_processamento 15 bold 50x280 ACCENT`, `btn_duplicadas 🔍 ANALISAR DUPLICADAS command fluxo_duplicadas 50x280 WARNING`, `btn_cancelar ✕ CANCELAR command cancelar_processamento 15 bold 50x180 DANGER #EF4444 hover #DC2626` criado mas `pack_forget` até `_mostrar_btn_cancelar` durante processamento.

## 15. `main.py:1-27` / `main.spec:1-50` / `gerar_icone_fk.py:1-92`
- `AppUserModelID "Tecsoil.FiltraKIJO.v4.2.0"` `10` antes de criar janela (evita duplicar ícone).
- `multiprocessing.freeze_support()` `19` para .exe.
- `ctk.set_appearance_mode Light, theme blue` `22-23`, `CtK()`, `AplicacaoVisual(root)`, `mainloop` `25-27`.
- `main.spec:4` `datas=[('fk_icon.ico','.')]` `7-8` `collect_all customtkinter` `excludes PyQt5...` `exe name Filtra_KIJO_V_4_2_0 console False icon fk_icon.ico upx True` `30-50`.
- `gerar_icone_fk.py:8` gera 8 tamanhos `[256,128,64,48,32,24,20,16]` gradiente/sólido, rounded mask, fonte 0.58-0.62, sombra apenas >=32.

## 16. Regras transversais
- **Trim**: toda entrada `pos`, `valor`, `nome` é `strip()` antes de uso.
- **Case**: `KIJO` contém é case-sensitive; `Contém` é case-sensitive (`literal=True`); chave `upper()`.
- **Erros silenciosos**: `_carregar/_salvar biblioteca:366,395`, `filter_engine:46-47`, `file_processor:356-361` logam ou ignoram.
- **Memória**: `gc.collect()` pós processamento e em finally; `EmptyWorkingSet` `1551` pós finalizar.
- **Export formats**: `TXT/CSV` via `_safe_replace` copia temp (retry 1224); `Excel` via `write_excel` colunas `"1..n"`; formato duplicadas sempre TXT.
- **Timestamp ordering**: **removido em v4.2.1** para voltar à ordem de chegada 4.1 (antes era string lexical `YYYY-MM-DD hh:mm:ss` sortável, mas causava perdas de filtro e erro 1224 por memory-map no sort).
- **Temp cleanup**: `finally` com `_safe_remove` protege `None`; Excel remove `temp_sorted` + original; `separar_arquivos` remove cada `t_file`.
- **Persistência dirs**: `dir_abertura` atualizado só em `abrir_arquivos`; `dir_salvamento` atualizado em `fluxo_duplicadas` e `definir_destino`; ambos salvos em `__config__`.

---

## 17. Changelog adquirido v4.2.1 (2026-09-23)

- **1224 ERROR_USER_MAPPED_FILE**: `pl.read_csv` faz memory-map; escrever no mesmo arquivo causa `A operação solicitada não pode ser executada em um arquivo com uma seção mapeada pelo usuário aberta`. Fix: `_safe_remove/_safe_replace` retry 5x `0.05*2^attempt` + `gc`, `_ensure_reader_closed`, escrever em `.sorted` temporário diferente e `del df_sort + gc` antes do replace. Temp órfão `344012.txt.temp.csv` com handle preso foi deletado via `Remove-Item -Force`.
- **NoneType stat bug**: `temp_csv_final = None` após `_safe_replace` TXT/CSV fazia `finally`/`_safe_remove(None)` → `stat: path should be string... not NoneType`. Fix: guardar `if temp_csv_final:` antes de remover (`file_processor.py:509, 554-558`).
- **Ordenação 4.1 vs 4.2**: `FiltraKijo_v4.1.0.exe` (binário) tem `timestamp`=1x/`Ordenando`=0x vs 4.2 com 15x/3x → 4.1 não ordenava. Removida ordenação final para voltar à ordem de chegada (filtragem voltou a 100% correta).
- **Cancelamento**: estado `_cancel_processamento`, botão `✕ CANCELAR` surge só durante `⌛ PROCESSANDO/ANALISANDO`, `cancel_callback` checado por arquivo e por batch (50k), `InterruptedError` limpa temps sem `showerror`.
- **Biblioteca**: rename via `Button-3` menu + validação vazio/duplicado, auto-rename com gap reuse (`_gerar_nome_unico` verifica só ativos ao carregar da biblioteca, `verificar_biblioteca=False`), botões renomear 440x240 `height 44 expand=True` corrigem espremimento vertical.
- **Build**: `filtra-kijo-slim` Python 3.10.18 + PyInstaller 6.20.0 `--clean --noconfirm` ~100-113s, `taskkill` antes de `Copy-Item` para destino `Executaveis/FiltraKijo_v4.2.0.exe` quando em uso.

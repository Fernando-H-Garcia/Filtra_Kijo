# FiltraKIJO v4.3.0 — Documento Exaustivo de Regras de Negócio
*Sweep em `Filtra_KIJO_V_4_0_0` — 2026-09-18 — verificado por `Select-String -n` / leitura completa dos fontes*

> Cada bullet cita `arquivo:linha` exata (1-indexed). Linhas conferidas nesta revisão; `core/file_processor.py` possui 947 linhas, `gui/application.py` 2103 linhas, `core/filter_engine.py` 121 linhas, `utils/validators.py` 13 linhas.

---

## 1. `core/config.py:1-5`

- `VERSION = "4.3.0"` `core/config.py:2` — fonte única de verdade. Consumida em `gui/application.py:132,273` (título `Filtra KIJO v{VERSION}`), `gui/manual.py:5,18,158` (`Guia … V{VERSION}` / `Bem-vindo V{VERSION}`).
- `APP_NAME = "Filtra KIJO"` `core/config.py:4` — constante documentada, não consumida diretamente no runtime (título usa `VERSION`).
- **C-01 fix (v4.3.0)**: `main.py:10` e `gui/application.py:90` e `gui/manual.py:31` agora `Tecsoil.FiltraKIJO.v4.3.0` via `SetCurrentProcessExplicitAppUserModelID`; `main.spec:36` `name='Filtra_KIJO_V_4_3_0'`. Antes estavam `v4.2.0` dessincronizados com `core/config.py:2`.

---

## 2. `utils/validators.py:1-13` — validadores de entrada (Tk `validate="key"`)

### 2.1 `validar_inteiro(valor):5-9`
```python
def validar_inteiro(valor): # validators.py:5
    if valor == "": return True          # :7  permite campo vazio durante digitação
    if not valor.isdigit(): return False # :8
    return int(valor) > 0                # :9  só >0 passa
```
- `""` → `True`; `valor.isdigit()` obrigatório — rejeita `"-123"`, `" 42 "`, `"12.3"`, `"1e5"`, `"abc"` `tests/test_validators.py:13-17`.
- `int(valor) > 0` → `"0"` → `False` no código, mas **teste espera `True`** `tests/test_validators.py:9` → **divergência teste vs código** (H-01). Na UI `gui/application.py:290-292,1620` (`v_num` registrado) o usuário nunca consegue confirmar `"0"` porque o `FocusOut`/`compilação` descarta, porém o teste falha se executado.
- Regex alternativa rejeitada: `"-0"` etc. também `False`.
- Registrado como `validate="key"` para `e_pos` `gui/application.py:290-291,1620` com `validatecommand=(v_num, "%P")`.

### 2.2 `validar_valor(valor):11-13`
```python
def validar_valor(valor): # validators.py:11
    return bool(re.fullmatch(r"^-?\d*\.?\d*$", valor)) or valor == ""  # :13
```
- Aceita `""`, `"."`, `"-"`, `"-."`, `".5"`, `"-0.5"`, `"-12.5"`, `"123"` `tests/test_validators.py:22-29`. Nota: `re.fullmatch(r"^-?\d*\.?\d*$")` aceita `"."`, `"-"`, `"-."` como *tecnicamente* `True` na digitação intermediária — validado pelo motor como `val_num=None` depois e portanto **descartado/nunca casa** em `core/filter_engine.py:34-38,94-95`.
- Rejeita `"12,5"`, `" 42.0 "`, `"1e5"`, `"abc"` `tests/test_validators.py:32-35`.
- Usado dinamicamente só quando `op in [> < >= <=]` via `_validar_dinamico` `gui/application.py:1668-1676` — retorna `validar_valor(P)` se numérico, senão `return True` (permite qualquer texto para `= != Contém`). `H-02` incompleto antes: agora documentado que `"."`, `"-"` são permitidos na digitação mas viram `pl.lit(False)` no engine.

---

## 3. Campo **Posição**

### 3.1 Definição UI `gui/application.py:1619-1622`
- Label `"Posição:"` `gui/application.py:1619`, `CTkEntry width=80`, `font Segoe UI 14`, `validate="key"` com `v_num` `gui/application.py:1620`.
- 1 `row` por condição dentro de `rows_container` `gui/application.py:1603,1618`.
- Valor inicial `pos=""` se nova regra `gui/application.py:1616` (`def adicionar_condicao(f_id, pos="", val="", op="=")`).

### 3.2 Validação de entrada
- Só dígitos `>0` via `validar_inteiro` — typing bloqueado para `"-"`, `"."`, letras `utils/validators.py:5-9`.
- Ao `FocusOut` chama `verificar_posicao_unica` `gui/application.py:1622` (`e_pos.bind("<FocusOut>", lambda e: self.verificar_posicao_unica(f_id, e_pos))`).

### 3.3 Unicidade por filtro `gui/application.py:1647-1654`  *(corrigido: antes 1647-1653, faltava linha 1654 `e_pos.delete`)*
```python
def verificar_posicao_unica(self, f_id, e_pos): # :1647
    pos = e_pos.get().strip()                   # :1648
    if not pos.isdigit(): return                # :1649  não valida vazio/não-numérico
    for cond in self.filtros[f_id]["condicoes"]: # :1650
        if cond["pos_widget"] != e_pos and cond["pos_widget"].get() == pos: # :1651
            messagebox.showwarning("Aviso", f"Posição {pos} já configurada neste filtro!") # :1652
            e_pos.delete(0, tk.END)             # :1653-1654
```
- Não verifica unicidade entre filtros diferentes — repetir posição em filtros distintos é permitido.

### 3.4 Compilação `core/filter_engine.py:25-26`
- `pos = int(c["posicao"]) - 1` `core/filter_engine.py:26` → 1-indexed na UI vira 0-indexed (`field_0` = Pos 1). `ValueError` → `except: pass` descarta condição `core/filter_engine.py:46-47`.

### 3.5 Limite físico `core/filter_engine.py:78-79`, `core/file_processor.py:209,223-227`
- `if pos <0 or pos >=100: cond_expr = pl.lit(False)` `core/filter_engine.py:78-79` → Pos 0 ou >100 nunca casa (não estoura, apenas `False`).
- `max_cols = 100` fixo `core/file_processor.py:209`; `list.to_struct(upper_bound=max_cols)` `core/file_processor.py:223-224`; rename `field_0..field_n` `core/file_processor.py:230-241`. Comentário `:209` alerta que KIJO com >100 colunas exigiria bump.
- Conversão Excel usa `max_cols` dinâmico `core/file_processor.py:880-892` (conta vírgulas, `+1`, `upper_bound=max_cols` `:907`).

### 3.6 Obrigatoriedade `gui/application.py:843-854`, `1743-1759`
- `fluxo_processamento` varre todos filtros; `if c["pos_widget"].get().strip()` → se nenhum preenchido `tem_posicao==False` → `showwarning("Atenção: É obrigatório informar ao menos uma Posição nas regras de filtro!")` `gui/application.py:852-854` e `return`.
- `abrir_configuracao_colunas:1743-1759` → se `conds` vazio (`pos_val` vazio) → `showwarning("Configure pelo menos uma condição com posição antes de configurar a saída!")` `gui/application.py:1757-1759`.

---

## 4. Campo **Operação**

### 4.1 Mapa `gui/application.py:139-147` e `1624-1632`
```python
OP_MAP = {"Igual a":"=", "Diferente de":"!=", "Maior que":">", "Menor que":"<", "Maior ou igual a":">=", "Menor ou igual a":"<=", "Contém":"Contém"} # :139-147
# Re-declarado localmente em adicionar_condicao :1624-1632 (sombreia o global)
REV_OP_MAP = {v: k for k, v in OP_MAP.items()} # :1635
```

### 4.2 Widget `gui/application.py:1637-1638`
- `CTkComboBox values=[7 labels]`, `width=180`, `justify="center"`, `state="readonly"`, `font bold 16` `gui/application.py:1637`.
- Default `op="="` → `REV_OP_MAP.get(op,op)` `gui/application.py:1638`.
- `command=lambda _: e_val.delete(0,tk.END)` `gui/application.py:1637` → trocar operador limpa Valor (evita valor numérico residual quando muda para `Contém`/`=` etc.).

### 4.3 Engine `core/filter_engine.py:84-103`
- `"="`: se `val_num is not None` → `(col.cast(Float64, strict=False)==val_num) | (col==val)` `core/filter_engine.py:85-89`; senão `col==val`. Permite `"100"` casar com `100.0`.
- `"!="`: `col != val` `core/filter_engine.py:90-91` (sempre comparação string, não numérica).
- `> < >= <=`: `col_num = col.cast(Float64, strict=False)` `core/filter_engine.py:93`; se `val_num is None` → `pl.lit(False)` `core/filter_engine.py:94-95` (valor não-numérico digitado nunca casa); senão comparação numérica `core/filter_engine.py:96-99`.
- `"Contém"`: `col.str.contains(val, literal=True)` `core/filter_engine.py:100-101` — case-sensitive, literal (ponto não é regex).
- Desconhecido → `pl.lit(False)` `core/filter_engine.py:102-103`.

---

## 5. Campo **Valor**

### 5.1 Widget `gui/application.py:1640-1641`
- `CTkEntry width=200`, `validate="key"` com `v_val = register(_validar_dinamico)` `gui/application.py:294-296`.
- `validatecommand=(v_val, "%P", f_id, idx)` onde `idx=len(condicoes)` antes de `append` `gui/application.py:1640`.

### 5.2 Validação dinâmica `gui/application.py:1668-1676` *(corrigido range)*
```python
def _validar_dinamico(self, P, f_id, cond_idx): # :1668
    try:                                        # :1669
        idx = int(cond_idx)                     # :1670
        if f_id in self.filtros and idx < len(self.filtros[f_id]["condicoes"]): # :1671
            op_label = self.filtros[f_id]["condicoes"][idx]["op_widget"].get() # :1672
            op = OP_MAP.get(op_label, op_label) # :1673
            if op in [">", "<", ">=", "<="]: return validar_valor(P) # :1674
        return True                             # :1675
    except: return True                         # :1676
```

### 5.3 Compilação `core/filter_engine.py:28-32` *(corrigido: antes 28-32 citava 27-32; correto 31-32 é o `if val==""`)*
- `val = str(c["valor"]).strip()` `core/filter_engine.py:28` → trim automático.
- `if val=="" and op not in ["=", "!="]: continue` `core/filter_engine.py:31-32` → **condição descartada silenciosamente** (não vira `False`, é removida de `condicoes_compiladas`).

### 5.4 Conversão numérica `core/filter_engine.py:34-38`
- `try: val_num=float(val) except: pass` `core/filter_engine.py:34-38` → `None` se não-numérico; usado só para `=` (comparação dual) e `> < >= <=` (gate).

---

## 6. Filtro / Regra (Card)

### 6.1 Criação `gui/application.py:1584-1615`
- `criar_filtro(nome_inicial=None, condicoes_iniciais=None, colunas_saida_iniciais=None)` `gui/application.py:1584`.
- `contador_filtros +=1; f_id=f"filtro_{contador}"` `gui/application.py:1585-1586` — monotônico crescente, nunca reutiliza IDs (evita colisão de `f_id` mesmo após `remover_filtro`).
- Card `CTkFrame border #E5E7EB fg #F9FAFB`, header `height 45 fg #F1F5F9` `gui/application.py:1587-1590`.
- `entry_nome` placeholder `"Nome do Filtro"`, `width 280`, `font bold 15`; `nome_default = nome_inicial or "Nova Regra"` `gui/application.py:1591-1593`.
- Botões header: `✕` remover `gui/application.py:1595`, `💾` salvar `gui/application.py:1596`, `⚙️ Configurar Saída width 140` `gui/application.py:1599-1600`.
- `self.filtros[f_id] = {widget, nome_entry, rows_container, condicoes:[], colunas_saida}` `gui/application.py:1604-1610`.
- Botão `+ Adicionar Condição width 170 fg #6366F1` `gui/application.py:1611`.
- Se `condicoes_iniciais` vier da biblioteca, re-hidrata `colunas_saida_iniciais` `gui/application.py:1612-1614`; senão cria 1 condição vazia `gui/application.py:1614`.

### 6.2 Condições no mesmo filtro = AND `core/filter_engine.py:105-108`
- `expr_filtro &= cond_expr` `core/filter_engine.py:108`.

### 6.3 Múltiplos filtros = OR `core/filter_engine.py:113-121`
- `lista_expressoes_filtros` unida por `|=` `core/filter_engine.py:118-119`; `df.filter(expr_final)` `core/filter_engine.py:121`. Filtro vazio → `return df` `:58-59`; sem expressão válida → `df.filter(pl.lit(False))` `:114`.

### 6.4 Adicionar/Remover condição `gui/application.py:1616-1666`
- `atualizar_visibilidade_botoes:1662-1666` → se `len==1` esconde `btn_rem` (`pack_forget`) `gui/application.py:1664`, senão mostra todos `gui/application.py:1666` (`pack side LEFT padx 5`).
- `remover_condicao:1655-1660` destrói `row_widget`, remove `cond_data` da lista, **reindexa** `validatecommand` de todos `val_widget` restantes com novo `i` `gui/application.py:1659-1660` (sem isso o índice `cond_idx` ficaria stale e `_validar_dinamico` validaria operador errado).

---

## 7. Biblioteca de Regras

### 7.1 Arquivo `gui/application.py:311-313,344-369`
- `self.caminho_biblioteca = "filtros_salvos.json"` relativo ao CWD `gui/application.py:311-313`.
- `_carregar_biblioteca:344-369` — `os.path.exists` `:346`, `json.load` `:357`, `data.pop("__config__",{})` `:359`, captura `dir_abertura`, `dir_salvamento`, `nomes_colunas_mapeadas`; `except: return {}` `:366-367` silencia JSON corrompido.

### 7.2 Estrutura JSON `gui/application.py:375-392`
```json
{
  "nome_regra": {"condicoes":[{"posicao":str,"operacao":str,"valor":str}], "colunas_saida":[int]|null},
  "__config__":{"dir_abertura":str,"dir_salvamento":str,"nomes_colunas_mapeadas":{chave:{idx:str}}}
}
```
- `indent=4, ensure_ascii=False` `gui/application.py:388-392`.
- Compatibilidade retroativa: se valor for lista pura (formato antigo) → tratado como `condicoes` `gui/application.py:1706-1707`.

### 7.3 Salvar `_salvar_biblioteca:371-396`
- `data_to_save = biblioteca.copy(); data_to_save["__config__"]= {dir_abertura, dir_salvamento, nomes_colunas_mapeadas}` `gui/application.py:375-380`; `open(..., 'w', encoding='utf-8')` `gui/application.py:382-386`; `except: pass` `gui/application.py:395-396` silencia I/O error (ex.: OneDrive lock — ver §17).

### 7.4 `salvar_na_biblioteca(f_id):1682-1698`
- `nome = strip() or f"Filtra_{time}"` `gui/application.py:1683`, coleta `conds` mapeando `OP_MAP` `gui/application.py:1684-1688`, `self.biblioteca_filtros[nome]={"condicoes":conds,"colunas_saida":info.get("colunas_saida")}` `gui/application.py:1691-1694`.

### 7.5 `atualizar_lista_biblioteca:1699-1729`
- `for w in scroll_lib destroy` → rebuild `gui/application.py:1700`.
- `has_files = len(arquivos_selecionados)>0` `gui/application.py:1701`.
- Itera `sorted(keys)` → ordem alfabética `gui/application.py:1702`.
- Botão `CTkButton text="📜 {nome}" fg #F9FAFB hover #E0E7FF anchor w height 50 bold 15`, `command=lambda: criar_filtro(n,conds,cols) if has_files else showwarning("Selecione os arquivos antes de carregar filtros!")` `gui/application.py:1713-1722`.
- Se `not has_files`: `configure(state="disabled")` `gui/application.py:1725-1726`.
- Botão `🗑` overlay `gui/application.py:1727-1728` com `place(relx=0.94)`.

---

## 8. Seleção de Arquivos `gui/application.py:1733-1742`

- `filedialog.askopenfilenames(initialdir=dir_abertura or "/", title="Selecione os arquivos KIJO (GPRS)", filetypes=("Arquivos de Texto *.txt","Todos *.*"))` `gui/application.py:1734`.
- Se `caminhos`: `arquivos_selecionados = list(caminhos)`; `dir_abertura = dirname(caminhos[0])` `gui/application.py:1736`; `lbl_status_files configure text="✅ N arquivos selecionados" color SUCCESS` `gui/application.py:1736`; `tooltip_files.text_list = [basename...]` `gui/application.py:1741`; `_salvar_biblioteca()` persiste dir `gui/application.py:1737`; `btn_nova_regra state normal` `gui/application.py:1738`; `atualizar_lista_biblioteca()` reabilita botões `gui/application.py:1739`.

---

## 9. Processamento Normal `core/file_processor.py:39-503` *(assinatura e range corrigidos)*

- **Assinatura completa** `core/file_processor.py:39-47`:
  ```python
  def processar_e_exportar_em_chunks(self, formato, caminho_saida, chunksize=50000, max_workers=None, deduplicar=True, separar_arquivos=False): # :39-46
  ```
  `max_workers=None` existe mas **nunca usado** (C-02) — reservado para futuro paralelismo; documentado para evitar falso-positivo de "parâmetro inexistente". `chunksize` padrão `50000` `:43`.
- Inicialização `:58-66` `total_linhas_processadas/filtradas`, `linhas_duplicadas=0`, `hashes_vistos=set()` único global `:66`.
- `tamanho_total=sum(getsize)` `:73-76`, `filtros_compilados=FilterEngine.compilar_filtros(self.filtros)` `:78-82`.
- Se `separar_arquivos` (bool ou dict `mapa_nomes`) `:84-88`: `dir_out=dirname(caminho_saida)`, `ext="."+formato.lower()` `:86`, dedup nomes com `while nome_regra in nomes_vistos` `:100-101`, cria `temp_files_por_regra[f_id]={"final":path,"temp":path+".temp.csv"}` `:109-112`, limpa `temp` pré-existente `:114-120`.
- Senão `:121-124`: `temp_csv_final=caminho_saida+".temp.csv"` e `os.remove` se existir.
- **Loop arquivos** `:130-368`:
  - `pl.read_csv_batched(has_header=False, new_columns=["line"], separator="\x01", truncate_ragged_lines=True, encoding="utf8-lossy", low_memory=True, quote_char=None, batch_size=chunksize)` `:147-157` — `separator \x01` impede split em vírgulas naturais; `utf8-lossy` troca bytes inválidos por `�` em vez de falhar; `truncate_ragged_lines=True` ignora linhas malformadas; `quote_char=None` desativa quoting.
  - **FILTRA KIJO** `:175-178` `df.filter(pl.col("line").str.contains("KIJO"))` — case-sensitive.
  - **EXTRAI KIJO** `:187-202` `str.extract(r"(KIJO.*)",1).alias("raw_kijo")` e `str.extract(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",1).fill_null("").alias("timestamp")`.
  - **SPLIT** `:209-227` `str.split(",").list.eval(element.str.strip_chars()).alias("parts")` → `list.to_struct(upper_bound=100).unnest("parts")` → `field_0..field_n` rename `:230-241`.
  - **CONCAT** `:247-256` `pl.concat([df_cols, df_base.select("raw_kijo","timestamp")], how="horizontal")`.
  - **FILTROS & FORMATAÇÃO DINÂMICA** `:273-292`: `linhas_filtradas_por_regra={f_id:[]}` para cada `filtro_singular` `df_regra=aplicar_filtros_compilados(df_temp, ...)` e `colunas_saida = f_info.get("colunas_saida")`; se `colunas_saida not None` → `parts=[p.strip() for p in kijo.split(",")]; parts_filtradas=[parts[i] for i in colunas_saida if 0<=i<len(parts)]; linhas.append((ts, ",".join(parts_filtradas)))` `:285-289` senão `append((ts,kijo))` `:291-292`. Nota: `colunas_saida` fora de range é silenciosamente ignorado.
  - **DEDUP & SAVE** `:298-354`: se `separar`: para cada `f_id,linhas_regra`, `temp_file`, se `deduplicar` hash `xxhash.xxh64(linha).intdigest()` global `308-313` else direto, `total_linhas_filtradas+=len(linhas_out)`, `df_out=DataFrame({"timestamp":..., "raw_kijo":...})`, `write_csv(open(temp_file,"ab"), include_header=False, separator="\x01", quote_style="never")` `:323-325`; senão similar `:327-354`. `linhas_duplicadas` incrementada quando hash já visto.
  - `tamanho_processado+=tamanho_arquivo; atualizar_progresso()` `:363-367` — progresso por **bytes** (`tamanho_processado/tamanho_total`), não por linhas.
  - `except Exception as e: logging.error` `:356-361` — arquivo com erro é logado e **ignorado**, loop continua (hidden constraint).
- **Finalização** `:373-441`:
  - `if total_linhas_filtradas==0: raise ValueError("Nenhum dado encontrado.")` `:373-376`.
  - `status "Finalizando exportação..."` `:378-381`.
  - Se `separar`: para cada `paths`, **ordena** `read_csv(t_file, has_header False new_columns=["timestamp","raw_kijo"] separator \x01)` `:391-397`, `sort("timestamp")` `:399`, `select("raw_kijo").write_csv(t_file, include_header False)` `:400-401`, se `TXT/CSV` → `os.replace(t_file,f_file)` `:403-404`, se `Excel` → `_converter_csv_para_excel(f_file, t_file)` `:405-407`.
  - Senão `:408-441`: `sort("timestamp")` `:423`, `select("raw_kijo")` `:424`, `os.replace` ou `_converter_csv_para_excel`.
  - `duracao=time.time()-inicio` `:442`, `return {"sucesso":True, linhas_filtradas, linhas_processadas, linhas_duplicadas, total_arquivos, duracao}` `:459-471`.
  - `finally: remove cada temp; gc.collect()` `:481-503`.

---

## 10. Deduplicação — constraints ocultas

- `hashes_vistos = set()` único global para **todos arquivos e todas regras** `core/file_processor.py:66`. Consequência: duplicata entre regras diferentes conta como `linhas_duplicadas` e é descartada, mesmo com `separar_arquivos=True` (ordem de processamento define quem fica).
- `xxhash.xxh64(linha).intdigest()` `core/file_processor.py:308,337,602,708` — não criptográfico; colisão teoricamente possível mas desprezível. Hash é sobre `raw_kijo` (ou `kijo` filtrado com `colunas_saida`), **não** sobre `timestamp` nem `original_line`.
- `deduplicar=True` por padrão `core/file_processor.py:45`; só desativável via parâmetro (UI sempre `True` — checkbox não exposto). Desativar dobra saída mas remove proteção.
- **Memória**: `hashes_vistos` guarda 8 bytes por hash + overhead `set` (~72 bytes/entry) → 10M linhas únicas ≈ 700 MB RAM. Sem limite/spill-to-disk — arquivo gigante pode OOM. `gc.collect()` `:503,845` e `limpar_memoria` (`EmptyWorkingSet`) `gui/application.py:1551` mitigam pós-processamento, não durante.
- Encoding: `encoding="utf8-lossy"` `:153,562,669` — bytes inválidos viram `�`; `open(..., encoding="utf-8", errors="ignore")` `gui/application.py:1814` na busca de colunas — bytes latin1 são silenciosamente descartados (pode truncar KIJO). Não há detecção de `latin1`/`cp1252`.
- **OneDrive / file lock (hidden constraint)**: `filtros_salvos.json` e `*.temp.csv` residem no `CWD` que frequentemente é pasta sincronizada OneDrive. OneDrive pode bloquear arquivo durante sync → `open(..., 'w')` em `_salvar_biblioteca:382` falha silenciosamente (`except: pass` `:395-396`); `os.remove(temp)` em `finally:481-500,832-843` também silencia (`except: pass`). Resultado: biblioteca pode não persistir e temps órfãos permanecerem. `os.replace` `:404,431,788` é atômico localmente mas pode falhar com `PermissionError` se OneDrive tiver handle aberto.

---

## 11. Fluxo Duplicadas `core/file_processor.py:509-845`

- `processar_apenas_duplicadas(formato, caminho_saida, chunksize=50000)` `core/file_processor.py:509-514` — `formato` ignorado (sempre TXT); `chunksize` 50000.
- **Passo 1 — Conta hashes** `core/file_processor.py:530-626`: `status "Analisando duplicadas (Passagem 1/2)..."` `:536-539`, `tamanho_total sum` `:541-544`, `read_csv_batched` mesmo config `:556-565`, filtra `KIJO` `:580-582`, extrai `raw_kijo=r"(KIJO.*)"` `:585`, `linhas=to_list()` `:592-595`, `for linha: h=xxh64(linha).intdigest(); contagem[h]=get+1` `:599-610`, `hashes_duplicados={h for h,c if c>1}` `:622-626`, `if ==0: raise ValueError("Nenhuma duplicata encontrada.")` `:632-635`.
- **Passo 2 — Exporta** `core/file_processor.py:642-752`: `status "Exportando duplicadas (Passagem 2/2)..."` `:642-645`, `tamanho_processado=0` `:648`, `if exists temp: remove` `:650-651`, `linhas_exportadas=0` `:653`, para cada arquivo: `read_csv_batched` `:663-672`, para cada `original_line, kijo_str` zip `:702-704`, `h=xxh64(kijo_str)` `:707-710`, `if h in duplicados: linhas_originais.append(original_line); kijo_para_ordem.append(kijo_str)` `:713-720`, se `linhas_originais`: `nome_arquivo=basename` `:728`, `df_out=DataFrame({"filename":..., "raw_kijo":..., "original_line":...})` `:730-734`, `write_csv(temp_csv_final, ab, separator \x01, quote never)` `:740-746`.
- **Ordenação** `core/file_processor.py:758-790`: `status "Ordenando duplicadas para agrupamento..."` `:759`, `read_csv(temp_csv_final, new_columns=["filename","raw_kijo","original_line"])` `:762-769`, `sort(["raw_kijo","filename","original_line"])` `:773`, `select((filename+" "+original_line).alias("out"))` `:776-778`, `write_csv(temp_csv_final, include_header False)` `:780-784`, `os.replace(temp_csv_final,caminho_saida)` `:788-791`.
- **Memória duplicadas**: `contagem_hashes` dict cresce com **todos** hashes únicos (pior que `hashes_vistos`). 20M linhas únicas → dict pode exceder RAM antes mesmo da Passagem 2.

---

## 12. Configurar Saída (Colunas) `gui/application.py:1743-2103`

- Coleta `conds` de `filtros[f_id]["condicoes"]` onde `pos_widget.get().strip() != ""` `gui/application.py:1746-1755`.
- Se `not conds` → `showwarning` `gui/application.py:1757-1759`.
- `lbl_status "Procurando próxima ocorrência..." if index>0 else "Procurando ocorrência compatível..."` `gui/application.py:1762-1763`.
- Popup loading `400x150` centralizado, `indeterminate progress`, `grab_set, topmost`, `protocol WM_DELETE_WINDOW → busca_cancelada[0]=True + destroy` `gui/application.py:1765-1790`.
- Thread `thread_busca:1792-1924`: `FilterEngine.compilar_filtros({f_id: conds})` `:1797`, `tem_pos2_fixa = any(c["posicao"]=="2" and c["operacao"]=="=" for c)` `:1802`, `valores_pos2_vistos=set(), ocorrencias_encontradas=0`, para cada `caminho_arq` em `arquivos_selecionados`: `open utf-8 errors ignore` `:1814`, `for line: if "KIJO" not in continue; idx=find("KIJO"); kijo_str=line[idx:].strip(); parts=[p.strip() for p in split(",")]`, valida manualmente contra `filtros_compilados` `:1831-1881`, se `match`: se `tem_pos2_fixa`: se `ocorrencias_encontradas==ocorrencia_index` → `linha_encontrada=kijo_str break` else `+=1`, senão: `val_pos2=parts[1] if len>1 else ""`; se não visto → add set e checa index mesmo `:1892-1900`.
- Se `busca_cancelada` → `after lbl_status "Busca cancelada." return` `:1905-1907`.
- Se `not linha_encontrada and ocorrencia_index>0`: `after lambda abrir_configuracao_colunas(f_id,0)` (wrap-around) `:1918-1920`.
- Senão `after lambda exibir_modal_colunas(f_id, conds, linha_encontrada, ocorrencia_index)` `:1923`.
- `exibir_modal_colunas:1927-2103`: `lbl_status reset` `:1928`; `if not linha_encontrada: showinfo "Nenhuma linha compatível..." return` `:1929-1931`; `parts = split strip` `:1933`; **Chave KIJO** `gui/application.py:1935-1963`: tenta extrair `val_pos1/2/4` das `conds` onde `posicao=="1/2/4"`; se vazio, pega de `parts[0], [1], [3]`; `chave = f"{pos1}_{pos2}" + f"_{pos4}" if pos4` `gui/application.py:1958-1963` uppercased — usada como chave em `nomes_colunas_mapeadas[chave]` para **persistir apelidos de coluna por tipo de KIJO**.
- Popup `750x620` centralizado, título `"⚙️ Selecione e Nomeie..."` `:1966-1972`, instrução `"Mapeando nomes para o padrão: {chave}"` `:1980-1981`, label linha `"Linha de exemplo encontrada:\n{kijo}" color #10B981 Consolas 11` `:1984`, Scroll `height 270` `:1988`, header `Exportar? Nº Nome da Coluna Valor da Amostra` `:1992-1997`, estado `colunas_marcadas = filtros[f_id].get("colunas_saida",None) or list(range(len(parts)))` `:2003-2005`, `nomes_salvos = nomes_colunas_mapeadas.get(chave,{})` `:2009-2010`; `lbl_preview "Prévia da saída: (todas)" color ACCENT Consolas bold` `:2013`, `atualizar_preview` coleta `checkboxes` checked → `",".join([parts[i] for i in selecionadas])` `:2015-2026`; Para cada `i,campo in enumerate(parts)`: `row_item`, `var = BooleanVar(value=i in marcadas)` `:2033`, `CheckBox command atualizar_preview` `:2034`, `Label "Col {i+1}" width 50` `:2039`, `Entry width 200 preenchido com nomes_salvos[str(i)] or f"Coluna {i+1}"` `:2043-2046`, `Label "->  {campo}" Consolas 12` `:2050`; Ações `salvar_colunas:2061-2084`: coleta `selecionadas`, se vazio → `showerror "... pelo menos 1 coluna"` `:2068`; se `chave` → `dict_nomes={str(idx): entry.get().strip() if strip else skip}`, `nomes_colunas_mapeadas[chave]=dict`, `_salvar_biblioteca()` `:2072-2079`; `filtros[f_id]["colunas_saida"]=selecionadas` `:2082`, `lbl_status "Filtro 'nome' configurado com N colunas."` `:2083`, `destroy`.

---

## 13. Fluxo Processamento GUI `gui/application.py:823-1089` + `1165-1280`

- Valida arquivos `gui/application.py:825-832` e filtros `gui/application.py:834-841` e `tem_posicao` `gui/application.py:843-854`.
- `progress 0`, `status "📄 Preparando..." color ACCENT` `gui/application.py:856-865`.
- Popup `CTkToplevel title "Configurar Exportação" 500x320 centralizado, topmost, grab_set` `gui/application.py:867-898`, Entrada `e_nome placeholder "Opcional: Digite o nome do arquivo único" width 380` `gui/application.py:908-918`, Container dinâmico `container_dinamico + scroll_frame width 450 height 200` `gui/application.py:921-923`, `grupos_disponiveis = [f"Grupo {l}" for l in ascii_uppercase]` `gui/application.py:926`, `regra_grupo_map`, `grupo_nome_map` `gui/application.py:928-945`, `render_grupos()` para cada grupo `card fg #F3F4F6 corner 8` header label `"{grupo}:" bold 14` `gui/application.py:960` `Entry textvariable grupo_nome_map width 200` para cada `f_id` no grupo `rule_frame` label `• {nome_regra}` + `OptionMenu values=grupos_disponiveis[:max(len filtros,1)] command change_group` `gui/application.py:968-992`, `separar_arquivos_var = BooleanVar(False)` `gui/application.py:994`, `toggle_separar`: se True → `e_nome disable, geometry 520x600, pack container before lbl_formato, render`, else `enable, 500x320, forget` `gui/application.py:996-1005`, `CheckBox "Separar regras de filtro (Agrupamento Dinâmico)"` `gui/application.py:1007-1014`, `Label "Escolha o formato de saída:"` `gui/application.py:1016-1023`, `selecionar(fmt):1034-1056`: `nome_custom=e_nome.get().strip()`, `separar=var.get(); if separar: mapa={f_id: grupo_nome_map[g].get().strip() or f"Regra_{f_id}"}`; `pop.destroy(); reset_ui(); definir_destino_e_iniciar(fmt, nome_custom, mapa)` `gui/application.py:1049-1056`.
- `definir_destino_e_iniciar:1165-1280` — `askdirectory initialdir=dir_salvamento or dir_abertura` `:1172-1178`, persist `dir_salvamento` `:1183-1184`, conflito: `isinstance(separar_arquivos, dict)` itera `re.sub(r'[\\/*?:"<>|]',"", nome)` `:1191`, `os.path.exists` `:1194-1196` coleta `arquivos_conflito`; `askyesno "Confirmar Substituição"` `:1221`; `status "⌛ PROCESSANDO..."` `:1226`, `btn_processar disabled text "⌛ PROCESSANDO..."` `:1228-1231`, `timer start` `:1237-1239`, coleta `filtros_formatados` `OP_MAP.get` `:1241-1269`, `thread executar_thread` `:1271-1280`.
- `executar_thread:1286-1344` — `FileProcessor(arquivos_selecionados, filtros, progress_callback, status_callback)` `:1296-1307`, `processar_e_exportar_em_chunks(formato=fmt.upper().replace(".",""), caminho_saida, separar_arquivos)` `:1309-1318`, `after finalizar_processamento` `:1321-1325` ou `showerror "Erro Fatal"` `:1334`.

---

## 14. Fluxo Duplicadas GUI `gui/application.py:1094-1160` + `1349-1400`

- `fluxo_duplicadas:1094-1159` — valida `arquivos_selecionados` `:1096-1103`, `progress 0` `:1105`, `status "🔍 Preparando análise..."` `:1107-1114`, `askdirectory` `:1116-1122`, `dir_salvamento` persist `:1127-1128`, `nome_final f"Duplicadas_{int(time.time())}.txt"` `:1130-1133`, `status "⌛ ANALISANDO..."` `:1140`, `btn_processar/duplicadas disabled` `:1142-1149`, `timer` `:1151-1153`, `thread executar_thread_duplicadas` `:1155-1159`.
- `executar_thread_duplicadas:1349-1399` — `FileProcessor(..., filtros={})` `:1356-1367`, `processar_apenas_duplicadas(formato="TXT", caminho_saida)` `:1371-1374`, `after finalizar_duplicadas` `:1377-1381`.

---

## 15. UI Estrutura `gui/application.py:266-790`

- `AplicacaoVisual.__init__:268-339` - `title f"Filtra KIJO v{VERSION}"` `:272-274`, `geometry 1300x850` `:276`, `fg_color BG` `:278-280`, `_set_window_icon(root)` `:283`, `after 0 state zoomed` `:285-288`, `v_num/register validar_inteiro` `:290-292`, `v_val/register _validar_dinamico` `:294-296`, `ManualDinamico` `:298-300`, `arquivos=[], dirs "", filtros={}, contador 0, biblioteca=_carregar` `:302-317`, `grid column 0 weight 1, row 1 weight 1` `:319-327`, `criar_header/corpo/rodape` `:329-331`, `timer none, status "Aguardando..."` `:333-338`.
- `criar_header:402-500` - `header CTkFrame height 120 corner 0 fg HEADER grid row 0 sticky ew` `:404-415`, `grid column 1 weight 1` `:417-420`, label `🔍 Filtra KIJO 28 bold white` `:422-431`, `frame_btn transparent grid column 2` `:441-450`, `Button 📂 Abrir Arquivo command abrir_arquivos fg ACCENT hover #4338CA 220x55 font 18 bold` `:452-464`, `Button ❓ Ajuda command manual.mostrar 130x55 #4B5563` `:466-478`, `lbl_status_files "Nenhum arquivo selecionado" 14 #9CA3AF grid row1 col0 colSpan3` `:480-494`, `ToolTip(lbl,[])` `:496-499`.
- `criar_corpo:505-653` - `corpo fg transparent grid row1 sticky nsew padx25 pady15, column 0 weight3 column1 weight1 row0 weight1` `:505-533`, `frame_filtros_container fg #FFFFFF border #E5E7EB grid row0 col0 sticky nsew padx0-15, row1 weight1 col0 weight1` `:535-557`, header `fg transparent` `:559-570`, label `🎯 Regras de Filtragem 22 bold` `:572-577`, `btn_nova_regra + Nova Regra command criar_filtro 160x42 SUCCESS disabled` `:579-591`, `scroll_filtros CTkScrollableFrame fg transparent grid row1` `:592-603`, `frame_lib width 320 fg #FFFFFF border` `:605-617`, `grid row0 col1 sticky nsew, row1 weight1 col0 weight1` `:619-627`, label `📜 Regras Salvas 18 bold` `:629-638`, `scroll_lib` `:640-651`.
- `criar_rodape:659-790` - `rodape fg transparent grid row2 sticky ew padx25 pady0-20, col0 weight1` `:659-677`, `card_rodape fg #FFFFFF border col0 weight1` `:679-695`, `frame_bottom fg transparent grid padx40 pady20 sticky ew col0 weight1` `:697-713`, `lbl_status_unificado "🕒 00:00 | 📄 Aguardando..." 16 bold` `:715-726`, `progress_bar height14 progress_color ACCENT grid pady15-20 sticky ew set 0` `:728-741`, `frame_botoes transparent grid row2` `:747-756`, `btn_processar ⚡ INICIAR PROCESSAMENTO command fluxo_processamento 15 bold 50x280 ACCENT` `:758-772`, `btn_duplicadas 🔍 ANALISAR DUPLICADAS command fluxo_duplicadas 50x280 WARNING #F59E0B` `:774-788`.

---

## 16. `main.py:1-27` / `main.spec:1-50` / `gerar_icone_fk.py:1-92`

- `AppUserModelID "Tecsoil.FiltraKIJO.v4.3.0"` `main.py:10` e `gui/application.py:90` e `gui/manual.py:31` antes de criar janela (evita duplicar ícone).
- `multiprocessing.freeze_support()` `main.py:19` para .exe Windows.
- `ctk.set_appearance_mode Light, theme blue` `main.py:22-23`, `CtK()`, `AplicacaoVisual(root)`, `mainloop` `main.py:25-27`.
- `main.spec:4` `datas=[('fk_icon.ico','.')]` `main.spec:7-8` `collect_all customtkinter` `excludes PyQt5...` `exe name Filtra_KIJO_V_4_3_0` `main.spec:36` `console False icon fk_icon.ico upx True` `main.spec:30-50`.
- `gerar_icone_fk.py:8` gera 8 tamanhos `[256,128,64,48,32,24,20,16]` gradiente/sólido, rounded mask, fonte 0.58-0.62, sombra apenas >=32.

---

## 16b. Icon/DPI/Janela — `gui/application.py:14-128` / `gerar_icone_fk.py:8-86` (v4.3.0)

- **DPI awareness** `gui/application.py:14-20` — `ctypes.windll.shcore.SetProcessDpiAwareness(1)` com fallback `SetProcessDPIAware()` para multi-monitor; evita embaçado em 125%/150% (`gui/application.py:14-15` + `18`).
- **`_resource_path(relative_path)`** `gui/application.py:23-30` — resolve `fk_icon.ico` para dev (`os.path.dirname(__file__)/..`) e para PyInstaller (`sys._MEIPASS`); fallback `alt` em `gui/application.py:85-87` se `icon_path` não existir.
- **`_create_fk_image(tam)`** `gui/application.py:32-77` — gera imagem FK nítida nativa no tamanho exato (evita `resize` borrado): `Image.new RGBA` (`:35`), gradiente `18,58,138→32,96,196` só `>=48` (`:37-42`) senão sólido `(28,78,168)` (`:43-44`), máscara `rounded_rectangle radius max(tam//6,2)` (`:45-49`), `font_size 0.58-0.62*tam` (`:50-55`), `arialbd.ttf`/`arial.ttf` fallback (`:57-64`), centralização `textbbox` (`:66-71`), sombra `offset (1,1)` só `>=48`/`>=32` (`:72-75`), texto branco (`:76`).
- **`_set_window_icon(window)`** `gui/application.py:79-128` — sequência: `SetCurrentProcessExplicitAppUserModelID("Tecsoil.FiltraKIJO.v4.3.0")` (`:90`), `iconbitmap(icon_path)` (`:95`), `iconphoto(True,*6photos)` (`:120`) com 6 tamanhos nítidos `[16,20,24,32,48,64]` (`:102`), tenta `_create_fk_image(sz)` nativo senão `Image.open(ico, sizes=[(sz,sz)])` fallback + `LANCZOS resize` (`:104-114`), `PhotoImage` (`:115`), **anti-GC** `window._icon_refs` + `window._icon_photo` (`:121-124`) — sem refs o `PhotoImage` é coletado e ícone some/volta quadrado azul.
- **Call sites** `gui/application.py:283` (`AplicacaoVisual.__init__` root), `gui/application.py:875` (popup `Configurar Exportação`), `gui/application.py:1767` (popup `Pesquisando` loading), `gui/application.py:1968` (modal `Configurar Colunas`), e `gui/manual.py:31-77` (manual `CTkToplevel` com mesmo padrão `iconbitmap`+`iconphoto` + `_icon_photos`).
- **`gerar_icone_fk.py:8-86`** — `criar_icone_fk(caminho_saida)` gera `.ico` multi-resolução: `tamanhos=[256,128,64,48,32,24,20,16]` (`:8`), gradiente/sólido idêntico a `_create_fk_image` (`:16-24`), `rounded_rectangle` (`:30-34`), fonte `0.58-0.62` (`:38-43`), sombra só `>=32` (`:66-69`), `stroke_width` só `>=48` (`:73-76`), `save(format='ICO', sizes=[...], append_images=...)` (`:81-85`), `__main__` em `gerar_icone_fk.py:89-92` salva `fk_icon.ico` na raiz.
- **Bundling**: `main.spec:4` `datas=[('fk_icon.ico','.')]` expõe em `_MEIPASS`; `main.spec:49` `icon='fk_icon.ico'` para ícone do arquivo `.exe` no Explorer — ambos necessários, um não substitui o outro (v. `docs/BUILD.md:7`).

---

## 17. Restrições ocultas / armadilhas (não documentadas antes)

- **OneDrive / Sync Lock**: `filtros_salvos.json` (`gui/application.py:311`) e `*.temp.csv` são criados no CWD; se CWD for pasta OneDrive, `os.replace`/`os.remove` podem levantar `PermissionError` quando OneDrive mantém handle. Código silencia (`except: pass` em `core/file_processor.py:356-361,483-500,832-843` e `gui/application.py:395-396`), portanto falha é silenciosa: biblioteca não salva, temps órfãos não limpos.
- **Encoding**: `core/file_processor.py:153,562,669` `encoding="utf8-lossy"` — bytes inválidos (latin1 `café` etc.) viram `�`, linha ainda processada mas conteúdo corrompido. `gui/application.py:1814` usa `open(..., errors="ignore")` — bytes inválidos são descartados, não `�`. Nenhum fallback `latin1`/`cp1252`. `tests/test_file_processor.py:127-151` espera latin1 mas real é utf8-lossy → teste quebra se executado com Polars.
- **Deduplicação memória**: ver §10 — `hashes_vistos` e `contagem_hashes` sem spill; 10M hashes ≈ 700 MB–1 GB. `tamanho_total` baseado em `getsize` bytes, mas `hashes_vistos` baseado em linhas; arquivos esparsos (muitas linhas curtas) estouram antes de progresso chegar a 50%.
- **Progresso por bytes**: `core/file_processor.py:928-947` `progresso = 5 + (tamanho_processado/tamanho_total)*90` — se arquivos têm tamanhos muito desiguais, barra salta. `tamanho_processado` só atualizado **após** arquivo inteiro, não por batch, então UI congela durante arquivo grande.
- **Coluna inexistente**: `core/filter_engine.py:78` `pl.lit(False)` — filtro com `pos` inexistente nunca casa, não erro. `tests/test_filter_engine.py:232-273` documenta mas testes usam API inexistente `aplicar_filtros_com_validacao` com `MagicMock(get=...)` e `pandas` — quebrados na base atual (ver §18).
- **`colunas_saida` fora de range**: `core/file_processor.py:288` `if i>=0 and i<len(parts)` — índices inválidos silenciosamente ignorados; se todos inválidos, linha vira `""` (string vazia) e ainda é deduplicada/exportada.
- **Chave KIJO `nomes_colunas_mapeadas`**: `gui/application.py:1958-1963` chave `f"{pos1}_{pos2}_{pos4}".upper()` — colisão se `pos4` vazio vs `pos1_pos2` sem pos4; `upper()` torna case-insensitive para chave mas `Contém` é case-sensitive.

---

## 18. Testes — status quebrado (não documentado antes)

- `tests/test_validators.py:9` `assert validar_inteiro("0") is True` **falha** — código retorna `False` (`int("0")>0` é `False`). `tests/test_validators.py:1-35` demais asserts passam.
- `tests/test_filter_engine.py:1-355` — **todos quebrados**: importam `pandas` e `FilterEngine.aplicar_filtros_com_validacao` (método inexistente; atual é `compilar_filtros` + `aplicar_filtros_compilados` com `polars`). Usam `MagicMock(get=...)` para simular widgets, mas `core/filter_engine.py:10-53` espera dict `{"posicao":str, "operacao":str, "valor":str}`. Rodar `pytest tests/test_filter_engine.py` → `AttributeError`/`ImportError`.
- `tests/test_file_processor.py:1-313` — **todos quebrados**: `FileProcessor.processar_para_dataframe()` não existe (removido na migração Polars V3); `FileProcessor([path])` sem `filtros` e com `processar_para_dataframe` + asserts `df.iloc` estilo pandas — atual retorna dict via `processar_e_exportar_em_chunks`. Alguns testes passam `filtros` com lambdas `lambda: "999"` (objeto, não string) — incompatível com `FilterEngine.compilar_filtros`. `pytest` coleta mas falha em todos exceto `test_arquivo_vazio`/`test_sem_kijo` se mockado.
- **Recomendação**: marcar `tests/test_filter_engine.py` e `tests/test_file_processor.py` como `xfail`/`skip` até reescrita para Polars, ou reintroduzir shim `aplicar_filtros_com_validacao` + `processar_para_dataframe` para compatibilidade retroativa. `test_validators.py:9` corrigir para `assert validar_inteiro("0") is False` ou mudar regra para `>=0`.

---

## 19. Regras transversais (atualizado)

- **Trim**: toda entrada `pos`, `valor`, `nome` é `strip()` antes de uso `core/filter_engine.py:28`, `gui/application.py:1244-1261,1753`.
- **Case**: `KIJO` contém é case-sensitive `core/file_processor.py:177,581,688` (`str.contains("KIJO")`); `Contém` é case-sensitive (`literal=True`) `core/filter_engine.py:101`; chave `nomes_colunas_mapeadas` é `upper()` `gui/application.py:1963`.
- **Erros silenciosos**: `_carregar/_salvar biblioteca:366,395`, `filter_engine:46-47`, `file_processor:356-361,483-500,832-843` logam ou ignoram (ver §17 OneDrive).
- **Memória**: `gc.collect()` pós processamento e em `finally` `core/file_processor.py:503,845`, `gui/application.py:1492,1544`; `EmptyWorkingSet` `gui/application.py:1551` pós finalizar — libera WorkingSet no Windows, não durante.
- **Export formats**: `TXT/CSV` via `os.replace` copia temp; `Excel` via `write_excel` colunas `"1..n"` `core/file_processor.py:913-922`; formato duplicadas sempre TXT `gui/application.py:1372`.
- **Timestamp ordering**: string lexical funciona porque formato `YYYY-MM-DD hh:mm:ss` é sortável `core/file_processor.py:399,423,773`.
- **Persistência dirs**: `dir_abertura` atualizado só em `abrir_arquivos` `gui/application.py:1736`; `dir_salvamento` atualizado em `fluxo_duplicadas` `gui/application.py:1127` e `definir_destino` `gui/application.py:1183`; ambos salvos em `__config__` `gui/application.py:376-379`.

---

## 20. Auditoria — correções aplicadas nesta revisão (rastreabilidade)

- **C-01**: `VERSION` header `4.2.0→4.3.0`; `main.py:10`, `gui/application.py:90`, `gui/manual.py:31`, `main.spec:36` alinhados a `core/config.py:2`.
- **C-02**: assinatura `core/file_processor.py:39-46` agora documenta `max_workers=None` (não usado) + `deduplicar` + `separar_arquivos`.
- **Ranges**: `core/file_processor.py:39-503` (antes `39-503` correto para export normal, mas doc omitia `509-947`); agora `39-503` normal + `509-845` duplicadas + `851-922` Excel + `928-947` progresso; `gui/application.py:1647-1654` (antes 1647-1653), `core/filter_engine.py:31-32` (antes 28-32), `gui/application.py:1668-1676`, `1743-1759`, `1927-2103`, etc. conferidos.
- **H-01/H-02**: `utils/validators.py:5-13` documenta divergência `"0"` e `"." / "-"` aceitos na digitação mas `pl.lit(False)` no engine.
- **Hidden constraints**: §17 adiciona OneDrive lock, `utf8-lossy` vs `errors="ignore"`, dedup memória OOM, progresso por bytes, `colunas_saida` fora de range.
- **Tests quebrado**: §18 novo — `test_validators "0"`, `test_filter_engine` API inexistente + pandas, `test_file_processor` `processar_para_dataframe` inexistente.

---

## 21. Qt Visual (v4.3) — Appendix: `gui_qt/` + `main_qt.py` (visual shell only, core unchanged)

> **Invariante v4.3**: Qt é **visual shell only** — `gui_qt/main_window.py:1-176`, `gui_qt/theme.py:1-501`, `gui_qt/manual.py:1-336`, `main_qt.py:1-50` apenas reimplementam UI com PySide6; `core/` (`filter_engine.py:1-121`, `file_processor.py:1-947`, `config.py:1-5`) permanece idêntico e compartilhado com Tk. Cards hardcoded de exemplo, sem lógica de filtros/processamento ainda.

### 21.1 `gui_qt/main_window.py:1-176` — Janela Qt (QMainWindow)

- **Imports** `gui_qt/main_window.py:1-9` — `QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFrame,QLabel,QPushButton,QLineEdit,QComboBox,QScrollArea,QSplitter,QToolButton,QStackedWidget` (`:3-6`), `Qt,QSize` (`:7`), `QIcon` (`:8`), `VERSION` (`:9`).
- **`_rp(p)`** `gui_qt/main_window.py:11-14` — helper `_resource_path` para `fk_icon.ico` (try `sys._MEIPASS` fallback `dirname(dirname(__file__))`), usado em `gui_qt/main_window.py:24-25`.
- **`OP_LIST`** `gui_qt/main_window.py:16` — `["Igual a","Diferente de","Maior que","Menor que","Maior ou igual a","Menor ou igual a","Contém"]` (espelha `gui/application.py:139-147`).
- **`MainWindow.__init__`** `gui_qt/main_window.py:18-127` — `setWindowTitle f"Filtra KIJO v{VERSION} - v4.3 Visual"` (`:21`), `setMinimumSize(1280,800)` (`:22`), `setWindowIcon(QIcon(_rp("fk_icon.ico")))` (`:23-26`) — ícone via `QIcon` (não `AppUserModelID`; Qt gerencia agrupamento nativo, ver `main_qt.py:18-26` nota).
- **Header 64px** `gui_qt/main_window.py:30-53` — `header QFrame fixedHeight 64` (`:30`), `bg #1F2937` (`:30`), `QHBoxLayout` com `logo "🔍 Filtra KIJO"` (`:32`), **stepper** `① Arquivos → ② Filtros → ③ Exportar` (`:35-44`) com `bg #4F46E5` active / `#374151` inactive, `btn_abrir 150x36 #4F46E5` (`:48-50`), `btn_ajuda 90x36 #4B5563` (`:51-53`).
- **Status bar** `gui_qt/main_window.py:56-60` — `status QFrame fixedHeight 28 bg #E5E7EB` (`:56`), `lbl_status "✅ Nenhum arquivo selecionado • Pronto para v4.3 visual"` (`:58`).
- **Body QSplitter** `gui_qt/main_window.py:62` — `QSplitter(Qt.Horizontal) handleWidth 1 handle bg #E5E7EB` (`:62`), `setSizes([900,320])` (`:113`).
- **Left filtros** `gui_qt/main_window.py:64-84` — `left QFrame bg #F3F4F6` (`:64`), `QVBoxLayout 16,16,8,16` (`:65`), title `🎯 Regras de Filtragem` (`:69`), `btn_nova 130x34 #10B981` (`:71-73`), `QScrollArea` + `content QWidget` + `filter_layout QVBoxLayout AlignTop` (`:76-78`), **example cards hardcoded** `self._add_example_card("Nova Regra",[("", "Igual a","")])` (`:80`) e `self._add_example_card("Filtro Exemplo",[("2","Igual a","00"),("5","Contém","V4")])` (`:82`) — puramente visual, sem `filtros` dict, sem `FileProcessor`, sem `FilterEngine`.
- **Right biblioteca drawer 320** `gui_qt/main_window.py:87-112` — `right QFrame min 280 max 380 bg white border #E5E7EB radius 8` (`:87`), header `48px bg #F9FAFB border-bottom #E5E7EB` (`:89-92`), `search QLineEdit placeholder "Buscar..." 120x28` (`:93-95`), `lib_scroll QScrollArea` + `lib_lay AlignTop` (`:97-99`), 3 items hardcoded `["Filtro Equipamento ABC","Regra V4 00","Duplicatas 2024"]` (`:100-108`) com `QToolButton 🗑` (`:105-107`) — sem persistência `filtros_salvos.json`, sem `_carregar_biblioteca`.
- **Footer 56px** `gui_qt/main_window.py:116-127` — `footer QFrame fixedHeight 56 bg white border-top #E5E7EB` (`:116`), `lbl_timer "🕒 00:00"` (`:118`), `btn_proc 200x36 #4F46E5 "⚡ INICIAR PROCESSAMENTO"` (`:121-123`), `btn_dup 160x36 #F59E0B "🔍 DUPLICADAS"` (`:124-126`) — visual only, sem `fluxo_processamento`/`executar_thread`.
- **`_add_example_card(nome,conds)`** `gui_qt/main_window.py:129-176` — `card QFrame bg white border #E5E7EB radius 8` (`:130`), header `48px bg #F1F5F9` (`:132-133`), `QLineEdit nome 180x30` (`:134-135`), `btn_cfg "⚙️ Configurar" 110x28 #4F46E5` (`:138-140`), `btn_save "💾" 32x28` (`:141-144`), `btn_close "✕" 32x28 #EF4444` (`:145-148`), body `QVBoxLayout` (`:150`), rows `Posição: QLineEdit 60x30` (`:156-159`) + `QComboBox 130x30 OP_LIST` (`:160-163`) + `QLineEdit valor 150x30` (`:164-167`) + `btn_x "✕" 32x30 #FEE2E2` (`:168-170`), `btn_add "+ Adicionar Condição" #6366F1` (`:172-174`) — todos widgets hardcoded, sem `validate`, sem `OP_MAP`, sem `verificar_posicao_unica`.

### 21.2 `gui_qt/theme.py:1-501` — Tema Qt (GLOBAL_STYLE + LightBranchStyle)

- **Palette** `gui_qt/theme.py:10-45` — `COLOR_HEADER #1F2937 BG #F3F4F6 ACCENT #4F46E5 SUCCESS #10B981 DANGER #EF4444 WARNING #F59E0B` (`:10-18`), `BG_PRIMARY/SECONDARY/CARD/HOVER/INPUT` (`:20-24`), `TEXT_PRIMARY/DISABLED` (`:26-29`), `ACCENT_HOVER #4338CA ACTIVE #3730A3` (`:31-33`), `BORDER_SUBTLE #E5E7EB FOCUS #4F46E5` (`:41-43`), spacing `XS 4 SM 8 MD 16 LG 24 XL 32` (`:48-52`), radius `SM 4 MD 6 LG 10` (`:55-57`), fonts `CAPTION 11 BODY 12 SUBTITLE 17 TITLE 22 HEADER 28` (`:60-65`).
- **`GLOBAL_STYLE` QSS** `gui_qt/theme.py:73-441` — `QWidget bg BG_PRIMARY color TEXT_PRIMARY font Segoe UI 12px` (`:74-79`), `QMainWindow bg BG_PRIMARY` (`:80-82`), `QFrame#Header bg #1F2937` (`:89-91`), `QFrame#Card/#FilterCard bg white/#F9FAFB border #E5E7EB radius 10/6` (`:106-125`), `QScrollArea transparent` (`:128-134`), `QPushButton base/hover/pressed/disabled` (`:137-156`), `QPushButton#primary/#success/#warning/#dangerSubtle/#accentSubtle/#ghost` com `hover` explícito (`:159-245`), `QLineEdit bg white border #E5E7EB focus #4F46E5 hover #D1D5DB` (`:248-294`), `QLineEdit#SearchInput/#FilterPos/#FilterVal` (`:269-294`), `QComboBox bg white border #E5E7EB popup light white selection #E0E7FF` (`:297-342`), `QProgressBar bg #E5E7EB chunk #4F46E5 radius 7` (`:345-359`), `QCheckBox indicator 16px border #D1D5DB checked #4F46E5` (`:362-379`), `QScrollBar handle #D1D5DB hover #4F46E5` (`:382-409`), `QLabel transparent` (`:412-415`), `QToolTip bg white color #1F2937 border #E5E7EB` (`:426-433`), `QFrame#GroupCard bg #F3F4F6 radius 8` (`:436-440`).
- **`LightBranchStyle`** `gui_qt/theme.py:443-484` — `QProxyStyle` (`:452`) para `PE_IndicatorBranch` desenha triângulo `QPolygonF/QPainterPath` `BRANCH_ARROW_COLOR #9CA3AF` (`:450`) com `r *0.22` (`:464`), `State_Open` (para baixo) vs fechado (para direita) (`:465-477`), alias `LightBranchStyle = None` fallback (`:444`) e `CHECKBOX_STYLE` (`:488-498`), `get_status_color` (`:500-501`).
- **Consumo**: `main_qt.py:33-35` — `if LightBranchStyle is not None: app.setStyle(LightBranchStyle(app.style()))` + `app.setStyleSheet(GLOBAL_STYLE)` (`gui_qt/theme.py:73-441`); Tk usa `ctk.set_appearance_mode Light` (`gui/application.py:153`), Qt usa `GLOBAL_STYLE`.

### 21.3 `gui_qt/manual.py:1-336` — Manual Qt (QDialog + QTextBrowser)

- **Imports/header** `gui_qt/manual.py:1-19` — `QDialog,QVBoxLayout,QHBoxLayout,QFrame,QLabel,QPushButton,QTextBrowser,QScrollArea,QWidget` (`:3-6`), `Qt,QSize` (`:7`), `QIcon,QFont` (`:8`), `VERSION` (`:11`), `_resource_path` (`:13-18`) idêntico a `main_qt.py:8-13` e `gui_qt/main_window.py:11-14`.
- **HTML helpers** `gui_qt/manual.py:23-45` — `_html_header(title)` `26px #4F46E5` (`:23-24`), `_h2` `18px #111827` (`:26-27`), `_h3` `14px #4338CA` (`:29-30`), `_p` `12px #1F2937 line 1.6` (`:32-33`), `_bullet` `• 12px` (`:35-36`), `_ex` `bg #ECFDF5 border-left #10B981 Consolas 11px #065F46` (`:38-39`), `_notice` bold (`:41-42`), `_sep` `hr #E5E7EB` (`:44-45`).
- **`_build_sections()`** `gui_qt/manual.py:47-206` — 9 seções idênticas ao Tk `gui/manual.py` (Início Rápido `🚀 V{VERSION}` `:49`, Abrindo Arquivos `:66-79`, Criar Filtros `:82-106`, Configurar Saída `:109-121`, Operadores Detalhado `:124-140`, Salvando Regras `:143-157`, Exportando `:160-176`, Duplicadas `:179-190`, FAQ `:193-205`), armazenadas em `SECTIONS` dict (`:21`), `ORDER` list (`:209-219`).
- **`ManualDialog(QDialog)`** `gui_qt/manual.py:221-336` — `setWindowTitle f"Guia do Usuário - Filtra KIJO V{VERSION}"` (`:224`), `resize 1100x800` (`:225`), `setWindowIcon(QIcon(_rp("fk_icon.ico")))` (`:226-229`), `setModal(False)` (`:232`), `_setup_ui` (`:233`) e `_load_section(ORDER[0])` (`:234`).
- **`_setup_ui`** `gui_qt/manual.py:236-294` — `QHBoxLayout` margins 0 spacing 0 (`:237-239`), left `menu_frame 260px bg #1F2937` (`:242-245`), `VBoxLayout 10,20,10,20 spacing 2` (`:246-248`), title `📖 MANUAL 22px bold white` (`:250-253`), 9 `QPushButton menu` transparent `#D1D5DB hover #374151` (`:257-274`), `clicked λ _load_section` (`:274`), `QTextBrowser bg white #FFFFFF color #1F2937 padding 20 Segoe UI 12px` (`:282-293`).
- **`_load_section(name)`** `gui_qt/manual.py:296-331` — destaca ativo `bg #4F46E5 color white radius 4` (`:298-310`) vs inativo `transparent #D1D5DB hover #374151` (`:312-326`), `SECTIONS.get(name)` (`:327`), `setHtml` com wrapper `div padding 10 20` (`:329-330`), `verticalScrollBar setValue 0` (`:331`).
- **`show_manual`** `gui_qt/manual.py:333-336` — `show()` + `raise_()` + `activateWindow()` (`:334-336`); Tk equivalente `gui/manual.py:12-16` `CTkToplevel lift`.

### 21.4 `main_qt.py:1-50` — Entrypoint Qt

- **`_resource_path`** `main_qt.py:8-13` — `sys._MEIPASS` fallback `dirname(__file__)` (`:10-12`), retorna `os.path.join(base, relative_path)` (`:13`).
- **`QApplication`** `main_qt.py:16` — `app = QApplication(sys.argv)` (`:16`); Tk usa `ctk.CTk()` (`main.py:25`).
- **Icon** `main_qt.py:18-28` + `42-48` — `app.setWindowIcon(QIcon(icon_path))` (`:22`) e `w.setWindowIcon(QIcon(...))` (`:46`) via `_resource_path("fk_icon.ico")` (`:20,44`), fallback `alt` (`:24-26`), try/except silencia (`:27-28,47-48`); Tk usa `SetCurrentProcessExplicitAppUserModelID` + `iconbitmap` + `iconphoto` `gui/application.py:90,95,120`.
- **Theme** `main_qt.py:30-37` — `from gui_qt.theme import GLOBAL_STYLE, LightBranchStyle` (`:33`), `app.setStyle(LightBranchStyle(app.style()))` se não None (`:34-35`), `app.setStyleSheet(GLOBAL_STYLE)` (`:35`), warning print (`:37`).
- **`MainWindow`** `main_qt.py:39-50` — `from gui_qt.main_window import MainWindow` (`:39`), `w = MainWindow()` (`:41`), `w.setWindowIcon` (`:44-46`), `w.showMaximized()` (`:49`), `sys.exit(app.exec())` (`:50`); Tk usa `AplicacaoVisual(root)` + `root.mainloop()` (`main.py:25-27`), `root.state('zoomed')` (`gui/application.py:285-288`).
- **Qt vs Tk core**: Qt não importa `FileProcessor`/`FilterEngine`/`filtros_salvos.json`/`xxhash`/`polars` — apenas `VERSION` (`core/config.py:2`) e `QIcon`/`GLOBAL_STYLE`; confirma **core unchanged**.

---

## 22. Auditoria — correções aplicadas nesta revisão (rastreabilidade v4.3.0 — terceira auditoria)

- **BUILD.md**: `4.2.0→4.3.0` global — `main.spec:36 name='Filtra_KIJO_V_4_3_0'` (`BUILD.md:9`), `dist\Filtra_KIJO_V_4_3_0.exe` (`:32-33,45`), `$versao="v4.3.0"` + `Copy-Item Filtra_KIJO_V_4_3_0.exe → FiltraKijo_v4.3.0.exe` (`:50-53`), `core/config.py:2 == 4.3.0` (`:71`), `Ícone (v4.3.0)` + `SetCurrentProcessExplicitAppUserModelID v4.3.0` (`:83-90`), `gui/application.py:283,875,1767,1968` call sites + `gerar_icone_fk.py:8` 8 tamanhos (`:94-96`), `VERSION="4.3.0"` (`:105`) e log `Filtra_KIJO_V_4_3_0.exe` (`:106`); **novo §8** `main_qt.spec PySide6` (`BUILD.md:108-130`) com `Analysis(['main_qt.py'])` `collect_all PySide6/shiboken6` `excludes customtkinter/tkinter` `name='Filtra_KIJO_V_4_3_0_Qt'` `QIcon` `GLOBAL_STYLE`.
- **BUSINESS_RULES.md §16b**: novo Icon/DPI/Janela — `gui/application.py:14-20 DPI` (`SetProcessDpiAwareness`), `23-30 _resource_path`, `32-77 _create_fk_image` (gradiente/sólido/rounded/font/shadow), `79-128 _set_window_icon` (AppUserModelID+iconbitmap+iconphoto 6 tamanhos), call sites `283,875,1767,1968`, `_icon_refs` anti-GC (`:121-124`), `gerar_icone_fk.py:8-86` (`:8 tamanhos, 20,16` etc.), `main.spec:4 datas` + `:49 icon`.
- **BUSINESS_RULES.md §21**: novo Qt Visual appendix — `gui_qt/main_window.py:1-176` (QSplitter, header 64, QIcon, GLOBAL_STYLE, example cards hardcoded `80-82`), `gui_qt/theme.py:1-501` (GLOBAL_STYLE QSS `73-441`, LightBranchStyle `444-484`), `gui_qt/manual.py:1-336` (QDialog, QTextBrowser, `_build_sections` 9 seções, `ManualDialog 221-336`), `main_qt.py:1-50` (QApplication, QIcon, GLOBAL_STYLE, showMaximized); **Qt visual shell only, core unchanged** (`filter_engine`, `file_processor`, `config` idênticos Tk/Qt).
- **Stale headers**: `core/filter_engine.py:1` `Filtra_KIJO_V_3_4_0→Filtra_KIJO_V_4_3_0 (header bumped from v3.4.0 → v4.3.0; core unchanged)`, `core/file_processor.py:1` `Filtra_KIJO_V_3_6_0→Filtra_KIJO_V_4_3_0`.
- **Line refs**: `gui/application.py:1647-1654` (antes 1647-1653), `core/filter_engine.py:31-32`, `gui/application.py:1668-1676`, `1743-1759`, `1927-2103`, `core/file_processor.py:39-503`/`509-845`/`851-922`/`928-947` conferidos vs `Select-String -n`.


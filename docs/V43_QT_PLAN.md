# v4.3 Qt - Plano de Migração Correta (base v4.2.0 CTk estável)

> Branch `v4.3` criado de `v4.2.0` (`5ad6ad9` AppUserModelID + `fk_icon.ico` 8 tamanhos). `core/` inalterado.

## O que deu errado em `pyqt5` (apagada)
- `Fixed 180+135+38+38` + `stretch` errado espremeu `💾`/`✕` e `Posição` `Fixed` cortou `X`
- `QComboBox::down-arrow image:url(none)` quadrado preto, `QToolTip` preto, `QFont -1` `text-visible` inválido
- `thread_busca` com `timeout`/`max_lines` e `val_num` fallback duplicado quebrou `pos2=00` (`00`→`0.0` vs string), `on_reject` recursion `RecursionError`

## Como fazer certo em `v4.3`
### 1. Incremental, não 100% de uma vez
- Passo 1: só `main_qt.py` + `gui_qt/theme.py` + `MainWindow` shell vazio (header/corpo vazios) + `QIcon(fk_icon.ico)` nativo - validar ícone único na barra sem duplicar, sem `ctypes`.
- Passo 2: portar `header` (Nova Regra) com `entry 180 Expanding` + `stretch` + `Config 120 + Save 32 + Close 32` `spacing8 margins12` - testar em 1366×768 sem cortes (card `Expanding`).
- Passo 3: `Posição[Nº 60] Condicao[120-150] Valor[100-150] X 32` `AlignLeft` + tooltips, `QComboBox` sem `down-arrow` custom (usa default ▼), `QToolTip` light `#FFF #1F2937`.
- Passo 4: `biblioteca` com `QMenu` right-click só em `item_frame` (não filtro), `colunas_saida`/`nomes_colunas_mapeadas` idêntico `v4.2`.
- Passo 5: `Configurar saída` - copiar **exato** `gui/application.py:1743` `thread_busca` (sem timeout, `pos-1`, `float==val_num` ou `==val`, `tem_pos2_fixa`/`valores_pos2_vistos`, `chave pos1_pos2_pos4`), `exibir_modal_colunas` com `Ctrl` `pos1/2/4` e `nomes_colunas_mapeadas`. Testar com `Teste pequeno 3.txt` `pos2=00` deve achar `KIJO42,00` em <0.1s.

### 2. Testes obrigatórios a cada passo
```powershell
python -m py_compile gui_qt/main_window.py
$env:QT_QPA_PLATFORM="offscreen"; python -c "from gui_qt.main_window import MainWindow; w=MainWindow(); print(w.windowTitle())"
python main_qt.py  # visual: header não corta, X visível, combo ▼, tooltip claro
```

### 3. Build
- Manter `main.spec` CTk (`customtkinter`) e `main_qt.spec` PySide6 (`PySide6.QtCore/Gui/Widgets`, `datas fk_icon.ico`, `name Filtra_KIJO_V_4_3_Qt`) separados até Qt validado.

## Próximos passos
1. Gerar `gui_qt/` passo 1 shell e validar ícone
2. Portar header/corpo incremental com screenshots 1366×768
3. Replicar `abrir_configuracao_colunas` byte-a-byte de `v4.2`

Branch `v4.3` pronta para migração correta.

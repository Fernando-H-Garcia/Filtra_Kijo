# Build - FiltraKIJO

Guia rápido para gerar o `.exe` de forma rápida e confiável no Windows. Baseado no build bem-sucedido de `18/09/2026` (~98s).

## 1. Pré-requisitos

- **Conda** instalado
- Env `filtra-kijo-slim` criado e com dependências instaladas (Python 3.10.18, PyInstaller 6.20.0, customtkinter, pandas, etc.)
- `main.spec` na raiz do projeto (`Filtra_KIJO_V_4_0_0/main.spec:4` -> `datas=[('fk_icon.ico','.')]` + `main.spec:36` -> `name='Filtra_KIJO_V_4_3_0'`, ícone `fk_icon.ico` bundled + `icon='fk_icon.ico'` para o .exe)
- `main_qt.spec` na raiz para variante Qt (`Filtra_KIJO_V_4_0_0/main_qt.spec:4` -> `datas=[('fk_icon.ico','.')]` + `main_qt.spec:36` -> `name='Filtra_KIJO_V_4_3_0_Qt'`, `Analysis(['main_qt.py'])`, `collect_all('PySide6')`)

## 2. Passo a passo (PowerShell)

```powershell
# 1. Ir para a raiz do projeto
cd "C:\Users\Fernando Garcia\OneDrive - Tecsoil Automação e Sistemas S.A\Solinftec\Programas Python\Para Kijos\FiltraKijo\Filtra_KIJO_V_4_0_0"

# 2. ATIVAR O ENV CORRETO (crítico!)
conda activate filtra-kijo-slim
# Confirme: (filtra-kijo-slim) no prompt e
# Python environment: ...\.conda\envs\filtra-kijo-slim no log do PyInstaller

# 3. Limpeza completa (evita cache corrompido / build lento)
Remove-Item -Recurse -Force .\build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\dist -ErrorAction SilentlyContinue

# 4. Build limpo
pyinstaller --clean --noconfirm main.spec
# --clean  : limpa cache em %LOCALAPPDATA%\pyinstaller
# --noconfirm : não pede confirmação para sobrescrever

# 5. Resultado
# dist\Filtra_KIJO_V_4_3_0.exe (~95s, ver log: "Build complete!")
```

### Saída esperada (trecho final do log)

```
95295 INFO: checking EXE
95340 INFO: Copying icon to EXE
95426 INFO: Appending PKG archive to EXE
98789 INFO: Building EXE from EXE-00.toc completed successfully.
98923 INFO: Build complete! The results are available in: ...\dist
```

Resultado: `dist\Filtra_KIJO_V_4_3_0.exe` (v4.3.0, `core/config.py:2` -> `VERSION="4.3.0"`)

## 3. Publicação (opcional)

```powershell
$versao = "v4.3.0"
$dest = "C:\Users\Fernando Garcia\OneDrive - Tecsoil Automação e Sistemas S.A\Solinftec\Programas Python\Para Kijos\FiltraKijo\Executaveis"
Copy-Item "dist\Filtra_KIJO_V_4_3_0.exe" "$dest\FiltraKijo_$versao.exe" -Force
# Ex: FiltraKijo_v4.3.0.exe
```

> Nota: corrigir typo `Fitlrakijo` -> `FiltraKijo`. `Filtra_KIJO_V_4_3_0.exe` já sai com nome correto do spec; cópia acima apenas renomeia para padrão `FiltraKijo_vX.Y.Z.exe`.

## 4. Aprendizados - O que deu errado antes e por quê agora foi rápido

| Erro anterior | Correção | Impacto |
|---|---|---|
| `C:\Anaconda\python.exe -m PyInstaller main.spec --noconfirm` (env `base` / Python 3.11) | Usar `conda activate filtra-kijo-slim` + `pyinstaller --clean ...` direto | `base` tinha PyInstaller diferente, hooks desatualizados e `PYTHONPATH` poluído; `filtra-kijo-slim` (Python 3.10.18) já tem todas as libs pinadas e é ~5-10x mais rápido |
| Não limpar `build/`/`dist/` nem cache | `Remove-Item build/dist` + `--clean` | Evita `Analysis-00.toc` antigo, `warn` obsoleto e reuso de `PYZ-00.pyz` corrompido. No log anterior, `Building Analysis because Analysis-00.toc is non existent` só ocorreu após limpeza |
| `python -m PyInstaller` via `C:\Anaconda` | `pyinstaller` do env ativo (`\.conda\envs\filtra-kijo-slim\Scripts\pyinstaller.exe`) | Resolve `Module search paths` correto e `Extra DLL search directories` para `numpy.libs`/`pandas.libs` |
| Processo isolado `_child.py` (PyInstaller 6.x) preso por tempo indeterminado | Env slim + `--clean` reduziu de >20min (travado) para ~90-100s | Verificado em `18/09/2026`: total `1000 INFO` -> `98923 INFO` = 98s |

## 5. Checklist antes do próximo build

- [ ] `conda env list` mostra `filtra-kijo-slim` ativo
- [ ] `python --version` == `3.10.18` e `pyinstaller --version` == `6.20.0`
- [ ] `fk_icon.ico` existe na raiz (usado em `main.spec:4` como `datas` + `main.spec:49` como `icon`) e `core/config.py:2` == `4.3.0`
- [ ] Ícone da barra de tarefas ok: `gui/application.py:23` `_resource_path` + `gui/application.py:79` `_set_window_icon` (iconbitmap + iconphoto + `SetCurrentProcessExplicitAppUserModelID`) aplicado no `root` e nos `Toplevel`s; Qt usa `QIcon` em `main_qt.py:22,46` e `gui_qt/main_window.py:25`
- [ ] Sem `python.exe` de build anterior rodando (`Get-CimInstance Win32_Process | Where CommandLine -like "*PyInstaller*"`)
- [ ] OneDrive não está sincronizando `dist/` no momento (pode travar `Copying bootloader EXE`)

## 6. Troubleshooting

- **Build trava em `Analyzing modules`**: mate `python.exe _child.py` e refaça com `--clean`. Verifique se o env é `filtra-kijo-slim`, não `base`.
- **Warnings `Hidden import "jinja2" not found!`**: ignorável (hook de pandas). Aparece mesmo no build rápido e não impede `Build complete!`.
- **`dist` vazia após interrupção**: normal se `Stop-Process` foi usado antes de `Building EXE completed`. Refaça o build completo.
- **Antivírus bloqueando `.exe`**: adicione exceção para `dist\` e `Executaveis\`.

## 7. Ícone - Correção do quadrado azul + embaçado + duplicado na barra (v4.3.0)

Problema 1 - quadrado azul: `icon='fk_icon.ico'` no spec só muda o ícone do arquivo `.exe` no Explorer. A janela `CTk` usava ícone padrão (quadrado azul) porque nenhum `iconbitmap`/`iconphoto` era chamado.
Problema 2 - embaçado: `Image.open(ico).resize((32,32))` único é esticado em DPI 125%/150% (32→48px borrado).
Problema 3 - duplicado: fixar o `.exe` antigo (sem AppUserModelID) e rodar o novo (com ID diferente) faz Windows criar 2 botões. O em execução ficava borrado porque usava o ícone da janela, não o do arquivo.

Solução v4.3.0:
- `main.py:10` **DEVE** setar `SetCurrentProcessExplicitAppUserModelID("Tecsoil.FiltraKIJO.v4.3.0")` **antes** de `ctk.CTk()` (unifica fixado vs em execução, evita duplicar)
- `main.spec:4` bundle: `datas=[('fk_icon.ico', '.')]` expõe o ícone em `sys._MEIPASS` quando congelado
- `gui/application.py:23` helper `_resource_path()` resolve `fk_icon.ico` para dev e para `sys._MEIPASS`
- `gui/application.py:32` helper `_create_fk_image(tam)` gera FK nítido nativo em cada tamanho (16,20,24,32,48,64) - sólido em ≤32, `arialbd.ttf` 0.60-0.62*tam, evita resize borrado
- `gui/application.py:79` helper `_set_window_icon()` faz: `SetCurrentProcessExplicitAppUserModelID` + `iconbitmap(ico)` + `iconphoto(True, *6photos)` (16,20,24,32,48,64) - Windows escolhe o melhor para DPI, mantém refs `_icon_refs` contra GC
- Chamado em `gui/application.py:283` no `__init__` do `CTk` e nos `Toplevel`s (`gui/application.py:875` export, `gui/application.py:1767` loading, `gui/application.py:1968` colunas) e em `gui/manual.py:31` para o manual
- `gerar_icone_fk.py:8` regenerado com 8 tamanhos (16,20,24,32,48,64,128,256) nítidos, sólido em pequenos
- Resultado: ícone FK idêntico e nítido no Explorer, na barra fixada e na janela em execução (mesmo botão, sem duplicar), em `python main.py` e no `.exe`

**Se ainda duplicar/borrar após atualizar o exe:** desafixe o antigo, rode o novo `Filtra_KIJO_V_4_3_0.exe`, com ele aberto clique direito no ícone **em execução** (o nítido) → `Fixar na barra de tarefas`. O atalho novo herda o mesmo AppUserModelID e agrupará corretamente.

## 8. Build Qt (PySide6) — main_qt.spec (v4.3 visual shell)

Variante Qt é **visual shell only** (v4.3): `gui_qt/` + `main_qt.py` apenas reimplementa UI com PySide6; `core/` (`filter_engine`, `file_processor`, `config`) permanece idêntico e compartilhado com Tk.

- **Entrypoint**: `main_qt.py:1-50` — `QApplication`, `_resource_path` (`main_qt.py:8-13`), `app.setWindowIcon(QIcon(icon_path))` (`main_qt.py:22,46`), `GLOBAL_STYLE` + `LightBranchStyle` (`main_qt.py:33-35`), `MainWindow` (`main_qt.py:39-41`), `showMaximized` (`main_qt.py:49`).
- **Spec**: `main_qt.spec:1-50` — `Analysis(['main_qt.py'])`, `datas=[('fk_icon.ico','.')]` (`main_qt.spec:4`), `collect_all('PySide6')` + `collect_all('shiboken6')` (`main_qt.spec:7-9`), `excludes=['customtkinter','tkinter','PyQt5','scipy',...]` (`main_qt.spec:20-24`), `exe name='Filtra_KIJO_V_4_3_0_Qt'` (`main_qt.spec:36`), `icon='fk_icon.ico'` (`main_qt.spec:49`), `console=False`.
- **Comando**:
```powershell
conda activate filtra-kijo-slim
# requer PySide6 instalado no env: pip install PySide6
Remove-Item -Recurse -Force .\build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\dist -ErrorAction SilentlyContinue
pyinstaller --clean --noconfirm main_qt.spec
# dist\Filtra_KIJO_V_4_3_0_Qt.exe
```
- **Ícone Qt**: via `QIcon` (`gui_qt/main_window.py:25`, `main_qt.py:22`) — não usa `AppUserModelID` (Qt gerencia agrupamento nativo); `fk_icon.ico` bundled via `datas` + `_resource_path` igual ao Tk.
- **Tema Qt**: `gui_qt/theme.py:1-501` — `GLOBAL_STYLE` (QSS light, `ACCENT #4F46E5`) aplicado em `main_qt.py:35` via `app.setStyleSheet(GLOBAL_STYLE)`; `LightBranchStyle` opcional (`theme.py:444-484`) para `QTreeView` branch arrow.
- **Obs**: `core/config.py:2` `VERSION="4.3.0"` único para ambos exes; `main_qt.spec` compartilha `fk_icon.ico` e `VERSION`; Qt é preview visual com cards hardcoded (`gui_qt/main_window.py:80-82`), sem lógica de filtros/processamento ainda — core inalterado.

## 9. Referências

- `main.py:1-27` - entrypoint Tk (`Analysis(['main.py'])`)
- `main_qt.py:1-50` - entrypoint Qt (`Analysis(['main_qt.py'])`, `QIcon`, `GLOBAL_STYLE`)
- `main.spec:1-50` - spec Tk completo (coletando `customtkinter`, excluindo `PyQt5`, `scipy`, etc., `name='Filtra_KIJO_V_4_3_0'`)
- `main_qt.spec:1-50` - spec Qt completo (coletando `PySide6`/`shiboken6`, excluindo `customtkinter`/`tkinter`, `name='Filtra_KIJO_V_4_3_0_Qt'`)
- `core/config.py:2` - `VERSION="4.3.0"` (exibido em `gui/application.py:273` e `gui/manual.py:18` e `gui_qt/main_window.py:21` e `gui_qt/manual.py:224`)
- `gui_qt/main_window.py:1-176` - Janela Qt (QSplitter, header 64, QIcon, example cards)
- `gui_qt/theme.py:1-501` - Tema Qt (GLOBAL_STYLE, LightBranchStyle)
- `gui_qt/manual.py:1-336` - Manual Qt (QDialog, QTextBrowser)
- Log completo do build rápido: `18/09/2026 10:??` em PowerShell `filtra-kijo-slim` (atualizado para `Filtra_KIJO_V_4_3_0.exe` / `Filtra_KIJO_V_4_3_0_Qt.exe`)

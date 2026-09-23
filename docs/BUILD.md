# Build - FiltraKIJO

Guia rápido para gerar o `.exe` de forma rápida e confiável no Windows. Baseado no build bem-sucedido de `18/09/2026` (~98s).

## 1. Pré-requisitos

- **Conda** instalado
- Env `filtra-kijo-slim` criado e com dependências instaladas (Python 3.10.18, PyInstaller 6.20.0, customtkinter, pandas, etc.)
- `main.spec` na raiz do projeto (`Filtra_KIJO_V_4_0_0/main.spec:4` -> `datas=[('fk_icon.ico','.')]` + `main.spec:36` -> `name='Filtra_KIJO_V_4_2_0'`, ícone `fk_icon.ico` bundled + `icon='fk_icon.ico'` para o .exe)

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
# dist\Filtra_KIJO_V_4_2_0.exe (~95s, ver log: "Build complete!")
```

### Saída esperada (trecho final do log)

```
95295 INFO: checking EXE
95340 INFO: Copying icon to EXE
95426 INFO: Appending PKG archive to EXE
98789 INFO: Building EXE from EXE-00.toc completed successfully.
98923 INFO: Build complete! The results are available in: ...\dist
```

Resultado: `dist\Filtra_KIJO_V_4_2_0.exe` (v4.2.1, `core/config.py:2` -> `VERSION="4.2.0"` mantido, docs `BUSINESS_RULES v4.2.1`)

## 2.1 Histórico de builds (aprendizado)

- `18/09/2026 ~98s` - build base v4.2.0
- `23/09/2026 11:10 ~107s` - fix renomear biblioteca espremido (440x240 height44), inclui menu contexto
- `23/09/2026 11:56 ~102s` - fix 1224 `.sorted` temporário + `del df+gc` antes de `_safe_replace`
- `23/09/2026 12:12 ~127s` - fix `NoneType stat` (`if temp_csv_final:` antes de `_safe_remove`)
- `23/09/2026 14:08 ~103s` - limpeza temps Excel/TXT pós-replace
- `23/09/2026 17:00 ~113s` - **v4.2.1 remove ordenação timestamp** (volta 4.1), mantém `_safe_*` retry 1224 e cancelamento

## 3. Publicação (opcional)

```powershell
$versao = "v4.2.0"
$dest = "C:\Users\Fernando Garcia\OneDrive - Tecsoil Automação e Sistemas S.A\Solinftec\Programas Python\Para Kijos\FiltraKijo\Executaveis"
Copy-Item "dist\Filtra_KIJO_V_4_2_0.exe" "$dest\FiltraKijo_$versao.exe" -Force
# Ex: FiltraKijo_v4.2.0.exe
```

> Nota: corrigir typo `Fitlrakijo` -> `FiltraKijo`. `Filtra_KIJO_V_4_2_0.exe` já sai com nome correto do spec; cópia acima apenas renomeia para padrão `FiltraKijo_vX.Y.Z.exe`.

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
- [ ] `fk_icon.ico` existe na raiz (usado em `main.spec:4` como `datas` + `main.spec:49` como `icon`) e `core/config.py:2` == `4.2.0`
- [ ] Ícone da barra de tarefas ok: `gui/application.py:24` `_resource_path` + `_set_window_icon` (iconbitmap + iconphoto + `SetCurrentProcessExplicitAppUserModelID`) aplicado no `root` e nos `Toplevel`s
- [ ] Sem `python.exe` de build anterior rodando (`Get-CimInstance Win32_Process | Where CommandLine -like "*PyInstaller*"`)
- [ ] OneDrive não está sincronizando `dist/` no momento (pode travar `Copying bootloader EXE`)

## 6. Troubleshooting

- **Build trava em `Analyzing modules`**: mate `python.exe _child.py` e refaça com `--clean`. Verifique se o env é `filtra-kijo-slim`, não `base`.
- **Warnings `Hidden import "jinja2" not found!`**: ignorável (hook de pandas). Aparece mesmo no build rápido e não impede `Build complete!`.
- **`dist` vazia após interrupção**: normal se `Stop-Process` foi usado antes de `Building EXE completed`. Refaça o build completo.
- **Antivírus bloqueando `.exe`**: adicione exceção para `dist\` e `Executaveis\`.
- **`Copy-Item` falha "arquivo sendo usado por outro processo"**: `taskkill /f /im FiltraKijo_v4.2.0.exe; Start-Sleep 1; Copy-Item ... -Force` (`Executaveis` em uso por teste manual).
- **`stat: path should be string... not NoneType`**: era `temp_csv_final = None` antes de `_safe_remove`; fix `if temp_csv_final:` (`core/file_processor.py:509,554`).
- **`ERROR_USER_MAPPED_FILE 1224`**: `pl.read_csv(... timestamp, raw_kijo)` mapeia `t_file`; `write_csv` no mesmo `t_file` falha. Fix v4.2.1 → remove sort + `_safe_replace/_safe_remove` retry `0.05*2^n` + `_ensure_reader_closed`.

## 7. Ícone - Correção do quadrado azul + embaçado + duplicado na barra (v4.2.0)

Problema 1 - quadrado azul: `icon='fk_icon.ico'` no spec só muda o ícone do arquivo `.exe` no Explorer. A janela `CTk` usava ícone padrão (quadrado azul) porque nenhum `iconbitmap`/`iconphoto` era chamado.
Problema 2 - embaçado: `Image.open(ico).resize((32,32))` único é esticado em DPI 125%/150% (32→48px borrado).
Problema 3 - duplicado: fixar o `.exe` antigo (sem AppUserModelID) e rodar o novo (com ID diferente) faz Windows criar 2 botões. O em execução ficava borrado porque usava o ícone da janela, não o do arquivo.

Solução v4.2.0:
- `main.py:5` **DEVE** setar `SetCurrentProcessExplicitAppUserModelID("Tecsoil.FiltraKIJO.v4.2.0")` **antes** de `ctk.CTk()` (unifica fixado vs em execução, evita duplicar)
- `main.spec:4` bundle: `datas=[('fk_icon.ico', '.')]` expõe o ícone em `sys._MEIPASS` quando congelado
- `gui/application.py:23` helper `_resource_path()` resolve `fk_icon.ico` para dev e para `sys._MEIPASS`
- `gui/application.py:32` helper `_create_fk_image(tam)` gera FK nítido nativo em cada tamanho (16,20,24,32,48,64) - sólido em ≤32, `arialbd.ttf` 0.60-0.62*tam, evita resize borrado
- `gui/application.py:70` helper `_set_window_icon()` faz: `SetCurrentProcessExplicitAppUserModelID` + `iconbitmap(ico)` + `iconphoto(True, *6photos)` (16,20,24,32,48,64) - Windows escolhe o melhor para DPI, mantém refs `_icon_refs` contra GC
- Chamado em `gui/application.py:205` no `__init__` do `CTk` e nos `Toplevel`s (export, config colunas, loading) e em `gui/manual.py:22` para o manual
- `gerar_icone_fk.py:6` regenerado com 8 tamanhos (16,20,24,32,48,64,128,256) nítidos, sólido em pequenos
- Resultado: ícone FK idêntico e nítido no Explorer, na barra fixada e na janela em execução (mesmo botão, sem duplicar), em `python main.py` e no `.exe`

**Se ainda duplicar/borrar após atualizar o exe:** desafixe o antigo, rode o novo `Filtra_KIJO_V_4_2_0.exe`, com ele aberto clique direito no ícone **em execução** (o nítido) → `Fixar na barra de tarefas`. O atalho novo herda o mesmo AppUserModelID e agrupará corretamente.

## 8. Referências

- `main.py:1` - entrypoint (`Analysis(['main.py'])`)
- `main.spec:1` - spec completo (coletando `customtkinter`, excluindo `PyQt5`, `scipy`, etc.)
- `core/config.py:2` - `VERSION="4.2.0"` (exibido em `gui/application.py:273` e `gui/manual.py:18`)
- Log completo do build rápido: `18/09/2026 10:??` em PowerShell `filtra-kijo-slim` (atualizado para `Filtra_KIJO_V_4_2_0.exe`)
- `docs/BUSINESS_RULES.md:17` - changelog v4.2.1 (1224, NoneType, cancelamento, renomear gap-reuse)
- `gui/manual.py:413-580` - ajuda atualizada: renomear botão direito, `✕ CANCELAR`, ordem saída v4.1

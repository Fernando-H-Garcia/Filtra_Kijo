# gui/manual.py
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from core.config import VERSION

class ManualDinamico:
    def __init__(self, root):
        self.root = root
        self.janela_manual = None

    def mostrar_manual(self):
        if self.janela_manual and self.janela_manual.winfo_exists():
            self.janela_manual.lift()
            return

        self.janela_manual = ctk.CTkToplevel(self.root)
        self.janela_manual.title(f"Guia do Usuário - Filtra KIJO V{VERSION}")
        self.janela_manual.geometry("1100x800")
        # Ícone nítido idêntico ao app (múltiplos tamanhos, evita embaçado)
        try:
            import os, sys, ctypes
            try:
                b = sys._MEIPASS  # type: ignore
            except Exception:
                b = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            p = os.path.join(b, "fk_icon.ico")
            if not os.path.exists(p):
                p = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "fk_icon.ico")
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Tecsoil.FiltraKIJO.v4.2.0")
            except Exception:
                pass
            if os.path.exists(p):
                try:
                    self.janela_manual.iconbitmap(p)
                except Exception:
                    pass
            try:
                from PIL import Image, ImageTk, ImageDraw, ImageFont
                def _mk(tam):
                    im = Image.new('RGBA', (tam, tam), (0, 0, 0, 0))
                    dr = ImageDraw.Draw(im)
                    if tam >= 48:
                        for y in range(tam):
                            r = int(18 + (y / tam) * 14); g = int(58 + (y / tam) * 38); b2 = int(138 + (y / tam) * 58)
                            dr.line([(0, y), (tam-1, y)], fill=(r,g,b2,255))
                    else:
                        dr.rectangle([(0,0),(tam-1,tam-1)], fill=(28,78,168,255))
                    ra = max(tam//6,2)
                    ms = Image.new('L',(tam,tam),0); d2=ImageDraw.Draw(ms)
                    d2.rounded_rectangle([(0,0),(tam-1,tam-1)], radius=ra, fill=255)
                    im.putalpha(ms)
                    fs = int(tam*0.58) if tam>=64 else int(tam*0.62) if tam>=32 else int(tam*0.60)
                    ft=None
                    for cand in ["C:/Windows/Fonts/arialbd.ttf","arialbd.ttf","C:/Windows/Fonts/arial.ttf","arial.ttf"]:
                        try:
                            ft=ImageFont.truetype(cand, fs); break
                        except OSError:
                            continue
                    if ft is None: ft=ImageFont.load_default()
                    bb=dr.textbbox((0,0),"FK",font=ft); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
                    x=(tam-tw)//2-bb[0]; y=(tam-th)//2-bb[1]-max(1,tam//32)
                    if tam>=48: dr.text((x+1,y+1),"FK",fill=(0,0,0,90),font=ft)
                    elif tam>=32: dr.text((x+1,y+1),"FK",fill=(0,0,0,60),font=ft)
                    dr.text((x,y),"FK",fill=(255,255,255,255),font=ft)
                    return im
                phs=[]
                for sz in [16,20,24,32,48,64]:
                    try:
                        phs.append(ImageTk.PhotoImage(_mk(sz)))
                    except Exception:
                        continue
                if phs:
                    self.janela_manual.iconphoto(True, *phs)
                    self.janela_manual._icon_photos = phs
            except Exception:
                pass
        except Exception:
            pass
        
        self.janela_manual.attributes("-topmost", True)
        self.janela_manual.lift()
        self.janela_manual.focus_force()
        self.janela_manual.after(1000, lambda: self.janela_manual.attributes("-topmost", False))

        self.janela_manual.grid_columnconfigure(0, weight=1, minsize=260)
        self.janela_manual.grid_columnconfigure(1, weight=4)
        self.janela_manual.grid_rowconfigure(0, weight=1)

        self.frame_menu = ctk.CTkFrame(self.janela_manual, corner_radius=0, fg_color="#1F2937")
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.frame_menu, text="📖 MANUAL", text_color="white", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=40)

        self.secoes = {
            "🚀 Início Rápido": self._conteudo_bem_vindo,
            "📂 Abrindo Arquivos": self._conteudo_abrir_arquivos,
            "🎯 Como Criar Filtros": self._conteudo_filtros,
            "⚙️ Configurar Saída": self._conteudo_configurar_saida,
            "🔎 Operadores (Detalhado)": self._conteudo_operadores,
            "💾 Salvando Regras": self._conteudo_biblioteca,
            "📤 Exportando Resultados": self._conteudo_exportacao,
            "🔍 Analisando Duplicadas": self._conteudo_duplicadas,
            "❓ Perguntas Frequentes": self._conteudo_faq,
        }

        self.botoes_menu = []
        for nome in self.secoes:
            btn = ctk.CTkButton(self.frame_menu, text=nome, fg_color="transparent", text_color="#D1D5DB",
                               hover_color="#374151", anchor="w",
                               font=ctk.CTkFont(size=14, weight="bold"), height=50,
                               command=lambda n=nome: self._carregar_secao(n))
            btn.pack(fill="x", padx=10, pady=2)
            self.botoes_menu.append((nome, btn))

        self.frame_conteudo = ctk.CTkFrame(self.janela_manual, fg_color="#F9FAFB")
        self.frame_conteudo.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        self.text_area = tk.Text(self.frame_conteudo, bg="#FFFFFF", fg="#1F2937",
                                font=("Segoe UI", 12), wrap=tk.WORD, relief="flat", 
                                padx=40, pady=40)
        self.text_area.pack(fill="both", expand=True)
        
        self.text_area.tag_configure("h1", font=("Segoe UI", 26, "bold"), foreground="#4F46E5", spacing3=30)
        self.text_area.tag_configure("h2", font=("Segoe UI", 18, "bold"), foreground="#111827", spacing1=35, spacing3=15)
        self.text_area.tag_configure("h3", font=("Segoe UI", 14, "bold"), foreground="#4338CA", spacing1=20, spacing3=10)
        self.text_area.tag_configure("body", font=("Segoe UI", 12), spacing3=12)
        self.text_area.tag_configure("destaque", font=("Segoe UI", 12, "bold"), foreground="#4F46E5", spacing3=12)
        self.text_area.tag_configure("exemplo", font=("Consolas", 11), foreground="#065F46", background="#ECFDF5", spacing1=8, spacing3=8, lmargin1=30, lmargin2=30)
        self.text_area.tag_configure("aviso", font=("Segoe UI", 12, "bold"), foreground="#B45309", spacing3=12)
        self.text_area.tag_configure("bullet", font=("Segoe UI", 12), lmargin1=30, lmargin2=50, spacing3=10)
        self.text_area.tag_configure("separador", font=("Segoe UI", 6), foreground="#E5E7EB", spacing1=10, spacing3=10)

        self._carregar_secao("🚀 Início Rápido")

    def _carregar_secao(self, nome):
        for n, btn in self.botoes_menu:
            if n == nome:
                btn.configure(fg_color="#4F46E5", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#D1D5DB")
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.secoes[nome]()
        self.text_area.config(state=tk.DISABLED)

    def _inserir(self, texto, tag="body"):
        self.text_area.insert(tk.END, texto + "\n", tag)

    def _separador(self):
        self._inserir("─" * 70, "separador")

    # ==========================================
    # SEÇÃO 1 — INÍCIO RÁPIDO
    # ==========================================
    def _conteudo_bem_vindo(self):
        self._inserir(f"🚀 Bem-vindo ao Filtra KIJO V{VERSION}", "h1")

        self._inserir("O Filtra KIJO serve para filtrar dados dentro de arquivos KIJO (GPRS). "
                       "Imagine que você tem um arquivo com milhares de linhas e precisa encontrar "
                       "apenas as linhas onde uma determinada coluna tem um valor específico — "
                       "é exatamente isso que este programa faz.", "body")

        self._separador()
        self._inserir("Como funciona em 4 passos:", "h2")

        self._inserir("1️  ABRIR — Clique no botão \"📂 Abrir Arquivo\" (canto superior direito) "
                       "e selecione um ou mais arquivos .txt do KIJO.", "bullet")

        self._inserir("2️  FILTRAR — Crie uma regra clicando em \"+ Nova Regra\". "
                       "Defina a posição (coluna), o operador e o valor desejado.", "bullet")

        self._inserir("3️  PROCESSAR — Clique em \"⚡ Iniciar Processamento\", "
                       "escolha o formato (TXT ou CSV) e a pasta de destino.", "bullet")

        self._inserir("4️  RESULTADO — O programa gera um novo arquivo contendo "
                       "somente as linhas que passaram no filtro.", "bullet")

        self._separador()
        self._inserir("Exemplo prático:", "h2")

        self._inserir("Suponha que você quer encontrar todas as linhas onde a coluna 5 "
                       "tem o valor \"100\":", "body")

        self._inserir("  → Posição: 5", "exemplo")
        self._inserir("  → Operador: Igual a", "exemplo")
        self._inserir("  → Valor: 100", "exemplo")

        self._inserir("O programa vai ler todas as linhas do arquivo, verificar a coluna 5 "
                       "de cada uma, e exportar apenas aquelas onde o valor é \"100\".", "body")

    # ==========================================
    # SEÇÃO 2 — ABRINDO ARQUIVOS
    # ==========================================
    def _conteudo_abrir_arquivos(self):
        self._inserir("📂 Abrindo Arquivos", "h1")

        self._inserir("Como selecionar arquivos:", "h2")

        self._inserir("1. Clique no botão \"📂 Abrir Arquivo\" no canto superior direito.", "bullet")
        self._inserir("2. Na janela que abrir, navegue até a pasta dos seus arquivos KIJO.", "bullet")
        self._inserir("3. Selecione um ou mais arquivos .txt (segure Ctrl para selecionar vários).", "bullet")
        self._inserir("4. Clique em \"Abrir\".", "bullet")

        self._inserir("Após selecionar, o programa mostrará no topo da tela quantos arquivos "
                       "foram carregados (ex: \"✅ 15 arquivos selecionados\").", "body")
                       
        self._inserir("💡 O programa lembra automaticamente a última pasta de onde você abriu e salvou arquivos. Ao reabrir o aplicativo, ele voltará direto para as mesmas pastas.", "destaque")

        self._separador()
        self._inserir("Como ver quais arquivos foram selecionados:", "h2")

        self._inserir("Passe o mouse sobre o texto \"✅ X arquivos selecionados\" no topo da tela. "
                       "Um balão (tooltip) aparecerá mostrando o nome de cada arquivo.", "body")

        self._inserir("💡 Se a lista for longa, use a rodinha do mouse para rolar dentro do balão.", "destaque")

        self._separador()
        self._inserir("Posso processar vários arquivos de uma vez?", "h3")

        self._inserir("Sim! Quando você seleciona múltiplos arquivos, o programa processa "
                       "todos eles em sequência e combina os resultados em um único arquivo de saída. "
                       "Isso é útil quando seus dados estão divididos em vários arquivos.", "body")

    # ==========================================
    # SEÇÃO 3 — COMO CRIAR FILTROS
    # ==========================================
    def _conteudo_filtros(self):
        self._inserir("🎯 Como Criar Filtros", "h1")

        self._inserir("O que é um filtro?", "h2")

        self._inserir("Um filtro é uma regra que diz ao programa: \"quero apenas as linhas "
                       "onde a coluna X tem o valor Y\". Você pode criar quantos filtros quiser.", "body")

        self._separador()
        self._inserir("Passo a passo para criar um filtro:", "h2")

        self._inserir("1. Clique em \"+ Nova Regra\" na área central da tela.", "bullet")
        self._inserir("2. Um card (cartão) aparecerá com uma condição em branco.", "bullet")
        self._inserir("3. Preencha os três campos:", "bullet")

        self._inserir("  → Posição: o número da coluna no KIJO (ex: 5)", "exemplo")
        self._inserir("  → Operador: escolha na lista (ex: \"Igual a\")", "exemplo")
        self._inserir("  → Valor: o que você quer buscar (ex: 100)", "exemplo")

        self._separador()
        self._inserir("O que é \"Posição\"?", "h2")

        self._inserir("Cada linha do arquivo KIJO é dividida em colunas separadas por vírgula. "
                       "A \"Posição\" é o número da coluna que você quer verificar.", "body")

        self._inserir("Exemplo de uma linha KIJO:", "h3")
        self._inserir("      KIJO71,ABC123,2024,01,15,100,200,DADOS,...", "exemplo")
        self._inserir("  Pos:  1       2     3   4  5  6   7    8", "exemplo")

        self._inserir("Neste exemplo, se você quiser filtrar pelo valor \"100\", "
                       "deve colocar Posição = 6, porque \"100\" está na 6ª coluna.", "body")

        self._separador()
        self._inserir("Adicionando várias condições ao mesmo filtro:", "h2")

        self._inserir("Dentro de cada card de regra, clique em \"+ Adicionar Condição\" "
                       "para adicionar mais condições. Todas as condições dentro do mesmo "
                       "card devem ser verdadeiras para a linha ser incluída (lógica E).", "body")

        self._inserir("Exemplo: buscar linhas onde a coluna 3 é \"2024\" E a coluna 6 é maior que 50:", "h3")
        self._inserir("  Condição 1 → Posição: 3 | Operador: Igual a     | Valor: 2024", "exemplo")
        self._inserir("  Condição 2 → Posição: 6 | Operador: Maior que   | Valor: 50", "exemplo")

        self._separador()
        self._inserir("Usando múltiplos filtros (lógica OU):", "h2")

        self._inserir("Se você criar mais de um card de regra (clicando em \"+ Nova Regra\" "
                       "novamente), o programa exportará linhas que atendam a QUALQUER um "
                       "dos filtros. Ou seja, entre filtros diferentes a lógica é OU.", "body")

        self._inserir("Exemplo:", "h3")
        self._inserir("  Filtro 1: Posição 5 → Igual a → 100", "exemplo")
        self._inserir("  Filtro 2: Posição 5 → Igual a → 200", "exemplo")
        self._inserir("  Resultado: exporta linhas onde coluna 5 é 100 OU 200.", "exemplo")

        self._separador()
        self._inserir("Como remover uma condição ou filtro:", "h2")

        self._inserir("• Para remover uma condição: clique no botão ✕ ao lado dela.", "bullet")
        self._inserir("• Para remover o filtro inteiro: clique no botão ✕ no canto superior "
                       "direito do card.", "bullet")

    # ==========================================
    # SEÇÃO 4 — OPERADORES (DETALHADO)
    # ==========================================
    def _conteudo_operadores(self):
        self._inserir("🔎 Operadores — Guia Detalhado", "h1")

        self._inserir("Ao criar uma condição, você escolhe um operador na lista suspensa. "
                       "Abaixo está a explicação de cada um com exemplos práticos.", "body")

        self._separador()

        # --- Igual a ---
        self._inserir("\"Igual a\"", "h2")
        self._inserir("Seleciona linhas onde o valor da coluna é exatamente igual ao que você digitou.", "body")
        self._inserir("Exemplo: Posição 3 | Igual a | 2024", "h3")
        self._inserir("  Linha: KIJO71,ABC,2024,01  →  coluna 3 = \"2024\"  ✅ Incluída", "exemplo")
        self._inserir("  Linha: KIJO1B,ABC,2023,01  →  coluna 3 = \"2023\"  ❌ Excluída", "exemplo")
        self._inserir("  Linha: KIJO1D,ABC,2024X,01 →  coluna 3 = \"2024X\" ❌ Excluída", "exemplo")
        self._inserir("💡 Funciona tanto com números quanto com textos. "
                       "A comparação é exata (\"2024\" não é igual a \"2024X\").", "destaque")

        self._separador()

        # --- Diferente de ---
        self._inserir("\"Diferente de\"", "h2")
        self._inserir("Seleciona linhas onde o valor da coluna é qualquer coisa DIFERENTE do que você digitou.", "body")
        self._inserir("Exemplo: Posição 3 | Diferente de | 2023", "h3")
        self._inserir("  Linha com coluna 3 = \"2024\"  ✅ Incluída (é diferente de 2023)", "exemplo")
        self._inserir("  Linha com coluna 3 = \"2023\"  ❌ Excluída (é igual a 2023)", "exemplo")

        self._separador()

        # --- Maior que ---
        self._inserir("\"Maior que\"", "h2")
        self._inserir("Seleciona linhas onde o valor numérico da coluna é MAIOR que o informado.", "body")
        self._inserir("Exemplo: Posição 6 | Maior que | 50", "h3")
        self._inserir("  Coluna 6 = 100   ✅ Incluída (100 > 50)", "exemplo")
        self._inserir("  Coluna 6 = 50    ❌ Excluída (50 não é maior que 50)", "exemplo")
        self._inserir("  Coluna 6 = 30    ❌ Excluída (30 < 50)", "exemplo")
        self._inserir("⚠️ Funciona apenas com valores numéricos. Se a coluna contiver texto, "
                       "a linha será ignorada.", "aviso")

        self._separador()

        # --- Menor que ---
        self._inserir("\"Menor que\"", "h2")
        self._inserir("Seleciona linhas onde o valor numérico da coluna é MENOR que o informado.", "body")
        self._inserir("Exemplo: Posição 6 | Menor que | 200", "h3")
        self._inserir("  Coluna 6 = 100   ✅ Incluída (100 < 200)", "exemplo")
        self._inserir("  Coluna 6 = 200   ❌ Excluída (200 não é menor que 200)", "exemplo")
        self._inserir("  Coluna 6 = 300   ❌ Excluída (300 > 200)", "exemplo")

        self._separador()

        # --- Maior ou igual a ---
        self._inserir("\"Maior ou igual a\"", "h2")
        self._inserir("Seleciona linhas onde o valor numérico é MAIOR OU IGUAL ao informado.", "body")
        self._inserir("Exemplo: Posição 6 | Maior ou igual a | 50", "h3")
        self._inserir("  Coluna 6 = 100   ✅ Incluída (100 >= 50)", "exemplo")
        self._inserir("  Coluna 6 = 50    ✅ Incluída (50 >= 50)", "exemplo")
        self._inserir("  Coluna 6 = 30    ❌ Excluída (30 < 50)", "exemplo")

        self._separador()

        # --- Menor ou igual a ---
        self._inserir("\"Menor ou igual a\"", "h2")
        self._inserir("Seleciona linhas onde o valor numérico é MENOR OU IGUAL ao informado.", "body")
        self._inserir("Exemplo: Posição 6 | Menor ou igual a | 200", "h3")
        self._inserir("  Coluna 6 = 100   ✅ Incluída (100 <= 200)", "exemplo")
        self._inserir("  Coluna 6 = 200   ✅ Incluída (200 <= 200)", "exemplo")
        self._inserir("  Coluna 6 = 300   ❌ Excluída (300 > 200)", "exemplo")

        self._separador()

        # --- Contém ---
        self._inserir("\"Contém\"", "h2")
        self._inserir("Seleciona linhas onde o valor da coluna contém o texto informado "
                       "em qualquer parte (não precisa ser exato).", "body")
        self._inserir("Exemplo: Posição 2 | Contém | ABC", "h3")
        self._inserir("  Coluna 2 = \"ABC123\"    ✅ Incluída (contém \"ABC\")", "exemplo")
        self._inserir("  Coluna 2 = \"XYZABC99\"  ✅ Incluída (contém \"ABC\")", "exemplo")
        self._inserir("  Coluna 2 = \"XYZ999\"    ❌ Excluída (não contém \"ABC\")", "exemplo")
        self._inserir("💡 Útil quando você quer buscar por parte de um código ou nome.", "destaque")

        self._separador()

        # --- Buscar vazio ---
        self._inserir("Buscar por valores vazios:", "h2")
        self._inserir("Se você quiser encontrar linhas onde uma coluna está VAZIA, "
                       "use o operador \"Igual a\" e deixe o campo Valor em branco.", "body")
        self._inserir("  Posição: 8 | Operador: Igual a | Valor: (vazio)", "exemplo")
        self._inserir("⚠️ Se a linha não possuir a coluna informada (ex: filtrar coluna 8 "
                       "mas a linha só tem 7 colunas), essa linha será automaticamente "
                       "excluída do resultado.", "aviso")

    # ==========================================
    # SEÇÃO 4.5 — CONFIGURAR SAÍDA
    # ==========================================
    def _conteudo_configurar_saida(self):
        self._inserir("⚙️ Configurando Colunas de Saída", "h1")

        self._inserir("Agora, você pode escolher exatamente quais colunas deseja exportar para cada filtro individualmente! "
                       "Isso permite que regras diferentes no mesmo processamento gerem formatos de colunas totalmente diferentes.", "body")

        self._separador()
        self._inserir("Como funciona o fluxo de configuração:", "h2")

        self._inserir("1. Selecione os arquivos de entrada primeiro. A criação de regras ficará bloqueada até carregar pelo menos um arquivo.", "bullet")
        self._inserir("2. Crie uma regra/filtro normalmente.", "bullet")
        self._inserir("3. No cabeçalho do card da regra, clique no botão \"⚙️ Configurar Saída\".", "bullet")
        self._inserir("4. O sistema irá realizar uma busca super rápida (em segundo plano) pelos seus arquivos e encontrar a PRIMEIRA ocorrência que atenda a essa regra.", "bullet")
        self._inserir("5. Uma janela pop-up será exibida com uma tabela listando cada coluna encontrada na linha e uma caixa de seleção (checkbox).", "bullet")
        self._inserir("6. Conforme você seleciona ou desmarca as caixas de colunas, uma PRÉVIA em tempo real no final da janela mostra exatamente como a linha ficará salva no arquivo final!", "bullet")

        self._separador()
        self._inserir("Vantagens:", "h2")
        self._inserir("• Economia de espaço e clareza: Remova campos irrelevantes que só poluem sua planilha ou TXT.", "bullet")
        self._inserir("• Formatação sob medida: O Filtro A pode exportar as colunas 1, 2 e 5; enquanto o Filtro B no mesmo processamento pode exportar 1, 3 e 4. Suas sequências originais e integridade dos dados são mantidas.", "bullet")

    # ==========================================
    # SEÇÃO 5 — SALVANDO REGRAS
    # ==========================================
    def _conteudo_biblioteca(self):
        self._inserir("💾 Salvando e Reutilizando Regras", "h1")

        self._inserir("Se você usa os mesmos filtros com frequência, pode salvá-los "
                       "na Biblioteca de Regras para não precisar recriá-los toda vez.", "body")

        self._separador()
        self._inserir("Como salvar uma regra:", "h2")

        self._inserir("1. Crie uma regra e configure todas as condições desejadas.", "bullet")
        self._inserir("2. No topo do card da regra, digite um nome descritivo "
                       "(ex: \"Filtro Equipamento ABC\").", "bullet")
        self._inserir("3. Clique no ícone de disquete 💾 dentro do card.", "bullet")
        self._inserir("4. A regra será salva e aparecerá no painel \"📜 Regras Salvas\" "
                       "à direita da tela.", "bullet")

        self._separador()
        self._inserir("Como usar uma regra salva:", "h2")

        self._inserir("Basta clicar no nome da regra no painel \"📜 Regras Salvas\" à direita. "
                       "Um novo card será criado automaticamente na área central, já preenchido "
                       "com todas as condições que foram salvas.", "body")

        self._inserir("💡 Você pode usar uma regra salva e ainda modificá-la antes de processar. "
                       "As alterações só serão salvas se você clicar no 💾 novamente.", "destaque")

        self._separador()
        self._inserir("Como renomear uma regra salva:", "h2")

        self._inserir("Clique com o botão direito sobre a regra no painel \"📜 Regras Salvas\" "
                       "e escolha \"✏️ Renomear\". Uma janela será aberta para digitar o novo nome. "
                       "O programa não permite nomes duplicados ou vazios.", "body")

        self._inserir("Nomes duplicados são tratados automaticamente: se você clicar "
                       "várias vezes na mesma regra salva (ex: \"teste\") ou em \"+ Nova Regra\" "
                       "com nome repetido, o programa cria \"teste\", \"teste - 2\", \"teste - 3\" "
                       "reaproveitando o menor número disponível. Ex: se \"teste 3\" já existe "
                       "e você adiciona outro \"teste 3\", vira \"teste 3 - 2\".", "destaque")

        self._separador()
        self._inserir("Como excluir uma regra salva:", "h2")

        self._inserir("No painel \"📜 Regras Salvas\", passe o mouse sobre a regra e clique "
                       "no ícone de lixeira 🗑 à direita do nome. Também é possível "
                       "excluir pelo menu do botão direito (\"🗑 Excluir\").", "body")

        self._separador()
        self._inserir("Onde as regras ficam armazenadas?", "h2")

        self._inserir("As regras são salvas automaticamente no arquivo \"filtros_salvos.json\" "
                       "na mesma pasta do programa. Enquanto esse arquivo existir, suas regras "
                       "estarão disponíveis mesmo após fechar e reabrir o programa.", "body")

    # ==========================================
    # SEÇÃO 6 — EXPORTANDO RESULTADOS
    # ==========================================
    def _conteudo_exportacao(self):
        self._inserir("📤 Exportando Resultados", "h1")

        self._inserir("Após configurar seus filtros, veja como exportar os resultados:", "body")

        self._separador()
        self._inserir("Passo a passo:", "h2")

        self._inserir("1. Clique no botão \"⚡ Iniciar Processamento\" na parte inferior da tela.", "bullet")
        self._inserir("2. Uma janela aparecerá com as opções de saída.", "bullet")

        self._inserir("  → Campo de nome único: digite o nome desejado caso queira salvar tudo em um só arquivo.", "exemplo")
        self._inserir("  → Agrupamento Dinâmico: Se marcar a opção de 'Separar regras de filtro', "
                       "a janela expande mostrando as regras em Grupos (Cartões). "
                       "Você pode mover regras de um grupo para o outro e escolher o "
                       "nome do arquivo de destino para cada grupo!", "exemplo")

        self._inserir("3. Escolha o formato:", "bullet")
        self._inserir("  → 📄 TXT (Original): mantém o formato original do KIJO.", "exemplo")
        self._inserir("  → 📊 CSV (Excel): gera um arquivo que abre direto no Excel.", "exemplo")

        self._inserir("4. Escolha a pasta onde o arquivo será salvo.", "bullet")
        self._inserir("💡 Se algum arquivo já existir na pasta, o programa avisará e pedirá confirmação antes de substituir.", "destaque")
        
        self._inserir("5. O processamento começará e você verá:", "bullet")
        self._inserir("  → Um cronômetro mostrando o tempo decorrido.", "exemplo")
        self._inserir("  → Uma barra de progresso.", "exemplo")
        self._inserir("  → Um botão vermelho \"✕ CANCELAR\" ao lado dos demais — clique para interromper a qualquer momento (o programa limpa os arquivos temporários e volta a \"Aguardando...\").", "exemplo")
        self._inserir("  → A contagem de linhas encontradas ao finalizar.", "exemplo")

        self._separador()
        self._inserir("Qual formato escolher?", "h2")

        self._inserir("📄 TXT — Use quando quiser manter o formato original do KIJO, "
                       "por exemplo para reimportar em outro sistema ou compartilhar com "
                       "alguém que usa o mesmo programa.", "body")

        self._inserir("📊 CSV — Use quando quiser abrir os dados no Excel para análise, "
                       "criar gráficos ou tabelas dinâmicas. O CSV separa cada coluna "
                       "automaticamente.", "body")

        self._separador()
        self._inserir("Dica de Performance:", "h2")

        self._inserir("O Filtra KIJO utiliza o motor Polars, que é extremamente rápido. "
                       "Você pode processar arquivos de centenas de megabytes sem problemas. "
                       "O processamento acontece em segundo plano, então a tela não trava.", "body")

        self._separador()
        self._inserir("Ordem da saída (v4.2.1):", "h2")

        self._inserir("Desde a v4.2.1 a ordenação por data/hora do cabeçalho foi removida "
                       "para voltar ao comportamento correto da v4.1.0. O arquivo de saída mantém "
                       "a ordem de chegada dos dados (ordem dos arquivos + ordem das linhas dentro de cada lote). "
                       "A correção também elimina o erro \"seção mapeada pelo usuário aberta (1224)\" "
                       "causado pelo re-ordenamento com memory-map.", "body")

    # ==========================================
    # SEÇÃO 7 — ANALISANDO DUPLICADAS
    # ==========================================
    def _conteudo_duplicadas(self):
        self._inserir("🔍 Analisando Duplicadas", "h1")

        self._inserir("Além da filtragem convencional, o programa agora possui uma ferramenta dedicada para "
                       "identificar e extrair KIJOs duplicados. Isso é muito útil para limpar relatórios ou encontrar loops.", "body")

        self._separador()
        self._inserir("Como funciona a análise:", "h2")

        self._inserir("1. Selecione um ou mais arquivos KIJO.", "bullet")
        self._inserir("2. Clique no botão laranja \"🔍 Analisar Duplicadas\" (não é necessário criar filtros).", "bullet")
        self._inserir("3. Escolha a pasta onde o resultado será salvo.", "bullet")
        self._inserir("4. O programa vai ler tudo e exportar APENAS as linhas onde o conteúdo do 'KIJO' é idêntico.", "bullet")

        self._separador()
        self._inserir("Como o arquivo final é organizado?", "h2")
        
        self._inserir("O arquivo de saída agrupa todas as duplicadas sequencialmente. Para ajudar na investigação, "
                       "o programa insere o NOME do arquivo original no início da linha, permitindo que você rastreie "
                       "de onde cada cópia veio. As datas, ips e horas originais são mantidas perfeitamente.", "body")

        self._separador()
        self._inserir("Uso de Memória RAM", "h2")

        self._inserir("A pesquisa de duplicadas é um processo intensivo e pode usar bastante memória RAM enquanto "
                       "ocorre, pois memoriza todos os milhões de identificadores de KIJO na memória ao mesmo tempo. "
                       "Mas não se preocupe: assim que o processamento for concluído, o sistema limpa à força essa "
                       "memória e devolve o espaço integralmente para o Windows.", "body")

    # ==========================================
    # SEÇÃO 8 — PERGUNTAS FREQUENTES
    # ==========================================
    def _conteudo_faq(self):
        self._inserir("❓ Perguntas Frequentes", "h1")

        # --- Pergunta 1 ---
        self._inserir("O programa travou? Como cancelar?", "h2")
        self._inserir("Provavelmente não! Durante o processamento de arquivos grandes, "
                       "a tela pode parecer lenta, mas o processamento continua em segundo "
                       "plano. Observe o cronômetro e a barra de progresso — se estiverem "
                       "avançando, tudo está funcionando. Se precisar interromper, clique no "
                       "botão vermelho \"✕ CANCELAR\" que aparece ao lado de \"Iniciar Processamento\" "
                       "enquanto o status estiver \"⌛ PROCESSANDO...\" ou \"⌛ ANALISANDO...\". "
                       "O cancelamento é checado a cada arquivo e a cada lote de 50 mil linhas, "
                       "remove os .temp.csv pendentes e libera a memória.", "body")

        self._separador()

        # --- Pergunta 2 ---
        self._inserir("Posso processar mais de um arquivo ao mesmo tempo?", "h2")
        self._inserir("Sim! Selecione vários arquivos ao abrir (segure Ctrl e clique em cada um). "
                       "O programa processará todos em sequência e combinará os resultados "
                       "em um único arquivo de saída.", "body")

        self._separador()

        # --- Pergunta 3 ---
        self._inserir("Minha coluna não existe na linha — o que acontece?", "h2")
        self._inserir("Se você filtrar pela coluna 8, mas uma linha do arquivo tem apenas "
                       "7 colunas, essa linha será automaticamente excluída do resultado. "
                       "Isso é intencional: o programa só analisa dados que realmente existem.", "body")

        self._separador()

        # --- Pergunta 4 ---
        self._inserir("Como sei qual é o número da Posição (coluna)?", "h2")
        self._inserir("Abra o arquivo .txt em um editor de texto (como o Bloco de Notas) "
                       "e conte as colunas separadas por vírgula. A primeira coluna é a "
                       "posição 1, a segunda é a posição 2, e assim por diante.", "body")
        self._inserir("Exemplo:", "h3")
        self._inserir("  KIJO1B,ABC123,2024,01,15,100", "exemplo")
        self._inserir("  1=KIJO1B  2=ABC123  3=2024  4=01  5=15  6=100", "exemplo")

        self._separador()

        # --- Pergunta 5 ---
        self._inserir("Posso combinar vários operadores no mesmo filtro?", "h2")
        self._inserir("Sim! Cada card de regra pode ter múltiplas condições. "
                       "Todas devem ser verdadeiras ao mesmo tempo (lógica E).", "body")
        self._inserir("Exemplo: buscar linhas onde coluna 3 = \"2024\" E coluna 6 > 50:", "h3")
        self._inserir("  Condição 1 → Posição: 3 | Igual a     | 2024", "exemplo")
        self._inserir("  Condição 2 → Posição: 6 | Maior que   | 50", "exemplo")

        self._separador()

        # --- Pergunta 6 ---
        self._inserir("Qual a diferença entre múltiplas condições e múltiplos filtros?", "h2")
        self._inserir("• Condições no MESMO card: a linha deve atender a TODAS (lógica E).", "bullet")
        self._inserir("• Cards DIFERENTES: a linha deve atender a PELO MENOS UM (lógica OU).", "bullet")

        self._separador()

        # --- Pergunta 7 ---
        self._inserir("Minhas regras salvas desapareceram!", "h2")
        self._inserir("As regras ficam no arquivo \"filtros_salvos.json\" na pasta do programa. "
                       "Se esse arquivo for apagado ou movido, as regras serão perdidas. "
                       "Para fazer backup, copie esse arquivo para outro local.", "body")
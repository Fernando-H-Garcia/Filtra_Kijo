import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import re
import pandas as pd
import time

class AplicacaoVisual:
    def __init__(self, root):
        self.root = root
        self.root.title("Filtra KIJO v1.0.6")
        self.root.geometry("1200x700")
        self.root.configure(bg="#2E3440")
        self.root.state('zoomed')  # Maximiza a janela

        self.configurar_estilos()
        self.frame_principal = ttk.Frame(root, style="Dark.TFrame")
        self.frame_principal.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.criar_parte_abrir_arquivo()

        self.frame_filtros_exportacao = ttk.Frame(self.frame_principal, style="Dark.TFrame")
        self.frame_filtros_exportacao.pack(fill=tk.BOTH, expand=True, pady=10)

        self.frame_filtros_container = ttk.Frame(self.frame_filtros_exportacao, style="Dark.TFrame")
        self.frame_filtros_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.canvas_filtros = tk.Canvas(self.frame_filtros_container, bg="#3B4252", highlightthickness=0)
        self.scrollbar_filtros = ttk.Scrollbar(self.frame_filtros_container, orient="vertical", command=self.canvas_filtros.yview)
        self.frame_filtros = ttk.Frame(self.canvas_filtros, style="Dark.TFrame")

        self.canvas_filtros.configure(yscrollcommand=self.scrollbar_filtros.set)
        self.canvas_filtros.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_filtros.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas_filtros.create_window((0, 0), window=self.frame_filtros, anchor="nw")
        self.frame_filtros.bind("<Configure>", lambda e: self.canvas_filtros.configure(scrollregion=self.canvas_filtros.bbox("all")))

        self.frame_exportacao = ttk.Frame(self.frame_filtros_exportacao, style="Dark.TFrame")
        self.frame_exportacao.grid(row=0, column=1, sticky="nsew")

        self.frame_filtros_exportacao.grid_columnconfigure(0, weight=2)
        self.frame_filtros_exportacao.grid_columnconfigure(1, weight=1)
        self.frame_filtros_exportacao.grid_rowconfigure(0, weight=1)

        btn_criar_filtro = tk.Button(self.frame_filtros, text="Criar Filtro", bg="#3B4252", fg="white", 
                                     font=("Arial", 10), command=self.criar_filtro)
        btn_criar_filtro.pack(pady=5)

        self.contador_filtros = 0
        self.filtros = {}
        self.criar_painel_exportacao()
        self.criar_filtro()
        self.arquivos_selecionados = []
        
        # Barra de progresso
        self.progresso = ttk.Progressbar(self.frame_principal, orient="horizontal", length=300, mode="determinate")
        self.progresso.pack(pady=10)

        # Label para status
        self.label_status = ttk.Label(self.frame_principal, text="", style="Dark.TLabel")
        self.label_status.pack(pady=5)
        
    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.configure("Dark.TFrame", background="#3B4252", bordercolor="#4C566A", relief="solid", borderwidth=2)
        self.style.configure("Dark.TLabel", background="#3B4252", foreground="white", font=("Arial", 10))

    def criar_parte_abrir_arquivo(self):
        frame_abrir_arquivo = ttk.Frame(self.frame_principal, style="Dark.TFrame")
        frame_abrir_arquivo.pack(fill=tk.X, pady=10)

        btn_abrir_arquivo = tk.Button(frame_abrir_arquivo, text="Abrir Arquivo", 
                                    bg="#3B4252", fg="white", font=("Arial", 10),
                                    relief="raised", bd=2, padx=10, pady=5,
                                    activebackground="#434C5E", activeforeground="white",
                                    command=self.abrir_arquivo)
        btn_abrir_arquivo.pack(side=tk.LEFT, padx=10, pady=10)

        self.label_caminho_arquivo = ttk.Label(frame_abrir_arquivo, text="Nenhum arquivo selecionado",
                                            style="Dark.TLabel", anchor="w")
        self.label_caminho_arquivo.pack(side=tk.LEFT, padx=10, pady=10)
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.withdraw()
        self.tooltip.overrideredirect(True)
        self.tooltip_label = tk.Label(self.tooltip, text="", bg="yellow", fg="black", font=("Arial", 10), relief="solid", bd=1, padx=5, pady=2)
        self.tooltip_label.pack()

        self.label_caminho_arquivo.bind("<Enter>", self.mostrar_tooltip)
        self.label_caminho_arquivo.bind("<Motion>", self.atualizar_tooltip)
        self.label_caminho_arquivo.bind("<Leave>", self.esconder_tooltip)
    def abrir_arquivo(self):
        arquivos = filedialog.askopenfilenames(title="Abrir Arquivo", filetypes=[("Arquivos de Texto", "*.txt")])

        if arquivos:
            self.arquivos_selecionados = arquivos
            diretorio = os.path.dirname(arquivos[0])
            nome_pasta = os.path.basename(diretorio)
            qtd_arquivos = len(arquivos)

            if qtd_arquivos == 1:
                texto_exibido = f"1 arquivo aberto em {nome_pasta}"
            else:
                texto_exibido = f"{qtd_arquivos} arquivos abertos em {nome_pasta}"

            self.label_caminho_arquivo.config(text=texto_exibido)
            self.tooltip_label.config(text="\n".join([os.path.basename(arquivo) for arquivo in arquivos]))

    def mostrar_tooltip(self, event):
        if self.tooltip_label.cget("text"):
            self.tooltip.deiconify()
            self.atualizar_tooltip(event)

    def atualizar_tooltip(self, event):
        x = event.x_root + 10
        y = event.y_root + 10
        self.tooltip.geometry(f"+{x}+{y}")

    def esconder_tooltip(self, event):
        self.tooltip.withdraw()

    def criar_filtro(self):
        self.contador_filtros += 1
        filtro_id = f"Filtro_{self.contador_filtros}"
        self.filtros[filtro_id] = []

        frame_filtro = ttk.Frame(self.frame_filtros, style="Dark.TFrame", relief="solid", borderwidth=2)
        frame_filtro.pack(fill=tk.X, pady=5)

        lbl_filtro = ttk.Label(frame_filtro, text=filtro_id, style="Dark.TLabel")
        lbl_filtro.pack(side=tk.LEFT, padx=5)

        btn_adicionar_condicao = tk.Button(frame_filtro, text="Adicionar Condição", bg="#4C566A", fg="white", 
                                           command=lambda: self.adicionar_condicao(filtro_id, frame_filtro))
        btn_adicionar_condicao.pack(side=tk.LEFT, padx=5)

        btn_excluir_filtro = tk.Button(frame_filtro, text="Excluir Filtro", bg="red", fg="white", 
                                       command=lambda: self.excluir_filtro(filtro_id, frame_filtro))
        btn_excluir_filtro.pack(side=tk.RIGHT, padx=5)

        self.adicionar_condicao(filtro_id, frame_filtro)

    def adicionar_condicao(self, filtro_id, frame_filtro):
        frame_condicao = ttk.Frame(frame_filtro, style="Dark.TFrame")
        frame_condicao.pack(fill=tk.X, padx=10, pady=2)

        ttk.Label(frame_condicao, text="Posição:", style="Dark.TLabel").pack(side=tk.LEFT, padx=5)

        entry_posicao = ttk.Entry(frame_condicao, width=5, validate="key", 
                                    validatecommand=(self.root.register(self.validar_inteiro), "%P"))
        entry_posicao.pack(side=tk.LEFT, padx=5)

        entry_posicao.bind("<FocusOut>", lambda event: self.verificar_posicao_unica(filtro_id, entry_posicao))

        ttk.Label(frame_condicao, text="Operação:", style="Dark.TLabel").pack(side=tk.LEFT, padx=5)
        combo_operacao = ttk.Combobox(frame_condicao, values=["=", ">", "<", ">=", "<=", "!="], 
                                        width=5, justify="center", state="readonly")
        combo_operacao.pack(side=tk.LEFT, padx=5)
        combo_operacao.set("=")

        ttk.Label(frame_condicao, text="Valor:", style="Dark.TLabel").pack(side=tk.LEFT, padx=5)
        entry_valor = ttk.Entry(frame_condicao, width=10, validate="key")
        entry_valor.pack(side=tk.LEFT, padx=5)

        combo_operacao.bind("<<ComboboxSelected>>", lambda event: self.atualizar_valor(entry_valor, combo_operacao))

        condicao = {"posicao": entry_posicao, "operacao": combo_operacao, "valor": entry_valor}
        self.filtros[filtro_id].append(condicao)

        btn_excluir_condicao = tk.Button(frame_condicao, text="Excluir", bg="red", fg="white",
                                            command=lambda: self.excluir_condicao(filtro_id, condicao, frame_condicao))
        btn_excluir_condicao.pack(side=tk.RIGHT, padx=5)

    def verificar_posicao_unica(self, filtro_id, entry_posicao):
        nova_posicao = entry_posicao.get().strip()

        if not nova_posicao.isdigit():
            return

        for condicao in self.filtros[filtro_id]:
            if condicao["posicao"] != entry_posicao and condicao["posicao"].get() == nova_posicao:
                messagebox.showwarning("Posição Duplicada", f"A posição {nova_posicao} já foi usada neste filtro!")
                entry_posicao.delete(0, tk.END)
                return

    def excluir_filtro(self, filtro_id, frame_filtro):
        if filtro_id in self.filtros:
            del self.filtros[filtro_id]
        frame_filtro.destroy()

    def excluir_condicao(self, filtro_id, condicao, frame_condicao):
        if filtro_id in self.filtros and condicao in self.filtros[filtro_id]:
            self.filtros[filtro_id].remove(condicao)
        frame_condicao.destroy()

    def atualizar_valor(self, entry_valor, combo_operacao):
        operacao = combo_operacao.get()
        entry_valor.delete(0, tk.END)

        if operacao in ["=", "!="]:
            entry_valor.config(validate="none")
        else:
            entry_valor.config(validate="key", validatecommand=(self.root.register(self.validar_valor), "%P"))

    def validar_valor(self, valor):
        return bool(re.fullmatch(r"^-?\d*\.?\d*$", valor)) or valor == ""

    def validar_inteiro(self, valor):
        return valor.isdigit() or valor == ""

    def criar_painel_exportacao(self):
        lbl_exportar = ttk.Label(self.frame_exportacao, text="Exportar Dados", style="Dark.TLabel")
        lbl_exportar.pack(pady=10)

        formatos = {"TXT": "Exportando para TXT", "Excel": "Exportando para Excel", "CSV": "Exportando para CSV"}

        for formato, texto in formatos.items():
            btn_exportar = tk.Button(self.frame_exportacao, text=f"Exportar para {formato}", bg="#4C566A", fg="white", 
                                     font=("Arial", 10), command=lambda t=texto: self.acionar_exportacao(t))
            btn_exportar.pack(pady=8, fill=tk.X, padx=20)

    def verificar_campos_preenchidos(self):
        for filtro_id, condicoes in self.filtros.items():
            for condicao in condicoes:
                if not condicao["posicao"].get().strip() or not condicao["operacao"].get().strip() or not condicao["valor"].get().strip():
                    return False
        return True


    def acionar_exportacao(self, formato):
        if not self.verificar_campos_preenchidos():
            tk.messagebox.showerror("Erro", "Por favor, preencha todos os campos de filtros e condições antes de exportar.")
            return

        if not self.arquivos_selecionados:
            tk.messagebox.showerror("Erro", "Nenhum arquivo selecionado.")
            return

        # Pergunta onde salvar o arquivo antes de processar
        if formato == "Exportando para TXT":
            arquivo_salvo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de Texto", "*.txt")])
        elif formato == "Exportando para Excel":
            arquivo_salvo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Arquivos Excel", "*.xlsx")])
        elif formato == "Exportando para CSV":
            arquivo_salvo = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Arquivos CSV", "*.csv")])

        if not arquivo_salvo:  # Se o usuário cancelar a janela de salvar
            return

        self.progresso["value"] = 0
        self.progresso["maximum"] = 100
        self.label_status.config(text="Processando...")
        self.root.update()

        threading.Thread(target=self.processar_arquivos, args=(formato, arquivo_salvo), daemon=True).start()

    def processar_arquivos(self, formato, arquivo_salvo):
        def worker():
            try:
                self.tamanho_total = 0  # Tamanho total dos arquivos em bytes
                self.tamanho_processado = 0  # Tamanho processado em bytes

                # **Passo 1: Calcular o tamanho total dos arquivos**
                for arquivo in self.arquivos_selecionados:
                    self.tamanho_total += os.path.getsize(arquivo)

                if self.tamanho_total == 0:
                    messagebox.showwarning("Aviso", "Os arquivos selecionados estão vazios.")
                    return

                self.progresso["value"] = 5  
                self.label_status.config(text="Iniciando processamento...")
                self.root.update_idletasks()

                linhas_filtradas = []

                # **Passo 2: Processamento real dos arquivos**
                for arquivo in self.arquivos_selecionados:
                    tamanho_arquivo = os.path.getsize(arquivo)
                    try:
                        with open(arquivo, "r", encoding="utf-8") as f:
                            for linha in f:
                                self.tamanho_processado += len(linha.encode('utf-8'))  # Atualiza o tamanho processado
                                if "KIJO" in linha:
                                    linha_filtrada = linha[linha.index("KIJO"):]
                                    linhas_filtradas.append(linha_filtrada.strip().split(","))

                                # Atualiza a barra de progresso a cada 3 segundos
                                if time.time() - self.ultima_atualizacao >= 3:
                                    self.atualizar_progresso()
                                    self.ultima_atualizacao = time.time()

                    except UnicodeDecodeError:
                        with open(arquivo, "r", encoding="latin1") as f:
                            for linha in f:
                                self.tamanho_processado += len(linha.encode('latin1'))  # Atualiza o tamanho processado
                                if "KIJO" in linha:
                                    linha_filtrada = linha[linha.index("KIJO"):]
                                    linhas_filtradas.append(linha_filtrada.strip().split(","))

                                # Atualiza a barra de progresso a cada 3 segundos
                                if time.time() - self.ultima_atualizacao >= 3:
                                    self.atualizar_progresso()
                                    self.ultima_atualizacao = time.time()

                if not linhas_filtradas:
                    messagebox.showinfo("Info", "Nenhum dado filtrado para exportar.")
                    return

                self.label_status.config(text="Filtrando dados...")
                df = pd.DataFrame(linhas_filtradas)
                df_filtrado = self.aplicar_filtros(df)

                self.progresso["value"] = 50
                self.root.update_idletasks()

                
                if formato == "Exportando para TXT":
                    self.label_status.config(text="Exportando dados para txt ...")
                    df_filtrado.to_csv(arquivo_salvo, index=False, header=False, sep="\t")
                elif formato == "Exportando para Excel":
                    self.label_status.config(text="Exportando dados para xlsx... Pode levar alguns minutos...")
                    df_filtrado.to_excel(arquivo_salvo, index=False, header=True, engine='openpyxl')  # Ajuste para salvar com cabeçalho
                elif formato == "Exportando para CSV":
                    self.label_status.config(text="Exportando dados para xCSV ...")
                    df_filtrado.to_csv(arquivo_salvo, index=False, header=True)

                self.progresso["value"] = 100
                self.label_status.config(text="Processamento concluído!")

                messagebox.showinfo("Sucesso", f"Dados exportados para {arquivo_salvo}")

            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
                self.label_status.config(text="Erro durante o processamento.")
                self.progresso["value"] = 0

        # Inicializa a variável para controlar a última atualização
        self.ultima_atualizacao = time.time()

        # Inicia a thread de processamento
        threading.Thread(target=worker, daemon=True).start()

    def atualizar_progresso(self):
        """Atualiza a barra de progresso com base no tamanho processado."""
        if self.tamanho_total > 0:
            progresso_atual = 5 + ((self.tamanho_processado / self.tamanho_total) * 85)
            self.progresso["value"] = min(progresso_atual, 90)
            self.root.update_idletasks()
    def aplicar_filtros(self, df):
        resultados_filtrados = []

        for filtro_id, condicoes in self.filtros.items():
            df_filtro = df.copy()  # Cria uma cópia do DataFrame para aplicar o filtro atual

            for condicao in condicoes:
                posicao = int(condicao["posicao"].get()) - 1
                operacao = condicao["operacao"].get()
                valor = condicao["valor"].get()

                if posicao >= 0 and posicao < df_filtro.shape[1]:
                    coluna = df_filtro.iloc[:, posicao]

                    if operacao == "=":
                        df_filtro = df_filtro[coluna == valor]
                    elif operacao == "!=":
                        df_filtro = df_filtro[coluna != valor]
                    elif operacao == ">":
                        coluna = pd.to_numeric(coluna, errors='coerce')
                        df_filtro = df_filtro[coluna > float(valor)]
                    elif operacao == "<":
                        coluna = pd.to_numeric(coluna, errors='coerce')
                        df_filtro = df_filtro[coluna < float(valor)]
                    elif operacao == ">=":
                        coluna = pd.to_numeric(coluna, errors='coerce')
                        df_filtro = df_filtro[coluna >= float(valor)]
                    elif operacao == "<=":
                        coluna = pd.to_numeric(coluna, errors='coerce')
                        df_filtro = df_filtro[coluna <= float(valor)]

            # Adiciona as linhas filtradas ao resultado final
            resultados_filtrados.append(df_filtro)

        # Combina todos os resultados usando a lógica OR
        if resultados_filtrados:
            df_final = pd.concat(resultados_filtrados).drop_duplicates()
            return df_final
        else:
            return pd.DataFrame()  # Retorna um DataFrame vazio se não houver filtros

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacaoVisual(root)
    root.mainloop()
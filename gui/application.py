# gui/application.py

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import os
import time
import json
import ctypes
import gc

# --- OTIMIZAÇÃO DE PERFORMANCE (MULTI-MONITOR) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# --- ÍCONE DA JANELA / BARRA DE TAREFAS (corrige quadrado azul + embaçado) ---
def _resource_path(relative_path):
    """Retorna caminho absoluto para recurso, funciona para dev e PyInstaller (_MEIPASS)."""
    import sys, os
    try:
        base = sys._MEIPASS  # type: ignore
    except Exception:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, relative_path)

def _create_fk_image(tam):
    """Gera imagem FK nítida no tamanho exato (evita resize borrado)."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGBA', (tam, tam), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if tam >= 48:
        for y in range(tam):
            r = int(18 + (y / tam) * 14)
            g = int(58 + (y / tam) * 38)
            b = int(138 + (y / tam) * 58)
            draw.line([(0, y), (tam - 1, y)], fill=(r, g, b, 255))
    else:
        draw.rectangle([(0, 0), (tam - 1, tam - 1)], fill=(28, 78, 168, 255))
    raio = max(tam // 6, 2)
    mascara = Image.new('L', (tam, tam), 0)
    draw_mask = ImageDraw.Draw(mascara)
    draw_mask.rounded_rectangle([(0, 0), (tam - 1, tam - 1)], radius=raio, fill=255)
    img.putalpha(mascara)
    if tam >= 64:
        font_size = int(tam * 0.58)
    elif tam >= 32:
        font_size = int(tam * 0.62)
    else:
        font_size = int(tam * 0.60)
    font = None
    for cand in ["C:/Windows/Fonts/arialbd.ttf", "arialbd.ttf", "C:/Windows/Fonts/arial.ttf", "arial.ttf"]:
        try:
            font = ImageFont.truetype(cand, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    texto = "FK"
    bbox = draw.textbbox((0, 0), texto, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (tam - tw) // 2 - bbox[0]
    y = (tam - th) // 2 - bbox[1]
    y -= max(1, tam // 32)
    if tam >= 48:
        draw.text((x + 1, y + 1), texto, fill=(0, 0, 0, 90), font=font)
    elif tam >= 32:
        draw.text((x + 1, y + 1), texto, fill=(0, 0, 0, 60), font=font)
    draw.text((x, y), texto, fill=(255, 255, 255, 255), font=font)
    return img

def _set_window_icon(window):
    """Aplica fk_icon.ico na janela e na barra de tarefas sem embaçar (múltiplos tamanhos nítidos)."""
    import os
    try:
        icon_path = _resource_path("fk_icon.ico")
        if not os.path.exists(icon_path):
            alt = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "fk_icon.ico")
            if os.path.exists(alt):
                icon_path = alt
        # Agrupamento correto na barra de tarefas (evita ícone genérico)
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Tecsoil.FiltraKIJO.v4.2.0")
        except Exception:
            pass
        if os.path.exists(icon_path):
            try:
                window.iconbitmap(icon_path)
            except Exception:
                pass
        # iconphoto com múltiplos tamanhos nítidos (Windows escolhe o melhor para DPI)
        try:
            from PIL import Image, ImageTk
            photos = []
            for sz in [16, 20, 24, 32, 48, 64]:
                try:
                    # Tenta gerar nítido nativo; fallback para resize do ico se falhar
                    try:
                        img = _create_fk_image(sz)
                    except Exception:
                        img = Image.open(icon_path)
                        # PIL ICO com sizes param para pegar melhor aproximação
                        try:
                            img = Image.open(icon_path, sizes=[(sz, sz)])
                        except Exception:
                            resample = getattr(Image, "LANCZOS", 1)
                            img = img.resize((sz, sz), resample)
                    photo = ImageTk.PhotoImage(img)
                    photos.append(photo)
                except Exception:
                    continue
            if photos:
                window.iconphoto(True, *photos)
                if not hasattr(window, "_icon_refs"):
                    window._icon_refs = []
                window._icon_refs.extend(photos)
                window._icon_photo = photos[3] if len(photos) > 3 else photos[0]
        except Exception:
            pass
    except Exception:
        pass

from utils.validators import validar_inteiro, validar_valor
from core.file_processor import FileProcessor
from core.config import VERSION
from .manual import ManualDinamico

# ==========================================================
# OPERADORES
# ==========================================================

OP_MAP = {
    "Igual a": "=",
    "Diferente de": "!=",
    "Maior que": ">",
    "Menor que": "<",
    "Maior ou igual a": ">=",
    "Menor ou igual a": "<=",
    "Contém": "Contém",
}

# ==========================================================
# APARÊNCIA
# ==========================================================

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

# ==========================================================
# CORES
# ==========================================================

COLOR_HEADER = "#1F2937"
COLOR_BG = "#F3F4F6"
COLOR_ACCENT = "#4F46E5"
COLOR_SUCCESS = "#10B981"
COLOR_DANGER = "#EF4444"
COLOR_SECONDARY = "#6B7280"
COLOR_WARNING = "#F59E0B"

COLOR_TEXT_LIGHT = "#FFFFFF"
COLOR_TEXT_DARK = "#1F2937"

# ==========================================================
# TOOLTIP
# ==========================================================

class ToolTip:

    def __init__(self, widget, text_list=None):

        self.widget = widget
        self.text_list = text_list or []

        self.tip_window = None
        self.scroll_frame = None

        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        self.widget.bind("<MouseWheel>", self.on_mousewheel)

    def show_tip(self, event=None):

        if self.tip_window or not self.text_list:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 30

        self.tip_window = tw = tk.Toplevel(self.widget)

        tw.wm_overrideredirect(True)

        max_h = 400
        row_h = 25

        calc_h = min(
            max_h,
            len(self.text_list) * row_h + 20
        )

        tw.wm_geometry(f"350x{calc_h}+{x}+{y}")

        self.scroll_frame = ctk.CTkScrollableFrame(
            tw,
            fg_color="#1F2937",
            corner_radius=0,
            scrollbar_button_color="#4F46E5",
            scrollbar_button_hover_color="#4338CA"
        )

        self.scroll_frame.pack(
            fill="both",
            expand=True
        )

        for arq in self.text_list:

            lbl = ctk.CTkLabel(
                self.scroll_frame,
                text=f"• {arq}",
                font=("Segoe UI", 11),
                text_color="white",
                anchor="w",
                justify="left"
            )

            lbl.pack(
                fill="x",
                padx=10,
                pady=1
            )

    def hide_tip(self, event=None):

        tw = self.tip_window

        self.tip_window = None
        self.scroll_frame = None

        if tw:
            tw.destroy()

    def on_mousewheel(self, event):

        if self.scroll_frame:

            self.scroll_frame._parent_canvas.yview_scroll(
                int(-20 * (event.delta / 120)),
                "units"
            )

# ==========================================================
# APLICAÇÃO
# ==========================================================

class AplicacaoVisual:

    def __init__(self, root):

        self.root = root

        self.root.title(
            f"Filtra KIJO v{VERSION}"
        )

        self.root.geometry("1300x850")

        self.root.configure(
            fg_color=COLOR_BG
        )

        # Ícone idêntico ao do .exe (corrige quadrado azul na barra de tarefas)
        _set_window_icon(self.root)

        self.root.after(
            0,
            lambda: self.root.state('zoomed')
        )

        self.v_num = self.root.register(
            validar_inteiro
        )

        self.v_val = self.root.register(
            self._validar_dinamico
        )

        self.manual = ManualDinamico(
            self.root
        )

        self.arquivos_selecionados = []

        self.dir_abertura = ""
        self.dir_salvamento = ""

        self.filtros = {}

        self.contador_filtros = 0

        self.caminho_biblioteca = (
            "filtros_salvos.json"
        )

        self.biblioteca_filtros = (
            self._carregar_biblioteca()
        )

        self.root.grid_columnconfigure(
            0,
            weight=1
        )

        self.root.grid_rowconfigure(
            1,
            weight=1
        )

        self.criar_header()
        self.criar_corpo()
        self.criar_rodape()

        self._timer_inicio = None
        self._timer_id = None

        self._status_atual = (
            "Aguardando..."
        )
        self._cancel_processamento = False

    # ==========================================================
    # BIBLIOTECA
    # ==========================================================

    def _carregar_biblioteca(self):
        self.nomes_colunas_mapeadas = {}
        if os.path.exists(
            self.caminho_biblioteca
        ):

            try:

                with open(
                    self.caminho_biblioteca,
                    'r',
                    encoding='utf-8'
                ) as f:
                    data = json.load(f)
                    
                    config = data.pop("__config__", {})
                    self.dir_abertura = config.get("dir_abertura", "")
                    self.dir_salvamento = config.get("dir_salvamento", "")
                    self.nomes_colunas_mapeadas = config.get("nomes_colunas_mapeadas", {})
                    
                    return data

            except:
                return {}

        return {}

    def _salvar_biblioteca(self):

        try:
            
            data_to_save = self.biblioteca_filtros.copy()
            data_to_save["__config__"] = {
                "dir_abertura": getattr(self, "dir_abertura", ""),
                "dir_salvamento": getattr(self, "dir_salvamento", ""),
                "nomes_colunas_mapeadas": getattr(self, "nomes_colunas_mapeadas", {})
            }

            with open(
                self.caminho_biblioteca,
                'w',
                encoding='utf-8'
            ) as f:

                json.dump(
                    data_to_save,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

        except:
            pass

    # ==========================================================
    # HEADER
    # ==========================================================

    def criar_header(self):

        self.header = ctk.CTkFrame(
            self.root,
            height=120,
            corner_radius=0,
            fg_color=COLOR_HEADER
        )

        self.header.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        self.header.grid_columnconfigure(
            1,
            weight=1
        )

        lbl_logo = ctk.CTkLabel(
            self.header,
            text="🔍 Filtra KIJO",
            text_color=COLOR_TEXT_LIGHT,
            font=ctk.CTkFont(
                family="Segoe UI",
                size=28,
                weight="bold"
            )
        )

        lbl_logo.grid(
            row=0,
            column=0,
            padx=40,
            pady=25,
            sticky="w"
        )

        frame_btn = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )

        frame_btn.grid(
            row=0,
            column=2,
            padx=40
        )

        ctk.CTkButton(
            frame_btn,
            text="📂 Abrir Arquivo",
            command=self.abrir_arquivos,
            fg_color=COLOR_ACCENT,
            hover_color="#4338CA",
            width=220,
            height=55,
            font=("Segoe UI", 18, "bold")
        ).pack(
            side=tk.LEFT,
            padx=10
        )

        ctk.CTkButton(
            frame_btn,
            text="❓ Ajuda",
            command=self.manual.mostrar_manual,
            fg_color="#4B5563",
            hover_color="#374151",
            width=130,
            height=55,
            font=("Segoe UI", 15, "bold")
        ).pack(
            side=tk.LEFT,
            padx=10
        )

        self.lbl_status_files = ctk.CTkLabel(
            self.header,
            text="Nenhum arquivo selecionado",
            font=("Segoe UI", 14),
            text_color="#9CA3AF"
        )

        self.lbl_status_files.grid(
            row=1,
            column=0,
            columnspan=3,
            padx=40,
            sticky="w",
            pady=(0, 20)
        )

        self.tooltip_files = ToolTip(
            self.lbl_status_files,
            []
        )

    # ==========================================================
    # CORPO
    # ==========================================================

    def criar_corpo(self):

        self.corpo = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )

        self.corpo.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=25,
            pady=15
        )

        self.corpo.grid_columnconfigure(
            0,
            weight=3
        )

        self.corpo.grid_columnconfigure(
            1,
            weight=1
        )

        self.corpo.grid_rowconfigure(
            0,
            weight=1
        )

        self.frame_filtros_container = ctk.CTkFrame(
            self.corpo,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#E5E7EB"
        )

        self.frame_filtros_container.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 15)
        )

        self.frame_filtros_container.grid_rowconfigure(
            1,
            weight=1
        )

        self.frame_filtros_container.grid_columnconfigure(
            0,
            weight=1
        )

        header_f = ctk.CTkFrame(
            self.frame_filtros_container,
            fg_color="transparent"
        )

        header_f.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=20
        )

        ctk.CTkLabel(
            header_f,
            text="🎯 Regras de Filtragem",
            text_color=COLOR_TEXT_DARK,
            font=("Segoe UI", 22, "bold")
        ).pack(side=tk.LEFT)

        self.btn_nova_regra = ctk.CTkButton(
            header_f,
            text="+ Nova Regra",
            command=self.criar_filtro,
            width=160,
            height=42,
            font=("Segoe UI", 15, "bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#059669"
        )
        self.btn_nova_regra.pack(side=tk.RIGHT)
        self.btn_nova_regra.configure(state="disabled")

        self.scroll_filtros = ctk.CTkScrollableFrame(
            self.frame_filtros_container,
            fg_color="transparent"
        )

        self.scroll_filtros.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )

        self.frame_lib = ctk.CTkFrame(
            self.corpo,
            width=320,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#E5E7EB"
        )

        self.frame_lib.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.frame_lib.grid_rowconfigure(
            1,
            weight=1
        )

        self.frame_lib.grid_columnconfigure(
            0,
            weight=1
        )

        ctk.CTkLabel(
            self.frame_lib,
            text="📜 Regras Salvas",
            text_color=COLOR_TEXT_DARK,
            font=("Segoe UI", 18, "bold")
        ).grid(
            row=0,
            column=0,
            pady=20
        )

        self.scroll_lib = ctk.CTkScrollableFrame(
            self.frame_lib,
            fg_color="transparent"
        )

        self.scroll_lib.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=8,
            pady=8
        )

        self.atualizar_lista_biblioteca()

    # ==========================================================
    # RODAPÉ
    # ==========================================================

    def criar_rodape(self):

        self.rodape = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )

        self.rodape.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=25,
            pady=(0, 20)
        )

        self.rodape.grid_columnconfigure(
            0,
            weight=1
        )

        self.card_rodape = ctk.CTkFrame(
            self.rodape,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#E5E7EB"
        )

        self.card_rodape.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        self.card_rodape.grid_columnconfigure(
            0,
            weight=1
        )

        frame_bottom = ctk.CTkFrame(
            self.card_rodape,
            fg_color="transparent"
        )

        frame_bottom.grid(
            row=0,
            column=0,
            padx=40,
            pady=20,
            sticky="ew"
        )

        frame_bottom.grid_columnconfigure(
            0,
            weight=1
        )

        self.lbl_status_unificado = ctk.CTkLabel(
            frame_bottom,
            text="🕒 00:00 | 📄 Aguardando...",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_TEXT_DARK
        )

        self.lbl_status_unificado.grid(
            row=0,
            column=0,
            sticky="n"
        )

        self.progress_bar = ctk.CTkProgressBar(
            frame_bottom,
            height=14,
            progress_color=COLOR_ACCENT
        )

        self.progress_bar.grid(
            row=1,
            column=0,
            pady=(15, 20),
            sticky="ew"
        )

        self.progress_bar.set(0)

        # ======================================================
        # BOTÕES
        # ======================================================

        frame_botoes = ctk.CTkFrame(
            frame_bottom,
            fg_color="transparent"
        )

        frame_botoes.grid(
            row=2,
            column=0,
            pady=(5, 0)
        )

        self.btn_processar = ctk.CTkButton(
            frame_botoes,
            text="⚡ INICIAR PROCESSAMENTO",
            command=self.fluxo_processamento,
            font=("Segoe UI", 15, "bold"),
            height=50,
            width=280,
            fg_color=COLOR_ACCENT,
            hover_color="#4338CA"
        )

        self.btn_processar.pack(
            side=tk.LEFT,
            padx=10
        )

        self.btn_duplicadas = ctk.CTkButton(
            frame_botoes,
            text="🔍 ANALISAR DUPLICADAS",
            command=self.fluxo_duplicadas,
            font=("Segoe UI", 15, "bold"),
            height=50,
            width=280,
            fg_color=COLOR_WARNING,
            hover_color="#D97706"
        )

        self.btn_duplicadas.pack(
            side=tk.LEFT,
            padx=10
        )

        self.btn_cancelar = ctk.CTkButton(
            frame_botoes,
            text="✕ CANCELAR",
            command=self.cancelar_processamento,
            font=("Segoe UI", 15, "bold"),
            height=50,
            width=180,
            fg_color=COLOR_DANGER,
            hover_color="#DC2626"
        )
        # inicialmente oculto; será mostrado apenas durante processamento

    # ==========================================================
    # TIMER
    # ==========================================================

    def atualizar_timer(self):

        if self._timer_inicio:

            decorrido = (
                time.time()
                - self._timer_inicio
            )

            minutos = int(decorrido // 60)
            segundos = int(decorrido % 60)

            tempo_str = (
                f"{minutos:02d}:{segundos:02d}"
            )

            self.lbl_status_unificado.configure(
                text=f"🕒 {tempo_str} | {self._status_atual}"
            )

            self._timer_id = self.root.after(
                1000,
                self.atualizar_timer
            )

    # ==========================================================
    # PROCESSAMENTO NORMAL
    # ==========================================================

    def fluxo_processamento(self):

        if not self.arquivos_selecionados:

            messagebox.showwarning(
                "Aviso",
                "Selecione ao menos um arquivo primeiro!"
            )

            return

        if not self.filtros:

            messagebox.showwarning(
                "Aviso",
                "Crie ao menos uma regra de filtro!"
            )

            return

        tem_posicao = False
        for f_id, info in self.filtros.items():
            for c in info["condicoes"]:
                if c["pos_widget"].get().strip():
                    tem_posicao = True
                    break
            if tem_posicao:
                break
        
        if not tem_posicao:
            messagebox.showwarning("Aviso", "Atenção: É obrigatório informar ao menos uma Posição nas regras de filtro!")
            return

        self.progress_bar.set(0)

        self._status_atual = (
            "📄 Preparando..."
        )

        self.lbl_status_unificado.configure(
            text=f"🕒 00:00 | {self._status_atual}",
            text_color=COLOR_ACCENT
        )

        pop = ctk.CTkToplevel(
            self.root
        )

        pop.title(
            "Configurar Exportação"
        )

        _set_window_icon(pop)

        w, h = 500, 320

        x = (
            (pop.winfo_screenwidth() // 2)
            - (w // 2)
        )

        y = (
            (pop.winfo_screenheight() // 2)
            - (h // 2)
        )

        pop.geometry(
            f"{w}x{h}+{x}+{y}"
        )

        pop.attributes(
            "-topmost",
            True
        )

        pop.grab_set()

        ctk.CTkLabel(
            pop,
            text="Salvar arquivo(s) como:",
            font=("Segoe UI", 16, "bold")
        ).pack(
            pady=(20, 5)
        )

        e_nome = ctk.CTkEntry(
            pop,
            placeholder_text=
                "Opcional: Digite o nome do arquivo único",
            width=380,
            font=("Segoe UI", 14)
        )

        e_nome.pack(
            pady=10
        )

        # Dynamic container for rules
        container_dinamico = ctk.CTkFrame(pop, fg_color="transparent")
        scroll_frame = ctk.CTkScrollableFrame(container_dinamico, width=450, height=200, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        import string
        grupos_disponiveis = [f"Grupo {l}" for l in string.ascii_uppercase]

        self.regra_grupo_map = {}
        self.grupo_nome_map = {}

        idx = 0
        nomes_usados = set()
        for f_id in self.filtros:
            nome_base = self.filtros[f_id]["nome_entry"].get().strip() or f_id
            nome_default = nome_base
            contador = 2
            while nome_default in nomes_usados:
                nome_default = f"{nome_base}_{contador}"
                contador += 1
            nomes_usados.add(nome_default)
            
            grupo_nome = grupos_disponiveis[idx] if idx < len(grupos_disponiveis) else f"Grupo {idx+1}"
            self.regra_grupo_map[f_id] = grupo_nome
            self.grupo_nome_map[grupo_nome] = ctk.StringVar(value=nome_default)
            idx += 1

        def render_grupos():
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            grupos_ativos = sorted(list(set(self.regra_grupo_map.values())))

            for grupo in grupos_ativos:
                card = ctk.CTkFrame(scroll_frame, fg_color="#F3F4F6", corner_radius=8)
                card.pack(fill="x", padx=5, pady=5)

                header = ctk.CTkFrame(card, fg_color="transparent")
                header.pack(fill="x", padx=10, pady=(10, 5))

                ctk.CTkLabel(header, text=f"{grupo}:", font=("Segoe UI", 14, "bold"), text_color="#1F2937").pack(side="left")

                if grupo not in self.grupo_nome_map:
                    self.grupo_nome_map[grupo] = ctk.StringVar(value=f"Arquivo_{grupo.replace(' ', '_')}")

                entry = ctk.CTkEntry(header, textvariable=self.grupo_nome_map[grupo], width=200, height=30)
                entry.pack(side="left", padx=10)

                for f_id, g in self.regra_grupo_map.items():
                    if g == grupo:
                        rule_frame = ctk.CTkFrame(card, fg_color="transparent")
                        rule_frame.pack(fill="x", padx=20, pady=(0, 5))

                        nome_regra = self.filtros[f_id]["nome_entry"].get().strip() or f_id
                        lbl = ctk.CTkLabel(rule_frame, text=f"• {nome_regra}", font=("Segoe UI", 13), text_color="#4B5563")
                        lbl.pack(side="left")

                        def make_change_group(rule_id):
                            def change_group(new_group):
                                self.regra_grupo_map[rule_id] = new_group
                                render_grupos()
                            return change_group

                        opt = ctk.CTkOptionMenu(
                            rule_frame,
                            values=grupos_disponiveis[:max(len(self.filtros), 1)],
                            command=make_change_group(f_id),
                            width=100,
                            height=25,
                            font=("Segoe UI", 12)
                        )
                        opt.set(grupo)
                        opt.pack(side="right")

        self.separar_arquivos_var = ctk.BooleanVar(value=False)

        def toggle_separar():
            if self.separar_arquivos_var.get():
                e_nome.configure(state="disabled")
                pop.geometry("520x600")
                container_dinamico.pack(fill="both", expand=True, before=lbl_formato, pady=10)
                render_grupos()
            else:
                e_nome.configure(state="normal")
                pop.geometry(f"{w}x{h}")
                container_dinamico.pack_forget()

        chk_separar = ctk.CTkCheckBox(
            pop,
            text="Separar regras de filtro (Agrupamento Dinâmico)",
            variable=self.separar_arquivos_var,
            command=toggle_separar,
            font=("Segoe UI", 13)
        )
        chk_separar.pack(pady=(5, 10))

        lbl_formato = ctk.CTkLabel(
            pop,
            text="Escolha o formato de saída:",
            font=("Segoe UI", 14)
        )
        lbl_formato.pack(
            pady=(5, 5)
        )

        btn_f = ctk.CTkFrame(
            pop,
            fg_color="transparent"
        )

        btn_f.pack(
            pady=10
        )

        def selecionar(fmt):

            nome_custom = (
                e_nome.get().strip()
            )

            separar = self.separar_arquivos_var.get()
            
            mapa_arquivos = None
            if separar:
                mapa_arquivos = {}
                for f_id, g in self.regra_grupo_map.items():
                    nome_arq = self.grupo_nome_map[g].get().strip() or f"Regra_{f_id}"
                    mapa_arquivos[f_id] = nome_arq

            pop.destroy()
            self.reset_ui() # reset status in case of error

            self.definir_destino_e_iniciar(
                fmt,
                nome_custom,
                mapa_arquivos
            )

        def on_close():
            self.reset_ui()
            pop.destroy()

        pop.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkButton(
            btn_f,
            text="📄 TXT (Original)",
            width=140,
            height=45,
            font=("Segoe UI", 13, "bold"),
            command=lambda:
                selecionar(".txt")
        ).pack(
            side=tk.LEFT,
            padx=15
        )

        ctk.CTkButton(
            btn_f,
            text="📊 CSV (Excel)",
            width=140,
            height=45,
            font=("Segoe UI", 13, "bold"),
            command=lambda:
                selecionar(".csv")
        ).pack(
            side=tk.LEFT,
            padx=15
        )

    # ==========================================================
    # DUPLICADAS
    # ==========================================================

    def fluxo_duplicadas(self):

        if not self.arquivos_selecionados:

            messagebox.showwarning(
                "Aviso",
                "Selecione ao menos um arquivo!"
            )

            return

        self.progress_bar.set(0)

        self._status_atual = (
            "🔍 Preparando análise..."
        )

        self.lbl_status_unificado.configure(
            text=f"🕒 00:00 | {self._status_atual}",
            text_color=COLOR_WARNING
        )

        dir_out = filedialog.askdirectory(
            initialdir=(
                self.dir_salvamento
                or self.dir_abertura
            ),
            title="Pasta de Destino"
        )

        if not dir_out:
            return

        self.dir_salvamento = dir_out
        self._salvar_biblioteca()

        nome_final = (
            f"Duplicadas_"
            f"{int(time.time())}.txt"
        )

        caminho_completo = os.path.join(
            dir_out,
            nome_final
        )

        self._status_atual = "⌛ ANALISANDO..."
        self._cancel_processamento = False

        self.btn_processar.configure(
            state="disabled"
        )

        self.btn_duplicadas.configure(
            state="disabled",
            text="⌛ ANALISANDO..."
        )
        self._mostrar_btn_cancelar()

        self._timer_inicio = time.time()

        self.atualizar_timer()

        threading.Thread(
            target=self.executar_thread_duplicadas,
            args=(caminho_completo,),
            daemon=True
        ).start()

    # ==========================================================
    # DEFINIR DESTINO
    # ==========================================================

    def definir_destino_e_iniciar(
        self,
        fmt,
        nome_custom,
        separar_arquivos=False
    ):

        dir_out = filedialog.askdirectory(
            initialdir=(
                self.dir_salvamento
                or self.dir_abertura
            ),
            title="Pasta de Destino"
        )

        if not dir_out:
            return

        self.dir_salvamento = dir_out
        self._salvar_biblioteca()

        arquivos_conflito = []

        if isinstance(separar_arquivos, dict):
            for f_id, nome_arq in separar_arquivos.items():
                import re
                nome_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_arq)
                nome_final = f"{nome_limpo}{fmt}"
                caminho_chk = os.path.join(dir_out, nome_final)
                if os.path.exists(caminho_chk):
                    if caminho_chk not in arquivos_conflito:
                        arquivos_conflito.append(caminho_chk)
            
            # Placeholder para passar pra frente
            caminho_completo = os.path.join(dir_out, f"dummy_base{fmt}")
        else:
            if nome_custom:
                nome_final = f"{nome_custom}{fmt}"
            else:
                nome_final = f"FiltraKIJO_Resultado_{int(time.time())}{fmt}"

            caminho_completo = os.path.join(dir_out, nome_final)
            if os.path.exists(caminho_completo):
                arquivos_conflito.append(caminho_completo)

        if arquivos_conflito:
            if len(arquivos_conflito) == 1:
                msg = f"O arquivo '{os.path.basename(arquivos_conflito[0])}' já existe.\nDeseja substituir?"
            else:
                msg = "Os seguintes arquivos já existem:\n\n"
                for a in arquivos_conflito[:5]:
                    msg += f"- {os.path.basename(a)}\n"
                if len(arquivos_conflito) > 5:
                    msg += f"... e mais {len(arquivos_conflito) - 5} arquivos.\n"
                msg += "\nDeseja substituir todos eles?"
                
            resp = messagebox.askyesno("Confirmar Substituição", msg)
            if not resp:
                self.reset_ui()
                return

        self._status_atual = "⌛ PROCESSANDO..."
        self._cancel_processamento = False

        self.btn_processar.configure(
            state="disabled",
            text="⌛ PROCESSANDO..."
        )

        self.btn_duplicadas.configure(
            state="disabled"
        )
        self._mostrar_btn_cancelar()

        self._timer_inicio = time.time()

        self.atualizar_timer()

        filtros_formatados = {}

        for f_id, info in self.filtros.items():

            conds = []

            for c in info["condicoes"]:

                conds.append({
                    "posicao":
                        c["pos_widget"].get(),

                    "operacao":
                        OP_MAP.get(
                            c["op_widget"].get(),
                            c["op_widget"].get()
                        ),

                    "valor":
                        c["val_widget"].get()
                })

            if conds:

                filtros_formatados[f_id] = {
                    "nome": info["nome_entry"].get().strip() or f_id,
                    "condicoes": conds,
                    "colunas_saida": info.get("colunas_saida", None)
                }

        threading.Thread(
            target=self.executar_thread,
            args=(
                filtros_formatados,
                caminho_completo,
                fmt,
                separar_arquivos
            ),
            daemon=True
        ).start()

    # ==========================================================
    # THREAD NORMAL
    # ==========================================================

    def executar_thread(
        self,
        filtros,
        caminho_final,
        fmt,
        separar_arquivos
    ):

        try:

            processor = FileProcessor(
                arquivos_selecionados=
                    self.arquivos_selecionados,

                filtros=filtros,

                progress_callback=
                    self.atualizar_ui_progresso,

                status_callback=
                    self.atualizar_ui_status,

                cancel_callback=self._is_cancel_requested
            )

            resultado = (
                processor
                .processar_e_exportar_em_chunks(
                    formato=
                        fmt.upper().replace(".", ""),

                    caminho_saida=
                        caminho_final,
                    separar_arquivos=separar_arquivos
                )
            )

            # Se foi cancelado mas não lançou (chegou ao fim logo após flag), tratar como cancel
            if self._is_cancel_requested():
                self.root.after(0, self._finalizar_cancelamento)
                return

            self.root.after(
                0,
                lambda r=resultado:
                    self.finalizar_processamento(r)
            )

        except InterruptedError as erro_cancel:
            self.root.after(0, self._finalizar_cancelamento)

        except Exception as erro:

            # Se foi cancelado, não mostrar erro
            if self._is_cancel_requested() or "cancelado" in str(erro).lower():
                self.root.after(0, self._finalizar_cancelamento)
                return

            mensagem = str(erro)

            self.root.after(
                0,
                lambda msg=mensagem:
                    messagebox.showerror(
                        "Erro Fatal",
                        f"Erro no processamento: {msg}"
                    )
            )

            self.root.after(
                0,
                self.reset_ui
            )

    # ==========================================================
    # THREAD DUPLICADAS
    # ==========================================================

    def executar_thread_duplicadas(
        self,
        caminho_final
    ):

        try:

            processor = FileProcessor(
                arquivos_selecionados=
                    self.arquivos_selecionados,

                filtros={},

                progress_callback=
                    self.atualizar_ui_progresso,

                status_callback=
                    self.atualizar_ui_status,

                cancel_callback=self._is_cancel_requested
            )

            resultado = (
                processor
                .processar_apenas_duplicadas(
                    formato="TXT",
                    caminho_saida=caminho_final
                )
            )

            if self._is_cancel_requested():
                self.root.after(0, self._finalizar_cancelamento)
                return

            self.root.after(
                0,
                lambda r=resultado:
                    self.finalizar_duplicadas(r)
            )

        except InterruptedError:
            self.root.after(0, self._finalizar_cancelamento)

        except Exception as erro:

            if self._is_cancel_requested() or "cancelado" in str(erro).lower():
                self.root.after(0, self._finalizar_cancelamento)
                return

            mensagem = str(erro)

            self.root.after(
                0,
                lambda msg=mensagem:
                    messagebox.showerror(
                        "Erro",
                        msg
                    )
            )

            self.root.after(
                0,
                self.reset_ui
            )

    # ==========================================================
    # UI
    # ==========================================================

    def atualizar_ui_progresso(self, valor):

        self.root.after(
            0,
            lambda:
                self.progress_bar.set(
                    valor / 100
                )
        )

    def atualizar_ui_status(self, msg):

        self._status_atual = f"⚡ {msg}"

        texto_atual = (
            self.lbl_status_unificado
            .cget("text")
        )

        timer_parte = (
            texto_atual.split("|")[0].strip()
            if "|" in texto_atual
            else "🕒 00:00"
        )

        cor = COLOR_ACCENT

        if (
            "duplicada" in msg.lower()
            or "duplicadas" in msg.lower()
        ):
            cor = COLOR_WARNING

        self.lbl_status_unificado.configure(
            text=f"{timer_parte} | {self._status_atual}",
            text_color=cor
        )

    # ==========================================================
    # FINALIZA NORMAL
    # ==========================================================

    def finalizar_processamento(
        self,
        resultado
    ):

        if self._timer_id:

            self.root.after_cancel(
                self._timer_id
            )

        tempo_total = (
            time.time()
            - self._timer_inicio
        )

        self._timer_inicio = None
        self._cancel_processamento = False
        self._esconder_btn_cancelar()

        self.btn_processar.configure(
            state="normal",
            text="⚡ INICIAR PROCESSAMENTO"
        )

        self.btn_duplicadas.configure(
            state="normal"
        )

        self.progress_bar.set(1.0)

        m = int(tempo_total // 60)
        s = int(tempo_total % 60)

        resumo = (
            f"📄 Encontradas: "
            f"{resultado['linhas_filtradas']} | "
            f"🕒 Tempo: "
            f"{m:02d}:{s:02d} | "
            f"✅ Concluído!"
        )

        self.lbl_status_unificado.configure(
            text=resumo,
            text_color=COLOR_ACCENT
        )

        gc.collect()
        self.limpar_memoria()

    # ==========================================================
    # FINALIZA DUPLICADAS
    # ==========================================================

    def finalizar_duplicadas(
        self,
        resultado
    ):

        if self._timer_id:

            self.root.after_cancel(
                self._timer_id
            )

        tempo_total = (
            time.time()
            - self._timer_inicio
        )

        self._timer_inicio = None
        self._cancel_processamento = False
        self._esconder_btn_cancelar()

        self.btn_processar.configure(
            state="normal"
        )

        self.btn_duplicadas.configure(
            state="normal",
            text="🔍 ANALISAR DUPLICADAS"
        )

        self.progress_bar.set(1.0)

        m = int(tempo_total // 60)
        s = int(tempo_total % 60)

        resumo = (
            f"🔍 Tipos duplicados: "
            f"{resultado['tipos_duplicados']} | "
            f"📄 Ocorrências: "
            f"{resultado['linhas_exportadas']} | "
            f"🕒 {m:02d}:{s:02d}"
        )

        self.lbl_status_unificado.configure(
            text=resumo,
            text_color=COLOR_WARNING
        )

        gc.collect()
        self.limpar_memoria()

    def limpar_memoria(self):
        try:
            import ctypes
            # Esvazia a "bolha" de memória que o Windows reserva pro app
            ctypes.windll.psapi.EmptyWorkingSet(
                ctypes.windll.kernel32.GetCurrentProcess()
            )
        except Exception as e:
            print(f"Erro ao limpar memória: {e}")

    # ==========================================================
    # RESET UI
    # ==========================================================

    def reset_ui(self):

        if self._timer_id:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self._timer_inicio = None
        self._cancel_processamento = False

        self.btn_processar.configure(
            state="normal",
            text="⚡ INICIAR PROCESSAMENTO"
        )

        self.btn_duplicadas.configure(
            state="normal",
            text="🔍 ANALISAR DUPLICADAS"
        )
        # esconder botão cancelar
        try:
            self.btn_cancelar.pack_forget()
        except Exception:
            pass
        try:
            self.btn_cancelar.configure(state="disabled")
        except Exception:
            pass

        self._status_atual = "Aguardando..."

        self.lbl_status_unificado.configure(
            text="🕒 00:00 | 📄 Aguardando...",
            text_color=COLOR_TEXT_DARK
        )

    # ==========================================================
    # CANCELAMENTO
    # ==========================================================

    def _mostrar_btn_cancelar(self):
        try:
            self.btn_cancelar.configure(state="normal")
            self.btn_cancelar.pack(side=tk.LEFT, padx=10)
        except Exception:
            pass

    def _esconder_btn_cancelar(self):
        try:
            self.btn_cancelar.pack_forget()
        except Exception:
            pass
        try:
            self.btn_cancelar.configure(state="disabled")
        except Exception:
            pass

    def cancelar_processamento(self):
        if self._cancel_processamento:
            return
        self._cancel_processamento = True
        self._status_atual = "✕ Cancelando..."
        self.lbl_status_unificado.configure(
            text=f"🕒 --:-- | {self._status_atual}",
            text_color=COLOR_DANGER
        )
        self.btn_cancelar.configure(state="disabled", text="✕ Cancelando...")
        self.btn_processar.configure(state="disabled")
        self.btn_duplicadas.configure(state="disabled")

    def _is_cancel_requested(self):
        return bool(getattr(self, "_cancel_processamento", False))

    def _finalizar_cancelamento(self):
        if self._timer_id:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self._timer_inicio = None
        self._cancel_processamento = False
        self.progress_bar.set(0)
        self.btn_processar.configure(state="normal", text="⚡ INICIAR PROCESSAMENTO")
        self.btn_duplicadas.configure(state="normal", text="🔍 ANALISAR DUPLICADAS")
        try:
            self.btn_cancelar.configure(state="disabled", text="✕ CANCELAR")
            self.btn_cancelar.pack_forget()
        except Exception:
            pass
        self._status_atual = "Cancelado pelo usuário."
        self.lbl_status_unificado.configure(
            text=f"🕒 00:00 | ✕ Cancelado.",
            text_color=COLOR_DANGER
        )
        gc.collect()
        self.limpar_memoria()

    def _gerar_nome_unico(self, nome_base, verificar_biblioteca=True):
        """Gera um nome único encontrando o próximo número disponível.
        
        Args:
            nome_base: Nome base desejado
            verificar_biblioteca: Se True, verifica também na biblioteca (para 'Nova Regra').
                                 Se False, verifica apenas filtros ativos (para carregar da biblioteca).
        """
        # Sempre verifica filtros ativos na tela
        nomes_existentes = set()
        for info in self.filtros.values():
            nome_ativo = info["nome_entry"].get().strip()
            if nome_ativo:
                nomes_existentes.add(nome_ativo)
        
        # Verifica biblioteca apenas se solicitado (para nova regra manual)
        if verificar_biblioteca:
            nomes_existentes.update(self.biblioteca_filtros.keys())
        
        if nome_base not in nomes_existentes:
            return nome_base
        
        # Encontra todos os números já usados para este nome base
        numeros_usados = set()
        prefixo = f"{nome_base} - "
        for nome in nomes_existentes:
            if nome == nome_base:
                numeros_usados.add(1)
            elif nome.startswith(prefixo):
                try:
                    num = int(nome[len(prefixo):])
                    numeros_usados.add(num)
                except ValueError:
                    pass
        
        # Encontra o menor número disponível (começando do 2)
        for i in range(2, 1000):
            if i not in numeros_usados:
                return f"{nome_base} - {i}"
        
        return f"{nome_base} - {len(numeros_usados) + 2}"

    def criar_filtro(self, nome_inicial=None, condicoes_iniciais=None, colunas_saida_iniciais=None):
        self.contador_filtros += 1
        f_id = f"filtro_{self.contador_filtros}"
        card = ctk.CTkFrame(self.scroll_filtros, border_width=1, border_color="#E5E7EB", fg_color="#F9FAFB")
        card.pack(fill="x", padx=10, pady=10)
        header = ctk.CTkFrame(card, height=45, fg_color="#F1F5F9")
        header.pack(fill="x")
        
        if nome_inicial:
            # Carregando da biblioteca: verifica apenas filtros ativos (não a biblioteca)
            nome_default = self._gerar_nome_unico(nome_inicial, verificar_biblioteca=False)
        else:
            # Nova regra manual: verifica biblioteca + filtros ativos
            nome_default = self._gerar_nome_unico("Nova Regra", verificar_biblioteca=True)
        
        entry_nome = ctk.CTkEntry(header, placeholder_text="Nome do Filtro", width=280, fg_color="transparent", border_width=0, font=("Segoe UI", 15, "bold"))
        entry_nome.insert(0, nome_default); entry_nome.pack(side=tk.LEFT, padx=10, pady=5)
        
        ctk.CTkButton(header, text="✕", width=38, height=38, fg_color="transparent", text_color=COLOR_DANGER, hover_color="#FEE2E2", font=("Segoe UI", 18, "bold"), command=lambda: self.remover_filtro(f_id, card)).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(header, text="💾", width=38, height=38, fg_color="transparent", text_color=COLOR_ACCENT, hover_color="#E0E7FF", font=("Segoe UI", 18), command=lambda: self.salvar_na_biblioteca(f_id)).pack(side=tk.RIGHT, padx=5)
        
        # Botão ⚙️ Configurar Saída
        btn_config = ctk.CTkButton(header, text="⚙️ Configurar Saída", width=140, height=32, fg_color="#4F46E5", hover_color="#4338CA", font=("Segoe UI", 12, "bold"), command=lambda: self.abrir_configuracao_colunas(f_id))
        btn_config.pack(side=tk.RIGHT, padx=10, pady=5)

        body = ctk.CTkFrame(card, fg_color="transparent"); body.pack(fill="x", padx=15, pady=12)
        rows_container = ctk.CTkFrame(body, fg_color="transparent"); rows_container.pack(fill="x")
        self.filtros[f_id] = {
            "widget": card,
            "nome_entry": entry_nome,
            "rows_container": rows_container,
            "condicoes": [],
            "colunas_saida": colunas_saida_iniciais
        }
        ctk.CTkButton(body, text="+ Adicionar Condição", width=170, height=32, fg_color="#6366F1", font=("Segoe UI", 13, "bold"), command=lambda: self.adicionar_condicao(f_id)).pack(pady=8)
        if condicoes_iniciais:
            for c in condicoes_iniciais: self.adicionar_condicao(f_id, c['posicao'], c['valor'], c['operacao'])
        else: self.adicionar_condicao(f_id)

    def adicionar_condicao(self, f_id, pos="", val="", op="="):
        container = self.filtros[f_id]["rows_container"]
        row = ctk.CTkFrame(container, fg_color="transparent"); row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text="Posição:", font=("Segoe UI", 14)).pack(side=tk.LEFT, padx=5)
        e_pos = ctk.CTkEntry(row, width=80, font=("Segoe UI", 14), validate="key", validatecommand=(self.v_num, "%P"))
        e_pos.insert(0, pos); e_pos.pack(side=tk.LEFT, padx=5)
        e_pos.bind("<FocusOut>", lambda e: self.verificar_posicao_unica(f_id, e_pos))
        
        OP_MAP = {
            "Igual a": "=",
            "Diferente de": "!=",
            "Maior que": ">",
            "Menor que": "<",
            "Maior ou igual a": ">=",
            "Menor ou igual a": "<=",
            "Contém": "Contém",
        }
        
        # Mapeamento inverso para setar o ComboBox corretamente
        REV_OP_MAP = {v: k for k, v in OP_MAP.items()}
        
        cb_op = ctk.CTkComboBox(row, values=["Igual a", "Diferente de", "Maior que", "Menor que", "Maior ou igual a", "Menor ou igual a", "Contém"], width=180, font=("Segoe UI", 16, "bold"), justify="center", state="readonly", command=lambda _: e_val.delete(0, tk.END))
        cb_op.set(REV_OP_MAP.get(op, op))
        cb_op.pack(side=tk.LEFT, padx=5)
        e_val = ctk.CTkEntry(row, width=200, font=("Segoe UI", 14), validate="key", validatecommand=(self.v_val, "%P", f_id, len(self.filtros[f_id]["condicoes"])))
        e_val.insert(0, val); e_val.pack(side=tk.LEFT, padx=5)
        btn_rem = ctk.CTkButton(row, text="✕", width=35, height=35, fg_color="transparent", text_color=COLOR_DANGER, hover_color="#FEE2E2", font=("Segoe UI", 16, "bold"))
        cond_data = {"pos_widget": e_pos, "op_widget": cb_op, "val_widget": e_val, "row_widget": row, "btn_rem": btn_rem}
        btn_rem.configure(command=lambda: self.remover_condicao(f_id, row, cond_data))
        self.filtros[f_id]["condicoes"].append(cond_data); self.atualizar_visibilidade_botoes(f_id)

    def verificar_posicao_unica(self, f_id, e_pos):
        pos = e_pos.get().strip()
        if not pos.isdigit(): return
        for cond in self.filtros[f_id]["condicoes"]:
            if cond["pos_widget"] != e_pos and cond["pos_widget"].get() == pos:
                messagebox.showwarning("Aviso", f"Posição {pos} já configurada neste filtro!")
                e_pos.delete(0, tk.END)

    def remover_condicao(self, f_id, row_widget, cond_data):
        row_widget.destroy()
        if f_id in self.filtros:
            self.filtros[f_id]["condicoes"].remove(cond_data); self.atualizar_visibilidade_botoes(f_id)
            for i, c in enumerate(self.filtros[f_id]["condicoes"]):
                c["val_widget"].configure(validatecommand=(self.v_val, "%P", f_id, i))

    def atualizar_visibilidade_botoes(self, f_id):
        conds = self.filtros[f_id]["condicoes"]
        if len(conds) == 1: conds[0]["btn_rem"].pack_forget()
        else:
            for c in conds: c["btn_rem"].pack(side=tk.LEFT, padx=5)

    def _validar_dinamico(self, P, f_id, cond_idx):
        try:
            idx = int(cond_idx)
            if f_id in self.filtros and idx < len(self.filtros[f_id]["condicoes"]):
                op_label = self.filtros[f_id]["condicoes"][idx]["op_widget"].get()
                op = OP_MAP.get(op_label, op_label)
                if op in [">", "<", ">=", "<="]: return validar_valor(P)
            return True
        except: return True

    def remover_filtro(self, f_id, card_widget):
        card_widget.destroy()
        if f_id in self.filtros: del self.filtros[f_id]

    def salvar_na_biblioteca(self, f_id):
        info = self.filtros[f_id]; nome = info["nome_entry"].get().strip() or f"Filtra_{int(time.time())}"
        conds = [{
            "posicao": c["pos_widget"].get(),
            "operacao": OP_MAP.get(c["op_widget"].get(), c["op_widget"].get()),
            "valor": c["val_widget"].get()
        } for c in info["condicoes"]]
        
        # Salva o dicionário com condições e colunas_saida
        self.biblioteca_filtros[nome] = {
            "condicoes": conds,
            "colunas_saida": info.get("colunas_saida")
        }
        self._salvar_biblioteca()
        self.atualizar_lista_biblioteca()
        self.lbl_status_unificado.configure(text=f"Regra '{nome}' salva.")

    def _renomear_filtro_biblioteca(self, nome_antigo):
        """Abre um diálogo para renomear um filtro salvo na biblioteca."""
        if nome_antigo not in self.biblioteca_filtros:
            return
        
        pop = ctk.CTkToplevel(self.root)
        pop.title("Renomear Regra")
        _set_window_icon(pop)
        w, h = 440, 240
        x = (pop.winfo_screenwidth() // 2) - (w // 2)
        y = (pop.winfo_screenheight() // 2) - (h // 2)
        pop.geometry(f"{w}x{h}+{x}+{y}")
        pop.attributes("-topmost", True)
        pop.grab_set()
        pop.resizable(False, False)

        ctk.CTkLabel(pop, text="✏️ Renomear Regra Salva", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT_DARK).pack(pady=(20, 5))
        ctk.CTkLabel(pop, text=f"Nome atual: {nome_antigo}", font=("Segoe UI", 12), text_color=COLOR_SECONDARY).pack(pady=(0, 10))

        entry_novo = ctk.CTkEntry(pop, width=320, font=("Segoe UI", 14))
        entry_novo.insert(0, nome_antigo)
        entry_novo.pack(pady=10)
        entry_novo.focus()
        entry_novo.select_range(0, tk.END)

        def confirmar():
            novo_nome = entry_novo.get().strip()
            if not novo_nome:
                messagebox.showwarning("Aviso", "O nome não pode ser vazio!")
                return
            if novo_nome == nome_antigo:
                pop.destroy()
                return
            if novo_nome in self.biblioteca_filtros:
                messagebox.showwarning("Aviso", f"Já existe uma regra com o nome '{novo_nome}'!")
                return
            
            self.biblioteca_filtros[novo_nome] = self.biblioteca_filtros.pop(nome_antigo)
            self._salvar_biblioteca()
            self.atualizar_lista_biblioteca()
            self.lbl_status_unificado.configure(text=f"Regra renomeada para '{novo_nome}'.")
            pop.destroy()

        btn_frame = ctk.CTkFrame(pop, fg_color="transparent")
        btn_frame.pack(pady=25, fill="x", padx=30)
        ctk.CTkButton(btn_frame, text="Cancelar", height=44, fg_color="#6B7280", hover_color="#4B5563", font=("Segoe UI", 13, "bold"), command=pop.destroy).pack(side=tk.LEFT, expand=True, padx=10)
        ctk.CTkButton(btn_frame, text="Salvar", height=44, fg_color=COLOR_SUCCESS, hover_color="#059669", font=("Segoe UI", 13, "bold"), command=confirmar).pack(side=tk.LEFT, expand=True, padx=10)

        pop.bind("<Return>", lambda e: confirmar())
        pop.bind("<Escape>", lambda e: pop.destroy())

    def _mostrar_menu_contexto_biblioteca(self, event, nome):
        """Mostra menu de contexto ao clicar com botão direito em um filtro salvo."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="✏️ Renomear", command=lambda: self._renomear_filtro_biblioteca(nome))
        menu.add_separator()
        menu.add_command(label="🗑 Excluir", command=lambda: self.excluir_da_biblioteca(nome))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def atualizar_lista_biblioteca(self):
        for w in self.scroll_lib.winfo_children(): w.destroy()
        has_files = len(self.arquivos_selecionados) > 0
        for nome in sorted(self.biblioteca_filtros.keys()):
            regra_info = self.biblioteca_filtros[nome]
            
            # Compatibilidade com o formato antigo (que salvava apenas lista de condições)
            if isinstance(regra_info, list):
                condicoes_carregar = regra_info
                colunas_carregar = None
            else:
                condicoes_carregar = regra_info.get("condicoes", [])
                colunas_carregar = regra_info.get("colunas_saida", None)

            item = ctk.CTkButton(
                self.scroll_lib,
                text=f"📜 {nome}",
                fg_color="#F9FAFB",
                text_color=COLOR_TEXT_DARK,
                hover_color="#E0E7FF",
                anchor="w",
                height=50,
                font=("Segoe UI", 15, "bold"),
                command=lambda n=nome, conds=condicoes_carregar, cols=colunas_carregar: self.criar_filtro(n, conds, cols) if has_files else messagebox.showwarning("Aviso", "Selecione os arquivos antes de carregar filtros!")
            )
            item.pack(fill="x", pady=4, padx=5)
            if not has_files:
                item.configure(state="disabled")
            
            # Bind do botão direito para menu de contexto
            item.bind("<Button-3>", lambda e, n=nome: self._mostrar_menu_contexto_biblioteca(e, n))
            
            btn_del = ctk.CTkButton(item, text="🗑", width=32, height=32, fg_color="transparent", text_color=COLOR_SECONDARY, hover_color="#FEE2E2", font=("Segoe UI", 18), command=lambda n=nome: self.excluir_da_biblioteca(n))
            btn_del.place(relx=0.94, rely=0.5, anchor="e")

    def excluir_da_biblioteca(self, nome):
        if nome in self.biblioteca_filtros: del self.biblioteca_filtros[nome]; self._salvar_biblioteca(); self.atualizar_lista_biblioteca(); self.lbl_status_unificado.configure(text="Regra removida.")

    def abrir_arquivos(self):
        caminhos = filedialog.askopenfilenames(initialdir=self.dir_abertura or "/", title="Selecione os arquivos KIJO (GPRS)", filetypes=(("Arquivos de Texto", "*.txt"), ("Todos", "*.*")))
        if caminhos: 
            self.arquivos_selecionados = list(caminhos); self.dir_abertura = os.path.dirname(caminhos[0]); self.lbl_status_files.configure(text=f"✅ {len(caminhos)} arquivos selecionados", text_color=COLOR_SUCCESS)
            self._salvar_biblioteca()
            self.btn_nova_regra.configure(state="normal")
            self.atualizar_lista_biblioteca()
            self._status_atual = "Pronto para processar."; self.lbl_status_unificado.configure(text=f"🕒 00:00 | 📄 {self._status_atual}"); self.progress_bar.set(0)
            self.tooltip_files.text_list = [os.path.basename(a) for a in self.arquivos_selecionados]

    def abrir_configuracao_colunas(self, f_id, ocorrencia_index=0):
        # 1. Obter condições atuais do filtro
        info = self.filtros[f_id]
        conds = []
        for c in info["condicoes"]:
            pos_val = c["pos_widget"].get().strip()
            if not pos_val:
                continue
            conds.append({
                "posicao": pos_val,
                "operacao": OP_MAP.get(c["op_widget"].get(), c["op_widget"].get()),
                "valor": c["val_widget"].get()
            })
        
        if not conds:
            messagebox.showwarning("Aviso", "Configure pelo menos uma condição com posição antes de configurar a saída!")
            return

        # Status loading
        msg_loading = "Procurando próxima ocorrência..." if ocorrencia_index > 0 else "Procurando ocorrência compatível..."
        self.lbl_status_unificado.configure(text=f"🕒 {msg_loading}")
        
        pop_loading = ctk.CTkToplevel(self.root)
        pop_loading.title("Pesquisando")
        _set_window_icon(pop_loading)
        w_load, h_load = 400, 150
        x_load = (pop_loading.winfo_screenwidth() // 2) - (w_load // 2)
        y_load = (pop_loading.winfo_screenheight() // 2) - (h_load // 2)
        pop_loading.geometry(f"{w_load}x{h_load}+{x_load}+{y_load}")
        pop_loading.resizable(False, False)
        pop_loading.attributes("-topmost", True)
        pop_loading.grab_set()
        
        ctk.CTkLabel(pop_loading, text=msg_loading, font=("Segoe UI", 16, "bold"), text_color="#4F46E5").pack(pady=(30, 10))
        pb = ctk.CTkProgressBar(pop_loading, width=300, mode="indeterminate", progress_color="#4F46E5")
        pb.pack(pady=10)
        pb.start()
        
        busca_cancelada = [False]
        
        def cancelar_busca():
            busca_cancelada[0] = True
            try:
                pop_loading.destroy()
            except Exception:
                pass
                
        pop_loading.protocol("WM_DELETE_WINDOW", cancelar_busca)

        def thread_busca():
            linha_encontrada = None
            filtros_compilados = {}
            # Compila o filtro usando nossa engine existente
            from core.filter_engine import FilterEngine
            filtros_compilados = FilterEngine.compilar_filtros({f_id: conds})
            
            # Determinar se a Posição 2 já foi fixada pelo usuário no filtro (ex: Pos 2 = 33)
            # Se sim, não devemos exigir que a Pos2 seja única nas próximas buscas.
            # A exceção (buscar únicas) é apenas quando NÃO é dito qual o valor esperado na Posição 2.
            tem_pos2_fixa = any(c["posicao"] == "2" and c["operacao"] == "=" for c in conds)
            
            valores_pos2_vistos = set()
            ocorrencias_encontradas = 0
            
            for caminho_arq in self.arquivos_selecionados:
                if busca_cancelada[0]:
                    break
                if not os.path.exists(caminho_arq):
                    continue
                try:
                    # Leitura ultrarápida linha por linha em Python para não travar a UI e gastar pouca RAM
                    with open(caminho_arq, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if busca_cancelada[0]:
                                break
                            if "KIJO" not in line:
                                continue
                            
                            # Extrai a parte do KIJO
                            idx_kijo = line.find("KIJO")
                            if idx_kijo == -1:
                                continue
                            kijo_str = line[idx_kijo:].strip()
                            
                            # Faz o split de teste
                            parts = [p.strip() for p in kijo_str.split(",")]
                            
                            # Valida com as regras compiladas
                            match = True
                            for f_id_key, f_info in filtros_compilados.items():
                                condicoes = f_info["condicoes"]
                                for cond in condicoes:
                                    pos = cond["pos"]
                                    op = cond["op"]
                                    val = cond["val"]
                                    val_num = cond["val_num"]
                                    
                                    if pos < 0 or pos >= len(parts):
                                        match = False
                                        break
                                    
                                    col_val = parts[pos]
                                    if op == "=":
                                        if val_num is not None:
                                            try:
                                                match_val = float(col_val) == val_num
                                            except ValueError:
                                                match_val = col_val == val
                                            if not match_val:
                                                match = False
                                                break
                                        else:
                                            if col_val != val:
                                                match = False
                                                break
                                    elif op == "!=":
                                        if col_val == val:
                                            match = False
                                            break
                                    elif op in [">", "<", ">=", "<="]:
                                        try:
                                            col_num = float(col_val)
                                            if val_num is None:
                                                match = False
                                                break
                                            if op == ">" and not (col_num > val_num): match = False; break
                                            elif op == "<" and not (col_num < val_num): match = False; break
                                            elif op == ">=" and not (col_num >= val_num): match = False; break
                                            elif op == "<=" and not (col_num <= val_num): match = False; break
                                        except ValueError:
                                            match = False
                                            break
                                    elif op == "Contém":
                                        if val not in col_val:
                                            match = False
                                            break
                                if not match:
                                    break
                            
                            if match:
                                if tem_pos2_fixa:
                                    # Posição 2 fixada: qualquer ocorrência serve
                                    # (pois já sabemos o valor esperado na Posição 2)
                                    if ocorrencias_encontradas == ocorrencia_index:
                                        linha_encontrada = kijo_str
                                        break
                                    else:
                                        ocorrencias_encontradas += 1
                                else:
                                    # Busca por ocorrências com Posição 2 única
                                    val_pos2 = parts[1] if len(parts) > 1 else ""
                                    if val_pos2 not in valores_pos2_vistos:
                                        valores_pos2_vistos.add(val_pos2)
                                        if ocorrencias_encontradas == ocorrencia_index:
                                            linha_encontrada = kijo_str
                                            break
                                        else:
                                            ocorrencias_encontradas += 1
                except Exception as ex:
                    print(f"Erro na varredura rápida: {ex}")
                if linha_encontrada:
                    break
            if busca_cancelada[0]:
                self.root.after(0, lambda: self.lbl_status_unificado.configure(text=f"🕒 Busca cancelada."))
                return

            def fechar_loading_e_prosseguir(acao):
                try:
                    pop_loading.withdraw()
                    pop_loading.after(300, pop_loading.destroy)
                except Exception:
                    pass
                acao()

            # Se acabarem as ocorrências e o index for maior que zero, reinicia do primeiro (index 0) de forma transparente!
            if not linha_encontrada and ocorrencia_index > 0:
                self.root.after(0, lambda: fechar_loading_e_prosseguir(lambda: self.abrir_configuracao_colunas(f_id, 0)))
                return

            # Voltar para a main thread do Tkinter
            self.root.after(0, lambda: fechar_loading_e_prosseguir(lambda: self.exibir_modal_colunas(f_id, conds, linha_encontrada, ocorrencia_index)))

        threading.Thread(target=thread_busca, daemon=True).start()

    def exibir_modal_colunas(self, f_id, conds, linha_encontrada, ocorrencia_index):
        self.lbl_status_unificado.configure(text=f"🕒 00:00 | 📄 {self._status_atual}")
        if not linha_encontrada:
            messagebox.showinfo("Busca Concluída", "Nenhuma linha compatível com esse filtro foi encontrada nos arquivos abertos para prévia de colunas.\n\nPor favor, exporte ou adicione dados compatíveis para habilitar a visualização.")
            return
        
        parts = [p.strip() for p in linha_encontrada.split(",")]
        
        # Identificar a assinatura do KIJO (Posições 1, 2 e 4)
        # Primeiro, tenta pegar das condições de busca ativas no filtro
        val_pos1 = ""
        val_pos2 = ""
        val_pos4 = ""
        for c in conds:
            if c["posicao"] == "1":
                val_pos1 = c["valor"].strip()
            elif c["posicao"] == "2":
                val_pos2 = c["valor"].strip()
            elif c["posicao"] == "4":
                val_pos4 = c["valor"].strip()
        
        # Se não vier do filtro, extraímos diretamente da própria linha encontrada!
        # A Posição 1 é o primeiro elemento (parts[0]), Posição 2 é o segundo (parts[1]) e a Posição 4 é o quarto (parts[3])
        if not val_pos1 and len(parts) > 0:
            val_pos1 = parts[0]
        if not val_pos2 and len(parts) > 1:
            val_pos2 = parts[1]
        if not val_pos4 and len(parts) > 3:
            val_pos4 = parts[3]
        
        # Chave identificadora ex: "KIJO1B_33_V4"
        chave_kijo_idx = ""
        if val_pos1 and val_pos2:
            chave_kijo_idx = f"{val_pos1}_{val_pos2}"
            if val_pos4:
                chave_kijo_idx += f"_{val_pos4}"
            chave_kijo_idx = chave_kijo_idx.upper()
        
        # Modal
        pop = ctk.CTkToplevel(self.root)
        pop.title("⚙️ Configurar Colunas de Saída")
        _set_window_icon(pop)
        w, h = 750, 620
        x = (pop.winfo_screenwidth() // 2) - (w // 2)
        y = (pop.winfo_screenheight() // 2) - (h // 2)
        pop.geometry(f"{w}x{h}+{x}+{y}")
        pop.attributes("-topmost", True)
        pop.grab_set()

        # Título
        ctk.CTkLabel(pop, text="⚙️ Selecione e Nomeie as Colunas para Exportação", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT_DARK).pack(pady=(15, 2))
        
        # Como extraímos dinamicamente, chave_kijo_idx estará sempre presente para linhas válidas!
        texto_instrucao = f"Mapeando nomes para o padrão: {chave_kijo_idx}" if chave_kijo_idx else "Modifique os campos de texto para nomear as colunas."
        ctk.CTkLabel(pop, text=texto_instrucao, font=("Segoe UI", 11, "bold"), text_color=COLOR_SECONDARY).pack(pady=(0, 10))

        # Linha Original
        lbl_original = ctk.CTkLabel(pop, text=f"Linha de exemplo encontrada:\n{linha_encontrada}", font=("Consolas", 11), text_color="#10B981", justify="left", wraplength=700)
        lbl_original.pack(pady=5, padx=20, fill="x")

        # Scrollable area para checkboxes e inputs de texto
        scroll = ctk.CTkScrollableFrame(pop, height=270)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Cabeçalho da tabela de colunas
        header_table = ctk.CTkFrame(scroll, fg_color="transparent")
        header_table.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(header_table, text="Exportar?", font=("Segoe UI", 11, "bold"), width=70, anchor="w").pack(side=tk.LEFT)
        ctk.CTkLabel(header_table, text="Nº", font=("Segoe UI", 11, "bold"), width=40, anchor="w").pack(side=tk.LEFT)
        ctk.CTkLabel(header_table, text="Nome da Coluna", font=("Segoe UI", 11, "bold"), width=220, anchor="w").pack(side=tk.LEFT)
        ctk.CTkLabel(header_table, text="Valor da Amostra", font=("Segoe UI", 11, "bold"), anchor="w").pack(side=tk.LEFT)

        checkboxes = []
        entries_nomes = []
        
        # Se já tiver colunas_saida configurado no filtro, carregar as marcas
        colunas_marcadas_anteriormente = self.filtros[f_id].get("colunas_saida", None)
        if colunas_marcadas_anteriormente is None:
            colunas_marcadas_anteriormente = list(range(len(parts)))

        # Carregar nomes de colunas pré-salvos se houver
        nomes_salvos_para_este_kijo = {}
        if chave_kijo_idx:
            nomes_salvos_para_este_kijo = self.nomes_colunas_mapeadas.get(chave_kijo_idx, {})

        # Prévia da linha
        lbl_preview = ctk.CTkLabel(pop, text="Prévia da saída: (todas)", font=("Consolas", 11, "bold"), text_color=COLOR_ACCENT, wraplength=700, justify="left")

        def atualizar_preview(*args):
            colunas_selecionadas = []
            for idx, cb in enumerate(checkboxes):
                if cb.get():
                    colunas_selecionadas.append(idx)
            
            # Montar a string prévia
            if not colunas_selecionadas:
                lbl_preview.configure(text="Prévia da saída: (NENHUMA COLUNA SELECIONADA)")
            else:
                linha_prev = ",".join([parts[i] for i in colunas_selecionadas])
                lbl_preview.configure(text=f"Prévia da saída:\n{linha_prev}")

        # Popular scroll com as linhas de configuração
        for i, campo in enumerate(parts):
            row_item = ctk.CTkFrame(scroll, fg_color="transparent")
            row_item.pack(fill="x", padx=10, pady=4)
            
            var_cb = tk.BooleanVar(value=(i in colunas_marcadas_anteriormente))
            cb = ctk.CTkCheckBox(row_item, text="", variable=var_cb, width=50, command=atualizar_preview)
            cb.pack(side=tk.LEFT)
            checkboxes.append(var_cb)
            
            # Label da Coluna (1-indexed)
            lbl_num = ctk.CTkLabel(row_item, text=f"Col {i+1}", font=("Segoe UI", 12), width=50, anchor="w")
            lbl_num.pack(side=tk.LEFT)
            
            # Campo de entrada para dar nome personalizado (sempre ativado!)
            nome_original_apelido = nomes_salvos_para_este_kijo.get(str(i), f"Coluna {i+1}")
            entry_nome = ctk.CTkEntry(row_item, width=200, font=("Segoe UI", 12))
            entry_nome.insert(0, nome_original_apelido)
            entry_nome.pack(side=tk.LEFT, padx=(0, 15))
            entries_nomes.append(entry_nome)
            
            # Valor da amostra correspondente
            lbl_valor = ctk.CTkLabel(row_item, text=f"->  {campo}", font=("Consolas", 12), text_color="#1F2937", anchor="w")
            lbl_valor.pack(side=tk.LEFT, fill="x", expand=True)

        lbl_preview.pack(pady=10, padx=20, fill="x")
        
        atualizar_preview()

        # Botões de Ação
        btn_frame = ctk.CTkFrame(pop, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)

        def salvar_colunas():
            colunas_selecionadas = []
            for idx, cb in enumerate(checkboxes):
                if cb.get():
                    colunas_selecionadas.append(idx)
            
            if not colunas_selecionadas:
                messagebox.showerror("Erro", "Você precisa selecionar pelo menos 1 coluna para salvar!")
                return
            
            # Salvar nomes personalizados se tiver chave identificadora
            if chave_kijo_idx:
                dict_nomes_novos = {}
                for idx, entry in enumerate(entries_nomes):
                    apelido = entry.get().strip()
                    if apelido:
                        dict_nomes_novos[str(idx)] = apelido
                self.nomes_colunas_mapeadas[chave_kijo_idx] = dict_nomes_novos
                self._salvar_biblioteca() # persiste no JSON

            # Salvar no filtro ativo
            self.filtros[f_id]["colunas_saida"] = colunas_selecionadas
            self.lbl_status_unificado.configure(text=f"Filtro '{self.filtros[f_id]['nome_entry'].get()}' configurado com {len(colunas_selecionadas)} colunas.")
            pop.destroy()

        def marcar_todas():
            for cb in checkboxes:
                cb.set(True)
            atualizar_preview()

        def desmarcar_todas():
            for cb in checkboxes:
                cb.set(False)
            atualizar_preview()

        def procurar_proxima_ocorrencia():
            pop.destroy()
            self.abrir_configuracao_colunas(f_id, ocorrencia_index + 1)

        ctk.CTkButton(btn_frame, text="Marcar Todas", width=110, fg_color="#6B7280", hover_color="#4B5563", font=("Segoe UI", 12, "bold"), command=marcar_todas).pack(side=tk.LEFT, padx=(15, 5))
        ctk.CTkButton(btn_frame, text="Desmarcar Todas", width=120, fg_color="#6B7280", hover_color="#4B5563", font=("Segoe UI", 12, "bold"), command=desmarcar_todas).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Procurar Próxima Ocorrência 🔍", width=220, fg_color=COLOR_WARNING, hover_color="#D97706", font=("Segoe UI", 12, "bold"), command=procurar_proxima_ocorrencia).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Confirmar Saída", width=160, fg_color=COLOR_SUCCESS, hover_color="#059669", font=("Segoe UI", 13, "bold"), command=salvar_colunas).pack(side=tk.RIGHT, padx=15)
# gui_qt/main_window.py — FiltraKIJO Qt (PySide6) v4.3.0
# Port fiel de gui/application.py (CTk) — BUSINESS_RULES §2-§14 como single source of truth
import os
import sys
import json
import time
import re
import gc
import threading
import ctypes

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QComboBox, QScrollArea, QSplitter,
    QProgressBar, QCheckBox, QMessageBox, QFileDialog, QDialog,
    QToolButton, QMenu, QApplication
)
from PySide6.QtCore import Qt, QSize, QTimer, QRegularExpression
from PySide6.QtGui import QIcon, QRegularExpressionValidator, QPixmap
from core.config import VERSION
from core.file_processor import FileProcessor
from core.filter_engine import FilterEngine
from utils.validators import validar_inteiro, validar_valor
from gui_qt.manual import ManualDialog

# ── Validators regex ──────────────────────────────────────────────
RE_INTEIRO = QRegularExpression(r"^([1-9][0-9]{0,2})?$")  # 1-999 + "" (validar_inteiro)
RE_VALOR = QRegularExpression(r"^-?\d*\.?\d*$")           # validar_valor + ""

OP_MAP = {
    "Igual a": "=",
    "Diferente de": "!=",
    "Maior que": ">",
    "Menor que": "<",
    "Maior ou igual a": ">=",
    "Menor ou igual a": "<=",
    "Contém": "Contém",
}
REV_OP_MAP = {v: k for k, v in OP_MAP.items()}
OP_LIST = ["Igual a", "Diferente de", "Maior que", "Menor que", "Maior ou igual a", "Menor ou igual a", "Contém"]

# ── DPI awareness (same as CTk) ───────────────────────────────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def _resource_path(relative_path: str) -> str:
    try:
        base = sys._MEIPASS  # type: ignore
    except Exception:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, relative_path)

def _create_fk_image(tam: int):
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
    dm = ImageDraw.Draw(mascara)
    dm.rounded_rectangle([(0, 0), (tam - 1, tam - 1)], radius=raio, fill=255)
    img.putalpha(mascara)
    if tam >= 64:
        fs = int(tam * 0.58)
    elif tam >= 32:
        fs = int(tam * 0.62)
    else:
        fs = int(tam * 0.60)
    font = None
    for cand in ["C:/Windows/Fonts/arialbd.ttf", "arialbd.ttf", "C:/Windows/Fonts/arial.ttf", "arial.ttf"]:
        try:
            font = ImageFont.truetype(cand, fs)
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
    y = (tam - th) // 2 - bbox[1] - max(1, tam // 32)
    if tam >= 48:
        draw.text((x + 1, y + 1), texto, fill=(0, 0, 0, 90), font=font)
    elif tam >= 32:
        draw.text((x + 1, y + 1), texto, fill=(0, 0, 0, 60), font=font)
    draw.text((x, y), texto, fill=(255, 255, 255, 255), font=font)
    return img

def _set_window_icon(window):
    try:
        icon_path = _resource_path("fk_icon.ico")
        if not os.path.exists(icon_path):
            alt = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "fk_icon.ico")
            if os.path.exists(alt):
                icon_path = alt
        if os.path.exists(icon_path):
            qicon = QIcon(icon_path)
            # Try to add sharp variants via PIL for DPI
            try:
                from PIL import Image
                from PySide6.QtGui import QPixmap
                for sz in [16, 20, 24, 32, 48, 64]:
                    try:
                        img = _create_fk_image(sz)
                        # Convert PIL to QPixmap via buffer
                        import io
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        pm = QPixmap()
                        pm.loadFromData(buf.getvalue(), "PNG")
                        qicon.addPixmap(pm)
                    except Exception:
                        continue
            except Exception:
                pass
            window.setWindowIcon(qicon)
            # keep ref to avoid GC
            window._icon_ref = qicon
    except Exception:
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Filtra KIJO v{VERSION}")
        self.setMinimumSize(1280, 800)
        _set_window_icon(self)

        # State — mirrors gui/application.py:302-317
        self.arquivos_selecionados = []
        self.dir_abertura = ""
        self.dir_salvamento = ""
        self.filtros = {}
        self.contador_filtros = 0
        self.caminho_biblioteca = "filtros_salvos.json"
        self.biblioteca_filtros = {}
        self.nomes_colunas_mapeadas = {}
        self._carregar_biblioteca()

        self._timer_inicio = None
        self._timer_id = None
        self._status_atual = "Aguardando..."

        # Manual dialog (lazy)
        self._manual_dialog = None

        # Validators (shared)
        self._val_pos = QRegularExpressionValidator(RE_INTEIRO)
        self._val_num = QRegularExpressionValidator(RE_VALOR)

        self._setup_ui()

    # ── Biblioteca ────────────────────────────────────────────────
    def _carregar_biblioteca(self):
        self.nomes_colunas_mapeadas = {}
        if os.path.exists(self.caminho_biblioteca):
            try:
                with open(self.caminho_biblioteca, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config = data.pop("__config__", {})
                    self.dir_abertura = config.get("dir_abertura", "")
                    self.dir_salvamento = config.get("dir_salvamento", "")
                    self.nomes_colunas_mapeadas = config.get("nomes_colunas_mapeadas", {})
                    self.biblioteca_filtros = data
                    return
            except Exception:
                self.biblioteca_filtros = {}
                return
        self.biblioteca_filtros = {}

    def _salvar_biblioteca(self):
        try:
            data_to_save = self.biblioteca_filtros.copy()
            data_to_save["__config__"] = {
                "dir_abertura": getattr(self, "dir_abertura", ""),
                "dir_salvamento": getattr(self, "dir_salvamento", ""),
                "nomes_colunas_mapeadas": getattr(self, "nomes_colunas_mapeadas", {})
            }
            with open(self.caminho_biblioteca, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    # ── UI Setup ─────────────────────────────────────────────────
    def _setup_ui(self):
        central = QWidget()
        central.setStyleSheet("background-color: #F3F4F6;")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._criar_header(outer)
        self._criar_corpo(outer)
        self._criar_rodape(outer)

    def _criar_header(self, outer):
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(60)
        header.setStyleSheet("QFrame#Header { background-color: #1F2937; border: none; }")
        outer.addWidget(header)
        vlay = QVBoxLayout(header)
        vlay.setContentsMargins(24, 6, 24, 4)
        vlay.setSpacing(2)
        lbl_logo = QLabel("🔍 Filtra KIJO")
        lbl_logo.setObjectName("Logo")
        lbl_logo.setStyleSheet("color: white; font-size: 22px; font-weight: bold; background: transparent; border: none;")
        self.lbl_status_files = QLabel("Nenhum arquivo selecionado")
        self.lbl_status_files.setStyleSheet("color: #9CA3AF; font-size: 12px; background: transparent; border: none;")
        self.lbl_status_files.setToolTip("Nenhum arquivo selecionado")
        self.btn_abrir = QPushButton("📂 Abrir Arquivo")
        self.btn_abrir.setObjectName("primary")
        self.btn_abrir.setFixedSize(180, 36)
        self.btn_abrir.setCursor(Qt.PointingHandCursor)
        self.btn_abrir.setToolTip("Selecionar arquivos KIJO (GPRS)")
        self.btn_abrir.clicked.connect(self.abrir_arquivos)
        self.btn_ajuda = QPushButton("❓ Ajuda")
        self.btn_ajuda.setStyleSheet("""
            QPushButton { background-color: #4B5563; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #374151; }
            QPushButton:pressed { background-color: #2D3748; }
        """)
        self.btn_ajuda.setFixedSize(110, 36)
        self.btn_ajuda.setCursor(Qt.PointingHandCursor)
        self.btn_ajuda.setToolTip("Abrir manual do usuário")
        self.btn_ajuda.clicked.connect(self.mostrar_manual)
        top = QHBoxLayout()
        top.setSpacing(12)
        top.setContentsMargins(0, 0, 0, 0)
        top.addWidget(lbl_logo)
        top.addStretch(1)
        top.addWidget(self.btn_abrir)
        top.addWidget(self.btn_ajuda)
        vlay.addLayout(top)
        vlay.addWidget(self.lbl_status_files)

    def _criar_corpo(self, outer):
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E5E7EB; }")
        outer.addWidget(splitter, stretch=1)

        # Left — Filtros
        left = QFrame()
        left.setStyleSheet("QFrame { background-color: #F3F4F6; border: none; }")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(16, 16, 8, 16)
        left_lay.setSpacing(8)

        # Left header
        left_header = QFrame()
        left_header.setStyleSheet("background: transparent;")
        lh = QHBoxLayout(left_header)
        lh.setContentsMargins(0, 0, 0, 0)
        title = QLabel("🎯 Regras de Filtragem")
        title.setStyleSheet("color: #1F2937; font-size: 16px; font-weight: bold; background: transparent;")
        lh.addWidget(title)
        lh.addStretch(1)
        self.btn_nova_regra = QPushButton("+ Nova Regra")
        self.btn_nova_regra.setObjectName("success")
        self.btn_nova_regra.setFixedSize(140, 32)
        self.btn_nova_regra.setCursor(Qt.PointingHandCursor)
        self.btn_nova_regra.setToolTip("Criar nova regra de filtragem")
        self.btn_nova_regra.clicked.connect(lambda: self.criar_filtro())
        self.btn_nova_regra.setEnabled(False)
        lh.addWidget(self.btn_nova_regra)
        left_lay.addWidget(left_header)

        # Scroll filtros
        self.scroll_filtros = QScrollArea()
        self.scroll_filtros.setWidgetResizable(True)
        self.scroll_filtros.setStyleSheet("QScrollArea { background: transparent; border: none; } QWidget { background: transparent; }")
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.filter_layout = QVBoxLayout(self.scroll_content)
        self.filter_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_layout.setSpacing(12)
        self.filter_layout.setAlignment(Qt.AlignTop)
        self.scroll_filtros.setWidget(self.scroll_content)
        left_lay.addWidget(self.scroll_filtros, stretch=1)

        # Right — Biblioteca
        right = QFrame()
        right.setMinimumWidth(280)
        right.setMaximumWidth(380)
        right.setStyleSheet("QFrame { background-color: white; border: 1px solid #E5E7EB; border-radius: 10px; }")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        lib_header = QFrame()
        lib_header.setFixedHeight(48)
        lib_header.setStyleSheet("QFrame { background-color: #F9FAFB; border: none; border-bottom: 1px solid #E5E7EB; border-top-left-radius: 10px; border-top-right-radius: 10px; }")
        lh2 = QHBoxLayout(lib_header)
        lh2.setContentsMargins(16, 8, 16, 8)
        lib_title = QLabel("📜 Regras Salvas")
        lib_title.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        lh2.addWidget(lib_title)
        lh2.addStretch(1)
        right_lay.addWidget(lib_header)

        self.scroll_lib = QScrollArea()
        self.scroll_lib.setWidgetResizable(True)
        self.scroll_lib.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.lib_content = QWidget()
        self.lib_content.setStyleSheet("background: transparent;")
        self.lib_layout = QVBoxLayout(self.lib_content)
        self.lib_layout.setContentsMargins(8, 8, 8, 8)
        self.lib_layout.setSpacing(6)
        self.lib_layout.setAlignment(Qt.AlignTop)
        self.scroll_lib.setWidget(self.lib_content)
        right_lay.addWidget(self.scroll_lib, stretch=1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([900, 320])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        self._splitter = splitter
        self.atualizar_lista_biblioteca()

    def _criar_rodape(self, outer):
        rodape = QFrame()
        rodape.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        outer.addWidget(rodape)
        lay = QVBoxLayout(rodape)
        lay.setContentsMargins(24, 12, 24, 16)
        lay.setSpacing(8)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet("QFrame#Card { background-color: white; border: 1px solid #E5E7EB; border-radius: 10px; }")
        lay.addWidget(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 16, 24, 16)
        cl.setSpacing(8)

        self.lbl_status_unificado = QLabel("🕒 00:00 | 📄 Aguardando...")
        self.lbl_status_unificado.setAlignment(Qt.AlignCenter)
        self.lbl_status_unificado.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        cl.addWidget(self.lbl_status_unificado)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        cl.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch(1)
        self.btn_processar = QPushButton("⚡ INICIAR PROCESSAMENTO")
        self.btn_processar.setObjectName("primary")
        self.btn_processar.setFixedSize(240, 40)
        self.btn_processar.setCursor(Qt.PointingHandCursor)
        self.btn_processar.setToolTip("Iniciar processamento dos arquivos com os filtros configurados")
        self.btn_processar.clicked.connect(self.fluxo_processamento)
        btn_row.addWidget(self.btn_processar)

        self.btn_duplicadas = QPushButton("🔍 ANALISAR DUPLICADAS")
        self.btn_duplicadas.setStyleSheet("""
            QPushButton { background-color: #F59E0B; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #D97706; }
            QPushButton:pressed { background-color: #B45309; }
            QPushButton:disabled { background-color: #FDE68A; color: #92400E; }
        """)
        self.btn_duplicadas.setFixedSize(220, 40)
        self.btn_duplicadas.setCursor(Qt.PointingHandCursor)
        self.btn_duplicadas.setToolTip("Analisar duplicatas nos arquivos selecionados")
        self.btn_duplicadas.clicked.connect(self.fluxo_duplicadas)
        btn_row.addWidget(self.btn_duplicadas)
        btn_row.addStretch(1)
        cl.addLayout(btn_row)

    # ── Helpers UI thread ────────────────────────────────────────
    def _after(self, func):
        QTimer.singleShot(0, func)

    def _show_warning(self, title, msg):
        QMessageBox.warning(self, title, msg)

    def _show_error(self, title, msg):
        QMessageBox.critical(self, title, msg)

    def _show_info(self, title, msg):
        QMessageBox.information(self, title, msg)

    # ── Validators ───────────────────────────────────────────────
    def _validar_dinamico(self, P, f_id, cond_idx):
        try:
            idx = int(cond_idx)
            if f_id in self.filtros and idx < len(self.filtros[f_id]["condicoes"]):
                op_label = self.filtros[f_id]["condicoes"][idx]["op_widget"].currentText()
                op = OP_MAP.get(op_label, op_label)
                if op in [">", "<", ">=", "<="]:
                    return validar_valor(P)
            return True
        except Exception:
            return True

    def _update_val_validator(self, f_id, idx):
        if f_id not in self.filtros or idx >= len(self.filtros[f_id]["condicoes"]):
            return
        cond = self.filtros[f_id]["condicoes"][idx]
        op = OP_MAP.get(cond["op_widget"].currentText(), cond["op_widget"].currentText())
        e_val = cond["val_widget"]
        if op in [">", "<", ">=", "<="]:
            e_val.setValidator(self._val_num)
        else:
            e_val.setValidator(None)

    # ── Biblioteca UI ────────────────────────────────────────────
    def atualizar_lista_biblioteca(self):
        # clear
        while self.lib_layout.count():
            item = self.lib_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        has_files = len(self.arquivos_selecionados) > 0
        for nome in sorted(self.biblioteca_filtros.keys()):
            regra_info = self.biblioteca_filtros[nome]
            if isinstance(regra_info, list):
                conds = regra_info
                cols = None
            else:
                conds = regra_info.get("condicoes", [])
                cols = regra_info.get("colunas_saida", None)
            item = QFrame()
            item.setFixedHeight(50)
            item.setStyleSheet("""
                QFrame { background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; }
                QFrame:hover { background-color: #E0E7FF; border: 1px solid #C7D2FE; }
            """)
            item.setCursor(Qt.PointingHandCursor)
            lay = QHBoxLayout(item)
            lay.setContentsMargins(12, 6, 8, 6)
            lay.setSpacing(8)
            btn = QPushButton(f"📜 {nome}")
            btn.setStyleSheet("QPushButton { background: transparent; border: none; text-align: left; color: #1F2937; font-size: 12px; font-weight: bold; } QPushButton:disabled { color: #9CA3AF; }")
            btn.setToolTip(f"Carregar filtro: {nome}")
            btn.setEnabled(has_files)
            if not has_files:
                btn.setToolTip("Selecione os arquivos antes de carregar filtros!")
            # capture correctly
            def _make_load(n=nome, c=conds, cl=cols):
                return lambda: self.criar_filtro(n, c, cl) if len(self.arquivos_selecionados) > 0 else self._show_warning("Aviso", "Selecione os arquivos antes de carregar filtros!")
            btn.clicked.connect(_make_load())
            lay.addWidget(btn, stretch=1)
            del_btn = QToolButton()
            del_btn.setText("🗑")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip(f"Excluir regra: {nome}")
            del_btn.setStyleSheet("QToolButton { background: transparent; border: none; color: #6B7280; font-size: 14px; } QToolButton:hover { background: #FEE2E2; border-radius: 4px; color: #EF4444; }")
            del_btn.clicked.connect(lambda _, n=nome: self.excluir_da_biblioteca(n))
            lay.addWidget(del_btn)
            # right-click context menu ONLY on biblioteca items
            item.setContextMenuPolicy(Qt.CustomContextMenu)
            def _make_menu(pos, n=nome, c=conds, cl=cols, widget=item):
                menu = QMenu(widget)
                act_load = menu.addAction("📥 Carregar")
                act_edit = menu.addAction("✏️ Renomear")
                act_del = menu.addAction("🗑 Excluir")
                act = menu.exec(widget.mapToGlobal(pos))
                if act == act_load:
                    if len(self.arquivos_selecionados) > 0:
                        self.criar_filtro(n, c, cl)
                    else:
                        self._show_warning("Aviso", "Selecione os arquivos antes de carregar filtros!")
                elif act == act_edit:
                    self._renomear_biblioteca(n)
                elif act == act_del:
                    self.excluir_da_biblioteca(n)
            item.customContextMenuRequested.connect(_make_menu)
            item.setToolTip(f"Regra: {nome} — clique para carregar, direito para editar")
            self.lib_layout.addWidget(item)

    def _renomear_biblioteca(self, nome_antigo):
        from PySide6.QtWidgets import QInputDialog
        novo, ok = QInputDialog.getText(self, "Renomear regra", "Novo nome:", text=nome_antigo)
        if ok and novo and novo.strip() and novo.strip() != nome_antigo:
            novo = novo.strip()
            if novo in self.biblioteca_filtros:
                self._show_warning("Aviso", f"Já existe uma regra com nome '{novo}'!")
                return
            self.biblioteca_filtros[novo] = self.biblioteca_filtros.pop(nome_antigo)
            self._salvar_biblioteca()
            self.atualizar_lista_biblioteca()
            self.lbl_status_unificado.setText(f"Regra renomeada para '{novo}'.")

    def excluir_da_biblioteca(self, nome):
        if nome in self.biblioteca_filtros:
            del self.biblioteca_filtros[nome]
            self._salvar_biblioteca()
            self.atualizar_lista_biblioteca()
            self.lbl_status_unificado.setText("Regra removida.")

    # ── Arquivos ─────────────────────────────────────────────────
    def abrir_arquivos(self):
        init = self.dir_abertura or "/"
        files, _ = QFileDialog.getOpenFileNames(self, "Selecione os arquivos KIJO (GPRS)", init, "Arquivos de Texto (*.txt);;Todos (*.*)")
        if files:
            self.arquivos_selecionados = list(files)
            self.dir_abertura = os.path.dirname(files[0])
            self.lbl_status_files.setText(f"✅ {len(files)} arquivos selecionados")
            self.lbl_status_files.setStyleSheet("color: #10B981; font-size: 12px; background: transparent;")
            # tooltip with basenames
            basenames = [os.path.basename(a) for a in self.arquivos_selecionados]
            self.lbl_status_files.setToolTip("\n".join(basenames))
            self._salvar_biblioteca()
            self.btn_nova_regra.setEnabled(True)
            self.atualizar_lista_biblioteca()
            self._status_atual = "Pronto para processar."
            self.lbl_status_unificado.setText(f"🕒 00:00 | 📄 {self._status_atual}")
            self.progress_bar.setValue(0)

    # ── Filtros ──────────────────────────────────────────────────
    def criar_filtro(self, nome_inicial=None, condicoes_iniciais=None, colunas_saida_iniciais=None):
        self.contador_filtros += 1
        f_id = f"filtro_{self.contador_filtros}"
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet("QFrame#Card { background-color: white; border: 1px solid #E5E7EB; border-radius: 8px; }")
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(45)
        header.setStyleSheet("QFrame { background-color: #F1F5F9; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }")
        h = QHBoxLayout(header)
        h.setContentsMargins(12, 6, 12, 6)
        h.setSpacing(8)

        nome_default = nome_inicial if nome_inicial else "Nova Regra"
        entry_nome = QLineEdit()
        entry_nome.setPlaceholderText("Nome do Filtro")
        entry_nome.setText(nome_default)
        entry_nome.setFixedHeight(30)
        entry_nome.setMinimumWidth(180)
        entry_nome.setStyleSheet("QLineEdit { background-color: white; border: 1px solid #E5E7EB; border-radius: 4px; padding: 4px 8px; font-size: 13px; font-weight: bold; } QLineEdit:focus { border: 1px solid #4F46E5; }")
        entry_nome.setToolTip("Nome da regra — usado para salvar na biblioteca e para nomear arquivos com agrupamento")
        h.addWidget(entry_nome, stretch=1)

        btn_config = QPushButton("⚙️ Configurar Saída")
        btn_config.setFixedSize(120, 28)
        btn_config.setObjectName("primary")
        btn_config.setCursor(Qt.PointingHandCursor)
        btn_config.setToolTip("Configurar quais colunas serão exportadas para esta regra")
        btn_config.clicked.connect(lambda: self.abrir_configuracao_colunas(f_id))
        h.addWidget(btn_config)

        btn_save = QPushButton("💾")
        btn_save.setFixedSize(32, 28)
        btn_save.setObjectName("accentSubtle")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setToolTip("Salvar esta regra na biblioteca")
        btn_save.clicked.connect(lambda: self.salvar_na_biblioteca(f_id))
        h.addWidget(btn_save)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 28)
        btn_close.setObjectName("closeSmall")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setToolTip("Remover este filtro")
        btn_close.clicked.connect(lambda: self.remover_filtro(f_id, card))
        h.addWidget(btn_close)

        v.addWidget(header)

        body = QFrame()
        body.setStyleSheet("QFrame { background: transparent; border: none; }")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(12, 12, 12, 12)
        bl.setSpacing(8)

        rows_container = QWidget()
        rows_container.setStyleSheet("background: transparent;")
        rows_lay = QVBoxLayout(rows_container)
        rows_lay.setContentsMargins(0, 0, 0, 0)
        rows_lay.setSpacing(6)
        rows_lay.setAlignment(Qt.AlignTop)
        bl.addWidget(rows_container)

        self.filtros[f_id] = {
            "widget": card,
            "nome_entry": entry_nome,
            "rows_container": rows_container,
            "rows_layout": rows_lay,
            "condicoes": [],
            "colunas_saida": colunas_saida_iniciais
        }

        btn_add = QPushButton("+ Adicionar Condição")
        btn_add.setFixedSize(170, 28)
        btn_add.setStyleSheet("""
            QPushButton { background-color: #6366F1; color: white; border: none; border-radius: 4px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background-color: #4F46E5; }
            QPushButton:pressed { background-color: #4338CA; }
        """)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setToolTip("Adicionar nova condição (AND dentro deste filtro)")
        btn_add.clicked.connect(lambda: self.adicionar_condicao(f_id))
        bl.addWidget(btn_add, alignment=Qt.AlignCenter)

        v.addWidget(body)
        self.filter_layout.addWidget(card)

        if condicoes_iniciais:
            for c in condicoes_iniciais:
                self.adicionar_condicao(f_id, c.get('posicao', ''), c.get('valor', ''), c.get('operacao', '='))
        else:
            self.adicionar_condicao(f_id)

    def adicionar_condicao(self, f_id, pos="", val="", op="="):
        if f_id not in self.filtros:
            return
        info = self.filtros[f_id]
        rows_lay = info["rows_layout"]
        idx = len(info["condicoes"])

        row = QFrame()
        row.setStyleSheet("QFrame { background: transparent; border: none; }")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(8)

        lbl = QLabel("Posição:")
        lbl.setStyleSheet("color: #1F2937; font-size: 12px; background: transparent; border: none;")
        lay.addWidget(lbl)

        e_pos = QLineEdit()
        e_pos.setFixedSize(60, 30)
        e_pos.setValidator(self._val_pos)
        e_pos.setPlaceholderText("Nº")
        e_pos.setText(str(pos))
        e_pos.setObjectName("FilterPos")
        e_pos.setToolTip("Posição da coluna (1-999) — 1 = primeira coluna do KIJO")
        lay.addWidget(e_pos)

        cb_op = QComboBox()
        cb_op.addItems(OP_LIST)
        cb_op.setFixedSize(140, 30)
        cb_op.setCursor(Qt.PointingHandCursor)
        cb_op.setToolTip("Operação de comparação")
        # set current
        rev = REV_OP_MAP.get(op, op)
        if rev in OP_LIST:
            cb_op.setCurrentText(rev)
        elif op in OP_LIST:
            cb_op.setCurrentText(op)
        else:
            # op may be "=" etc.
            inv = REV_OP_MAP.get(op, "=")
            if inv in OP_LIST:
                cb_op.setCurrentText(inv)
        lay.addWidget(cb_op)

        e_val = QLineEdit()
        e_val.setFixedHeight(30)
        e_val.setMinimumWidth(150)
        e_val.setSizePolicy(e_val.sizePolicy().horizontalPolicy(), e_val.sizePolicy().verticalPolicy())
        # Make expanding to avoid squeezing while respecting 150 minimum
        from PySide6.QtWidgets import QSizePolicy
        e_val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        e_val.setText(str(val))
        e_val.setPlaceholderText("Valor")
        e_val.setObjectName("FilterVal")
        e_val.setToolTip("Valor para comparação — vazio só permitido para Igual/Diferente")
        op_code = OP_MAP.get(cb_op.currentText(), cb_op.currentText())
        if op_code in [">", "<", ">=", "<="]:
            e_val.setValidator(self._val_num)
        lay.addWidget(e_val, stretch=1)

        btn_rem = QPushButton("✕")
        btn_rem.setFixedSize(32, 30)
        btn_rem.setObjectName("deleteX")
        btn_rem.setCursor(Qt.PointingHandCursor)
        btn_rem.setToolTip("Remover esta condição")
        lay.addWidget(btn_rem, alignment=Qt.AlignLeft)

        rows_lay.addWidget(row)

        # Style row interactions
        def _clean_val():
            e_val.clear()
            e_val.setValidator(self._val_num if OP_MAP.get(cb_op.currentText(), cb_op.currentText()) in [">", "<", ">=", "<="] else None)

        cb_op.currentTextChanged.connect(lambda _: _clean_val())
        # dynamic validator switch without clearing? need to update validator on change already handled

        # FocusOut uniqueness — editingFinished
        def _check_unique():
            self.verificar_posicao_unica(f_id, e_pos)
        e_pos.editingFinished.connect(_check_unique)

        # also update validator when op changes for this idx
        def _update_val_for_idx(_=None):
            self._update_val_validator(f_id, idx)
        # we need to re-wire after index may shift? For now handle via cb signal that updates current idx's validator via lookup
        cb_op.currentTextChanged.connect(lambda _, fid=f_id, i=idx: self._update_val_validator(fid, i))

        cond_data = {"pos_widget": e_pos, "op_widget": cb_op, "val_widget": e_val, "row_widget": row, "btn_rem": btn_rem}
        btn_rem.clicked.connect(lambda: self.remover_condicao(f_id, row, cond_data))
        self.filtros[f_id]["condicoes"].append(cond_data)
        self.atualizar_visibilidade_botoes(f_id)
        # Reindex validators for all after append
        for i, c in enumerate(self.filtros[f_id]["condicoes"]):
            # reconnect validator update with correct i — we need to disconnect previous? Simplified: update all validators now
            pass

    def verificar_posicao_unica(self, f_id, e_pos):
        pos = e_pos.text().strip()
        if not pos.isdigit():
            return
        for cond in self.filtros[f_id]["condicoes"]:
            if cond["pos_widget"] is not e_pos and cond["pos_widget"].text() == pos:
                self._show_warning("Aviso", f"Posição {pos} já configurada neste filtro!")
                e_pos.clear()
                return

    def remover_condicao(self, f_id, row_widget, cond_data):
        row_widget.deleteLater()
        if f_id in self.filtros and cond_data in self.filtros[f_id]["condicoes"]:
            self.filtros[f_id]["condicoes"].remove(cond_data)
            self.atualizar_visibilidade_botoes(f_id)
            # reindex not needed for Qt but keep validators consistent
            for i, c in enumerate(self.filtros[f_id]["condicoes"]):
                # ensure validator matches op
                self._update_val_validator(f_id, i)

    def atualizar_visibilidade_botoes(self, f_id):
        conds = self.filtros[f_id]["condicoes"]
        if len(conds) == 1:
            conds[0]["btn_rem"].hide()
        else:
            for c in conds:
                c["btn_rem"].show()

    def remover_filtro(self, f_id, card_widget):
        card_widget.deleteLater()
        if f_id in self.filtros:
            del self.filtros[f_id]

    def salvar_na_biblioteca(self, f_id):
        info = self.filtros[f_id]
        nome = info["nome_entry"].text().strip() or f"Filtra_{int(time.time())}"
        conds = [{
            "posicao": c["pos_widget"].text(),
            "operacao": OP_MAP.get(c["op_widget"].currentText(), c["op_widget"].currentText()),
            "valor": c["val_widget"].text()
        } for c in info["condicoes"]]
        self.biblioteca_filtros[nome] = {"condicoes": conds, "colunas_saida": info.get("colunas_saida")}
        self._salvar_biblioteca()
        self.atualizar_lista_biblioteca()
        self.lbl_status_unificado.setText(f"Regra '{nome}' salva.")

    # ── Timer ─────────────────────────────────────────────────────
    def atualizar_timer(self):
        if self._timer_inicio:
            decorrido = time.time() - self._timer_inicio
            minutos = int(decorrido // 60)
            segundos = int(decorrido % 60)
            tempo_str = f"{minutos:02d}:{segundos:02d}"
            self.lbl_status_unificado.setText(f"🕒 {tempo_str} | {self._status_atual}")
            self._timer_id = QTimer.singleShot(1000, self.atualizar_timer)

    def _start_timer(self):
        self._timer_inicio = time.time()
        self.atualizar_timer()

    def _stop_timer(self):
        self._timer_inicio = None
        # QTimer.singleShot can't cancel, but we just stop scheduling
        self._timer_id = None

    # ── Fluxo processamento ───────────────────────────────────────
    def fluxo_processamento(self):
        if not self.arquivos_selecionados:
            self._show_warning("Aviso", "Selecione ao menos um arquivo primeiro!")
            return
        if not self.filtros:
            self._show_warning("Aviso", "Crie ao menos uma regra de filtro!")
            return
        tem_posicao = False
        for f_id, info in self.filtros.items():
            for c in info["condicoes"]:
                if c["pos_widget"].text().strip():
                    tem_posicao = True
                    break
            if tem_posicao:
                break
        if not tem_posicao:
            self._show_warning("Aviso", "Atenção: É obrigatório informar ao menos uma Posição nas regras de filtro!")
            return

        self.progress_bar.setValue(0)
        self._status_atual = "📄 Preparando..."
        self.lbl_status_unificado.setText(f"🕒 00:00 | {self._status_atual}")
        self.lbl_status_unificado.setStyleSheet("color: #4F46E5; font-size: 13px; font-weight: bold; background: transparent; border: none;")

        # Build export dialog (QDialog)
        dlg = QDialog(self)
        dlg.setWindowTitle("Configurar Exportação")
        dlg.setModal(True)
        _set_window_icon(dlg)
        dlg.setFixedSize(500, 320)
        # Center
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        lbl = QLabel("Salvar arquivo(s) como:")
        lbl.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: bold; background: transparent;")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)

        e_nome = QLineEdit()
        e_nome.setPlaceholderText("Opcional: Digite o nome do arquivo único")
        e_nome.setFixedHeight(34)
        lay.addWidget(e_nome)

        # Dynamic container
        container = QFrame()
        container.setStyleSheet("background: transparent;")
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(200)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E5E7EB; border-radius: 6px; background: white; }")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: white;")
        scroll_lay = QVBoxLayout(scroll_content)
        scroll_lay.setAlignment(Qt.AlignTop)
        scroll_lay.setSpacing(8)
        scroll.setWidget(scroll_content)
        container_lay.addWidget(scroll)
        # initially hidden
        container.hide()
        lay.addWidget(container)

        import string
        grupos_disponiveis = [f"Grupo {l}" for l in string.ascii_uppercase]
        self.regra_grupo_map = {}
        self.grupo_nome_map = {}
        # Use QLineEdit dict for group names
        self._grupo_edits = {}
        nomes_usados = set()
        idx = 0
        for f_id in self.filtros:
            nome_base = self.filtros[f_id]["nome_entry"].text().strip() or f_id
            nome_default = nome_base
            contador = 2
            while nome_default in nomes_usados:
                nome_default = f"{nome_base}_{contador}"
                contador += 1
            nomes_usados.add(nome_default)
            grupo_nome = grupos_disponiveis[idx] if idx < len(grupos_disponiveis) else f"Grupo {idx+1}"
            self.regra_grupo_map[f_id] = grupo_nome
            self.grupo_nome_map[grupo_nome] = nome_default
            idx += 1

        def render_grupos():
            # clear
            while scroll_lay.count():
                it = scroll_lay.takeAt(0)
                w = it.widget()
                if w:
                    w.deleteLater()
            self._grupo_edits.clear()
            grupos_ativos = sorted(set(self.regra_grupo_map.values()))
            for grupo in grupos_ativos:
                card = QFrame()
                card.setObjectName("GroupCard")
                card.setStyleSheet("QFrame#GroupCard { background-color: #F3F4F6; border: 1px solid #E5E7EB; border-radius: 8px; }")
                cl = QVBoxLayout(card)
                cl.setContentsMargins(10, 8, 10, 8)
                cl.setSpacing(6)
                header = QHBoxLayout()
                header.setSpacing(8)
                glbl = QLabel(f"{grupo}:")
                glbl.setStyleSheet("color: #1F2937; font-size: 12px; font-weight: bold; background: transparent; border: none;")
                header.addWidget(glbl)
                if grupo not in self.grupo_nome_map:
                    self.grupo_nome_map[grupo] = f"Arquivo_{grupo.replace(' ', '_')}"
                edit = QLineEdit()
                edit.setText(self.grupo_nome_map[grupo])
                edit.setFixedHeight(28)
                edit.setStyleSheet("QLineEdit { background: white; border: 1px solid #E5E7EB; border-radius: 4px; padding: 4px; }")
                edit.setToolTip("Nome do arquivo para este grupo")
                # keep map updated
                def _make_updater(g=grupo, e=edit):
                    def _upd(txt):
                        self.grupo_nome_map[g] = txt
                    return _upd
                edit.textChanged.connect(_make_updater())
                self._grupo_edits[grupo] = edit
                header.addWidget(edit)
                header.addStretch(1)
                cl.addLayout(header)
                for f_id, g in self.regra_grupo_map.items():
                    if g == grupo:
                        rf = QHBoxLayout()
                        nome_regra = self.filtros[f_id]["nome_entry"].text().strip() or f_id
                        lblr = QLabel(f"• {nome_regra}")
                        lblr.setStyleSheet("color: #4B5563; font-size: 11px; background: transparent; border: none;")
                        rf.addWidget(lblr)
                        rf.addStretch(1)
                        opt = QComboBox()
                        opt.addItems(grupos_disponiveis[:max(len(self.filtros), 1)])
                        opt.setCurrentText(grupo)
                        opt.setFixedSize(100, 24)
                        opt.setToolTip("Mover para outro grupo")
                        def _make_change(rule_id):
                            def _chg(new_group):
                                self.regra_grupo_map[rule_id] = new_group
                                # ensure grupo_nome_map has entry
                                if new_group not in self.grupo_nome_map:
                                    # default name from rule
                                    nb = self.filtros[rule_id]["nome_entry"].text().strip() or rule_id
                                    self.grupo_nome_map[new_group] = nb
                                render_grupos()
                            return _chg
                        opt.currentTextChanged.connect(_make_change(f_id))
                        rf.addWidget(opt)
                        cw = QWidget()
                        cw.setStyleSheet("background: transparent;")
                        cw.setLayout(rf)
                        cl.addWidget(cw)
                scroll_lay.addWidget(card)

        # toggle
        chk = QCheckBox("Separar regras de filtro (Agrupamento Dinâmico)")
        chk.setStyleSheet("QCheckBox { color: #1F2937; font-size: 11px; }")
        chk.setToolTip("Cada grupo gerará um arquivo separado")
        def _toggle(state):
            if chk.isChecked():
                e_nome.setEnabled(False)
                dlg.setFixedSize(520, 600)
                container.show()
                render_grupos()
            else:
                e_nome.setEnabled(True)
                dlg.setFixedSize(500, 320)
                container.hide()
        chk.stateChanged.connect(_toggle)
        lay.addWidget(chk)

        lbl_fmt = QLabel("Escolha o formato de saída:")
        lbl_fmt.setStyleSheet("color: #1F2937; font-size: 12px; background: transparent;")
        lbl_fmt.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_fmt)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_txt = QPushButton("📄 TXT (Original)")
        btn_txt.setFixedSize(140, 38)
        btn_txt.setObjectName("ghost")
        btn_txt.setCursor(Qt.PointingHandCursor)
        btn_csv = QPushButton("📊 CSV (Excel)")
        btn_csv.setFixedSize(140, 38)
        btn_csv.setObjectName("ghost")
        btn_csv.setCursor(Qt.PointingHandCursor)
        btn_row.addWidget(btn_txt)
        btn_row.addWidget(btn_csv)
        btn_row.addStretch(1)
        lay.addLayout(btn_row)

        # capturar grupo nome edits antes de fechar
        def _collect_mapa():
            mapa = {}
            for f_id, g in self.regra_grupo_map.items():
                # read from edit if exists
                if g in self._grupo_edits:
                    nome_arq = self._grupo_edits[g].text().strip() or f"Regra_{f_id}"
                else:
                    nome_arq = self.grupo_nome_map.get(g, f"Regra_{f_id}").strip() or f"Regra_{f_id}"
                mapa[f_id] = nome_arq
            return mapa

        def selecionar(fmt):
            nome_custom = e_nome.text().strip()
            separar = chk.isChecked()
            mapa_arquivos = _collect_mapa() if separar else False
            # duplicate group name validation — if two groups have same file name, warn
            if separar and mapa_arquivos:
                vals = list(mapa_arquivos.values())
                if len(vals) != len(set(v.strip().lower() for v in vals)):
                    # Check duplicate group names (case-insensitive)
                    seen = {}
                    dups = set()
                    for v in vals:
                        k = v.strip().lower()
                        if k in seen:
                            dups.add(v)
                        seen[k] = True
                    if dups:
                        self._show_warning("Aviso", f"Nomes de grupo duplicados: {', '.join(dups)}. Cada grupo deve ter nome único.")
                        return
            dlg.accept()
            self.reset_ui()
            self.definir_destino_e_iniciar(fmt, nome_custom, mapa_arquivos if separar else False)

        btn_txt.clicked.connect(lambda: selecionar(".txt"))
        btn_csv.clicked.connect(lambda: selecionar(".csv"))
        dlg.exec()

    def definir_destino_e_iniciar(self, fmt, nome_custom, separar_arquivos=False):
        init = self.dir_salvamento or self.dir_abertura or "/"
        dir_out = QFileDialog.getExistingDirectory(self, "Pasta de Destino", init)
        if not dir_out:
            return
        self.dir_salvamento = dir_out
        self._salvar_biblioteca()
        arquivos_conflito = []
        if isinstance(separar_arquivos, dict):
            for f_id, nome_arq in separar_arquivos.items():
                nome_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_arq)
                nome_final = f"{nome_limpo}{fmt}"
                caminho_chk = os.path.join(dir_out, nome_final)
                if os.path.exists(caminho_chk):
                    if caminho_chk not in arquivos_conflito:
                        arquivos_conflito.append(caminho_chk)
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
            resp = QMessageBox.question(self, "Confirmar Substituição", msg, QMessageBox.Yes | QMessageBox.No)
            if resp != QMessageBox.Yes:
                self.reset_ui()
                return
        self._status_atual = "⌛ PROCESSANDO..."
        self.btn_processar.setEnabled(False)
        self.btn_processar.setText("⌛ PROCESSANDO...")
        self.btn_duplicadas.setEnabled(False)
        self._start_timer()
        # collect formatted filtros
        filtros_formatados = {}
        for f_id, info in self.filtros.items():
            conds = []
            for c in info["condicoes"]:
                conds.append({
                    "posicao": c["pos_widget"].text(),
                    "operacao": OP_MAP.get(c["op_widget"].currentText(), c["op_widget"].currentText()),
                    "valor": c["val_widget"].text()
                })
            if conds:
                filtros_formatados[f_id] = {"nome": info["nome_entry"].text().strip() or f_id, "condicoes": conds, "colunas_saida": info.get("colunas_saida", None)}
        threading.Thread(target=self.executar_thread, args=(filtros_formatados, caminho_completo, fmt, separar_arquivos), daemon=True).start()

    def executar_thread(self, filtros, caminho_final, fmt, separar_arquivos):
        try:
            processor = FileProcessor(
                arquivos_selecionados=self.arquivos_selecionados,
                filtros=filtros,
                progress_callback=self.atualizar_ui_progresso,
                status_callback=self.atualizar_ui_status
            )
            resultado = processor.processar_e_exportar_em_chunks(
                formato=fmt.upper().replace(".", ""),
                caminho_saida=caminho_final,
                separar_arquivos=separar_arquivos
            )
            self._after(lambda r=resultado: self.finalizar_processamento(r))
        except Exception as erro:
            mensagem = str(erro)
            self._after(lambda msg=mensagem: QMessageBox.critical(self, "Erro Fatal", f"Erro no processamento: {msg}"))
            self._after(self.reset_ui)

    def executar_thread_duplicadas(self, caminho_final):
        try:
            processor = FileProcessor(
                arquivos_selecionados=self.arquivos_selecionados,
                filtros={},
                progress_callback=self.atualizar_ui_progresso,
                status_callback=self.atualizar_ui_status
            )
            resultado = processor.processar_apenas_duplicadas(formato="TXT", caminho_saida=caminho_final)
            self._after(lambda r=resultado: self.finalizar_duplicadas(r))
        except Exception as erro:
            mensagem = str(erro)
            self._after(lambda msg=mensagem: QMessageBox.critical(self, "Erro", msg))
            self._after(self.reset_ui)

    # ── Duplicadas ───────────────────────────────────────────────
    def fluxo_duplicadas(self):
        if not self.arquivos_selecionados:
            self._show_warning("Aviso", "Selecione ao menos um arquivo!")
            return
        self.progress_bar.setValue(0)
        self._status_atual = "🔍 Preparando análise..."
        self.lbl_status_unificado.setText(f"🕒 00:00 | {self._status_atual}")
        self.lbl_status_unificado.setStyleSheet("color: #F59E0B; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        init = self.dir_salvamento or self.dir_abertura or "/"
        dir_out = QFileDialog.getExistingDirectory(self, "Pasta de Destino", init)
        if not dir_out:
            return
        self.dir_salvamento = dir_out
        self._salvar_biblioteca()
        nome_final = f"Duplicadas_{int(time.time())}.txt"
        caminho_completo = os.path.join(dir_out, nome_final)
        self._status_atual = "⌛ ANALISANDO..."
        self.btn_processar.setEnabled(False)
        self.btn_duplicadas.setEnabled(False)
        self.btn_duplicadas.setText("⌛ ANALISANDO...")
        self._start_timer()
        threading.Thread(target=self.executar_thread_duplicadas, args=(caminho_completo,), daemon=True).start()

    # ── UI callbacks ─────────────────────────────────────────────
    def atualizar_ui_progresso(self, valor):
        self._after(lambda: self.progress_bar.setValue(int(valor)))

    def atualizar_ui_status(self, msg):
        self._status_atual = f"⚡ {msg}"
        def _upd():
            txt = self.lbl_status_unificado.text()
            timer_parte = txt.split("|")[0].strip() if "|" in txt else "🕒 00:00"
            cor = "#4F46E5"
            if "duplicada" in msg.lower() or "duplicadas" in msg.lower():
                cor = "#F59E0B"
            self.lbl_status_unificado.setText(f"{timer_parte} | {self._status_atual}")
            self.lbl_status_unificado.setStyleSheet(f"color: {cor}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        self._after(_upd)

    def finalizar_processamento(self, resultado):
        self._stop_timer()
        duracao = time.time() - self._timer_inicio if self._timer_inicio else 0
        self._timer_inicio = None
        self.btn_processar.setEnabled(True)
        self.btn_processar.setText("⚡ INICIAR PROCESSAMENTO")
        self.btn_duplicadas.setEnabled(True)
        self.progress_bar.setValue(100)
        m = int(duracao // 60)
        s = int(duracao % 60)
        resumo = f"📄 Encontradas: {resultado['linhas_filtradas']} | 🕒 Tempo: {m:02d}:{s:02d} | ✅ Concluído!"
        self.lbl_status_unificado.setText(resumo)
        self.lbl_status_unificado.setStyleSheet("color: #4F46E5; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        gc.collect()
        self.limpar_memoria()

    def finalizar_duplicadas(self, resultado):
        self._stop_timer()
        duracao = time.time() - self._timer_inicio if self._timer_inicio else 0
        self._timer_inicio = None
        self.btn_processar.setEnabled(True)
        self.btn_duplicadas.setEnabled(True)
        self.btn_duplicadas.setText("🔍 ANALISAR DUPLICADAS")
        self.progress_bar.setValue(100)
        m = int(duracao // 60)
        s = int(duracao % 60)
        resumo = f"🔍 Tipos duplicados: {resultado['tipos_duplicados']} | 📄 Ocorrências: {resultado['linhas_exportadas']} | 🕒 {m:02d}:{s:02d}"
        self.lbl_status_unificado.setText(resumo)
        self.lbl_status_unificado.setStyleSheet("color: #F59E0B; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        gc.collect()
        self.limpar_memoria()

    def limpar_memoria(self):
        try:
            ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
        except Exception as e:
            print(f"Erro ao limpar memória: {e}")

    def reset_ui(self):
        self._stop_timer()
        self.btn_processar.setEnabled(True)
        self.btn_processar.setText("⚡ INICIAR PROCESSAMENTO")
        self.btn_duplicadas.setEnabled(True)
        self.btn_duplicadas.setText("🔍 ANALISAR DUPLICADAS")
        self._status_atual = "Aguardando..."
        self.lbl_status_unificado.setText("🕒 00:00 | 📄 Aguardando...")
        self.lbl_status_unificado.setStyleSheet("color: #1F2937; font-size: 13px; font-weight: bold; background: transparent; border: none;")

    # ── Configurar Saída ─────────────────────────────────────────
    def abrir_configuracao_colunas(self, f_id, ocorrencia_index=0):
        info = self.filtros[f_id]
        conds = []
        for c in info["condicoes"]:
            pos_val = c["pos_widget"].text().strip()
            if not pos_val:
                continue
            conds.append({
                "posicao": pos_val,
                "operacao": OP_MAP.get(c["op_widget"].currentText(), c["op_widget"].currentText()),
                "valor": c["val_widget"].text()
            })
        if not conds:
            self._show_warning("Aviso", "Configure pelo menos uma condição com posição antes de configurar a saída!")
            return
        msg_loading = "Procurando próxima ocorrência..." if ocorrencia_index > 0 else "Procurando ocorrência compatível..."
        self.lbl_status_unificado.setText(f"🕒 {msg_loading}")

        # loading dialog 400x150
        dlg = QDialog(self)
        dlg.setWindowTitle("Pesquisando")
        _set_window_icon(dlg)
        dlg.setFixedSize(400, 150)
        dlg.setModal(True)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        lay = QVBoxLayout(dlg)
        lay.setAlignment(Qt.AlignCenter)
        lbl = QLabel(msg_loading)
        lbl.setStyleSheet("color: #4F46E5; font-size: 14px; font-weight: bold; background: transparent;")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)
        pb = QProgressBar()
        pb.setRange(0, 0)
        pb.setFixedSize(300, 14)
        pb.setTextVisible(False)
        lay.addWidget(pb, alignment=Qt.AlignCenter)

        busca_cancelada = [False]
        def _on_close():
            busca_cancelada[0] = True
            dlg.reject()
        dlg.rejected.connect(lambda: busca_cancelada.__setitem__(0, True))
        # thread
        def thread_busca():
            linha_encontrada = None
            filtros_compilados = FilterEngine.compilar_filtros({f_id: conds})
            tem_pos2_fixa = any(c["posicao"] == "2" and c["operacao"] == "=" for c in conds)
            valores_pos2_vistos = set()
            ocorrencias_encontradas = 0
            for caminho_arq in self.arquivos_selecionados:
                if busca_cancelada[0]:
                    break
                if not os.path.exists(caminho_arq):
                    continue
                try:
                    with open(caminho_arq, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if busca_cancelada[0]:
                                break
                            if "KIJO" not in line:
                                continue
                            idx_kijo = line.find("KIJO")
                            if idx_kijo == -1:
                                continue
                            kijo_str = line[idx_kijo:].strip()
                            parts = [p.strip() for p in kijo_str.split(",")]
                            # validate manually — replica CTk exato
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
                                    if ocorrencias_encontradas == ocorrencia_index:
                                        linha_encontrada = kijo_str
                                        break
                                    else:
                                        ocorrencias_encontradas += 1
                                else:
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
                self._after(lambda: self.lbl_status_unificado.setText("🕒 Busca cancelada."))
                self._after(lambda: dlg.reject() if dlg.isVisible() else None)
                return
            def _close_and_proceed(action):
                try:
                    dlg.accept()
                except Exception:
                    pass
                QTimer.singleShot(50, action)
            if not linha_encontrada and ocorrencia_index > 0:
                self._after(lambda: _close_and_proceed(lambda: self.abrir_configuracao_colunas(f_id, 0)))
                return
            self._after(lambda: _close_and_proceed(lambda: self.exibir_modal_colunas(f_id, conds, linha_encontrada, ocorrencia_index)))
        threading.Thread(target=thread_busca, daemon=True).start()
        dlg.exec()

    def exibir_modal_colunas(self, f_id, conds, linha_encontrada, ocorrencia_index):
        self.lbl_status_unificado.setText(f"🕒 00:00 | 📄 {self._status_atual}")
        if not linha_encontrada:
            self._show_info("Busca Concluída", "Nenhuma linha compatível com esse filtro foi encontrada nos arquivos abertos para prévia de colunas.\n\nPor favor, exporte ou adicione dados compatíveis para habilitar a visualização.")
            return
        parts = [p.strip() for p in linha_encontrada.split(",")]
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
        if not val_pos1 and len(parts) > 0:
            val_pos1 = parts[0]
        if not val_pos2 and len(parts) > 1:
            val_pos2 = parts[1]
        if not val_pos4 and len(parts) > 3:
            val_pos4 = parts[3]
        chave_kijo_idx = ""
        if val_pos1 and val_pos2:
            chave_kijo_idx = f"{val_pos1}_{val_pos2}"
            if val_pos4:
                chave_kijo_idx += f"_{val_pos4}"
            chave_kijo_idx = chave_kijo_idx.upper()

        dlg = QDialog(self)
        dlg.setWindowTitle("⚙️ Selecione e Nomeie as Colunas para Exportação")
        _set_window_icon(dlg)
        dlg.setFixedSize(750, 620)
        dlg.setModal(True)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        title = QLabel("⚙️ Selecione e Nomeie as Colunas para Exportação")
        title.setStyleSheet("color: #1F2937; font-size: 14px; font-weight: bold; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        texto_instrucao = f"Mapeando nomes para o padrão: {chave_kijo_idx}" if chave_kijo_idx else "Modifique os campos de texto para nomear as colunas."
        instr = QLabel(texto_instrucao)
        instr.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: bold; background: transparent;")
        instr.setAlignment(Qt.AlignCenter)
        lay.addWidget(instr)

        lbl_original = QLabel(f"Linha de exemplo encontrada:\n{linha_encontrada}")
        lbl_original.setStyleSheet("color: #10B981; font-family: Consolas, monospace; font-size: 11px; background: transparent;")
        lbl_original.setWordWrap(True)
        lay.addWidget(lbl_original)

        # header da tabela
        header_tbl = QHBoxLayout()
        for txt, w in [("Exportar?", 70), ("Nº", 40), ("Nome da Coluna", 220)]:
            l = QLabel(txt)
            l.setFixedWidth(w)
            l.setStyleSheet("color: #1F2937; font-size: 11px; font-weight: bold; background: transparent;")
            header_tbl.addWidget(l)
        l = QLabel("Valor da Amostra")
        l.setStyleSheet("color: #1F2937; font-size: 11px; font-weight: bold; background: transparent;")
        header_tbl.addWidget(l)
        lay.addLayout(header_tbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(270)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E5E7EB; border-radius: 6px; background: white; }")
        content = QWidget()
        content.setStyleSheet("background: white;")
        cl = QVBoxLayout(content)
        cl.setAlignment(Qt.AlignTop)
        cl.setSpacing(4)
        scroll.setWidget(content)
        lay.addWidget(scroll)

        colunas_marcadas_anteriormente = self.filtros[f_id].get("colunas_saida", None)
        if colunas_marcadas_anteriormente is None:
            colunas_marcadas_anteriormente = list(range(len(parts)))
        nomes_salvos_para_este_kijo = {}
        if chave_kijo_idx:
            nomes_salvos_para_este_kijo = self.nomes_colunas_mapeadas.get(chave_kijo_idx, {})

        lbl_preview = QLabel("Prévia da saída: (todas)")
        lbl_preview.setStyleSheet("color: #4F46E5; font-family: Consolas, monospace; font-size: 11px; font-weight: bold; background: transparent;")
        lbl_preview.setWordWrap(True)
        # checkboxes and entries
        checkboxes = []
        entries_nomes = []
        for i, campo in enumerate(parts):
            row = QHBoxLayout()
            row.setSpacing(8)
            cb = QCheckBox()
            cb.setChecked(i in colunas_marcadas_anteriormente)
            cb.setStyleSheet("QCheckBox { background: transparent; } QCheckBox::indicator { width: 16px; height: 16px; }")
            checkboxes.append(cb)
            rw = QWidget()
            rw.setStyleSheet("background: transparent;")
            rwl = QHBoxLayout(rw)
            rwl.setContentsMargins(0, 0, 0, 0)
            rwl.setSpacing(8)
            rwl.addWidget(cb)
            lbl_num = QLabel(f"Col {i+1}")
            lbl_num.setFixedWidth(50)
            lbl_num.setStyleSheet("color: #1F2937; font-size: 11px; background: transparent;")
            rwl.addWidget(lbl_num)
            nome_pad = nomes_salvos_para_este_kijo.get(str(i), f"Coluna {i+1}")
            entry_nome = QLineEdit()
            entry_nome.setText(nome_pad)
            entry_nome.setFixedWidth(200)
            entry_nome.setToolTip("Nome da coluna para este padrão KIJO — será lembrado")
            rwl.addWidget(entry_nome)
            entries_nomes.append(entry_nome)
            lbl_valor = QLabel(f"->  {campo}")
            lbl_valor.setStyleSheet("color: #1F2937; font-family: Consolas, monospace; font-size: 11px; background: transparent;")
            rwl.addWidget(lbl_valor, stretch=1)
            # wrapper frame
            fr = QFrame()
            fr.setStyleSheet("QFrame { background: white; border: none; }")
            fr.setLayout(rwl)
            cl.addWidget(fr)

        def atualizar_preview(*args):
            sel = [idx for idx, cb in enumerate(checkboxes) if cb.isChecked()]
            if not sel:
                lbl_preview.setText("Prévia da saída: (NENHUMA COLUNA SELECIONADA)")
            else:
                linha_prev = ",".join([parts[i] for i in sel])
                lbl_preview.setText(f"Prévia da saída:\n{linha_prev}")

        for cb in checkboxes:
            cb.stateChanged.connect(atualizar_preview)
        atualizar_preview()
        lay.addWidget(lbl_preview)

        btn_frame = QHBoxLayout()
        btn_frame.setSpacing(8)
        def _marcar_todas():
            for cb in checkboxes:
                cb.setChecked(True)
        def _desmarcar_todas():
            for cb in checkboxes:
                cb.setChecked(False)
        def _procurar_proxima():
            dlg.accept()
            self.abrir_configuracao_colunas(f_id, ocorrencia_index + 1)
        def _salvar_colunas():
            selecionadas = [idx for idx, cb in enumerate(checkboxes) if cb.isChecked()]
            if not selecionadas:
                self._show_error("Erro", "Você precisa selecionar pelo menos 1 coluna para salvar!")
                return
            if chave_kijo_idx:
                dict_nomes = {}
                for idx, entry in enumerate(entries_nomes):
                    apelido = entry.text().strip()
                    if apelido:
                        dict_nomes[str(idx)] = apelido
                self.nomes_colunas_mapeadas[chave_kijo_idx] = dict_nomes
                self._salvar_biblioteca()
            self.filtros[f_id]["colunas_saida"] = selecionadas
            self.lbl_status_unificado.setText(f"Filtro '{self.filtros[f_id]['nome_entry'].text()}' configurado com {len(selecionadas)} colunas.")
            dlg.accept()

        btn_all = QPushButton("Marcar Todas")
        btn_all.setFixedSize(110, 30)
        btn_all.setStyleSheet("QPushButton { background: #6B7280; color: white; border: none; border-radius: 4px; font-size: 11px; font-weight: bold; } QPushButton:hover { background: #4B5563; }")
        btn_all.clicked.connect(_marcar_todas)
        btn_none = QPushButton("Desmarcar Todas")
        btn_none.setFixedSize(120, 30)
        btn_none.setStyleSheet("QPushButton { background: #6B7280; color: white; border: none; border-radius: 4px; font-size: 11px; font-weight: bold; } QPushButton:hover { background: #4B5563; }")
        btn_none.clicked.connect(_desmarcar_todas)
        btn_next = QPushButton("Procurar Próxima Ocorrência 🔍")
        btn_next.setFixedSize(210, 30)
        btn_next.setStyleSheet("QPushButton { background: #F59E0B; color: white; border: none; border-radius: 4px; font-size: 11px; font-weight: bold; } QPushButton:hover { background: #D97706; }")
        btn_next.clicked.connect(_procurar_proxima)
        btn_ok = QPushButton("Confirmar Saída")
        btn_ok.setFixedSize(150, 30)
        btn_ok.setObjectName("success")
        btn_ok.clicked.connect(_salvar_colunas)

        btn_frame.addWidget(btn_all)
        btn_frame.addWidget(btn_none)
        btn_frame.addWidget(btn_next)
        btn_frame.addStretch(1)
        btn_frame.addWidget(btn_ok)
        lay.addLayout(btn_frame)

        dlg.exec()

    def mostrar_manual(self):
        if self._manual_dialog is None:
            self._manual_dialog = ManualDialog(self)
        self._manual_dialog.show_manual()


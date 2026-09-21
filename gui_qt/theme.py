# gui_qt/theme.py — FiltraKIJO Qt Light Theme (v4.3.0)
# Visual shell only — core unchanged

from PySide6.QtWidgets import QProxyStyle, QStyle
from PySide6.QtGui import QColor, QPolygonF, QPainterPath
from PySide6.QtCore import QPointF

# ── Colors ──────────────────────────────────────────────────────────
COLOR_HEADER = "#1F2937"
COLOR_BG = "#F3F4F6"
COLOR_CARD = "#FFFFFF"
COLOR_CARD_ALT = "#F9FAFB"
COLOR_BORDER = "#E5E7EB"
COLOR_BORDER_HOVER = "#D1D5DB"
COLOR_TEXT_DARK = "#1F2937"
COLOR_TEXT_MUTED = "#6B7280"
COLOR_TEXT_LIGHT = "#FFFFFF"
COLOR_TEXT_DISABLED = "#9CA3AF"
COLOR_ACCENT = "#4F46E5"
COLOR_ACCENT_HOVER = "#4338CA"
COLOR_ACCENT_ACTIVE = "#3730A3"
COLOR_SUCCESS = "#10B981"
COLOR_SUCCESS_HOVER = "#059669"
COLOR_WARNING = "#F59E0B"
COLOR_WARNING_HOVER = "#D97706"
COLOR_DANGER = "#EF4444"
COLOR_DANGER_HOVER = "#DC2626"
COLOR_HOVER_LIGHT = "#E0E7FF"
COLOR_FOCUS = "#4F46E5"

BG_PRIMARY = COLOR_BG
BG_SECONDARY = "#FFFFFF"
BG_CARD = COLOR_CARD
BG_HOVER = "#F3F4F6"
BG_INPUT = "#FFFFFF"
TEXT_PRIMARY = COLOR_TEXT_DARK
TEXT_DISABLED = COLOR_TEXT_DISABLED
ACCENT_HOVER = COLOR_ACCENT_HOVER
BORDER_SUBTLE = COLOR_BORDER
BORDER_FOCUS = COLOR_FOCUS

# ── Spacing / Radius / Fonts ──────────────────────────────────────
XS = 4
SM = 8
MD = 16
LG = 24
XL = 32
RADIUS_SM = 4
RADIUS_MD = 6
RADIUS_LG = 10
FONT_CAPTION = 11
FONT_BODY = 12
FONT_SUBTITLE = 17
FONT_TITLE = 22
FONT_HEADER = 28

BRANCH_ARROW_COLOR = QColor("#9CA3AF")

# ── Global QSS ────────────────────────────────────────────────────
GLOBAL_STYLE = f"""
QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT_DARK};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}}

QMainWindow {{
    background-color: {COLOR_BG};
}}

QFrame#Header {{
    background-color: {COLOR_HEADER};
    border: none;
}}

QFrame#Card {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_LG}px;
}}

QFrame#FilterCard {{
    background-color: {COLOR_CARD_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
}}

QFrame#GroupCard {{
    background-color: #F3F4F6;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
}}

QScrollArea {{
    background-color: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

/* ── QLabel ── */
QLabel {{
    background-color: transparent;
    color: {COLOR_TEXT_DARK};
}}
QLabel#Logo {{
    color: {COLOR_TEXT_LIGHT};
    font-size: 22px;
    font-weight: bold;
    background-color: transparent;
}}
QLabel#Subtitle {{
    color: #9CA3AF;
    font-size: 11px;
    background-color: transparent;
}}

/* ── QPushButton base ── */
QPushButton {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT_DARK};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_SM}px;
    padding: 6px 12px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {COLOR_HOVER_LIGHT};
    border: 1px solid {COLOR_BORDER_HOVER};
}}
QPushButton:pressed {{
    background-color: {COLOR_BORDER};
}}
QPushButton:disabled {{
    background-color: #F9FAFB;
    color: {COLOR_TEXT_DISABLED};
    border: 1px solid #E5E7EB;
}}

/* Variants */
QPushButton#primary {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT_LIGHT};
    border: none;
}}
QPushButton#primary:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}
QPushButton#primary:pressed {{
    background-color: {COLOR_ACCENT_ACTIVE};
}}
QPushButton#primary:disabled {{
    background-color: #A5B4FC;
    color: white;
}}

QPushButton#success {{
    background-color: {COLOR_SUCCESS};
    color: white;
    border: none;
}}
QPushButton#success:hover {{
    background-color: {COLOR_SUCCESS_HOVER};
}}
QPushButton#success:pressed {{
    background-color: #047857;
}}

QPushButton#warning {{
    background-color: {COLOR_WARNING};
    color: white;
    border: none;
}}
QPushButton#warning:hover {{
    background-color: {COLOR_WARNING_HOVER};
}}
QPushButton#warning:pressed {{
    background-color: #B45309;
}}

QPushButton#dangerSubtle {{
    background-color: transparent;
    color: {COLOR_DANGER};
    border: none;
}}
QPushButton#dangerSubtle:hover {{
    background-color: #FEE2E2;
    border: none;
}}
QPushButton#dangerSubtle:pressed {{
    background-color: #FECACA;
}}

QPushButton#accentSubtle {{
    background-color: transparent;
    color: {COLOR_ACCENT};
    border: none;
}}
QPushButton#accentSubtle:hover {{
    background-color: {COLOR_HOVER_LIGHT};
    border: none;
}}
QPushButton#accentSubtle:pressed {{
    background-color: #C7D2FE;
}}

QPushButton#ghost {{
    background-color: transparent;
    color: {COLOR_TEXT_MUTED};
    border: 1px solid {COLOR_BORDER};
}}
QPushButton#ghost:hover {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT_DARK};
    border: 1px solid {COLOR_ACCENT};
}}
QPushButton#ghost:pressed {{
    background-color: {COLOR_BORDER};
}}

QPushButton#closeSmall {{
    background-color: transparent;
    color: {COLOR_DANGER};
    border: none;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton#closeSmall:hover {{
    background-color: #FEE2E2;
}}
QPushButton#closeSmall:pressed {{
    background-color: #FECACA;
}}

QPushButton#deleteX {{
    background-color: transparent;
    color: {COLOR_DANGER};
    border: none;
}}
QPushButton#deleteX:hover {{
    background-color: #FEE2E2;
}}

/* ── QLineEdit ── */
QLineEdit {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT_DARK};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_SM}px;
    padding: 6px 8px;
    selection-background-color: {COLOR_HOVER_LIGHT};
}}
QLineEdit:focus {{
    border: 1px solid {COLOR_FOCUS};
}}
QLineEdit:hover {{
    border: 1px solid {COLOR_BORDER_HOVER};
}}
QLineEdit:disabled {{
    background-color: #F9FAFB;
    color: {COLOR_TEXT_DISABLED};
}}
QLineEdit#SearchInput {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 14px;
    padding: 4px 10px;
}}
QLineEdit#FilterPos {{
    background-color: white;
    border: 1px solid {COLOR_BORDER};
}}
QLineEdit#FilterVal {{
    background-color: white;
    border: 1px solid {COLOR_BORDER};
}}

/* ── QComboBox ── */
QComboBox {{
    background-color: white;
    color: {COLOR_TEXT_DARK};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_SM}px;
    padding: 5px 8px;
    padding-right: 24px;
}}
QComboBox:focus {{
    border: 1px solid {COLOR_FOCUS};
}}
QComboBox:hover {{
    border: 1px solid {COLOR_BORDER_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox::down-arrow {{
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLOR_TEXT_MUTED};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: white;
    color: {COLOR_TEXT_DARK};
    border: 1px solid {COLOR_BORDER};
    selection-background-color: #E0E7FF;
    selection-color: {COLOR_TEXT_DARK};
    padding: 2px;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 8px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {COLOR_HOVER_LIGHT};
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: #E0E7FF;
}}

/* ── QProgressBar ── */
QProgressBar {{
    background-color: #E5E7EB;
    border: none;
    border-radius: 7px;
    text-align: center;
    color: {COLOR_TEXT_DARK};
    height: 14px;
}}
QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: 7px;
}}

/* ── QCheckBox ── */
QCheckBox {{
    color: {COLOR_TEXT_DARK};
    background-color: transparent;
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #D1D5DB;
    border-radius: 3px;
    background-color: white;
}}
QCheckBox::indicator:hover {{
    border: 1px solid {COLOR_ACCENT};
}}
QCheckBox::indicator:checked {{
    background-color: {COLOR_ACCENT};
    border: 1px solid {COLOR_ACCENT};
    image: none;
}}
QCheckBox::indicator:checked:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

/* ── QScrollBar ── */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: #D1D5DB;
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: #D1D5DB;
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLOR_ACCENT};
}}

/* ── QToolTip light ── */
QToolTip {{
    background-color: #FFFFFF;
    color: #1F2937;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 11px;
}}

/* ── QDialog ── */
QDialog {{
    background-color: white;
}}

/* ── QMenu (right-click biblioteca) ── */
QMenu {{
    background-color: white;
    color: {COLOR_TEXT_DARK};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {COLOR_HOVER_LIGHT};
    color: {COLOR_ACCENT};
}}

/* ── QSplitter ── */
QSplitter::handle {{
    background-color: #E5E7EB;
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}
"""

# LightBranchStyle for QTreeView branch arrows (optional, not used heavily but kept for parity)
try:
    class LightBranchStyle(QProxyStyle):
        def drawPrimitive(self, element, option, painter, widget=None):
            if element == QStyle.PE_IndicatorBranch:
                state = option.state
                rect = option.rect
                if state & QStyle.State_Children:
                    painter.save()
                    painter.setRenderHint(painter.Antialiasing)
                    painter.setPen(QColor("transparent"))
                    painter.setBrush(BRANCH_ARROW_COLOR)
                    cx = rect.x() + rect.width() / 2
                    cy = rect.y() + rect.height() / 2
                    r = min(rect.width(), rect.height()) * 0.22
                    if state & QStyle.State_Open:
                        tri = QPolygonF([
                            QPointF(cx - r, cy - r * 0.6),
                            QPointF(cx + r, cy - r * 0.6),
                            QPointF(cx, cy + r * 1.0),
                        ])
                    else:
                        tri = QPolygonF([
                            QPointF(cx - r * 0.6, cy - r),
                            QPointF(cx - r * 0.6, cy + r),
                            QPointF(cx + r * 1.0, cy),
                        ])
                    path = QPainterPath()
                    path.addPolygon(tri)
                    painter.drawPath(path)
                    painter.restore()
                    return
            super().drawPrimitive(element, option, painter, widget)
except Exception:
    LightBranchStyle = None

CHECKBOX_STYLE = """
QCheckBox { color: #1F2937; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #D1D5DB; border-radius: 3px;
    background-color: white;
}
QCheckBox::indicator:checked {
    background-color: #4F46E5; border-color: #4F46E5;
}
"""

def get_status_color(status: str) -> str:
    return COLOR_SUCCESS if "Conclu" in status else COLOR_WARNING if "duplic" in status.lower() else COLOR_ACCENT

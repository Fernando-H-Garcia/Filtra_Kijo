# main_qt.py — FiltraKIJO Qt entrypoint (PySide6) v4.3.0
import os
import sys

def _resource_path(relative_path: str) -> str:
    try:
        base = sys._MEIPASS  # type: ignore
    except Exception:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Icon — same as Tk: via QIcon + _resource_path
    icon_path = _resource_path("fk_icon.ico")
    alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fk_icon.ico")
    try:
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        elif os.path.exists(alt):
            app.setWindowIcon(QIcon(alt))
    except Exception:
        pass

    # Theme — Light FiltraKIJO + LightBranchStyle (parity with Central_de_Gestão)
    try:
        from gui_qt.theme import GLOBAL_STYLE, LightBranchStyle
        if LightBranchStyle is not None:
            app.setStyle(LightBranchStyle(app.style()))
        app.setStyleSheet(GLOBAL_STYLE)
    except Exception as e:
        print(f"Warning: could not apply theme: {e}")

    from gui_qt.main_window import MainWindow
    w = MainWindow()
    # Window icon explicit (besides app icon)
    try:
        if os.path.exists(icon_path):
            w.setWindowIcon(QIcon(icon_path))
        elif os.path.exists(alt):
            w.setWindowIcon(QIcon(alt))
    except Exception:
        pass
    w.showMaximized()
    sys.exit(app.exec())

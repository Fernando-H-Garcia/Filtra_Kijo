# main.py

import multiprocessing
import ctypes
import sys

# --- APP ID único: DEVE vir antes de criar qualquer janela ---
# Unifica o ícone fixado na barra com o ícone em execução (evita duplicar + embaçado)
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Tecsoil.FiltraKIJO.v4.2.0")
except Exception:
    pass

import customtkinter as ctk
from gui.application import AplicacaoVisual

if __name__ == "__main__":
    # Necessário para rodar o ProcessPoolExecutor dentro de um .exe no Windows
    multiprocessing.freeze_support()
    
    # Define o tema antes de criar a janela
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = AplicacaoVisual(root)
    root.mainloop()
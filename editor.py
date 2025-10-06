# editor.py
import os
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import tkinter.font as tkfont
from PIL import Image, ImageTk
from pdf_utils import load_page_image, save_pdf_with_texts

FONTS_DIR = "fonts"
DEFAULT_COLORS = ["#000000", "#FF0000", "#0000FF", "#008000", "#FFA500", "#800080", "#808080"]


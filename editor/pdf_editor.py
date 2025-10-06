import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
from PIL import Image, ImageTk
from .canvas_textbox import CanvasTextBox
from .pdf_utils import load_page_image, save_pdf_with_texts

FONTS_DIR = "fonts"
DEFAULT_COLORS = ["#000000", "#FF0000", "#0000FF", "#008000", "#FFA500", "#800080", "#808080"]

class PDFEditor:
	def __init__(self, root):
		self.root = root
		self.pdf_path = None
		self.display_img = None
		self.scale = 1.0
		self.textboxes = []
		self.selected_box = None
		self.dragging = False
		self.resizing = False
		self.resize_handle = None
		self.last_mouse = (0,0)
		self.clipboard_internal = ""

		self._load_fonts()
		self._build_ui()
		self._bind_shortcuts()

	# ---------------- font helpers ----------------
	def _load_fonts(self):
		self.system_fonts = sorted(set(tkfont.families()))
		self.custom_fonts = []
		if os.path.isdir(FONTS_DIR):
			for f in os.listdir(FONTS_DIR):
				if f.lower().endswith(".ttf"):
					self.custom_fonts.append(os.path.splitext(f)[0])
		self.font_list = self.custom_fonts + self.system_fonts

	# ---------------- UI ----------------
	def _build_ui(self):
		style = ttk.Style(self.root)
		style.theme_use("clam")
		toolbar = ttk.Frame(self.root, padding=4)
		toolbar.pack(side="top", fill="x")

		self.open_btn = ttk.Button(toolbar, text="📂 Apri", command=self.open_pdf)
		self.open_btn.pack(side="left", padx=4)
		self.save_btn = ttk.Button(toolbar, text="💾 Salva", command=self.save_pdf)
		self.save_btn.pack(side="left", padx=4)

		self.font_var = tk.StringVar(value="Arial")
		self.font_combo = ttk.Combobox(toolbar, textvariable=self.font_var, values=self.font_list, width=25)
		self.font_combo.pack(side="left", padx=4)
		self.font_combo.bind("<<ComboboxSelected>>", lambda e: self._update_selected_properties())

		self.size_var = tk.IntVar(value=12)
		self.size_combo = ttk.Combobox(toolbar, textvariable=self.size_var, values=[8,10,12,14,16,18,20,24,32], width=4)
		self.size_combo.pack(side="left", padx=4)
		self.size_combo.bind("<<ComboboxSelected>>", lambda e: self._update_selected_properties())

		self.color_var = tk.StringVar(value=DEFAULT_COLORS[0])
		self.color_var.trace_add("write", lambda *args: self._update_selected_properties())
		color_frame = ttk.Frame(toolbar)
		color_frame.pack(side="left", padx=6)
		for c in DEFAULT_COLORS:
			b = tk.Button(color_frame, bg=c, width=2, command=lambda col=c: self.color_var.set(col))
			b.pack(side="left", padx=2)

		self.align_var = tk.StringVar(value="left")
		ttk.Button(toolbar, text="⟸", command=lambda: self.align_set("left")).pack(side="left", padx=6)
		ttk.Button(toolbar, text="≡", command=lambda: self.align_set("center")).pack(side="left", padx=2)
		ttk.Button(toolbar, text="⟹", command=lambda: self.align_set("right")).pack(side="left", padx=2)

		self.del_btn = ttk.Button(toolbar, text="🗑 Rimuovi", command=self.remove_selected)
		self.del_btn.pack(side="left", padx=4)

		canvas_frame = ttk.Frame(self.root)
		canvas_frame.pack(fill="both", expand=True)
		self.hbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
		self.hbar.pack(side="bottom", fill="x")
		self.vbar = ttk.Scrollbar(canvas_frame, orient="vertical")
		self.vbar.pack(side="right", fill="y")
		self.canvas = tk.Canvas(canvas_frame, bg="#f3f3f3", xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
		self.canvas.pack(fill="both", expand=True, side="left")
		self.hbar.config(command=self.canvas.xview)
		self.vbar.config(command=self.canvas.yview)

		self.canvas.bind("<Button-1>", self._on_canvas_click)
		self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
		self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
		self.canvas.bind("<Double-1>", self._on_canvas_doubleclick)

	# ---------------- shortcuts ----------------
	def _bind_shortcuts(self):
		self.root.bind("<Delete>", self._on_delete_key)
		self.root.bind("<Control-BackSpace>", self._on_delete_key)
		self.root.bind("<Control-c>", self._shortcut_copy)
		self.root.bind("<Control-v>", self._shortcut_paste)

	# ---------------- core functions ----------------
	def _update_selected_properties(self):
		if self.selected_box:
			self.selected_box.set_font(self.font_var.get(), self.size_var.get())
			self.selected_box.set_color(self.color_var.get())
			self.selected_box.set_align(self.align_var.get())

	def _on_delete_key(self, event=None):
		if self.selected_box:
			self.remove_selected()

	def _on_canvas_doubleclick(self, event):
		x = self.canvas.canvasx(event.x)
		y = self.canvas.canvasy(event.y)
		font = (self.font_var.get(), self.size_var.get())
		color = self.color_var.get()
		tb = CanvasTextBox(self.canvas, self, x, y, 250, 40, "", font, color, self.align_var.get())
		self.textboxes.append(tb)
		self._select_box(tb)
		tb._edit_text()

	def _on_canvas_click(self, event):
		x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
		self.last_mouse = (x, y)
		clicked_box = None
		for tb in reversed(self.textboxes):
			x1, y1, x2, y2 = tb.bbox()
			if x1 <= x <= x2 and y1 <= y <= y2:
				clicked_box = tb
				break
		self._select_box(clicked_box)
		if clicked_box:
			self.dragging = True

	def _on_canvas_drag(self, event):
		if not self.selected_box or not self.dragging:
			return
		x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
		dx, dy = x - self.last_mouse[0], y - self.last_mouse[1]
		self.selected_box.move(dx, dy)
		self.last_mouse = (x, y)

	def _on_canvas_release(self, event):
		self.dragging = False

	def _select_box(self, box):
		if self.selected_box and self.selected_box is not box:
			self.selected_box.set_selected(False)
		self.selected_box = box
		if box:
			box.set_selected(True)
			self.font_var.set(box.font_name)
			self.size_var.set(box.font_size)
			self.color_var.set(box.color)
			self.align_var.set(box.align)

	# ---------------- add/remove ----------------
	def remove_selected(self):
		if self.selected_box:
			self.selected_box.destroy()
			self.textboxes.remove(self.selected_box)
			self.selected_box = None

	# ---------------- clipboard ----------------
	def _shortcut_copy(self, event=None):
		if self.selected_box:
			s = self.selected_box.get_text()
			self.root.clipboard_clear()
			self.root.clipboard_append(s)
			self.clipboard_internal = s

	def _shortcut_paste(self, event=None):
		try:
			s = self.root.clipboard_get()
		except tk.TclError:
			s = self.clipboard_internal or ""
		if self.selected_box:
			self.selected_box.insert_text(s)

	# ---------------- alignment ----------------
	def align_set(self, mode):
		self.align_var.set(mode)
		if self.selected_box:
			self.selected_box.set_align(mode)

	# ---------------- PDF operations ----------------
	def open_pdf(self):
		path = filedialog.askopenfilename(filetypes=[("PDF files","*.pdf")])
		if path:
			self.pdf_path = path
			self._render_page()

	def _render_page(self):
		if not self.pdf_path:
			return
		img, rect, w, h = load_page_image(self.pdf_path, 0, zoom=self.scale)
		self.display_img = img
		self.tk_img = ImageTk.PhotoImage(img)
		self.canvas.delete("all")
		self.canvas.create_image(0,0, anchor="nw", image=self.tk_img)
		self.canvas.config(scrollregion=(0,0,img.width,img.height))
		for tb in self.textboxes:
			tb.render_on_canvas()

	def save_pdf(self):
		if not self.pdf_path:
			messagebox.showinfo("Errore", "Apri prima un PDF")
			return
		out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
		if not out:
			return
		texts = []
		for tb in self.textboxes:
			texts.append({
				"text": tb.get_text(),
				"font": tb.font_name,
				"size": tb.font_size,
				"color": tb.color,
				"x": tb.x,
				"y": tb.y,
				"align": tb.align,
				"box_width": tb.w
			})
		save_pdf_with_texts(self.pdf_path, out, texts)
		messagebox.showinfo("Salvato", f"PDF salvato in {out}")

	def remove_selected(self):
		if self.selected_box:
			self.selected_box.destroy()
			self.textboxes.remove(self.selected_box)
			self.selected_box = None

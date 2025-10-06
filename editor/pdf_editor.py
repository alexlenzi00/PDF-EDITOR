import os
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
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
		self.page_rect = None
		self.display_img = None
		self.display_img_width = 1
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
		# load system fonts
		self.system_fonts = sorted(set(tkfont.families()))
		# try to detect ttf in fonts/ folder and "register" them (best-effort)
		self.custom_fonts = []
		if os.path.isdir(FONTS_DIR):
			for f in os.listdir(FONTS_DIR):
				if f.lower().endswith(".ttf"):
					path = os.path.abspath(os.path.join(FONTS_DIR, f))
					name = os.path.splitext(f)[0]
					# Try to register with tk (works on many systems)
					try:
						self.root.tk.call('font', 'create', name, '-family', name)
						# note: this doesn't actually load the ttf automatically on all systems
						self.custom_fonts.append(name)
					except Exception:
						# fallback: add filename as option
						self.custom_fonts.append(name)
		# final font list for combobox
		self.font_list = self.custom_fonts + self.system_fonts

	# ---------------- UI ----------------
	def _build_ui(self):
		style = ttk.Style(self.root)
		style.theme_use("clam")

		toolbar = ttk.Frame(self.root, padding=4)
		toolbar.pack(side="top", fill="x")

		# buttons with nicer appearance
		self.open_btn = ttk.Button(toolbar, text="📂 Apri", command=self.open_pdf)
		self.open_btn.pack(side="left", padx=4)

		self.full_btn = ttk.Button(toolbar, text="⤢ Fullscreen", command=self.toggle_fullscreen)
		self.full_btn.pack(side="left", padx=4)

		self.save_btn = ttk.Button(toolbar, text="💾 Salva", command=self.save_pdf)
		self.save_btn.pack(side="left", padx=4)

		# separator
		ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

		# font selector (combo)
		self.font_var = tk.StringVar(value="Helvetica")
		self.font_combo = ttk.Combobox(toolbar, textvariable=self.font_var, values=self.font_list, width=25)
		self.font_combo.pack(side="left", padx=4)
		self.font_combo.set("Helvetica")
		self.font_combo.bind("<<ComboboxSelected>>", lambda e: self._update_selected_properties())

		# size
		self.size_var = tk.IntVar(value=12)
		self.size_combo = ttk.Combobox(toolbar, textvariable=self.size_var, values=[8,10,12,14,16,18,20,24,32], width=4)
		self.size_combo.pack(side="left", padx=4)
		self.size_combo.bind("<<ComboboxSelected>>", lambda e: self._update_selected_properties())

		# color swatches
		self.color_var = tk.StringVar(value=DEFAULT_COLORS[0])
		self.color_var.trace_add("write", lambda *args: self._update_selected_properties())
		color_frame = ttk.Frame(toolbar)
		color_frame.pack(side="left", padx=6)
		ttk.Label(color_frame, text="Colore:").pack(side="left", padx=(0,4))
		for c in DEFAULT_COLORS:
			b = tk.Button(color_frame, bg=c, width=2, command=lambda col=c: self.color_var.set(col))
			b.pack(side="left", padx=2)

		# align buttons
		self.align_var = tk.StringVar(value="left")
		ttk.Button(toolbar, text="⟸", command=lambda: self.align_set("left")).pack(side="left", padx=6)
		ttk.Button(toolbar, text="≡", command=lambda: self.align_set("center")).pack(side="left", padx=2)
		ttk.Button(toolbar, text="⟹", command=lambda: self.align_set("right")).pack(side="left", padx=2)

		# add text toggle
		self.add_mode = False

		# delete
		self.del_btn = ttk.Button(toolbar, text="🗑 Rimuovi", command=self.remove_selected)
		self.del_btn.pack(side="left", padx=4)

		# spacer then zoom controls on right
		ttk.Separator(toolbar, orient="vertical").pack(side="right", fill="y", padx=6)
		zoom_frame = ttk.Frame(toolbar)
		zoom_frame.pack(side="right", padx=6)
		self.zoom_label = ttk.Label(zoom_frame, text="100%")
		self.zoom_label.pack(side="right", padx=6)
		ttk.Button(zoom_frame, text="+", width=3, command=lambda: self.zoom_step(0.1)).pack(side="right")
		ttk.Button(zoom_frame, text="−", width=3, command=lambda: self.zoom_step(-0.1)).pack(side="right")

		# Canvas & scrollbars
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

		# bindings on the canvas
		self.canvas.bind("<Button-1>", self._on_canvas_click)
		self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
		self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
		# mousewheel for scrolling
		self.canvas.bind("<MouseWheel>", self._on_mousewheel)          # windows
		self.canvas.bind("<Button-4>", self._on_mousewheel)            # linux up
		self.canvas.bind("<Button-5>", self._on_mousewheel)            # linux down

		# ctrl+wheel zoom
		self.canvas.bind_all("<Control-MouseWheel>", self._on_ctrl_wheel)
		self.canvas.bind_all("<Control-Button-4>", self._on_ctrl_wheel)
		self.canvas.bind_all("<Control-Button-5>", self._on_ctrl_wheel)

		self.canvas.bind("<Double-1>", self._on_canvas_doubleclick)

	# ---------------- shortcuts and bindings ----------------
	def _bind_shortcuts(self):
		self.root.bind("<Delete>", self._on_delete_key)
		self.root.bind("<Control-BackSpace>", self._on_delete_key)
		self.root.bind("<Control-c>", self._shortcut_copy)
		self.root.bind("<Control-v>", self._shortcut_paste)

	def _on_canvas_doubleclick(self, event):
		x = self.canvas.canvasx(event.x)
		y = self.canvas.canvasy(event.y)
		font = (self.font_var.get(), int(self.size_var.get()))
		color = self.color_var.get()
		tb = CanvasTextBox(self.canvas, x, y, w=250, h=40,
						text="", font=font, color=color,
						align=self.align_var.get())
		self.textboxes.append(tb)
		self._select_box(tb)

	def _on_delete_key(self, event=None):
		widget = self.root.focus_get()
		if isinstance(widget, tk.Text):
			return  # lascia che Text gestisca
		if self.selected_box:
			self.remove_selected()

	def _shortcut_copy(self, event=None):
		widget = self.root.focus_get()
		if isinstance(widget, tk.Text):
			return  # lascia che Text gestisca
		if self.selected_box:
			s = self.selected_box.get_text()
			self.root.clipboard_clear()
			self.root.clipboard_append(s)
			self.clipboard_internal = s

	def _shortcut_paste(self, event=None):
		widget = self.root.focus_get()
		if isinstance(widget, tk.Text):
			return  # lascia che Text gestisca
		try:
			s = self.root.clipboard_get()
		except tk.TclError:
			s = self.clipboard_internal or ""
		if self.selected_box:
			self.selected_box.text_widget.insert("insert", s)

	def _update_selected_properties(self):
		if not self.selected_box:
			return
		self.selected_box.set_font(self.font_var.get(), int(self.size_var.get()))
		self.selected_box.set_color(self.color_var.get())
		self.selected_box.set_align(self.align_var.get())

	def _on_mousewheel(self, event):
		# normal scroll when ctrl not pressed
		if event.state & 0x0004:  # ctrl is pressed? (platform dependent)
			return
		if event.num == 4 or event.delta > 0:
			self.canvas.yview_scroll(-1, "units")
		else:
			self.canvas.yview_scroll(1, "units")

	def _on_ctrl_wheel(self, event):
		# Ctrl + wheel -> zoom
		if getattr(event, "delta", 0) > 0 or getattr(event, "num", None) in (4,):
			self.zoom_step(0.1)
		else:
			self.zoom_step(-0.1)

	def zoom_step(self, delta):
		new = max(0.1, self.scale + delta)
		if abs(new - self.scale) < 0.001:
			return
		self.scale = new
		self.zoom_label.config(text=f"{int(self.scale*100)}%")
		# rescale the canvas content: we re-render page at new zoom and rescale textboxes coords
		if self.pdf_path:
			old_w = self.display_img.width if self.display_img else 1
			img, rect, w, h = load_page_image(self.pdf_path, 0, zoom=self.scale, dpi_scale=2)
			self.display_img = img
			self.page_rect = rect
			new_w = img.width
			scale_xy = new_w / old_w
			# rescale stored textbox positions and sizes
			for tb in self.textboxes:
				tb.x *= scale_xy
				tb.y *= scale_xy
				tb.w *= scale_xy
				tb.h *= scale_xy
				# update window and border
			self._render_page()

	# ---------------- open / render / save ----------------
	def open_pdf(self):
		path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
		if not path:
			return
		self.pdf_path = path
		self._render_page()

	def _render_page(self):
		if not self.pdf_path:
			return
		img, rect, w, h = load_page_image(self.pdf_path, 0, zoom=self.scale, dpi_scale=2)
		self.display_img = img
		self.page_rect = rect
		self.display_img_width = img.width

		self.tk_img = ImageTk.PhotoImage(img)
		self.canvas.delete("all")

		canvas_w = self.canvas.winfo_width()
		canvas_h = self.canvas.winfo_height()
		img_w = img.width
		img_h = img.height

		offset_x = max((canvas_w - img_w)//2, 0)
		offset_y = max((canvas_h - img_h)//2, 0)

		self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self.tk_img)
		self.canvas.config(scrollregion=(0,0,max(canvas_w,img_w), max(canvas_h,img_h)))

		# ricrea textbox
		for tb in self.textboxes:
			tb.window_id = self.canvas.create_window(offset_x + tb.x, offset_y + tb.y,
													window=tb.frame, anchor="nw",
													width=tb.w, height=tb.h)
			tb.border_id = self.canvas.create_rectangle(offset_x + tb.x, offset_y + tb.y,
														offset_x + tb.x + tb.w, offset_y + tb.y + tb.h,
														outline="#4a90e2" if tb.selected else "", dash=(3,2))
			tb._create_handles()
			if not tb.selected:
				tb.set_selected(False)
			# bind click destro per cancellazione
			tb.frame.bind("<Button-3>", lambda e, box=tb: self.remove_box(box))

	def save_pdf(self):
		if not self.pdf_path:
			messagebox.showinfo("Errore", "Apri prima un PDF.")
			return
		out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
		if not out:
			return
		# prepare texts list mapped to display coords and size
		texts = []
		for tb in self.textboxes:
			texts.append({
				"text": tb.get_text(),
				"font": tb.font_family,
				"size": tb.font_size,
				"color": tb.color,
				"x": tb.x,
				"y": tb.y,
				"align": tb.align,
				"box_width": tb.w
			})
		save_pdf_with_texts(self.pdf_path, out, texts, page_number=0, display_img_width=self.display_img_width, page_rect=self.page_rect)
		messagebox.showinfo("Salvato", f"PDF salvato in:\n{out}")

	def toggle_fullscreen(self):
		is_full = self.root.attributes("-fullscreen")
		self.root.attributes("-fullscreen", not is_full)

	# ---------------- add/select/move/resize logic ----------------
	def toggle_add_mode(self):
		self.add_mode = not self.add_mode
		if self.add_mode:
			self.add_btn.state(["pressed"])
		else:
			try:
				self.add_btn.state(["!pressed"])
			except Exception:
				pass

	def _on_canvas_click(self, event):
		x = self.canvas.canvasx(event.x)
		y = self.canvas.canvasy(event.y)
		self.last_mouse = (x, y)

		if self.add_mode:
			font = (self.font_var.get(), int(self.size_var.get()))
			color = self.color_var.get()
			text = "Nuovo testo"
			tb = CanvasTextBox(self.canvas, x, y, w=250, h=40,
							text=text, font=font, color=color, align=self.align_var.get())
			self.textboxes.append(tb)
			self._select_box(tb)
			self.add_mode = False
			return

		widget = event.widget
		if isinstance(widget, tk.Text):
			return  # lascia che Text gestisca drag/tasti

		for tb in reversed(self.textboxes):
			for key, hid in tb.handles.items():
				coords = self.canvas.coords(hid)
				if coords and coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
					self._select_box(tb)
					self.resizing = True
					self.resize_handle = key
					return

			x1, y1, x2, y2 = tb.bbox()
			if x1 <= x <= x2 and y1 <= y <= y2:
				self._select_box(tb)
				self.dragging = True
				self.last_mouse = (x, y)
				return

		self._select_box(None)

	def _on_canvas_drag(self, event):
		if not self.selected_box or (not self.dragging and not self.resizing):
			return

		x = self.canvas.canvasx(event.x)
		y = self.canvas.canvasy(event.y)
		dx = x - self.last_mouse[0]
		dy = y - self.last_mouse[1]
		self.last_mouse = (x, y)

		if self.dragging:
			self.selected_box.move(dx, dy)
		elif self.resizing:
			tb = self.selected_box
			if self.resize_handle == 'se':
				tb.resize(tb.w + dx, tb.h + dy)
			elif self.resize_handle == 'ne':
				tb.y += dy
				self.canvas.move(tb.window_id, 0, dy)
				self.canvas.move(tb.border_id, 0, dy)
				for h in tb.handles.values():
					self.canvas.move(h, 0, dy)
				tb.resize(tb.w + dx, tb.h - dy)
			elif self.resize_handle == 'sw':
				tb.x += dx
				self.canvas.move(tb.window_id, dx, 0)
				self.canvas.move(tb.border_id, dx, 0)
				for h in tb.handles.values():
					self.canvas.move(h, dx, 0)
				tb.resize(tb.w - dx, tb.h + dy)
			elif self.resize_handle == 'nw':
				tb.x += dx
				tb.y += dy
				self.canvas.move(tb.window_id, dx, dy)
				self.canvas.move(tb.border_id, dx, dy)
				for h in tb.handles.values():
					self.canvas.move(h, dx, dy)
				tb.resize(tb.w - dx, tb.h - dy)


	def _on_canvas_release(self, event):
		self.dragging = False
		self.resizing = False
		self.resize_handle = None

	def _select_box(self, box):
		if self.selected_box and self.selected_box is not box:
			self.selected_box.set_selected(False)
		self.selected_box = box
		if box:
			box.set_selected(True)
			# aggiorna toolbar proprietà
			self.font_var.set(box.font_family if box.font_family else "Helvetica")
			self.size_var.set(box.font_size if box.font_size else 12)
			self.color_var.set(box.color if box.color else DEFAULT_COLORS[0])
			self.align_var.set(box.align if box.align else "left")
			# assicurati che sia visibile
			self.canvas.see(box.window_id)
		else:
			pass

	def remove_box(self, box):
		if box in self.textboxes:
			box.destroy()
			self.textboxes.remove(box)
			if self.selected_box is box:
				self.selected_box = None

	# ---------------- copy/paste/remove ----------------
	def _shortcut_copy(self, event=None):
		if self.selected_box:
			try:
				s = self.selected_box.get_text()
				self.root.clipboard_clear()
				self.root.clipboard_append(s)
				self.clipboard_internal = s
			except Exception:
				pass

	def _shortcut_paste(self, event=None):
		try:
			s = self.root.clipboard_get()
		except tk.TclError:
			s = self.clipboard_internal or ""
		if self.selected_box:
			# paste into that textbox at insert
			self.selected_box.text_widget.insert("insert", s)

	def remove_selected(self):
		if not self.selected_box:
			messagebox.showinfo("Rimuovi", "Seleziona prima una casella.")
			return
		self.selected_box.destroy()
		self.textboxes = [t for t in self.textboxes if t is not self.selected_box]
		self.selected_box = None

	# ---------------- alignment and properties ----------------
	def align_set(self, mode):
		self.align_var.set(mode)
		if self.selected_box:
			self.selected_box.set_align(mode)

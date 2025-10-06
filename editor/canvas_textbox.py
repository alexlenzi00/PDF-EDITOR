import tkinter as tk

class CanvasTextBox:
	HANDLE_SIZE = 6

	def __init__(self, canvas, editor, x, y, w=200, h=40, text="", font=None, color="black", align="left"):
		self.canvas = canvas
		self.editor = editor
		self.x, self.y = x, y
		self.w, self.h = w, h
		self.text = text
		if isinstance(font, (tuple, list)) and len(font) == 2:
			self.font_family, self.font_size = font
		else:
			self.font_family = font or "Helvetica"
			self.font_size = 14

		self.color = color
		self.align = align

		# Cornice invisibile (necessaria per gestire il window del canvas)
		self.frame = tk.Frame(canvas, bd=0, highlightthickness=0, bg="")
		# Text trasparente (usa lo stesso colore del canvas)
		self.text_widget = tk.Text(
			self.frame,
			wrap="word",
			width=1,
			height=1,
			bd=0,
			padx=2,
			pady=2,
			highlightthickness=0,
			relief="flat",
			fg=self.color,
			bg=canvas["bg"],  # effetto trasparente reale
			font=(self.font_family, self.font_size)
		)
		self.text_widget.insert("1.0", text)
		self.text_widget.pack(expand=True, fill="both")

		# Eventi per drag e click
		self.text_widget.bind("<Button-1>", self._on_text_click)
		self.text_widget.bind("<B1-Motion>", self._on_drag)
		self.text_widget.bind("<ButtonRelease-1>", self._on_release)

		# Creazione finestra canvas
		self.window_id = canvas.create_window(x, y, window=self.frame, anchor="nw", width=w, height=h)

		self.is_selected = False
		self.dragging = False
		self.start_x = 0
		self.start_y = 0
		self.handles = {}

	# --- Selezione ---
	def set_selected(self, selected):
		self.is_selected = selected
		if selected:
			self._draw_handles()
		else:
			self._remove_handles()

	def _draw_handles(self):
		self._remove_handles()
		x1, y1, x2, y2 = self._get_bbox()
		for cx, cy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
			h = self.canvas.create_oval(
				cx - self.HANDLE_SIZE / 2, cy - self.HANDLE_SIZE / 2,
				cx + self.HANDLE_SIZE / 2, cy + self.HANDLE_SIZE / 2,
				fill="#3b82f6", outline="#3b82f6"
			)
			self.handles[h] = (cx, cy)

	def _remove_handles(self):
		for h in list(self.handles.keys()):
			self.canvas.delete(h)
		self.handles.clear()

	# --- Drag & Drop ---
	def _on_text_click(self, event):
		self.dragging = True
		self.start_x = event.x
		self.start_y = event.y
		self.editor._select_box(self)

	def _on_drag(self, event):
		if self.dragging:
			dx = event.x - self.start_x
			dy = event.y - self.start_y
			self.canvas.move(self.window_id, dx, dy)
			for h in self.handles:
				self.canvas.move(h, dx, dy)

	def _on_release(self, event):
		self.dragging = False

	# --- Bounding box ---
	def _get_bbox(self):
		bbox = self.canvas.bbox(self.window_id)
		return bbox if bbox else (0, 0, 0, 0)

	def bbox(self):
		return self._get_bbox()

	# --- Proprietà ---
	def set_font(self, family, size):
		self.font_family = family
		self.font_size = size
		self.text_widget.config(font=(family, size))

	def set_color(self, color):
		self.color = color
		self.text_widget.config(fg=color)

	def set_align(self, align):
		justify = {"left": "left", "center": "center", "right": "right"}.get(align, "left")
		self.text_widget.tag_configure("align", justify=justify)
		self.text_widget.tag_add("align", "1.0", "end")

	def get_text(self):
		return self.text_widget.get("1.0", "end-1c")

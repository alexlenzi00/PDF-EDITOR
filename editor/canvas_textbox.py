import tkinter as tk

class CanvasTextBox:
	def __init__(self, canvas, editor, x, y, w=250, h=40, text='', font=("Arial", 12), color='black', align='left'):
		self.canvas = canvas
		self.editor = editor
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.text = text
		self.font_name, self.font_size = font
		self.align = align
		self.selected = False
		self.entry = None
		self.text_widget = None
		self.color = color
		self.handles = {}

		# Determina l'anchor in base all'allineamento
		anchor_map = {'left': 'nw', 'center': 'n', 'right': 'ne'}
		self.anchor = anchor_map.get(self.align, 'nw')

		# Crea l'oggetto testo sul canvas
		self.text_id = canvas.create_text(x, y, text=self.text, font=(self.font_name, self.font_size), fill=self.color, width=self.w, anchor=self.anchor)

		# Collega il doppio click per modificare il testo
		canvas.tag_bind(self.text_id, '<Double-1>', self._edit_text)

	# --- Editing del testo ---
	def _edit_text(self, event=None):
		if self.entry:
			self.entry.destroy()

		x1, y1, x2, y2 = self.canvas.bbox(self.text_id)
		self.entry = tk.Entry(self.canvas, font=(self.font_name, self.font_size), bd=0, bg=self.canvas['bg'])
		self.entry.insert(0, self.text)
		self.entry.place(x=x1, y=y1, width=self.w, height=self.h)
		self.entry.focus()
		self.entry.bind("<Return>", self._save_edit)
		self.entry.bind("<Escape>", self._cancel_edit)
		self.entry.bind("<FocusOut>", self._save_edit)
		self.text_widget = self.entry  # compatibilità

	def _save_edit(self, event=None):
		if self.entry:
			self.text = self.entry.get()
			self.update_canvas_text()
			self.entry.destroy()
			self.entry = None
			self.text_widget = None

	def _cancel_edit(self, event=None):
		if self.entry:
			self.entry.destroy()
			self.entry = None
			self.text_widget = None

	# --- Font ---
	def set_font(self, font_name, size):
		self.font_name = font_name
		self.font_size = size
		self.update_canvas_text()
		if self.entry:
			self.entry.config(font=(self.font_name, self.font_size))

	# --- Altri metodi ---
	def move(self, dx, dy):
		self.x += dx
		self.y += dy
		self.canvas.move(self.text_id, dx, dy)

	def delete(self):
		self.destroy()

	def get_text(self):
		return self.text

	def set_selected(self, value=True):
		self.selected = value
		if hasattr(self, 'rect_id'):
			self.canvas.delete(self.rect_id)
		if value:
			x1, y1, x2, y2 = self.canvas.bbox(self.text_id)
			self.rect_id = self.canvas.create_rectangle(x1-2, y1-2, x2+2, y2+2, outline='blue')

	def is_selected(self):
		return self.selected

	def bbox(self):
		coords = self.canvas.bbox(self.text_id)
		if coords:
			return coords
		return (self.x, self.y, self.x + self.w, self.y + self.h)
	
	def set_color(self, color):
		self.color = color
		self.update_canvas_text()
		if self.entry:
			self.entry.config(fg=self.color)
	
	def set_align(self, align):
		self.align = align
		anchor_map = {'left': 'nw', 'center': 'n', 'right': 'ne'}
		self.anchor = anchor_map.get(self.align, 'nw')
		self.update_canvas_text()
		if self.entry:
			self.entry.config(justify=self.align)

	def bbox(self):
		"""
		Restituisce le coordinate del bounding box del testo sul canvas.
		Compatibile con _on_canvas_click.
		"""
		coords = self.canvas.bbox(self.text_id)
		if coords:
			return coords  # x1, y1, x2, y2
		return (self.x, self.y, self.x + self.w, self.y + self.h)

	def destroy(self):
		# cancella gli elementi dal canvas
		if hasattr(self, "rect_id"):
			self.canvas.delete(self.rect_id)
		if hasattr(self, "text_id"):
			self.canvas.delete(self.text_id)
		if self.entry:
			self.entry.destroy()
			self.entry = None

	def insert_text(self, text):
		# aggiunge testo alla textbox
		self.text += text
		self.update_canvas_text()

	def update_canvas_text(self):
		if hasattr(self, "text_id") and self.text_id:
			self.canvas.itemconfig(self.text_id, text=self.text, font=(self.font_name, self.font_size), fill=self.color, anchor=self.anchor)

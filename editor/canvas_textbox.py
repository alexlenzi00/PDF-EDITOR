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
		self.font = font
		self.color = color
		self.align = align

		# Determina l'anchor in base all'allineamento
		anchor_map = {'left': 'nw', 'center': 'n', 'right': 'ne'}
		self.anchor = anchor_map.get(self.align, 'nw')

		# Crea l'oggetto testo sul canvas
		self.text_id = canvas.create_text(x, y, text=self.text, font=self.font,
										fill=self.color, width=self.w, anchor=self.anchor)

		# Collega il doppio click per modificare il testo
		canvas.tag_bind(self.text_id, '<Double-1>', self._edit_text)

	def _edit_text(self, event):
		# Posiziona un Entry temporaneo sopra il canvas
		x1, y1 = self.canvas.coords(self.text_id)
		self.entry = tk.Entry(self.canvas, font=self.font, bd=0, bg=self.canvas['bg'], fg=self.fill)
		self.entry.insert(0, self.text)
		self.entry.place(x=x1, y=y1, width=self.w, height=self.h)
		self.entry.focus()
		self.entry.bind("<Return>", self._save_edit)
		self.entry.bind("<Escape>", self._cancel_edit)

	def _save_edit(self, event=None):
		self.text = self.entry.get()
		self.canvas.itemconfig(self.text_id, text=self.text)
		self.entry.destroy()
		del self.entry

	def _cancel_edit(self, event=None):
		self.entry.destroy()
		del self.entry

	def move(self, dx, dy):
		self.x += dx
		self.y += dy
		self.canvas.move(self.text_id, dx, dy)

	def delete(self):
		self.canvas.delete(self.text_id)

	def get_text(self):
		return self.text

	def set_selected(self, value=True):
		self.selected = value
		# evidenzia se selezionato
		outline_color = 'blue' if value else ''
		# rimuove eventuali rettangoli esistenti
		if hasattr(self, 'rect_id'):
			self.canvas.delete(self.rect_id)
		if value:
			x1, y1, x2, y2 = self._get_bbox()
			self.rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline=outline_color)

	def is_selected(self):
		return self.selected

	def _get_bbox(self):
		bbox = self.canvas.bbox(self.text_id)
		if bbox:
			return bbox
		return (self.x, self.y, self.x + self.w, self.y + self.h)
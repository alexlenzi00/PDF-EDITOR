

class CanvasTextBox:
	"""
	Rappresenta una 'casella di testo' sul canvas. Implementata come:
	- una rect (border) + corner handles per resize
	- un widget Text (tk.Text) embedded tramite canvas.create_window per testo editabile
	Gestisce selezione, spostamento e ridimensionamento.
	"""
	HANDLE_SIZE = 8

	def __init__(self, canvas, x, y, w=200, h=30, text="Nuovo testo", font=("Helvetica", 12), color="#000000", align="left"):
		self.canvas = canvas
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.text = text
		self.font_family = font[0]
		self.font_size = font[1]
		self.color = color
		self.align = align

		# create frame for text to allow background and padding
		self.frame = tk.Frame(canvas, bd=0, highlightthickness=0)
		# Text widget
		self.text_widget = tk.Text(self.frame, wrap="word", width=1, height=1, bd=0, padx=2, pady=2)
		self.text_widget.insert("1.0", text)
		self.text_widget.configure(font=(self.font_family, self.font_size), fg=self.color)
		# disable widget border; we'll show border via canvas
		self.text_widget.pack(expand=True, fill="both")
		# create canvas window
		self.window_id = canvas.create_window(self.x, self.y, window=self.frame, anchor="nw", width=self.w, height=self.h)
		# border rectangle and handles
		self.border_id = canvas.create_rectangle(self.x, self.y, self.x+self.w, self.y+self.h, outline="", dash=(3,2))
		self.handles = {}
		self._create_handles()
		self.selected = False

		# bindings on the inner Text for keyboard events
		self.text_widget.bind("<Control-c>", self._on_copy)
		self.text_widget.bind("<Control-C>", self._on_copy)
		self.text_widget.bind("<Control-v>", self._on_paste)
		self.text_widget.bind("<Control-V>", self._on_paste)

		self.frame.bind("<Button-3>", lambda e: self.canvas_editor.remove_box(self))

	def _create_handles(self):
		# corners: tl, tr, bl, br
		coords = self._coords()
		x1, y1, x2, y2 = coords
		s = self.HANDLE_SIZE
		self.handles['nw'] = self.canvas.create_rectangle(x1-s, y1-s, x1+s, y1+s, fill="white", outline="", tags="handle")
		self.handles['ne'] = self.canvas.create_rectangle(x2-s, y1-s, x2+s, y1+s, fill="white", outline="", tags="handle")
		self.handles['sw'] = self.canvas.create_rectangle(x1-s, y2-s, x1+s, y2+s, fill="white", outline="", tags="handle")
		self.handles['se'] = self.canvas.create_rectangle(x2-s, y2-s, x2+s, y2+s, fill="white", outline="", tags="handle")
		# initially hidden
		for h in self.handles.values():
			self.canvas.itemconfigure(h, state="hidden")
		self.canvas.itemconfigure(self.border_id, state="hidden")

	def _coords(self):
		return (self.x, self.y, self.x + self.w, self.y + self.h)

	def set_selected(self, sel=True):
		self.selected = sel
		if sel:
			self.canvas.itemconfigure(self.border_id, outline="#4a90e2", width=2, state="normal")
			for h in self.handles.values():
				self.canvas.itemconfigure(h, state="normal", outline="#4a90e2")
		else:
			self.canvas.itemconfigure(self.border_id, state="hidden")
			for h in self.handles.values():
				self.canvas.itemconfigure(h, state="hidden")

	def move(self, dx, dy):
		self.x += dx
		self.y += dy
		self.canvas.move(self.window_id, dx, dy)
		self.canvas.move(self.border_id, dx, dy)
		for h in self.handles.values():
			self.canvas.move(h, dx, dy)

	def resize(self, new_w, new_h):
		min_w, min_h = 30, 20
		self.w = max(min_w, int(new_w))
		self.h = max(min_h, int(new_h))
		# update window size and border/handles positions
		self.canvas.itemconfigure(self.window_id, width=self.w, height=self.h)
		x1, y1, x2, y2 = self._coords()
		self.canvas.coords(self.border_id, x1, y1, x2, y2)
		s = self.HANDLE_SIZE
		self.canvas.coords(self.handles['nw'], x1-s, y1-s, x1+s, y1+s)
		self.canvas.coords(self.handles['ne'], x2-s, y1-s, x2+s, y1+s)
		self.canvas.coords(self.handles['sw'], x1-s, y2-s, x1+s, y2+s)
		self.canvas.coords(self.handles['se'], x2-s, y2-s, x2+s, y2+s)

	def bbox(self):
		return self._coords()

	def get_text(self):
		return self.text_widget.get("1.0", "end-1c")

	def set_text(self, s):
		self.text_widget.delete("1.0", "end")
		self.text_widget.insert("1.0", s)

	def set_font(self, family, size):
		self.font_family = family
		self.font_size = size
		self.text_widget.configure(font=(self.font_family, self.font_size))

	def set_color(self, hexcolor):
		self.color = hexcolor
		self.text_widget.configure(fg=self.color)

	def set_align(self, align):
		self.align = align
		# Text widget alignment: use tag
		self.text_widget.tag_configure("a", justify=({"left":"left","center":"center","right":"right"}.get(align,"left")))
		self.text_widget.tag_add("a", "1.0", "end")

	def destroy(self):
		self.canvas.delete(self.window_id)
		self.canvas.delete(self.border_id)
		for h in self.handles.values():
			self.canvas.delete(h)
		self.frame.destroy()

	# copy/paste helpers
	def _on_copy(self, event=None):
		try:
			sel = self.text_widget.get("sel.first", "sel.last")
			self.text_widget.clipboard_clear()
			self.text_widget.clipboard_append(sel)
		except tk.TclError:
			pass
		return "break"

	def _on_paste(self, event=None):
		try:
			s = self.text_widget.clipboard_get()
			self.text_widget.insert("insert", s)
		except tk.TclError:
			pass
		return "break"


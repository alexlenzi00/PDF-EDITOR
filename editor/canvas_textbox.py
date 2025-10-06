import tkinter as tk

class CanvasTextBox:
	HANDLE_SIZE = 8

	def __init__(self, canvas, x, y, w=200, h=30, text="Nuovo testo",
				font=("Helvetica",12), color="#000000", align="left"):
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

		# frame e Text
		self.frame = tk.Frame(canvas)
		self.text_widget = tk.Text(self.frame, wrap="word", bd=0, padx=2, pady=2)
		self.text_widget.insert("1.0", text)
		self.text_widget.configure(font=(self.font_family, self.font_size), fg=self.color)
		self.text_widget.pack(expand=True, fill="both")
		self.text_widget.bind("<FocusOut>", lambda e: self.canvas.focus_set())
		self.text_widget.bind("<Button-1>", self._focus_click)

		# canvas window e border
		self.window_id = canvas.create_window(self.x, self.y, window=self.frame, anchor="nw", width=self.w, height=self.h)
		self.border_id = canvas.create_rectangle(self.x, self.y, self.x+self.w, self.y+self.h, outline="#4a90e2", dash=(3,2))

		# bind drag direttamente sul frame
		self.frame.bind("<Button-1>", self._on_frame_click)
		self.frame.bind("<B1-Motion>", self._on_frame_drag)
		self.frame.bind("<ButtonRelease-1>", self._on_frame_release)

		self._drag_start = None

	def _on_frame_click(self, event):
		# Seleziona questa casella
		self.canvas.master._select_box(self)
		self.canvas.master.dragging = True
		self.canvas.master.last_mouse = (event.x_root - self.canvas.winfo_rootx(),
										event.y_root - self.canvas.winfo_rooty())

	def _on_frame_drag(self, event):
		master = self.canvas.master
		if master.dragging and master.selected_box == self:
			x, y = event.x_root - self.canvas.winfo_rootx(), event.y_root - self.canvas.winfo_rooty()
			dx = x - master.last_mouse[0]
			dy = y - master.last_mouse[1]
			master.last_mouse = (x, y)
			self.move(dx, dy)

	def _on_frame_release(self, event):
		master = self.canvas.master
		master.dragging = False

	# --- metodi drag ---
	def _start_drag(self, event):
		self._drag_start = (event.x, event.y)

	def _drag(self, event):
		dx = event.x - self._drag_start[0]
		dy = event.y - self._drag_start[1]
		self.move(dx, dy)

	def _end_drag(self, event):
		self._drag_start = None

	# --- metodi di utilità ---
	def _focus_click(self, event):
		# Quando si clicca nel Text, seleziona la casella
		self.canvas.master._select_box(self)  # chiama il metodo del PDFEditor
		# permetti che il Text gestisca anche il click
		return None


	def move(self, dx, dy):
		self.x += dx
		self.y += dy
		self.canvas.move(self.window_id, dx, dy)
		self.canvas.move(self.border_id, dx, dy)

	def resize(self, new_w, new_h):
		self.w = max(30, new_w)
		self.h = max(20, new_h)
		self.canvas.itemconfigure(self.window_id, width=self.w, height=self.h)
		self.canvas.coords(self.border_id, self.x, self.y, self.x+self.w, self.y+self.h)

	def set_text(self, text):
		self.text_widget.delete("1.0","end")
		self.text_widget.insert("1.0", text)

	def get_text(self):
		return self.text_widget.get("1.0","end-1c")

	def set_font(self, family, size):
		self.font_family = family
		self.font_size = size
		self.text_widget.configure(font=(self.font_family, self.font_size))

	def set_color(self, color):
		self.color = color
		self.text_widget.configure(fg=self.color)

	def set_align(self, align):
		self.align = align
		self.text_widget.tag_configure("align", justify=align)
		self.text_widget.tag_add("align","1.0","end")

	def destroy(self):
		self.canvas.delete(self.window_id)
		self.canvas.delete(self.border_id)
		self.frame.destroy()

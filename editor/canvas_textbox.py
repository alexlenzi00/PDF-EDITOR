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

		# canvas window e border
		self.window_id = canvas.create_window(self.x, self.y, window=self.frame, anchor="nw", width=self.w, height=self.h)
		self.border_id = canvas.create_rectangle(self.x, self.y, self.x+self.w, self.y+self.h, outline="#4a90e2", dash=(3,2))

		# bind drag direttamente sul frame
		self.frame.bind("<Button-1>", self._start_drag)
		self.frame.bind("<B1-Motion>", self._drag)
		self.frame.bind("<ButtonRelease-1>", self._end_drag)

		self._drag_start = None

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

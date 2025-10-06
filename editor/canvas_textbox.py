import tkinter as tk

class CanvasTextBox:
    def __init__(self, canvas, x, y, w=200, h=40, text="", font=("Arial", 12),
                 color="#000000", align="left"):
        self.canvas = canvas
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.text = text
        self.font = font
        self.font_family = font[0]
        self.font_size = font[1]
        self.color = color
        self.align = align
        self.selected = False
        self.dragging = False
        self.start_x = None
        self.start_y = None

        # Crea il frame e la casella di testo
        self.frame = tk.Frame(canvas, bd=0, highlightthickness=0, bg="white")
        self.text_widget = tk.Text(
            self.frame,
            wrap="word",
            font=self.font,
            fg=self.color,
            padx=4, pady=2,
            height=1, width=1,
            relief="flat",
            undo=True
        )
        self.text_widget.insert("1.0", self.text)
        self.text_widget.pack(expand=True, fill="both")

        # Aggiungi frame al canvas
        self.window_id = self.canvas.create_window(
            x, y, window=self.frame, anchor="nw", width=w, height=h
        )

        # Bordo per evidenziare la selezione
        self.border_id = self.canvas.create_rectangle(
            x, y, x + w, y + h, outline="", width=2
        )

        # Dizionario per eventuali handle di resize
        self.handles = {}

        # Binding
        self.frame.bind("<Button-1>", self._on_frame_click)
        self.frame.bind("<B1-Motion>", self._on_frame_drag)
        self.frame.bind("<ButtonRelease-1>", self._on_frame_release)
        self.text_widget.bind("<Button-1>", self._on_text_click)
        self.text_widget.bind("<FocusOut>", self._on_focus_out)

    # ---- Gestione selezione ----
    def set_selected(self, sel=True):
        self.selected = sel
        if sel:
            self.canvas.itemconfigure(self.border_id, outline="#4a90e2", width=2)
        else:
            self.canvas.itemconfigure(self.border_id, outline="")

    # ---- Gestione movimento ----
    def _on_frame_click(self, event):
        master = self.canvas.master
        master._select_box(self)
        self.dragging = True
        self.start_x = event.x_root
        self.start_y = event.y_root

    def _on_frame_drag(self, event):
        if not self.dragging:
            return
        dx = event.x_root - self.start_x
        dy = event.y_root - self.start_y
        self.move(dx, dy)
        self.start_x = event.x_root
        self.start_y = event.y_root

    def _on_frame_release(self, event):
        self.dragging = False

    # ---- Gestione focus ----
    def _on_text_click(self, event):
        self.canvas.master._select_box(self)
        self.text_widget.focus_set()

    def _on_focus_out(self, event):
        # Quando clicchi fuori, rimuove il focus
        self.canvas.focus_set()

    # ---- Utility ----
    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.canvas.move(self.window_id, dx, dy)
        self.canvas.move(self.border_id, dx, dy)

    def get_text(self):
        return self.text_widget.get("1.0", "end-1c")

    def update_style(self, font=None, color=None):
        if font:
            self.font = font
            self.font_family = font[0]
            self.font_size = font[1]
            self.text_widget.configure(font=font)
        if color:
            self.color = color
            self.text_widget.configure(fg=color)

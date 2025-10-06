import tkinter as tk
from editor.pdf_editor import PDFEditor

def main():
	root = tk.Tk()
	root.title("PDF Editor - avanzato")
	try:
		root.state("zoomed")
	except Exception:
		root.attributes("-zoomed", True)

	editor = PDFEditor(root)
	root.mainloop()

if __name__ == "__main__":
	main()

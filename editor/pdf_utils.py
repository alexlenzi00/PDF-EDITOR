import fitz
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os

def load_page_image(pdf_path, page_number=0, zoom=1.0, dpi_scale=2):
	"""
	Ritorna (PIL.Image img, page_rect_pts, img_width, img_height)
	zoom = 1.0 corrisponde a 100%
	dpi_scale aumenta qualità raster
	"""
	doc = fitz.open(pdf_path)
	page = doc.load_page(page_number)
	m = fitz.Matrix(zoom * dpi_scale, zoom * dpi_scale)
	pix = page.get_pixmap(matrix=m, alpha=False)
	img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
	rect = page.rect
	doc.close()
	return img, rect, pix.width, pix.height

def carica_font_ttf(font_name):
	"""
	Registra un font TrueType per ReportLab.
	font_name: nome del font senza estensione (es. "Arial")
	Cerca il file TTF nella cartella "fonts" o nella cartella corrente.
	"""
	standard_fonts = ["Helvetica", "Times New Roman", "Courier"]
	if font_name in standard_fonts:
		return font_name
	# Cerca il file TTF nella cartella fonts o nella cartella corrente
	ttf_path = os.path.join("fonts", font_name + ".ttf")
	if not os.path.isfile(ttf_path):
		ttf_path = font_name + ".ttf"
	if os.path.isfile(ttf_path):
		try:
			if font_name not in pdfmetrics.getRegisteredFontNames():
				pdfmetrics.registerFont(TTFont(font_name, ttf_path))
				return font_name
		except Exception:
			return "Helvetica"
	else:
		return "Helvetica"

def hex_to_rgb(hex_color):
	hex_color = hex_color.lstrip('#')
	return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

def save_pdf_with_texts(pdf_path, out_path, texts, display_img_width, display_img_height):
	"""
	texts: list di dict con keys: text,font,size,color,x,y,align
	display_img_width: larghezza (px) dell'immagine visualizzata in editor, usata per mapping coords -> PDF points
	page_rect: fitz.Rect della pagina sorgente (punti PDF)
	"""
	reader = PdfReader(pdf_path)
	writer = PdfWriter()

	# Font standard supportati da ReportLab
	standard_fonts = ["Helvetica", "Times-Roman", "Courier"]

	for page_num, page in enumerate(reader.pages):
		packet = io.BytesIO()
		pdf_width = float(page.mediabox.width)
		pdf_height = float(page.mediabox.height)
		scale_x = pdf_width / display_img_width
		scale_y = pdf_height / display_img_height

		can = canvas.Canvas(packet, pagesize=(pdf_width, pdf_height))

		for t in texts:
			x = t['x'] * scale_x
			scale_font = (scale_x + scale_y) / 2 + 0.1
			font_size = t['size'] * scale_font
			y = pdf_height - (t['y'] * scale_y) - font_size
			font_name = carica_font_ttf(t.get("font", "Helvetica"))

			color = t.get("color", "#000000")
			r, g, b = hex_to_rgb(color)
			can.setFillColorRGB(r, g, b)
			can.setFont(font_name, font_size)
			can.drawString(x, y, t['text'])

		can.save()
		packet.seek(0)
		overlay_pdf = PdfReader(packet)
		page.merge_page(overlay_pdf.pages[0])
		writer.add_page(page)

	with open(out_path, "wb") as f:
		writer.write(f)

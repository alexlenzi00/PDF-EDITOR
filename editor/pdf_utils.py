import fitz
from PIL import Image

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

def save_pdf_with_texts(base_pdf_path, output_path, texts, page_number=0, display_img_width=1, page_rect=None):
	"""
	texts: list di dict con keys: text,font,size,color,x,y,align
	display_img_width: larghezza (px) dell'immagine visualizzata in editor, usata per mapping coords -> PDF points
	page_rect: fitz.Rect della pagina sorgente (punti PDF)
	"""
	if page_rect is None:
		# apri e usa prima pagina come fallback
		doc_tmp = fitz.open(base_pdf_path)
		page_rect = doc_tmp[0].rect
		doc_tmp.close()

	doc_src = fitz.open(base_pdf_path)
	new_doc = fitz.open()
	new_page = new_doc.new_page(width=page_rect.width, height=page_rect.height)
	new_page.show_pdf_page(page_rect, doc_src, page_number)

	# fattore punti-per-pixel
	factor = page_rect.width / float(display_img_width) if display_img_width else 1.0

	for t in texts:
		px = t["x"] * factor
		py = t["y"] * factor
		# convert hex color to tuple
		c = t.get("color", "#000000").lstrip("#")
		r, g, b = tuple(int(c[i:i+2], 16)/255.0 for i in (0,2,4))
		# scala size: display-size * factor
		pdf_size = max(1.0, t.get("size", 12) * factor)
		fontname = t.get("font", "helv")
		align = t.get("align", "left")
		# fitz text alignment via insert_textbox if needed
		try:
			# create a small bbox for single-line insert with alignment
			# width in points: approximate using factor * some width (we approximate with 200pt)
			width_pts = (t.get("box_width", 200) * factor) if t.get("box_width") else 200 * factor
			rect = fitz.Rect(px, py, px + width_pts, py + pdf_size*1.5)
			new_page.insert_textbox(rect, t["text"], fontsize=pdf_size, fontname=fontname, color=(r,g,b),
									align=({"left":0, "center":1, "right":2}.get(align, 0)))
		except Exception:
			# fallback insert_text
			try:
				new_page.insert_text((px, py), t["text"], fontsize=pdf_size, fontname=fontname, color=(r,g,b))
			except Exception:
				new_page.insert_text((px, py), t["text"], fontsize=pdf_size, color=(r,g,b))

	new_doc.save(output_path)
	new_doc.close()
	doc_src.close()

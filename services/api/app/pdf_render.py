import io
import pypdfium2 as pdfium


def validate_receipt(raw: bytes):
    with pdfium.PdfDocument(raw) as document:
        if not 1 <= len(document) <= 30:
            raise ValueError("Receipt must contain 1–30 readable pages")


def render_receipt(raw: bytes):
    with pdfium.PdfDocument(raw) as document:
        if not 1 <= len(document) <= 30:
            raise ValueError("Receipt must contain 1–30 readable pages")
        for index in range(len(document)):
            page = document[index]
            width, height = page.get_size()
            bitmap = page.render(scale=min(1.4, 1800 / max(width, height, 1)))
            image = bitmap.to_pil().convert("RGB")
            output = io.BytesIO()
            image.save(output, "JPEG", quality=88)
            yield index, output.getvalue(), image.width, image.height
            bitmap.close()
            page.close()

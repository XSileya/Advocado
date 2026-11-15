from pypdf import PdfReader
import re

def read_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages)

def normalize(text: str) -> str:
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Seitenzahlen
    text = re.sub(r'\n{3,}', '\n\n', text)                        # max 1 Leerzeile
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)                  # weiche Umbrüche
    return text

def load_pdf_text(path: str) -> str:
    return normalize(read_pdf(path))

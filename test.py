from pypdf import PdfReader
import re

text = "\n".join((p.extract_text() or "") for p in PdfReader("data/bgb.pdf").pages)

# Gezielt nach echten Paragraphen-Anfängen suchen
for para in ["§ 1 ", "§ 2 ", "§ 433", "§ 823"]:
    idx = text.find(para)
    if idx == -1:
        print(f"{para!r}: NICHT gefunden\n")
        continue
    # 100 Zeichen davor, 200 danach
    start = max(0, idx - 100)
    print(f"=== {para!r} bei Position {idx} ===")
    print(repr(text[start:idx + 200]))
    print()

import re

# Zeilen, die mit "§" beginnen (optional Whitespace davor)
lines_with_para_start = [
    line for line in text.split("\n")
    if re.match(r'^\s*§\s*\d+', line)
]
print(f"Zeilen, die mit '§' beginnen: {len(lines_with_para_start)}")
for line in lines_with_para_start[:5]:
    print(repr(line[:100]))
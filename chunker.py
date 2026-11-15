import re

def split_by_paragraph(text: str, law_name: str):
    pattern = r'(?=^§\s*\d+[a-z]?)'
    parts = re.split(pattern, text, flags=re.MULTILINE)

    chunks = []
    for part in parts:
        part = part.strip()
        if not part or not re.match(r'§\s*\d+', part):
            continue
        m = re.match(r'§\s*(\d+[a-z]?)', part)
        para_num = m.group(1) if m else "unknown"

        chunks.append({
            "text": part,
            "metadata": {
                "source": law_name,
                "paragraph": f"§ {para_num}"
            }
        })
    return chunks
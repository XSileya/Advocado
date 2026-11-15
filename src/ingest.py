"""
Ingest für GG und BGB.
Liest PDFs, normalisiert, chunkt nach Paragraphen/Artikeln, schreibt in ChromaDB.
"""
import os
import re
import glob
import hashlib
import chromadb
from openai import OpenAI
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = "text-embedding-3-small"
CHROMA_DIR = "chroma_db"
COLLECTION = "gesetze"

client = OpenAI(api_key=OPENAI_API_KEY)
chroma = chromadb.PersistentClient(path=CHROMA_DIR)
col = chroma.get_or_create_collection(COLLECTION)


# ---------- PDF lesen ----------

def read_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def normalize(text: str) -> str:
    # Non-breaking spaces (U+00A0) zu normalen Leerzeichen
    text = text.replace("\xa0", " ")
    # Fußnoten-Blöcke "(+++ ... +++)" entfernen (auch mehrzeilig)
    text = re.sub(r'\(\+\+\+.*?\+\+\+\)', '', text, flags=re.DOTALL)
    # Seitenzahlen allein auf einer Zeile entfernen
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    # Mehr als 2 aufeinanderfolgende Leerzeilen → 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


# ---------- Chunking ----------

def split_paragraphs(text: str, law_name: str, pattern: str, kind: str):
    """
    kind: 'Art' oder '§'
    pattern: Regex für Zeilenanfang, z.B. r'(?=^§\s*\d+)'
    """
    parts = re.split(pattern, text, flags=re.MULTILINE)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Nur Teile nehmen, die mit dem erwarteten Marker beginnen
        m = re.match(rf'^({kind}\s*\d+[a-z]?)', part)
        if not m:
            continue
        para_id = m.group(1).strip()
        chunks.append({
            "text": part,
            "metadata": {
                "source": law_name,
                "paragraph": para_id,
            },
        })
    return chunks


# ---------- Embeddings ----------

def embed(texts):
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def ingest_file(path: str, law_name: str, kind: str, pattern: str):
    print(f"\nVerarbeite {path} als {law_name} ({kind}-basiert)...")
    raw = read_pdf(path)
    clean = normalize(raw)
    chunks = split_paragraphs(clean, law_name, pattern, kind)

    if not chunks:
        print(f"  !! Keine Chunks gefunden — Regex prüfen!")
        return

    print(f"  {len(chunks)} Chunks gefunden")

    # In Batches embedden (OpenAI mag max ~2048 Inputs pro Request)
    BATCH = 100
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i + BATCH]
        texts = [c["text"] for c in batch]
        vecs = embed(texts)

        ids = [
            hashlib.md5(f"{law_name}:{c['metadata']['paragraph']}:{k}".encode()).hexdigest()
            for k, c in enumerate(batch)
        ]
        col.upsert(
            ids=ids,
            embeddings=vecs,
            documents=texts,
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  Batch {i // BATCH + 1}: {len(batch)} Chunks")

    print(f"  Fertig: {law_name}")


# ---------- Main ----------

if __name__ == "__main__":
    # GG: Artikel
    gg_path = "data/gg.pdf"
    if os.path.exists(gg_path):
        ingest_file(
            gg_path, "GG",
            kind="Art",
            pattern=r'(?=^Art\s*\d+[a-z]?)',
        )

    # BGB: Paragraphen
    bgb_path = "data/bgb.pdf"
    if os.path.exists(bgb_path):
        ingest_file(
            bgb_path, "BGB",
            kind="§",
            pattern=r'(?=^§\s*\d+[a-z]?)',
        )

    print(f"\nCollection '{COLLECTION}' enthält jetzt {col.count()} Chunks.")
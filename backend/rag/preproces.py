import os
from pathlib import Path

def load_raw_documents(raw_folder_path):
    """
    Load all text files from raw folder and return list of dicts with 'text' and 'source'.
    """
    docs = []
    raw_folder = Path(raw_folder_path)
    for file in raw_folder.glob("*.txt"):
        with open(file, encoding="utf-8") as f:
            text = f.read().strip()
            docs.append({"text": text, "source": file.name})
    return docs

def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into chunks with overlap (for better context capture).
    Returns list of text chunks.
    """
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

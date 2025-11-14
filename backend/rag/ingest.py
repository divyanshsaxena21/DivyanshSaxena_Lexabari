import os
import glob
import json
from pathlib import Path
from typing import List

try:
    import faiss
except Exception:
    raise SystemExit("faiss is required. Ensure 'faiss-cpu' is installed in requirements")

from rag.embedder import Embedder

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
EMBED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "embeddings")
Path(EMBED_DIR).mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 400  # words
CHUNK_OVERLAP = 50


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+size]
        chunks.append(" ".join(chunk))
        i += size - overlap
    return chunks


def ingest():
    embedder = Embedder()

    # Collect all chunks and metadata
    chunk_texts = []
    chunk_metas = []

    pattern = os.path.join(RAW_DIR, "*.txt")
    for path in sorted(glob.glob(pattern)):
        slug = os.path.splitext(os.path.basename(path))[0]
        meta_path = os.path.join(RAW_DIR, f"{slug}.json")
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as mf:
                try:
                    meta = json.load(mf)
                except Exception:
                    meta = {}

        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        chunks = chunk_text(text)
        for idx, c in enumerate(chunks):
            chunk_texts.append(c)
            chunk_metas.append({
                'doc_id': slug,
                'chunk_index': idx,
                'text_snippet': c[:300],
                'title': meta.get('title'),
                'source_url': meta.get('source_url')
            })

    if not chunk_texts:
        print("No chunks found to ingest.")
        return

    print(f"Encoding {len(chunk_texts)} chunks...")
    embeddings = embedder.encode(chunk_texts)

    import numpy as np
    arr = np.array(embeddings).astype('float32')

    dim = arr.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors -> cosine if normalized

    # Normalize vectors to unit length for cosine similarity
    faiss.normalize_L2(arr)
    index.add(arr)

    faiss_path = os.path.join(EMBED_DIR, 'index.faiss')
    faiss.write_index(index, faiss_path)

    meta_path = os.path.join(EMBED_DIR, 'metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as mf:
        json.dump(chunk_metas, mf, indent=2)

    print(f"Wrote FAISS index to {faiss_path} and metadata to {meta_path}")


if __name__ == '__main__':
    ingest()

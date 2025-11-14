import os
import json
import numpy as np
from pathlib import Path

EMBEDDINGS_DIR = Path(os.path.join(os.path.dirname(__file__), "../api/data/embeddings"))

def save_embeddings(filename, embeddings, documents):
    """
    Save embeddings (numpy array) and associated documents (metadata) as json and npy files.
    """
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_DIR / f"{filename}.npy", embeddings)
    with open(EMBEDDINGS_DIR / f"{filename}.json", "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

def load_embeddings(filename):
    """
    Load embeddings numpy array and documents json.
    Returns (embeddings, documents)
    """
    embeddings_path = EMBEDDINGS_DIR / f"{filename}.npy"
    documents_path = EMBEDDINGS_DIR / f"{filename}.json"
    if not embeddings_path.exists() or not documents_path.exists():
        return None, None
    embeddings = np.load(embeddings_path)
    with open(documents_path, "r", encoding="utf-8") as f:
        documents = json.load(f)
    return embeddings, documents

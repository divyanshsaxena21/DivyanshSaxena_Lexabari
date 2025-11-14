import os
import glob
import json
import numpy as np
from rag.embedder import Embedder

try:
    import faiss
except Exception:
    faiss = None


class Retriever:
    def __init__(self, raw_dir=None, embed_dir=None):
        self.raw_dir = raw_dir or os.path.join(os.path.dirname(__file__), "..", "data", "raw")
        self.embed_dir = embed_dir or os.path.join(os.path.dirname(__file__), "..", "data", "embeddings")
        self.embedder = Embedder()
        # Prefer FAISS index if present
        self.index = None
        self.metadata = None
        if faiss and os.path.exists(os.path.join(self.embed_dir, 'index.faiss')):
            try:
                self.index = faiss.read_index(os.path.join(self.embed_dir, 'index.faiss'))
                with open(os.path.join(self.embed_dir, 'metadata.json'), 'r', encoding='utf-8') as mf:
                    self.metadata = json.load(mf)
                print(f"Loaded FAISS index with {len(self.metadata)} chunks")
            except Exception as e:
                print("Failed to load FAISS index:", e)

        # Fallback: load whole documents
        self.documents = self._load_documents()
        if not self.index:
            # Precompute embeddings for full docs
            self.doc_embeddings = self._embed_documents()
        else:
            self.doc_embeddings = None

    def _load_documents(self):
        docs = []
        pattern = os.path.join(self.raw_dir, "*.txt")
        for path in sorted(glob.glob(pattern)):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
            except Exception:
                continue

            slug = os.path.splitext(os.path.basename(path))[0]
            meta_path = os.path.join(self.raw_dir, f"{slug}.json")
            meta = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as mf:
                        meta = json.load(mf)
                except Exception:
                    meta = {}

            doc = {
                'id': slug,
                'text': text,
                'title': meta.get('title') or slug,
                'source_url': meta.get('source_url'),
                'meta': meta,
            }
            docs.append(doc)

        return docs

    def _embed_documents(self):
        if not self.documents:
            return np.array([])

        texts = [doc['text'] for doc in self.documents]
        embeddings = self.embedder.encode(texts)
        try:
            arr = np.array(embeddings)
        except Exception:
            arr = np.array([])
        return arr

    def retrieve(self, query, top_k=3, score_threshold=0.12):
        """
        Retrieve top_k most relevant chunks or documents for the query.
        Returns list of results and max score.
        """
        # If FAISS index exists, use it to retrieve chunk-level matches
        if self.index is not None and self.metadata is not None and faiss is not None:
            q_emb = self.embedder.encode([query])
            q_vec = np.array(q_emb).astype('float32')
            if q_vec.ndim == 2:
                q_vec = q_vec[0]
            # normalize and reshape for faiss
            q_vec = q_vec.reshape(1, -1).astype('float32')
            faiss.normalize_L2(q_vec)
            D, I = self.index.search(q_vec, top_k)
            results = []
            max_score = 0.0
            for dist, idx in zip(D[0], I[0]):
                if idx < 0 or idx >= len(self.metadata):
                    continue
                score = float(dist)
                if score > max_score:
                    max_score = score
                if score < score_threshold:
                    continue
                meta = self.metadata[idx]
                results.append({
                    'chunk_id': idx,
                    'text': meta.get('text_snippet'),
                    'title': meta.get('title'),
                    'doc_id': meta.get('doc_id'),
                    'source_url': meta.get('source_url'),
                    'score': score,
                })
            return results, max_score

        # Fallback to full-document retrieval
        if self.doc_embeddings is None or self.doc_embeddings.size == 0:
            return [], 0.0

        q_emb = self.embedder.encode([query])
        q_vec = np.array(q_emb)
        if q_vec.ndim == 2:
            q_vec = q_vec[0]

        try:
            sims = np.dot(self.doc_embeddings, q_vec) / (
                np.linalg.norm(self.doc_embeddings, axis=1) * np.linalg.norm(q_vec) + 1e-10
            )
        except Exception:
            return [], 0.0

        top_indices = sims.argsort()[::-1][:top_k]
        results = []
        for i in top_indices:
            score = float(sims[i])
            if score < score_threshold:
                continue
            doc = self.documents[i]
            results.append({
                'doc_id': doc['id'],
                'text': doc['text'][:300],
                'title': doc['title'],
                'source_url': doc.get('source_url'),
                'score': score,
            })

        max_score = float(sims.max()) if sims.size > 0 else 0.0
        return results, max_score

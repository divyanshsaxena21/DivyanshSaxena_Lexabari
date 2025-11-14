import numpy as np
from rag.embedder import Embedder

class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.documents = [
            {"text": "The constitution of India guarantees fundamental rights.", "source": "Bare Act 1"},
            {"text": "The Supreme Court ruled on privacy as a fundamental right.", "source": "Case Law 1"},
            {"text": "Data protection rules were introduced under the IT Act.", "source": "Regulation 1"},
        ]
        # Precompute embeddings for all documents
        self.doc_embeddings = self._embed_documents()

    def _embed_documents(self):
        texts = [doc["text"] for doc in self.documents]
        embeddings = self.embedder.encode(texts)  # HF API returns list of lists
        return np.array(embeddings)

    def retrieve(self, query, top_k=2):
        query_vec = np.array(self.embedder.encode([query]))[0]  # (dim,)
        
        similarities = np.dot(self.doc_embeddings, query_vec) / (
            np.linalg.norm(self.doc_embeddings, axis=1) * np.linalg.norm(query_vec) + 1e-10
        )

        top_indices = similarities.argsort()[::-1][:top_k]

        results = [
            {
                "text": self.documents[i]["text"],
                "source": self.documents[i]["source"],
                "score": float(similarities[i])
            }
            for i in top_indices
        ]

        return results

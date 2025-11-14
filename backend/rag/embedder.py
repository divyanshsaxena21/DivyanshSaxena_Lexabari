import os
import requests
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Load .env located one level above this file if present
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))


class Embedder:
    """Embedder that prefers the Hugging Face Router (if HF_API_KEY is set)
    but falls back to a lightweight TF-IDF vectorizer (no torch required).
    """

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name

        # Try several possible HF router/api endpoints (best-effort)
        self.endpoints = [
            f"https://router.huggingface.co/hf-inference/{model_name}",
            f"https://router.huggingface.co/hf-inference-pipeline/{model_name}",
            f"https://api-inference.huggingface.co/models/{model_name}",
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}",
        ]

        self.hf_token = os.getenv("HF_API_KEY")
        if self.hf_token:
            self.headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json",
            }
        else:
            self.headers = None

        # TF-IDF vectorizer will be created lazily if we need to fallback
        self._vectorizer = None

    def _call_hf(self, texts):
        if not self.hf_token:
            return None

        payload = {"inputs": texts, "options": {"wait_for_model": True}}

        for url in self.endpoints:
            try:
                resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
            except Exception:
                # network error or invalid URL, try next
                continue

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    return None

                # Normalize several possible HF response shapes into numpy array
                if isinstance(data, list) and all(isinstance(x, (list, float, int)) for x in data):
                    return np.array(data)

                if isinstance(data, list) and all(isinstance(x, dict) for x in data):
                    # e.g. [{'embedding': [...]}, ...]
                    if all('embedding' in x for x in data):
                        return np.array([x['embedding'] for x in data])

                if isinstance(data, dict):
                    # e.g. {'embedding': [...]}
                    if 'embedding' in data and isinstance(data['embedding'], list):
                        return np.array(data['embedding'])
                    if 'embeddings' in data and isinstance(data['embeddings'], list):
                        return np.array(data['embeddings'])

                # If we get a nested numeric result, try to coerce
                try:
                    arr = np.array(data)
                    if arr.dtype != object:
                        return arr
                except Exception:
                    pass

            # non-200 or unexpected shape: try next endpoint
        return None

    def _tfidf_encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]

        # Initialize and fit vectorizer on provided texts (simple fallback)
        if self._vectorizer is None:
            self._vectorizer = TfidfVectorizer()
            # Fit on the texts so that transform returns dense arrays
            # (For a real app, fit on your whole corpus once instead)
            self._vectorizer.fit(texts)

        emb = self._vectorizer.transform(texts).toarray()
        return emb

    def encode(self, texts):
        """
        texts: List[str] or str
        Returns: numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        # Try Hugging Face router endpoints first (if API key provided)
        hf_emb = self._call_hf(texts)
        if hf_emb is not None:
            return hf_emb

        # Fallback to TF-IDF (no torch required)
        return self._tfidf_encode(texts)

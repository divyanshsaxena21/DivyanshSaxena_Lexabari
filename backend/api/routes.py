from fastapi import APIRouter, HTTPException, Query
from rag.retriever import Retriever
from rag.generator import Generator
import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

router = APIRouter()

retriever = Retriever()
generator = Generator()

# GROQ optional configuration. If `GROQ_API_KEY` is not provided the app still starts
# but `/groq_search` will return a 501 indicating the feature is not configured.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/v1/indexes/your_index_name/query")
GROQ_ENABLED = bool(GROQ_API_KEY)
# Server-side confidence threshold for returned results
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.12'))


def _normalize_results(results):
    """Ensure each result has a `source` field for frontend display."""
    normalized = []
    for r in results:
        if not isinstance(r, dict):
            normalized.append(r)
            continue
        source = r.get('source') or r.get('source_url') or r.get('title') or r.get('doc_id') or r.get('id')
        nr = dict(r)
        nr['source'] = source
        normalized.append(nr)
    return normalized


@router.get("/retrieve")
async def retrieve_documents(query: str = Query(..., min_length=1)):
    try:
        results, max_score = retriever.retrieve(query)

        # filter results by server-side confidence threshold
        filtered = [r for r in results if isinstance(r.get('score'), (int, float)) and r.get('score') >= CONFIDENCE_THRESHOLD]
        return {"results": _normalize_results(filtered)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groq_search")
async def groq_search(query: str = Query(..., min_length=1)):
    if not GROQ_ENABLED:
        raise HTTPException(status_code=501, detail="GROQ search is not configured. Set GROQ_API_KEY to enable.")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "limit": 5
    }
    try:
        response = requests.post(GROQ_BASE_URL, headers=headers, json=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_endpoint(payload: dict):
    """Accepts JSON body with a `query` field and returns retrieval results.
    This is provided as a POST-compatible alias for frontends that POST to `/query`.
    """
    q = payload.get("query") if isinstance(payload, dict) else None
    if not q:
        raise HTTPException(status_code=400, detail="Missing 'query' in request body")
    try:
        results, max_score = retriever.retrieve(q)

        # Server-side filtering
        filtered = [r for r in results if isinstance(r.get('score'), (int, float)) and r.get('score') >= CONFIDENCE_THRESHOLD]
        filtered_max = max([r.get('score') for r in filtered], default=0.0)

        # If no confident local result and GROQ is enabled, fallback to GROQ
        groq_threshold = float(os.getenv('GROQ_SCORE_THRESHOLD', '0.12'))
        if (not filtered or filtered_max < groq_threshold) and GROQ_ENABLED:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            groq_payload = {"query": q, "limit": 5}
            try:
                resp = requests.post(GROQ_BASE_URL, headers=headers, json=groq_payload, timeout=30)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                groq_data = resp.json()
                # Return local (normalized) results (if any) and groq fallback
                return {"results": _normalize_results(filtered), "fallback": "groq", "groq": groq_data}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        return {"results": _normalize_results(filtered)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask_endpoint(payload: dict):
    """Accepts JSON body with `question` field; returns an `answer` and `sources`.
    Uses local retriever first; if low confidence, optionally falls back to GROQ and returns its response.
    """
    q = payload.get("question") if isinstance(payload, dict) else None
    if not q:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")

    try:
        results, max_score = retriever.retrieve(q)

        # Server-side filtering
        filtered = [r for r in results if isinstance(r.get('score'), (int, float)) and r.get('score') >= CONFIDENCE_THRESHOLD]
        filtered_max = max([r.get('score') for r in filtered], default=0.0)

        groq_threshold = float(os.getenv('GROQ_SCORE_THRESHOLD', '0.12'))
        if (not filtered or filtered_max < groq_threshold) and GROQ_ENABLED:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            groq_payload = {"query": q, "limit": 5}
            resp = requests.post(GROQ_BASE_URL, headers=headers, json=groq_payload, timeout=30)
            if resp.status_code == 200:
                groq_data = resp.json()
                # For now, use GROQ response as a fallback answer
                return {"answer": None, "fallback": "groq", "groq": groq_data}

        # Use generator to synthesize an answer from local filtered results
        answer, sources = generator.generate(q, filtered)
        return {"answer": answer, "sources": sources, "results": _normalize_results(filtered)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

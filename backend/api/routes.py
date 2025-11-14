from fastapi import APIRouter, HTTPException, Query
from rag.retriever import Retriever
import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

router = APIRouter()

retriever = Retriever()

# GROQ optional configuration. If `GROQ_API_KEY` is not provided the app still starts
# but `/groq_search` will return a 501 indicating the feature is not configured.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/v1/indexes/your_index_name/query")
GROQ_ENABLED = bool(GROQ_API_KEY)


@router.get("/retrieve")
async def retrieve_documents(query: str = Query(..., min_length=1)):
    try:
        results = retriever.retrieve(query)
        return {"results": results}
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
        results = retriever.retrieve(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

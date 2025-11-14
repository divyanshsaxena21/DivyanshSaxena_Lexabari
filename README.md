# Legal RAG — Readme

**Overview:**
- **Project:** Legal RAG (Retrieval-Augmented Generation) prototype combining a small document store + retriever and a simple generator.
- **Structure:** backend (FastAPI) and frontend (Vite + React).

**Quick Facts:**
- **Backend:** `backend/` (FastAPI). Runs with `uvicorn main:app --reload --port <port>`.
- **Frontend:** `frontend/frontend/` (Vite + React). Dev server via `npm run dev`.

**Valid Routes (backend)**
- **GET `/retrieve`**: query param `query` (required) — returns `{"results": [...]}`. Example:
  ```
  curl "http://localhost:8080/retrieve?query=privacy+law"
  ```
- **GET `/groq_search`**: query param `query` (requires `GROQ_API_KEY`). This forwards the query to a GROQ index. Example:
  ```
  curl "http://localhost:8080/groq_search?query=data+protection"
  ```
- **POST `/query`**: JSON body `{ "query": "..." }` — returns `{"results": [...]}` and is suitable for POST requests from the frontend.
  ```
  curl -X POST http://localhost:8080/query -H "Content-Type: application/json" -d "{\"query\":\"privacy law\"}"
  ```
- **Docs & OpenAPI:** `GET /docs`, `GET /redoc`, `GET /openapi.json` (FastAPI automatic).

**Response Shape (retrieve/query)**
- `results` is an array of objects with keys: `text` (string), `source` (string), `score` (float).

**Embedding behavior (important)**
- The embedder prefers calling Hugging Face router endpoints if `HF_API_KEY` is present.
- If `HF_API_KEY` is not set or HF calls fail, the code falls back to a TF-IDF-based embedding (no `torch` required). This makes deployment on platforms with limited compute (like Render free tier) possible.

**Environment variables**
- Backend (create a `.env` in `backend/` or set env vars):
  - `HF_API_KEY` (optional) — Hugging Face token to call router endpoints. If not set, TF-IDF fallback will be used.
  - `GROQ_API_KEY` (optional) — required only if you intend to use `/groq_search`. Note: current code raises a ValueError at startup if `GROQ_API_KEY` is missing; set it or remove the GROQ usage.
- Frontend (Vite):
  - `VITE_API_URL` — base URL for backend, typically `http://localhost:8080` in development. Put this in `frontend/frontend/.env.local` (the repository already contains a sample `.env.local`).

**Install & Run (local development)**
- Backend (Python):
  ```powershell
  cd C:\Users\admin\Desktop\legal_rag\backend
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  uvicorn main:app --reload --port 8080
  ```
  Notes:
  - If you want to use `sentence-transformers` locally you will need `torch` which may increase deployment complexity. The repo includes a TF-IDF fallback specifically to avoid requiring `torch` for simple deployments.

- Frontend (Vite + React):
  ```powershell
  cd C:\Users\admin\Desktop\legal_rag\frontend\frontend
  npm install
  npm run dev
  ```

**Frontend configuration**
- The React app reads the backend base URL from `import.meta.env.VITE_API_URL`. Edit `frontend/frontend/.env.local` or set `VITE_API_URL` in your environment to change which backend the app uses.

**Deployment notes**
- For lightweight hosting (Render free tier or similar) avoid installing `torch`. Use the default behavior (no `HF_API_KEY`) so the embedder uses TF-IDF fallback.
- If you require better semantic embeddings in production, consider:
  - Hosting a separate ML worker with `sentence-transformers` + `torch` on an instance that supports it.
  - Or using a paid HF inference endpoint and setting `HF_API_KEY` (watch for API limits/costs).

**Troubleshooting**
- If the app fails on startup with a `ValueError: GROQ_API_KEY not found`, either set `GROQ_API_KEY` in the backend `.env` or modify `backend/api/routes.py` to make `groq_search` optional.
- If embeddings are empty or shapes mismatch, check `backend/rag/embedder.py` to see if HF calls were attempted (log output) or if TF-IDF produced a sparse vector.

**Files of interest**
- `backend/main.py` — app entry and CORS config.
- `backend/api/routes.py` — route definitions (`/retrieve`, `/groq_search`, `/query`).
- `backend/rag/embedder.py` — embedder: HF router usage and TF-IDF fallback.
- `backend/rag/retriever.py` — computes document embeddings and does similarity retrieval.
- `frontend/frontend/src/App.jsx` — React UI and API calls (configured via `VITE_API_URL`).

**If you want changes**
- I can:
  - Add a `POST /ask` route that returns `{answer, sources}` (if you prefer the original frontend format).
  - Make `groq_search` optional so the app starts without `GROQ_API_KEY`.
  - Replace TF-IDF fallback with a lightweight hosted embedding provider.

---
If you'd like, I can also add a short `CONTRIBUTING.md` or expand any section of this README. Which part should I expand next?

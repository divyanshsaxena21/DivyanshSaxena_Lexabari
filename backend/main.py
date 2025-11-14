from fastapi import FastAPI
from api.routes import router
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Configure allowed origins via env var FRONTEND_ORIGINS (comma-separated). If not set,
# include localhost and the known Vercel host(s). Avoid trailing slashes in origins.
raw = os.getenv("FRONTEND_ORIGINS")
if raw:
    origins = [o.strip() for o in raw.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://divyansh-saxena-lexabari.vercel.app",
        "https://divyansh-saxena-lexabari-3nuqgk8ru-divyanshsaxena21s-projects.vercel.app",
    ]

# If you need to allow credentials (cookies/authorization), set ALLOW_CREDENTIALS=true in env.
allow_creds = os.getenv("ALLOW_CREDENTIALS", "false").lower() in ("1", "true", "yes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
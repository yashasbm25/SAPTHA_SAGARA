
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT_DIR / "agents" / "exp"
BACKEND_DIR = Path(__file__).resolve().parent

# Make the repository, agent files, and backend imports discoverable.
for directory in (ROOT_DIR, AGENT_DIR, BACKEND_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from api.marine import router as marine_router
from api.route import router as route_router

app = FastAPI(
    title="SAPTHA SAGARA Marine Intelligence API",
    description="Marine intelligence, conditions, and route analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "SAPTHA SAGARA",
        "message": "Marine Intelligence API is running.",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "saptha-sagara-backend"}


app.include_router(marine_router, prefix="/api")
app.include_router(route_router, prefix="/api")

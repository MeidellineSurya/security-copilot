from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import copilot, assessments, upload, sync
from app.db.mongo import connect_db, close_db
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

app = FastAPI(title="Security Copilot API", version="1.0.0", lifespan=lifespan)

# Allow both local dev and production frontend URLs
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", ""),        # set this in Railway env vars
    os.getenv("VERCEL_URL", ""),          # auto-set by Vercel
]

# Filter out empty strings
ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
app.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])

@app.get("/health")
async def health():
    return {"status": "ok"}
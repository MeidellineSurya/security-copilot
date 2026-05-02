from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import copilot, assessments, upload, sync
from app.db.mongo import connect_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

app = FastAPI(title="Security Copilot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
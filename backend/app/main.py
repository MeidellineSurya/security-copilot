from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import copilot, assessments
from app.db.mongo import connect_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the app starts, opens MongoDB connection
    await connect_db() # ← before yield = startup
    yield # ← app runs here
    # Runs once when the app shuts down, closes MongoDB connection
    await close_db() # ← after yield = shutdown

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

@app.get("/health")
async def health():
    return {"status": "ok"}
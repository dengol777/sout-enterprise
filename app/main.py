from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db
from app.api import auth, employees, briefings, inspector

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="СУОТ Enterprise",
    description="Система управления охраной труда (In-House)",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(briefings.router)
app.include_router(inspector.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

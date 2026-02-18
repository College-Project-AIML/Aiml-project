"""
Government Schemes Discovery Platform — FastAPI Backend

Run with:
    uvicorn services.api.app:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.db import init_pool, close_pool
from services.api.routes.schemes import router as schemes_router
from services.api.routes.search import router as search_router
from services.api.routes.categories import router as categories_router
from services.api.routes.eligibility import router as eligibility_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()


app = FastAPI(
    title="Aiml-project API",
    description="Government Schemes Discovery Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schemes_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(eligibility_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"name": "Aiml-project API", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}

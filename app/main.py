from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers.books import router as books_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Momentum Library API",
    version="0.1.0",
    description="Simple Library API -- books inventory and lending status.",
    lifespan=lifespan,
)

app.include_router(books_router)


@app.get("/health", tags=["system"])
def healthcheck():
    return {"status": "ok"}

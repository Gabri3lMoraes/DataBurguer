from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.database import create_tables
from app.logging_config import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    create_tables()
    yield


app = FastAPI(
    title="DataBurguer API",
    description="API operacional e analítica do MVP acadêmico DataBurguer.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)

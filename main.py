from contextlib import asynccontextmanager

from fastapi import FastAPI

from data.db import check_database_connection
from routers.ask import router as ask_router
from routers.health import router as health_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await check_database_connection()
    yield


app = FastAPI(title="AI Assistant Service", version="1.0.0", lifespan=lifespan)
app.include_router(ask_router)
app.include_router(health_router)

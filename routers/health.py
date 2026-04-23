from fastapi import APIRouter

from data.db import check_database_connection


router = APIRouter()


@router.get("/health/db")
async def database_health() -> dict[str, str]:
    await check_database_connection()
    return {"status": "ok"}

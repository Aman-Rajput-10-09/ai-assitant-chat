import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


load_dotenv()


def _normalize_database_url(database_url: str) -> str:
    normalized = database_url
    if normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", "postgresql+asyncpg://", 1)

    parts = urlsplit(normalized)
    query_pairs = dict(parse_qsl(parts.query, keep_blank_values=True))

    sslmode = query_pairs.pop("sslmode", None)
    query_pairs.pop("channel_binding", None)
    if sslmode == "require":
        query_pairs["ssl"] = "require"

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query_pairs),
            parts.fragment,
        )
    )


DATABASE_URL = os.getenv("DATABASE_URL", "")
ASYNC_DATABASE_URL = _normalize_database_url(DATABASE_URL) if DATABASE_URL else ""

if not ASYNC_DATABASE_URL:
    raise ValueError("DATABASE_URL is required. Add it to the project .env file.")

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def check_database_connection() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

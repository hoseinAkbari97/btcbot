from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis

router = APIRouter(tags=["system"])


class ComponentStatus(BaseModel):
    status: Literal["up", "down"]
    detail: str | None = None


class SystemStatus(BaseModel):
    status: Literal["healthy", "degraded"]
    api: ComponentStatus
    database: ComponentStatus
    redis: ComponentStatus


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/v1/system/status", response_model=SystemStatus)
async def system_status(
    session: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis)
) -> SystemStatus:
    database_status = ComponentStatus(status="up")
    redis_status = ComponentStatus(status="up")
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - exercised against deployed dependencies
        database_status = ComponentStatus(status="down", detail=type(exc).__name__)
    try:
        await redis.ping()
    except Exception as exc:  # pragma: no cover - exercised against deployed dependencies
        redis_status = ComponentStatus(status="down", detail=type(exc).__name__)

    status = "healthy" if database_status.status == redis_status.status == "up" else "degraded"
    return SystemStatus(
        status=status,
        api=ComponentStatus(status="up"),
        database=database_status,
        redis=redis_status,
    )

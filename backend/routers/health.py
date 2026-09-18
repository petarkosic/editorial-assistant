from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.settings import settings

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health(response: Response, session: AsyncSession = Depends(get_session)):
    db_ok = True

    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    key_ok = bool(settings.openai_api_key)
    if not db_ok:
        response.status_code = 503
        
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "down",
        "openai_key": key_ok,
    }

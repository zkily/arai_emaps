"""自動車ニュースティッカー API"""
from fastapi import APIRouter, Depends, Query

from app.core.config import settings
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.services.auto_news_service import get_auto_news

router = APIRouter()


@router.get("/auto-news")
async def fetch_auto_news(
    limit: int = Query(default=20, ge=1, le=50),
    _current_user: User = Depends(verify_token_and_get_user),
):
    """本日（JST）の日本自動車ニュース RSS 集約。クリックで原文 URL を開く用途。"""
    payload = await get_auto_news(limit=limit)
    return {
        "date": payload["date"],
        "items": payload["items"],
        "isFallback": payload.get("isFallback", False),
        "cached": payload.get("cached", False),
        "fetchedAt": payload.get("fetchedAt"),
        "enabled": settings.AUTO_NEWS_ENABLED,
    }

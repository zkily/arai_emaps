"""
品質管理モジュール
  /api/quality/inspection-newspaper  → 検査新聞紙通知（対象製品・自動メール設定）
"""
from fastapi import APIRouter

from app.modules.quality.inspection_newspaper_api import router as inspection_newspaper_router

router = APIRouter()
router.include_router(inspection_newspaper_router, tags=["検査新聞紙通知"])

__all__ = ["router"]

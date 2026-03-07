"""
システム管理モジュール
ユーザー管理、組織管理、権限・ロール管理、システム設定
"""
from fastapi import APIRouter
from .api import router as main_router
from .settings_api import router as settings_router

# 統合ルーター
router = APIRouter()
router.include_router(main_router)
router.include_router(settings_router)

__all__ = ["router"]

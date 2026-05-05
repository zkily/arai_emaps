"""
APSモジュール
"""
from fastapi import APIRouter

from .api import router as core_router
from .plating_draft_api import router as plating_draft_router

router = APIRouter()
router.include_router(core_router)
router.include_router(plating_draft_router)

__all__ = ["router"]

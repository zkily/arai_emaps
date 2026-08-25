"""
APSモジュール
"""
from fastapi import APIRouter

from .api import router as core_router
from .plating_draft_api import router as plating_draft_router
from .efficiency_period_override_api import router as efficiency_period_override_router

router = APIRouter()
router.include_router(core_router)
router.include_router(plating_draft_router)
router.include_router(efficiency_period_override_router)

__all__ = ["router"]

"""備品購入モジュール"""
from fastapi import APIRouter

from app.modules.supply_purchase.api import router as purchase_router

router = APIRouter()
router.include_router(purchase_router)

__all__ = ["router"]

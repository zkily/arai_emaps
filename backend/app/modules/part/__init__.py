"""部品購買・在庫モジュール（材料管理と対応するエンドポイント）"""
from fastapi import APIRouter
from app.modules.part.stock_api import router as stock_router

router = APIRouter()
router.include_router(stock_router, prefix="/stock", tags=["部品在庫"])

__all__ = ["router"]

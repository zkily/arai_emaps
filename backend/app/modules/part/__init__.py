"""部品購買・在庫モジュール（材料管理と対応するエンドポイント）"""
from fastapi import APIRouter
from app.modules.part.stock_api import router as stock_router
from app.modules.part.receiving_api import router as receiving_router

router = APIRouter()
router.include_router(stock_router, prefix="/stock", tags=["部品在庫"])
router.include_router(receiving_router, prefix="/receiving", tags=["部品受入ログ"])

__all__ = ["router"]

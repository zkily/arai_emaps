"""
材料管理モジュール
  /api/material/inspection-master  → 検品基準マスタ
  /api/material/receiving          → 受入ログ
  /api/material/stock              → 材料在庫（メイン + サブ）
  /api/material/stock-materials    → 在庫材料管理
  /api/material/forecast           → 内示・フォーキャスト
"""
from fastapi import APIRouter
from app.modules.material.inspection_api import router as inspection_router
from app.modules.material.receiving_api import router as receiving_router
from app.modules.material.stock_api import router as stock_router
from app.modules.material.stock_materials_api import router as stock_materials_router
from app.modules.material.forecast_api import router as forecast_router

router = APIRouter()
router.include_router(inspection_router, prefix="/inspection-master", tags=["材料検品基準マスタ"])
router.include_router(receiving_router, prefix="/receiving", tags=["材料受入ログ"])
router.include_router(stock_router, prefix="/stock", tags=["材料在庫"])
router.include_router(stock_materials_router, prefix="/stock-materials", tags=["在庫材料管理"])
router.include_router(forecast_router, prefix="/forecast", tags=["材料内示管理"])

__all__ = ["router"]

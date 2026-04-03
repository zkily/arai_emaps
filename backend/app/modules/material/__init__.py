"""
材料管理モジュール
  /api/material/inspection-master              → 検品基準マスタ
  /api/material/receiving                      → 受入ログ
  /api/material/stock                          → 材料在庫（メイン + サブ）
  /api/material/stock-materials                → 在庫材料管理
  /api/material/forecast                       → 内示・フォーキャスト
  /api/material/usage                          → 材料使用済（切断工程使用数反映）
  /api/material/cutting                        → 材料切断ログ CSV インポート
  /api/material/product-material-association   → 製品ー材料照会
"""
from fastapi import APIRouter
from app.modules.material.inspection_api import router as inspection_router
from app.modules.material.receiving_api import router as receiving_router
from app.modules.material.stock_api import router as stock_router
from app.modules.material.stock_materials_api import router as stock_materials_router
from app.modules.material.forecast_api import router as forecast_router
from app.modules.material.usage_api import router as usage_router
from app.modules.material.cutting_import_api import router as cutting_router
from app.modules.material.product_material_association_api import router as product_material_router

router = APIRouter()
router.include_router(inspection_router, prefix="/inspection-master", tags=["材料検品基準マスタ"])
router.include_router(receiving_router, prefix="/receiving", tags=["材料受入ログ"])
router.include_router(stock_router, prefix="/stock", tags=["材料在庫"])
router.include_router(stock_materials_router, prefix="/stock-materials", tags=["在庫材料管理"])
router.include_router(forecast_router, prefix="/forecast", tags=["材料内示管理"])
router.include_router(usage_router, prefix="/usage", tags=["材料使用済"])
router.include_router(cutting_router, prefix="/cutting", tags=["材料切断ログ"])
router.include_router(product_material_router, prefix="/product-material-association", tags=["製品ー材料照会"])

__all__ = ["router"]

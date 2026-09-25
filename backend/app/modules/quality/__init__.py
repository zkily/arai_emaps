"""
品質管理モジュール
  /api/quality/inspection-newspaper  → 検査新聞紙通知（対象製品・自動メール設定）
  /api/quality/equipment-maintenance → 設備保全管理
  /api/quality/process-cautions      → 生産注意事項（工程別）
"""
from fastapi import APIRouter

from app.modules.quality.equipment_maintenance_api import router as equipment_maintenance_router
from app.modules.quality.inspection_newspaper_api import router as inspection_newspaper_router
from app.modules.quality.process_caution_api import router as process_caution_router

router = APIRouter()
router.include_router(inspection_newspaper_router, tags=["検査新聞紙通知"])
router.include_router(equipment_maintenance_router, tags=["設備保全管理"])
router.include_router(process_caution_router, tags=["生産注意事項"])

__all__ = ["router"]

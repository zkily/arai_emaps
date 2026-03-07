"""
データベース系API（production_summarys 等）＋在庫KPI
"""
from fastapi import APIRouter
from app.modules.database.api import router as production_summarys_router
from app.modules.database.inventory_kpi_api import router as inventory_kpi_router

router = APIRouter()
router.include_router(production_summarys_router)
router.include_router(inventory_kpi_router, prefix="/inventory-kpi")

__all__ = ["router"]

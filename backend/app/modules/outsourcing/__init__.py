"""
外注管理モジュール（外注先マスタ・工程製品・メッキ/溶接注文等）
"""
from fastapi import APIRouter
from app.modules.outsourcing.suppliers_api import router as suppliers_router
from app.modules.outsourcing.process_products_api import router as process_products_router
from app.modules.outsourcing.welding_api import router as welding_router

router = APIRouter()
router.include_router(suppliers_router, prefix="/suppliers", tags=["外注先マスタ"])
router.include_router(process_products_router, prefix="/process-products", tags=["外注工程製品"])
router.include_router(welding_router, prefix="/welding", tags=["溶接注文・受入"])

__all__ = ["router"]

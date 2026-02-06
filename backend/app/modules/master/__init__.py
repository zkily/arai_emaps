"""
マスタ管理モジュール（製品マスタ・材料マスタ等）
"""
from fastapi import APIRouter
from app.modules.master.api import router as product_router
from app.modules.master.api_material import router as material_router
from app.modules.master.api_supplier import router as supplier_router
from app.modules.master.api_process_route import router as process_route_router

router = APIRouter()
router.include_router(product_router, prefix="/products", tags=["製品マスタ"])
router.include_router(material_router, prefix="/materials", tags=["材料マスタ"])
router.include_router(supplier_router, prefix="/suppliers", tags=["仕入先マスタ"])
router.include_router(process_route_router, prefix="/process-routes", tags=["工程ルートマスタ"])

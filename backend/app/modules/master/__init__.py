"""
マスタ管理モジュール（製品マスタ・材料マスタ等）
"""
from fastapi import APIRouter
from app.modules.master.api import router as product_router
from app.modules.master.api_material import router as material_router
from app.modules.master.api_supplier import router as supplier_router
from app.modules.master.api_process_route import router as process_route_router
from app.modules.master.api_process import router as process_router
from app.modules.master.api_destination import router as destination_router
from app.modules.master.api_customer import router as customer_router
from app.modules.master.api_carrier import router as carrier_router
from app.modules.master.api_machine import router as machine_router
from app.modules.master.api_product_route_steps import router as product_route_steps_router

router = APIRouter()
router.include_router(product_router, prefix="/products", tags=["製品マスタ"])
router.include_router(material_router, prefix="/materials", tags=["材料マスタ"])
router.include_router(supplier_router, prefix="/suppliers", tags=["仕入先マスタ"])
router.include_router(process_router, prefix="/processes", tags=["工程マスタ"])
router.include_router(process_route_router, prefix="/process-routes", tags=["工程ルートマスタ"])
router.include_router(destination_router, prefix="/destinations", tags=["納入先マスタ"])
router.include_router(customer_router, prefix="/customers", tags=["顧客マスタ"])
router.include_router(carrier_router, prefix="/carriers", tags=["運送便マスタ"])
router.include_router(machine_router, prefix="/machines", tags=["設備マスタ"])
router.include_router(
    product_route_steps_router,
    prefix="/product/process/routes",
    tags=["製品別工程ルートステップ"],
)

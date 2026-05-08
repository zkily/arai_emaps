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
from app.modules.master.api_product_process_bom import router as product_process_bom_router
from app.modules.master.api_product_machine_config import router as product_machine_config_router
from app.modules.master.api_equipment_efficiency import router as equipment_efficiency_router
from app.modules.master.api_options import router as options_router
from app.modules.master.api_product_bom import router as product_bom_router
from app.modules.master.api_product_process_unit_price import router as product_unit_price_router
from app.modules.master.api_process_processing_fee import router as process_processing_fee_router
from app.modules.master.api_part_master import router as part_master_router
from app.modules.master.api_product_cost_snapshot import router as product_cost_snapshot_router
from app.modules.master.api_roller_bom import router as roller_bom_router
from app.modules.master.api_roller_master import router as roller_master_router
from app.modules.master.api_roller_usage import (
    status_router as roller_usage_status_router,
    log_router as roller_usage_log_router,
    action_router as roller_usage_action_router,
)

router = APIRouter()
router.include_router(options_router, prefix="/options", tags=["マスタオプション"])
router.include_router(product_router, prefix="/products", tags=["製品マスタ"])
router.include_router(material_router, prefix="/materials", tags=["材料マスタ"])
router.include_router(part_master_router, prefix="/parts", tags=["部品マスタ"])
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
router.include_router(product_process_bom_router, prefix="/product-process-bom", tags=["製品工程BOM"])
router.include_router(product_machine_config_router, prefix="/product-machine-config", tags=["製品機器設定"])
router.include_router(equipment_efficiency_router, prefix="/equipment-efficiency", tags=["設備能率管理"])
router.include_router(product_bom_router, prefix="/product-bom", tags=["明細BOM"])
router.include_router(product_unit_price_router, prefix="/product-process-unit-prices", tags=["工程別標準原価"])
router.include_router(process_processing_fee_router, prefix="/process-processing-fees", tags=["工程加工費マスタ"])
router.include_router(product_cost_snapshot_router, prefix="/product-cost-snapshots", tags=["累計単価スナップショット"])
router.include_router(roller_bom_router, prefix="/roller-bom", tags=["ローラーBOM"])
router.include_router(roller_master_router, prefix="/roller-master", tags=["ローラーマスタ"])
router.include_router(roller_usage_status_router, prefix="/roller-usage-status", tags=["ローラー使用状況"])
router.include_router(roller_usage_log_router, prefix="/roller-usage-log", tags=["ローラー使用ログ"])
router.include_router(roller_usage_action_router, prefix="/roller-usage", tags=["ローラー使用管理アクション"])

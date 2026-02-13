"""
出荷管理モジュール
- 納入先分组 (destination_groups) API
- 出荷明細 (shipping_items) API
- 印刷記録 (shipping_records) API
- ピッキングCSVエクスポート (export/export-picking-csv) API
- 出荷報告 overview / 印刷履歴 print/history API
"""
from fastapi import APIRouter
from app.modules.shipping.destination_groups_api import router as destination_groups_router
from app.modules.shipping.shipping_items_api import router as shipping_items_router
from app.modules.shipping.print_record_api import router as print_record_router
from app.modules.shipping.export_picking_api import router as export_picking_router
from app.modules.shipping.shipping_overview_api import router as overview_router
from app.modules.shipping.print_history_api import router as print_history_router
from app.modules.shipping.welding_api import router as welding_router
from app.modules.shipping.picking_api import router as picking_router

router = APIRouter()
router.include_router(destination_groups_router, prefix="/destination-groups", tags=["出荷・納入先分组"])
router.include_router(welding_router, prefix="/welding", tags=["溶接出荷管理"])
router.include_router(picking_router, prefix="/picking", tags=["ピッキング管理"])
router.include_router(shipping_items_router, prefix="/items", tags=["出荷明細"])
router.include_router(print_record_router, prefix="/print-record", tags=["印刷記録"])
router.include_router(export_picking_router, prefix="/export", tags=["ピッキングエクスポート"])
router.include_router(overview_router, prefix="/overview", tags=["出荷報告一覧"])
router.include_router(print_history_router, prefix="/print", tags=["印刷履歴"])

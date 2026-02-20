"""
ERPモジュール
統合されたERP機能（在庫管理、購買管理、販売管理、基礎データ管理）
"""
from fastapi import APIRouter
from .api import router as main_router
from .inventory_api import router as inventory_router
from .sales_api import router as sales_router
from .master_api import router as master_router
from .stock_transaction_log_api import router as stock_transaction_log_router
from .production_actual_api import router as production_actual_router

# メインルーター（すべてのERPサブルーターを統合）
router = APIRouter()

# 既存のメインAPIを含める
router.include_router(main_router)

# 新しいモジュールルーターを含める
router.include_router(inventory_router)
router.include_router(sales_router)
router.include_router(master_router)
router.include_router(stock_transaction_log_router)
router.include_router(production_actual_router)

__all__ = ['router']


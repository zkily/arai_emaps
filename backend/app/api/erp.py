"""
ERP（企業資源計画）APIエンドポイント
販売管理、購買管理、在庫管理など
"""
from fastapi import APIRouter, Depends
from app.api.auth import verify_token_and_get_user
from app.models.user import User

router = APIRouter()


@router.get("/sales")
async def get_sales(current_user: User = Depends(verify_token_and_get_user)):
    """販売管理データ取得"""
    return {"message": "販売管理データ", "data": []}


@router.get("/purchase")
async def get_purchase(current_user: User = Depends(verify_token_and_get_user)):
    """購買管理データ取得"""
    return {"message": "購買管理データ", "data": []}


@router.get("/inventory")
async def get_inventory(current_user: User = Depends(verify_token_and_get_user)):
    """在庫管理データ取得"""
    return {"message": "在庫管理データ", "data": []}


@router.get("/accounting")
async def get_accounting(current_user: User = Depends(verify_token_and_get_user)):
    """会計管理データ取得"""
    return {"message": "会計管理データ", "data": []}


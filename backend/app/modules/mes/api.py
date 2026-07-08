"""
MES（製造実行システム）APIエンドポイント
製造実行管理、品質管理、設備管理など
"""
from fastapi import APIRouter, Depends
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.mes.product_label_api import router as product_label_router

router = APIRouter()
router.include_router(product_label_router, prefix="/product-label", tags=["製品ラベル発行"])


@router.get("/execution")
async def get_execution(current_user: User = Depends(verify_token_and_get_user)):
    """製造実行データ取得"""
    return {"message": "製造実行データ", "data": []}


@router.get("/quality")
async def get_quality(current_user: User = Depends(verify_token_and_get_user)):
    """品質管理データ取得"""
    return {"message": "品質管理データ", "data": []}


@router.get("/equipment")
async def get_equipment(current_user: User = Depends(verify_token_and_get_user)):
    """設備管理データ取得"""
    return {"message": "設備管理データ", "data": []}


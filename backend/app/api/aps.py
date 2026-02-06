"""
APS（先進的計画・スケジューリング）APIエンドポイント
生産計画、スケジューリング、MRPなど
"""
from fastapi import APIRouter, Depends
from app.api.auth import verify_token_and_get_user
from app.models.user import User

router = APIRouter()


@router.get("/planning")
async def get_planning(current_user: User = Depends(verify_token_and_get_user)):
    """生産計画データ取得"""
    return {"message": "生産計画データ", "data": []}


@router.get("/scheduling")
async def get_scheduling(current_user: User = Depends(verify_token_and_get_user)):
    """スケジューリングデータ取得"""
    return {"message": "スケジューリングデータ", "data": []}


@router.get("/mrp")
async def get_mrp(current_user: User = Depends(verify_token_and_get_user)):
    """資材所要量計画データ取得"""
    return {"message": "MRPデータ", "data": []}


@router.get("/capacity")
async def get_capacity(current_user: User = Depends(verify_token_and_get_user)):
    """生産能力計画データ取得"""
    return {"message": "生産能力計画データ", "data": []}


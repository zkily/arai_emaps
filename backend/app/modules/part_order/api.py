"""部品注文作成（材料側 material-order と同形のスタブ／将来連携用）"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

router = APIRouter()


class PartOrderCreateBody(BaseModel):
    date: Optional[str] = None
    part_cd: Optional[str] = None
    part_name: Optional[str] = None
    material_cd: Optional[str] = None
    material_name: Optional[str] = None
    order_quantity: Optional[float] = None
    order_bundle_quantity: Optional[float] = None
    raw: Optional[dict[str, Any]] = None

    class Config:
        extra = "allow"


@router.post("/create")
async def create_part_order(
    body: PartOrderCreateBody,
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    return {"success": True, "message": "部品注文作成は記録のみ（詳細連携は今後拡張）", "data": body.model_dump()}

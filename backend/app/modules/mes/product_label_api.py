"""
MES 製品ラベル（現品票）発行 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.product_label_service import build_label_preview

router = APIRouter()


@router.get("/preview")
async def get_product_label_preview(
    product_cd: str = Query(..., description="製品CD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品ラベル印刷プレビュー用データ（設定 + 成型設備）。"""
    product_cd = (product_cd or "").strip()
    if not product_cd:
        raise HTTPException(status_code=400, detail="製品CDは必須です")
    try:
        data = await build_label_preview(db, product_cd)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True, "data": data}

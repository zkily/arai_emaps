"""溶接品在庫推移 API（生産計画・只読）"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.erp.welding_inventory_trend_service import get_welding_inventory_trend

router = APIRouter(prefix="/production", tags=["溶接品在庫推移"])


def _parse_date(raw: str, name: str) -> date:
    try:
        return date.fromisoformat((raw or "").strip()[:10])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{name} は YYYY-MM-DD 形式で指定してください")


@router.get("/welding-inventory-trend")
async def welding_inventory_trend(
    date_from: str = Query(..., description="開始日 YYYY-MM-DD"),
    date_to: str = Query(..., description="終了日 YYYY-MM-DD"),
    keyword: str = Query("", description="製品CD・製品名"),
    part_cd: str = Query("", description="部品CD（部分一致）"),
    shortage_only: bool = Query(False, description="在庫不足の製品のみ"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """社内溶接ルート製品の日別在庫推移（部品・内示・倉庫を含む）。"""
    d0 = _parse_date(date_from, "date_from")
    d1 = _parse_date(date_to, "date_to")
    try:
        data = await get_welding_inventory_trend(
            db,
            d0,
            d1,
            keyword=keyword,
            part_cd=part_cd,
            shortage_only=shortage_only,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("溶接品在庫推移の取得に失敗しました")
        raise HTTPException(status_code=500, detail=f"取得に失敗しました: {e}")
    return {"success": True, "data": data}

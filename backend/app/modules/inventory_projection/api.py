"""月末在庫予測 API"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.inventory_projection.service import (
    EDITABLE_PLAN_PROCESS_KEYS,
    _cache,
    delete_plan_override,
    get_projection_cached,
    load_plan_overrides,
    month_bounds,
    parse_year_month,
    upsert_plan_overrides,
)

router = APIRouter(tags=["月末在庫予測"])


class PlanOverrideItem(BaseModel):
    plan_date: str = Field(..., description="対象日 YYYY-MM-DD")
    process_key: str = Field(..., description="工程 key")
    qty: Optional[int] = Field(None, description="手動計画合計（None で削除）")


class PlanOverrideSaveRequest(BaseModel):
    items: list[PlanOverrideItem]


def _parse_base_date(raw: str | None) -> date:
    if not raw or not raw.strip():
        return date.today()
    try:
        return date.fromisoformat(raw.strip()[:10])
    except ValueError:
        raise HTTPException(
            status_code=400, detail="base_date は YYYY-MM-DD 形式で指定してください"
        )


@router.get("/summary")
async def get_projection_summary(
    year_month: str = Query(..., description="対象月 YYYY-MM"),
    base_date: str | None = Query(None, description="基準日 YYYY-MM-DD（省略時は当日）"),
    force: bool = Query(False, description="キャッシュを無視して再計算"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程グループ別の日別在庫推移（基準日以前=実績、以降=予測）。"""
    bd = _parse_base_date(base_date)
    try:
        payload = await get_projection_cached(db, year_month, bd, force=force)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("月末在庫予測の計算に失敗しました")
        raise HTTPException(status_code=500, detail=f"計算に失敗しました: {e}")
    data = {k: v for k, v in payload.items() if not k.startswith("_")}
    return {"success": True, "data": data}


@router.get("/detail")
async def get_projection_detail(
    year_month: str = Query(..., description="対象月 YYYY-MM"),
    process_key: str = Query(..., description="工程グループ key"),
    base_date: str | None = Query(None, description="基準日 YYYY-MM-DD（省略時は当日）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定工程グループの製品別 日別在庫推移（ドリルダウン用）。"""
    bd = _parse_base_date(base_date)
    try:
        payload = await get_projection_cached(db, year_month, bd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("月末在庫予測の計算に失敗しました")
        raise HTTPException(status_code=500, detail=f"計算に失敗しました: {e}")
    detail = (payload.get("_product_detail") or {}).get(process_key)
    if detail is None:
        raise HTTPException(status_code=400, detail=f"process_key が不正です: {process_key}")
    return {
        "success": True,
        "data": {
            "year_month": payload.get("year_month"),
            "base_date": payload.get("base_date"),
            "projection_start": payload.get("projection_start"),
            "dates": payload.get("dates"),
            "process_key": process_key,
            "rows": detail,
        },
    }


@router.get("/plan-overrides")
async def get_plan_overrides(
    year_month: str = Query(..., description="対象月 YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """当月の計画合計手動修正の一覧。"""
    try:
        y, m = parse_year_month(year_month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    ps, pe = month_bounds(y, m)
    overrides = await load_plan_overrides(db, ps, pe)
    items = [
        {"plan_date": ds, "process_key": pk, "qty": qty}
        for (pk, ds), qty in sorted(overrides.items(), key=lambda x: (x[0][1], x[0][0]))
    ]
    return {
        "success": True,
        "data": {"items": items, "editable_process_keys": list(EDITABLE_PLAN_PROCESS_KEYS)},
    }


@router.put("/plan-overrides")
async def save_plan_overrides(
    body: PlanOverrideSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """計画合計手動修正の一括保存（qty=None は削除）。保存後キャッシュを破棄。"""
    try:
        count = await upsert_plan_overrides(
            db,
            [item.model_dump() for item in body.items],
            updated_by=getattr(current_user, "username", None),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("計画合計手動修正の保存に失敗しました")
        raise HTTPException(status_code=500, detail=f"保存に失敗しました: {e}")
    _cache.clear()
    return {"success": True, "data": {"count": count}}


@router.delete("/plan-overrides")
async def remove_plan_override(
    plan_date: str = Query(..., description="対象日 YYYY-MM-DD"),
    process_key: str = Query(..., description="工程 key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """計画合計手動修正を 1 件削除。"""
    try:
        d = date.fromisoformat(plan_date.strip()[:10])
    except ValueError:
        raise HTTPException(
            status_code=400, detail="plan_date は YYYY-MM-DD 形式で指定してください"
        )
    deleted = await delete_plan_override(db, d, process_key.strip())
    _cache.clear()
    return {"success": True, "data": {"deleted": deleted}}

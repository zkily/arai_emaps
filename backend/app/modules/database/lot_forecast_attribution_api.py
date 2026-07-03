"""管理コード → 日内示帰属 API。"""
from __future__ import annotations

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_mes_operation
from app.modules.auth.models import User
from app.modules.database.forming_daily_plan_service import parse_iso_date
from app.modules.database.lot_forecast_attribution_service import (
    delete_process_status_override,
    enrich_rows_with_process_status,
    build_reconcile_report,
    enrich_attribution_display_names,
    get_primary_forecast_summary,
    query_attributions,
    recompute_attribution,
    upsert_process_status_override,
)

router = APIRouter(prefix="/lot-forecast-attribution", tags=["lot-forecast-attribution"])


class RecomputeBody(BaseModel):
    startDate: str = Field(..., description="YYYY-MM-DD 計算開始日（この日以降を対象、終了日上限なし）")
    productCds: Optional[List[str]] = None
    modes: Optional[List[str]] = Field(default=None, description="PLAN / ACTUAL")


class BatchSummaryBody(BaseModel):
    management_codes: List[str] = Field(..., min_length=1, max_length=500)
    process_key: str = Field(default="molding")


class ProcessStatusOverrideBody(BaseModel):
    management_code: str = Field(..., min_length=1, max_length=100)
    aps_batch_plan_id: Optional[int] = None
    cutting_completed: Optional[bool] = Field(
        None, description="true/false=手動指定、null=自動判定"
    )
    molding_completed: Optional[bool] = Field(
        None, description="true/false=手動指定、null=自動判定"
    )
    remark: Optional[str] = Field(None, max_length=500)


@router.post("/recompute")
async def recompute_lot_forecast_attribution(
    body: RecomputeBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    try:
        ps = parse_iso_date(body.startDate)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="日付形式は YYYY-MM-DD です") from e

    modes = body.modes or ["PLAN", "ACTUAL"]
    for m in modes:
        if m not in ("PLAN", "ACTUAL"):
            raise HTTPException(status_code=400, detail="modes は PLAN / ACTUAL のみ")

    try:
        result = await recompute_attribution(db, ps, body.productCds, modes)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"内示帰属の再計算に失敗しました: {e}",
        ) from e
    return {"code": 200, "data": result, "message": f"内示帰属の再計算が完了しました（{result['inserted']} 件）"}


@router.get("")
async def list_lot_forecast_attribution(
    management_code: Optional[str] = Query(None),
    aps_batch_plan_id: Optional[int] = Query(None),
    product_cd: Optional[str] = Query(None),
    destination_cd: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    process_key: Optional[str] = Query(None),
    attribution_mode: Optional[str] = Query(None),
    prefer_actual: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = parse_iso_date(start_date) if start_date else None
    pe = parse_iso_date(end_date) if end_date else None
    rows = await query_attributions(
        db,
        management_code=management_code,
        aps_batch_plan_id=aps_batch_plan_id,
        product_cd=product_cd,
        destination_cd=destination_cd,
        start_date=ps,
        end_date=pe,
        process_key=process_key,
        attribution_mode=attribution_mode,
        prefer_actual=prefer_actual,
        require_management_code=True,
    )
    await enrich_attribution_display_names(db, rows)
    await enrich_rows_with_process_status(db, rows)
    return {"code": 200, "data": rows, "total": len(rows)}


@router.put("/process-status-override")
async def save_process_status_override(
    body: ProcessStatusOverrideBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """管理コードの切断完了・成型完了を手動指定（帰属再計算の影響を受けない）。"""
    try:
        data = await upsert_process_status_override(
            db,
            body.management_code,
            aps_batch_plan_id=body.aps_batch_plan_id,
            cutting_completed=body.cutting_completed,
            molding_completed=body.molding_completed,
            remark=body.remark,
            updated_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状態の保存に失敗しました: {e}") from e
    return {"code": 200, "data": data, "message": "状態を保存しました"}


@router.delete("/process-status-override")
async def remove_process_status_override(
    management_code: str = Query(..., min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    """手動指定を解除し、全項目を自動判定に戻す。"""
    try:
        deleted = await delete_process_status_override(db, management_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状態の解除に失敗しました: {e}") from e
    if not deleted:
        return {"code": 200, "message": "手動指定はありません"}
    return {"code": 200, "message": "手動指定を解除しました"}

@router.get("/reconcile")
async def reconcile_lot_forecast_attribution(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    run_id: Optional[str] = Query(None),
    canonical_product_cd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = parse_iso_date(start_date)
    pe = parse_iso_date(end_date)
    report = await build_reconcile_report(db, run_id, ps, pe, canonical_product_cd)
    return {"code": 200, "data": report}


@router.post("/batch-summary")
async def batch_forecast_summary(
    body: BatchSummaryBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """切断/面取指示：management_code 一括で主内示帰属日を取得。"""
    data = await get_primary_forecast_summary(db, body.management_codes, body.process_key)
    return {"code": 200, "data": data}


async def trigger_attribution_recompute_for_product(
    db: AsyncSession,
    product_cd: str,
    start_date: date | None = None,
) -> None:
    """钩子用：按品番增量重算（失败不阻断主流程）。"""
    from datetime import timedelta

    try:
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        await recompute_attribution(
            db,
            start_date,
            product_cds=[product_cd],
            modes=["PLAN", "ACTUAL"],
        )
        await db.commit()
    except Exception:
        await db.rollback()

"""ラベル枚数管理 API（複数月ロール対応）"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_master_operation
from app.modules.master.label_quantity_service import (
    LABELS_PER_SHEET,
    SAFETY_FACTOR,
    apply_issue_qty_defaults,
    batch_upsert_label_quantity,
    build_label_quantity_period,
    recalculate_period_roll,
    record_label_print_history,
)

router = APIRouter()


class LabelQuantityItemBody(BaseModel):
    product_cd: str
    year_month: str | None = None
    opening_stock: int = 0
    issue_qty: int = Field(ge=0, default=0)
    issued_qty: int = Field(ge=0, default=0)
    opening_locked: bool = False
    last_issue_history: str | None = None


class LabelQuantityBatchBody(BaseModel):
    label_type: str
    start_month: str
    months: int = Field(default=1, ge=1, le=3)
    items: list[LabelQuantityItemBody] = Field(min_length=1)


class LabelQuantityPeriodBody(BaseModel):
    start_month: str
    months: int = Field(default=1, ge=1, le=3)
    label_type: str
    fill_issue_qty: bool = True
    only_unsaved: bool = False


class LabelQuantityPrintItemBody(BaseModel):
    product_cd: str
    paper_sheets: int = Field(ge=0, default=1)
    labels_per_sheet: int | None = Field(default=None, ge=1)
    label_count: int | None = Field(default=None, ge=0)


class LabelQuantityRecordPrintBody(BaseModel):
    label_type: str
    year_month: str | None = None
    items: list[LabelQuantityPrintItemBody] = Field(min_length=1)


def _user_label(user: User) -> str | None:
    return (
        getattr(user, "username", None)
        or getattr(user, "email", None)
        or str(getattr(user, "id", "") or "")
        or None
    )


def _ok(period: dict, **extra):
    return {
        "success": True,
        "safety_factor": SAFETY_FACTOR,
        "labels_per_sheet": LABELS_PER_SHEET,
        **period,
        **extra,
    }


@router.get("")
async def list_label_quantity(
    start_month: Optional[str] = Query(None, description="開始月 YYYY-MM"),
    year_month: Optional[str] = Query(None, description="互換: 単月 YYYY-MM"),
    months: int = Query(1, ge=1, le=3),
    label_type: str = Query(..., description="molding / product_use"),
    keyword: Optional[str] = Query(None),
    sufficiency: Optional[str] = Query(None),
    supply_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    sm = (start_month or year_month or "").strip()
    if not sm:
        raise HTTPException(status_code=400, detail="start_month または year_month を指定してください")
    try:
        period = await build_label_quantity_period(
            db,
            start_month=sm,
            months=months,
            label_type=label_type,
            keyword=keyword,
            sufficiency=sufficiency,
            supply_type=supply_type,
            apply_roll_preview=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _ok(period)


@router.post("/recalculate")
async def recalculate_label_quantity(
    body: LabelQuantityPeriodBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    try:
        result = await recalculate_period_roll(
            db,
            start_month=body.start_month,
            months=body.months,
            label_type=body.label_type,
            fill_issue_qty=body.fill_issue_qty,
            updated_by=_user_label(current_user),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _ok(
        result,
        message=(
            f"期間再計算完了（月初ロール {result.get('rolled_openings', 0)} /"
            f" 発行更新 {result.get('issue_updated', 0)} / 新規 {result.get('created', 0)}）"
            " ※手動ロック月初は上書きしていません"
        ),
    )


@router.post("/fill-issue-qty")
async def fill_issue_qty(
    body: LabelQuantityPeriodBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    try:
        result = await apply_issue_qty_defaults(
            db,
            start_month=body.start_month,
            months=body.months,
            label_type=body.label_type,
            updated_by=_user_label(current_user),
            only_unsaved=body.only_unsaved,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _ok(
        result,
        message=(
            f"発行予定（紙枚数）を CEIL(max(0,必要−発行済)/{LABELS_PER_SHEET}) で更新しました"
            f"（新規 {result.get('created', 0)} / 更新 {result.get('updated', 0)}）"
        ),
    )


@router.post("/record-print")
async def record_print_history(
    body: LabelQuantityRecordPrintBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """成型用/製品用ラベル印刷後に最終発行・印刷履歴を更新。"""
    try:
        result = await record_label_print_history(
            db,
            label_type=body.label_type,
            year_month=body.year_month,
            items=[item.model_dump() for item in body.items],
            updated_by=_user_label(current_user),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "message": (
            f"印刷履歴を更新しました（新規 {result.get('created', 0)} /"
            f" 更新 {result.get('updated', 0)}）"
        ),
        **result,
        "safety_factor": SAFETY_FACTOR,
        "labels_per_sheet": LABELS_PER_SHEET,
    }


@router.put("/batch")
async def batch_save_label_quantity(
    body: LabelQuantityBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    try:
        result = await batch_upsert_label_quantity(
            db,
            label_type=body.label_type,
            start_month=body.start_month,
            months=body.months,
            items=[item.model_dump() for item in body.items],
            updated_by=_user_label(current_user),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _ok(result, message=f"{result.get('saved', 0)} 件を保存しました")

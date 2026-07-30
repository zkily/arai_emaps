"""生産検討会資料 API"""
from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_inventory_operation
from app.modules.erp.production_review_models import ProductionReviewMeeting
from app.modules.erp.production_review_service import (
    build_meeting_data,
    generate_section_comments,
    get_capacity_rows,
    meeting_from_json,
    meeting_to_json,
    upsert_capacity_rows,
)

router = APIRouter(prefix="/production-review", tags=["生産検討会資料"])

_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


class SaveMeetingBody(BaseModel):
    status: str = Field(default="draft", description="draft/final")
    data: Dict[str, Any]


class CapacityItem(BaseModel):
    process_cd: str
    process_name: str
    equipment_label: Optional[str] = None
    standard_rate: int = 0
    shift_label: Optional[str] = None
    working_days: int = 0
    utilization_rate_pct: float = 96
    plan_adjust_rate_pct: float = 100
    daily_regular_hours: int = 0
    sort_order: int = 0


class CapacityPutBody(BaseModel):
    items: List[CapacityItem]


class WorkingDaysItemIn(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    working_days: int = Field(..., ge=0, le=31)
    remark: Optional[str] = None


class WorkingDaysPutBody(BaseModel):
    items: List[WorkingDaysItemIn] = Field(default_factory=list)


def _validate_month(month: str) -> str:
    m = (month or "").strip()
    if not _MONTH_RE.match(m):
        raise HTTPException(status_code=400, detail="month は YYYY-MM 形式で指定してください")
    return m


def _row_to_dict(row: ProductionReviewMeeting) -> dict:
    data = meeting_from_json(row.data_json or "{}")
    return {
        "id": row.id,
        "target_month": row.target_month,
        "status": row.status,
        "data": data,
        "generated_at": row.generated_at.strftime("%Y-%m-%d %H:%M:%S") if row.generated_at else None,
        "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
        "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else None,
    }


@router.get("/months")
async def list_saved_months(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    rows = list(
        (
            await db.execute(
                select(ProductionReviewMeeting).order_by(ProductionReviewMeeting.target_month.desc())
            )
        ).scalars().all()
    )
    return {
        "success": True,
        "data": [
            {
                "target_month": r.target_month,
                "status": r.status,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None,
            }
            for r in rows
        ],
    }


@router.get("/capacity")
async def get_capacity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    return {"success": True, "data": await get_capacity_rows(db)}


@router.put("/capacity")
async def put_capacity(
    body: CapacityPutBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    items = [it.model_dump() for it in body.items]
    data = await upsert_capacity_rows(db, items)
    return {"success": True, "data": data, "message": f"{len(items)}件の工程能力を保存しました"}


class GenerateCommentsBody(BaseModel):
    kind: str = Field(
        ...,
        description="performance / scrap / inventory / inventory_forecast / load_plan",
    )
    section: Dict[str, Any] = Field(default_factory=dict)


@router.post("/comments/generate")
async def post_generate_comments(
    body: GenerateCommentsBody,
    current_user: User = Depends(require_inventory_operation("edit")),
):
    """現在のセクションデータ（手改含む）からコメントを自動再生成。"""
    _ = current_user
    try:
        comments = generate_section_comments(body.kind, body.section or {})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("コメント自動生成に失敗")
        raise HTTPException(status_code=500, detail=f"コメント生成に失敗しました: {exc}") from exc
    return {"success": True, "data": {"kind": body.kind, "comments": comments}}


@router.get("/inventory-by-date")
async def get_inventory_by_date(
    date: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定日の工程別在庫（千本）。当月在庫列の基準日切替用。"""
    from datetime import date as date_cls

    from app.modules.erp.production_review_service import build_inventory_qty_map_for_date

    _ = current_user
    raw = (date or "").strip()
    try:
        as_of = date_cls.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date は YYYY-MM-DD 形式で指定してください") from exc
    try:
        data = await build_inventory_qty_map_for_date(db, as_of)
    except Exception as exc:
        logger.exception("指定日在庫の取得に失敗")
        raise HTTPException(status_code=500, detail=f"在庫取得に失敗しました: {exc}") from exc
    return {"success": True, "data": data}


@router.get("/working-days")
async def get_working_days(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """月次稼働日（1〜12月）。DB未登録月はカレンダー推計。"""
    from datetime import date as date_cls

    from app.modules.budget.service import get_working_days_map
    from app.modules.erp.production_review_service import _working_days

    _ = current_user
    y = int(year or date_cls.today().year)
    wd_map = await get_working_days_map(db, y)
    items = []
    for m in range(1, 13):
        saved = int(wd_map.get((y, m)) or 0)
        if saved > 0:
            days, source = saved, "saved"
        else:
            days = await _working_days(db, y, m)
            source = "estimated"
        items.append(
            {
                "year": y,
                "month": m,
                "label": f"{y}/{m:02d}",
                "working_days": int(days or 0),
                "source": source,
            }
        )
    return {"success": True, "data": {"year": y, "items": items}}


@router.put("/working-days")
async def put_working_days(
    body: WorkingDaysPutBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    """月次稼働日を保存（budget_working_days に upsert）。在庫率補正・負荷計算で参照。"""
    from app.modules.budget import service as budget_service

    if not body.items:
        raise HTTPException(status_code=400, detail="items が空です")
    updated_by = getattr(current_user, "username", None) or getattr(
        current_user, "full_name", None
    )
    data = await budget_service.upsert_working_days(
        db,
        items=[it.model_dump() for it in body.items],
        updated_by=updated_by,
    )
    return {
        "success": True,
        "data": data,
        "message": f"{len(body.items)}件の稼働日を保存しました",
    }


@router.get("/efficiency-trend")
async def get_efficiency_trend(
    start_month: str,
    end_month: str,
    processes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程別・月次の時間当たり能率推移（折線チャート用）。"""
    from app.modules.erp.production_review_productivity import get_process_efficiency_trend

    start = _validate_month(start_month)
    end = _validate_month(end_month)
    keys = None
    if processes and str(processes).strip():
        keys = [p.strip() for p in str(processes).split(",") if p.strip()]
    try:
        data = await get_process_efficiency_trend(db, start, end, keys)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("時間当たり能率推移の集計に失敗")
        raise HTTPException(status_code=500, detail=f"集計に失敗しました: {exc}") from exc
    return {"success": True, "data": data}


@router.get("/{month}")
async def get_meeting(
    month: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    target_month = _validate_month(month)
    row = (
        await db.execute(
            select(ProductionReviewMeeting).where(ProductionReviewMeeting.target_month == target_month)
        )
    ).scalar_one_or_none()
    if row:
        return {"success": True, "data": _row_to_dict(row), "source": "saved"}
    try:
        data = await build_meeting_data(db, target_month)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("生産検討会資料の集計に失敗")
        raise HTTPException(status_code=500, detail=f"集計に失敗しました: {exc}") from exc
    return {"success": True, "data": {"target_month": target_month, "status": "draft", "data": data}, "source": "computed"}


@router.post("/{month}/recalculate")
async def recalculate_meeting(
    month: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    target_month = _validate_month(month)
    row = (
        await db.execute(
            select(ProductionReviewMeeting).where(ProductionReviewMeeting.target_month == target_month)
        )
    ).scalar_one_or_none()
    existing = meeting_from_json(row.data_json) if row else None
    try:
        data = await build_meeting_data(db, target_month, existing=existing)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("生産検討会資料の再計算に失敗")
        raise HTTPException(status_code=500, detail=f"再計算に失敗しました: {exc}") from exc
    return {"success": True, "data": data, "message": "数値を再計算しました（コメント等の手入力は保持）"}


@router.put("/{month}")
async def save_meeting(
    month: str,
    body: SaveMeetingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    target_month = _validate_month(month)
    if body.data.get("target_month") and body.data["target_month"] != target_month:
        raise HTTPException(status_code=400, detail="data.target_month が URL の month と一致しません")
    status = body.status if body.status in ("draft", "final") else "draft"
    now = datetime.now()
    row = (
        await db.execute(
            select(ProductionReviewMeeting).where(ProductionReviewMeeting.target_month == target_month)
        )
    ).scalar_one_or_none()
    payload = meeting_to_json(body.data)
    if row:
        row.status = status
        row.data_json = payload
        row.generated_at = now
        row.updated_by_user_id = current_user.id
    else:
        row = ProductionReviewMeeting(
            target_month=target_month,
            status=status,
            data_json=payload,
            generated_at=now,
            created_by_user_id=current_user.id,
            updated_by_user_id=current_user.id,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _row_to_dict(row), "message": "保存しました"}


@router.post("/{month}/pptx")
async def download_pptx(
    month: str,
    body: Optional[SaveMeetingBody] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("export")),
):
    target_month = _validate_month(month)
    data: Optional[Dict[str, Any]] = None
    if body and body.data:
        data = body.data
    else:
        row = (
            await db.execute(
                select(ProductionReviewMeeting).where(ProductionReviewMeeting.target_month == target_month)
            )
        ).scalar_one_or_none()
        if row:
            data = meeting_from_json(row.data_json)
        else:
            data = await build_meeting_data(db, target_month)
    try:
        from app.modules.erp.production_review_ppt import build_production_review_pptx

        content = build_production_review_pptx(data)
    except ModuleNotFoundError as exc:
        if exc.name == "pptx":
            raise HTTPException(
                status_code=503,
                detail="PPT生成には python-pptx が必要です。backend venv で pip install python-pptx を実行してください。",
            ) from exc
        raise
    except Exception as exc:
        logger.exception("PPT生成に失敗")
        raise HTTPException(status_code=500, detail=f"PPT生成に失敗しました: {exc}") from exc
    label = (data.get("meta") or {}).get("meeting_month_label") or target_month
    filename = f"{label}生産検討会.pptx"
    encoded = quote(filename)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )

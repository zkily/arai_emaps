"""大量廃棄・保留品記録 API"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_inventory_operation
from app.modules.erp.bulk_disposal_retention_models import BulkDisposalRetentionRecord

router = APIRouter(prefix="/bulk-disposal-retention", tags=["BulkDisposalRetention"])

REPORT_CATEGORIES = ("大量廃棄", "保留品", "その他")
PROCESS_NAMES = ("切断", "面取", "成型", "メッキ", "溶接", "検査", "その他")
HANDLING_STATUSES = ("未処理", "処理済")


class BulkDisposalRetentionBase(BaseModel):
    occurred_date: date
    report_category: str
    process_name: str
    product_cd: Optional[str] = None
    product_name: str
    quantity: int = Field(ge=0)
    handling_status: str = "未処理"
    processed_date: Optional[date] = None
    processing_deadline_date: Optional[date] = None
    management_no: Optional[str] = None
    remarks: Optional[str] = None

    @model_validator(mode="after")
    def validate_retention_deadline(self):
        if self.report_category == "保留品" and self.handling_status == "未処理":
            if not self.processing_deadline_date:
                raise ValueError("保留品の場合、期間内処理期限は必須です")
        return self

    @field_validator("report_category")
    @classmethod
    def validate_report_category(cls, v: str) -> str:
        v = (v or "").strip()
        if v not in REPORT_CATEGORIES:
            raise ValueError(f"report_category は {REPORT_CATEGORIES} のいずれかです")
        return v

    @field_validator("process_name")
    @classmethod
    def validate_process_name(cls, v: str) -> str:
        v = (v or "").strip()
        if v not in PROCESS_NAMES:
            raise ValueError(f"process_name は {PROCESS_NAMES} のいずれかです")
        return v

    @field_validator("handling_status")
    @classmethod
    def validate_handling_status(cls, v: str) -> str:
        v = (v or "").strip()
        if v not in HANDLING_STATUSES:
            raise ValueError(f"handling_status は {HANDLING_STATUSES} のいずれかです")
        return v

    @field_validator("product_name")
    @classmethod
    def validate_product_name(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("product_name は必須です")
        return v


class BulkDisposalRetentionCreate(BulkDisposalRetentionBase):
    pass


class BulkDisposalRetentionUpdate(BulkDisposalRetentionBase):
    pass


class NotifySendBody(BaseModel):
    user_ids: list[int] = Field(min_length=1)
    record_ids: Optional[list[int]] = None


def _parse_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    if not text:
        return None
    return date.fromisoformat(text[:10])


def _is_overdue(row: BulkDisposalRetentionRecord, *, as_of: date | None = None) -> bool:
    if row.report_category != "保留品" or row.handling_status != "未処理":
        return False
    if not row.processing_deadline_date:
        return False
    ref = as_of or date.today()
    return row.processing_deadline_date < ref


def _overdue_filters(as_of: date | None = None):
    ref = as_of or date.today()
    return [
        BulkDisposalRetentionRecord.report_category == "保留品",
        BulkDisposalRetentionRecord.handling_status == "未処理",
        BulkDisposalRetentionRecord.processing_deadline_date.isnot(None),
        BulkDisposalRetentionRecord.processing_deadline_date < ref,
    ]


def _record_to_dict(row: BulkDisposalRetentionRecord) -> dict:
    return {
        "id": row.id,
        "occurred_date": row.occurred_date.isoformat() if row.occurred_date else None,
        "report_category": row.report_category,
        "process_name": row.process_name,
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "quantity": int(row.quantity or 0),
        "handling_status": row.handling_status,
        "processed_date": row.processed_date.isoformat() if row.processed_date else None,
        "processing_deadline_date": (
            row.processing_deadline_date.isoformat() if row.processing_deadline_date else None
        ),
        "is_overdue": _is_overdue(row),
        "management_no": row.management_no,
        "remarks": row.remarks,
        "created_by_user_id": row.created_by_user_id,
        "updated_by_user_id": row.updated_by_user_id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _apply_payload(row: BulkDisposalRetentionRecord, payload: BulkDisposalRetentionBase) -> None:
    row.occurred_date = payload.occurred_date
    row.report_category = payload.report_category
    row.process_name = payload.process_name
    row.product_cd = (payload.product_cd or "").strip() or None
    row.product_name = payload.product_name
    row.quantity = payload.quantity
    row.handling_status = payload.handling_status
    row.processed_date = payload.processed_date
    if payload.report_category == "保留品":
        row.processing_deadline_date = payload.processing_deadline_date
    else:
        row.processing_deadline_date = None
    row.management_no = (payload.management_no or "").strip() or None
    row.remarks = (payload.remarks or "").strip() or None
    if row.handling_status == "処理済" and not row.processed_date:
        row.processed_date = date.today()


@router.get("/options")
async def get_bulk_disposal_retention_options(
    current_user: User = Depends(verify_token_and_get_user),
):
    return {
        "report_categories": list(REPORT_CATEGORIES),
        "process_names": list(PROCESS_NAMES),
        "handling_statuses": list(HANDLING_STATUSES),
    }


@router.get("")
async def list_bulk_disposal_retention_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    occurred_date_from: Optional[str] = Query(None),
    occurred_date_to: Optional[str] = Query(None),
    report_category: Optional[str] = Query(None),
    process_name: Optional[str] = Query(None),
    handling_status: Optional[str] = Query(None),
    product_cd: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    overdue_only: Optional[bool] = Query(None, description="保留品の処理期限超過のみ"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    filters = []
    if occurred_date_from:
        filters.append(BulkDisposalRetentionRecord.occurred_date >= _parse_date(occurred_date_from))
    if occurred_date_to:
        filters.append(BulkDisposalRetentionRecord.occurred_date <= _parse_date(occurred_date_to))
    if report_category:
        filters.append(BulkDisposalRetentionRecord.report_category == report_category.strip())
    if process_name:
        filters.append(BulkDisposalRetentionRecord.process_name == process_name.strip())
    if handling_status:
        filters.append(BulkDisposalRetentionRecord.handling_status == handling_status.strip())
    if product_cd:
        filters.append(BulkDisposalRetentionRecord.product_cd == product_cd.strip())
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        filters.append(
            (BulkDisposalRetentionRecord.product_name.like(kw))
            | (BulkDisposalRetentionRecord.management_no.like(kw))
            | (BulkDisposalRetentionRecord.remarks.like(kw))
        )
    if overdue_only:
        filters.extend(_overdue_filters())

    count_q = select(func.count()).select_from(BulkDisposalRetentionRecord)
    if filters:
        count_q = count_q.where(*filters)
    total = (await db.execute(count_q)).scalar() or 0

    pending_q = select(func.count()).select_from(BulkDisposalRetentionRecord).where(
        BulkDisposalRetentionRecord.handling_status == "未処理"
    )
    pending_total = (await db.execute(pending_q)).scalar() or 0

    overdue_q = select(func.count()).select_from(BulkDisposalRetentionRecord).where(*_overdue_filters())
    overdue_total = (await db.execute(overdue_q)).scalar() or 0

    query = select(BulkDisposalRetentionRecord)
    if filters:
        query = query.where(*filters)
    query = (
        query.order_by(
            BulkDisposalRetentionRecord.occurred_date.desc(),
            BulkDisposalRetentionRecord.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(query)).scalars().all()

    return {
        "list": [_record_to_dict(r) for r in rows],
        "total": int(total),
        "pending_total": int(pending_total),
        "overdue_total": int(overdue_total),
        "page": page,
        "page_size": page_size,
    }


@router.get("/notify/preview")
async def preview_bulk_disposal_retention_notification(
    record_ids: Optional[str] = Query(None, description="カンマ区切り ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("export")),
):
    from app.services.bulk_disposal_retention_notification import (
        get_bulk_disposal_retention_notification_preview,
    )

    ids = None
    if record_ids:
        ids = [int(x.strip()) for x in record_ids.split(",") if x.strip()]
    return await get_bulk_disposal_retention_notification_preview(db, record_ids=ids)


@router.post("/notify/send")
async def send_bulk_disposal_retention_notification_api(
    body: NotifySendBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("export")),
):
    from app.services.bulk_disposal_retention_notification import (
        send_bulk_disposal_retention_notification,
    )

    return await send_bulk_disposal_retention_notification(
        db,
        user_ids=body.user_ids,
        current_user=current_user,
        record_ids=body.record_ids,
    )


@router.get("/overdue-summary")
async def get_bulk_disposal_retention_overdue_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """保留品の期間内処理期限超過（未処理）サマリ（ヘッダー通知用）"""
    today = date.today()
    count_q = select(func.count()).select_from(BulkDisposalRetentionRecord).where(*_overdue_filters(today))
    count = int((await db.execute(count_q)).scalar() or 0)

    list_q = (
        select(BulkDisposalRetentionRecord)
        .where(*_overdue_filters(today))
        .order_by(
            BulkDisposalRetentionRecord.processing_deadline_date.asc(),
            BulkDisposalRetentionRecord.id.asc(),
        )
        .limit(8)
    )
    rows = (await db.execute(list_q)).scalars().all()

    return {
        "as_of": today.isoformat(),
        "count": count,
        "list": [
            {
                "id": r.id,
                "product_name": r.product_name,
                "product_cd": r.product_cd,
                "management_no": r.management_no,
                "processing_deadline_date": (
                    r.processing_deadline_date.isoformat() if r.processing_deadline_date else None
                ),
                "occurred_date": r.occurred_date.isoformat() if r.occurred_date else None,
                "quantity": int(r.quantity or 0),
            }
            for r in rows
        ],
    }


@router.get("/{record_id}")
async def get_bulk_disposal_retention_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(BulkDisposalRetentionRecord, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="記録が見つかりません")
    return _record_to_dict(row)


@router.post("")
async def create_bulk_disposal_retention_record(
    body: BulkDisposalRetentionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("create")),
):
    row = BulkDisposalRetentionRecord()
    _apply_payload(row, body)
    row.created_by_user_id = current_user.id
    row.updated_by_user_id = current_user.id
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _record_to_dict(row)


@router.put("/{record_id}")
async def update_bulk_disposal_retention_record(
    record_id: int,
    body: BulkDisposalRetentionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    row = await db.get(BulkDisposalRetentionRecord, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="記録が見つかりません")
    _apply_payload(row, body)
    row.updated_by_user_id = current_user.id
    await db.commit()
    await db.refresh(row)
    return _record_to_dict(row)


@router.delete("/{record_id}")
async def delete_bulk_disposal_retention_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("delete")),
):
    row = await db.get(BulkDisposalRetentionRecord, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="記録が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}

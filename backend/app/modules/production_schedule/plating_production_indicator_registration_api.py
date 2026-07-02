# coding: utf-8
"""メッキ工程 生産管理指標 手動登録 API（plating_production_indicator CRUD）"""
from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.production_schedule.api import _parse_date_ymd

MANUAL_SOURCE_FILE = "MANUAL_REGISTRATION"
DATA_SOURCE_MANUAL = "manual"
MANUAL_SYNC_PREFIX = "plat_manual:"

INSERT_COLUMNS = [
    "fiscal_year",
    "production_month",
    "production_day",
    "source_line",
    "source_file",
    "planned_quantity",
    "actual_quantity",
    "defect_quantity",
    "defect_plating_scratch",
    "defect_moya_kaburi",
    "defect_nickel",
    "defect_contact",
    "defect_other",
    "shift_hours",
    "maintenance_hours",
    "trouble_hours",
    "choco_stop_hours",
    "planned_stop_hours",
    "available_work_hours",
    "work_hours",
    "work_rate",
    "utilization_rate",
    "total_inspection_qty",
    "efficiency_rate",
    "data_source",
    "external_sync_key",
    "remarks",
]


def _fiscal_year_from_day(d: date) -> int:
    return d.year if d.month >= 4 else d.year - 1


def _to_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        n = float(value)
        return n if n == n else None
    try:
        n = float(str(value).replace(",", "").strip())
        return n if n == n else None
    except (TypeError, ValueError):
        return None


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    for k in ("production_month", "production_day", "created_at", "updated_at"):
        v = item.get(k)
        if isinstance(v, datetime):
            item[k] = v.isoformat()
        elif isinstance(v, date):
            item[k] = v.isoformat()
    for k in (
        "shift_hours",
        "maintenance_hours",
        "trouble_hours",
        "choco_stop_hours",
        "planned_stop_hours",
        "available_work_hours",
        "work_hours",
        "efficiency_rate",
        "utilization_rate",
        "work_rate",
    ):
        v = item.get(k)
        if isinstance(v, Decimal):
            item[k] = float(v)
    return item


def _make_manual_sync_key(*, row_id: int | None = None) -> str:
    token = str(row_id) if row_id is not None else uuid.uuid4().hex
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:40]
    return f"{MANUAL_SYNC_PREFIX}{digest}"


def _compute_metrics(
    *,
    planned: int | None,
    actual: int | None,
    defect: int | None,
    defect_plating_scratch: int | None,
    defect_moya_kaburi: int | None,
    defect_nickel: int | None,
    defect_contact: int | None,
    defect_other: int | None,
    shift_hours: float | None,
    maintenance_hours: float | None,
    trouble_hours: float | None,
    choco_stop_hours: float | None,
    planned_stop_hours: float | None,
) -> dict[str, Any]:
    actual_n = int(actual or 0)
    shift_h = max(0.0, _to_optional_float(shift_hours) or 0.0)
    maint_h = max(0.0, _to_optional_float(maintenance_hours) or 0.0)
    trouble_h = max(0.0, _to_optional_float(trouble_hours) or 0.0)
    choco_h = max(0.0, _to_optional_float(choco_stop_hours) or 0.0)
    planned_stop_h = max(0.0, _to_optional_float(planned_stop_hours) or 0.0)
    loss_h = maint_h + trouble_h + choco_h + planned_stop_h
    available_h = max(0.0, shift_h - loss_h) if shift_h > 0 else None
    work_h = available_h if available_h and available_h > 0 else None

    efficiency = None
    if actual_n > 0 and work_h and work_h > 0:
        efficiency = round(actual_n / work_h, 1)

    utilization = round(work_h / shift_h, 4) if shift_h > 0 and work_h is not None else None
    work_rate = round(work_h / available_h, 4) if available_h and available_h > 0 and work_h is not None else None

    defect_sum = sum(
        int(x or 0)
        for x in (
            defect_plating_scratch,
            defect_moya_kaburi,
            defect_nickel,
            defect_contact,
            defect_other,
        )
    )
    defect_total = int(defect) if defect is not None else (defect_sum if defect_sum > 0 else None)

    return {
        "planned_quantity": int(planned) if planned is not None else None,
        "actual_quantity": actual_n if actual is not None else None,
        "defect_quantity": defect_total,
        "defect_plating_scratch": int(defect_plating_scratch) if defect_plating_scratch is not None else None,
        "defect_moya_kaburi": int(defect_moya_kaburi) if defect_moya_kaburi is not None else None,
        "defect_nickel": int(defect_nickel) if defect_nickel is not None else None,
        "defect_contact": int(defect_contact) if defect_contact is not None else None,
        "defect_other": int(defect_other) if defect_other is not None else None,
        "shift_hours": round(shift_h, 3) if shift_h > 0 else None,
        "maintenance_hours": round(maint_h, 3) if maint_h > 0 else None,
        "trouble_hours": round(trouble_h, 3) if trouble_h > 0 else None,
        "choco_stop_hours": round(choco_h, 3) if choco_h > 0 else None,
        "planned_stop_hours": round(planned_stop_h, 3) if planned_stop_h > 0 else None,
        "available_work_hours": round(available_h, 3) if available_h and available_h > 0 else None,
        "work_hours": round(work_h, 3) if work_h and work_h > 0 else None,
        "utilization_rate": utilization,
        "work_rate": work_rate,
        "total_inspection_qty": actual_n if actual_n > 0 else None,
        "efficiency_rate": efficiency,
    }


class PlatingIndicatorManualBody(BaseModel):
    production_day: str
    planned_quantity: Optional[int] = None
    actual_quantity: Optional[int] = None
    defect_quantity: Optional[int] = None
    defect_plating_scratch: Optional[int] = None
    defect_moya_kaburi: Optional[int] = None
    defect_nickel: Optional[int] = None
    defect_contact: Optional[int] = None
    defect_other: Optional[int] = None
    shift_hours: Optional[float] = None
    maintenance_hours: Optional[float] = None
    trouble_hours: Optional[float] = None
    choco_stop_hours: Optional[float] = None
    planned_stop_hours: Optional[float] = None
    remarks: Optional[str] = None


class PlatingIndicatorPatchBody(PlatingIndicatorManualBody):
    production_day: Optional[str] = None


def _assert_manual_row(row: dict[str, Any]) -> None:
    if (row.get("data_source") or "").strip().lower() != DATA_SOURCE_MANUAL:
        raise HTTPException(status_code=403, detail="Excel/CSV 取込データは手動編集できません")


async def _assert_no_duplicate_manual_day(
    db: AsyncSession,
    day: date,
    *,
    exclude_id: int | None = None,
) -> None:
    sql = """
        SELECT id FROM plating_production_indicator
        WHERE production_day = :production_day AND data_source = :data_source
    """
    params: dict[str, Any] = {"production_day": day, "data_source": DATA_SOURCE_MANUAL}
    if exclude_id is not None:
        sql += " AND id <> :exclude_id"
        params["exclude_id"] = exclude_id
    sql += " LIMIT 1"
    result = await db.execute(text(sql), params)
    if result.fetchone():
        raise HTTPException(status_code=400, detail="この生産日の手動登録は既に存在します")


def register_registration_routes(router: APIRouter) -> None:
    @router.get("/plan/plating-production-indicator/list")
    async def list_plating_production_indicators(
        production_day: str = Query(..., description="生産日 YYYY-MM-DD"),
        limit: int = Query(200, ge=1, le=500),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        day = _parse_date_ymd(production_day)
        if day is None:
            raise HTTPException(status_code=400, detail="生産日が不正です")
        sql = """
            SELECT id, fiscal_year, production_month, production_day, source_line, source_file,
                   planned_quantity, actual_quantity, defect_quantity,
                   defect_plating_scratch, defect_moya_kaburi, defect_nickel,
                   defect_contact, defect_other,
                   shift_hours, maintenance_hours, trouble_hours, choco_stop_hours,
                   planned_stop_hours, available_work_hours, work_hours,
                   work_rate, utilization_rate, total_inspection_qty, efficiency_rate,
                   data_source, external_sync_key, remarks, created_at, updated_at
            FROM plating_production_indicator
            WHERE production_day = :production_day
            ORDER BY data_source ASC, id ASC
            LIMIT :lim
        """
        try:
            result = await db.execute(text(sql), {"production_day": day, "lim": limit})
            rows = [_normalize_row(dict(r)) for r in result.mappings().all()]
        except Exception as e:
            msg = str(e).lower()
            if "plating_production_indicator" in msg and (
                "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
            ):
                raise HTTPException(status_code=503, detail="plating_production_indicator テーブルが存在しません") from e
            raise HTTPException(status_code=500, detail=str(e)) from e
        return {"success": True, "data": rows}

    @router.post("/plan/plating-production-indicator/manual")
    async def create_plating_production_indicator_manual(
        body: PlatingIndicatorManualBody,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        day = _parse_date_ymd(body.production_day)
        if day is None:
            raise HTTPException(status_code=400, detail="生産日が不正です")
        await _assert_no_duplicate_manual_day(db, day)

        metrics = _compute_metrics(
            planned=body.planned_quantity,
            actual=body.actual_quantity,
            defect=body.defect_quantity,
            defect_plating_scratch=body.defect_plating_scratch,
            defect_moya_kaburi=body.defect_moya_kaburi,
            defect_nickel=body.defect_nickel,
            defect_contact=body.defect_contact,
            defect_other=body.defect_other,
            shift_hours=body.shift_hours,
            maintenance_hours=body.maintenance_hours,
            trouble_hours=body.trouble_hours,
            choco_stop_hours=body.choco_stop_hours,
            planned_stop_hours=body.planned_stop_hours,
        )
        actual_qty = int(metrics.get("actual_quantity") or 0)
        if actual_qty <= 0:
            raise HTTPException(status_code=400, detail="実績数を入力してください")

        sync_key = _make_manual_sync_key()
        params = {
            "fiscal_year": _fiscal_year_from_day(day),
            "production_month": day.replace(day=1),
            "production_day": day,
            "source_line": None,
            "source_file": MANUAL_SOURCE_FILE,
            "data_source": DATA_SOURCE_MANUAL,
            "external_sync_key": sync_key,
            "remarks": (body.remarks or "").strip() or None,
            **metrics,
        }
        placeholders = ", ".join([f":{c}" for c in INSERT_COLUMNS])
        sql = f"INSERT INTO plating_production_indicator ({', '.join(INSERT_COLUMNS)}) VALUES ({placeholders})"
        try:
            result = await db.execute(text(sql), params)
            await db.commit()
            new_id = result.lastrowid
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        fetch = await db.execute(
            text("SELECT * FROM plating_production_indicator WHERE id = :id"),
            {"id": new_id},
        )
        row = fetch.mappings().first()
        return {"success": True, "data": _normalize_row(dict(row)) if row else {"id": new_id}}

    @router.patch("/plan/plating-production-indicator/{row_id}")
    async def patch_plating_production_indicator(
        row_id: int,
        body: PlatingIndicatorPatchBody,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        existing = await db.execute(
            text("SELECT * FROM plating_production_indicator WHERE id = :id"),
            {"id": row_id},
        )
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="データが見つかりません")
        current = dict(row)
        _assert_manual_row(current)

        day = _parse_date_ymd(body.production_day) if body.production_day else current.get("production_day")
        if isinstance(day, str):
            day = _parse_date_ymd(day)
        if day is None:
            raise HTTPException(status_code=400, detail="生産日が不正です")
        await _assert_no_duplicate_manual_day(db, day, exclude_id=row_id)

        def pick_int(field: str, body_val: int | None) -> int | None:
            if body_val is not None:
                return body_val
            v = current.get(field)
            return int(v) if v is not None else None

        def pick_float(field: str, body_val: float | None) -> float | None:
            if body_val is not None:
                return body_val
            v = current.get(field)
            return float(v) if v is not None else None

        metrics = _compute_metrics(
            planned=pick_int("planned_quantity", body.planned_quantity),
            actual=pick_int("actual_quantity", body.actual_quantity),
            defect=pick_int("defect_quantity", body.defect_quantity),
            defect_plating_scratch=pick_int("defect_plating_scratch", body.defect_plating_scratch),
            defect_moya_kaburi=pick_int("defect_moya_kaburi", body.defect_moya_kaburi),
            defect_nickel=pick_int("defect_nickel", body.defect_nickel),
            defect_contact=pick_int("defect_contact", body.defect_contact),
            defect_other=pick_int("defect_other", body.defect_other),
            shift_hours=pick_float("shift_hours", body.shift_hours),
            maintenance_hours=pick_float("maintenance_hours", body.maintenance_hours),
            trouble_hours=pick_float("trouble_hours", body.trouble_hours),
            choco_stop_hours=pick_float("choco_stop_hours", body.choco_stop_hours),
            planned_stop_hours=pick_float("planned_stop_hours", body.planned_stop_hours),
        )

        params = {
            "id": row_id,
            "fiscal_year": _fiscal_year_from_day(day),
            "production_month": day.replace(day=1),
            "production_day": day,
            "remarks": (body.remarks if body.remarks is not None else current.get("remarks")),
            **metrics,
        }
        sql = """
            UPDATE plating_production_indicator SET
              fiscal_year = :fiscal_year,
              production_month = :production_month,
              production_day = :production_day,
              planned_quantity = :planned_quantity,
              actual_quantity = :actual_quantity,
              defect_quantity = :defect_quantity,
              defect_plating_scratch = :defect_plating_scratch,
              defect_moya_kaburi = :defect_moya_kaburi,
              defect_nickel = :defect_nickel,
              defect_contact = :defect_contact,
              defect_other = :defect_other,
              shift_hours = :shift_hours,
              maintenance_hours = :maintenance_hours,
              trouble_hours = :trouble_hours,
              choco_stop_hours = :choco_stop_hours,
              planned_stop_hours = :planned_stop_hours,
              available_work_hours = :available_work_hours,
              work_hours = :work_hours,
              work_rate = :work_rate,
              utilization_rate = :utilization_rate,
              total_inspection_qty = :total_inspection_qty,
              efficiency_rate = :efficiency_rate,
              remarks = :remarks
            WHERE id = :id
        """
        try:
            await db.execute(text(sql), params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        fetch = await db.execute(
            text("SELECT * FROM plating_production_indicator WHERE id = :id"),
            {"id": row_id},
        )
        updated = fetch.mappings().first()
        return {"success": True, "data": _normalize_row(dict(updated)) if updated else None}

    @router.delete("/plan/plating-production-indicator/{row_id}")
    async def delete_plating_production_indicator(
        row_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        existing = await db.execute(
            text("SELECT id, data_source FROM plating_production_indicator WHERE id = :id"),
            {"id": row_id},
        )
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="データが見つかりません")
        _assert_manual_row(dict(row))
        try:
            await db.execute(
                text("DELETE FROM plating_production_indicator WHERE id = :id"),
                {"id": row_id},
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        return {"success": True, "message": "削除しました"}

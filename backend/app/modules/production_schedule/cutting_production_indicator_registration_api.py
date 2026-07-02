# coding: utf-8
"""切断工程 生産管理指標 手動登録 API（cutting_production_indicator CRUD）"""
from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.production_schedule.api import _parse_date_ymd

MANUAL_SOURCE_FILE = "MANUAL_REGISTRATION"
DATA_SOURCE_MANUAL = "manual"
MANUAL_SYNC_PREFIX = "cut_manual:"

INSERT_COLUMNS = [
    "fiscal_year",
    "production_month",
    "production_day",
    "source_line",
    "source_file",
    "product_cd",
    "production_line",
    "product_name",
    "planned_quantity",
    "actual_quantity",
    "quantity_variance",
    "shift_hours",
    "break_hours",
    "setup_hours",
    "repair_hours",
    "saw_blade_exchange_hours",
    "loss_stop_day_hours",
    "loss_stop_night_hours",
    "invisible_loss_stop_hours",
    "planned_stop_hours",
    "available_work_hours",
    "work_hours",
    "utilization_rate",
    "work_rate",
    "total_production_qty",
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
    for k in ("production_month", "production_day", "forming_process_date", "created_at", "updated_at"):
        v = item.get(k)
        if isinstance(v, datetime):
            item[k] = v.isoformat()
        elif isinstance(v, date):
            item[k] = v.isoformat()
    for k in (
        "shift_hours",
        "break_hours",
        "setup_hours",
        "repair_hours",
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
    variance: int | None,
    shift_hours: float | None,
    break_hours: float | None,
    setup_hours: float | None,
) -> dict[str, Any]:
    planned_n = int(planned or 0)
    actual_n = int(actual or 0)
    if variance is None:
        variance_n = planned_n - actual_n if planned_n > 0 else None
    else:
        variance_n = int(variance)

    shift_h = max(0.0, _to_optional_float(shift_hours) or 0.0)
    break_h = max(0.0, _to_optional_float(break_hours) or 0.0)
    setup_h = max(0.0, _to_optional_float(setup_hours) or 0.0)
    work_h = max(0.0, shift_h - break_h - setup_h) if shift_h > 0 else None
    available_h = max(0.0, shift_h - break_h) if shift_h > 0 else None

    efficiency = None
    if actual_n > 0 and work_h and work_h > 0:
        efficiency = round(actual_n / work_h, 2)

    utilization = round(work_h / shift_h, 4) if shift_h > 0 and work_h is not None else None
    work_rate = round(work_h / available_h, 4) if available_h and available_h > 0 and work_h is not None else None

    return {
        "planned_quantity": planned_n if planned is not None else None,
        "actual_quantity": actual_n,
        "quantity_variance": variance_n,
        "shift_hours": round(shift_h, 3) if shift_h > 0 else None,
        "break_hours": round(break_h, 3) if break_h > 0 else None,
        "setup_hours": round(setup_h, 3) if setup_h > 0 else None,
        "available_work_hours": round(available_h, 3) if available_h and available_h > 0 else None,
        "work_hours": round(work_h, 3) if work_h and work_h > 0 else None,
        "utilization_rate": utilization,
        "work_rate": work_rate,
        "total_production_qty": actual_n if actual_n > 0 else None,
        "efficiency_rate": efficiency,
    }


class CuttingIndicatorManualBody(BaseModel):
    production_day: str
    production_line: str
    product_cd: str
    product_name: Optional[str] = None
    planned_quantity: Optional[int] = None
    actual_quantity: int = Field(..., ge=0)
    quantity_variance: Optional[int] = None
    shift_hours: Optional[float] = None
    break_hours: Optional[float] = None
    setup_hours: Optional[float] = None
    remarks: Optional[str] = None


class CuttingIndicatorPatchBody(CuttingIndicatorManualBody):
    production_day: Optional[str] = None
    production_line: Optional[str] = None
    product_cd: Optional[str] = None
    actual_quantity: Optional[int] = Field(None, ge=0)


def _assert_manual_row(row: dict[str, Any]) -> None:
    if (row.get("data_source") or "").strip().lower() != DATA_SOURCE_MANUAL:
        raise HTTPException(status_code=403, detail="Excel/CSV 取込データは手動編集できません")


def register_registration_routes(router: APIRouter) -> None:
    @router.get("/plan/cutting-production-indicator/list")
    async def list_cutting_production_indicators(
        production_day: str = Query(..., description="生産日 YYYY-MM-DD"),
        production_line: Optional[str] = Query(None, description="ライン名"),
        limit: int = Query(2000, ge=1, le=5000),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        day = _parse_date_ymd(production_day)
        if day is None:
            raise HTTPException(status_code=400, detail="生産日が不正です")
        where = ["production_day = :production_day"]
        params: dict[str, Any] = {"production_day": day, "lim": limit}
        line_norm = (production_line or "").strip()
        if line_norm:
            where.append("production_line = :production_line")
            params["production_line"] = line_norm
        sql = f"""
            SELECT id, fiscal_year, production_month, production_day, source_line, source_file,
                   product_cd, production_line, product_name,
                   planned_quantity, actual_quantity, quantity_variance,
                   shift_hours, break_hours, setup_hours, repair_hours,
                   saw_blade_exchange_hours, loss_stop_day_hours, loss_stop_night_hours,
                   invisible_loss_stop_hours, planned_stop_hours, available_work_hours,
                   work_hours, utilization_rate, work_rate, total_production_qty,
                   efficiency_rate, data_source, external_sync_key, remarks,
                   created_at, updated_at
            FROM cutting_production_indicator
            WHERE {' AND '.join(where)}
            ORDER BY production_line ASC, product_cd ASC, id ASC
            LIMIT :lim
        """
        try:
            result = await db.execute(text(sql), params)
            rows = [_normalize_row(dict(r)) for r in result.mappings().all()]
        except Exception as e:
            msg = str(e).lower()
            if "cutting_production_indicator" in msg and (
                "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
            ):
                raise HTTPException(status_code=503, detail="cutting_production_indicator テーブルが存在しません") from e
            raise HTTPException(status_code=500, detail=str(e)) from e
        return {"success": True, "data": rows}

    @router.post("/plan/cutting-production-indicator/manual")
    async def create_cutting_production_indicator_manual(
        body: CuttingIndicatorManualBody,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        day = _parse_date_ymd(body.production_day)
        if day is None:
            raise HTTPException(status_code=400, detail="生産日が不正です")
        line = (body.production_line or "").strip()
        product_cd = (body.product_cd or "").strip()
        if not line:
            raise HTTPException(status_code=400, detail="ラインを指定してください")
        if not product_cd:
            raise HTTPException(status_code=400, detail="製品CDを指定してください")

        metrics = _compute_metrics(
            planned=body.planned_quantity,
            actual=body.actual_quantity,
            variance=body.quantity_variance,
            shift_hours=body.shift_hours,
            break_hours=body.break_hours,
            setup_hours=body.setup_hours,
        )
        sync_key = _make_manual_sync_key()
        params = {
            "fiscal_year": _fiscal_year_from_day(day),
            "production_month": day.replace(day=1),
            "production_day": day,
            "source_line": None,
            "source_file": MANUAL_SOURCE_FILE,
            "product_cd": product_cd,
            "production_line": line,
            "product_name": (body.product_name or "").strip() or product_cd,
            "data_source": DATA_SOURCE_MANUAL,
            "external_sync_key": sync_key,
            "remarks": (body.remarks or "").strip() or None,
            **metrics,
        }
        placeholders = ", ".join([f":{c}" for c in INSERT_COLUMNS])
        sql = f"INSERT INTO cutting_production_indicator ({', '.join(INSERT_COLUMNS)}) VALUES ({placeholders})"
        try:
            result = await db.execute(text(sql), params)
            await db.commit()
            new_id = result.lastrowid
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        fetch = await db.execute(
            text("SELECT * FROM cutting_production_indicator WHERE id = :id"),
            {"id": new_id},
        )
        row = fetch.mappings().first()
        return {"success": True, "data": _normalize_row(dict(row)) if row else {"id": new_id}}

    @router.patch("/plan/cutting-production-indicator/{row_id}")
    async def patch_cutting_production_indicator(
        row_id: int,
        body: CuttingIndicatorPatchBody,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        existing = await db.execute(
            text("SELECT * FROM cutting_production_indicator WHERE id = :id"),
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

        line = (body.production_line or current.get("production_line") or "").strip()
        product_cd = (body.product_cd or current.get("product_cd") or "").strip()
        if not line or not product_cd:
            raise HTTPException(status_code=400, detail="ラインと製品CDは必須です")

        actual = body.actual_quantity if body.actual_quantity is not None else current.get("actual_quantity")
        planned = body.planned_quantity if body.planned_quantity is not None else current.get("planned_quantity")
        variance = body.quantity_variance if body.quantity_variance is not None else current.get("quantity_variance")
        shift_h = body.shift_hours if body.shift_hours is not None else current.get("shift_hours")
        break_h = body.break_hours if body.break_hours is not None else current.get("break_hours")
        setup_h = body.setup_hours if body.setup_hours is not None else current.get("setup_hours")

        metrics = _compute_metrics(
            planned=int(planned) if planned is not None else None,
            actual=int(actual or 0),
            variance=int(variance) if variance is not None else None,
            shift_hours=shift_h,
            break_hours=break_h,
            setup_hours=setup_h,
        )

        params = {
            "id": row_id,
            "fiscal_year": _fiscal_year_from_day(day),
            "production_month": day.replace(day=1),
            "production_day": day,
            "product_cd": product_cd,
            "production_line": line,
            "product_name": (body.product_name or current.get("product_name") or product_cd),
            "remarks": (body.remarks if body.remarks is not None else current.get("remarks")),
            **metrics,
        }
        sql = """
            UPDATE cutting_production_indicator SET
              fiscal_year = :fiscal_year,
              production_month = :production_month,
              production_day = :production_day,
              product_cd = :product_cd,
              production_line = :production_line,
              product_name = :product_name,
              planned_quantity = :planned_quantity,
              actual_quantity = :actual_quantity,
              quantity_variance = :quantity_variance,
              shift_hours = :shift_hours,
              break_hours = :break_hours,
              setup_hours = :setup_hours,
              available_work_hours = :available_work_hours,
              work_hours = :work_hours,
              utilization_rate = :utilization_rate,
              work_rate = :work_rate,
              total_production_qty = :total_production_qty,
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
            text("SELECT * FROM cutting_production_indicator WHERE id = :id"),
            {"id": row_id},
        )
        updated = fetch.mappings().first()
        return {"success": True, "data": _normalize_row(dict(updated)) if updated else None}

    @router.delete("/plan/cutting-production-indicator/{row_id}")
    async def delete_cutting_production_indicator(
        row_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        existing = await db.execute(
            text("SELECT id, data_source FROM cutting_production_indicator WHERE id = :id"),
            {"id": row_id},
        )
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="データが見つかりません")
        _assert_manual_row(dict(row))
        try:
            await db.execute(
                text("DELETE FROM cutting_production_indicator WHERE id = :id"),
                {"id": row_id},
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        return {"success": True, "message": "削除しました"}

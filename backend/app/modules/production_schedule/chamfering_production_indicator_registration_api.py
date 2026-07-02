# coding: utf-8
"""面取工程 生産管理指標 手動登録 API（chamfering_production_indicator CRUD）"""
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
MANUAL_SYNC_PREFIX = "cham_manual:"

INSERT_COLUMNS = [
    "fiscal_year",
    "production_month",
    "production_day",
    "source_line",
    "source_file",
    "product_cd",
    "production_line",
    "product_name",
    "chamfer_planned_quantity",
    "chamfer_actual_quantity",
    "chamfer_defect_quantity",
    "sw_planned_quantity",
    "sw_actual_quantity",
    "sw_defect_quantity",
    "shift_hours",
    "break_hours",
    "setup_hours",
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
    chamfer_planned: int | None,
    chamfer_actual: int | None,
    chamfer_defect: int | None,
    sw_planned: int | None,
    sw_actual: int | None,
    sw_defect: int | None,
    shift_hours: float | None,
    break_hours: float | None,
    setup_hours: float | None,
) -> dict[str, Any]:
    chamfer_a = int(chamfer_actual or 0)
    sw_a = int(sw_actual or 0)
    total = chamfer_a + sw_a

    shift_h = max(0.0, _to_optional_float(shift_hours) or 0.0)
    break_h = max(0.0, _to_optional_float(break_hours) or 0.0)
    setup_h = max(0.0, _to_optional_float(setup_hours) or 0.0)
    pause_h = break_h + setup_h
    work_h = max(0.0, shift_h - pause_h) if shift_h > 0 else None
    available_h = max(0.0, shift_h - break_h) if shift_h > 0 else None

    efficiency = None
    if total > 0 and work_h and work_h > 0:
        efficiency = round(total / work_h, 2)

    utilization = round(work_h / shift_h, 4) if shift_h > 0 and work_h is not None else None
    work_rate = round(work_h / available_h, 4) if available_h and available_h > 0 and work_h is not None else None

    return {
        "chamfer_planned_quantity": int(chamfer_planned) if chamfer_planned is not None else None,
        "chamfer_actual_quantity": chamfer_a if chamfer_actual is not None else None,
        "chamfer_defect_quantity": int(chamfer_defect) if chamfer_defect is not None else None,
        "sw_planned_quantity": int(sw_planned) if sw_planned is not None else None,
        "sw_actual_quantity": sw_a if sw_actual is not None else None,
        "sw_defect_quantity": int(sw_defect) if sw_defect is not None else None,
        "shift_hours": round(shift_h, 3) if shift_h > 0 else None,
        "break_hours": round(break_h, 3) if break_h > 0 else None,
        "setup_hours": round(setup_h, 3) if setup_h > 0 else None,
        "available_work_hours": round(available_h, 3) if available_h and available_h > 0 else None,
        "work_hours": round(work_h, 3) if work_h and work_h > 0 else None,
        "utilization_rate": utilization,
        "work_rate": work_rate,
        "total_production_qty": total if total > 0 else None,
        "efficiency_rate": efficiency,
    }


class ChamferingIndicatorManualBody(BaseModel):
    production_day: str
    production_line: str
    product_cd: str
    product_name: Optional[str] = None
    chamfer_planned_quantity: Optional[int] = None
    chamfer_actual_quantity: Optional[int] = None
    chamfer_defect_quantity: Optional[int] = None
    sw_planned_quantity: Optional[int] = None
    sw_actual_quantity: Optional[int] = None
    sw_defect_quantity: Optional[int] = None
    shift_hours: Optional[float] = None
    break_hours: Optional[float] = None
    setup_hours: Optional[float] = None
    remarks: Optional[str] = None


class ChamferingIndicatorPatchBody(ChamferingIndicatorManualBody):
    production_day: Optional[str] = None
    production_line: Optional[str] = None
    product_cd: Optional[str] = None


def _assert_manual_row(row: dict[str, Any]) -> None:
    if (row.get("data_source") or "").strip().lower() != DATA_SOURCE_MANUAL:
        raise HTTPException(status_code=403, detail="Excel/CSV 取込データは手動編集できません")


def register_registration_routes(router: APIRouter) -> None:
    @router.get("/plan/chamfering-production-indicator/list")
    async def list_chamfering_production_indicators(
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
                   chamfer_planned_quantity, chamfer_actual_quantity, chamfer_defect_quantity,
                   sw_planned_quantity, sw_actual_quantity, sw_defect_quantity,
                   shift_hours, break_hours, setup_hours, repair_hours, adjustment_hours,
                   choco_stop_hours, planned_stop_hours, available_work_hours,
                   work_hours, utilization_rate, work_rate, total_production_qty,
                   efficiency_rate, data_source, external_sync_key, remarks,
                   created_at, updated_at
            FROM chamfering_production_indicator
            WHERE {' AND '.join(where)}
            ORDER BY production_line ASC, product_cd ASC, id ASC
            LIMIT :lim
        """
        try:
            result = await db.execute(text(sql), params)
            rows = [_normalize_row(dict(r)) for r in result.mappings().all()]
        except Exception as e:
            msg = str(e).lower()
            if "chamfering_production_indicator" in msg and (
                "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
            ):
                raise HTTPException(status_code=503, detail="chamfering_production_indicator テーブルが存在しません") from e
            raise HTTPException(status_code=500, detail=str(e)) from e
        return {"success": True, "data": rows}

    @router.post("/plan/chamfering-production-indicator/manual")
    async def create_chamfering_production_indicator_manual(
        body: ChamferingIndicatorManualBody,
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
            chamfer_planned=body.chamfer_planned_quantity,
            chamfer_actual=body.chamfer_actual_quantity,
            chamfer_defect=body.chamfer_defect_quantity,
            sw_planned=body.sw_planned_quantity,
            sw_actual=body.sw_actual_quantity,
            sw_defect=body.sw_defect_quantity,
            shift_hours=body.shift_hours,
            break_hours=body.break_hours,
            setup_hours=body.setup_hours,
        )
        total_qty = int(metrics.get("total_production_qty") or 0)
        if total_qty <= 0:
            raise HTTPException(status_code=400, detail="面取またはSWの生産数を入力してください")
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
        sql = f"INSERT INTO chamfering_production_indicator ({', '.join(INSERT_COLUMNS)}) VALUES ({placeholders})"
        try:
            result = await db.execute(text(sql), params)
            await db.commit()
            new_id = result.lastrowid
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        fetch = await db.execute(
            text("SELECT * FROM chamfering_production_indicator WHERE id = :id"),
            {"id": new_id},
        )
        row = fetch.mappings().first()
        return {"success": True, "data": _normalize_row(dict(row)) if row else {"id": new_id}}

    @router.patch("/plan/chamfering-production-indicator/{row_id}")
    async def patch_chamfering_production_indicator(
        row_id: int,
        body: ChamferingIndicatorPatchBody,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        existing = await db.execute(
            text("SELECT * FROM chamfering_production_indicator WHERE id = :id"),
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

        chamfer_actual = (
            body.chamfer_actual_quantity
            if body.chamfer_actual_quantity is not None
            else current.get("chamfer_actual_quantity")
        )
        sw_actual = (
            body.sw_actual_quantity if body.sw_actual_quantity is not None else current.get("sw_actual_quantity")
        )
        chamfer_planned = (
            body.chamfer_planned_quantity
            if body.chamfer_planned_quantity is not None
            else current.get("chamfer_planned_quantity")
        )
        sw_planned = (
            body.sw_planned_quantity if body.sw_planned_quantity is not None else current.get("sw_planned_quantity")
        )
        chamfer_defect = (
            body.chamfer_defect_quantity
            if body.chamfer_defect_quantity is not None
            else current.get("chamfer_defect_quantity")
        )
        sw_defect = (
            body.sw_defect_quantity if body.sw_defect_quantity is not None else current.get("sw_defect_quantity")
        )
        shift_h = body.shift_hours if body.shift_hours is not None else current.get("shift_hours")
        break_h = body.break_hours if body.break_hours is not None else current.get("break_hours")
        setup_h = body.setup_hours if body.setup_hours is not None else current.get("setup_hours")

        metrics = _compute_metrics(
            chamfer_planned=int(chamfer_planned) if chamfer_planned is not None else None,
            chamfer_actual=int(chamfer_actual) if chamfer_actual is not None else None,
            chamfer_defect=int(chamfer_defect) if chamfer_defect is not None else None,
            sw_planned=int(sw_planned) if sw_planned is not None else None,
            sw_actual=int(sw_actual) if sw_actual is not None else None,
            sw_defect=int(sw_defect) if sw_defect is not None else None,
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
            UPDATE chamfering_production_indicator SET
              fiscal_year = :fiscal_year,
              production_month = :production_month,
              production_day = :production_day,
              product_cd = :product_cd,
              production_line = :production_line,
              product_name = :product_name,
              chamfer_planned_quantity = :chamfer_planned_quantity,
              chamfer_actual_quantity = :chamfer_actual_quantity,
              chamfer_defect_quantity = :chamfer_defect_quantity,
              sw_planned_quantity = :sw_planned_quantity,
              sw_actual_quantity = :sw_actual_quantity,
              sw_defect_quantity = :sw_defect_quantity,
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
            text("SELECT * FROM chamfering_production_indicator WHERE id = :id"),
            {"id": row_id},
        )
        updated = fetch.mappings().first()
        return {"success": True, "data": _normalize_row(dict(updated)) if updated else None}

    @router.delete("/plan/chamfering-production-indicator/{row_id}")
    async def delete_chamfering_production_indicator(
        row_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        existing = await db.execute(
            text("SELECT id, data_source FROM chamfering_production_indicator WHERE id = :id"),
            {"id": row_id},
        )
        row = existing.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="データが見つかりません")
        _assert_manual_row(dict(row))
        try:
            await db.execute(
                text("DELETE FROM chamfering_production_indicator WHERE id = :id"),
                {"id": row_id},
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e)) from e
        return {"success": True, "message": "削除しました"}

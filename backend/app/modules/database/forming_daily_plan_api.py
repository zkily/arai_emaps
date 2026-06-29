"""
工程別計画試算（FormingDailyPlanSummary）API
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_aps_operation
from app.modules.auth.models import User
from app.modules.database.forming_daily_plan_service import (
    apply_scenario_to_summary,
    build_order_matrix_for_period,
    build_summary,
    parse_iso_date,
)
from app.modules.database.order_forecast_service import build_order_forecast

router = APIRouter(tags=["forming-daily-plan"])

ALLOWED_PROCESS_KEYS = frozenset(
    {
        "cutting",
        "chamfering",
        "molding",
        "plating",
        "outsourced_plating",
        "welding",
        "outsourced_welding",
        "inspection",
        "outsourced_warehouse",
    }
)


class ProcessRunCalendarItem(BaseModel):
    process_key: str = Field(..., max_length=32)
    dates: List[str] = Field(default_factory=list)


class ProcessRunCalendarPutBody(BaseModel):
    startDate: str
    endDate: str
    items: List[ProcessRunCalendarItem]


class SimulateBody(BaseModel):
    startDate: str
    endDate: str
    productCds: Optional[List[str]] = None
    processOverrides: Optional[Dict[str, Dict[str, Dict[str, int]]]] = None
    runCalendarItems: Optional[List[ProcessRunCalendarItem]] = None
    includeForecastMonths: bool = False
    baseMonth: Optional[str] = None
    includeOrderMatrix: bool = False


class ScenarioCreateBody(BaseModel):
    name: str = Field(..., max_length=128)
    startDate: str
    endDate: str
    baseMonth: str
    includeForecastMonths: bool = True
    processOverrides: Optional[Dict[str, Dict[str, Dict[str, int]]]] = None
    runCalendarItems: Optional[List[ProcessRunCalendarItem]] = None
    notes: Optional[str] = None


class ScenarioUpdateBody(BaseModel):
    name: Optional[str] = None
    processOverrides: Optional[Dict[str, Dict[str, Dict[str, int]]]] = None
    runCalendarItems: Optional[List[ProcessRunCalendarItem]] = None
    includeForecastMonths: Optional[bool] = None
    notes: Optional[str] = None


def _parse_iso_date(label: str, value: str) -> date:
    s = (value or "").strip()[:10]
    if len(s) != 10 or s[4] != "-" or s[7] != "-":
        raise HTTPException(status_code=400, detail=f"{label} は YYYY-MM-DD 形式で指定してください")
    try:
        y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
        return date(y, m, d)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{label} が不正な日付です")


def _daterange_inclusive(ps: date, pe: date) -> set[date]:
    out: set[date] = set()
    cur = ps
    while cur <= pe:
        out.add(cur)
        cur += timedelta(days=1)
    return out


def _calendar_items_to_dict(items: Optional[List[ProcessRunCalendarItem]]) -> list[dict[str, Any]]:
    if not items:
        return []
    return [{"process_key": i.process_key, "dates": i.dates} for i in items]


@router.get("/process-run-days")
async def get_process_run_days(
    startDate: str = Query(..., description="期間開始 YYYY-MM-DD"),
    endDate: str = Query(..., description="期間終了 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = _parse_iso_date("startDate", startDate)
    pe = _parse_iso_date("endDate", endDate)
    if ps > pe:
        raise HTTPException(status_code=400, detail="startDate は endDate 以前にしてください")

    meta_q = text(
        """
        SELECT 1 AS ok
        FROM forming_daily_plan_process_run_calendar_meta
        WHERE period_start = :ps AND period_end = :pe
        LIMIT 1
        """
    )
    meta_row = (await db.execute(meta_q, {"ps": ps, "pe": pe})).mappings().first()
    if not meta_row:
        return {
            "data": {
                "configured": False,
                "startDate": ps.isoformat(),
                "endDate": pe.isoformat(),
                "items": [],
            }
        }

    q = text(
        """
        SELECT process_key, calendar_date
        FROM forming_daily_plan_process_run_calendar
        WHERE period_start = :ps AND period_end = :pe
        ORDER BY process_key, calendar_date
        """
    )
    result = await db.execute(q, {"ps": ps, "pe": pe})
    grouped: dict[str, list[str]] = {k: [] for k in sorted(ALLOWED_PROCESS_KEYS)}
    for row in result.mappings().all():
        pk = str(row["process_key"] or "").strip().lower()
        cd = row["calendar_date"]
        if pk in grouped and cd is not None:
            if hasattr(cd, "isoformat"):
                grouped[pk].append(cd.isoformat()[:10])
            else:
                grouped[pk].append(str(cd)[:10])

    items = [{"process_key": k, "dates": grouped[k]} for k in sorted(ALLOWED_PROCESS_KEYS)]
    return {
        "data": {
            "configured": True,
            "startDate": ps.isoformat(),
            "endDate": pe.isoformat(),
            "items": items,
        }
    }


@router.put("/process-run-days")
async def put_process_run_days(
    body: ProcessRunCalendarPutBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    ps = _parse_iso_date("startDate", body.startDate)
    pe = _parse_iso_date("endDate", body.endDate)
    if ps > pe:
        raise HTTPException(status_code=400, detail="startDate は endDate 以前にしてください")

    allowed_dates = _daterange_inclusive(ps, pe)

    by_key: dict[str, list[date]] = {}
    for it in body.items:
        pk = (it.process_key or "").strip().lower()
        if pk not in ALLOWED_PROCESS_KEYS:
            raise HTTPException(
                status_code=400,
                detail=f"process_key は次のいずれかです: {sorted(ALLOWED_PROCESS_KEYS)}",
            )
        seen: set[date] = set()
        norm: list[date] = []
        for ds in it.dates or []:
            s = (ds or "").strip()[:10]
            if len(s) != 10:
                continue
            try:
                y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
                dd = date(y, m, d)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"日付が不正です: {ds}")
            if dd not in allowed_dates:
                raise HTTPException(
                    status_code=400,
                    detail=f"日付が期間外です: {ds}（{ps.isoformat()} ～ {pe.isoformat()}）",
                )
            if dd not in seen:
                seen.add(dd)
                norm.append(dd)
        norm.sort()
        by_key[pk] = norm

    for k in ALLOWED_PROCESS_KEYS:
        if k not in by_key:
            by_key[k] = []

    upsert_meta = text(
        """
        INSERT INTO forming_daily_plan_process_run_calendar_meta (period_start, period_end)
        VALUES (:ps, :pe)
        ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
        """
    )
    del_cal = text(
        """
        DELETE FROM forming_daily_plan_process_run_calendar
        WHERE period_start = :ps AND period_end = :pe
        """
    )
    ins_cal = text(
        """
        INSERT INTO forming_daily_plan_process_run_calendar
            (period_start, period_end, process_key, calendar_date)
        VALUES (:ps, :pe, :pk, :cd)
        """
    )

    await db.execute(upsert_meta, {"ps": ps, "pe": pe})
    await db.execute(del_cal, {"ps": ps, "pe": pe})
    for pk, date_list in sorted(by_key.items(), key=lambda x: x[0]):
        for cd in date_list:
            await db.execute(ins_cal, {"ps": ps, "pe": pe, "pk": pk, "cd": cd})
    await db.commit()

    items = [{"process_key": k, "dates": [x.isoformat() for x in by_key[k]]} for k in sorted(ALLOWED_PROCESS_KEYS)]
    return {
        "data": {
            "configured": True,
            "startDate": ps.isoformat(),
            "endDate": pe.isoformat(),
            "items": items,
        }
    }


@router.get("/summary")
async def get_forming_daily_plan_summary(
    startDate: str = Query(...),
    endDate: str = Query(...),
    productCd: Optional[str] = Query(None),
    includeForecastMonths: bool = Query(False),
    baseMonth: Optional[str] = Query(None),
    includeOrderMatrix: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    product_cds = [productCd.strip()] if productCd and productCd.strip() else None
    try:
        data = await build_summary(
            db,
            startDate,
            endDate,
            product_cds=product_cds,
            include_forecast=includeForecastMonths,
            base_month=baseMonth,
            include_order_matrix=includeOrderMatrix,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 200, "data": data}


@router.get("/order-matrix")
async def get_forming_order_matrix(
    startDate: str = Query(...),
    endDate: str = Query(...),
    productCd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受注明細印刷用の order_matrix のみ返す（初回 summary 負荷軽減）。"""
    product_cds = [productCd.strip()] if productCd and productCd.strip() else None
    try:
        rows, dates = await build_order_matrix_for_period(db, startDate, endDate, product_cds=product_cds)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 200, "data": {"rows": rows, "dates": dates}}


@router.get("/order-forecast")
async def get_order_forecast(
    baseMonth: str = Query(..., description="基准月 YYYY-MM"),
    months: int = Query(2, ge=1, le=3),
    productCd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    product_cd = productCd.strip() if productCd else None
    forecast = await build_order_forecast(db, baseMonth, months=months, product_cd=product_cd)
    return {"code": 200, "data": {"months": forecast}}


@router.post("/simulate")
async def simulate_forming_daily_plan(
    body: SimulateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        data = await build_summary(
            db,
            body.startDate,
            body.endDate,
            product_cds=body.productCds,
            process_overrides=body.processOverrides,
            run_calendar_items=_calendar_items_to_dict(body.runCalendarItems),
            include_forecast=body.includeForecastMonths,
            base_month=body.baseMonth,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 200, "data": data}


@router.get("/scenarios")
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = text(
        """
        SELECT id, name, period_start, period_end, base_month, status,
               created_by, applied_at, applied_by, created_at, updated_at
        FROM forming_daily_plan_scenarios
        ORDER BY updated_at DESC
        LIMIT 100
        """
    )
    rows = (await db.execute(q)).mappings().all()
    items = []
    for r in rows:
        items.append(
            {
                "id": r["id"],
                "name": r["name"],
                "period_start": r["period_start"].isoformat() if r["period_start"] else None,
                "period_end": r["period_end"].isoformat() if r["period_end"] else None,
                "base_month": r["base_month"],
                "status": r["status"],
                "created_by": r["created_by"],
                "applied_at": r["applied_at"].isoformat() if r["applied_at"] else None,
                "applied_by": r["applied_by"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
        )
    return {"code": 200, "data": {"items": items}}


@router.post("/scenarios")
async def create_scenario(
    body: ScenarioCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    ps = parse_iso_date(body.startDate)
    pe = parse_iso_date(body.endDate)
    cal_items = _calendar_items_to_dict(body.runCalendarItems)

    try:
        sim_result = await build_summary(
            db,
            body.startDate,
            body.endDate,
            process_overrides=body.processOverrides,
            run_calendar_items=cal_items,
            include_forecast=body.includeForecastMonths,
            base_month=body.baseMonth,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    payload = {
        "include_forecast_months": body.includeForecastMonths,
        "forecast_months": [],
        "process_overrides": body.processOverrides or {},
        "run_calendar_snapshot": cal_items,
        "notes": body.notes or "",
        "last_simulation": sim_result,
    }

    ins = text(
        """
        INSERT INTO forming_daily_plan_scenarios
            (name, period_start, period_end, base_month, status, created_by)
        VALUES (:name, :ps, :pe, :bm, 'draft', :by)
        """
    )
    res = await db.execute(
        ins,
        {
            "name": body.name,
            "ps": ps,
            "pe": pe,
            "bm": body.baseMonth,
            "by": getattr(current_user, "username", None) or str(current_user.id),
        },
    )
    scenario_id = res.lastrowid
    await db.execute(
        text("INSERT INTO forming_daily_plan_scenario_payload (scenario_id, payload) VALUES (:id, :payload)"),
        {"id": scenario_id, "payload": json.dumps(payload, ensure_ascii=False, default=str)},
    )
    await db.commit()
    return {"code": 200, "data": {"id": scenario_id, "simulation": sim_result}}


@router.get("/scenarios/{scenario_id}")
async def get_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    meta_q = text("SELECT * FROM forming_daily_plan_scenarios WHERE id = :id")
    meta = (await db.execute(meta_q, {"id": scenario_id})).mappings().first()
    if not meta:
        raise HTTPException(status_code=404, detail="方案不存在")
    payload_q = text("SELECT payload FROM forming_daily_plan_scenario_payload WHERE scenario_id = :id")
    payload_row = (await db.execute(payload_q, {"id": scenario_id})).mappings().first()
    payload = payload_row["payload"] if payload_row else {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    return {
        "code": 200,
        "data": {
            "id": meta["id"],
            "name": meta["name"],
            "period_start": meta["period_start"].isoformat(),
            "period_end": meta["period_end"].isoformat(),
            "base_month": meta["base_month"],
            "status": meta["status"],
            "payload": payload,
        },
    }


@router.put("/scenarios/{scenario_id}")
async def update_scenario(
    scenario_id: int,
    body: ScenarioUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    meta_q = text("SELECT * FROM forming_daily_plan_scenarios WHERE id = :id")
    meta = (await db.execute(meta_q, {"id": scenario_id})).mappings().first()
    if not meta:
        raise HTTPException(status_code=404, detail="方案不存在")

    payload_q = text("SELECT payload FROM forming_daily_plan_scenario_payload WHERE scenario_id = :id")
    payload_row = (await db.execute(payload_q, {"id": scenario_id})).mappings().first()
    payload = payload_row["payload"] if payload_row else {}
    if isinstance(payload, str):
        payload = json.loads(payload)

    if body.name:
        await db.execute(
            text("UPDATE forming_daily_plan_scenarios SET name = :name WHERE id = :id"),
            {"name": body.name, "id": scenario_id},
        )
    if body.processOverrides is not None:
        payload["process_overrides"] = body.processOverrides
    if body.runCalendarItems is not None:
        payload["run_calendar_snapshot"] = _calendar_items_to_dict(body.runCalendarItems)
    if body.includeForecastMonths is not None:
        payload["include_forecast_months"] = body.includeForecastMonths
    if body.notes is not None:
        payload["notes"] = body.notes

    await db.execute(
        text("UPDATE forming_daily_plan_scenario_payload SET payload = :payload WHERE scenario_id = :id"),
        {"id": scenario_id, "payload": json.dumps(payload, ensure_ascii=False, default=str)},
    )
    await db.commit()
    return {"code": 200, "data": {"id": scenario_id}}


@router.post("/scenarios/{scenario_id}/simulate")
async def simulate_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    meta_q = text("SELECT * FROM forming_daily_plan_scenarios WHERE id = :id")
    meta = (await db.execute(meta_q, {"id": scenario_id})).mappings().first()
    if not meta:
        raise HTTPException(status_code=404, detail="方案不存在")

    payload_q = text("SELECT payload FROM forming_daily_plan_scenario_payload WHERE scenario_id = :id")
    payload_row = (await db.execute(payload_q, {"id": scenario_id})).mappings().first()
    payload = payload_row["payload"] if payload_row else {}
    if isinstance(payload, str):
        payload = json.loads(payload)

    try:
        sim = await build_summary(
            db,
            meta["period_start"].isoformat(),
            meta["period_end"].isoformat(),
            process_overrides=payload.get("process_overrides"),
            run_calendar_items=payload.get("run_calendar_snapshot"),
            include_forecast=payload.get("include_forecast_months", False),
            base_month=meta["base_month"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    payload["last_simulation"] = sim
    await db.execute(
        text("UPDATE forming_daily_plan_scenario_payload SET payload = :payload WHERE scenario_id = :id"),
        {"id": scenario_id, "payload": json.dumps(payload, ensure_ascii=False, default=str)},
    )
    await db.commit()
    return {"code": 200, "data": sim}


@router.post("/scenarios/{scenario_id}/apply")
async def apply_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    try:
        result = await apply_scenario_to_summary(
            db,
            scenario_id,
            applied_by=getattr(current_user, "username", None) or str(current_user.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": 200, "data": result, "message": f"已应用方案，更新 {result.get('updated', 0)} 行"}


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("edit")),
):
    res = await db.execute(
        text("DELETE FROM forming_daily_plan_scenarios WHERE id = :id"),
        {"id": scenario_id},
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="方案不存在")
    await db.commit()
    return {"code": 200, "message": "已删除"}

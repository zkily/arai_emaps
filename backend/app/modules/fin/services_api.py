"""FIN 中核業務エンドポイント（手書き）。

汎用 CRUD（fin_codegen 生成）では表現しない横断・集計処理を提供する:
  - 会計: 仕訳転記 / 試算表
  - 連携: ERP イベント記録 / 仕訳一括生成
  - 給与: 給与計算

fin_codegen の再生成対象外。main.py で fin.router と並べて登録する。
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.fin.accounting.services import posting_service
from app.modules.fin.attendance.services import attendance_calc
from app.modules.fin.integration import erp_events
from app.modules.fin.payroll.services import calc_engine

router = APIRouter()


@router.post("/accounting/journals/{entry_id}/post", tags=["FIN 会計"], summary="仕訳転記")
async def post_journal(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(verify_token_and_get_user),
):
    entry = await posting_service.post_journal(db, entry_id, posted_by=user.username)
    return {"message": "転記しました", "id": entry.id, "status": entry.status}


@router.get("/accounting/trial-balance", tags=["FIN 会計"], summary="試算表")
async def trial_balance(
    period_ym: Optional[str] = Query(None, description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(verify_token_and_get_user),
):
    rows = await posting_service.trial_balance(db, period_ym=period_ym)
    return {"items": rows, "total": len(rows)}


@router.post("/integration/events", tags=["FIN 連携"], summary="ERP イベント記録")
async def record_event(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(verify_token_and_get_user),
):
    src = await erp_events.record_event(
        db,
        source_type=payload["source_type"],
        source_ref=payload.get("source_ref", ""),
        amount=payload.get("amount", 0),
        event_date=payload.get("event_date"),
        source_module=payload.get("source_module", "erp"),
        payload_json=payload.get("payload_json"),
        created_by=user.username,
    )
    return {"message": "イベントを記録しました", "id": src.id, "status": src.status}


@router.post("/integration/generate-journals", tags=["FIN 連携"], summary="仕訳一括生成")
async def generate_journals(
    period_ym: str = Query(..., description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(verify_token_and_get_user),
):
    return await erp_events.generate_journals(db, period_ym=period_ym, created_by=user.username)


@router.post("/payroll/runs/{run_id}/calculate", tags=["FIN 給与"], summary="給与計算")
async def calculate_payroll(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(verify_token_and_get_user),
):
    return await calc_engine.calculate_run(db, run_id, calculated_by=user.username)


@router.post("/attendance/records/{record_id}/recalc", tags=["FIN 勤怠"], summary="勤怠再計算")
async def recalc_attendance(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(verify_token_and_get_user),
):
    return await attendance_calc.recalc_record(db, record_id, updated_by=user.username)


__all__ = ["router"]

"""勤怠集計（スケルトン）。

出退勤打刻（clock_in / clock_out）から実働分・残業分を算出する。
所定労働時間や残業の判定基準はシフト（fin_shift_pattern）や就業規則に依存するため、
ここでは「所定 = 480 分（8時間）超過分を残業」とする単純既定値を用いる骨組み。
fin_codegen の再生成対象外（手書き）。
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fin.attendance import models as att

STANDARD_WORK_MINUTES = 480  # 所定労働分（既定 8 時間）


def compute_minutes(clock_in, clock_out, break_minutes: int) -> tuple[int, int]:
    """(実働分, 残業分) を返す。"""
    if not clock_in or not clock_out:
        return 0, 0
    gross = int((clock_out - clock_in).total_seconds() // 60)
    work = max(gross - int(break_minutes or 0), 0)
    overtime = max(work - STANDARD_WORK_MINUTES, 0)
    return work, overtime


async def recalc_record(db: AsyncSession, record_id: int, *, updated_by: str | None = None) -> dict:
    """1 件の勤怠記録の実働分・残業分を再計算する。"""
    rec = await db.get(att.AttendanceRecord, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="勤怠記録が見つかりません")
    work, overtime = compute_minutes(rec.clock_in, rec.clock_out, rec.break_minutes or 0)
    rec.work_minutes = work
    rec.overtime_minutes = overtime
    if updated_by:
        rec.updated_by = updated_by
    await db.commit()
    await db.refresh(rec)
    return {
        "id": rec.id,
        "work_minutes": work,
        "overtime_minutes": overtime,
    }

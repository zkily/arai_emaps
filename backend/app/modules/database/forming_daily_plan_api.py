"""
工程別計画試算（FormingDailyPlanSummary）向け：期間×工程×日历日の運行チェック CRUD
"""
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

router = APIRouter(tags=["forming-daily-plan"])

ALLOWED_PROCESS_KEYS = frozenset(
    {"cutting", "chamfering", "molding", "plating", "welding", "inspection"}
)


class ProcessRunCalendarItem(BaseModel):
    process_key: str = Field(..., max_length=32)
    dates: List[str] = Field(default_factory=list)


class ProcessRunCalendarPutBody(BaseModel):
    startDate: str
    endDate: str
    items: List[ProcessRunCalendarItem]


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
    current_user: User = Depends(verify_token_and_get_user),
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

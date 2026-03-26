"""
APS 排産エンジン
JST 強制の産能推算ループ。schedule_details / schedule_slice_allocations を生成し production_schedules を更新する。

日次上限：その日の実稼働 h（時間帯合算 or カレンダー or default）×（daily_capacity/15.3）× 能率%。
初日のみ段取（分）を稼働から差し引き、時間帯配分の先頭からも段取を消費（製品切替はライン順再計算で工単ごとに初日へ反映）。

時間別ガント用 slice：各区間の上限＝⌊ 個/h × 能率 × 区間時間(h) ⌋ とし、時系列が早い区間から最大能力で詰める。
最終生産日も「日量をその日の全時間に平均」はせず、先の時間帯を満杯にして残りは後ろの区間へ寄せる。
"""
import math
from collections import defaultdict
from datetime import date, time, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.master.models import Machine
from app.modules.aps.models import (
    LineCapacity,
    LineCapacityTimeSlot,
    ProductionSchedule,
    ScheduleDetail,
    ScheduleSliceAllocation,
)

# フロント Planning と同じ基準：日産能力 = floor(能率 × 15.3h)
SCHEDULE_STANDARD_DAY_HOURS = 15.3


def _time_to_hours(t: time) -> float:
    return t.hour + t.minute / 60.0 + (t.second or 0) / 3600.0


def _slot_duration_hours(start_t: time, end_t: time) -> float:
    sh = _time_to_hours(start_t)
    eh = _time_to_hours(end_t)
    if eh <= sh:
        return 0.0
    return eh - sh


def _hours_from_slots(day_slots: List[LineCapacityTimeSlot]) -> float:
    return sum(_slot_duration_hours(s.start_time, s.end_time) for s in day_slots)


async def _fetch_slots_by_date(
    db: AsyncSession,
    line_id: int,
    start_d: date,
    end_d: date,
) -> Dict[date, List[LineCapacityTimeSlot]]:
    result = await db.execute(
        select(LineCapacityTimeSlot)
        .where(
            LineCapacityTimeSlot.line_id == line_id,
            LineCapacityTimeSlot.work_date >= start_d,
            LineCapacityTimeSlot.work_date <= end_d,
        )
        .order_by(LineCapacityTimeSlot.work_date, LineCapacityTimeSlot.sort_order)
    )
    by_date: Dict[date, List[LineCapacityTimeSlot]] = defaultdict(list)
    for row in result.scalars().all():
        by_date[row.work_date].append(row)
    return by_date


def _resolve_day_operating_hours(
    d: date,
    slots_by_date: Dict[date, List[LineCapacityTimeSlot]],
    cal_map: dict[date, float],
    default_hours: float,
) -> float:
    """その日の稼働 h：時間帯行があれば帯の合算のみ。無ければ line_capacities → default。"""
    slots = slots_by_date.get(d)
    if slots:
        return float(_hours_from_slots(slots))
    return float(cal_map.get(d, default_hours))


def _minutes_from_midnight(t: time) -> int:
    return int(t.hour * 60 + t.minute + (t.second or 0) / 60)


def _minutes_to_time(m: int) -> time:
    m = max(0, m % (24 * 60))
    return time(m // 60, m % 60, 0)


def _productive_minute_segments(
    day_slots: List[LineCapacityTimeSlot],
    avail_hours: float,
    apply_setup: bool,
    setup_minutes: int,
    start_from_minute: Optional[int] = None,
) -> List[tuple[int, int]]:
    """
    生産に使う [start_min, end_min) の半開区間（0〜1440、同一日）。
    時間帯が無い場合は 06:00 から available_hours 分の仮想区間。
    apply_setup 時は稼働の先頭から段取分を消費。
    """
    segments: List[tuple[int, int]] = []
    if day_slots:
        for s in sorted(day_slots, key=lambda x: (x.sort_order, x.start_time)):
            sm = _minutes_from_midnight(s.start_time)
            em = _minutes_from_midnight(s.end_time)
            if em > sm:
                segments.append((sm, em))
    else:
        start_m = 6 * 60
        span_min = max(0, int(round(float(avail_hours) * 60)))
        end_m = min(start_m + span_min, 24 * 60)
        if end_m > start_m:
            segments.append((start_m, end_m))

    # start_from_minute（先頭日の切替時刻）が指定されている場合、
    # それ以前の区間を除外する。
    if start_from_minute is not None:
        clipped: List[tuple[int, int]] = []
        for sm, em in segments:
            sm2 = max(sm, start_from_minute)
            if em > sm2:
                clipped.append((sm2, em))
        segments = clipped

    setup_left = setup_minutes if apply_setup and setup_minutes > 0 else 0
    productive: List[tuple[int, int]] = []
    for sm, em in segments:
        cur = sm
        while cur < em and setup_left > 0:
            take = min(setup_left, em - cur)
            cur += take
            setup_left -= take
        if cur < em:
            productive.append((cur, em))
    return productive


def _split_segments_to_hour_chunks(segments: List[tuple[int, int]]) -> List[tuple[time, time]]:
    """各セグメントを最大 60 分の [st, et) に分割。"""
    chunks: List[tuple[time, time]] = []
    for sm, em in segments:
        cur = sm
        while cur < em:
            nxt = min(cur + 60, em)
            chunks.append((_minutes_to_time(cur), _minutes_to_time(nxt)))
            cur = nxt
    return chunks


async def _persist_slice_allocations(
    db: AsyncSession,
    schedule_id: int,
    work_date: date,
    day_slots: List[LineCapacityTimeSlot],
    avail_hours: float,
    apply_setup_day: bool,
    setup_minutes: int,
    today_qty: int,
    hourly_piece_rate: float,
    efficiency_pct: float,
    start_from_minute: Optional[int] = None,
) -> int:
    """
    1 日分を時間区間に配分して schedule_slice_allocations に保存。

    ガント（時間別）は「各区内の最大可能個数」上限で、**時系列が早い区間から詰める**。
    最終生産日も日量を全区間に平均せず、先の時間帯を最大能力で埋め残りは最後の区間に収まる。
    """
    if today_qty <= 0:
        return 0
    segs = _productive_minute_segments(
        day_slots, avail_hours, apply_setup_day, setup_minutes, start_from_minute=start_from_minute
    )
    chunks = _split_segments_to_hour_chunks(segs)
    if not chunks:
        return 0
    eff_factor = float(efficiency_pct or 100) / 100.0
    rate = float(hourly_piece_rate)
    if rate <= 0 or eff_factor <= 0:
        return 0
    rem = int(today_qty)
    sort_base = 0
    total_placed = 0
    last_alloc: Optional[ScheduleSliceAllocation] = None
    for st, et in chunks:
        len_min = max(0, _minutes_from_midnight(et) - _minutes_from_midnight(st))
        chunk_hours = len_min / 60.0
        # 当該区間の理論上限（個）：⌊ 個/h × 能率 × 区間時間(h) ⌋
        cap = int(math.floor(rate * eff_factor * chunk_hours + 1e-9))
        give = min(rem, cap)
        if give > 0:
            sa = ScheduleSliceAllocation(
                schedule_id=schedule_id,
                work_date=work_date,
                period_start=st,
                period_end=et,
                planned_qty=give,
                sort_order=sort_base,
            )
            db.add(sa)
            last_alloc = sa
            total_placed += give
            rem -= give
        sort_base += 1
    return total_placed


async def run_engine(
    db: AsyncSession,
    schedule_id: int,
    override_start_date: Optional[date] = None,
    override_start_time: Optional[time] = None,
) -> ProductionSchedule:
    """
    指定された工単に対して排産推算を実行する。

    1. schedule_details を全削除（冪等）
    2. 日別稼働 h：時間帯があれば合算、無ければ line_capacities → 設備 default
    3. 日次出来高 ⌊ 稼働 h × (daily_capacity/15.3) × 能率% ⌋ で schedule_details を INSERT（初日は段取を h から控除）
    4. 同一数量を稼働帯に「区間ごとの時間上限×個/h×能率」で先から詰め、最大 60 分区間ごとに schedule_slice_allocations を INSERT
    5. production_schedules の start_date / end_date / planned_output_qty / completion_rate を更新
    """
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise ValueError(f"ProductionSchedule id={schedule_id} not found")

    line = await db.get(Machine, ps.line_id)
    if line is None:
        raise ValueError(f"Machine id={ps.line_id} not found")

    # 既存明細・時間帯配分の削除（冪等性）
    await db.execute(
        delete(ScheduleSliceAllocation).where(
            ScheduleSliceAllocation.schedule_id == schedule_id
        )
    )
    await db.execute(
        delete(ScheduleDetail).where(ScheduleDetail.schedule_id == schedule_id)
    )
    await db.flush()

    # 基本パラメータ
    start = override_start_date or ps.start_date or now_jst().date()
    remaining = int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0)
    if remaining <= 0:
        ps.start_date = start
        ps.end_date = start
        ps.planned_output_qty = 0
        ps.completion_rate = Decimal("100.00")
        ps.status = "COMPLETED"
        return ps

    daily_capacity = int(ps.daily_capacity or 0)
    if daily_capacity <= 0:
        raise ValueError("daily_capacity must be > 0")

    default_hours = float(line.default_work_hours or 0)
    if default_hours <= 0:
        default_hours = 8.0

    efficiency_pct = float(ps.efficiency or 100)
    setup_minutes = int(ps.setup_time or 0)

    if SCHEDULE_STANDARD_DAY_HOURS <= 0:
        raise ValueError("SCHEDULE_STANDARD_DAY_HOURS must be > 0")
    # daily_capacity は「15.3h 標準日の目標日産」とみなし、製品の時間当たり出来高（個/h）を復元
    hourly_piece_rate = float(daily_capacity) / SCHEDULE_STANDARD_DAY_HOURS

    # 稼働カレンダー・時間帯を先読み（最大 365 日分）
    cal_end = start + timedelta(days=365)
    cal_result = await db.execute(
        select(LineCapacity)
        .where(
            LineCapacity.line_id == ps.line_id,
            LineCapacity.work_date >= start,
            LineCapacity.work_date <= cal_end,
        )
        .order_by(LineCapacity.work_date)
    )
    cal_map: dict[date, float] = {
        row.work_date: float(row.available_hours) for row in cal_result.scalars().all()
    }
    slots_by_date = await _fetch_slots_by_date(db, ps.line_id, start, cal_end)

    total_produced = 0
    current_date = start
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    is_first_day = True
    initial_start_from_minute = (
        _minutes_from_midnight(override_start_time)
        if override_start_time is not None
        else None
    )
    max_iterations = 730

    while remaining > 0 and max_iterations > 0:
        max_iterations -= 1
        avail_hours = _resolve_day_operating_hours(
            current_date, slots_by_date, cal_map, float(default_hours)
        )

        if avail_hours <= 0:
            current_date += timedelta(days=1)
            continue

        apply_setup_slices = is_first_day and setup_minutes > 0
        start_from_minute = initial_start_from_minute if is_first_day else None
        # apply_setup_slices は「初回実稼働開始日だけ」消費（旧仕様互換）
        if apply_setup_slices:
            is_first_day = False

        day_slot_list = slots_by_date.get(current_date) or []
        segs = _productive_minute_segments(
            day_slot_list,
            avail_hours,
            apply_setup_slices,
            int(setup_minutes),
            start_from_minute=start_from_minute,
        )
        chunks = _split_segments_to_hour_chunks(segs)
        if not chunks:
            current_date += timedelta(days=1)
            continue

        eff_factor = float(efficiency_pct or 100) / 100.0
        rate = float(hourly_piece_rate)
        if rate <= 0 or eff_factor <= 0:
            current_date += timedelta(days=1)
            continue

        total_cap = 0
        for st, et in chunks:
            len_min = max(0, _minutes_from_midnight(et) - _minutes_from_midnight(st))
            chunk_hours = len_min / 60.0
            cap = int(math.floor(rate * eff_factor * chunk_hours + 1e-9))
            total_cap += cap

        today_qty = min(total_cap, remaining)

        if today_qty > 0:
            placed = await _persist_slice_allocations(
                db,
                schedule_id,
                current_date,
                day_slot_list,
                avail_hours,
                apply_setup_slices,
                int(setup_minutes),
                today_qty,
                hourly_piece_rate,
                efficiency_pct,
                start_from_minute=start_from_minute,
            )
            if placed > 0:
                db.add(
                    ScheduleDetail(
                        schedule_id=schedule_id,
                        schedule_date=current_date,
                        planned_qty=placed,
                    )
                )
                remaining -= placed
                total_produced += placed
                if actual_start is None:
                    actual_start = current_date
                actual_end = current_date

        current_date += timedelta(days=1)

    ps.start_date = actual_start or start
    ps.end_date = actual_end or start
    ps.planned_output_qty = total_produced
    total_needed = int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0)
    if total_needed > 0:
        ps.completion_rate = Decimal(str(round(total_produced / total_needed * 100, 2)))
    else:
        ps.completion_rate = Decimal("100.00")

    if remaining <= 0:
        ps.due_date = actual_end
    if ps.status == "PLANNING" and total_produced > 0:
        ps.status = "PLANNING"

    return ps


async def _next_working_date(
    db: AsyncSession, line_id: int, after_date: date, default_hours: float
) -> date:
    """after_date の翌日から稼働 h > 0（時間帯合算 or line_capacities or default）の最初の日を返す。"""
    cursor = after_date + timedelta(days=1)
    window_end = cursor + timedelta(days=730)
    cal_result = await db.execute(
        select(LineCapacity)
        .where(
            LineCapacity.line_id == line_id,
            LineCapacity.work_date >= cursor,
            LineCapacity.work_date <= window_end,
        )
        .order_by(LineCapacity.work_date)
    )
    cal_map = {r.work_date: float(r.available_hours) for r in cal_result.scalars().all()}
    slots_by_date = await _fetch_slots_by_date(db, line_id, cursor, window_end)
    d = cursor
    for _ in range(730):
        h = _resolve_day_operating_hours(d, slots_by_date, cal_map, float(default_hours))
        if h > 0:
            return d
        d += timedelta(days=1)
    return d


async def replan_line_sequential(
    db: AsyncSession,
    line_id: int,
    anchor_start_date: Optional[date] = None,
) -> List[ProductionSchedule]:
    """
    指定産線の全 PLANNING/IN_PROGRESS 工単を order_no 順に串接重算する。
    最初の工単は anchor_start_date から、以降は前の工単 end_date の翌稼働日から。
    各工単の開始日は run_engine 内で「初日段取」をその製品の setup_time で控除する（製品切替＝次工単の初日に段取）。
    """
    line = await db.get(Machine, line_id)
    if line is None:
        raise ValueError(f"Machine id={line_id} not found")

    default_hours = float(line.default_work_hours or 0)
    if default_hours <= 0:
        default_hours = 8.0

    result = await db.execute(
        select(ProductionSchedule)
        .where(
            ProductionSchedule.line_id == line_id,
            ProductionSchedule.status.in_(["PLANNING", "IN_PROGRESS"]),
        )
        .order_by(ProductionSchedule.order_no, ProductionSchedule.id)
    )
    schedules = result.scalars().all()
    if not schedules:
        return []

    cursor_date = anchor_start_date or schedules[0].start_date or now_jst().date()
    cursor_time = time(0, 0, 0)
    updated: List[ProductionSchedule] = []

    for ps in schedules:
        ps = await run_engine(
            db,
            ps.id,
            override_start_date=cursor_date,
            override_start_time=cursor_time,
        )
        updated.append(ps)

        # 次工単の開始時刻は、前工単の最後の slice end 時刻（同日で切替するため）
        await db.flush()
        last_q = await db.execute(
            select(ScheduleSliceAllocation)
            .where(ScheduleSliceAllocation.schedule_id == ps.id)
            .order_by(
                ScheduleSliceAllocation.work_date.desc(),
                ScheduleSliceAllocation.period_end.desc(),
                ScheduleSliceAllocation.sort_order.desc(),
            )
            .limit(1)
        )
        last = last_q.scalars().first()
        if last is not None:
            cursor_date = last.work_date
            cursor_time = last.period_end
            # 00:00 は「24:00 保存（m % 1440）」の可能性があるため翌日に補正
            if cursor_time == time(0, 0, 0) and last.period_start != time(0, 0, 0):
                cursor_date = cursor_date + timedelta(days=1)
                cursor_time = time(0, 0, 0)
        else:
            cursor_date = ps.end_date or (cursor_date + timedelta(days=1))
            cursor_time = time(0, 0, 0)

    await db.flush()
    return updated

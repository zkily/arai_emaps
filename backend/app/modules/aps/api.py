"""
APS（先進的計画・スケジューリング）APIエンドポイント
産線管理、稼働カレンダー、工単 CRUD、排産エンジン、スケジューリンググリッド
"""
import math
import asyncio
import logging
from collections import defaultdict
from datetime import date, timedelta, datetime, time
from decimal import Decimal
from typing import Optional, List, Dict, Any, Iterable, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_, delete, update, text, exists, func, case
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.datetime_utils import now_jst
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

from app.modules.master.models import (
    Machine,
    EquipmentEfficiency,
    Process,
    Product,
    ProductRouteStep,
    Material,
    Supplier,
)
from app.modules.aps.models import (
    LineCapacity,
    LineCapacityTimeSlot,
    ProductionSchedule,
    ApsBatchPlan,
    ApsLineReplanAnchor,
    ScheduleDetail,
    ScheduleSliceAllocation,
    LineProductStandard,
)
from app.modules.aps.schemas import (
    ProductionLineOut,
    EquipmentEfficiencyProductOut,
    LineCapacityOut,
    LineCapacityBatchBody,
    DaySlotsBody,
    DaySlotsBatchBody,
    DaySlotsOut,
    TimeSlotOut,
    LineProductStandardBody,
    LineProductStandardOut,
    ScheduleCreateBody,
    ScheduleUpdateBody,
    ScheduleDailyPlanUpdateBody,
    ScheduleAppendPlannedBody,
    ScheduleOut,
    ScheduleWithLineOut,
    ScheduleGridRow,
    LineGridBlock,
    SchedulingGridResponse,
    SchedulingHourlyGridResponse,
    HourlyGridColumnOut,
    HourlyGridRowOut,
    ApsBatchPlanOut,
    ProgressLotItem,
    ProductionProgressResponse,
    DailyUpstreamTintSeg,
    LineReplanAnchorOut,
    LineReplanAnchorsBatchBody,
    UpstreamApsBatchPlanLinksBody,
    UpstreamApsBatchPlanLinksResult,
    ReassignCuttingManagementLotBody,
    ReassignCuttingManagementLotResult,
)
from app.modules.aps.engine import (
    APS_CALENDAR_PRELOAD_DAYS,
    SCHEDULE_STANDARD_DAY_HOURS,
    run_engine,
    replan_line_sequential,
    run_engine_append_qty,
    replan_following_schedules_on_line,
    productive_hours_from_slot_rows,
    hourly_piece_rate_from_daily_capacity,
    resolve_schedule_piece_rate,
    capacity_efficiency_factor,
    advance_line_cursor_after_slice,
    _fetch_slots_by_date,
)
from app.services.access_sync.production_plan_excel_sync import sync_production_plan_excel_to_access

router = APIRouter()
logger = logging.getLogger(__name__)


def _dec(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


# 設備能率マスタ由来の日産初期値と整合（productionPlanCreation/FormingPlanning.vue EE_DAILY_HOURS_STANDARD）
_APS_EE_STANDARD_DAY_HOURS = Decimal("15.3")
# 成型工程 CD：在庫ログの不良同期は transaction_type=不良 かつ process_cd 一致のみ（instruction_plans 同期と同一）
_APS_FORMING_PROCESS_CD = "KT04"
# 溶接工程 CD：溶接設備の不良同期・実績考慮再排産は当該工程のみ
_APS_WELDING_PROCESS_CD = "KT07"


def _equipment_efficiency_matches_machine(row: EquipmentEfficiency, machine: Machine) -> bool:
    m_cd = (machine.machine_cd or "").strip()
    m_name = (machine.machine_name or "").strip()
    r_cd = (row.machine_cd or "").strip()
    r_name = (row.machines_name or "").strip()
    if m_cd and (r_cd == m_cd or r_name == m_cd):
        return True
    if m_name and r_name == m_name:
        return True
    return False


async def _load_equipment_efficiency_rows_for_machines(
    db: AsyncSession,
    machines: Sequence[Machine],
) -> Dict[int, List[EquipmentEfficiency]]:
    """複数設備の equipment_efficiency 行を一括取得し、設備 id ごとに振り分ける。"""
    out: Dict[int, List[EquipmentEfficiency]] = {int(m.id): [] for m in machines}
    if not machines:
        return out

    match_conds = []
    for machine in machines:
        m_cd = (machine.machine_cd or "").strip()
        m_name = (machine.machine_name or "").strip()
        if m_cd:
            match_conds.append(EquipmentEfficiency.machine_cd == m_cd)
            match_conds.append(EquipmentEfficiency.machines_name == m_cd)
        if m_name:
            match_conds.append(EquipmentEfficiency.machines_name == m_name)
    if not match_conds:
        return out

    q = (
        select(EquipmentEfficiency)
        .where(or_(*match_conds))
        .where(or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status == 1))
        .order_by(EquipmentEfficiency.product_name, EquipmentEfficiency.product_cd, EquipmentEfficiency.id)
    )
    result = await db.execute(q)
    all_rows = list(result.scalars().all())
    for machine in machines:
        out[int(machine.id)] = [row for row in all_rows if _equipment_efficiency_matches_machine(row, machine)]
    return out


async def _load_equipment_efficiency_rows_for_machine(
    db: AsyncSession,
    machine: Machine,
) -> List[EquipmentEfficiency]:
    """選択設備に紐づく equipment_efficiency 行（/equipment-efficiency-products と同趣旨のマッチ）"""
    rows_by_machine = await _load_equipment_efficiency_rows_for_machines(db, [machine])
    return rows_by_machine.get(int(machine.id), [])


def _resolve_efficiency_rate_pieces_per_hour(
    ps: ProductionSchedule,
    ee_rows: List[EquipmentEfficiency],
) -> Optional[float]:
    """表示用：equipment_efficiency.efficiency_rate（本/H）。排産エンジンと同一ロジック。"""
    rate, _from_ee = resolve_schedule_piece_rate(ps, ee_rows)
    if rate > 0:
        return round(float(rate), 2)
    return None


def _sync_schedules_daily_capacity_from_ee(
    schedules: Sequence[ProductionSchedule],
    ee_rows: List[EquipmentEfficiency],
) -> None:
    """再計算前に daily_capacity を設備能率マスタ（⌊本/H×15.3⌋）へ揃える。"""
    for ps in schedules:
        rate, from_ee = resolve_schedule_piece_rate(ps, ee_rows)
        if not from_ee or rate <= 0:
            continue
        new_dc = int(math.floor(rate * SCHEDULE_STANDARD_DAY_HOURS))
        if new_dc > 0:
            ps.daily_capacity = new_dc


def _upstream_defect_daily_allocation_keys(
    daily: dict[str, int],
    *,
    start_iso: Optional[str],
    end_iso: Optional[str],
    forced_start_iso: Optional[str],
    min_slice_iso: Optional[str],
) -> list[tuple[str, int]]:
    """
    前工程不良の日別表示用：有効な生産日のみを按分対象とする。
    ロット合計（upstream_defect_qty）は日付に紐づかないが、ガント「前」行表示のため
    日別計画本数で按分する。開始日指定・工単 start/end 外の孤立日別計画は除外する。
    """
    floor_iso = start_iso
    if forced_start_iso and (floor_iso is None or forced_start_iso > floor_iso):
        floor_iso = forced_start_iso
    if min_slice_iso and (floor_iso is None or min_slice_iso > floor_iso):
        floor_iso = min_slice_iso

    weighted: list[tuple[str, int]] = []
    for k in sorted(daily.keys()):
        w = max(0, int(daily.get(k, 0) or 0))
        if w <= 0:
            continue
        if floor_iso and k < floor_iso:
            continue
        if end_iso and k > end_iso:
            continue
        weighted.append((k, w))
    return weighted


def _build_upstream_defect_daily(
    upstream_total: int,
    daily: dict[str, int],
    *,
    start_iso: Optional[str],
    end_iso: Optional[str],
    forced_start_iso: Optional[str],
    min_slice_iso: Optional[str],
) -> dict[str, int]:
    """ロット合計 upstream を有効生産日の計画本数比で按分（最大剰余）。対象日が無ければ日別は出さない。"""
    if upstream_total <= 0 or not daily:
        return {}
    weighted_keys = _upstream_defect_daily_allocation_keys(
        daily,
        start_iso=start_iso,
        end_iso=end_iso,
        forced_start_iso=forced_start_iso,
        min_slice_iso=min_slice_iso,
    )
    if not weighted_keys:
        return {}
    total_weight = sum(w for _k, w in weighted_keys)
    capped_total = min(int(upstream_total), total_weight) if total_weight > 0 else 0
    if capped_total <= 0:
        return {}
    out: dict[str, int] = {}
    acc = 0
    remainders: list[tuple[float, str]] = []
    for k, w in weighted_keys:
        raw = capped_total * (w / total_weight)
        q = int(raw)
        out[k] = q
        acc += q
        remainders.append((raw - q, k))
    rem = capped_total - acc
    for _frac, k in sorted(remainders, key=lambda x: (-x[0], x[1]))[:rem]:
        out[k] = int(out.get(k, 0) or 0) + 1
    return out


def _replan_actual_done_and_remaining(
    planned_total: int,
    period_actual: int,
    period_defect: int,
    upstream_defect_total: int,
) -> tuple[int, int]:
    """
    実績あり工単の Step3 再排産用。

    有効本数 ＝ 計画総数 − 前工程不良（upstream）。残数 ＝ 有効 − 良品実績 − 当工程不良。
    run_engine の actual_done_qty は upstream＋実績＋不良の合算（上限 planned_total）とし、
    前工程不良を二重控除しない（旧: upstream を actual に足し過ぎて 7801→7064 の不足があった）。
    """
    pt = int(planned_total or 0)
    upstream = max(0, int(upstream_defect_total or 0))
    pa = max(0, int(period_actual or 0))
    pd = max(0, int(period_defect or 0))
    effective_total = max(0, pt - upstream)
    gross_remaining = max(0, effective_total - pa - pd)
    actual_done = min(pt, upstream + pa + pd)
    return actual_done, gross_remaining


async def _line_cursor_after_schedule(
    db: AsyncSession,
    ps: ProductionSchedule,
    ee_rows: Optional[Sequence[Any]],
    cursor_date: date,
    cursor_time: time,
) -> tuple[date, time]:
    """ライン順次排産（Step1/3）：工単終了位置で游标を前進（既存游标より前には戻さない）。"""
    last_q = await db.execute(
        select(ScheduleSliceAllocation)
        .where(ScheduleSliceAllocation.schedule_id == ps.id)
        .order_by(
            ScheduleSliceAllocation.work_date.desc(),
            ScheduleSliceAllocation.sort_order.desc(),
            ScheduleSliceAllocation.id.desc(),
        )
        .limit(1)
    )
    last = last_q.scalars().first()
    cand_date = cursor_date
    cand_time = cursor_time
    if last is not None:
        ps_rate, from_ee = resolve_schedule_piece_rate(ps, ee_rows)
        if ps_rate <= 0:
            ps_rate = hourly_piece_rate_from_daily_capacity(int(ps.daily_capacity or 0))
            from_ee = False
        ps_eff = capacity_efficiency_factor(from_ee, float(ps.efficiency or 100)) * 100.0
        cand_date, cand_time = advance_line_cursor_after_slice(last, ps_rate, ps_eff)
    elif ps.end_date is not None:
        cand_date = ps.end_date
        cand_time = time(0, 0, 0)
    if (cand_date, cand_time) > (cursor_date, cursor_time):
        return cand_date, cand_time
    return cursor_date, cursor_time


def _schedule_has_replan_activity(info: dict, *, is_welding_line: bool) -> bool:
    if int(info.get("total_actual", 0) or 0) > 0:
        return True
    if not is_welding_line and int(info.get("total_defect", 0) or 0) > 0:
        return True
    return False


async def _fetch_line_replan_activity_maps(
    db: AsyncSession,
    sched_ids: List[int],
) -> tuple[dict[int, dict], dict[int, int]]:
    """日別明細集計と aps_batch_plans の upstream 合計（Step3 残数用）。"""
    agg_map: dict[int, dict] = {}
    upstream_by_schedule: dict[int, int] = {}
    if not sched_ids:
        return agg_map, upstream_by_schedule

    actual_agg_res = await db.execute(
        select(
            ScheduleDetail.schedule_id,
            func.coalesce(func.sum(ScheduleDetail.actual_qty), 0).label("total_actual"),
            func.coalesce(func.sum(ScheduleDetail.defect_qty), 0).label("total_defect"),
            func.coalesce(func.sum(ScheduleDetail.planned_qty), 0).label("total_planned"),
            func.max(
                case(
                    (ScheduleDetail.actual_qty > 0, ScheduleDetail.schedule_date),
                    else_=None,
                )
            ).label("last_actual_date"),
            func.max(
                case(
                    (ScheduleDetail.defect_qty > 0, ScheduleDetail.schedule_date),
                    else_=None,
                )
            ).label("last_defect_date"),
        )
        .where(ScheduleDetail.schedule_id.in_(sched_ids))
        .group_by(ScheduleDetail.schedule_id)
    )
    for row in actual_agg_res.all():
        agg_map[row.schedule_id] = {
            "total_actual": int(row.total_actual or 0),
            "total_defect": int(row.total_defect or 0),
            "total_planned": int(row.total_planned or 0),
            "last_actual_date": row.last_actual_date,
            "last_defect_date": row.last_defect_date,
        }

    upstream_defect_res = await db.execute(
        select(
            ApsBatchPlan.aps_schedule_id.label("sid"),
            func.coalesce(func.sum(ApsBatchPlan.upstream_defect_qty), 0).label("upstream_defect_total"),
        )
        .where(ApsBatchPlan.aps_schedule_id.in_(sched_ids))
        .group_by(ApsBatchPlan.aps_schedule_id)
    )
    upstream_by_schedule = {
        int(r.sid): int(r.upstream_defect_total or 0)
        for r in upstream_defect_res.all()
    }
    return agg_map, upstream_by_schedule


async def _activity_info_for_schedule(
    db: AsyncSession,
    sid: int,
    info: dict,
    forced_start_ps: Optional[date],
) -> dict:
    """開始日指定以降に実績・不良を集計し直す。"""
    period_actual = int(info.get("total_actual", 0) or 0)
    period_defect = int(info.get("total_defect", 0) or 0)
    lg = info.get("last_actual_date")
    lb = info.get("last_defect_date")
    if forced_start_ps is None:
        return info
    filt_res = await db.execute(
        select(
            func.coalesce(func.sum(ScheduleDetail.actual_qty), 0),
            func.coalesce(func.sum(ScheduleDetail.defect_qty), 0),
            func.max(
                case(
                    (ScheduleDetail.actual_qty > 0, ScheduleDetail.schedule_date),
                    else_=None,
                )
            ),
            func.max(
                case(
                    (ScheduleDetail.defect_qty > 0, ScheduleDetail.schedule_date),
                    else_=None,
                )
            ),
        ).where(
            ScheduleDetail.schedule_id == sid,
            ScheduleDetail.schedule_date >= forced_start_ps,
        )
    )
    filt_row = filt_res.one()
    return {
        **info,
        "total_actual": int(filt_row[0] or 0),
        "total_defect": int(filt_row[1] or 0),
        "last_actual_date": filt_row[2],
        "last_defect_date": filt_row[3],
    }


async def _replan_line_sequential_residual_aware(
    db: AsyncSession,
    *,
    all_line_schedules: List[ProductionSchedule],
    replan_start_anchor: Optional[date],
    agg_map: dict[int, dict],
    upstream_defect_by_schedule: dict[int, int],
    is_welding_line: bool,
    line_machine: Optional[Machine],
    shared_cal_map: dict[date, float],
    shared_slots: Dict[date, List[Any]],
    ee_rows: List[EquipmentEfficiency],
    include_debug: bool = False,
) -> tuple[List[ProductionSchedule], list[dict[str, Any]]]:
    """
    実績/不良ありライン向けの単一遍次排産（旧 Step3）。
    COMPLETED 占位 + 残数 run_engine。Step1 の全量無残数排産は行わない。
    """
    cursor_date_r = (
        replan_start_anchor
        or (all_line_schedules[0].start_date if all_line_schedules else None)
        or now_jst().date()
    )
    cursor_time_r = time(0, 0, 0)
    replanned_ids: set[int] = set()
    replan_debug_rows: list[dict[str, Any]] = []

    for idx, ps in enumerate(all_line_schedules):
        replannable = (ps.status or "").upper() in ("PLANNING", "IN_PROGRESS")
        if not replannable:
            cursor_date_r, cursor_time_r = await _line_cursor_after_schedule(
                db, ps, ee_rows, cursor_date_r, cursor_time_r
            )
            continue

        sid = ps.id
        info = await _activity_info_for_schedule(
            db,
            sid,
            agg_map.get(
                sid,
                {
                    "total_actual": 0,
                    "total_defect": 0,
                    "total_planned": 0,
                    "last_actual_date": None,
                    "last_defect_date": None,
                },
            ),
            getattr(ps, "forced_start_date", None),
        )
        lg = info.get("last_actual_date")
        lb = info.get("last_defect_date")
        last_activity_dt: Optional[date] = None
        if is_welding_line:
            last_activity_dt = lg
        elif lg is not None and lb is not None:
            last_activity_dt = max(lg, lb)
        else:
            last_activity_dt = lg or lb

        has_activity = _schedule_has_replan_activity(info, is_welding_line=is_welding_line)
        if has_activity and last_activity_dt is not None:
            replan_start = last_activity_dt + timedelta(days=1)
            if replan_start > cursor_date_r:
                cursor_date_r = replan_start
                cursor_time_r = time(0, 0, 0)

        forced_start = getattr(ps, "forced_start_date", None)
        effective_replan_start = cursor_date_r
        effective_replan_time = cursor_time_r
        if forced_start is not None and forced_start > effective_replan_start:
            effective_replan_start = forced_start
            effective_replan_time = time(0, 0, 0)

        period_actual = int(info.get("total_actual", 0) or 0)
        period_defect = int(info.get("total_defect", 0) or 0)

        if has_activity:
            planned_total = int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0)
            upstream_defect_total = int(upstream_defect_by_schedule.get(sid, 0) or 0)
            actual_done_for_engine, remaining = _replan_actual_done_and_remaining(
                planned_total,
                period_actual,
                period_defect,
                upstream_defect_total,
            )
            if include_debug:
                replan_debug_rows.append({
                    "schedule_id": int(ps.id),
                    "order_no": int(ps.order_no or 0),
                    "status": ps.status or "PLANNING",
                    "total_planned": int(info.get("total_planned", 0) or 0),
                    "total_actual": period_actual,
                    "total_defect": period_defect,
                    "upstream_defect_total": upstream_defect_total,
                    "remaining_for_replan": int(remaining or 0),
                    "planned_total": planned_total,
                    "actual_done_for_engine": int(actual_done_for_engine or 0),
                    "last_actual_date": lg.isoformat() if lg else None,
                    "last_defect_date": lb.isoformat() if lb else None,
                    "last_activity_date": last_activity_dt.isoformat() if last_activity_dt else None,
                    "replan_start_date": effective_replan_start.isoformat(),
                })
            ps = await run_engine(
                db,
                ps.id,
                override_start_date=effective_replan_start,
                override_start_time=effective_replan_time,
                actual_done_qty=actual_done_for_engine,
                use_setup_time=False,
                ps_obj=ps,
                machine_obj=line_machine,
                cal_map_preloaded=shared_cal_map,
                slots_by_date_preloaded=shared_slots,
                ee_rows_preloaded=ee_rows,
            )
        else:
            if include_debug:
                replan_debug_rows.append({
                    "schedule_id": int(ps.id),
                    "order_no": int(ps.order_no or 0),
                    "status": ps.status or "PLANNING",
                    "total_planned": int(info.get("total_planned", 0) or 0),
                    "total_actual": period_actual,
                    "total_defect": period_defect,
                    "remaining_for_replan": int(info.get("total_planned", 0) or 0),
                    "planned_total": int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0),
                    "actual_done_for_engine": 0,
                    "last_actual_date": None,
                    "last_defect_date": None,
                    "replan_start_date": effective_replan_start.isoformat(),
                })
            ps = await run_engine(
                db,
                ps.id,
                override_start_date=effective_replan_start,
                override_start_time=effective_replan_time,
                use_setup_time=idx != 0,
                ps_obj=ps,
                machine_obj=line_machine,
                cal_map_preloaded=shared_cal_map,
                slots_by_date_preloaded=shared_slots,
                ee_rows_preloaded=ee_rows,
            )

        replanned_ids.add(int(ps.id))
        await db.flush()
        cursor_date_r, cursor_time_r = await _line_cursor_after_schedule(
            db, ps, ee_rows, cursor_date_r, cursor_time_r
        )

    updated = [ps for ps in all_line_schedules if int(ps.id) in replanned_ids]
    return updated, replan_debug_rows


def _aps_machine_selectable_clause():
    """APS 下拉用：is_active が False でない、かつ status が active 系"""
    return and_(
        or_(Machine.is_active == True, Machine.is_active.is_(None)),
        or_(
            Machine.status == "active",
            Machine.status.is_(None),
            Machine.status == "",
        ),
    )


# ═══════════════════ Production Lines（データ源: machines）═══════════════════

@router.get("/lines", response_model=List[ProductionLineOut])
async def get_lines(
    processCd: Optional[str] = Query(
        None,
        description="工程CD（指定時は machines.machine_type が当該工程の名称またはCDと一致する設備のみ）",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(Machine).where(_aps_machine_selectable_clause())
    if processCd and processCd.strip():
        pc = processCd.strip()
        proc_result = await db.execute(select(Process).where(Process.process_cd == pc))
        proc = proc_result.scalar_one_or_none()
        if proc is None:
            return []
        pn = (proc.process_name or "").strip()
        pcc = (proc.process_cd or "").strip()
        type_conds = []
        if pn:
            type_conds.append(Machine.machine_type == pn)
        if pcc:
            type_conds.append(Machine.machine_type == pcc)
        if not type_conds:
            return []
        q = q.where(or_(*type_conds))
    result = await db.execute(
        q.order_by(Machine.machine_cd)
    )
    return [
        ProductionLineOut(
            id=r.id,
            line_code=r.machine_cd,
            line_name=(r.machine_name or "").strip(),
            default_work_hours=_dec(r.default_work_hours),
            is_active=bool(r.is_active) if r.is_active is not None else True,
        )
        for r in result.scalars().all()
    ]


@router.get("/line-replan-anchors", response_model=List[LineReplanAnchorOut])
async def get_line_replan_anchors(
    processCd: Optional[str] = Query(
        None,
        description="工程CD（指定時は GET /lines と同条件で machine_type により設備を絞る。成型計画画面では KT04 等）",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """APS 対象設備と保存済み再計算アンカー日。processCd 指定時は当該工程の設備のみ。"""
    q = select(Machine).where(_aps_machine_selectable_clause())
    if processCd and processCd.strip():
        pc = processCd.strip()
        proc_result = await db.execute(select(Process).where(Process.process_cd == pc))
        proc = proc_result.scalar_one_or_none()
        if proc is None:
            return []
        pn = (proc.process_name or "").strip()
        pcc = (proc.process_cd or "").strip()
        type_conds = []
        if pn:
            type_conds.append(Machine.machine_type == pn)
        if pcc:
            type_conds.append(Machine.machine_type == pcc)
        if not type_conds:
            return []
        q = q.where(or_(*type_conds))
    m_res = await db.execute(q.order_by(Machine.machine_cd))
    machines = m_res.scalars().all()
    ids = [int(m.id) for m in machines]
    anchor_map: Dict[int, date] = {}
    if ids:
        ar_res = await db.execute(select(ApsLineReplanAnchor).where(ApsLineReplanAnchor.line_id.in_(ids)))
        for row in ar_res.scalars().all():
            anchor_map[int(row.line_id)] = row.anchor_date
    return [
        LineReplanAnchorOut(
            line_id=int(m.id),
            line_code=(m.machine_cd or "").strip(),
            line_name=(m.machine_name or "").strip(),
            anchor_date=anchor_map.get(int(m.id)).isoformat() if int(m.id) in anchor_map else None,
        )
        for m in machines
    ]


@router.put("/line-replan-anchors")
async def put_line_replan_anchors(
    body: LineReplanAnchorsBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備別アンカー日を一括保存。anchor_date が空なら当該設備の行を削除（クエリ引数フォールバックに戻す）。"""
    for it in body.items:
        lid = int(it.line_id)
        m = await db.get(Machine, lid)
        if m is None:
            raise HTTPException(400, f"設備 machines.id={lid} が存在しません")
        raw = (it.anchor_date or "").strip() if it.anchor_date is not None else ""
        if raw:
            try:
                ad = date.fromisoformat(raw[:10])
            except ValueError:
                raise HTTPException(400, f"anchor_date は YYYY-MM-DD 形式で指定してください: {it.anchor_date}")
            ex = await db.get(ApsLineReplanAnchor, lid)
            if ex is None:
                db.add(ApsLineReplanAnchor(line_id=lid, anchor_date=ad))
            else:
                ex.anchor_date = ad
        else:
            await db.execute(delete(ApsLineReplanAnchor).where(ApsLineReplanAnchor.line_id == lid))
    await db.flush()
    return {"success": True, "message": "再計算アンカー日を保存しました"}


@router.post("/lines")
async def create_line(
    line_code: str,
    default_work_hours: float = 0.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    cd = line_code.strip()
    dup = await db.execute(select(Machine).where(Machine.machine_cd == cd))
    if dup.scalar_one_or_none():
        raise HTTPException(400, "同じ設備コードが既に存在します")
    row = Machine(
        machine_cd=cd,
        machine_name=cd,
        default_work_hours=Decimal(str(default_work_hours)) if default_work_hours else None,
        is_active=True,
        status="active",
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return {"success": True, "data": {"id": row.id, "line_code": row.machine_cd}}


@router.get("/equipment-efficiency-products", response_model=List[EquipmentEfficiencyProductOut])
async def get_equipment_efficiency_products_by_machine(
    machineId: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    選択設備（machines.id）に紐づく equipment_efficiency の製品一覧。
    machine_cd 一致、または machines_name が設備名／設備コードと一致する行を対象。
    """
    machine = await db.get(Machine, machineId)
    if machine is None:
        raise HTTPException(404, "設備が見つかりません")

    m_cd = (machine.machine_cd or "").strip()
    m_name = (machine.machine_name or "").strip()
    match_conds = []
    if m_cd:
        match_conds.append(EquipmentEfficiency.machine_cd == m_cd)
        match_conds.append(EquipmentEfficiency.machines_name == m_cd)
    if m_name:
        match_conds.append(EquipmentEfficiency.machines_name == m_name)
    if not match_conds:
        return []

    q = (
        select(EquipmentEfficiency)
        .where(or_(*match_conds))
        .where(or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status == 1))
        .order_by(EquipmentEfficiency.product_name, EquipmentEfficiency.product_cd, EquipmentEfficiency.id)
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    seen: set[tuple[str, str]] = set()
    candidates: list[EquipmentEfficiency] = []
    for r in rows:
        key = (r.product_cd or "", r.product_name or "")
        if key in seen:
            continue
        seen.add(key)
        candidates.append(r)

    cds_order: list[str] = []
    for r in candidates:
        cd = (r.product_cd or "").strip()
        if cd and cd not in cds_order:
            cds_order.append(cd)

    lot_by_cd: dict[str, int] = {}
    if cds_order:
        pr_res = await db.execute(
            select(Product.product_cd, Product.lot_size).where(Product.product_cd.in_(cds_order))
        )
        for prow in pr_res.mappings().all():
            pcd = (prow.get("product_cd") or "").strip()
            if not pcd:
                continue
            ls = prow.get("lot_size")
            if ls is not None:
                lot_by_cd[pcd] = int(ls)

    out: list[EquipmentEfficiencyProductOut] = []
    for r in candidates:
        cd = (r.product_cd or "").strip()
        out.append(
            EquipmentEfficiencyProductOut(
                id=r.id,
                product_cd=r.product_cd,
                product_name=r.product_name,
                efficiency_rate=_dec(r.efficiency_rate),
                step_time=int(r.step_time) if r.step_time is not None else None,
                lot_size=lot_by_cd.get(cd) if cd else None,
            )
        )
    return out


# ═══════════════════ Line Capacities ═══════════════════

@router.get("/line-capacities", response_model=List[LineCapacityOut])
async def get_line_capacities(
    lineId: int = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    result = await db.execute(
        select(LineCapacity)
        .where(
            LineCapacity.line_id == lineId,
            LineCapacity.work_date >= sd,
            LineCapacity.work_date <= ed,
        )
        .order_by(LineCapacity.work_date)
    )
    return [
        LineCapacityOut(
            id=r.id,
            line_id=r.line_id,
            work_date=r.work_date,
            available_hours=_dec(r.available_hours),
            note=r.note,
        )
        for r in result.scalars().all()
    ]


@router.post("/line-capacities/batch")
async def batch_upsert_line_capacities(
    body: LineCapacityBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    count = 0
    for item in body.items:
        existing = await db.execute(
            select(LineCapacity).where(
                LineCapacity.line_id == item.line_id,
                LineCapacity.work_date == item.work_date,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.available_hours = Decimal(str(item.available_hours))
            row.note = item.note
        else:
            db.add(LineCapacity(
                line_id=item.line_id,
                work_date=item.work_date,
                available_hours=Decimal(str(item.available_hours)),
                note=item.note,
            ))
        count += 1
    await db.flush()
    return {"success": True, "data": {"count": count}}


# ═══════════════════ Line Capacity Time Slots ═══════════════════

def _is_midnight_time(t) -> bool:
    return (
        t.hour == 0
        and t.minute == 0
        and t.second == 0
        and getattr(t, "microsecond", 0) == 0
    )


@router.get("/line-capacity-slots", response_model=List[DaySlotsOut])
async def get_line_capacity_slots(
    lineId: int = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    slots_result = await db.execute(
        select(LineCapacityTimeSlot)
        .where(
            LineCapacityTimeSlot.line_id == lineId,
            LineCapacityTimeSlot.work_date >= sd,
            LineCapacityTimeSlot.work_date <= ed,
        )
        .order_by(LineCapacityTimeSlot.work_date, LineCapacityTimeSlot.sort_order)
    )
    slots = slots_result.scalars().all()

    cap_result = await db.execute(
        select(LineCapacity).where(
            LineCapacity.line_id == lineId,
            LineCapacity.work_date >= sd,
            LineCapacity.work_date <= ed,
        )
    )
    cap_map = {r.work_date: _dec(r.available_hours) for r in cap_result.scalars().all()}

    grouped_orm: dict[date, list] = defaultdict(list)
    for s in slots:
        grouped_orm[s.work_date].append(s)

    result = []
    d = sd
    while d <= ed:
        orm_list = grouped_orm.get(d, [])
        if orm_list:
            total = productive_hours_from_slot_rows(orm_list)
        else:
            total = float(cap_map.get(d, 0))
        slot_list = [
            TimeSlotOut(
                id=s.id,
                start_time=s.start_time,
                end_time=s.end_time,
                sort_order=s.sort_order,
                is_rest=bool(getattr(s, "is_rest", False)),
            )
            for s in orm_list
        ]
        result.append(DaySlotsOut(work_date=d, available_hours=total, slots=slot_list))
        d += timedelta(days=1)

    return result


@router.put("/line-capacity-slots/batch")
async def batch_upsert_line_capacity_slots(
    body: DaySlotsBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    line = await db.get(Machine, body.line_id)
    if line is None:
        raise HTTPException(404, "設備が見つかりません")

    updated_days = 0
    for day_body in body.days:
        for slot in day_body.slots:
            if slot.start_time == slot.end_time:
                if not (_is_midnight_time(slot.start_time) and _is_midnight_time(slot.end_time)):
                    raise HTTPException(400, f"{day_body.work_date}: start_time と end_time が同一です")

        await db.execute(
            delete(LineCapacityTimeSlot).where(
                LineCapacityTimeSlot.line_id == body.line_id,
                LineCapacityTimeSlot.work_date == day_body.work_date,
            )
        )

        for idx, slot in enumerate(day_body.slots):
            db.add(LineCapacityTimeSlot(
                line_id=body.line_id,
                work_date=day_body.work_date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                sort_order=slot.sort_order if slot.sort_order else idx,
                is_rest=bool(slot.is_rest),
            ))
        total_hours = productive_hours_from_slot_rows(day_body.slots)

        existing_cap = await db.execute(
            select(LineCapacity).where(
                LineCapacity.line_id == body.line_id,
                LineCapacity.work_date == day_body.work_date,
            )
        )
        cap_row = existing_cap.scalar_one_or_none()
        if cap_row:
            cap_row.available_hours = Decimal(str(round(total_hours, 2)))
            cap_row.note = "時間帯から算出"
        else:
            db.add(LineCapacity(
                line_id=body.line_id,
                work_date=day_body.work_date,
                available_hours=Decimal(str(round(total_hours, 2))),
                note="時間帯から算出",
            ))
        updated_days += 1

    await db.flush()
    return {"success": True, "data": {"updated_days": updated_days}}


# ═══════════════════ Line Product Standard ═══════════════════

@router.get("/line-product-standards", response_model=List[LineProductStandardOut])
async def get_line_product_standards(
    lineId: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(LineProductStandard)
    if lineId is not None:
        q = q.where(LineProductStandard.line_id == lineId)
    q = q.order_by(LineProductStandard.line_id, LineProductStandard.product_cd)
    result = await db.execute(q)
    return [
        LineProductStandardOut(
            id=r.id,
            line_id=r.line_id,
            product_cd=r.product_cd,
            std_qty_per_hour=_dec(r.std_qty_per_hour),
            setup_time_min=int(r.setup_time_min or 0),
            efficiency_pct=_dec(r.efficiency_pct),
        )
        for r in result.scalars().all()
    ]


@router.post("/line-product-standards", response_model=LineProductStandardOut)
async def create_line_product_standard(
    body: LineProductStandardBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = LineProductStandard(
        line_id=body.line_id,
        product_cd=body.product_cd,
        std_qty_per_hour=Decimal(str(body.std_qty_per_hour)),
        setup_time_min=body.setup_time_min,
        efficiency_pct=Decimal(str(body.efficiency_pct)),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return LineProductStandardOut(
        id=row.id,
        line_id=row.line_id,
        product_cd=row.product_cd,
        std_qty_per_hour=_dec(row.std_qty_per_hour),
        setup_time_min=int(row.setup_time_min or 0),
        efficiency_pct=_dec(row.efficiency_pct),
    )


@router.put("/line-product-standards/{standard_id}", response_model=LineProductStandardOut)
async def update_line_product_standard(
    standard_id: int,
    body: LineProductStandardBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(LineProductStandard, standard_id)
    if row is None:
        raise HTTPException(404, "標準情報が見つかりません")
    row.line_id = body.line_id
    row.product_cd = body.product_cd
    row.std_qty_per_hour = Decimal(str(body.std_qty_per_hour))
    row.setup_time_min = body.setup_time_min
    row.efficiency_pct = Decimal(str(body.efficiency_pct))
    await db.flush()
    return LineProductStandardOut(
        id=row.id,
        line_id=row.line_id,
        product_cd=row.product_cd,
        std_qty_per_hour=_dec(row.std_qty_per_hour),
        setup_time_min=int(row.setup_time_min or 0),
        efficiency_pct=_dec(row.efficiency_pct),
    )


@router.delete("/line-product-standards/{standard_id}")
async def delete_line_product_standard(
    standard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(LineProductStandard, standard_id)
    if row is None:
        raise HTTPException(404, "標準情報が見つかりません")
    await db.delete(row)
    await db.flush()
    return {"success": True}


# ═══════════════════ Production Schedules (CRUD) ═══════════════════

def _schedule_month_overlap_clause(month_yyyy_mm: str):
    """当該暦月と start/end または schedule_details の日付が重なる条件"""
    from calendar import monthrange

    parts = month_yyyy_mm.strip().split("-")
    if len(parts) != 2:
        raise ValueError("productionMonth は YYYY-MM 形式で指定してください")
    try:
        y = int(parts[0])
        m = int(parts[1])
    except ValueError as e:
        raise ValueError("productionMonth が無効です") from e
    if m < 1 or m > 12:
        raise ValueError("月が無効です")
    month_start = date(y, m, 1)
    month_end = date(y, m, monthrange(y, m)[1])
    detail_in_month = exists().where(
        and_(
            ScheduleDetail.schedule_id == ProductionSchedule.id,
            ScheduleDetail.schedule_date >= month_start,
            ScheduleDetail.schedule_date <= month_end,
        )
    )
    return or_(
        and_(
            ProductionSchedule.start_date.isnot(None),
            ProductionSchedule.end_date.isnot(None),
            ProductionSchedule.start_date <= month_end,
            ProductionSchedule.end_date >= month_start,
        ),
        and_(
            ProductionSchedule.start_date.isnot(None),
            ProductionSchedule.end_date.is_(None),
            ProductionSchedule.start_date <= month_end,
        ),
        and_(
            ProductionSchedule.start_date.is_(None),
            ProductionSchedule.end_date.isnot(None),
            ProductionSchedule.end_date >= month_start,
        ),
        detail_in_month,
    )


async def _machine_ids_for_process_cd(db: AsyncSession, process_cd: str) -> List[int]:
    pc = process_cd.strip()
    proc_result = await db.execute(select(Process).where(Process.process_cd == pc))
    proc = proc_result.scalar_one_or_none()
    if proc is None:
        return []
    pn = (proc.process_name or "").strip()
    pcc = (proc.process_cd or "").strip()
    type_conds = []
    if pn:
        type_conds.append(Machine.machine_type == pn)
    if pcc:
        type_conds.append(Machine.machine_type == pcc)
    if not type_conds:
        return []
    q = select(Machine.id).where(_aps_machine_selectable_clause()).where(or_(*type_conds))
    result = await db.execute(q)
    return [row[0] for row in result.all()]


def _schedule_with_line_out(ps: ProductionSchedule, machine: Machine) -> ScheduleWithLineOut:
    base = _schedule_to_out(ps)
    return ScheduleWithLineOut(
        **base.model_dump(),
        line_code=(machine.machine_cd or "").strip(),
        line_name=(machine.machine_name or "").strip(),
    )


@router.get("/schedules", response_model=List[ScheduleWithLineOut])
async def list_schedules(
    lineId: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    processCd: Optional[str] = Query(
        None,
        description="工程CD（指定時は当該工程の設備に紐づく工単のみ）",
    ),
    productionMonth: Optional[str] = Query(
        None,
        description="YYYY-MM。当該月と開始/終了日または日別明細が重なる工単のみ",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    # 終了日が今日より前の工単は状態を完了へ自動補正（表示だけでなくDB実体も更新）。
    today_jst = now_jst().date()
    await db.execute(
        update(ProductionSchedule)
        .where(
            ProductionSchedule.end_date.isnot(None),
            ProductionSchedule.end_date < today_jst,
            ProductionSchedule.status != "COMPLETED",
        )
        .values(status="COMPLETED")
    )
    await db.commit()

    if processCd and processCd.strip():
        proc_line_ids = await _machine_ids_for_process_cd(db, processCd.strip())
        if not proc_line_ids:
            return []

    q = select(ProductionSchedule, Machine).join(Machine, Machine.id == ProductionSchedule.line_id)
    conditions = []
    if lineId is not None:
        conditions.append(ProductionSchedule.line_id == lineId)
    if status:
        conditions.append(ProductionSchedule.status == status)
    if processCd and processCd.strip():
        conditions.append(ProductionSchedule.line_id.in_(proc_line_ids))
    if productionMonth and productionMonth.strip():
        try:
            conditions.append(_schedule_month_overlap_clause(productionMonth.strip()))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    if conditions:
        q = q.where(and_(*conditions))
    q = q.order_by(ProductionSchedule.line_id, ProductionSchedule.order_no, ProductionSchedule.id)
    try:
        result = await db.execute(q)
    except (OperationalError, ProgrammingError) as e:
        msg = (
            "計画一覧の取得に失敗しました。production_schedules.product_cd 等が無い、またはマイグレーション未適用の可能性があります。"
            " `py scripts/bootstrap_full_database.py` を実行するか、`backend/database/migrations/02_baseline_full_schema.sql` を適用してください。"
        )
        if getattr(e, "orig", None):
            msg = f"{msg} ({e.orig!s})"
        raise HTTPException(status_code=500, detail=msg) from e
    return [_schedule_with_line_out(ps, m) for ps, m in result.all()]


@router.post("/schedules", response_model=ScheduleOut)
async def create_schedule(
    body: ScheduleCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    machine = await db.get(Machine, body.line_id)
    if machine is None:
        raise HTTPException(status_code=400, detail="指定された設備IDが存在しません（machines テーブルを確認してください）")

    setup_time = int(body.setup_time or 0)
    efficiency = float(body.efficiency) if body.efficiency is not None else 100.0
    daily_capacity = int(body.daily_capacity or 0)
    prev_carry = int(body.prev_month_carryover or 0)
    lot_q = int(body.lot_qty or 0)

    product_cd = (body.product_cd or "").strip() or None
    item_name = (body.item_name or "").strip()
    if not item_name:
        raise HTTPException(status_code=400, detail="品名（item_name）が空です")

    batch_count = int(body.planned_batch_count or 0)
    lot_snap = int(body.lot_size_snapshot or 0)

    if batch_count > 0:
        if lot_snap <= 0:
            if product_cd:
                pr = await db.execute(
                    select(Product.lot_size).where(Product.product_cd == product_cd)
                )
                row = pr.scalar_one_or_none()
                lot_snap = int(row) if row else 0
            if lot_snap <= 0:
                raise HTTPException(
                    400,
                    "ロットサイズが未設定です。製品マスタの lot_size を先に登録してください。",
                )
        planned_qty = batch_count * lot_snap
    else:
        planned_qty = int(body.planned_process_qty or 0)

    # line_product_standard 未適用（094）だと SELECT 時点で ProgrammingError になり得る → flush 前で未捕捉だと素の 500 になる
    std: LineProductStandard | None = None
    if product_cd:
        try:
            std_result = await db.execute(
                select(LineProductStandard).where(
                    LineProductStandard.line_id == body.line_id,
                    LineProductStandard.product_cd == product_cd,
                )
            )
            std = std_result.scalar_one_or_none()
        except ProgrammingError:
            await db.rollback()
            std = None

    if std:
        line = machine
        default_hours = float(line.default_work_hours or 0) if line else 8.0
        if default_hours <= 0:
            default_hours = 8.0
        if body.setup_time == 0 and std.setup_time_min:
            setup_time = int(std.setup_time_min)
        if body.efficiency == 100.0 and std.efficiency_pct:
            efficiency = float(std.efficiency_pct)
        if body.daily_capacity == 0 or daily_capacity == int(body.daily_capacity):
            derived = int(float(std.std_qty_per_hour) * default_hours)
            if derived > 0:
                daily_capacity = derived

    ps = ProductionSchedule(
        line_id=body.line_id,
        order_no=body.order_no,
        order_id=body.order_id,
        item_name=item_name[:100],
        product_cd=product_cd,
        material_shortage=bool(body.material_shortage),
        lot_qty=lot_q,
        planned_batch_count=batch_count,
        lot_size_snapshot=lot_snap,
        planned_process_qty=planned_qty,
        prev_month_carryover=prev_carry,
        due_date=body.due_date,
        material_date=body.material_date,
        forced_start_date=body.forced_start_date,
        setup_time=setup_time,
        efficiency=Decimal(str(efficiency)),
        daily_capacity=daily_capacity,
        start_date=body.start_date,
        status="PLANNING",
    )
    db.add(ps)
    try:
        await db.flush()
        await db.refresh(ps)
    except IntegrityError as e:
        await db.rollback()
        _suffix = f" ({e.orig!s})" if getattr(e, "orig", None) else f" ({e!s})"
        raise HTTPException(
            status_code=400,
            detail=(
                "計画の保存に失敗しました。line_id が machines.id と一致するか、"
                "マイグレーション 096（APS 外部キー→machines）を適用済みか確認してください。"
                + _suffix
            ),
        ) from e
    except (OperationalError, ProgrammingError) as e:
        await db.rollback()
        msg = (
            "計画の保存に失敗しました。production_schedules に product_cd 列が無い等、マイグレーション未適用の可能性があります。"
            " `py scripts/bootstrap_full_database.py` を実行するか、`backend/database/migrations/02_baseline_full_schema.sql` を適用してください。"
        )
        if getattr(e, "orig", None):
            msg = f"{msg} ({e.orig!s})"
        raise HTTPException(status_code=500, detail=msg) from e
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                "計画の保存中にデータベースエラーが発生しました。"
                "096（FK→machines）・095/098（product_cd 列）の適用状況を確認してください。"
                f" ({getattr(e, 'orig', None) or e!s})"
            ),
        ) from e

    if body.run_immediately:
        try:
            ps = await run_engine(
                db,
                ps.id,
                override_start_date=body.start_date,
                use_setup_time=int(ps.order_no or 0) != 1,
            )
            await db.flush()
            # 計画一覧へ計画を追加した直後にバッチ番号（aps_batch_plans）と
            # instruction_plans の各ロット行を生成する（cutting_management 連携の前段）。
            await _sync_instruction_plans_from_aps_schedule(db, ps, machine=machine)
            await db.flush()
        except ValueError as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) from e

    return _schedule_to_out(ps)


@router.put("/schedules/{schedule_id}", response_model=ScheduleOut)
async def update_schedule(
    schedule_id: int,
    body: ScheduleUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise HTTPException(404, "工単が見つかりません")

    for field in (
        "line_id", "order_no", "order_id", "item_name", "product_cd",
        "material_shortage", "lot_qty", "planned_process_qty", "prev_month_carryover",
        "due_date", "material_date", "setup_time", "daily_capacity", "start_date",
    ):
        val = getattr(body, field, None)
        if val is not None:
            setattr(ps, field, val)
    # Optional[date] を null で明示クリアできるよう、存在判定で反映する。
    if "forced_start_date" in body.model_fields_set:
        ps.forced_start_date = body.forced_start_date
    if body.efficiency is not None:
        ps.efficiency = Decimal(str(body.efficiency))

    if body.planned_batch_count is not None:
        ps.planned_batch_count = body.planned_batch_count
        if body.lot_size_snapshot is not None and body.lot_size_snapshot > 0:
            ps.lot_size_snapshot = body.lot_size_snapshot
        snap = int(ps.lot_size_snapshot or 0)
        if snap <= 0:
            pcd = (ps.product_cd or "").strip()
            if pcd:
                pr = await db.execute(
                    select(Product.lot_size).where(Product.product_cd == pcd)
                )
                row = pr.scalar_one_or_none()
                snap = int(row) if row else 0
                ps.lot_size_snapshot = snap
        if snap > 0 and body.planned_batch_count > 0:
            new_total = body.planned_batch_count * snap
            already_produced = await _sum_actual_qty(db, ps.id)
            if new_total < already_produced:
                min_batches = math.ceil(already_produced / snap) if snap > 0 else 0
                raise HTTPException(
                    400,
                    f"既に {already_produced} 本の実績があるため、"
                    f"ロット数は {min_batches} 以上にしてください。",
                )
            ps.planned_process_qty = new_total

    await db.flush()

    if body.run_immediately:
        ps = await run_engine(
            db,
            ps.id,
            override_start_date=body.start_date or ps.start_date,
            use_setup_time=int(ps.order_no or 0) != 1,
        )
        await db.flush()
        # 計画一覧の数量/順位等が変わった際、aps_batch_plans / instruction_plans を追従させる
        # （cutting_management に取り込み済みロットの管理コードは保持される）。
        await _sync_instruction_plans_from_aps_schedule(db, ps)
        await db.flush()

    return _schedule_to_out(ps)


@router.post("/schedules/{schedule_id}/append-planned")
async def append_schedule_planned_qty(
    schedule_id: int,
    body: ScheduleAppendPlannedBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    合計(本)増加時：既存日別計画の末尾に追記し、後続順位のみ必要なら再串接。
    ライン全件 replan-sequence による日別組替えを避ける。
    """
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise HTTPException(404, "工単が見つかりません")

    line_machine = await db.get(Machine, ps.line_id)
    if line_machine is None:
        raise HTTPException(404, "設備が見つかりません")

    ee_rows = await _load_equipment_efficiency_rows_for_machine(db, line_machine)
    cal_start = ps.start_date or now_jst().date()
    cal_end_d = cal_start + timedelta(days=APS_CALENDAR_PRELOAD_DAYS)
    cal_result = await db.execute(
        select(LineCapacity)
        .where(
            LineCapacity.line_id == ps.line_id,
            LineCapacity.work_date >= cal_start,
            LineCapacity.work_date <= cal_end_d,
        )
    )
    shared_cal_map = {
        row.work_date: float(row.available_hours) for row in cal_result.scalars().all()
    }
    shared_slots = await _fetch_slots_by_date(db, ps.line_id, cal_start, cal_end_d)

    try:
        ps, new_date, new_time, appended = await run_engine_append_qty(
            db,
            schedule_id,
            int(body.additional_qty),
            ps_obj=ps,
            machine_obj=line_machine,
            cal_map_preloaded=shared_cal_map,
            slots_by_date_preloaded=shared_slots,
            ee_rows_preloaded=ee_rows,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    await db.flush()
    following = await replan_following_schedules_on_line(
        db,
        int(ps.line_id),
        schedule_id,
        new_date,
        new_time,
        machine_obj=line_machine,
        cal_map_preloaded=shared_cal_map,
        slots_by_date_preloaded=shared_slots,
        ee_rows_preloaded=ee_rows,
    )
    for fps in following:
        await _sync_actual_from_stock_logs(db, fps, machine=line_machine)
    await db.flush()

    is_forming = await _machine_matches_process_cd(
        db, line_machine, _APS_INSTRUCTION_PLANS_SYNC_PROCESS_CD
    )
    if is_forming:
        await _sync_instruction_plans_from_aps_schedule(
            db, ps, machine=line_machine, is_forming_line=True
        )
        for fps in following:
            await _sync_instruction_plans_from_aps_schedule(
                db, fps, machine=line_machine, is_forming_line=True
            )
    await db.flush()

    return {
        "success": True,
        "appended_qty": int(appended),
        "following_replanned": len(following),
        "data": _schedule_to_out(ps).model_dump(),
    }


@router.put("/schedules/{schedule_id}/daily-planned")
async def update_schedule_daily_planned_qty(
    schedule_id: int,
    body: ScheduleDailyPlanUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise HTTPException(404, "工単が見つかりません")

    today_jst = now_jst().date()
    if body.schedule_date > today_jst:
        raise HTTPException(400, "日別計画数を編集できるのは本日以前のみです")

    detail_q = await db.execute(
        select(ScheduleDetail).where(
            ScheduleDetail.schedule_id == schedule_id,
            ScheduleDetail.schedule_date == body.schedule_date,
        )
    )
    detail = detail_q.scalar_one_or_none()
    if detail is None:
        detail = ScheduleDetail(
            schedule_id=schedule_id,
            schedule_date=body.schedule_date,
            planned_qty=int(body.planned_qty),
            actual_qty=0,
            defect_qty=0,
            remaining_qty=int(body.planned_qty),
        )
        db.add(detail)
    else:
        detail.planned_qty = int(body.planned_qty)
        detail.remaining_qty = int(detail.planned_qty or 0) - int(detail.actual_qty or 0) - int(detail.defect_qty or 0)

    await db.flush()

    # 日别计划手动修正（本日以前）は明細のみ更新し、工単総量（planned_process_qty）は不変とする。
    # 过去日の補正値で工単の「合計(本)」が変動してしまう問題を防ぐ。
    await db.flush()

    return {
        "success": True,
        "schedule_id": schedule_id,
        "schedule_date": body.schedule_date.isoformat(),
        "planned_qty": int(body.planned_qty),
        "planned_process_qty": int(ps.planned_process_qty or 0),
    }


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise HTTPException(404, "工単が見つかりません")

    # APS を削除する場合、紐づく aps_batch_plans → instruction_plans も削除する
    try:
        batch_q = await db.execute(
            select(ApsBatchPlan.id).where(ApsBatchPlan.aps_schedule_id == schedule_id)
        )
        batch_ids = [int(x[0]) for x in batch_q.all()]
        if batch_ids:
            for bid in batch_ids:
                await db.execute(
                    text("DELETE FROM instruction_plans WHERE aps_batch_plan_id = :bid"),
                    {"bid": bid},
                )
            await db.execute(
                delete(ApsBatchPlan).where(ApsBatchPlan.aps_schedule_id == schedule_id)
            )
    except OperationalError:
        # instruction_plans が存在しない/権限不足の環境では APS の削除だけ行う
        pass

    await db.delete(ps)
    await db.flush()
    return {"success": True, "message": "削除しました"}


@router.post("/schedules/{schedule_id}/run")
async def run_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise HTTPException(404, "工単が見つかりません")
    ps = await run_engine(
        db,
        schedule_id,
        override_start_date=ps.start_date,
        use_setup_time=int(ps.order_no or 0) != 1,
    )
    await db.flush()
    # エンジン再計算後は aps_batch_plans / instruction_plans のロット行を計画一覧と整合させる。
    await _sync_instruction_plans_from_aps_schedule(db, ps)
    await db.flush()
    return {"success": True, "data": _schedule_to_out(ps).model_dump()}


# ═══════════════════ Scheduling Grid ═══════════════════

@router.get("/scheduling/grid", response_model=SchedulingGridResponse)
async def get_scheduling_grid(
    startDate: str = Query(...),
    endDate: str = Query(...),
    lineId: Optional[int] = Query(None),
    processCd: Optional[str] = Query(
        None,
        description="工程CD（lineId 未指定時、当該工程の設備のみをグリッド対象に）",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    dates_list: list[str] = []
    d = sd
    while d <= ed:
        dates_list.append(d.isoformat())
        d += timedelta(days=1)
    today_jst = now_jst().date()

    # 設備取得（machines）
    line_q = select(Machine).where(_aps_machine_selectable_clause())
    if lineId is not None:
        line_q = line_q.where(Machine.id == lineId)
    elif processCd and processCd.strip():
        proc_ids = await _machine_ids_for_process_cd(db, processCd.strip())
        if not proc_ids:
            return SchedulingGridResponse(dates=dates_list, blocks=[])
        line_q = line_q.where(Machine.id.in_(proc_ids))
    line_q = line_q.order_by(Machine.machine_cd)
    lines_result = await db.execute(line_q)
    lines = lines_result.scalars().all()
    if not lines:
        return SchedulingGridResponse(dates=dates_list, blocks=[])

    line_ids = [int(line.id) for line in lines]

    # ── 全設備分を一括先読み（P0: 線体ループ内 DB 往復を排除） ──
    cal_result = await db.execute(
        select(LineCapacity).where(
            LineCapacity.line_id.in_(line_ids),
            LineCapacity.work_date >= sd,
            LineCapacity.work_date <= ed,
        )
    )
    calendar_by_line: dict[int, dict[str, float]] = defaultdict(dict)
    for row in cal_result.scalars().all():
        calendar_by_line[int(row.line_id)][row.work_date.isoformat()] = _dec(row.available_hours)

    sched_result = await db.execute(
        select(ProductionSchedule)
        .where(ProductionSchedule.line_id.in_(line_ids))
        .order_by(
            ProductionSchedule.line_id,
            ProductionSchedule.order_no.is_(None),
            ProductionSchedule.order_no.asc(),
            ProductionSchedule.id,
        )
    )
    all_schedules = sched_result.scalars().all()
    schedules_by_line: dict[int, list[ProductionSchedule]] = defaultdict(list)
    sid_to_line_id: dict[int, int] = {}
    all_schedule_ids: list[int] = []
    for ps in all_schedules:
        lid = int(ps.line_id)
        schedules_by_line[lid].append(ps)
        sid = int(ps.id)
        sid_to_line_id[sid] = lid
        all_schedule_ids.append(sid)

    ee_by_line = await _load_equipment_efficiency_rows_for_machines(db, lines)

    detail_planned_rows: dict[int, dict[str, int]] = defaultdict(dict)
    detail_actual_rows: dict[int, dict[str, int]] = defaultdict(dict)
    detail_defect_rows: dict[int, dict[str, int]] = defaultdict(dict)
    upstream_defect_total_rows: dict[int, int] = defaultdict(int)
    slice_rows: dict[int, dict[str, int]] = defaultdict(dict)
    slice_bounds: dict[int, tuple[Optional[date], Optional[date]]] = {}
    slices_by_sched: dict[int, list] = defaultdict(list)
    line_slice_dates_by_line: dict[int, set[str]] = defaultdict(set)

    if all_schedule_ids:
        detail_agg_result = await db.execute(
            select(
                ScheduleDetail.schedule_id,
                ScheduleDetail.schedule_date,
                func.coalesce(func.sum(ScheduleDetail.planned_qty), 0),
                func.coalesce(func.sum(ScheduleDetail.actual_qty), 0),
                func.coalesce(func.sum(ScheduleDetail.defect_qty), 0),
            )
            .where(
                ScheduleDetail.schedule_id.in_(all_schedule_ids),
                ScheduleDetail.schedule_date >= sd,
                ScheduleDetail.schedule_date <= ed,
            )
            .group_by(ScheduleDetail.schedule_id, ScheduleDetail.schedule_date)
        )
        for sid, d0, p_sum, a_sum, df_sum in detail_agg_result.all():
            if sid is None or d0 is None:
                continue
            dk = d0.isoformat()
            detail_planned_rows[int(sid)][dk] = int(p_sum or 0)
            detail_actual_rows[int(sid)][dk] = int(a_sum or 0)
            detail_defect_rows[int(sid)][dk] = int(df_sum or 0)

        upstream_agg_result = await db.execute(
            select(
                ApsBatchPlan.aps_schedule_id,
                func.coalesce(func.sum(ApsBatchPlan.upstream_defect_qty), 0),
            )
            .where(ApsBatchPlan.aps_schedule_id.in_(all_schedule_ids))
            .group_by(ApsBatchPlan.aps_schedule_id)
        )
        for sid, u_sum in upstream_agg_result.all():
            if sid is None:
                continue
            upstream_defect_total_rows[int(sid)] = int(u_sum or 0)

        slice_agg_result = await db.execute(
            select(
                ScheduleSliceAllocation.schedule_id,
                ScheduleSliceAllocation.work_date,
                func.coalesce(func.sum(ScheduleSliceAllocation.planned_qty), 0),
            )
            .where(
                ScheduleSliceAllocation.schedule_id.in_(all_schedule_ids),
                ScheduleSliceAllocation.work_date >= sd,
                ScheduleSliceAllocation.work_date <= ed,
            )
            .group_by(
                ScheduleSliceAllocation.schedule_id,
                ScheduleSliceAllocation.work_date,
            )
        )
        for sid, wd, s_sum in slice_agg_result.all():
            if sid is None or wd is None:
                continue
            wdk = wd.isoformat()
            sid_i = int(sid)
            slice_rows[sid_i][wdk] = int(s_sum or 0)
            lid = sid_to_line_id.get(sid_i)
            if lid is not None:
                line_slice_dates_by_line[lid].add(wdk)

        slice_bounds_result = await db.execute(
            select(
                ScheduleSliceAllocation.schedule_id,
                func.min(ScheduleSliceAllocation.work_date),
                func.max(ScheduleSliceAllocation.work_date),
            )
            .where(ScheduleSliceAllocation.schedule_id.in_(all_schedule_ids))
            .group_by(ScheduleSliceAllocation.schedule_id)
        )
        for sid, min_d, max_d in slice_bounds_result.all():
            if sid is None:
                continue
            slice_bounds[int(sid)] = (min_d, max_d)

        slice_detail_result = await db.execute(
            select(ScheduleSliceAllocation)
            .where(ScheduleSliceAllocation.schedule_id.in_(all_schedule_ids))
            .order_by(
                ScheduleSliceAllocation.schedule_id,
                ScheduleSliceAllocation.work_date,
                ScheduleSliceAllocation.period_start,
                ScheduleSliceAllocation.sort_order,
                ScheduleSliceAllocation.id,
            )
        )
        for sl in slice_detail_result.scalars().all():
            slices_by_sched[int(sl.schedule_id)].append(sl)

    batch_by_sid, lot_upstream_state = await _schedule_batch_upstream_context(db, all_schedule_ids)

    blocks: list[LineGridBlock] = []

    for line in lines:
        schedules = schedules_by_line.get(int(line.id), [])
        ee_rows = ee_by_line.get(int(line.id), [])
        calendar_map = dict(calendar_by_line.get(int(line.id), {}))
        line_slice_dates = line_slice_dates_by_line.get(int(line.id), set())

        # 计算每个工单的“下一个工单起点边界”（优先使用 next 的最早 slice 日）
        next_boundary_by_sid: dict[int, Optional[date]] = {}
        for idx, ps in enumerate(schedules):
            next_boundary: Optional[date] = None
            for j in range(idx + 1, len(schedules)):
                nxt = schedules[j]
                bnd = slice_bounds.get(int(nxt.id), (None, None))[0] or nxt.start_date
                if bnd is not None:
                    next_boundary = bnd
                    break
            next_boundary_by_sid[int(ps.id)] = next_boundary

        rows: list[ScheduleGridRow] = []
        daily_totals: dict[str, int] = defaultdict(int)
        sum_planned_process = 0
        sum_planned_output = 0

        for ps in schedules:
            sid = int(ps.id)
            planned_from_detail: dict[str, int] = dict(detail_planned_rows.get(sid, {}))
            actual_daily_raw: dict[str, int] = dict(detail_actual_rows.get(sid, {}))
            defect_daily_raw: dict[str, int] = dict(detail_defect_rows.get(sid, {}))
            planned_from_slice: dict[str, int] = dict(slice_rows.get(sid, {}))
            slice_dates: set[str] = set(planned_from_slice.keys())

            ps_start_iso = ps.start_date.isoformat() if ps.start_date else None
            ps_end_iso = ps.end_date.isoformat() if ps.end_date else None
            is_completed = (ps.status or '').upper() == 'COMPLETED'

            # actual_daily は daily 決定後に確定する（非完了工単の表示範囲を daily/remaining と揃える）
            actual_daily: dict[str, int] = {}

            daily: dict[str, int] = {}

            if is_completed:
                for dk, dv in planned_from_detail.items():
                    daily[dk] = dv
            else:
                min_slice_day, _max_slice_day = slice_bounds.get(sid, (None, None))
                next_boundary = next_boundary_by_sid.get(sid)
                for dk in set(planned_from_detail.keys()) | slice_dates:
                    if dk in slice_dates:
                        daily[dk] = planned_from_slice.get(dk, 0)
                        continue

                    if min_slice_day is not None:
                        if dk < min_slice_day.isoformat() and dk not in line_slice_dates:
                            daily[dk] = planned_from_detail.get(dk, 0)
                        continue

                    if next_boundary is not None and dk >= next_boundary.isoformat():
                        continue
                    if dk in line_slice_dates:
                        continue
                    if ps_start_iso is not None and dk < ps_start_iso:
                        continue
                    if ps_end_iso is not None and dk > ps_end_iso:
                        continue
                    daily[dk] = planned_from_detail.get(dk, 0)

            # 今天及以前的日计划保持 schedule_details 原值，不随切片重排改写。
            for dk, dv in planned_from_detail.items():
                try:
                    d0 = date.fromisoformat(dk)
                except ValueError:
                    continue
                if d0 <= today_jst:
                    daily[dk] = int(dv or 0)

            upstream_total = int(upstream_defect_total_rows.get(sid, 0) or 0)
            forced_start_iso = (
                ps.forced_start_date.isoformat()
                if getattr(ps, "forced_start_date", None)
                else None
            )
            min_slice_day, _max_slice_day = slice_bounds.get(sid, (None, None))
            min_slice_iso = min_slice_day.isoformat() if min_slice_day else None
            upstream_defect_daily = _build_upstream_defect_daily(
                upstream_total,
                daily,
                start_iso=ps_start_iso,
                end_iso=ps_end_iso,
                forced_start_iso=forced_start_iso,
                min_slice_iso=min_slice_iso,
            )

            # ガント日別「計」は排産エンジンが置いた gross 本数（スライス/明細の合計）。
            # 前工程不良は「前」行と残＝計−実−不−前 で示し、計から再控除しない（二重控除防止）。

            for k, v in daily.items():
                daily_totals[k] += int(v or 0)

            # actual_daily:
            # - COMPLETED は履歴保持のため全量表示
            # - それ以外は当該行で有効表示される日（daily または remaining）に限定
            #   → actual_qty を保ちつつ、他工単への“にじみ”を防ぐ
            if is_completed:
                actual_daily = dict(actual_daily_raw)
            else:
                # 非完了工単の実績は明細実績を全量表示する。
                # 日付フィルタは「実績が見えない」不具合を招きやすいため適用しない。
                # なお、他工単への実績にじみは _sync_actual_from_stock_logs 側の前順位控除で抑制する。
                actual_daily = dict(actual_daily_raw)

            defect_daily = dict(defect_daily_raw)
            defect_qty_sum = int(sum(int(v or 0) for v in defect_daily_raw.values()))

            # 残＝当日セルに表示する計画 − 良品実績 − 不良 − 前工程不良（日別按分）
            remaining_daily: dict[str, int] = {}
            for k in set(daily.keys()) | set(actual_daily.keys()) | set(defect_daily.keys()) | set(upstream_defect_daily.keys()):
                if (
                    int(daily.get(k, 0) or 0) == 0
                    and int(actual_daily.get(k, 0) or 0) == 0
                    and int(defect_daily.get(k, 0) or 0) == 0
                    and int(upstream_defect_daily.get(k, 0) or 0) == 0
                ):
                    continue
                remaining_daily[k] = (
                    int(daily.get(k, 0) or 0)
                    - int(actual_daily.get(k, 0) or 0)
                    - int(defect_daily.get(k, 0) or 0)
                    - int(upstream_defect_daily.get(k, 0) or 0)
                )

            batches_here = batch_by_sid.get(sid, [])
            has_aps_batch_plans = len(batches_here) > 0
            daily_upstream_tint: dict[str, DailyUpstreamTintSeg] = {}
            if has_aps_batch_plans:
                daily_upstream_tint = _daily_upstream_tint_map_for_schedule(
                    daily,
                    dates_list,
                    sid,
                    batches_here,
                    slices_by_sched.get(sid, []),
                    lot_upstream_state,
                )

            rows.append(ScheduleGridRow(
                id=ps.id,
                order_no=ps.order_no,
                item_name=ps.item_name,
                material_shortage=bool(ps.material_shortage),
                lot_qty=int(ps.lot_qty or 0),
                planned_batch_count=int(getattr(ps, "planned_batch_count", 0) or 0),
                lot_size_snapshot=int(getattr(ps, "lot_size_snapshot", 0) or 0),
                planned_process_qty=int(ps.planned_process_qty),
                prev_month_carryover=int(ps.prev_month_carryover or 0),
                due_date=ps.due_date.isoformat() if ps.due_date else None,
                material_date=ps.material_date.isoformat() if ps.material_date else None,
                setup_time=int(ps.setup_time or 0),
                efficiency=_dec(ps.efficiency),
                efficiency_rate=_resolve_efficiency_rate_pieces_per_hour(ps, ee_rows),
                daily_capacity=int(ps.daily_capacity),
                planned_output_qty=int(ps.planned_output_qty or 0),
                start_date=ps.start_date.isoformat() if ps.start_date else None,
                end_date=ps.end_date.isoformat() if ps.end_date else None,
                completion_rate=_dec(ps.completion_rate) if ps.completion_rate is not None else None,
                status=ps.status or "PLANNING",
                daily=daily,
                actual_daily=actual_daily,
                defect_daily=defect_daily,
                upstream_defect_daily=upstream_defect_daily,
                remaining_daily=remaining_daily,
                defect_qty_sum=defect_qty_sum,
                upstream_defect_qty_total=int(upstream_defect_total_rows.get(sid, 0) or 0),
                has_aps_batch_plans=has_aps_batch_plans,
                daily_upstream_tint=daily_upstream_tint,
            ))
            sum_planned_process += int(ps.planned_process_qty or 0)
            sum_planned_output += int(ps.planned_output_qty or 0)

        block_rate = None
        if sum_planned_process > 0:
            block_rate = round(sum_planned_output / sum_planned_process * 100, 2)

        blocks.append(LineGridBlock(
            line_id=line.id,
            line_code=line.machine_cd,
            default_work_hours=_dec(line.default_work_hours),
            calendar=calendar_map,
            rows=rows,
            daily_totals=dict(daily_totals),
            sum_planned_process_qty=sum_planned_process,
            sum_planned_output_qty=sum_planned_output,
            completion_rate=block_rate,
        ))

    return SchedulingGridResponse(dates=dates_list, blocks=blocks)


def _hourly_slice_key(work_d: date, st, et) -> str:
    return (
        f"{work_d.isoformat()}|{st.strftime('%H:%M:%S')}|{et.strftime('%H:%M:%S')}"
        if hasattr(st, "strftime")
        else f"{work_d.isoformat()}|{st}|{et}"
    )


@router.get("/scheduling/hourly-grid", response_model=SchedulingHourlyGridResponse)
async def get_scheduling_hourly_grid(
    startDate: str = Query(...),
    endDate: str = Query(...),
    lineId: int = Query(..., description="設備ID（machines.id）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    machine = await db.get(Machine, lineId)
    if machine is None:
        raise HTTPException(404, "設備が見つかりません")

    sched_result = await db.execute(
        select(ProductionSchedule)
        .where(ProductionSchedule.line_id == lineId)
        .order_by(
            ProductionSchedule.order_no.is_(None),
            ProductionSchedule.order_no.asc(),
            ProductionSchedule.id,
        )
    )
    schedules = sched_result.scalars().all()
    schedule_ids = [ps.id for ps in schedules]
    ee_rows = await _load_equipment_efficiency_rows_for_machine(db, machine)

    col_keys: set[str] = set()
    per_sched: dict[int, dict[str, int]] = defaultdict(dict)
    if schedule_ids:
        slice_result = await db.execute(
            select(ScheduleSliceAllocation)
            .where(
                ScheduleSliceAllocation.schedule_id.in_(schedule_ids),
                ScheduleSliceAllocation.work_date >= sd,
                ScheduleSliceAllocation.work_date <= ed,
            )
            .order_by(
                ScheduleSliceAllocation.work_date,
                ScheduleSliceAllocation.period_start,
                ScheduleSliceAllocation.sort_order,
                ScheduleSliceAllocation.id,
            )
        )
        for sl in slice_result.scalars().all():
            key = _hourly_slice_key(sl.work_date, sl.period_start, sl.period_end)
            col_keys.add(key)
            bucket = per_sched[sl.schedule_id]
            bucket[key] = bucket.get(key, 0) + int(sl.planned_qty or 0)

    sorted_keys = sorted(col_keys, key=lambda k: tuple(k.split("|")))

    columns: list[HourlyGridColumnOut] = []
    for k in sorted_keys:
        parts = k.split("|", 2)
        wd = parts[0] if len(parts) > 0 else ""
        ps = parts[1] if len(parts) > 1 else ""
        pe = parts[2] if len(parts) > 2 else ""
        columns.append(HourlyGridColumnOut(key=k, work_date=wd, period_start=ps, period_end=pe))

    rows: list[HourlyGridRowOut] = [
        HourlyGridRowOut(
            schedule_id=ps.id,
            order_no=ps.order_no,
            planned_batch_count=int(getattr(ps, "planned_batch_count", 0) or 0),
            lot_size_snapshot=int(getattr(ps, "lot_size_snapshot", 0) or 0),
            planned_process_qty=int(ps.planned_process_qty or 0),
            efficiency_rate=_resolve_efficiency_rate_pieces_per_hour(ps, ee_rows),
            item_name=ps.item_name or "",
            slice_qty=dict(per_sched.get(ps.id, {})),
        )
        for ps in schedules
    ]

    return SchedulingHourlyGridResponse(columns=columns, rows=rows)


# ═══════════════════ APS Batch Plans（lot_number表）═══════════════════
@router.get("/batch-plans", response_model=List[ApsBatchPlanOut])
async def get_aps_batch_plans(
    productionMonth: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    lineId: Optional[int] = Query(None, description="設備ID（machines.id）"),
    productCd: Optional[str] = Query(None, description="製品CD（完全一致）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    conditions = []
    q = select(ApsBatchPlan)

    if productionMonth and productionMonth.strip():
        try:
            y_m = productionMonth.strip().split("-")
            if len(y_m) == 2:
                y = int(y_m[0])
                m = int(y_m[1])
                d0 = date(y, m, 1)
                conditions.append(ApsBatchPlan.production_month == d0)
        except (ValueError, IndexError):
            pass

    if lineId is not None:
        q = q.join(ProductionSchedule, ApsBatchPlan.aps_schedule_id == ProductionSchedule.id)
        conditions.append(ProductionSchedule.line_id == lineId)

    if productCd and productCd.strip():
        conditions.append(ApsBatchPlan.product_cd == productCd.strip())

    if conditions:
        q = q.where(and_(*conditions))

    q = q.order_by(
        ApsBatchPlan.production_month.desc(),
        ApsBatchPlan.production_line.asc(),
        ApsBatchPlan.priority_order.asc(),
        ApsBatchPlan.lot_number.asc(),
    )

    result = await db.execute(q)
    return list(result.scalars().all())


@router.patch("/upstream-aps-batch-plan-links")
async def patch_upstream_aps_batch_plan_links(
    body: UpstreamApsBatchPlanLinksBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    cutting_management / instruction_plans の aps_batch_plan_id を一括設定またはクリア。
    管理コード所在照会で「バッチIDのみ」不一致を解消する用途。
    """
    new_id = body.new_aps_batch_plan_id
    if new_id is not None:
        bp = await db.get(ApsBatchPlan, int(new_id))
        if bp is None:
            raise HTTPException(status_code=404, detail="指定の aps_batch_plan_id は aps_batch_plans に存在しません")

    cutting_updated = 0
    instruction_updated = 0
    touched_cutting_ids: set[int] = set()

    for item in body.items:
        bid = int(item.batch_plan_id)
        cid = int(item.cutting_management_id) if item.cutting_management_id is not None else None

        if cid is not None and cid not in touched_cutting_ids:
            res = await db.execute(
                text(
                    "UPDATE cutting_management SET aps_batch_plan_id = :new_id WHERE id = :cid"
                ),
                {"new_id": new_id, "cid": cid},
            )
            touched_cutting_ids.add(cid)
            cutting_updated += int(res.rowcount or 0)
        elif cid is None:
            res = await db.execute(
                text(
                    "UPDATE cutting_management SET aps_batch_plan_id = :new_id "
                    "WHERE aps_batch_plan_id = :bid"
                ),
                {"new_id": new_id, "bid": bid},
            )
            cutting_updated += int(res.rowcount or 0)

        if body.update_instruction_plans:
            res_ins = await db.execute(
                text(
                    "UPDATE instruction_plans SET aps_batch_plan_id = :new_id "
                    "WHERE aps_batch_plan_id = :bid"
                ),
                {"new_id": new_id, "bid": bid},
            )
            instruction_updated += int(res_ins.rowcount or 0)

    await db.commit()
    action = "クリア" if new_id is None else f"設定（{new_id}）"
    return {
        "success": True,
        "message": (
            f"upstream 紐付けを{action}しました（切断 {cutting_updated} 件・指示 {instruction_updated} 件）"
        ),
        "data": UpstreamApsBatchPlanLinksResult(
            cutting_updated=cutting_updated,
            instruction_updated=instruction_updated,
        ).model_dump(),
    }


@router.post("/reassign-cutting-management-lot")
async def reassign_cutting_management_lot(
    body: ReassignCuttingManagementLotBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    誤って aps_batch_plan_id だけで紐づいた cutting_management を、
    移管先 APS ロットの品番・ロット等に合わせて更新し management_code を再生成（DB トリガー）した上で
    aps_batch_plan_id を正しいロットへ付け替える（C + B）。
    """
    cid = int(body.cutting_management_id)
    target_bid = int(body.target_batch_plan_id)

    cm_res = await db.execute(
        text(
            "SELECT id, management_code, aps_batch_plan_id FROM cutting_management WHERE id = :cid LIMIT 1"
        ),
        {"cid": cid},
    )
    cm_row = cm_res.mappings().first()
    if cm_row is None:
        raise HTTPException(status_code=404, detail="cutting_management が見つかりません")

    bp = await db.get(ApsBatchPlan, target_bid)
    if bp is None:
        raise HTTPException(status_code=404, detail="移管先 aps_batch_plan_id は aps_batch_plans に存在しません")

    new_mc = _instruction_management_code(
        bp.production_month,
        bp.production_line,
        bp.product_cd,
        bp.priority_order,
        bp.production_lot_size,
        bp.lot_number,
    )
    dup_res = await db.execute(
        text(
            "SELECT id FROM cutting_management WHERE management_code = :mc AND id <> :cid LIMIT 1"
        ),
        {"mc": new_mc, "cid": cid},
    )
    dup = dup_res.mappings().first()
    if dup is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"移管先の管理コード「{new_mc}」は既に cutting_management.id={int(dup['id'])} が使用中です"
            ),
        )

    prev_mc = (str(cm_row.get("management_code") or "").strip() or None)
    prev_bid_raw = cm_row.get("aps_batch_plan_id")
    prev_bid = int(prev_bid_raw) if prev_bid_raw is not None else None

    await db.execute(
        text(
            """
            UPDATE cutting_management SET
              production_month = :production_month,
              production_line = :production_line,
              product_cd = :product_cd,
              product_name = :product_name,
              priority_order = :priority_order,
              production_lot_size = :production_lot_size,
              lot_number = :lot_number,
              aps_batch_plan_id = :target_bid
            WHERE id = :cid
            """
        ),
        {
            "cid": cid,
            "target_bid": target_bid,
            "production_month": bp.production_month,
            "production_line": bp.production_line,
            "product_cd": bp.product_cd,
            "product_name": bp.product_name,
            "priority_order": bp.priority_order,
            "production_lot_size": int(bp.production_lot_size or 0),
            "lot_number": str(bp.lot_number or ""),
        },
    )

    instruction_updated = 0
    if body.update_instruction_plans:
        res_ins = await db.execute(
            text(
                "UPDATE instruction_plans SET aps_batch_plan_id = :target_bid "
                "WHERE management_code = :mc"
            ),
            {"target_bid": target_bid, "mc": new_mc},
        )
        instruction_updated = int(res_ins.rowcount or 0)

    await db.commit()
    result = ReassignCuttingManagementLotResult(
        cutting_management_id=cid,
        previous_batch_plan_id=prev_bid,
        target_batch_plan_id=target_bid,
        previous_management_code=prev_mc,
        new_management_code=new_mc,
        instruction_updated=instruction_updated,
    )
    return {
        "success": True,
        "message": (
            f"cutting_management.id={cid} をロット {target_bid} へ移管しました"
            f"（管理コード: {prev_mc or '—'} → {new_mc}）"
        ),
        "data": result.model_dump(),
    }


# ═══════════════════ Run All / Sequential ═══════════════════

@router.post("/production-plan-excel/rebuild")
async def rebuild_production_plan_excel(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    production_plan_excel を schedule_details から全量再構築し、
    順番（1/2）を全表再計算する。
    """
    try:
        await db.execute(text("CALL sp_rebuild_production_plan_excel_all()"))
        await db.execute(text("CALL sp_recalc_junban_full()"))
        rows_result = await db.execute(
            text(
                """
                SELECT
                  `検索`, `日付`, `加工機`, `製品CD`, `製品名`, `加工計画`, `生産順番`, `順番`
                FROM `production_plan_excel`
                ORDER BY `日付`, `加工機`, CAST(`生産順番` AS UNSIGNED), `id`
                """
            )
        )
        rows = [dict(r) for r in rows_result.mappings().all()]
        await db.commit()
        synced = await asyncio.to_thread(
            sync_production_plan_excel_to_access,
            rows,
            settings.ACCESS_PRODUCTION_PLAN_DB_PATH,
            settings.ACCESS_PRODUCTION_PLAN_TABLE,
        )
        return {
            "success": True,
            "message": "OK",
            "data": {
                "mysql_rows": len(rows),
                "access_rows": synced,
                "access_path": settings.ACCESS_PRODUCTION_PLAN_DB_PATH,
                "access_table": settings.ACCESS_PRODUCTION_PLAN_TABLE,
            },
        }
    except (OperationalError, ProgrammingError) as e:
        await db.rollback()
        raise HTTPException(500, f"production_plan_excel 再構築に失敗しました: {e}") from e
    except RuntimeError as e:
        raise HTTPException(500, f"Access 同期に失敗しました: {e}") from e
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(500, "production_plan_excel 再構築に失敗しました") from e
    except Exception as e:
        raise HTTPException(500, f"Access 同期に失敗しました: {e}") from e


@router.post("/lines/{line_id}/replan-sequence")
async def replan_sequence(
    line_id: int,
    anchorStartDate: Optional[str] = Query(None),
    includeDebug: bool = Query(False, description="true の場合、工単ごとの再排産デバッグ情報を返す"),
    syncInstructionPlans: bool = Query(
        True,
        description="false のとき instruction_plans を更新・INSERT せず、スケジュール・aps_batch_plans のみ（溶接計画作成等）",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    ライン順で再計算（実績考慮を統合）。

    - 当該ラインに実績/不良が無い: anchor から通常順次排産のみ（旧 Step1）+ 在庫同期。
    - 実績/不良あり: Step1 を省略し、在庫同期後に残数考慮の単一遍次排産（旧 Step3）のみ。

    溶接は当工程実績のみを活動とみなす。成型は当工程不良も活動扱い。
    同期後: aps_batch_plans はロットごとに upstream_defect を反映した有効本数へ更新。

    アンカー日の優先順位: aps_line_replan_anchors > クエリ anchorStartDate > engine 既定。
    """
    anchor = None
    ar_row = await db.get(ApsLineReplanAnchor, line_id)
    if ar_row is not None:
        anchor = ar_row.anchor_date
    elif anchorStartDate:
        try:
            anchor = date.fromisoformat(anchorStartDate)
        except ValueError:
            raise HTTPException(400, "anchorStartDate は YYYY-MM-DD 形式")

    # 计划变更时，先清理该线体“今天之后”的旧排产数据，避免旧数据残留混入新排产。
    # 为避免 anchor 位于未来时产生 [today+1, anchor-1] 的空窗，执行重排起点会钳制到 today+1。
    today = now_jst().date()
    clear_from = today + timedelta(days=1)
    replan_start_anchor = anchor
    if replan_start_anchor is not None and replan_start_anchor > clear_from:
        replan_start_anchor = clear_from
    line_sched_res = await db.execute(
        select(ProductionSchedule.id).where(
            ProductionSchedule.line_id == line_id,
            ProductionSchedule.status.in_(["PLANNING", "IN_PROGRESS"]),
        )
    )
    line_schedule_ids = [int(r[0]) for r in line_sched_res.all()]
    frozen_planned_snapshot: dict[tuple[int, date], int] = {}
    frozen_slice_snapshot: dict[tuple[int, date], list[dict[str, Any]]] = {}
    if line_schedule_ids:
        frozen_detail_res = await db.execute(
            select(ScheduleDetail).where(
                ScheduleDetail.schedule_id.in_(line_schedule_ids),
                or_(
                    ScheduleDetail.schedule_date < today,
                    and_(
                        ScheduleDetail.schedule_date == today,
                        func.coalesce(ScheduleDetail.actual_qty, 0) > 0,
                    ),
                ),
            )
        )
        frozen_keys: list[tuple[int, date]] = []
        for d in frozen_detail_res.scalars().all():
            sid = int(d.schedule_id)
            dte = d.schedule_date
            key = (sid, dte)
            frozen_keys.append(key)
            frozen_planned_snapshot[key] = int(d.planned_qty or 0)

        frozen_slice_res = await db.execute(
            select(ScheduleSliceAllocation).where(
                ScheduleSliceAllocation.schedule_id.in_(line_schedule_ids),
                ScheduleSliceAllocation.work_date <= today,
            )
        )
        frozen_key_set = set(frozen_keys)
        for s in frozen_slice_res.scalars().all():
            sid = int(s.schedule_id)
            dte = s.work_date
            key = (sid, dte)
            if key not in frozen_key_set:
                continue
            frozen_slice_snapshot.setdefault(key, []).append(
                {
                    "period_start": s.period_start,
                    "period_end": s.period_end,
                    "planned_qty": int(s.planned_qty or 0),
                    "sort_order": int(s.sort_order or 0),
                }
            )

    if line_schedule_ids:
        await db.execute(
            delete(ScheduleDetail).where(
                ScheduleDetail.schedule_id.in_(line_schedule_ids),
                ScheduleDetail.schedule_date >= clear_from,
            )
        )
        await db.execute(
            delete(ScheduleSliceAllocation).where(
                ScheduleSliceAllocation.schedule_id.in_(line_schedule_ids),
                ScheduleSliceAllocation.work_date >= clear_from,
            )
        )
        await db.flush()

    # 事前取得：Machine（全ステップで共有）
    line_machine = await db.get(Machine, line_id)

    # 共有日历/时间帯を一括先読み
    cal_start = replan_start_anchor or today
    cal_end_d = cal_start + timedelta(days=APS_CALENDAR_PRELOAD_DAYS)
    cal_result = await db.execute(
        select(LineCapacity)
        .where(
            LineCapacity.line_id == line_id,
            LineCapacity.work_date >= cal_start,
            LineCapacity.work_date <= cal_end_d,
        )
        .order_by(LineCapacity.work_date)
    )
    shared_cal_map: dict[date, float] = {
        row.work_date: float(row.available_hours) for row in cal_result.scalars().all()
    }
    shared_slots = await _fetch_slots_by_date(db, line_id, cal_start, cal_end_d)

    ee_rows: List[EquipmentEfficiency] = []
    if line_machine is not None:
        ee_rows = await _load_equipment_efficiency_rows_for_machine(db, line_machine)
    all_line_sched_res = await db.execute(
        select(ProductionSchedule).where(
            ProductionSchedule.line_id == line_id,
            ProductionSchedule.status.in_(["PLANNING", "IN_PROGRESS", "COMPLETED"]),
        )
    )
    all_line_schedules = sorted(
        all_line_sched_res.scalars().all(),
        key=lambda ps: (ps.order_no is None, ps.order_no or 0, ps.id),
    )
    if ee_rows and all_line_schedules:
        _sync_schedules_daily_capacity_from_ee(all_line_schedules, ee_rows)
        await db.flush()

    replannable_on_line = [
        ps for ps in all_line_schedules if (ps.status or "").upper() in ("PLANNING", "IN_PROGRESS")
    ]
    await _purge_pre_forced_start_schedule_rows(db, replannable_on_line)

    # 在庫同期（活動判定前）：stock_transaction_logs → schedule_details
    for ps in replannable_on_line:
        await _sync_actual_from_stock_logs(db, ps, machine=line_machine)
    await db.flush()
    await _purge_pre_forced_start_schedule_rows(db, replannable_on_line)

    sched_ids = [ps.id for ps in replannable_on_line]
    agg_map, upstream_defect_by_schedule = await _fetch_line_replan_activity_maps(db, sched_ids)
    is_welding_line = (
        await _machine_matches_process_cd(db, line_machine, _APS_WELDING_PROCESS_CD)
        if line_machine
        else False
    )
    has_any_activity = any(
        _schedule_has_replan_activity(v, is_welding_line=is_welding_line) for v in agg_map.values()
    )
    replan_debug_rows: list[dict[str, Any]] = []
    skipped_step1 = False

    if has_any_activity:
        skipped_step1 = True
        updated, replan_debug_rows = await _replan_line_sequential_residual_aware(
            db,
            all_line_schedules=all_line_schedules,
            replan_start_anchor=replan_start_anchor,
            agg_map=agg_map,
            upstream_defect_by_schedule=upstream_defect_by_schedule,
            is_welding_line=is_welding_line,
            line_machine=line_machine,
            shared_cal_map=shared_cal_map,
            shared_slots=shared_slots,
            ee_rows=ee_rows,
            include_debug=includeDebug,
        )
        await db.flush()
    else:
        updated = await replan_line_sequential(
            db,
            line_id,
            replan_start_anchor,
            machine_obj=line_machine,
            cal_map_preloaded=shared_cal_map,
            slots_by_date_preloaded=shared_slots,
            ee_rows_preloaded=ee_rows,
        )
        await db.flush()

    for ps in updated:
        await _sync_actual_from_stock_logs(db, ps, machine=line_machine)
    await db.flush()
    await _purge_pre_forced_start_schedule_rows(db, updated)

    # 最終：開始日指定前の孤立日別行を除去（当日分の再同期後も）
    if updated:
        await _purge_pre_forced_start_schedule_rows(db, updated)

    # instruction_plans 同期（事前に共通データを一括取得）
    # syncInstructionPlans=false のときは成型設備でも instruction_plans に触れない（排産・aps_batch_plans のみ）
    if syncInstructionPlans:
        is_forming_line = await _machine_matches_process_cd(
            db, line_machine, _APS_INSTRUCTION_PLANS_SYNC_PROCESS_CD
        ) if line_machine else False
    else:
        is_forming_line = False

    product_cds = list({(ps.product_cd or "").strip() for ps in updated if ps.product_cd})
    product_cache: dict[str, Optional[Product]] = {}
    if product_cds:
        prod_res = await db.execute(select(Product).where(Product.product_cd.in_(product_cds)))
        for p in prod_res.scalars().all():
            product_cache[(p.product_cd or "").strip()] = p

    material_cache: dict[str, Optional[Material]] = {}
    mat_cds = list({(p.material_cd or "").strip() for p in product_cache.values() if p and p.material_cd})
    if mat_cds:
        mat_res = await db.execute(select(Material).where(Material.material_cd.in_(mat_cds)))
        for m in mat_res.scalars().all():
            material_cache[(m.material_cd or "").strip()] = m

    supplier_cache: dict[str, Optional[Supplier]] = {}
    sup_cds = list({(m.supplier_cd or "").strip() for m in material_cache.values() if m and m.supplier_cd})
    if sup_cds:
        sup_res = await db.execute(select(Supplier).where(Supplier.supplier_cd.in_(sup_cds)))
        for s in sup_res.scalars().all():
            supplier_cache[(s.supplier_cd or "").strip()] = s

    chamfer_sw_cache: dict[str, tuple[int, int]] = {}
    for pc in product_cds:
        chamfer_sw_cache[pc] = await _instruction_plans_chamfer_sw_flags(
            db, pc, product_cache.get(pc)
        )

    for ps in updated:
        await _sync_instruction_plans_from_aps_schedule(
            db, ps,
            machine=line_machine,
            is_forming_line=is_forming_line,
            product_cache=product_cache,
            material_cache=material_cache,
            supplier_cache=supplier_cache,
            chamfer_sw_cache=chamfer_sw_cache,
        )
    await db.flush()

    # 恢复冻结范围内计划（date < today）：仅恢复 planned_qty 与对应时段分配；
    # actual/defect 维持重排后最新同步值，remaining 随之重算。
    if line_schedule_ids:
        # autoflush=False のため SELECT が同セッション未 flush の明細を見落とし、
        # 既存行があるのに INSERT して uk_schedule_date に抵触することがある。
        # MySQL の upsert で冪等に上書きする。
        for (sid, work_date), frozen_planned in frozen_planned_snapshot.items():
            fp = int(frozen_planned)
            ins = mysql_insert(ScheduleDetail.__table__).values(
                schedule_id=int(sid),
                schedule_date=work_date,
                planned_qty=fp,
                actual_qty=0,
                defect_qty=0,
                remaining_qty=fp,
            )
            await db.execute(
                ins.on_duplicate_key_update(
                    planned_qty=ins.inserted.planned_qty,
                )
            )

        # 冻结范围内的时段分配按快照恢复（未快照的工单/日期保持当前结果）
        if frozen_slice_snapshot:
            for sid, work_date in frozen_slice_snapshot.keys():
                await db.execute(
                    delete(ScheduleSliceAllocation).where(
                        ScheduleSliceAllocation.schedule_id == int(sid),
                        ScheduleSliceAllocation.work_date == work_date,
                    )
                )
            for (sid, work_date), rows in frozen_slice_snapshot.items():
                for r in rows:
                    db.add(
                        ScheduleSliceAllocation(
                            schedule_id=int(sid),
                            work_date=work_date,
                            period_start=r["period_start"],
                            period_end=r["period_end"],
                            planned_qty=int(r["planned_qty"]),
                            sort_order=int(r["sort_order"]),
                        )
                    )
        await db.flush()

    anchor_debug_payload = {
        "line_id": int(line_id),
        "requested_anchor": anchorStartDate or None,
        "db_anchor": ar_row.anchor_date.isoformat() if (ar_row and ar_row.anchor_date) else None,
        "effective_anchor": replan_start_anchor.isoformat() if replan_start_anchor else None,
        "clear_from": clear_from.isoformat(),
        "anchor_clamped_to_clear_from": bool(
            anchor is not None and replan_start_anchor is not None and replan_start_anchor != anchor
        ),
    }
    logger.info(
        "[重排锚点] 线体=%s，请求锚点=%s，DB锚点=%s，实际执行锚点=%s，清理起点=%s，是否发生锚点钳制=%s，"
        "实绩路径=%s，跳过Step1=%s，件数=%s",
        anchor_debug_payload["line_id"],
        anchor_debug_payload["requested_anchor"],
        anchor_debug_payload["db_anchor"],
        anchor_debug_payload["effective_anchor"],
        anchor_debug_payload["clear_from"],
        "是" if anchor_debug_payload["anchor_clamped_to_clear_from"] else "否",
        "是" if has_any_activity else "否",
        "是" if skipped_step1 else "否",
        len(updated),
    )

    data: dict[str, Any] = {
        "count": len(updated),
        "residual_aware_path": bool(has_any_activity),
        "skipped_step1": skipped_step1,
    }
    if includeDebug:
        data["replan_anchor_debug"] = {
            "requested_anchor": anchor_debug_payload["requested_anchor"],
            "db_anchor": anchor_debug_payload["db_anchor"],
            "effective_anchor": anchor_debug_payload["effective_anchor"],
            "clear_from": anchor_debug_payload["clear_from"],
            "anchor_clamped_to_clear_from": anchor_debug_payload["anchor_clamped_to_clear_from"],
        }
        data["replan_debug"] = replan_debug_rows

    msg_suffix = "（実績考慮・単遍）" if has_any_activity else ""
    return {
        "success": True,
        "data": data,
        "message": f"{len(updated)}件の工単を再計算しました{msg_suffix}",
    }


@router.post("/run-all")
async def run_all_schedules(
    lineId: Optional[int] = Query(None),
    sequential: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    if sequential and lineId is not None:
        updated = await replan_line_sequential(db, lineId)
        return {"success": True, "data": {"count": len(updated)}, "message": f"{len(updated)}件の工単を順次再計算しました"}

    q = select(ProductionSchedule).where(
        ProductionSchedule.status.in_(["PLANNING", "IN_PROGRESS"])
    )
    if lineId is not None:
        q = q.where(ProductionSchedule.line_id == lineId)
    result = await db.execute(q)
    schedules = result.scalars().all()
    count = 0
    for ps in schedules:
        await run_engine(
            db,
            ps.id,
            override_start_date=ps.start_date,
            use_setup_time=int(ps.order_no or 0) != 1,
        )
        count += 1
    await db.flush()
    return {"success": True, "data": {"count": count}, "message": f"{count}件の工単を再計算しました"}


# ═══════════════════ Daily Equipment Report ═══════════════════

@router.get("/daily-equipment-report")
async def get_daily_equipment_report(
    startDate: str = Query(...),
    endDate: str = Query(...),
    lineId: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        sd = date.fromisoformat(startDate)
        ed = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(400, "日付は YYYY-MM-DD 形式で指定してください")

    sql = text("""
        SELECT
            sd.schedule_date,
            m.id AS line_id,
            m.machine_cd AS line_code,
            m.machine_name AS line_name,
            ps.order_no,
            ps.item_name,
            ps.product_cd,
            sd.planned_qty,
            sd.actual_qty,
            lc.available_hours
        FROM schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN line_capacities lc ON lc.line_id = m.id AND lc.work_date = sd.schedule_date
        WHERE sd.schedule_date >= :sd AND sd.schedule_date <= :ed
          AND (:line_id IS NULL OR m.id = :line_id)
        ORDER BY sd.schedule_date, m.machine_cd, ps.order_no, ps.id
    """)
    result = await db.execute(sql, {"sd": sd, "ed": ed, "line_id": lineId})
    rows = result.mappings().all()

    report: list[dict] = []
    for r in rows:
        report.append({
            "schedule_date": r["schedule_date"].isoformat() if r["schedule_date"] else None,
            "line_id": r["line_id"],
            "line_code": r["line_code"],
            "line_name": r["line_name"],
            "order_no": r["order_no"],
            "item_name": r["item_name"],
            "product_cd": r["product_cd"],
            "planned_qty": int(r["planned_qty"] or 0),
            "actual_qty": int(r["actual_qty"] or 0),
            "available_hours": float(r["available_hours"]) if r["available_hours"] else None,
        })

    return {"success": True, "data": report}


# ═══════════════════ Production Progress（生産進捗） ═══════════════════


def _batch_display_planned_qty(batch: ApsBatchPlan) -> int:
    """計画一覧で確定したロット本数。original_planned_quantity があれば優先（成型再排産で planned_quantity が変わっても不変）。"""
    oq = getattr(batch, "original_planned_quantity", None)
    if oq is not None and int(oq) > 0:
        return int(oq)
    return int(batch.planned_quantity or 0)


def _batch_forming_progress_cap(batch: ApsBatchPlan) -> int:
    """ロット別生産進捗の上限用：計画表示本数から前工程不良（upstream_defect_qty）を差し引いた成型側有効本数（下限0）。"""
    base = _batch_display_planned_qty(batch)
    u = int(getattr(batch, "upstream_defect_qty", 0) or 0)
    return max(0, base - u)


def _split_actual_across_lots(actual_total: int, shares: dict[str, int]) -> dict[str, int]:
    """
    工単日次 actual_qty をロット間で按分（スライス計画日別比率）。最大剰余法で合計を一致。
    shares に正の値が無い場合は先頭ロットに全量を寄せる。
    """
    if actual_total <= 0:
        return {k: 0 for k in shares}
    keys = list(shares.keys())
    if not keys:
        return {}
    out = {k: 0 for k in keys}
    positive = [(k, shares[k]) for k in sorted(keys) if shares[k] > 0]
    if not positive:
        out[sorted(keys)[0]] = actual_total
        return out
    total_share = sum(v for _, v in positive)
    allocated = 0
    fractions: list[tuple[float, str]] = []
    for k, v in positive:
        exact = actual_total * v / total_share
        q = int(math.floor(exact))
        out[k] = q
        allocated += q
        fractions.append((exact - q, k))
    diff = actual_total - allocated
    fractions.sort(key=lambda x: -x[0])
    for i in range(diff):
        out[fractions[i % len(fractions)][1]] += 1
    return out


def _lot_displayed_consumed_before(
    lot_daily: dict[str, dict[str, int]],
    lk: str,
    before_d: str,
) -> int:
    dm = lot_daily.get(lk) or {}
    return sum(int(dm[d]) for d in sorted(dm.keys()) if d < before_d)


def _allocate_day_total_across_lots(
    lot_keys: List[str],
    target: int,
    weights: dict[str, int],
    rooms: dict[str, int],
) -> dict[str, int]:
    """
    target を weights 比でロットに配分。各ロットは rooms[lk] を上限。端数は最大剰余で target まで埋める。
    """
    out = {lk: 0 for lk in lot_keys}
    if target <= 0 or not lot_keys:
        return out
    W = sum(max(0, int(weights.get(lk, 0) or 0)) for lk in lot_keys)
    rem = target
    fr: list[tuple[float, str]] = []
    if W <= 0:
        idx = 0
        while rem > 0 and idx < len(lot_keys) * (target + 5):
            progressed = False
            for lk in sorted(lot_keys):
                if rem <= 0:
                    break
                if out[lk] < max(0, int(rooms.get(lk, 0) or 0)):
                    out[lk] += 1
                    rem -= 1
                    progressed = True
            if not progressed:
                break
            idx += 1
        return out
    for lk in lot_keys:
        w = max(0, int(weights.get(lk, 0) or 0))
        x = target * w / W if W > 0 else 0.0
        q = int(math.floor(x))
        q = min(q, max(0, int(rooms.get(lk, 0) or 0)))
        out[lk] = q
        fr.append((x - q, lk))
        rem -= q
    fr.sort(key=lambda z: -z[0])
    guard = 0
    while rem > 0 and guard < 100000:
        progressed = False
        for _, lk in fr:
            if rem <= 0:
                break
            cap_r = max(0, int(rooms.get(lk, 0) or 0))
            if out[lk] < cap_r:
                out[lk] += 1
                rem -= 1
                progressed = True
        if not progressed:
            break
        guard += 1
    return out


def _align_progress_planned_to_schedule_day_totals(
    lot_daily: dict[str, dict[str, int]],
    lot_daily_source: dict[str, dict[str, str]],
    planned_by_schedule_date: dict[int, dict[str, int]],
    actual_by_schedule_date: dict[int, dict[str, int]],
    sched_lot_keys: dict[int, list[str]],
    lot_planned_daily: dict[str, dict[str, int]],
    lot_planned_cap: dict[str, int],
) -> None:
    """
    ガント（日別）の schedule_details.planned_qty 日次合計と、生産進捗の「計画」セル合計を一致させる。
    成型実績のない日は工単日計 P に合わせてロット間で再按分（スライス比率・各ロット残枠を考慮）。
    ロット残枠の合計が P 未満のときは合計は min(P, 残枠合計) に留まる（データ上の上限）。
    """
    for sid, lot_keys in sched_lot_keys.items():
        uniq_keys = list(dict.fromkeys(lot_keys))
        all_dates: set[str] = set()
        for lk in uniq_keys:
            all_dates |= set((lot_daily.get(lk) or {}).keys())
        for d_str in sorted(all_dates):
            if int(actual_by_schedule_date.get(sid, {}).get(d_str, 0) or 0) > 0:
                continue
            P = int(planned_by_schedule_date.get(sid, {}).get(d_str, 0) or 0)
            if P <= 0:
                continue
            participating: List[str] = []
            for lk in uniq_keys:
                src = (lot_daily_source.get(lk) or {}).get(d_str)
                if src == "ACTUAL":
                    continue
                cap = int(lot_planned_cap.get(lk, 0) or 0)
                prev = _lot_displayed_consumed_before(lot_daily, lk, d_str)
                room = max(0, cap - prev)
                has_cell = d_str in (lot_daily.get(lk) or {})
                raw_w = int((lot_planned_daily.get(lk) or {}).get(d_str, 0) or 0)
                if has_cell and src in ("PLANNED", "WAIT_UPSTREAM"):
                    participating.append(lk)
                elif not has_cell and room > 0 and raw_w > 0:
                    participating.append(lk)
            if not participating:
                continue
            Q = sum(int((lot_daily.get(lk) or {}).get(d_str, 0) or 0) for lk in participating)
            if Q == P:
                continue
            rooms = {
                lk: max(
                    0,
                    int(lot_planned_cap.get(lk, 0) or 0) - _lot_displayed_consumed_before(lot_daily, lk, d_str),
                )
                for lk in participating
            }
            weights = {lk: max(0, int((lot_planned_daily.get(lk) or {}).get(d_str, 0) or 0)) for lk in participating}
            cap_sum = sum(rooms[lk] for lk in participating)
            target = min(P, cap_sum)
            if target <= 0:
                for lk in participating:
                    if lk in lot_daily and d_str in lot_daily[lk]:
                        del lot_daily[lk][d_str]
                    if lk in lot_daily_source and d_str in lot_daily_source[lk]:
                        del lot_daily_source[lk][d_str]
                continue
            alloc = _allocate_day_total_across_lots(participating, target, weights, rooms)
            for lk in participating:
                nq = int(alloc.get(lk, 0) or 0)
                src_prev = (lot_daily_source.get(lk) or {}).get(d_str, "PLANNED")
                if nq <= 0:
                    if lk in lot_daily and d_str in lot_daily[lk]:
                        del lot_daily[lk][d_str]
                    if lk in lot_daily_source and d_str in lot_daily_source[lk]:
                        del lot_daily_source[lk][d_str]
                else:
                    if lk not in lot_daily:
                        lot_daily[lk] = {}
                    if lk not in lot_daily_source:
                        lot_daily_source[lk] = {}
                    lot_daily[lk][d_str] = nq
                    lot_daily_source[lk][d_str] = src_prev if src_prev in ("PLANNED", "WAIT_UPSTREAM") else "PLANNED"


def _enforce_lot_progress_row_sum_cap(
    lot_daily: dict[str, dict[str, int]],
    lot_daily_source: dict[str, dict[str, str]],
    lot_planned_cap: dict[str, int],
) -> None:
    """
    各ロット行の日別セル合計が planned_quantity を超えないようにする。
    工単日次との整列（_align）と実績按分の組み合わせで、同一ロットの合計が 1956+1400 のように
    計画数を超えることがあるため、最後に矯正する。
    新しい日から PLANNED/WAIT_UPSTREAM を削り、足りなければ ACTUAL 表示も削る。
    """
    for lk, cap in lot_planned_cap.items():
        if cap <= 0:
            continue
        daily = lot_daily.get(lk)
        if not daily:
            continue
        src_map = lot_daily_source.setdefault(lk, {})
        total = sum(int(v) for v in daily.values())
        if total <= cap:
            continue
        excess = total - cap
        for d_str in sorted(daily.keys(), reverse=True):
            if excess <= 0:
                break
            if src_map.get(d_str, "PLANNED") == "ACTUAL":
                continue
            q = int(daily[d_str])
            if q <= 0:
                continue
            cut = min(q, excess)
            excess -= cut
            nq = q - cut
            if nq <= 0:
                del daily[d_str]
                src_map.pop(d_str, None)
            else:
                daily[d_str] = nq
        for d_str in sorted(daily.keys(), reverse=True):
            if excess <= 0:
                break
            q = int(daily[d_str])
            if q <= 0:
                continue
            cut = min(q, excess)
            excess -= cut
            nq = q - cut
            if nq <= 0:
                del daily[d_str]
                src_map.pop(d_str, None)
            else:
                daily[d_str] = nq


def _sort_lot_keys_in_schedule(uniq_keys: List[str]) -> List[str]:
    """同一工単内の lot_key（{schedule_id}_{lot_number}）をロット番号昇順で並べる。"""

    def sort_key(lk: str) -> tuple:
        try:
            _, lot_rest = lk.split("_", 1)
        except ValueError:
            return (1, lk)
        try:
            return (0, int(str(lot_rest).strip()))
        except ValueError:
            return (1, lot_rest)

    return sorted(uniq_keys, key=sort_key)


def _collect_schedule_progress_dates(
    sid: int,
    ordered_lks: List[str],
    lot_planned_daily: dict[str, dict[str, int]],
    actual_by_schedule_date: dict[int, dict[str, int]],
    planned_by_schedule_date: dict[int, dict[str, int]],
) -> List[str]:
    ds: set[str] = set()
    for lk in ordered_lks:
        ds |= set((lot_planned_daily.get(lk) or {}).keys())
    for dk, aq in (actual_by_schedule_date.get(sid) or {}).items():
        if int(aq or 0) > 0:
            ds.add(dk)
    ds |= set((planned_by_schedule_date.get(sid) or {}).keys())
    return sorted(ds)


def _build_lot_daily_sequential_forming_actuals(
    sid: int,
    uniq_keys: List[str],
    lot_planned_daily: dict[str, dict[str, int]],
    lot_planned_cap: dict[str, int],
    lot_progress_status: dict[str, str],
    actual_by_schedule_date: dict[int, dict[str, int]],
    planned_by_schedule_date: dict[int, dict[str, int]],
    material_flag: bool,
    lot_daily: dict[str, dict[str, int]],
    lot_daily_source: dict[str, dict[str, str]],
) -> None:
    """
    日次成型実績はロット番号順にのみ割当て：先頭ロットの残 cap を尽くしてから次ロットへ（同日も同様）。
    スライス比率での横並び按分はしない。残計画は cap 控除後、最終実績日の翌日以降にスライス形状で配分。
    """
    ordered = _sort_lot_keys_in_schedule(list(dict.fromkeys(uniq_keys)))
    if not ordered:
        return
    sorted_dates = _collect_schedule_progress_dates(
        sid, ordered, lot_planned_daily, actual_by_schedule_date, planned_by_schedule_date
    )
    if not sorted_dates:
        return

    rem_cap = {lk: max(0, int(lot_planned_cap.get(lk, 0) or 0)) for lk in ordered}

    for d_str in sorted_dates:
        a_left = int((actual_by_schedule_date.get(sid) or {}).get(d_str, 0) or 0)
        if a_left <= 0:
            continue
        i = 0
        while a_left > 0:
            while i < len(ordered) and rem_cap.get(ordered[i], 0) <= 0:
                i += 1
            if i >= len(ordered):
                break
            lk = ordered[i]
            room = rem_cap[lk]
            x = min(a_left, room)
            if x <= 0:
                i += 1
                continue
            lot_daily.setdefault(lk, {})
            lot_daily[lk][d_str] = int(lot_daily[lk].get(d_str, 0) or 0) + x
            lot_daily_source.setdefault(lk, {})
            lot_daily_source[lk][d_str] = "ACTUAL"
            rem_cap[lk] -= x
            a_left -= x

    for lk in ordered:
        rem = rem_cap.get(lk, 0)
        if rem <= 0:
            continue
        src_map = lot_daily_source.setdefault(lk, {})
        dm = lot_daily.setdefault(lk, {})
        last_actual: Optional[str] = None
        for d_str in sorted(dm.keys()):
            if int(dm.get(d_str) or 0) > 0 and src_map.get(d_str) == "ACTUAL":
                last_actual = d_str

        eligible = [d for d in sorted_dates if last_actual is None or d > last_actual]
        if not eligible:
            eligible = sorted_dates
        weights = {d: max(0, int((lot_planned_daily.get(lk) or {}).get(d, 0) or 0)) for d in eligible}
        wsum = sum(weights.values())
        if wsum <= 0:
            weights = {d: 1 for d in eligible}
        alloc = _split_actual_across_lots(rem, weights)
        st = lot_progress_status.get(lk, "PLANNED")
        src = "WAIT_UPSTREAM" if (material_flag or st == "PLANNED") else "PLANNED"
        for d_str, q in alloc.items():
            qn = int(q or 0)
            if qn <= 0:
                continue
            if src_map.get(d_str) == "ACTUAL":
                continue
            cur = int(dm.get(d_str, 0) or 0)
            dm[d_str] = cur + qn
            src_map[d_str] = src


def _trim_lot_progress_by_lot_cap(
    lot_daily: dict[str, dict[str, int]],
    lot_daily_source: dict[str, dict[str, str]],
    lot_cap: dict[str, int],
) -> None:
    """
    各ロットの計画数（aps_batch_plans.planned_quantity）を上限に、日付昇順で処理する。
    先に出た実績（ACTUAL）で本数を消化し、残りに対してのみ PLANNED / WAIT_UPSTREAM を表示する。
    例: 計画1956、1日目実績1400 → 2日目のスライス按分が1956でも表示は556に縮む。
    """
    for lk, cap in lot_cap.items():
        if cap <= 0:
            continue
        daily = lot_daily.get(lk)
        if not daily:
            continue
        src_map = lot_daily_source.setdefault(lk, {})
        consumed = 0
        for d_str in sorted(daily.keys()):
            q = int(daily.get(d_str) or 0)
            if q <= 0:
                continue
            src = src_map.get(d_str, "PLANNED")
            if src == "ACTUAL":
                consumed += q
                continue
            room = max(0, cap - consumed)
            new_q = min(q, room)
            if new_q <= 0:
                del daily[d_str]
                src_map.pop(d_str, None)
            else:
                daily[d_str] = new_q
                consumed += new_q


@router.get("/production-progress", response_model=ProductionProgressResponse)
async def get_production_progress(
    lineId: int = Query(..., description="対象設備 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定ラインの APS ロットごとに instruction_plans / cutting_management を照合し、
    リアルタイムの生産進捗ステータス＋日別数量を返す。
    全 aps_batch_plans ロットを返し、本工程（成型）の日別計画・実績を欠かさない。
    cutting_management / instruction_plans はステータス・切断(本)列のみに使用し、行の有無では落とさない。
    cutting_management にあれば生産中、instruction_plans のみなら指示済、未同期は PLANNED。
    日別セルは成型ガント連動（schedule_details の planned/actual）。actual_qty は再計算時に在庫ログから
    当該設備・製品へ同期される成型実績であり、切断完工の代替ではない。切断の本数・完了は cutting_* フィールドで返す。
    True のとき成型実績はロット番号順に日次のみ割当（同日も先頭ロットから順に、横並び按分なし）、残計画はスライス再配置。
    False のときは従来のスライス比率実績按分。
    計画数表示は original_planned_quantity を維持。上流待ちは WAIT_UPSTREAM。
    """
    sched_result = await db.execute(
        select(ProductionSchedule)
        .where(ProductionSchedule.line_id == lineId)
        .order_by(
            ProductionSchedule.order_no.is_(None),
            ProductionSchedule.order_no.asc(),
            ProductionSchedule.id,
        )
    )
    schedules = sched_result.scalars().all()
    if not schedules:
        return ProductionProgressResponse(lots=[], dates=[], lot_daily={}, lot_daily_source={})

    schedule_map = {s.id: s for s in schedules}
    schedule_ids = list(schedule_map.keys())

    batch_result = await db.execute(
        select(ApsBatchPlan)
        .where(ApsBatchPlan.aps_schedule_id.in_(schedule_ids))
        .order_by(ApsBatchPlan.aps_schedule_id, ApsBatchPlan.lot_number)
    )
    batches = batch_result.scalars().all()
    if not batches:
        return ProductionProgressResponse(lots=[], dates=[], lot_daily={}, lot_daily_source={})

    if _PRODUCTION_PROGRESS_USE_FORMING_ACTUAL:
        for ps in schedules:
            await _sync_actual_from_stock_logs(db, ps)
        await db.flush()

    slice_result = await db.execute(
        select(ScheduleSliceAllocation)
        .where(ScheduleSliceAllocation.schedule_id.in_(schedule_ids))
        .order_by(
            ScheduleSliceAllocation.schedule_id,
            ScheduleSliceAllocation.work_date,
            ScheduleSliceAllocation.period_start,
            ScheduleSliceAllocation.sort_order,
        )
    )
    all_slices = slice_result.scalars().all()
    slices_by_sched: dict[int, list] = defaultdict(list)
    for s in all_slices:
        slices_by_sched[s.schedule_id].append(s)

    det_result = await db.execute(
        select(ScheduleDetail).where(ScheduleDetail.schedule_id.in_(schedule_ids))
    )
    actual_by_schedule_date: dict[int, dict[str, int]] = defaultdict(dict)
    planned_by_schedule_date: dict[int, dict[str, int]] = defaultdict(dict)
    for det in det_result.scalars().all():
        dkey = det.schedule_date.isoformat()
        sid = det.schedule_id
        planned_by_schedule_date[sid][dkey] = planned_by_schedule_date[sid].get(dkey, 0) + int(det.planned_qty or 0)
        if _PRODUCTION_PROGRESS_USE_FORMING_ACTUAL:
            actual_by_schedule_date[sid][dkey] = actual_by_schedule_date[sid].get(dkey, 0) + int(det.actual_qty or 0)

    lot_planned_daily: dict[str, dict[str, int]] = {}
    lot_progress_status: dict[str, str] = {}
    lot_planned_cap: dict[str, int] = {}
    sched_lot_keys: dict[int, list[str]] = defaultdict(list)
    lots: list[ProgressLotItem] = []

    sched_lot_size_ctx: dict[int, dict[str, int]] = {}
    for ps in schedules:
        sched_lot_size_ctx[ps.id] = _schedule_lot_size_code_context(
            ps, slices_by_sched.get(ps.id, [])
        )

    for batch in batches:
        ps = schedule_map.get(batch.aps_schedule_id)
        if not ps:
            continue

        ls_ctx = sched_lot_size_ctx.get(ps.id, {})
        pls_forming_row = int(batch.production_lot_size or 0)
        pls_instruction = int(ls_ctx.get("production_lot_size_instruction") or 0)

        # 進捗照会は計画一覧の順位（ps.order_no）で管理コードを組み立てる。
        # batch.priority_order が古い値のままだと、他順位の切断行と誤って紐づくため。
        po_progress = ps.order_no if ps.order_no is not None else batch.priority_order
        mc = _instruction_management_code(
            production_month=batch.production_month,
            production_line=batch.production_line,
            product_cd=batch.product_cd,
            priority_order=po_progress,
            production_lot_size=batch.production_lot_size,
            lot_number=batch.lot_number,
        )
        mc_instruction = _instruction_management_code(
            production_month=batch.production_month,
            production_line=batch.production_line,
            product_cd=batch.product_cd,
            priority_order=po_progress,
            production_lot_size=pls_instruction if pls_instruction > 0 else batch.production_lot_size,
            lot_number=batch.lot_number,
        )
        mc_norm = (mc or "").strip()
        mc_instr_norm = (mc_instruction or "").strip()
        lot_size_code_dual_source = (pls_instruction > 0 and pls_forming_row != pls_instruction) or (
            mc_instr_norm != mc_norm
        )
        progress_status = "PLANNED"
        status_determined_by = "PLANNED"
        edit_location_hint = "どちらの表にも未登録 — 成型計画で「ライン順で再計算」で instruction_plans を同期"
        in_cutting_management = False
        in_cutting_by_management_code = False
        in_cutting_by_batch_plan_id = False
        cutting_management_code_in_db: Optional[str] = None
        cutting_management_row_id: Optional[int] = None
        cutting_batch_link_mismatch_id: Optional[int] = None
        cutting_batch_link_mismatch_db_code: Optional[str] = None
        in_instruction_plans = False
        in_instruction_by_management_code = False
        in_instruction_by_batch_plan_id = False
        instruction_management_code_in_db: Optional[str] = None
        cutting_match_field: Optional[str] = None
        instruction_match_field: Optional[str] = None
        upstream_data_table: Optional[str] = None
        cut_planned: Optional[int] = None
        cut_actual: Optional[int] = None
        cut_done: Optional[bool] = None
        in_instruction_plans_by_instruction_code = False
        try:
            cut_res = await db.execute(
                text(
                    "SELECT id, management_code, planned_quantity, actual_production_quantity, "
                    "COALESCE(production_completed_check, 0) AS pcc "
                    "FROM cutting_management "
                    "WHERE management_code = :mc "
                    "  AND COALESCE(priority_order, 0) = COALESCE(:priority_order, 0) "
                    "LIMIT 1"
                ),
                {"mc": mc_norm, "priority_order": po_progress},
            )
            cut_row = cut_res.mappings().first()
            if cut_row is not None:
                in_cutting_by_management_code = True
                cutting_match_field = "management_code"
                in_cutting_management = True
                cutting_management_row_id = int(cut_row.get("id") or 0) or None
                db_mc = (cut_row.get("management_code") or "")
                cutting_management_code_in_db = str(db_mc).strip() or None
                progress_status = "IN_PROGRESS"
                status_determined_by = "CUTTING_BY_MC"
                upstream_data_table = "cutting_management"
                edit_location_hint = (
                    "cutting_management（管理コード一致）— 切断済リストで当該コードを検索"
                )
                cut_planned = int(cut_row.get("planned_quantity") or 0)
                cut_actual = int(cut_row.get("actual_production_quantity") or 0)
                cut_done = bool(int(cut_row.get("pcc") or 0))
            elif batch.id is not None:
                cut_bid_res = await db.execute(
                    text(
                        f"""
                        SELECT cm.id, cm.management_code, cm.planned_quantity,
                               cm.actual_production_quantity,
                               COALESCE(cm.production_completed_check, 0) AS pcc
                        FROM cutting_management cm
                        {_CUTTING_ABP_FIELD_ALIGN_SQL}
                          AND COALESCE(cm.priority_order, 0) = COALESCE(:schedule_priority, 0)
                        ORDER BY cm.id DESC LIMIT 1
                        """
                    ),
                    {"bid": int(batch.id), "schedule_priority": po_progress},
                )
                cut_bid_row = cut_bid_res.mappings().first()
                if cut_bid_row is not None:
                    bid_db_mc = str(cut_bid_row.get("management_code") or "").strip()
                    if bid_db_mc and bid_db_mc != mc_norm:
                        cutting_batch_link_mismatch_id = int(cut_bid_row.get("id") or 0) or None
                        cutting_batch_link_mismatch_db_code = bid_db_mc
                    elif bid_db_mc == mc_norm:
                        in_cutting_by_batch_plan_id = True
                        cutting_match_field = "aps_batch_plan_id"
                        in_cutting_management = True
                        cutting_management_row_id = int(cut_bid_row.get("id") or 0) or None
                        cutting_management_code_in_db = bid_db_mc or None
                        progress_status = "IN_PROGRESS"
                        status_determined_by = "CUTTING_BY_BID"
                        upstream_data_table = "cutting_management"
                        edit_location_hint = (
                            "cutting_management（aps_batch_plan_id 一致・順位/品番/ロット整合）"
                        )
                        cut_planned = int(cut_bid_row.get("planned_quantity") or 0)
                        cut_actual = int(cut_bid_row.get("actual_production_quantity") or 0)
                        cut_done = bool(int(cut_bid_row.get("pcc") or 0))

            ins_row = None
            ins_res_mc = await db.execute(
                text(
                    "SELECT id, management_code FROM instruction_plans "
                    "WHERE management_code = :mc "
                    "  AND COALESCE(priority_order, 0) = COALESCE(:priority_order, 0) "
                    "ORDER BY id DESC LIMIT 1"
                ),
                {"mc": mc_norm, "priority_order": po_progress},
            )
            ins_row = ins_res_mc.mappings().first()
            if ins_row is not None:
                in_instruction_by_management_code = True
                instruction_match_field = "management_code"
                in_instruction_plans = True
                instruction_management_code_in_db = (
                    str(ins_row.get("management_code") or "").strip() or None
                )
            elif mc_instr_norm and mc_instr_norm != mc_norm:
                ins_res_instr = await db.execute(
                    text(
                        "SELECT id, management_code FROM instruction_plans "
                        "WHERE management_code = :mc "
                        "  AND COALESCE(priority_order, 0) = COALESCE(:priority_order, 0) "
                        "ORDER BY id DESC LIMIT 1"
                    ),
                    {"mc": mc_instr_norm, "priority_order": po_progress},
                )
                ins_instr_row = ins_res_instr.mappings().first()
                if ins_instr_row is not None:
                    in_instruction_plans_by_instruction_code = True
                    in_instruction_plans = True
                    instruction_management_code_in_db = (
                        str(ins_instr_row.get("management_code") or "").strip() or None
                    )
                    instruction_match_field = "management_code_instruction"

            if not in_cutting_management and in_instruction_plans:
                progress_status = "RELEASED"
                status_determined_by = "INSTRUCTION"
                upstream_data_table = "instruction_plans"
                edit_location_hint = (
                    "instruction_plans（管理コード一致）— 製造指示で修正"
                )
            elif in_cutting_management and in_instruction_plans:
                edit_location_hint = (
                    "進捗は cutting_management（管理コード一致）。"
                    "instruction_plans にも行あり（管理コード一致）"
                )
            elif cutting_batch_link_mismatch_id is not None:
                edit_location_hint = (
                    f"aps_batch_plan_id={batch.id} に切断行 id={cutting_batch_link_mismatch_id} が紐づくが、"
                    f"DBコード「{cutting_batch_link_mismatch_db_code or '空'}」≠ 照会「{mc_norm}」。"
                    "進捗・所在には含めない。誤紐付け修正または aps_batch_plan_id クリアを推奨。"
                )
            elif lot_size_code_dual_source:
                edit_location_hint = (
                    f"ロット数口径が二重：成型={pls_forming_row}（スライス残 {ls_ctx.get('slice_total', 0)}）、"
                    f"指示={pls_instruction}（一覧合計 {ls_ctx.get('full_plan_total', 0)}）。"
                    f"照会码={mc_norm}、指示同期码={mc_instr_norm}。"
                    "instruction は指示用コードで検索。"
                )
        except (OperationalError, ProgrammingError):
            pass

        order_label = ps.order_no if ps.order_no is not None else "—"
        position_summary = (
            f"順位 {order_label} · 工単 ID {int(ps.id)} · ロット #{batch.lot_number}"
        )

        start_iso = batch.start_date.isoformat() if batch.start_date else None
        end_iso = batch.end_date.isoformat() if batch.end_date else None

        disp_qty = _batch_display_planned_qty(batch)
        u_def = int(getattr(batch, "upstream_defect_qty", 0) or 0)
        eff_qty = _batch_forming_progress_cap(batch)
        lots.append(ProgressLotItem(
            batch_plan_id=batch.id,
            aps_schedule_id=batch.aps_schedule_id,
            product_cd=batch.product_cd,
            product_name=batch.product_name,
            lot_number=batch.lot_number,
            planned_quantity=disp_qty,
            order_no=ps.order_no,
            start_date=start_iso,
            end_date=end_iso,
            predicted_completion=end_iso,
            progress_status=progress_status,
            management_code=mc,
            production_lot_size_forming=pls_forming_row,
            production_lot_size_instruction=pls_instruction if pls_instruction > 0 else None,
            management_code_instruction=mc_instruction if lot_size_code_dual_source else None,
            lot_size_code_dual_source=lot_size_code_dual_source,
            schedule_slice_total=int(ls_ctx.get("slice_total") or 0) or None,
            schedule_full_plan_total=int(ls_ctx.get("full_plan_total") or 0) or None,
            in_instruction_plans_by_instruction_code=in_instruction_plans_by_instruction_code,
            production_line=batch.production_line or "",
            cutting_planned_qty=cut_planned,
            cutting_actual_qty=cut_actual,
            cutting_completed=cut_done,
            upstream_defect_qty=u_def,
            forming_effective_planned_qty=eff_qty,
            status_determined_by=status_determined_by,
            edit_location_hint=edit_location_hint,
            position_summary=position_summary,
            in_cutting_management=in_cutting_management,
            in_cutting_by_management_code=in_cutting_by_management_code,
            in_cutting_by_batch_plan_id=in_cutting_by_batch_plan_id,
            cutting_management_code_in_db=cutting_management_code_in_db,
            cutting_management_row_id=cutting_management_row_id,
            cutting_batch_link_mismatch_id=cutting_batch_link_mismatch_id,
            cutting_batch_link_mismatch_db_code=cutting_batch_link_mismatch_db_code,
            in_instruction_plans=in_instruction_plans,
            in_instruction_by_management_code=in_instruction_by_management_code,
            in_instruction_by_batch_plan_id=in_instruction_by_batch_plan_id,
            instruction_management_code_in_db=instruction_management_code_in_db,
            cutting_match_field=cutting_match_field,
            instruction_match_field=instruction_match_field,
            upstream_data_table=upstream_data_table,
        ))

        lot_key = f"{batch.aps_schedule_id}_{batch.lot_number}"
        sched_lot_keys[ps.id].append(lot_key)
        lot_progress_status[lot_key] = progress_status
        lot_planned_cap[lot_key] = max(
            lot_planned_cap.get(lot_key, 0),
            eff_qty,
        )
        daily_map: dict[str, int] = {}

        slices = slices_by_sched.get(ps.id, [])
        if slices and batch.start_date and batch.end_date:
            b_start = batch.start_date
            b_end = batch.end_date
            for sl in slices:
                sl_start = _combine_work_date_and_time(sl.work_date, sl.period_start, end_of_day=False)
                is_eod = sl.period_end == time(0, 0, 0) and sl.period_start != time(0, 0, 0)
                sl_end = _combine_work_date_and_time(sl.work_date, sl.period_end, end_of_day=is_eod)
                if sl_end <= b_start or sl_start >= b_end:
                    continue
                sq = int(sl.planned_qty or 0)
                if sq <= 0:
                    continue
                overlap_start = max(sl_start, b_start)
                overlap_end = min(sl_end, b_end)
                sl_dur = max(1.0, (sl_end - sl_start).total_seconds())
                overlap_dur = max(0.0, (overlap_end - overlap_start).total_seconds())
                portion = int(round(sq * overlap_dur / sl_dur))
                if portion <= 0:
                    continue
                d_key = sl.work_date.isoformat()
                daily_map[d_key] = daily_map.get(d_key, 0) + portion

        lot_planned_daily[lot_key] = daily_map

    lot_daily: dict[str, dict[str, int]] = {}
    lot_daily_source: dict[str, dict[str, str]] = {}

    for sid, lot_keys in sched_lot_keys.items():
        ps = schedule_map.get(sid)
        if ps is None or not lot_keys:
            continue
        uniq_keys = list(dict.fromkeys(lot_keys))
        material_flag = bool(ps.material_shortage)
        if _PRODUCTION_PROGRESS_USE_FORMING_ACTUAL:
            _build_lot_daily_sequential_forming_actuals(
                sid,
                uniq_keys,
                lot_planned_daily,
                lot_planned_cap,
                lot_progress_status,
                actual_by_schedule_date,
                planned_by_schedule_date,
                material_flag,
                lot_daily,
                lot_daily_source,
            )
            continue

        date_keys: set[str] = set()
        for lk in uniq_keys:
            date_keys |= set(lot_planned_daily.get(lk, {}).keys())
        for dk, aq in actual_by_schedule_date.get(sid, {}).items():
            if aq > 0:
                date_keys.add(dk)

        for d_str in sorted(date_keys):
            actual_total = int(actual_by_schedule_date.get(sid, {}).get(d_str, 0) or 0)
            shares = {lk: lot_planned_daily.get(lk, {}).get(d_str, 0) for lk in uniq_keys}

            if actual_total > 0:
                split = _split_actual_across_lots(actual_total, shares)
                for lk in uniq_keys:
                    q = int(split.get(lk, 0) or 0)
                    if q <= 0:
                        continue
                    if lk not in lot_daily:
                        lot_daily[lk] = {}
                    if lk not in lot_daily_source:
                        lot_daily_source[lk] = {}
                    lot_daily[lk][d_str] = q
                    lot_daily_source[lk][d_str] = "ACTUAL"
                continue

            for lk in uniq_keys:
                q = int(shares.get(lk, 0) or 0)
                if q <= 0:
                    continue
                st = lot_progress_status.get(lk, "PLANNED")
                src = "WAIT_UPSTREAM" if (material_flag or st == "PLANNED") else "PLANNED"
                if lk not in lot_daily:
                    lot_daily[lk] = {}
                if lk not in lot_daily_source:
                    lot_daily_source[lk] = {}
                lot_daily[lk][d_str] = q
                lot_daily_source[lk][d_str] = src

    _trim_lot_progress_by_lot_cap(lot_daily, lot_daily_source, lot_planned_cap)
    _align_progress_planned_to_schedule_day_totals(
        lot_daily,
        lot_daily_source,
        planned_by_schedule_date,
        actual_by_schedule_date,
        sched_lot_keys,
        lot_planned_daily,
        lot_planned_cap,
    )
    _enforce_lot_progress_row_sum_cap(lot_daily, lot_daily_source, lot_planned_cap)
    all_dates_set: set[str] = set()
    for dm in lot_daily.values():
        all_dates_set |= set(dm.keys())
    dates = sorted(all_dates_set)
    return ProductionProgressResponse(
        lots=lots,
        dates=dates,
        lot_daily=lot_daily,
        lot_daily_source=lot_daily_source,
    )


# ═══════════════════ helpers ═══════════════════


async def _sum_actual_qty(db: AsyncSession, schedule_id: int) -> int:
    """schedule_details の actual_qty 合計（from-now 下限チェック用）。"""
    from sqlalchemy import func as sa_func
    res = await db.execute(
        select(sa_func.coalesce(sa_func.sum(ScheduleDetail.actual_qty), 0))
        .where(ScheduleDetail.schedule_id == schedule_id)
    )
    return int(res.scalar() or 0)


async def _actual_daily_from_schedule_details(
    db: AsyncSession,
    schedule_id: int,
    start_date: date,
    end_date: date,
) -> dict[str, int]:
    """
    schedule_details から実績を日別集計（YYYY-MM-DD -> qty）。
    """
    q = await db.execute(
        select(ScheduleDetail).where(
            ScheduleDetail.schedule_id == schedule_id,
            ScheduleDetail.schedule_date >= start_date,
            ScheduleDetail.schedule_date <= end_date,
        )
    )
    out: dict[str, int] = {}
    for det in q.scalars().all():
        k = det.schedule_date.isoformat()
        out[k] = out.get(k, 0) + int(det.actual_qty or 0)
    return out


async def _sum_actual_qty_until(
    db: AsyncSession,
    schedule_id: int,
    start_date: date,
    end_date: date,
) -> int:
    if end_date < start_date:
        return 0
    res = await db.execute(
        select(ScheduleDetail).where(
            ScheduleDetail.schedule_id == schedule_id,
            ScheduleDetail.schedule_date >= start_date,
            ScheduleDetail.schedule_date <= end_date,
        )
    )
    return sum(int(r.actual_qty or 0) for r in res.scalars().all())


async def _last_actual_date_for_line(db: AsyncSession, line_id: int) -> Optional[date]:
    rows = await db.execute(
        select(ScheduleDetail.schedule_date)
        .join(ProductionSchedule, ProductionSchedule.id == ScheduleDetail.schedule_id)
        .where(
            ProductionSchedule.line_id == line_id,
            ScheduleDetail.actual_qty > 0,
        )
        .order_by(ScheduleDetail.schedule_date.desc())
        .limit(1)
    )
    return rows.scalar_one_or_none()


async def _purge_pre_forced_start_schedule_rows(
    db: AsyncSession,
    schedules: Sequence[ProductionSchedule],
) -> None:
    """開始日指定より前の日別計画・スライスを削除（後順位への計画・実績のにじみ防止）。"""
    for ps in schedules:
        if (ps.status or "").upper() == "COMPLETED":
            continue
        fs = getattr(ps, "forced_start_date", None)
        if fs is None:
            continue
        await db.execute(
            delete(ScheduleDetail).where(
                ScheduleDetail.schedule_id == ps.id,
                ScheduleDetail.schedule_date < fs,
            )
        )
        await db.execute(
            delete(ScheduleSliceAllocation).where(
                ScheduleSliceAllocation.schedule_id == ps.id,
                ScheduleSliceAllocation.work_date < fs,
            )
        )
    await db.flush()


async def _schedule_id_owning_actual_on_date(
    db: AsyncSession,
    line_id: int,
    product_cd_norm: str,
    work_date: date,
) -> Optional[int]:
    """
    同一ライン・同一製品で、当該日の良品実績を配賦すべき工単 ID。
    計画（planned_qty>0）がある行のうち順位が最小のものを優先する。
    開始日指定より前の日付は対象外。
    """
    from sqlalchemy import func as sa_func

    res = await db.execute(
        select(ProductionSchedule.id)
        .join(ScheduleDetail, ScheduleDetail.schedule_id == ProductionSchedule.id)
        .where(
            ProductionSchedule.line_id == line_id,
            sa_func.trim(sa_func.coalesce(ProductionSchedule.product_cd, "")) == product_cd_norm,
            ScheduleDetail.schedule_date == work_date,
            ScheduleDetail.planned_qty > 0,
            or_(
                ProductionSchedule.forced_start_date.is_(None),
                ScheduleDetail.schedule_date >= ProductionSchedule.forced_start_date,
            ),
        )
        .order_by(
            ProductionSchedule.order_no.is_(None),
            ProductionSchedule.order_no.asc(),
            ProductionSchedule.id.asc(),
        )
        .limit(1)
    )
    return res.scalar_one_or_none()


async def _stock_log_defect_process_cd_for_machine(
    db: AsyncSession, machine: Machine
) -> Optional[str]:
    """在庫ログ不良同期に使う process_cd（設備の工程に合わせる。未判定は同期しない）。"""
    if await _machine_matches_process_cd(db, machine, _APS_WELDING_PROCESS_CD):
        return _APS_WELDING_PROCESS_CD
    if await _machine_matches_process_cd(db, machine, _APS_FORMING_PROCESS_CD):
        return _APS_FORMING_PROCESS_CD
    return None


async def _sync_actual_from_stock_logs(
    db: AsyncSession, ps: ProductionSchedule, *, machine: Optional[Machine] = None
):
    """
    stock_transaction_logs を schedule_details に日別同期する。
    - transaction_type='実績' → actual_qty（良品・machine_cd 一致）
    - transaction_type='不良' かつ process_cd=当設備工程（成型 KT04 / 溶接 KT07）→ defect_qty
      マッチ：TRIM(ps.product_cd)=TRIM(target_cd)、DATE(transaction_time)=schedule_date、
      SUM(quantity)。不良は在庫ログに machine_cd が無い場合があるため device 一致は課さない。
    同一ライン・同一製品の前順位工単に配賦済みの良品/不良を控除し、二重計上を防ぐ。
    remaining_qty は 計画 − 良品実績 − 不良 で上書きする。
    """
    from sqlalchemy import func as sa_func

    if machine is None:
        machine = await db.get(Machine, ps.line_id)
    if machine is None:
        return

    details_res = await db.execute(
        select(ScheduleDetail).where(ScheduleDetail.schedule_id == ps.id)
    )
    details = details_res.scalars().all()
    if not details:
        return

    from app.modules.erp.stock_transaction_log_models import StockTransactionLog

    product_cd_norm = (ps.product_cd or "").strip()
    if not product_cd_norm:
        return

    all_dates = [det.schedule_date for det in details]
    min_d = min(all_dates)
    max_d = max(all_dates)
    # 当該工単の明細期間を基準にするが、同一ライン・同一製品の他工単が
    # より早い日付を持つ場合はそちらまで遡る（前順位の実績控除漏れを防ぐ）。
    line_min_res = await db.execute(
        select(func.min(ScheduleDetail.schedule_date))
        .join(ProductionSchedule, ProductionSchedule.id == ScheduleDetail.schedule_id)
        .where(
            ProductionSchedule.line_id == ps.line_id,
            func.trim(func.coalesce(ProductionSchedule.product_cd, "")) == product_cd_norm,
        )
    )
    line_min_d = line_min_res.scalar_one_or_none()
    lookback_d = min_d
    if line_min_d is not None and line_min_d < lookback_d:
        lookback_d = line_min_d
    forced_start = getattr(ps, "forced_start_date", None)

    machine_cd_norm = (machine.machine_cd or "").strip() if machine is not None else ""
    machine_name_norm = (machine.machine_name or "").strip() if machine is not None else ""
    machine_match_cond = None
    if machine_cd_norm and machine_name_norm:
        machine_match_cond = or_(
            sa_func.trim(sa_func.coalesce(StockTransactionLog.machine_cd, "")) == machine_cd_norm,
            sa_func.trim(sa_func.coalesce(StockTransactionLog.machine_cd, "")) == machine_name_norm,
        )
    elif machine_cd_norm:
        machine_match_cond = (
            sa_func.trim(sa_func.coalesce(StockTransactionLog.machine_cd, "")) == machine_cd_norm
        )
    elif machine_name_norm:
        machine_match_cond = (
            sa_func.trim(sa_func.coalesce(StockTransactionLog.machine_cd, "")) == machine_name_norm
        )
    else:
        # 設備識別子が取れない場合は machine 絞り込みを行わない（target_cd で同期）
        machine_match_cond = text("1=1")

    agg_res = await db.execute(
        select(
            sa_func.date(StockTransactionLog.transaction_time).label("tx_date"),
            sa_func.coalesce(sa_func.sum(StockTransactionLog.quantity), 0).label("qty"),
        )
        .where(
            StockTransactionLog.transaction_type == '実績',
            StockTransactionLog.transaction_time.isnot(None),
            sa_func.date(StockTransactionLog.transaction_time) >= lookback_d,
            sa_func.date(StockTransactionLog.transaction_time) <= max_d,
            machine_match_cond,
            sa_func.trim(StockTransactionLog.target_cd) == product_cd_norm,
        )
        .group_by(sa_func.date(StockTransactionLog.transaction_time))
    )
    actual_by_date: dict[date, int] = {}
    for row in agg_res.all():
        d = row.tx_date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        actual_by_date[d] = int(row.qty or 0)

    defect_process_cd = await _stock_log_defect_process_cd_for_machine(db, machine)
    defect_by_date: dict[date, int] = {}
    if defect_process_cd:
        agg_def = await db.execute(
            select(
                sa_func.date(StockTransactionLog.transaction_time).label("tx_date"),
                sa_func.coalesce(sa_func.sum(StockTransactionLog.quantity), 0).label("qty"),
            )
            .where(
                sa_func.trim(StockTransactionLog.transaction_type) == "不良",
                sa_func.trim(sa_func.coalesce(StockTransactionLog.process_cd, ""))
                == defect_process_cd,
                StockTransactionLog.transaction_time.isnot(None),
                sa_func.date(StockTransactionLog.transaction_time) >= lookback_d,
                sa_func.date(StockTransactionLog.transaction_time) <= max_d,
                sa_func.trim(StockTransactionLog.target_cd) == product_cd_norm,
            )
            .group_by(sa_func.date(StockTransactionLog.transaction_time))
        )
        for row in agg_def.all():
            d = row.tx_date
            if isinstance(d, str):
                d = date.fromisoformat(d)
            defect_by_date[d] = int(row.qty or 0)

    # 同一ライン・同一製品で前順位工単に既に配賦済みの実績を控除し、
    # 同日実績の二重計上（複数工単への重複反映）を防ぐ。
    ps_order = ps.order_no
    if ps_order is None:
        prior_cond = or_(
            ProductionSchedule.order_no.isnot(None),
            and_(ProductionSchedule.order_no.is_(None), ProductionSchedule.id < ps.id),
        )
    else:
        prior_cond = or_(
            ProductionSchedule.order_no < ps_order,
            and_(ProductionSchedule.order_no == ps_order, ProductionSchedule.id < ps.id),
        )

    prior_res = await db.execute(
        select(
            ScheduleDetail.schedule_date,
            sa_func.coalesce(sa_func.sum(ScheduleDetail.actual_qty), 0),
        )
        .join(ProductionSchedule, ProductionSchedule.id == ScheduleDetail.schedule_id)
        .where(
            ProductionSchedule.line_id == ps.line_id,
            sa_func.trim(sa_func.coalesce(ProductionSchedule.product_cd, "")) == product_cd_norm,
            ScheduleDetail.schedule_date <= max_d,
            ScheduleDetail.schedule_id != ps.id,
            prior_cond,
        )
        .group_by(ScheduleDetail.schedule_date)
    )
    prior_assigned_by_date: dict[date, int] = {}
    for d0, q0 in prior_res.all():
        if d0 is None:
            continue
        prior_assigned_by_date[d0] = int(q0 or 0)

    prior_def_res = await db.execute(
        select(
            ScheduleDetail.schedule_date,
            sa_func.coalesce(sa_func.sum(ScheduleDetail.defect_qty), 0),
        )
        .join(ProductionSchedule, ProductionSchedule.id == ScheduleDetail.schedule_id)
        .where(
            ProductionSchedule.line_id == ps.line_id,
            sa_func.trim(sa_func.coalesce(ProductionSchedule.product_cd, "")) == product_cd_norm,
            ScheduleDetail.schedule_date <= max_d,
            ScheduleDetail.schedule_id != ps.id,
            prior_cond,
        )
        .group_by(ScheduleDetail.schedule_date)
    )
    prior_defect_by_date: dict[date, int] = {}
    for d0, q0 in prior_def_res.all():
        if d0 is None:
            continue
        prior_defect_by_date[d0] = int(q0 or 0)

    # 同一ライン・同一製品・同日で「後順位」に計画がある日を集める。
    # 当該日が含まれる場合、自順位は当日計画数で頭打ちし、溢出（計画超過分）を後順位へ回す。
    # 含まれない（後順位に同製品の計画が無い）場合は最終順位として溢出も取り込む。
    if ps_order is None:
        later_cond = and_(
            ProductionSchedule.order_no.is_(None), ProductionSchedule.id > ps.id
        )
    else:
        later_cond = or_(
            ProductionSchedule.order_no.is_(None),
            ProductionSchedule.order_no > ps_order,
            and_(ProductionSchedule.order_no == ps_order, ProductionSchedule.id > ps.id),
        )
    later_planned_res = await db.execute(
        select(ScheduleDetail.schedule_date)
        .join(ProductionSchedule, ProductionSchedule.id == ScheduleDetail.schedule_id)
        .where(
            ProductionSchedule.line_id == ps.line_id,
            sa_func.trim(sa_func.coalesce(ProductionSchedule.product_cd, "")) == product_cd_norm,
            ProductionSchedule.status.in_(["PLANNING", "IN_PROGRESS"]),
            ScheduleDetail.schedule_date <= max_d,
            ScheduleDetail.schedule_id != ps.id,
            ScheduleDetail.planned_qty > 0,
            later_cond,
        )
        .group_by(ScheduleDetail.schedule_date)
    )
    later_planned_dates: set[date] = {
        d0 for (d0,) in later_planned_res.all() if d0 is not None
    }

    details_to_drop: list[ScheduleDetail] = []
    for det in details:
        dte = det.schedule_date
        if forced_start is not None and dte < forced_start:
            details_to_drop.append(det)
            continue

        raw_actual = actual_by_date.get(dte, 0)
        raw_defect = defect_by_date.get(dte, 0)
        already_assigned = prior_assigned_by_date.get(dte, 0)
        already_defect = prior_defect_by_date.get(dte, 0)
        actual = max(0, raw_actual - already_assigned)
        defect = max(0, raw_defect - already_defect)
        planned_today = int(det.planned_qty or 0)

        owner_id = await _schedule_id_owning_actual_on_date(db, ps.line_id, product_cd_norm, dte)

        if planned_today > 0:
            # 同一ライン・同一製品・同日で順位（order_no）順に良品実績を瀑布配分する。
            # 前順位が既に取り込んだ分（already_assigned）を控除した残りを当順位へ。
            # 後順位に同製品の計画があれば自順位の計画数で頭打ちし、溢出を後順位へ回す。
            # 後順位に計画が無ければ最終順位として溢出（計画超過分）も取り込む。
            if dte in later_planned_dates:
                actual = min(actual, planned_today)
        else:
            # 当該日に自工単の計画が無い場合は、従来どおり最小順位の計画工単（owner）へ寄せる。
            if owner_id is not None and int(owner_id) != int(ps.id):
                actual = 0

        # 不良は従来どおり最小順位の計画工単（owner）へ集約する。
        if owner_id is not None and int(owner_id) != int(ps.id):
            defect = 0

        det.actual_qty = actual
        det.defect_qty = defect
        det.remaining_qty = planned_today - int(actual) - int(defect)

    for det in details_to_drop:
        await db.delete(det)

    # 後続工単（後順位）の sync が前順位の確定済み actual を控除（already_assigned）できるよう、
    # 当工単の配分結果をここで flush する。呼び出し側は順位昇順に sync する前提。
    await db.flush()


async def _schedule_has_actual(db: AsyncSession, schedule_id: int) -> bool:
    from sqlalchemy import func as sa_func
    res = await db.execute(
        select(sa_func.coalesce(sa_func.sum(ScheduleDetail.actual_qty), 0))
        .where(ScheduleDetail.schedule_id == schedule_id)
    )
    return int(res.scalar() or 0) > 0


async def _last_actual_date_for_schedule(db: AsyncSession, schedule_id: int) -> Optional[date]:
    rows = await db.execute(
        select(ScheduleDetail.schedule_date)
        .where(
            ScheduleDetail.schedule_id == schedule_id,
            ScheduleDetail.actual_qty > 0,
        )
        .order_by(ScheduleDetail.schedule_date.desc())
        .limit(1)
    )
    return rows.scalar_one_or_none()


async def _sum_planned_qty_in_details(db: AsyncSession, schedule_id: int) -> int:
    from sqlalchemy import func as sa_func
    res = await db.execute(
        select(sa_func.coalesce(sa_func.sum(ScheduleDetail.planned_qty), 0))
        .where(ScheduleDetail.schedule_id == schedule_id)
    )
    return int(res.scalar() or 0)


def _combine_work_date_and_time(work_d: date, t, *, end_of_day: bool = False) -> datetime:
    """work_date + period_start/period_end を datetime に結合（period_end=00:00 の 24:00 相当対応）。"""
    if end_of_day and t.hour == 0 and t.minute == 0 and t.second == 0:
        return datetime(work_d.year, work_d.month, work_d.day) + timedelta(days=1)
    return datetime(work_d.year, work_d.month, work_d.day, t.hour, t.minute, t.second or 0)


def _instruction_management_code(
    production_month: date,
    production_line: str,
    product_cd: str,
    priority_order: Optional[int],
    production_lot_size: int,
    lot_number: str,
) -> str:
    """instruction_plans の management_code トリガーと同等ロジック（照合用）。"""
    yy = str(production_month.year)[-2:]
    mm = f"{production_month.month:02d}"
    line_suffix = (production_line or "")[-2:]  # RIGHT(production_line,2)
    po = int(priority_order or 0)
    po2 = f"{po:02d}"
    pls2 = f"{int(production_lot_size or 0):02d}"
    ln = str(lot_number or "")
    ln2 = ln.zfill(2)[-2:]  # LPAD(COALESCE(lot_number,''),2,'0')
    return f"{yy}{mm}{product_cd}{line_suffix}{po2}-{pls2}-{ln2}"


def _schedule_lot_size_code_context(ps: ProductionSchedule, slices: list) -> dict[str, int]:
    """
    工単ごとのロット数口径（再計算同期と同じ定義）。
    - forming: スライス残合計から算出する production_lot_size_engine
    - instruction: 計画一覧合計 full_plan_total から算出する production_lot_size_ip
    """
    slice_total = sum(int(s.planned_qty or 0) for s in slices)
    full_plan_total = int(ps.planned_process_qty or 0) + int(getattr(ps, "prev_month_carryover", 0) or 0)
    if full_plan_total <= 0:
        full_plan_total = slice_total
    lot_size_snapshot = int(getattr(ps, "lot_size_snapshot", 0) or 0)
    pls_engine = 0
    pls_instruction = 0
    if lot_size_snapshot > 0:
        if slice_total > 0:
            pls_engine, _ = _aps_build_batch_qty_rows(slice_total, lot_size_snapshot)
        if full_plan_total > 0:
            pls_instruction, _ = _aps_build_batch_qty_rows(full_plan_total, lot_size_snapshot)
    return {
        "slice_total": slice_total,
        "full_plan_total": full_plan_total,
        "production_lot_size_forming": int(pls_engine),
        "production_lot_size_instruction": int(pls_instruction),
    }


def _lot_progress_key(aps_schedule_id: int, lot_number: str) -> str:
    return f"{int(aps_schedule_id)}_{str(lot_number or '')}"


def _lot_planned_daily_from_slices_for_schedule(
    aps_schedule_id: int,
    batches: List[ApsBatchPlan],
    slices: list,
) -> dict[str, dict[str, int]]:
    """
    ロット別：スライス時間帯と aps_batch_plans の start/end 重なりで日別配分。
    get_production_progress の lot_planned_daily 構築と同趣旨。
    """
    out: dict[str, dict[str, int]] = {}
    if not batches or not slices:
        return out
    sid = int(aps_schedule_id)
    for batch in batches:
        if int(batch.aps_schedule_id) != sid:
            continue
        lk = _lot_progress_key(batch.aps_schedule_id, str(batch.lot_number or ""))
        daily_map: dict[str, int] = {}
        b_start = batch.start_date
        b_end = batch.end_date
        if not b_start or not b_end:
            out[lk] = daily_map
            continue
        for sl in slices:
            if int(sl.schedule_id) != sid:
                continue
            sl_start = _combine_work_date_and_time(sl.work_date, sl.period_start, end_of_day=False)
            is_eod = sl.period_end == time(0, 0, 0) and sl.period_start != time(0, 0, 0)
            sl_end = _combine_work_date_and_time(sl.work_date, sl.period_end, end_of_day=is_eod)
            if sl_end <= b_start or sl_start >= b_end:
                continue
            sq = int(sl.planned_qty or 0)
            if sq <= 0:
                continue
            overlap_start = max(sl_start, b_start)
            overlap_end = min(sl_end, b_end)
            sl_dur = max(1.0, (sl_end - sl_start).total_seconds())
            overlap_dur = max(0.0, (overlap_end - overlap_start).total_seconds())
            portion = int(round(sq * overlap_dur / sl_dur))
            if portion <= 0:
                continue
            d_key = sl.work_date.isoformat()
            daily_map[d_key] = daily_map.get(d_key, 0) + portion
        out[lk] = daily_map
    return out


def _split_int_by_weights(total: int, weights: dict[str, int]) -> dict[str, int]:
    """weights に比例して total を整数配分（合計一致）。"""
    keys = [k for k in weights]
    if total <= 0:
        return {k: 0 for k in keys}
    ws = [max(0, int(weights.get(k, 0) or 0)) for k in keys]
    ssum = sum(ws)
    if ssum <= 0:
        return {k: 0 for k in keys}
    raw_fracs: list[tuple[float, str]] = []
    acc = 0
    out: dict[str, int] = {}
    for k, w in zip(keys, ws):
        val = total * w / ssum
        q = int(val)
        out[k] = q
        acc += q
        raw_fracs.append((val - q, k))
    rem = total - acc
    raw_fracs.sort(key=lambda x: (-x[0], x[1]))
    for i in range(rem):
        out[raw_fracs[i][1]] += 1
    return out


def _daily_upstream_tint_map_for_schedule(
    daily: dict[str, int],
    dates_list: list[str],
    aps_schedule_id: int,
    batches: List[ApsBatchPlan],
    slices: list,
    lot_upstream_state: dict[str, str],
) -> dict[str, DailyUpstreamTintSeg]:
    if not batches:
        return {}
    sid = int(aps_schedule_id)
    lot_planned = _lot_planned_daily_from_slices_for_schedule(sid, batches, slices)
    lot_keys = [_lot_progress_key(sid, str(b.lot_number or "")) for b in batches if int(b.aps_schedule_id) == sid]
    lot_keys = list(dict.fromkeys(lot_keys))
    out: dict[str, DailyUpstreamTintSeg] = {}
    for d in dates_list:
        t_total = int(daily.get(d, 0) or 0)
        if t_total <= 0:
            continue
        shares = {lk: int(lot_planned.get(lk, {}).get(d, 0) or 0) for lk in lot_keys}
        portions = _split_int_by_weights(t_total, shares)
        if sum(portions.values()) == 0:
            w_sched: dict[str, int] = {}
            for b in batches:
                if int(b.aps_schedule_id) != sid:
                    continue
                lk0 = _lot_progress_key(sid, str(b.lot_number or ""))
                w_sched[lk0] = max(0, int(_batch_display_planned_qty(b)))
            portions = _split_int_by_weights(t_total, w_sched)
        if sum(portions.values()) == 0:
            out[d] = DailyUpstreamTintSeg(in_cutting=0, in_instruction=0, only_planned=t_total)
            continue
        ic = ins = pl = 0
        for lk, qty in portions.items():
            if qty <= 0:
                continue
            st = lot_upstream_state.get(lk, "planned")
            if st == "cutting":
                ic += qty
            elif st == "instruction":
                ins += qty
            else:
                pl += qty
        out[d] = DailyUpstreamTintSeg(in_cutting=ic, in_instruction=ins, only_planned=pl)
    return out


async def _schedule_batch_upstream_context(
    db: AsyncSession, schedule_ids: list[int],
) -> tuple[dict[int, list[ApsBatchPlan]], dict[str, str]]:
    """
    各製造指示の APS ロット一覧と、ロットキー別の上流状態（cutting / instruction / planned）。
    """
    if not schedule_ids:
        return {}, {}
    by_sched: dict[int, list[ApsBatchPlan]] = defaultdict(list)
    batch_result = await db.execute(
        select(ApsBatchPlan).where(ApsBatchPlan.aps_schedule_id.in_(schedule_ids))
    )
    line_batches = batch_result.scalars().all()
    for b in line_batches:
        by_sched[int(b.aps_schedule_id)].append(b)
    if not line_batches:
        return dict(by_sched), {}

    bids = [int(b.id) for b in line_batches]
    mc_by_bid: dict[int, str] = {}
    for b in line_batches:
        bid = int(b.id)
        mc_by_bid[bid] = _instruction_management_code(
            b.production_month,
            b.production_line or "",
            b.product_cd or "",
            b.priority_order,
            int(b.production_lot_size or 0),
            b.lot_number or "",
        )

    hit_bids_cm: set[int] = set()
    if bids:
        res_b = await db.execute(
            text(
                """
                SELECT DISTINCT abp.id
                FROM aps_batch_plans abp
                INNER JOIN cutting_management cm ON cm.aps_batch_plan_id = abp.id
                  AND TRIM(cm.product_cd) = TRIM(abp.product_cd)
                  AND TRIM(COALESCE(cm.lot_number, '')) = TRIM(COALESCE(abp.lot_number, ''))
                  AND cm.production_month = abp.production_month
                  AND COALESCE(cm.priority_order, 0) = COALESCE(abp.priority_order, 0)
                  AND COALESCE(cm.production_lot_size, 0) = COALESCE(abp.production_lot_size, 0)
                WHERE abp.id IN :bids
                """
            ),
            {"bids": tuple(bids)},
        )
        for row in res_b.mappings().all():
            x = row.get("id")
            if x is not None:
                hit_bids_cm.add(int(x))

    all_mcs = tuple({str(v) for v in mc_by_bid.values() if v})
    hit_mcs_cm: set[str] = set()
    if all_mcs:
        res_m = await db.execute(
            text("SELECT DISTINCT management_code FROM cutting_management WHERE management_code IN :mcs"),
            {"mcs": all_mcs},
        )
        for row in res_m.mappings().all():
            mc0 = row.get("management_code")
            if mc0 is not None:
                hit_mcs_cm.add(str(mc0))

    hit_bids_ins: set[int] = set()
    hit_mcs_ins: set[str] = set()
    try:
        if bids:
            ins_b = await db.execute(
                text(
                    """
                    SELECT DISTINCT abp.id
                    FROM aps_batch_plans abp
                    INNER JOIN instruction_plans ip ON ip.aps_batch_plan_id = abp.id
                      AND TRIM(ip.management_code) = TRIM(
                        CONCAT(
                          RIGHT(YEAR(abp.production_month), 2),
                          LPAD(MONTH(abp.production_month), 2, '0'),
                          abp.product_cd,
                          RIGHT(COALESCE(abp.production_line, ''), 2),
                          LPAD(COALESCE(abp.priority_order, 0), 2, '0'),
                          '-',
                          LPAD(COALESCE(abp.production_lot_size, 0), 2, '0'),
                          '-',
                          LPAD(COALESCE(abp.lot_number, ''), 2, '0')
                        )
                      )
                    WHERE abp.id IN :bids
                    """
                ),
                {"bids": tuple(bids)},
            )
            for row in ins_b.mappings().all():
                x = row.get("id")
                if x is not None:
                    hit_bids_ins.add(int(x))
        if all_mcs:
            ins_m = await db.execute(
                text(
                    "SELECT DISTINCT management_code FROM instruction_plans "
                    "WHERE management_code IN :mcs"
                ),
                {"mcs": all_mcs},
            )
            for row in ins_m.mappings().all():
                mc0 = row.get("management_code")
                if mc0 is not None:
                    hit_mcs_ins.add(str(mc0))
    except (OperationalError, ProgrammingError):
        pass

    lot_upstream_state: dict[str, str] = {}
    for b in line_batches:
        bid = int(b.id)
        mc = mc_by_bid[bid]
        lk = _lot_progress_key(b.aps_schedule_id, str(b.lot_number or ""))
        in_cm = bid in hit_bids_cm or mc in hit_mcs_cm
        in_ins = bid in hit_bids_ins or mc in hit_mcs_ins
        if in_cm:
            lot_upstream_state[lk] = "cutting"
        elif in_ins:
            lot_upstream_state[lk] = "instruction"
        else:
            lot_upstream_state[lk] = "planned"

    return dict(by_sched), lot_upstream_state


# cutting_management ↔ aps_batch_plans の「業務上一致」JOIN（照会・進捗・不良と共通）
_CUTTING_ABP_FIELD_ALIGN_SQL = """
INNER JOIN aps_batch_plans abp ON abp.id = :bid
  AND cm.aps_batch_plan_id = abp.id
  AND TRIM(cm.product_cd) = TRIM(abp.product_cd)
  AND TRIM(COALESCE(cm.lot_number, '')) = TRIM(COALESCE(abp.lot_number, ''))
  AND cm.production_month = abp.production_month
  AND COALESCE(cm.priority_order, 0) = COALESCE(abp.priority_order, 0)
  AND COALESCE(cm.production_lot_size, 0) = COALESCE(abp.production_lot_size, 0)
"""


async def _upstream_defect_qty_for_aligned_batch_plan(db: AsyncSession, batch_plan_id: int) -> int:
    """
    aps_batch_plans と cutting の品番・ロット・月・顺位・ロット数が一致する行のみ不良合算。
    aps_batch_plan_id だけの誤紐付けは含めない（照会バインディングと同趣旨）。
    """
    bid = int(batch_plan_id)
    if bid <= 0:
        return 0
    cut_res = await db.execute(
        text(
            f"""
            SELECT COALESCE(SUM(COALESCE(cm.defect_qty, 0)), 0) AS s
            FROM cutting_management cm
            {_CUTTING_ABP_FIELD_ALIGN_SQL}
            """
        ),
        {"bid": bid},
    )
    cut_def = int(cut_res.scalar() or 0)
    ch_res = await db.execute(
        text(
            f"""
            SELECT COALESCE(SUM(COALESCE(ch.defect_qty, 0)), 0) AS s
            FROM chamfering_management ch
            INNER JOIN cutting_management cm ON cm.id = ch.cutting_management_id
            {_CUTTING_ABP_FIELD_ALIGN_SQL}
            """
        ),
        {"bid": bid},
    )
    cham_def = int(ch_res.scalar() or 0)
    return cut_def + cham_def


async def _upstream_defect_qty_for_management_code_fallback(db: AsyncSession, management_code: str) -> int:
    """
    management_code 一致で切断・面取不良を合算（照会コードと DB コードが一致する行のみ）。
    切断行が無い場合は面取のみ management_code 一致で合算。
    """
    mc = (management_code or "").strip()
    if not mc:
        return 0
    cut_res = await db.execute(
        text(
            "SELECT id, COALESCE(defect_qty, 0) AS dq FROM cutting_management "
            "WHERE management_code = :mc LIMIT 1"
        ),
        {"mc": mc},
    )
    crow = cut_res.mappings().first()
    cut_def = int(crow["dq"] or 0) if crow else 0
    if crow and crow.get("id") is not None:
        cid = int(crow["id"])
        ch_res = await db.execute(
            text(
                "SELECT COALESCE(SUM(COALESCE(defect_qty, 0)), 0) AS s FROM chamfering_management "
                "WHERE cutting_management_id = :cid"
            ),
            {"cid": cid},
        )
        cham_def = int(ch_res.scalar() or 0)
    else:
        ch_res = await db.execute(
            text(
                "SELECT COALESCE(SUM(COALESCE(defect_qty, 0)), 0) AS s FROM chamfering_management "
                "WHERE management_code = :mc"
            ),
            {"mc": mc},
        )
        cham_def = int(ch_res.scalar() or 0)
    return cut_def + cham_def


async def _upstream_defect_qty_resolved(
    db: AsyncSession,
    *,
    batch_plan_id: Optional[int],
    management_code: str,
) -> int:
    """
    前工程不良合算（照会・進捗の紐付け規則に合わせる）。

    1. 照会 management_code と cutting_management.management_code が一致 → その行＋面取
    2. 上記が無く、aps_batch_plans と cutting がフィールド一致で紐づく → 一致行のみ合算
    3. 切断は無いが面取のみ code 一致 → 面取のみ
    4. 誤紐付け（batch_id のみ・code 不一致）は 0（不良を他ロットに持ち込まない）
    """
    mc = (management_code or "").strip()
    if mc:
        cut_mc_res = await db.execute(
            text(
                "SELECT COUNT(*) AS c FROM cutting_management WHERE management_code = :mc"
            ),
            {"mc": mc},
        )
        if int(cut_mc_res.scalar() or 0) > 0:
            return await _upstream_defect_qty_for_management_code_fallback(db, mc)

    bid = int(batch_plan_id) if batch_plan_id is not None else 0
    if bid > 0:
        align_cnt = await db.execute(
            text(
                f"""
                SELECT COUNT(*) AS c FROM cutting_management cm
                {_CUTTING_ABP_FIELD_ALIGN_SQL}
                """
            ),
            {"bid": bid},
        )
        if int(align_cnt.scalar() or 0) > 0:
            return await _upstream_defect_qty_for_aligned_batch_plan(db, bid)

    if mc:
        return await _upstream_defect_qty_for_management_code_fallback(db, mc)
    return 0


async def _upstream_defect_qty_by_lots(
    db: AsyncSession,
    *,
    production_month: date,
    production_line: str,
    product_cd: str,
    priority_order: Optional[int],
    production_lot_size_engine: int,
    lot_numbers_ordered: Iterable[str],
    existing_bp_by_lot: Optional[Dict[str, ApsBatchPlan]] = None,
) -> dict[str, int]:
    """ロット番号ごとの前工程不良。既存 aps_batch_plans.id があれば cutting.aps_batch_plan_id 経路を優先。"""
    out: dict[str, int] = {}
    seen: set[str] = set()
    bp_map = existing_bp_by_lot or {}
    for ln in lot_numbers_ordered:
        s = str(ln)
        if s in seen:
            continue
        seen.add(s)
        mc = _instruction_management_code(
            production_month,
            production_line,
            product_cd,
            priority_order,
            production_lot_size_engine,
            s,
        )
        ex = bp_map.get(s)
        bid = int(ex.id) if ex is not None else None
        out[s] = await _upstream_defect_qty_resolved(db, batch_plan_id=bid, management_code=mc)
    return out


async def _backfill_cutting_management_aps_batch_plan_id(
    db: AsyncSession,
    schedule_id: int,
) -> None:
    """同一成型工単の aps_batch_plans と切断行を品番・ロット・生産月・顺位・ロット数で突合し aps_batch_plan_id を補完する。"""
    await db.execute(
        text(
            """
            UPDATE cutting_management cm
            INNER JOIN aps_batch_plans abp
              ON abp.aps_schedule_id = :sid
             AND TRIM(cm.product_cd) = TRIM(abp.product_cd)
             AND TRIM(COALESCE(cm.lot_number, '')) = TRIM(COALESCE(abp.lot_number, ''))
             AND cm.production_month = abp.production_month
             AND COALESCE(cm.priority_order, 0) = COALESCE(abp.priority_order, 0)
             AND COALESCE(cm.production_lot_size, 0) = COALESCE(abp.production_lot_size, 0)
            SET cm.aps_batch_plan_id = abp.id
            WHERE cm.aps_batch_plan_id IS NULL
            """
        ),
        {"sid": int(schedule_id)},
    )


def _aps_build_batch_qty_rows(total_qty: int, lot_size_snapshot: int) -> tuple[int, List[tuple[int, int]]]:
    """ロット数と [(lot_index, qty), ...]（qty>0 のみ）。"""
    production_lot_size = max(1, int(math.ceil(total_qty / float(lot_size_snapshot))))
    batch_qtys: List[tuple[int, int]] = []
    for i in range(1, production_lot_size + 1):
        if i < production_lot_size:
            batch_qtys.append((i, lot_size_snapshot))
        else:
            remain = total_qty - lot_size_snapshot * (production_lot_size - 1)
            batch_qtys.append((i, max(0, int(remain))))
    batch_qtys = [(i, q) for i, q in batch_qtys if q > 0]
    return production_lot_size, batch_qtys


def _scale_slice_rows_to_instruction_total(
    slices: List[ScheduleSliceAllocation],
    slice_total: int,
    target_total: int,
) -> List[tuple[ScheduleSliceAllocation, int]]:
    """
    成型スライス合計 slice_total を、切断指示用の計画本数 target_total に比例拡大（切断前計画）。
    成型実績でスライスが「残数」のみでも、instruction_plans は計画一覧の合計本数を表す。
    """
    if not slices:
        return []
    if slice_total <= 0 or target_total <= 0:
        return [(s, int(s.planned_qty or 0)) for s in slices]
    if slice_total == target_total:
        return [(s, int(s.planned_qty or 0)) for s in slices]
    out: List[tuple[ScheduleSliceAllocation, int]] = []
    acc = 0
    for idx in range(len(slices) - 1):
        s = slices[idx]
        q = int(s.planned_qty or 0)
        sq = int(math.floor(target_total * q / slice_total))
        out.append((s, sq))
        acc += sq
    last_s = slices[-1]
    out.append((last_s, max(0, target_total - acc)))
    return out


def _walk_slice_pairs_to_batches(
    slice_pairs: List[tuple[ScheduleSliceAllocation, int]],
    batch_qtys: List[tuple[int, int]],
) -> List[Dict[str, Any]]:
    """スライス（数量付き）をロットへ割当、開始・終了時刻を付与。"""
    batches: List[Dict[str, Any]] = []
    if not batch_qtys:
        return batches
    batch_idx = 0
    batch_accum_qty = 0
    batch_start_dt: Optional[datetime] = None
    batch_end_dt: Optional[datetime] = None

    for s, slice_total_qty in slice_pairs:
        if slice_total_qty <= 0:
            continue
        slice_allocated_qty_in_current = 0
        is_end_of_day = s.period_end == time(0, 0, 0) and s.period_start != time(0, 0, 0)
        slice_start_dt = _combine_work_date_and_time(s.work_date, s.period_start, end_of_day=False)
        slice_end_dt = _combine_work_date_and_time(s.work_date, s.period_end, end_of_day=is_end_of_day)
        duration_sec = max(0.0, (slice_end_dt - slice_start_dt).total_seconds())

        slice_remaining_qty = slice_total_qty - slice_allocated_qty_in_current
        while slice_remaining_qty > 0 and batch_idx < len(batch_qtys):
            lot_i, qty_i = batch_qtys[batch_idx]
            batch_need = int(qty_i - batch_accum_qty)
            if batch_need <= 0:
                batch_idx += 1
                batch_accum_qty = 0
                if batch_idx >= len(batch_qtys):
                    break
                batch_start_dt = None
                batch_end_dt = None
                continue

            portion_qty = min(slice_remaining_qty, batch_need)
            start_frac = slice_allocated_qty_in_current / float(slice_total_qty)
            end_allocated_qty = slice_allocated_qty_in_current + portion_qty
            end_frac = end_allocated_qty / float(slice_total_qty)
            portion_start_dt = slice_start_dt + timedelta(seconds=duration_sec * start_frac)
            portion_end_dt = slice_start_dt + timedelta(seconds=duration_sec * end_frac)

            if batch_start_dt is None:
                batch_start_dt = portion_start_dt
            batch_end_dt = portion_end_dt
            batch_accum_qty += portion_qty
            slice_allocated_qty_in_current += portion_qty
            slice_remaining_qty -= portion_qty

            if batch_accum_qty >= qty_i:
                batches.append(
                    {
                        "lot_number": str(lot_i),
                        "planned_quantity": int(qty_i),
                        "start_date": batch_start_dt,
                        "end_date": batch_end_dt,
                    }
                )
                batch_idx += 1
                batch_accum_qty = 0
                batch_start_dt = None
                batch_end_dt = None
    return batches


# instruction_plans へ書き込むのは「成型」(KT04) の設備に限る（get_lines の processCd 判定と同一）。aps_batch_plans は全工程で更新する。
_APS_INSTRUCTION_PLANS_SYNC_PROCESS_CD = _APS_FORMING_PROCESS_CD
# 生産進捗：True のとき schedule_details.actual_qty をロット順に割当て、残数を翌日以降に再按分し日別ガントと整列する。
_PRODUCTION_PROGRESS_USE_FORMING_ACTUAL = True


async def _machine_matches_process_cd(
    db: AsyncSession,
    machine: Machine,
    process_cd: str,
) -> bool:
    """設備の machine_type が指定工程の名称または工程CDと一致するか（/lines?processCd= と同じ）。"""
    pc = (process_cd or "").strip()
    if not pc:
        return False
    proc_result = await db.execute(select(Process).where(Process.process_cd == pc))
    proc = proc_result.scalar_one_or_none()
    if proc is None:
        return False
    pn = (proc.process_name or "").strip()
    pcc = (proc.process_cd or "").strip()
    mt = (machine.machine_type or "").strip()
    if not mt:
        return False
    if pn and mt == pn:
        return True
    if pcc and mt == pcc:
        return True
    return False


def _norm_lot_number(v: Any) -> str:
    s = str(v or "").strip()
    s2 = s.lstrip("0")
    return s2 if s2 else "0"


async def _cutting_identity_lock_for_instruction_sync(
    db: AsyncSession,
    *,
    production_month: date,
    production_line: str,
    product_cd: str,
    priority_order: Optional[int],
    target_lot_norms: set[str],
) -> tuple[set[str], set[str]]:
    """
    計画数量変更で management_code が変わっても、既に cutting_management にあるロットは
    instruction_plans の新規 INSERT 対象から外す。
    同一品番でも順位（priority_order）が異なれば別ロットとして扱い、他順位の切断行でロックしない。
    戻り値: (ロックするロットの正規化キー, 既存切断の management_code 集合)
    """
    locked_norms: set[str] = set()
    legacy_mcs: set[str] = set()
    if not target_lot_norms:
        return locked_norms, legacy_mcs
    res = await db.execute(
        text(
            """
            SELECT TRIM(COALESCE(lot_number, '')) AS lot_number,
                   TRIM(COALESCE(management_code, '')) AS management_code
            FROM cutting_management
            WHERE production_month = :production_month
              AND TRIM(COALESCE(production_line, '')) = TRIM(COALESCE(:production_line, ''))
              AND TRIM(COALESCE(product_cd, '')) = TRIM(COALESCE(:product_cd, ''))
              AND COALESCE(priority_order, 0) = COALESCE(:priority_order, 0)
            """
        ),
        {
            "production_month": production_month,
            "production_line": str(production_line),
            "product_cd": (product_cd or "").strip(),
            "priority_order": priority_order,
        },
    )
    for row in res.mappings().all():
        ln_norm = _norm_lot_number(row.get("lot_number"))
        if ln_norm in target_lot_norms:
            locked_norms.add(ln_norm)
            mc = str(row.get("management_code") or "").strip()
            if mc:
                legacy_mcs.add(mc)
    return locked_norms, legacy_mcs


async def _instruction_plans_chamfer_sw_flags(
    db: AsyncSession,
    product_cd: str,
    prod: Optional[Product],
) -> tuple[int, int]:
    """
    製品工程ルートに基づき面取工程・SW工程の有無（instruction_plans 用 0/1）。
    master.get_product_batch_detail と同じ判定（工程名に「面取」「SW」/ swaging）。
    """
    route_cd = ""
    if prod is not None and getattr(prod, "route_cd", None):
        route_cd = (prod.route_cd or "").strip()
    if not route_cd:
        pr = await db.execute(select(Product.route_cd).where(Product.product_cd == product_cd))
        route_cd = (pr.scalar() or "").strip()
    if not route_cd:
        return (0, 0)
    steps_res = await db.execute(
        select(ProductRouteStep.process_cd).where(
            ProductRouteStep.product_cd == product_cd,
            ProductRouteStep.route_cd == route_cd,
        )
    )
    process_cds = [r[0] for r in steps_res.all() if r[0]]
    if not process_cds:
        return (0, 0)
    proc_res = await db.execute(select(Process.process_name).where(Process.process_cd.in_(process_cds)))
    has_ch = 0
    has_sw = 0
    for (pname,) in proc_res.all():
        name = (pname or "").strip()
        if "面取" in name:
            has_ch = 1
        if "SW" in name or "swaging" in name.lower():
            has_sw = 1
    return (has_ch, has_sw)


async def _sync_instruction_plans_from_aps_schedule(
    db: AsyncSession,
    ps: ProductionSchedule,
    *,
    machine: Optional[Machine] = None,
    is_forming_line: Optional[bool] = None,
    product_cache: Optional[dict[str, Optional[Product]]] = None,
    material_cache: Optional[dict[str, Optional[Material]]] = None,
    supplier_cache: Optional[dict[str, Optional[Supplier]]] = None,
    chamfer_sw_cache: Optional[dict[str, tuple[int, int]]] = None,
) -> None:
    """
    APS の工単スケジュールをロット（lot_number）に展開し、aps_batch_plans / instruction_plans を
    1:1 で同期する（簡素化版）。

    ・ロット構造は計画一覧の合計（planned_process_qty + prev_month_carryover）と lot_size_snapshot
      から一意に決まり、aps_batch_plans と instruction_plans の両テーブルで共通とする。
      これにより同一スケジュール内のロットは管理コード命名（年月+品番+ライン+順位+ロット数+ロット番号）
      が一意で、品番が同じでも順位が違えば管理コードは異なる。
    ・cutting_management に既に取り込まれたロット（管理コード一致 or aps_batch_plan_id 紐付け）は、
      管理コードに関わる identity フィールド（production_month / priority_order /
      production_lot_size / lot_number / product_cd）を一切更新せず、instruction_plans も触らない。
      これにより「計画一覧の変更で管理コードが書き換わる」事故を防ぐ。
    ・計画減量等で対象外になった unlocked ロットは両テーブルから削除する。
    ・aps_batch_plans.planned_quantity は full_lot_qty - upstream_defect_qty（成型側有効本数）、
      original_planned_quantity は full_lot_qty（計画一覧で確定したロット本数）として保存する。
    ・エンジン未走行（スライス無し）の場合は start_date / end_date が None のまま行のみ作成する。

    性能最適化パラメータ（省略時は従来通り DB 取得）:
      machine            事前取得済みの Machine
      is_forming_line    事前判定済みの成型ライン判定
      product_cache      {product_cd: Product}
      material_cache     {material_cd: Material}
      supplier_cache     {supplier_cd: Supplier}
      chamfer_sw_cache   {product_cd: (has_chamfering, has_sw)}
    """
    if not ps.product_cd:
        return

    if machine is None:
        machine = await db.get(Machine, ps.line_id)
    if machine is None:
        return
    if is_forming_line is None:
        sync_instruction_plans = await _machine_matches_process_cd(
            db, machine, _APS_INSTRUCTION_PLANS_SYNC_PROCESS_CD
        )
    else:
        sync_instruction_plans = is_forming_line

    slice_result = await db.execute(
        select(ScheduleSliceAllocation)
        .where(ScheduleSliceAllocation.schedule_id == ps.id)
        .order_by(
            ScheduleSliceAllocation.work_date,
            ScheduleSliceAllocation.period_start,
            ScheduleSliceAllocation.sort_order,
            ScheduleSliceAllocation.id,
        )
    )
    slices = slice_result.scalars().all()
    slice_total = sum(int(s.planned_qty or 0) for s in slices)

    full_plan_total = int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0)
    if full_plan_total <= 0:
        full_plan_total = slice_total
    if full_plan_total <= 0:
        return

    # 生産月/ライン/製品情報（管理コードと整合させるため機械側情報を優先）
    # instruction_plans の management_code トリガーは RIGHT(production_line,2) を使うため、
    # instruction_plans 側に保存する production_line は「設備名」に揃える
    production_line = (machine.machine_name or '').strip() or (machine.machine_cd or str(machine.id))
    production_name = ps.item_name or ""
    production_product_cd = (ps.product_cd or "").strip()

    # cutting/scrap/material 情報（products -> materials）
    # APS schedule は products/material のキー（product_cd/material_cd）を持つ前提で同期する。
    cutting_length = None
    chamfering_length = None
    developed_length = None
    scrap_length = None
    take_count = None
    material_name = None
    material_manufacturer = None
    standard_specification = None

    prod = None
    if production_product_cd:
        if product_cache is not None:
            prod = product_cache.get(production_product_cd)
        else:
            prod_res = await db.execute(select(Product).where(Product.product_cd == production_product_cd))
            prod = prod_res.scalars().first()

    if prod is not None:
        cutting_length = float(prod.cut_length) if prod.cut_length is not None else None
        chamfering_length = float(prod.chamfer_length) if prod.chamfer_length is not None else None
        developed_length = float(prod.developed_length) if prod.developed_length is not None else None
        scrap_length = float(prod.scrap_length) if prod.scrap_length is not None else None
        take_count = int(prod.take_count) if prod.take_count is not None else None

        if prod.material_cd:
            mat_cd = (prod.material_cd or "").strip()
            mat = None
            if material_cache is not None:
                mat = material_cache.get(mat_cd)
            else:
                mat_res = await db.execute(select(Material).where(Material.material_cd == mat_cd))
                mat = mat_res.scalars().first()
            if mat is not None:
                material_name = mat.material_name
                s_cd = (mat.supplier_cd or "").strip() if mat.supplier_cd else ""
                if s_cd:
                    sup = None
                    if supplier_cache is not None:
                        sup = supplier_cache.get(s_cd)
                    else:
                        sup_res = await db.execute(select(Supplier).where(Supplier.supplier_cd == s_cd))
                        sup = sup_res.scalars().first()
                    material_manufacturer = (sup.supplier_name or "").strip() if sup is not None else s_cd
                else:
                    material_manufacturer = None
                standard_specification = mat.standard_spec

    if chamfer_sw_cache is not None and production_product_cd in chamfer_sw_cache:
        has_chamfering_process, has_sw_process = chamfer_sw_cache[production_product_cd]
    else:
        has_chamfering_process, has_sw_process = await _instruction_plans_chamfer_sw_flags(
            db, production_product_cd, prod
        )

    lot_size_snapshot = int(getattr(ps, "lot_size_snapshot", 0) or 0)
    if lot_size_snapshot <= 0:
        if prod is not None and getattr(prod, "lot_size", None) is not None:
            lot_size_snapshot = int(prod.lot_size or 0)
        else:
            pr_res = await db.execute(select(Product.lot_size).where(Product.product_cd == production_product_cd))
            lot_size_snapshot = int(pr_res.scalar() or 0)
    if lot_size_snapshot <= 0:
        return

    # 単一の真実源：計画一覧合計（full_plan_total）と lot_size_snapshot からロット構造を確定する。
    # 同一スケジュールの aps_batch_plans / instruction_plans はこの構造で 1:1 対応する。
    production_lot_size, batch_qtys = _aps_build_batch_qty_rows(full_plan_total, lot_size_snapshot)
    if not batch_qtys:
        return

    # 生産月：スライスがあれば最初日基準、無ければ今日基準（計画一覧追加直後のエンジン未走行ケース）
    if slices:
        min_work_date = min(s.work_date for s in slices)
        production_month = date(min_work_date.year, min_work_date.month, 1)
    else:
        today = now_jst().date()
        production_month = date(today.year, today.month, 1)

    # エンジンスライスがあればロット別 start_date/end_date を算出（スライスを full_plan_total へ比例拡大）
    batch_dates_by_lot: dict[str, tuple[Optional[datetime], Optional[datetime]]] = {}
    if slices and slice_total > 0:
        slice_pairs_scaled = _scale_slice_rows_to_instruction_total(slices, slice_total, full_plan_total)
        walked = _walk_slice_pairs_to_batches(slice_pairs_scaled, batch_qtys)
        for w in walked:
            batch_dates_by_lot[str(w["lot_number"])] = (w["start_date"], w["end_date"])

    target_lot_nums: list[str] = [str(lot_i) for lot_i, _ in batch_qtys]
    target_lot_qtys: dict[str, int] = {str(lot_i): int(qty_i) for lot_i, qty_i in batch_qtys}
    target_lot_norms: set[str] = {_norm_lot_number(n) for n in target_lot_nums}

    # 既存 aps_batch_plans を先読み
    existing_bp_res = await db.execute(
        select(ApsBatchPlan).where(ApsBatchPlan.aps_schedule_id == ps.id)
    )
    existing_bp_by_lot: dict[str, ApsBatchPlan] = {
        str(bp.lot_number): bp for bp in existing_bp_res.scalars().all()
    }

    # 既存 APS ロットに紐づく切断行へ aps_batch_plan_id を補完
    await _backfill_cutting_management_aps_batch_plan_id(db, ps.id)

    # 管理コード一致／aps_batch_plan_id 紐付けで cutting_management に存在するロットを lock 判定
    all_lot_norms_for_lock = target_lot_norms | {_norm_lot_number(n) for n in existing_bp_by_lot.keys()}
    cutting_locked_lot_norms, cutting_exists_mcs = await _cutting_identity_lock_for_instruction_sync(
        db,
        production_month=production_month,
        production_line=str(production_line),
        product_cd=production_product_cd,
        priority_order=ps.order_no,
        target_lot_norms=all_lot_norms_for_lock,
    )
    if existing_bp_by_lot:
        bid_list = [int(bp.id) for bp in existing_bp_by_lot.values() if bp.id is not None]
        if bid_list:
            bid_lock_res = await db.execute(
                text(
                    f"""
                    SELECT DISTINCT abp.id
                    FROM aps_batch_plans abp
                    INNER JOIN cutting_management cm ON cm.aps_batch_plan_id = abp.id
                      AND TRIM(cm.product_cd) = TRIM(abp.product_cd)
                      AND TRIM(COALESCE(cm.lot_number, '')) = TRIM(COALESCE(abp.lot_number, ''))
                      AND cm.production_month = abp.production_month
                      AND COALESCE(cm.priority_order, 0) = COALESCE(abp.priority_order, 0)
                      AND COALESCE(cm.production_lot_size, 0) = COALESCE(abp.production_lot_size, 0)
                      AND COALESCE(cm.priority_order, 0) = COALESCE(:schedule_priority, 0)
                    WHERE abp.id IN :bids
                    """
                ),
                {"bids": tuple(bid_list), "schedule_priority": ps.order_no},
            )
            locked_bids = {int(r[0]) for r in bid_lock_res.all() if r[0] is not None}
            for lot_str, bp in existing_bp_by_lot.items():
                if bp.id is not None and int(bp.id) in locked_bids:
                    cutting_locked_lot_norms.add(_norm_lot_number(lot_str))

    # ロット別 upstream 不良（成型側有効本数 = full_lot_qty - upstream）
    lot_nums_for_upstream = list(dict.fromkeys([*target_lot_nums, *existing_bp_by_lot.keys()]))
    upstream_map = await _upstream_defect_qty_by_lots(
        db,
        production_month=production_month,
        production_line=str(production_line),
        product_cd=production_product_cd,
        priority_order=ps.order_no,
        production_lot_size_engine=production_lot_size,
        lot_numbers_ordered=lot_nums_for_upstream,
        existing_bp_by_lot=existing_bp_by_lot,
    )

    # ── aps_batch_plans 同期（cutting-locked ロットは identity 列を温存）──
    for lot_num in target_lot_nums:
        full_lot_qty = target_lot_qtys[lot_num]
        upstream = int(upstream_map.get(lot_num, 0) or 0)
        effective_qty = max(0, full_lot_qty - upstream)
        start_dt, end_dt = batch_dates_by_lot.get(lot_num, (None, None))
        is_locked = _norm_lot_number(lot_num) in cutting_locked_lot_norms
        existing = existing_bp_by_lot.get(lot_num)

        if existing is None:
            db.add(
                ApsBatchPlan(
                    aps_schedule_id=ps.id,
                    production_month=production_month,
                    production_line=str(production_line),
                    priority_order=ps.order_no,
                    product_cd=production_product_cd,
                    product_name=production_name,
                    planned_quantity=effective_qty,
                    upstream_defect_qty=upstream,
                    original_planned_quantity=full_lot_qty,
                    production_lot_size=production_lot_size,
                    lot_number=lot_num,
                    start_date=start_dt,
                    end_date=end_dt,
                )
            )
        elif is_locked:
            # 切断取り込み済み：管理コードに影響する identity 列（production_month / priority_order /
            # production_lot_size / lot_number / product_cd）は一切更新しない。
            existing.product_name = production_name
            existing.planned_quantity = effective_qty
            existing.upstream_defect_qty = upstream
            existing.original_planned_quantity = max(
                int(existing.original_planned_quantity or 0),
                full_lot_qty,
            )
            if start_dt is not None:
                existing.start_date = start_dt
            if end_dt is not None:
                existing.end_date = end_dt
        else:
            existing.production_month = production_month
            existing.production_line = str(production_line)
            existing.priority_order = ps.order_no
            existing.product_cd = production_product_cd
            existing.product_name = production_name
            existing.planned_quantity = effective_qty
            existing.upstream_defect_qty = upstream
            existing.original_planned_quantity = max(
                int(existing.original_planned_quantity or 0),
                full_lot_qty,
            )
            existing.production_lot_size = production_lot_size
            existing.lot_number = lot_num
            existing.start_date = start_dt
            existing.end_date = end_dt

    # 削減同期：計画一覧から消えた unlocked ロットは aps_batch_plans / instruction_plans から削除
    stale_lots_unlocked = [
        lot_str for lot_str in existing_bp_by_lot.keys()
        if _norm_lot_number(lot_str) not in target_lot_norms
        and _norm_lot_number(lot_str) not in cutting_locked_lot_norms
    ]
    stale_bid_ids = [
        int(existing_bp_by_lot[lot].id)
        for lot in stale_lots_unlocked
        if existing_bp_by_lot[lot].id is not None
    ]
    if stale_bid_ids:
        await db.execute(
            text("DELETE FROM instruction_plans WHERE aps_batch_plan_id IN :bids"),
            {"bids": tuple(stale_bid_ids)},
        )
        await db.execute(
            delete(ApsBatchPlan).where(ApsBatchPlan.id.in_(stale_bid_ids))
        )

    # 古い production_lot_size で残っている孤児 instruction_plans（aps_batch_plan_id 未設定）の掃除
    if stale_lots_unlocked:
        stale_orphan_mcs = []
        for lot in stale_lots_unlocked:
            bp = existing_bp_by_lot.get(str(lot))
            pls = int(getattr(bp, "production_lot_size", 0) or 0) if bp is not None else 0
            if pls <= 0:
                pls = production_lot_size
            stale_orphan_mcs.append(
                _instruction_management_code(
                    production_month=production_month,
                    production_line=str(production_line),
                    product_cd=production_product_cd,
                    priority_order=ps.order_no,
                    production_lot_size=pls,
                    lot_number=str(lot),
                )
            )
        stale_orphan_mcs = list(dict.fromkeys(stale_orphan_mcs))
        if stale_orphan_mcs:
            await db.execute(
                text(
                    """
                    DELETE FROM instruction_plans
                    WHERE production_month = :production_month
                      AND TRIM(COALESCE(production_line, '')) = TRIM(COALESCE(:production_line, ''))
                      AND priority_order = :priority_order
                      AND TRIM(COALESCE(product_cd, '')) = TRIM(COALESCE(:product_cd, ''))
                      AND aps_batch_plan_id IS NULL
                      AND management_code IN :mcs
                    """
                ),
                {
                    "production_month": production_month,
                    "production_line": str(production_line),
                    "priority_order": ps.order_no,
                    "product_cd": production_product_cd,
                    "mcs": tuple(stale_orphan_mcs),
                },
            )

    await db.flush()
    await _backfill_cutting_management_aps_batch_plan_id(db, ps.id)

    if not sync_instruction_plans:
        return

    # 同期後の aps_batch_plans を再取得（INSERT 行に id を採番させた状態で）
    bp_map_res = await db.execute(
        select(ApsBatchPlan).where(ApsBatchPlan.aps_schedule_id == ps.id)
    )
    bp_by_lot: dict[str, ApsBatchPlan] = {
        str(bp.lot_number): bp for bp in bp_map_res.scalars().all()
    }

    # 各ロットの management_code を事前算出（unified production_lot_size を採用）
    target_mcs = [
        _instruction_management_code(
            production_month=production_month,
            production_line=str(production_line),
            product_cd=production_product_cd,
            priority_order=ps.order_no,
            production_lot_size=production_lot_size,
            lot_number=lot_num,
        )
        for lot_num in target_lot_nums
    ]

    # 既存 instruction_plans を aps_batch_plan_id / management_code 経由で先読み
    bp_ids_for_lookup = [int(bp.id) for bp in bp_by_lot.values() if bp.id is not None]
    existing_ip_by_bid: dict[int, int] = {}
    if bp_ids_for_lookup:
        ip_res = await db.execute(
            text(
                "SELECT id, aps_batch_plan_id FROM instruction_plans "
                "WHERE aps_batch_plan_id IN :bids"
            ),
            {"bids": tuple(bp_ids_for_lookup)},
        )
        for r in ip_res.mappings().all():
            existing_ip_by_bid[int(r["aps_batch_plan_id"])] = int(r["id"])

    existing_ip_by_mc: dict[str, dict] = {}
    if target_mcs:
        ip_mc_res = await db.execute(
            text(
                "SELECT id, management_code, aps_batch_plan_id FROM instruction_plans "
                "WHERE management_code IN :mcs"
            ),
            {"mcs": tuple(target_mcs)},
        )
        for r in ip_mc_res.mappings().all():
            existing_ip_by_mc[str(r["management_code"])] = {
                "id": int(r["id"]),
                "aps_batch_plan_id": r.get("aps_batch_plan_id"),
            }

    _ip_update_sql = text(
        "UPDATE instruction_plans SET "
        "production_month=:production_month, production_line=:production_line, "
        "priority_order=:priority_order, product_cd=:product_cd, product_name=:product_name, "
        "planned_quantity=:instruction_planned_qty, actual_production_quantity=:batch_planned_qty, "
        "take_count=:take_count, "
        "cutting_length=:cutting_length, chamfering_length=:chamfering_length, "
        "developed_length=:developed_length, scrap_length=:scrap_length, "
        "material_name=:material_name, material_manufacturer=:material_manufacturer, "
        "standard_specification=:standard_specification, "
        "has_chamfering_process=:has_chamfering_process, has_sw_process=:has_sw_process, "
        "start_date=:start_date, end_date=:end_date, "
        "production_lot_size=:production_lot_size, lot_number=:lot_number, "
        "aps_batch_plan_id=:aps_batch_plan_id "
        "WHERE id=:ins_id"
    )

    _ip_insert_sql = text(
        """
        INSERT INTO instruction_plans (
          production_month, production_line, priority_order, product_cd, product_name,
          planned_quantity, start_date, end_date, production_lot_size, lot_number,
          is_cutting_instructed, has_chamfering_process, is_chamfering_instructed,
          has_sw_process, is_sw_instructed,
          actual_production_quantity, take_count,
          cutting_length, chamfering_length, developed_length, scrap_length,
          material_name, material_manufacturer, standard_specification,
          aps_batch_plan_id
        ) VALUES (
          :production_month, :production_line, :priority_order, :product_cd, :product_name,
          :instruction_planned_qty, :start_date, :end_date, :production_lot_size, :lot_number,
          0, :has_chamfering_process, 0,
          :has_sw_process, 0,
          :batch_planned_qty, :take_count,
          :cutting_length, :chamfering_length, :developed_length, :scrap_length,
          :material_name, :material_manufacturer, :standard_specification,
          :aps_batch_plan_id
        )
        """
    )

    # ── instruction_plans 同期：cutting-locked ロットは管理コード保持のため一切触らない ──
    for idx, lot_num in enumerate(target_lot_nums):
        if _norm_lot_number(lot_num) in cutting_locked_lot_norms:
            continue
        bp = bp_by_lot.get(lot_num)
        if bp is None or bp.id is None:
            continue

        full_lot_qty = target_lot_qtys[lot_num]
        start_dt, end_dt = batch_dates_by_lot.get(lot_num, (None, None))
        mc = target_mcs[idx]

        params = {
            "production_month": production_month,
            "production_line": str(production_line),
            "priority_order": ps.order_no,
            "product_cd": production_product_cd,
            "product_name": production_name,
            "instruction_planned_qty": full_plan_total,
            "batch_planned_qty": full_lot_qty,
            "take_count": take_count,
            "cutting_length": cutting_length,
            "chamfering_length": chamfering_length,
            "developed_length": developed_length,
            "scrap_length": scrap_length,
            "material_name": material_name,
            "material_manufacturer": material_manufacturer,
            "standard_specification": standard_specification,
            "has_chamfering_process": has_chamfering_process,
            "has_sw_process": has_sw_process,
            "start_date": start_dt,
            "end_date": end_dt,
            "production_lot_size": production_lot_size,
            "lot_number": lot_num,
            "aps_batch_plan_id": int(bp.id),
        }

        # aps_batch_plan_id 紐付けで既存行があれば UPDATE
        ip_id = existing_ip_by_bid.get(int(bp.id))
        if ip_id is not None:
            params["ins_id"] = ip_id
            await db.execute(_ip_update_sql, params)
            continue

        # 兜底：management_code 一致で既存（aps_batch_plan_id 未設定の旧データ）が見つかれば再利用
        legacy = existing_ip_by_mc.get(mc)
        if legacy is not None:
            params["ins_id"] = legacy["id"]
            await db.execute(_ip_update_sql, params)
            continue

        await db.execute(_ip_insert_sql, params)


def _schedule_to_out(ps: ProductionSchedule) -> ScheduleOut:
    return ScheduleOut(
        id=ps.id,
        line_id=ps.line_id,
        order_no=ps.order_no,
        order_id=ps.order_id,
        item_name=ps.item_name or "",
        product_cd=getattr(ps, "product_cd", None),
        material_shortage=bool(ps.material_shortage),
        lot_qty=int(ps.lot_qty or 0),
        planned_batch_count=int(getattr(ps, "planned_batch_count", 0) or 0),
        lot_size_snapshot=int(getattr(ps, "lot_size_snapshot", 0) or 0),
        planned_process_qty=int(ps.planned_process_qty or 0),
        prev_month_carryover=int(ps.prev_month_carryover or 0),
        due_date=ps.due_date,
        material_date=ps.material_date,
        forced_start_date=getattr(ps, "forced_start_date", None),
        setup_time=int(ps.setup_time or 0),
        efficiency=_dec(ps.efficiency),
        daily_capacity=int(ps.daily_capacity or 0),
        planned_output_qty=int(ps.planned_output_qty or 0),
        start_date=ps.start_date,
        end_date=ps.end_date,
        completion_rate=_dec(ps.completion_rate) if ps.completion_rate is not None else None,
        status=ps.status or "PLANNING",
    )

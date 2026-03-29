from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.cutting_planning.engine import (
    as_float,
    as_int,
    build_segments,
    enrich_planned_item_cutting_hints,
    fetch_cutting_machines,
    fetch_efficiency_map,
    fetch_eligible_machine_names_by_product,
    fetch_existing_fixed_items,
    fetch_instruction_plans,
    fetch_line_capacities,
    fetch_process_bom_cutting_forming_lt,
    fetch_run_items,
    fetch_time_slots,
    fixed_items_excluding_reschedule_targets,
    get_or_create_run,
    item_from_instruction_plan,
    month_end,
    parse_month,
    persist_partial_scheduled_items,
    PlannedItem,
    refresh_instruction_hints_for_items,
    replace_run_items,
    schedule_items,
    sync_cutting_plan_items_from_instructions,
)
from app.modules.cutting_planning.schemas import (
    CuttingPlannerAutoScheduleBody,
    CuttingPlannerLockBody,
    CuttingPlannerPublishBody,
    CuttingPlannerReorderBody,
    CuttingPlannerScheduleSelectedBody,
    CuttingPlannerSyncFromInstructionsBody,
)

router = APIRouter()


def parse_month_or_400(value: str) -> date:
    try:
        return parse_month(value)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def raise_cutting_planning_db_error(exc: Exception) -> None:
    msg = str(exc).lower()
    if "product_process_bom" in msg:
        raise HTTPException(
            status_code=503,
            detail="product_process_bom テーブルが存在しません。マイグレーション 025_product_process_bom.sql を確認してください。",
        ) from exc
    if "instruction_production_quantity" in msg and ("unknown column" in msg or "doesn't exist" in msg):
        raise HTTPException(
            status_code=503,
            detail="DB スキーマとバックエンドのバージョンが一致していません。最新の engine / マイグレーションを反映してください。",
        ) from exc
    if "cutting_plan_runs" in msg or "cutting_plan_items" in msg or "cutting_plan_slices" in msg:
        raise HTTPException(
            status_code=503,
            detail="切断計画作成テーブルが存在しません。マイグレーション 205_cutting_planning_tables.sql を実行してください。",
        ) from exc
    if "instruction_plans" in msg:
        raise HTTPException(
            status_code=503,
            detail="instruction_plans テーブルが存在しません。マイグレーション 052_cutting_instruction_plans.sql を確認してください。",
        ) from exc
    if "cutting_management" in msg:
        raise HTTPException(
            status_code=503,
            detail="cutting_management テーブルが存在しません。マイグレーション 053_cutting_management.sql を確認してください。",
        ) from exc
    raise exc


def serialize_item(item: Any) -> dict[str, Any]:
    return {
        "id": getattr(item, "id", None),
        "instruction_plan_id": item.instruction_plan_id,
        "product_cd": item.product_cd,
        "product_name": item.product_name,
        "material_name": item.material_name,
        "production_line": item.production_line,
        "planned_quantity": item.planned_quantity,
        "instruction_production_quantity": as_int(getattr(item, "instruction_production_quantity", 0)),
        "forming_start_date": item.forming_start_date.isoformat() if getattr(item, "forming_start_date", None) else None,
        "forming_end_date": item.forming_end_date.isoformat() if getattr(item, "forming_end_date", None) else None,
        "recommended_cutting_start_date": item.recommended_cutting_start_date.isoformat()
        if getattr(item, "recommended_cutting_start_date", None)
        else None,
        "production_lot_size": item.production_lot_size,
        "lot_number": item.lot_number,
        "take_count": item.take_count,
        "cutting_length": item.cutting_length,
        "assigned_machine_id": item.assigned_machine_id,
        "assigned_machine": item.assigned_machine,
        "sequence_no": item.sequence_no,
        "planned_day": item.planned_day.isoformat() if item.planned_day else None,
        "planned_start": item.planned_start.isoformat() if item.planned_start else None,
        "planned_end": item.planned_end.isoformat() if item.planned_end else None,
        "estimated_minutes": round(as_float(item.estimated_minutes), 2),
        "efficiency_rate": item.efficiency_rate,
        "setup_time_min": item.setup_time_min,
        "is_locked": bool(item.is_locked),
        "publish_status": item.publish_status,
        "published_cutting_id": item.published_cutting_id,
        "actual_quantity": item.actual_quantity,
        "completion_status": item.completion_status,
        "source_management_code": item.source_management_code,
    }


async def get_run_meta(db: AsyncSession, production_month: date) -> dict[str, Any] | None:
    res = await db.execute(
        text(
            """
            SELECT id, production_month, status, generated_at, published_at
            FROM cutting_plan_runs
            WHERE production_month = :production_month
            """
        ),
        {"production_month": production_month},
    )
    row = res.mappings().first()
    return dict(row) if row else None


async def attach_progress(db: AsyncSession, items: list[Any]) -> None:
    published_ids = [item.published_cutting_id for item in items if getattr(item, "published_cutting_id", None)]
    mgmt_codes = [item.source_management_code for item in items if getattr(item, "source_management_code", None)]
    if not published_ids and not mgmt_codes:
        return
    conditions = []
    params: dict[str, Any] = {}
    if published_ids:
        placeholders = ", ".join(f":cid_{idx}" for idx, _ in enumerate(published_ids))
        params.update({f"cid_{idx}": value for idx, value in enumerate(published_ids)})
        conditions.append(f"id IN ({placeholders})")
    if mgmt_codes:
        placeholders = ", ".join(f":mc_{idx}" for idx, _ in enumerate(mgmt_codes))
        params.update({f"mc_{idx}": value for idx, value in enumerate(mgmt_codes)})
        conditions.append(f"management_code IN ({placeholders})")
    sql = text(
        f"""
        SELECT id, management_code, actual_production_quantity, production_completed_check
        FROM cutting_management
        WHERE {' OR '.join(conditions)}
        """
    )
    res = await db.execute(sql, params)
    by_id: dict[int, dict[str, Any]] = {}
    by_code: dict[str, dict[str, Any]] = {}
    for row in res.mappings().all():
        data = dict(row)
        by_id[as_int(data["id"])] = data
        if data.get("management_code"):
            by_code[str(data["management_code"])] = data
    for item in items:
        target = None
        if getattr(item, "published_cutting_id", None) is not None:
            target = by_id.get(as_int(item.published_cutting_id))
        if target is None and getattr(item, "source_management_code", None):
            target = by_code.get(str(item.source_management_code))
        if target is None:
            continue
        item.published_cutting_id = as_int(target["id"])
        item.actual_quantity = as_int(target.get("actual_production_quantity"))
        item.publish_status = "PUBLISHED"
        if as_int(target.get("production_completed_check")) == 1:
            item.completion_status = "COMPLETED"
        elif item.actual_quantity > 0:
            item.completion_status = "IN_PROGRESS"
        else:
            item.completion_status = "PUBLISHED"


async def load_list_data(
    db: AsyncSession,
    production_month: date,
    machine_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
) -> dict[str, Any]:
    run_meta = await get_run_meta(db, production_month)
    machines = await fetch_cutting_machines(db)
    if run_meta:
        items = await fetch_run_items(db, as_int(run_meta["id"]))
        await attach_progress(db, items)
    else:
        source_rows = await fetch_instruction_plans(db, production_month)
        items = [item_from_instruction_plan(row) for row in source_rows]
        bom_preview = await fetch_process_bom_cutting_forming_lt(db, [it.product_cd for it in items])
        for it in items:
            enrich_planned_item_cutting_hints(it, bom_preview)
        machine_names = [m.machine_name for m in machines]
        eff_map = await fetch_efficiency_map(db, [item.product_cd for item in items], machine_names)
        for item in items:
            best_rate = 0.0
            best_setup = 0
            for machine in machines:
                rate, setup = eff_map.get((item.product_cd, machine.machine_name), (0.0, 0))
                if rate > best_rate:
                    best_rate, best_setup = rate, setup
                    item.assigned_machine_id = machine.id
                    item.assigned_machine = machine.machine_name
            item.efficiency_rate = best_rate or None
            item.setup_time_min = best_setup or None
            rate = best_rate or 60.0
            item.estimated_minutes = round((item.planned_quantity / max(rate, 1.0)) * 60 + (best_setup or 0), 2)
            item.publish_status = "PLANNED"
            item.completion_status = "PLANNED"
    if machine_id is not None:
        items = [item for item in items if item.assigned_machine_id == machine_id]
    if status:
        normalized = status.strip().upper()
        items = [item for item in items if (item.completion_status or item.publish_status).upper() == normalized or item.publish_status.upper() == normalized]
    if keyword:
        q = keyword.strip().lower()
        items = [
            item for item in items
            if q in (item.product_cd or "").lower()
            or q in (item.product_name or "").lower()
            or q in (item.material_name or "").lower()
            or q in (item.assigned_machine or "").lower()
        ]
    serialized = [serialize_item(item) for item in items]
    total_planned = sum(as_int(item["planned_quantity"]) for item in serialized)
    total_instruction_prod = sum(as_int(item.get("instruction_production_quantity", 0)) for item in serialized)
    total_actual = sum(as_int(item["actual_quantity"]) for item in serialized)
    summary = {
        "total_items": len(serialized),
        "planned_items": sum(1 for item in serialized if item["publish_status"] == "PLANNED"),
        "published_items": sum(1 for item in serialized if item["publish_status"] == "PUBLISHED"),
        "in_progress_items": sum(1 for item in serialized if item["completion_status"] == "IN_PROGRESS"),
        "completed_items": sum(1 for item in serialized if item["completion_status"] == "COMPLETED"),
        "total_planned_quantity": total_planned,
        "total_instruction_production_quantity": total_instruction_prod,
        "total_actual_quantity": total_actual,
    }
    return {
        "run_id": as_int(run_meta["id"]) if run_meta else None,
        "generated_at": run_meta["generated_at"].isoformat() if run_meta and run_meta.get("generated_at") else None,
        "published_at": run_meta["published_at"].isoformat() if run_meta and run_meta.get("published_at") else None,
        "machines": [
            {
                "id": machine.id,
                "machine_cd": machine.machine_cd,
                "machine_name": machine.machine_name,
                "default_work_hours": machine.default_work_hours,
            }
            for machine in machines
        ],
        "items": serialized,
        "summary": summary,
    }


@router.get("/machines")
async def get_cutting_planning_machines(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        machines = await fetch_cutting_machines(db)
        return [
            {
                "id": machine.id,
                "machine_cd": machine.machine_cd,
                "machine_name": machine.machine_name,
                "default_work_hours": machine.default_work_hours,
            }
            for machine in machines
        ]
    except (OperationalError, ProgrammingError) as exc:
        raise_cutting_planning_db_error(exc)


@router.get("/list")
async def get_cutting_planning_list(
    productionMonth: str = Query(..., description="生産月 YYYY-MM"),
    machineId: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    production_month = parse_month_or_400(productionMonth)
    try:
        return await load_list_data(db, production_month, machineId, status, keyword)
    except (OperationalError, ProgrammingError) as exc:
        raise_cutting_planning_db_error(exc)


@router.post("/sync-from-instructions")
async def sync_cutting_plan_from_instructions(
    body: CuttingPlannerSyncFromInstructionsBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """instruction_plans を cutting_plan_items に取り込み（INSERT/UPDATE）。排産時刻は上書きしない。"""
    production_month = parse_month_or_400(body.production_month)
    try:
        run_id = await get_or_create_run(db, production_month)
        await sync_cutting_plan_items_from_instructions(db, run_id, production_month)
        await db.commit()
        return await load_list_data(db, production_month)
    except HTTPException:
        await db.rollback()
        raise
    except (OperationalError, ProgrammingError) as exc:
        await db.rollback()
        raise_cutting_planning_db_error(exc)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/schedule-selected")
async def schedule_selected_cutting_plans(
    body: CuttingPlannerScheduleSelectedBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """選択した cutting_plan_items のみ切断スケジュールを計算し、該当行のみ UPDATE（全削除しない）。"""
    production_month = parse_month_or_400(body.production_month)
    try:
        run_meta = await get_run_meta(db, production_month)
        if not run_meta or as_int(run_meta["id"]) != body.run_id:
            raise HTTPException(status_code=404, detail="切断計画Runが見つかりません")

        items = await fetch_run_items(db, body.run_id)
        item_id_set = {as_int(x) for x in body.item_ids if as_int(x) > 0}
        to_schedule = [
            it
            for it in items
            if it.id is not None
            and as_int(it.id) in item_id_set
            and not it.is_locked
            and not it.published_cutting_id
        ]
        if not to_schedule:
            raise HTTPException(
                status_code=400,
                detail="排産対象がありません（ロック・下発済みは選択できません）",
            )

        machines = await fetch_cutting_machines(db, body.machine_ids)
        if not machines:
            raise HTTPException(status_code=400, detail="切断機が見つかりません")

        ts_ids = {as_int(it.id) for it in to_schedule if it.id is not None}
        fixed_items = fixed_items_excluding_reschedule_targets(items, ts_ids)

        for it in to_schedule:
            it.planned_day = None
            it.planned_start = None
            it.planned_end = None
            it.slices = []
            it.assigned_machine_id = None
            it.assigned_machine = None
            it.sequence_no = 0

        bom_map = await fetch_process_bom_cutting_forming_lt(db, [it.product_cd for it in to_schedule])
        await refresh_instruction_hints_for_items(db, to_schedule, bom_map)
        eligible_by_product = await fetch_eligible_machine_names_by_product(
            db, [it.product_cd for it in to_schedule],
        )

        start_date = body.start_date or production_month
        end_date = max(month_end(production_month), start_date + timedelta(days=body.horizon_days - 1))
        slot_map = await fetch_time_slots(db, [m.id for m in machines], start_date, end_date)
        capacity_map = await fetch_line_capacities(db, [m.id for m in machines], start_date, end_date)
        segments = build_segments(machines, slot_map, start_date, end_date, capacity_map)
        efficiency_map = await fetch_efficiency_map(
            db,
            [it.product_cd for it in to_schedule] + [it.product_cd for it in fixed_items],
            [m.machine_name for m in machines],
        )
        scheduled = schedule_items(
            to_schedule, machines, segments, fixed_items, efficiency_map, eligible_by_product,
        )
        await persist_partial_scheduled_items(db, body.run_id, scheduled)
        await db.commit()
        return await load_list_data(db, production_month)
    except HTTPException:
        await db.rollback()
        raise
    except (OperationalError, ProgrammingError) as exc:
        await db.rollback()
        raise_cutting_planning_db_error(exc)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/auto-schedule")
async def auto_schedule_cutting_plans(
    body: CuttingPlannerAutoScheduleBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    production_month = parse_month_or_400(body.production_month)
    try:
        run_id = await get_or_create_run(db, production_month)
        machines = await fetch_cutting_machines(db, body.machine_ids)
        if not machines:
            raise HTTPException(status_code=400, detail="切断機が見つかりません")

        start_date = body.start_date or production_month
        end_date = max(month_end(production_month), start_date + timedelta(days=body.horizon_days - 1))
        fixed_items = await fetch_existing_fixed_items(db, run_id) if body.preserve_published else []
        fixed_instruction_ids = {item.instruction_plan_id for item in fixed_items if item.instruction_plan_id is not None}
        source_rows = await fetch_instruction_plans(db, production_month)
        active_rows = [r for r in source_rows if r.get("id") not in fixed_instruction_ids]
        bom_map = await fetch_process_bom_cutting_forming_lt(db, [str(r.get("product_cd") or "") for r in active_rows])
        eligible_by_product = await fetch_eligible_machine_names_by_product(
            db, [str(r.get("product_cd") or "") for r in active_rows],
        )
        source_items: list[PlannedItem] = []
        for row in active_rows:
            item = item_from_instruction_plan(row)
            enrich_planned_item_cutting_hints(item, bom_map)
            source_items.append(item)
        slot_map = await fetch_time_slots(db, [machine.id for machine in machines], start_date, end_date)
        capacity_map = await fetch_line_capacities(db, [m.id for m in machines], start_date, end_date)
        segments = build_segments(machines, slot_map, start_date, end_date, capacity_map)
        efficiency_map = await fetch_efficiency_map(
            db,
            [item.product_cd for item in source_items] + [item.product_cd for item in fixed_items],
            [machine.machine_name for machine in machines],
        )
        planned_items = schedule_items(
            source_items, machines, segments, fixed_items, efficiency_map, eligible_by_product,
        )
        await replace_run_items(db, run_id, planned_items, production_month)
        await db.commit()
        return await load_list_data(db, production_month)
    except HTTPException:
        await db.rollback()
        raise
    except (OperationalError, ProgrammingError) as exc:
        await db.rollback()
        raise_cutting_planning_db_error(exc)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/lock")
async def lock_cutting_plan_item(
    body: CuttingPlannerLockBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        run_res = await db.execute(
            text("SELECT production_month FROM cutting_plan_runs WHERE id = :run_id"),
            {"run_id": body.run_id},
        )
        production_month = run_res.scalar_one_or_none()
        if production_month is None:
            raise HTTPException(status_code=404, detail="切断計画が見つかりません")
        await db.execute(
            text(
                """
                UPDATE cutting_plan_items
                SET is_locked = :is_locked, updated_at = NOW()
                WHERE run_id = :run_id AND id = :item_id
                """
            ),
            {
                "is_locked": 1 if body.is_locked else 0,
                "run_id": body.run_id,
                "item_id": body.item_id,
            },
        )
        await db.commit()
        return await load_list_data(db, production_month)
    except (OperationalError, ProgrammingError) as exc:
        await db.rollback()
        raise_cutting_planning_db_error(exc)


@router.post("/reorder")
async def reorder_cutting_plans(
    body: CuttingPlannerReorderBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        run_res = await db.execute(
        text("SELECT production_month FROM cutting_plan_runs WHERE id = :run_id"),
        {"run_id": body.run_id},
        )
        production_month = run_res.scalar_one_or_none()
        if production_month is None:
            raise HTTPException(status_code=404, detail="切断計画が見つかりません")

        all_items = await fetch_run_items(db, body.run_id)
        machines = await fetch_cutting_machines(db, [body.machine_id])
        if not machines:
            raise HTTPException(status_code=404, detail="切断機が見つかりません")
        machine = machines[0]

        fixed_items = [item for item in all_items if item.assigned_machine_id == body.machine_id and (item.is_locked or item.published_cutting_id is not None)]
        target_items = [item for item in all_items if item.assigned_machine_id == body.machine_id and not item.is_locked and item.published_cutting_id is None]
        other_items = [item for item in all_items if item.assigned_machine_id != body.machine_id]
        ordered_lookup = {item_id: idx for idx, item_id in enumerate(body.ordered_item_ids)}
        target_items.sort(key=lambda x: ordered_lookup.get(getattr(x, "id", 0), 999999))
        for target in target_items:
            target.assigned_machine_id = None
            target.assigned_machine = None
            target.sequence_no = 0
            target.planned_day = None
            target.planned_start = None
            target.planned_end = None
            target.slices = []
            target.publish_status = "PLANNED"
            target.completion_status = "PLANNED"
        start_date = production_month
        end_date = max(month_end(production_month), start_date + timedelta(days=body.horizon_days - 1))
        slot_map = await fetch_time_slots(db, [machine.id], start_date, end_date)
        capacity_map = await fetch_line_capacities(db, [machine.id], start_date, end_date)
        segments = build_segments([machine], slot_map, start_date, end_date, capacity_map)
        efficiency_map = await fetch_efficiency_map(db, [item.product_cd for item in target_items], [machine.machine_name])
        rebuilt_machine_items = schedule_items(target_items, [machine], segments, fixed_items, efficiency_map)
        combined = other_items + rebuilt_machine_items
        await replace_run_items(db, body.run_id, combined, production_month)
        await db.commit()
        return await load_list_data(db, production_month)
    except (OperationalError, ProgrammingError) as exc:
        await db.rollback()
        raise_cutting_planning_db_error(exc)


async def fetch_instruction_plan_detail(db: AsyncSession, instruction_plan_id: int | None, management_code: str | None) -> dict[str, Any] | None:
    if instruction_plan_id is not None:
        res = await db.execute(
            text("SELECT * FROM instruction_plans WHERE id = :plan_id"),
            {"plan_id": instruction_plan_id},
        )
        row = res.mappings().first()
        if row:
            return dict(row)
    if management_code:
        res = await db.execute(
            text("SELECT * FROM instruction_plans WHERE management_code = :management_code ORDER BY id DESC LIMIT 1"),
            {"management_code": management_code},
        )
        row = res.mappings().first()
        if row:
            return dict(row)
    return None


@router.post("/publish")
async def publish_cutting_plans(
    body: CuttingPlannerPublishBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    run_res = await db.execute(
        text("SELECT production_month FROM cutting_plan_runs WHERE id = :run_id"),
        {"run_id": body.run_id},
    )
    production_month = run_res.scalar_one_or_none()
    if production_month is None:
        raise HTTPException(status_code=404, detail="切断計画が見つかりません")

    items = await fetch_run_items(db, body.run_id)
    if body.item_ids:
        target_ids = set(body.item_ids)
        selected_items = [item for item in items if getattr(item, "id", None) in target_ids]
    else:
        selected_items = items

    published_count = 0
    for item in selected_items:
        if item.published_cutting_id is not None:
            continue
        if not item.assigned_machine or item.planned_day is None:
            continue

        existing = None
        if item.source_management_code:
            existing_res = await db.execute(
                text("SELECT id FROM cutting_management WHERE management_code = :management_code ORDER BY id DESC LIMIT 1"),
                {"management_code": item.source_management_code},
            )
            existing = existing_res.scalar_one_or_none()
        if existing is not None and not body.overwrite_existing:
            await db.execute(
                text(
                    """
                    UPDATE cutting_plan_items
                    SET published_cutting_id = :cutting_id, publish_status = 'PUBLISHED', completion_status = 'PUBLISHED'
                    WHERE run_id = :run_id AND source_management_code = :management_code
                    """
                ),
                {"cutting_id": existing, "run_id": body.run_id, "management_code": item.source_management_code},
            )
            published_count += 1
            continue

        plan_detail = await fetch_instruction_plan_detail(db, item.instruction_plan_id, item.source_management_code)
        order_res = await db.execute(
            text(
                """
                SELECT COALESCE(MAX(production_sequence), 0) + 1
                FROM cutting_management
                WHERE cutting_machine = :cutting_machine AND production_day = :production_day
                """
            ),
            {"cutting_machine": item.assigned_machine, "production_day": item.planned_day},
        )
        production_sequence = as_int(order_res.scalar_one(), 1)

        params = {
            "production_month": production_month,
            "production_day": item.planned_day,
            "production_line": (plan_detail or {}).get("production_line") or item.production_line or item.assigned_machine,
            "cutting_machine": item.assigned_machine,
            "production_sequence": production_sequence,
            "priority_order": (plan_detail or {}).get("priority_order"),
            "product_cd": item.product_cd,
            "product_name": item.product_name,
            "planned_quantity": item.planned_quantity,
            "start_date": item.planned_start,
            "end_date": item.planned_end,
            "production_lot_size": item.production_lot_size,
            "lot_number": item.lot_number,
            "is_cutting_instructed": 1,
            "has_chamfering_process": 1 if (plan_detail or {}).get("has_chamfering_process") else 0,
            "is_chamfering_instructed": 1 if (plan_detail or {}).get("is_chamfering_instructed") else 0,
            "has_sw_process": 1 if (plan_detail or {}).get("has_sw_process") else 0,
            "is_sw_instructed": 1 if (plan_detail or {}).get("is_sw_instructed") else 0,
            "management_code": item.source_management_code,
            "actual_production_quantity": 0,
            "take_count": item.take_count,
            "cutting_length": item.cutting_length,
            "chamfering_length": as_float((plan_detail or {}).get("chamfering_length")) if (plan_detail or {}).get("chamfering_length") is not None else None,
            "developed_length": as_float((plan_detail or {}).get("developed_length")) if (plan_detail or {}).get("developed_length") is not None else None,
            "scrap_length": as_float((plan_detail or {}).get("scrap_length")) if (plan_detail or {}).get("scrap_length") is not None else None,
            "material_name": item.material_name,
            "material_manufacturer": (plan_detail or {}).get("material_manufacturer"),
            "standard_specification": (plan_detail or {}).get("standard_specification"),
            "use_material_stock_sub": 1 if (plan_detail or {}).get("use_material_stock_sub") else 0,
            "usage_count": as_float((plan_detail or {}).get("usage_count"), 1.0),
        }
        if existing is None:
            await db.execute(
                text(
                    """
                    INSERT INTO cutting_management (
                        production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
                        product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
                        is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
                        management_code, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
                        developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
                        production_completed_check, use_material_stock_sub, usage_count
                    ) VALUES (
                        :production_month, :production_day, :production_line, :cutting_machine, :production_sequence, :priority_order,
                        :product_cd, :product_name, :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
                        :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
                        :management_code, :actual_production_quantity, 0, :take_count, :cutting_length, :chamfering_length,
                        :developed_length, :scrap_length, :material_name, :material_manufacturer, :standard_specification,
                        0, :use_material_stock_sub, :usage_count
                    )
                    """
                ),
                params,
            )
            last_id_res = await db.execute(text("SELECT LAST_INSERT_ID()"))
            cutting_id = as_int(last_id_res.scalar_one())
        else:
            cutting_id = as_int(existing)
            if body.overwrite_existing:
                params["cutting_id"] = cutting_id
                await db.execute(
                    text(
                        """
                        UPDATE cutting_management
                        SET production_day = :production_day,
                            cutting_machine = :cutting_machine,
                            production_sequence = :production_sequence,
                            planned_quantity = :planned_quantity,
                            start_date = :start_date,
                            end_date = :end_date
                        WHERE id = :cutting_id
                        """
                    ),
                    params,
                )

        await db.execute(
            text(
                """
                UPDATE cutting_plan_items
                SET published_cutting_id = :cutting_id,
                    publish_status = 'PUBLISHED',
                    completion_status = 'PUBLISHED'
                WHERE run_id = :run_id
                  AND product_cd = :product_cd
                  AND lot_number <=> :lot_number
                  AND source_management_code <=> :management_code
                """
            ),
            {
                "cutting_id": cutting_id,
                "run_id": body.run_id,
                "product_cd": item.product_cd,
                "lot_number": item.lot_number,
                "management_code": item.source_management_code,
            },
        )
        published_count += 1

    await db.execute(
        text(
            """
            UPDATE cutting_plan_runs
            SET status = 'PUBLISHED', published_at = NOW(), updated_at = NOW()
            WHERE id = :run_id
            """
        ),
        {"run_id": body.run_id},
    )
    await db.commit()
    return {
        "success": True,
        "published_count": published_count,
        "data": await load_list_data(db, production_month),
    }


@router.get("/gantt")
async def get_cutting_planning_gantt(
    productionMonth: str = Query(...),
    runId: Optional[int] = Query(None),
    startDate: Optional[date] = Query(None),
    endDate: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    production_month = parse_month_or_400(productionMonth)
    run_meta = await get_run_meta(db, production_month)
    if runId is None:
        runId = as_int(run_meta["id"]) if run_meta else None
    if runId is None:
        return {"dates": [], "blocks": []}
    items = await fetch_run_items(db, runId)
    await attach_progress(db, items)
    if not items:
        return {"dates": [], "blocks": []}
    if startDate is None:
        startDate = min((item.planned_day for item in items if item.planned_day), default=production_month)
    if endDate is None:
        endDate = max((item.planned_end.date() for item in items if item.planned_end), default=month_end(production_month))
    dates: list[str] = []
    cursor = startDate
    while cursor <= endDate:
        dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    machine_blocks: dict[tuple[int, str], dict[str, Any]] = {}
    for item in items:
        if item.assigned_machine_id is None or not item.assigned_machine:
            continue
        key = (item.assigned_machine_id, item.assigned_machine)
        block = machine_blocks.setdefault(
            key,
            {
                "machine_id": item.assigned_machine_id,
                "machine_name": item.assigned_machine,
                "rows": [],
                "daily_totals": {d: 0 for d in dates},
            },
        )
        daily: dict[str, int] = {d: 0 for d in dates}
        for sl in item.slices or []:
            d = sl.work_date.isoformat()
            if d in daily:
                daily[d] += as_int(sl.planned_qty)
                block["daily_totals"][d] += as_int(sl.planned_qty)
        block["rows"].append(
            {
                "item_id": getattr(item, "id", 0),
                "sequence_no": item.sequence_no,
                "product_name": item.product_name,
                "product_cd": item.product_cd,
                "planned_quantity": item.planned_quantity,
                "daily": daily,
            }
        )
    blocks = sorted(machine_blocks.values(), key=lambda x: (x["machine_name"], x["machine_id"]))
    return {"dates": dates, "blocks": blocks}


@router.get("/hourly-gantt")
async def get_cutting_planning_hourly_gantt(
    productionMonth: str = Query(...),
    runId: Optional[int] = Query(None),
    machineId: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    production_month = parse_month_or_400(productionMonth)
    run_meta = await get_run_meta(db, production_month)
    if runId is None:
        runId = as_int(run_meta["id"]) if run_meta else None
    if runId is None:
        return {"columns": [], "rows": []}
    items = await fetch_run_items(db, runId)
    if machineId is not None:
        items = [item for item in items if item.assigned_machine_id == machineId]
    column_keys: dict[str, dict[str, str]] = {}
    rows: list[dict[str, Any]] = []
    for item in items:
        slice_qty: dict[str, int] = {}
        for sl in item.slices or []:
            key = f"{sl.work_date.isoformat()}_{sl.period_start.strftime('%H:%M:%S')}_{sl.period_end.strftime('%H:%M:%S')}"
            column_keys.setdefault(
                key,
                {
                    "key": key,
                    "work_date": sl.work_date.isoformat(),
                    "period_start": sl.period_start.strftime("%H:%M:%S"),
                    "period_end": sl.period_end.strftime("%H:%M:%S"),
                },
            )
            slice_qty[key] = as_int(sl.planned_qty)
        rows.append(
            {
                "item_id": getattr(item, "id", 0),
                "sequence_no": item.sequence_no,
                "product_name": item.product_name,
                "product_cd": item.product_cd,
                "planned_quantity": item.planned_quantity,
                "slice_qty": slice_qty,
            }
        )
    columns = sorted(column_keys.values(), key=lambda x: (x["work_date"], x["period_start"], x["period_end"]))
    return {"columns": columns, "rows": rows}


@router.get("/progress")
async def get_cutting_planning_progress(
    productionMonth: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    production_month = parse_month_or_400(productionMonth)
    data = await load_list_data(db, production_month)
    return {
        "production_month": production_month.isoformat()[:7],
        "run_id": data["run_id"],
        **data["summary"],
    }


@router.get("/report")
async def get_cutting_planning_report(
    productionMonth: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    production_month = parse_month_or_400(productionMonth)
    data = await load_list_data(db, production_month)
    items = sorted(
        data["items"],
        key=lambda x: (
            x.get("assigned_machine") or "",
            x.get("planned_day") or "",
            x.get("sequence_no") or 0,
            x.get("product_cd") or "",
        ),
    )
    return {
        "production_month": production_month.isoformat()[:7],
        "generated_at": data["generated_at"],
        "items": [
            {
                "machine_name": item.get("assigned_machine"),
                "planned_day": item.get("planned_day"),
                "sequence_no": item.get("sequence_no") or 0,
                "product_cd": item.get("product_cd") or "",
                "product_name": item.get("product_name") or "",
                "material_name": item.get("material_name"),
                "planned_quantity": item.get("planned_quantity") or 0,
                "instruction_production_quantity": item.get("instruction_production_quantity") or 0,
                "estimated_minutes": item.get("estimated_minutes") or 0,
                "publish_status": item.get("publish_status") or "PLANNED",
                "completion_status": item.get("completion_status") or "PLANNED",
            }
            for item in items
        ],
    }

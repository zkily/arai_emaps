"""成型工程计划试算 — 数据加载与模拟编排。"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from sqlalchemy import and_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.database.api import (
    PROCESS_CD_TO_PREFIX,
    _get_route_sequence,
    _num,
    _row_to_dict,
    _subtract_business_days,
)
from app.modules.database.forming_plan_cascade import (
    PROCESS_KEY_MACHINE_FIELD,
    PROCESS_KEY_TO_PLAN_FIELD,
    SIMULATION_PROCESS_KEYS,
    apply_molding_cascade_to_row,
    molding_derived_plan_for_process,
    pick_product_machine,
)
from app.modules.database.inventory_simulator import simulate_product_inventory_series
from app.modules.database.models import ProductionSummary
from app.modules.database.order_forecast_service import build_order_forecast
from app.modules.database.order_process_totals_service import (
    build_order_matrix_rows,
    compute_order_process_totals_from_monthly,
    load_order_daily_by_product_date,
    load_product_process_cds,
)
from app.modules.master.models import ProcessRouteStep, Product

MAX_PERIOD_DAYS = 93

PROCESS_LT_MAP: dict[str, str] = {
    "cutting": "cuting_process_lt",
    "chamfering": "chamfering_process_lt",
    "molding": "forming_process_lt",
    "plating": "plating_process_lt",
    "welding": "welding_process_lt",
    "inspection": "inspection_process_lt",
}


def parse_iso_date(value: str) -> date:
    s = (value or "").strip()[:10]
    y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
    return date(y, m, d)


def daterange_inclusive(ps: date, pe: date) -> list[str]:
    out: list[str] = []
    cur = ps
    while cur <= pe:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def validate_period(ps: date, pe: date) -> None:
    if ps > pe:
        raise ValueError("startDate は endDate 以前にしてください")
    if (pe - ps).days + 1 > MAX_PERIOD_DAYS:
        raise ValueError(f"期間は最大 {MAX_PERIOD_DAYS} 日までです")


async def _load_route_process_cds(db: AsyncSession) -> dict[str, set[str]]:
    q = select(ProcessRouteStep.route_cd, ProcessRouteStep.process_cd)
    res = await db.execute(q)
    out: dict[str, set[str]] = {}
    for route_cd, process_cd in res.all():
        if not route_cd:
            continue
        out.setdefault(str(route_cd), set()).add(str(process_cd))
    return out


async def _load_sw_machine_products(db: AsyncSession) -> set[str]:
    q = text(
        """
        SELECT DISTINCT product_cd FROM product_machine_config
        WHERE sw_machine IS NOT NULL AND TRIM(COALESCE(sw_machine, '')) <> ''
        """
    )
    res = await db.execute(q)
    return {str(r[0]).strip() for r in res.all() if r[0]}


async def _load_bom_lt(db: AsyncSession) -> dict[str, dict[str, int]]:
    q = text("SELECT product_cd, cuting_process_lt, chamfering_process_lt, forming_process_lt, "
             "plating_process_lt, welding_process_lt, inspection_process_lt FROM product_process_bom")
    res = await db.execute(q)
    out: dict[str, dict[str, int]] = {}
    for row in res.mappings().all():
        cd = str(row["product_cd"] or "").strip()
        if not cd:
            continue
        lt: dict[str, int] = {}
        for pk, col in PROCESS_LT_MAP.items():
            v = row.get(col)
            if v is not None:
                try:
                    lt[pk] = int(v)
                except (TypeError, ValueError):
                    pass
        out[cd] = lt
    return out


async def _load_molding_production_orders(
    db: AsyncSession,
    ps: date,
    pe: date,
    product_cds: list[str] | None = None,
) -> dict[str, dict[str, int]]:
    """APS 成型（KT04）の生産順 order_no。product_cd → { 成型機名 → 最小 order_no }。"""
    sql = """
        SELECT sch.product_cd AS product_cd,
               TRIM(m.machine_name) AS machine_name,
               MIN(sch.order_no) AS molding_order
        FROM schedule_details sd
        INNER JOIN production_schedules sch ON sch.id = sd.schedule_id
        INNER JOIN machines m ON m.id = sch.line_id
        INNER JOIN processes pr ON m.machine_type IS NOT NULL
          AND (TRIM(m.machine_type) = pr.process_name OR TRIM(m.machine_type) = pr.process_cd)
        WHERE pr.process_cd = 'KT04'
          AND sch.product_cd IS NOT NULL AND TRIM(sch.product_cd) <> ''
          AND sch.order_no IS NOT NULL
          AND sd.schedule_date >= :start_date AND sd.schedule_date <= :end_date
          AND COALESCE(sd.planned_qty, 0) > 0
    """
    params: dict[str, Any] = {"start_date": ps, "end_date": pe}
    if product_cds:
        placeholders = ", ".join(f":pc{i}" for i in range(len(product_cds)))
        sql += f" AND sch.product_cd IN ({placeholders})"
        for i, cd in enumerate(product_cds):
            params[f"pc{i}"] = cd
    sql += " GROUP BY sch.product_cd, TRIM(m.machine_name)"
    res = await db.execute(text(sql), params)
    out: dict[str, dict[str, int]] = {}
    for row in res.mappings().all():
        cd = str(row.get("product_cd") or "").strip()
        mn = str(row.get("machine_name") or "").strip()
        try:
            order = int(row.get("molding_order"))
        except (TypeError, ValueError):
            continue
        if not cd or not mn:
            continue
        out.setdefault(cd, {})[mn] = order
    return out


def _pick_molding_order(
    product_cd: str,
    molding_machine: str,
    orders_by_product: dict[str, dict[str, int]],
) -> int | None:
    per_machine = orders_by_product.get(product_cd) or {}
    if molding_machine and molding_machine in per_machine:
        return per_machine[molding_machine]
    if per_machine:
        return min(per_machine.values())
    return None


async def _load_summary_rows(
    db: AsyncSession,
    ps: date,
    pe: date,
    product_cds: list[str] | None,
) -> list[dict[str, Any]]:
    q = select(ProductionSummary).where(
        and_(ProductionSummary.date >= ps, ProductionSummary.date <= pe)
    )
    if product_cds:
        q = q.where(ProductionSummary.product_cd.in_(product_cds))
    q = q.order_by(ProductionSummary.product_cd, ProductionSummary.date)
    res = await db.execute(q)
    rows = [_row_to_dict(r) for r in res.scalars().all()]

    inactive: set[str] = set()
    cds = {(r.get("product_cd") or "").strip() for r in rows if r.get("product_cd")}
    if cds:
        pq = select(Product.product_cd, Product.status).where(Product.product_cd.in_(list(cds)))
        pr = await db.execute(pq)
        for pc, st in pr.all():
            if st and str(st).strip().lower() == "inactive":
                inactive.add(str(pc))

    return [r for r in rows if (r.get("product_cd") or "").strip() not in inactive]


def _resolve_run_date(
    target_date: str,
    process_key: str,
    run_calendar: dict[str, set[str]],
    strategy: str = "forward",
) -> str:
    """未勾选运行日时向前找最近运行日。"""
    dates_set = run_calendar.get(process_key, set())
    if not dates_set or target_date in dates_set:
        return target_date
    if strategy != "forward":
        return target_date
    try:
        d = parse_iso_date(target_date)
    except (ValueError, TypeError):
        return target_date
    for _ in range(30):
        d -= timedelta(days=1)
        ds = d.isoformat()
        if ds in dates_set:
            return ds
    return target_date


async def build_summary(
    db: AsyncSession,
    start_date: str,
    end_date: str,
    product_cds: list[str] | None = None,
    process_overrides: dict[str, dict[str, dict[str, int]]] | None = None,
    run_calendar_items: list[dict[str, Any]] | None = None,
    include_forecast: bool = False,
    base_month: str | None = None,
    include_order_matrix: bool = False,
) -> dict[str, Any]:
    ps = parse_iso_date(start_date)
    pe = parse_iso_date(end_date)
    validate_period(ps, pe)
    dates = daterange_inclusive(ps, pe)

    process_overrides = process_overrides or {}
    run_calendar: dict[str, set[str]] = {}
    for item in run_calendar_items or []:
        pk = str(item.get("process_key", "")).lower()
        run_calendar[pk] = set(item.get("dates") or [])

    rows = await _load_summary_rows(db, ps, pe, product_cds)
    route_cds_map = await _load_route_process_cds(db)
    product_process_cds = await load_product_process_cds(db)
    sw_products = await _load_sw_machine_products(db)
    bom_lt = await _load_bom_lt(db)

    route_sequences: dict[str, list[str]] = {}
    products_meta: dict[str, dict[str, Any]] = {}

    for row in rows:
        cd = (row.get("product_cd") or "").strip()
        route_cd = (row.get("route_cd") or "").strip()
        if cd and cd not in products_meta:
            products_meta[cd] = {
                "product_cd": cd,
                "product_name": row.get("product_name") or "",
                "route_cd": route_cd,
            }
        if route_cd and route_cd not in route_sequences:
            route_sequences[route_cd] = await _get_route_sequence(db, route_cd)

    # 按 product 分组
    by_product: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        cd = (row.get("product_cd") or "").strip()
        if cd:
            by_product.setdefault(cd, []).append(row)

    daily_matrix_rows: list[dict[str, Any]] = []
    inventory_matrix_rows: list[dict[str, Any]] = []
    trend_matrix_rows: list[dict[str, Any]] = []
    total_molding_plan = 0
    min_warehouse = 0
    negative_wh_days = 0
    has_molding_plan = False

    for product_cd, product_rows in sorted(by_product.items()):
        if product_cd in products_meta:
            machines: dict[str, str] = {}
            for pk in PROCESS_KEY_MACHINE_FIELD:
                m = pick_product_machine(product_rows, pk)
                if m:
                    machines[pk] = m
            products_meta[product_cd]["machines"] = machines

    molding_orders = await _load_molding_production_orders(
        db, ps, pe, list(products_meta.keys()) or None
    )
    for product_cd, meta in products_meta.items():
        molding_machine = (meta.get("machines") or {}).get("molding", "").strip()
        order = _pick_molding_order(product_cd, molding_machine, molding_orders)
        if order is not None:
            meta["molding_order"] = order

    for product_cd, product_rows in sorted(by_product.items()):
        route_cd = (product_rows[0].get("route_cd") or "").strip()
        route_pcds = route_cds_map.get(route_cd, set())
        has_sw = product_cd in sw_products
        sequence = route_sequences.get(route_cd) or list(SIMULATION_PROCESS_KEYS)

        cascaded_rows: list[dict[str, Any]] = []
        for row in product_rows:
            r = dict(row)
            apply_molding_cascade_to_row(r, route_pcds, has_sw)
            mp = _num(r, "molding_plan")
            for pk, field in PROCESS_KEY_TO_PLAN_FIELD.items():
                if pk == "molding":
                    continue
                r[field] = molding_derived_plan_for_process(mp, pk, route_pcds)
            cascaded_rows.append(r)

        # 构建 plan matrix rows
        for pk in SIMULATION_PROCESS_KEYS:
            by_date: dict[str, Any] = {}
            for row in cascaded_rows:
                ds = str(row.get("date") or "")[:10]
                if not ds:
                    continue
                ov = (process_overrides.get(product_cd) or {}).get(ds, {}).get(pk)
                molding_plan = _num(row, "molding_plan")
                if pk == "molding":
                    derived = molding_plan
                    total_molding_plan += molding_plan
                    if molding_plan > 0:
                        has_molding_plan = True
                else:
                    derived = molding_derived_plan_for_process(molding_plan, pk, route_pcds)
                final = ov if ov is not None else derived
                by_date[ds] = {
                    "molding_plan": molding_plan if pk == "molding" else _num(row, "molding_plan"),
                    "derived_plan": derived,
                    "final_plan": final,
                    "override_plan": ov,
                }
            daily_matrix_rows.append(
                {"product_cd": product_cd, "process_key": pk, "by_date": by_date}
            )

        # 在库试算
        overrides_by_date: dict[str, dict[str, int]] = {}
        for ds, pmap in (process_overrides.get(product_cd) or {}).items():
            overrides_by_date[ds] = dict(pmap)

        sorted_rows = sorted(
            [(str(r.get("date") or "")[:10], r) for r in cascaded_rows],
            key=lambda x: x[0],
        )
        inv_series, trend_series = simulate_product_inventory_series(sorted_rows, sequence, overrides_by_date)

        for pk in (*SIMULATION_PROCESS_KEYS, "warehouse"):
            cfg_key = pk
            from app.modules.database.api import _get_process_config_by_key

            cfg = _get_process_config_by_key(cfg_key)
            inv_field = cfg.get("fields", {}).get("inventory") if cfg else None
            trend_field = cfg.get("fields", {}).get("trend") if cfg else None
            if not inv_field:
                continue
            inv_by_date: dict[str, int] = {}
            trend_by_date: dict[str, int] = {}
            current_by_date: dict[str, int] = {}
            sim_by_date: dict[str, int] = {}
            for row in cascaded_rows:
                ds = str(row.get("date") or "")[:10]
                current_by_date[ds] = _num(row, inv_field)
            for entry in inv_series:
                ds = entry.get("date", "")
                sim_by_date[ds] = entry.get(inv_field, 0)
            for entry in trend_series:
                ds = entry.get("date", "")
                if trend_field:
                    trend_by_date[ds] = entry.get(trend_field, 0)
            for ds in dates:
                inv_by_date[ds] = sim_by_date.get(ds, current_by_date.get(ds, 0))
                if pk == "warehouse":
                    v = inv_by_date[ds]
                    if v < min_warehouse:
                        min_warehouse = v
                    if v < 0:
                        negative_wh_days += 1

            inventory_matrix_rows.append(
                {
                    "product_cd": product_cd,
                    "process_key": pk,
                    "by_date": {ds: {"simulated": inv_by_date.get(ds, 0), "current": current_by_date.get(ds, 0)} for ds in dates},
                }
            )
            if trend_field:
                trend_matrix_rows.append(
                    {"product_cd": product_cd, "process_key": pk, "by_date": trend_by_date}
                )

    order_forecast: list[dict[str, Any]] = []
    if include_forecast and base_month:
        order_forecast = await build_order_forecast(db, base_month, months=2, product_cd=None)

    # 各工程计划合计（成型基准级联 + override 后的 final_plan 汇总）
    process_totals_map: dict[str, int] = {pk: 0 for pk in SIMULATION_PROCESS_KEYS}
    process_daily_map: dict[str, dict[str, int]] = {pk: {d: 0 for d in dates} for pk in SIMULATION_PROCESS_KEYS}
    for matrix_row in daily_matrix_rows:
        pk = matrix_row.get("process_key", "")
        if pk not in process_totals_map:
            continue
        for ds, cell in (matrix_row.get("by_date") or {}).items():
            qty = int(cell.get("final_plan") if cell.get("final_plan") is not None else cell.get("derived_plan") or 0)
            process_totals_map[pk] += qty
            if ds in process_daily_map[pk]:
                process_daily_map[pk][ds] += qty

    molding_total = process_totals_map.get("molding", 0) or total_molding_plan
    process_plan_totals = []
    for pk in SIMULATION_PROCESS_KEYS:
        total = process_totals_map.get(pk, 0)
        ratio = round(total / molding_total, 4) if molding_total > 0 else None
        process_plan_totals.append(
            {
                "process_key": pk,
                "total": total,
                "ratio_to_molding": ratio,
                "is_baseline": pk == "molding",
            }
        )
    process_plan_daily_totals = [
        {"process_key": pk, "by_date": process_daily_map[pk], "total": process_totals_map.get(pk, 0)}
        for pk in SIMULATION_PROCESS_KEYS
    ]

    order_process_totals = await compute_order_process_totals_from_monthly(db, ps, pe)
    order_matrix_rows: list[dict[str, Any]] = []
    if include_order_matrix:
        order_daily_map = await load_order_daily_by_product_date(db, ps, pe)
        order_matrix_rows = build_order_matrix_rows(
            sorted(products_meta.keys()),
            dates,
            order_daily_map,
            product_process_cds,
        )

    payload: dict[str, Any] = {
        "period": {"start": ps.isoformat(), "end": pe.isoformat()},
        "dates": dates,
        "products": list(products_meta.values()),
        "daily_matrix": {"rows": daily_matrix_rows},
        "inventory_matrix": {"rows": inventory_matrix_rows},
        "trend_matrix": {"rows": trend_matrix_rows},
        "order_forecast": order_forecast,
        "process_plan_totals": process_plan_totals,
        "process_plan_daily_totals": process_plan_daily_totals,
        "order_process_totals": order_process_totals,
        "kpi": {
            "total_molding_plan": total_molding_plan,
            "negative_warehouse_days": negative_wh_days,
            "min_warehouse_inventory": min_warehouse,
            "has_molding_plan": has_molding_plan,
            "product_count": len(products_meta),
            "process_plan_totals": process_plan_totals,
        },
    }
    if include_order_matrix:
        payload["order_matrix"] = {"rows": order_matrix_rows}
    return payload


async def build_order_matrix_for_period(
    db: AsyncSession,
    start_date: str,
    end_date: str,
    product_cds: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """受注明細印刷用 matrix のみ構築。"""
    ps = parse_iso_date(start_date)
    pe = parse_iso_date(end_date)
    validate_period(ps, pe)
    dates = daterange_inclusive(ps, pe)
    rows = await _load_summary_rows(db, ps, pe, product_cds)
    products = sorted({(r.get("product_cd") or "").strip() for r in rows if (r.get("product_cd") or "").strip()})
    product_process_cds = await load_product_process_cds(db)
    order_daily_map = await load_order_daily_by_product_date(db, ps, pe)
    matrix_rows = build_order_matrix_rows(products, dates, order_daily_map, product_process_cds)
    return matrix_rows, dates


async def apply_scenario_to_summary(
    db: AsyncSession,
    scenario_id: int,
    applied_by: str,
) -> dict[str, Any]:
    """将草稿中最终 plan（除 molding_plan）写回 production_summarys。"""
    meta_q = text(
        "SELECT id, period_start, period_end, status FROM forming_daily_plan_scenarios WHERE id = :id"
    )
    meta = (await db.execute(meta_q, {"id": scenario_id})).mappings().first()
    if not meta:
        raise ValueError("方案不存在")
    if meta["status"] == "applied":
        raise ValueError("方案已应用")

    payload_q = text("SELECT payload FROM forming_daily_plan_scenario_payload WHERE scenario_id = :id")
    payload_row = (await db.execute(payload_q, {"id": scenario_id})).mappings().first()
    if not payload_row:
        raise ValueError("方案数据不存在")

    payload = payload_row["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)

    sim = (payload or {}).get("last_simulation") or {}
    daily_rows = (sim.get("daily_matrix") or {}).get("rows") or []
    overrides = (payload or {}).get("process_overrides") or {}

    plan_fields = {k: v for k, v in PROCESS_KEY_TO_PLAN_FIELD.items() if k != "molding"}

    updated = 0
    ps = meta["period_start"]
    pe = meta["period_end"]

    for matrix_row in daily_rows:
        product_cd = matrix_row.get("product_cd")
        pk = matrix_row.get("process_key")
        if pk == "molding" or pk not in plan_fields:
            continue
        field = plan_fields[pk]
        by_date = matrix_row.get("by_date") or {}
        for ds, cell in by_date.items():
            qty = cell.get("override_plan")
            if qty is None:
                qty = cell.get("final_plan", cell.get("derived_plan", 0))
            ov = (overrides.get(product_cd) or {}).get(ds, {}).get(pk)
            if ov is not None:
                qty = ov
            stmt = (
                update(ProductionSummary)
                .where(
                    and_(
                        ProductionSummary.product_cd == product_cd,
                        ProductionSummary.date == ds,
                    )
                )
                .values({field: int(qty or 0)})
            )
            res = await db.execute(stmt)
            updated += res.rowcount or 0

    await db.execute(
        text(
            """
            UPDATE forming_daily_plan_scenarios
            SET status = 'applied', applied_at = NOW(), applied_by = :by
            WHERE id = :id
            """
        ),
        {"id": scenario_id, "by": applied_by},
    )
    await db.commit()
    return {"updated": updated, "scenario_id": scenario_id}

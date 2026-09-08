"""
日受注 + 製品ルートから CP-SAT スナップショットを展開する。

製品CDは末尾を 1 にそろえ、同一交期は日合計したあと製品マスタのロットサイズで分割する。
1 ロット = 1 ジョブ。ロットサイズ未設定（1 以下）は日合計を 1 ジョブのままにする。
倉庫系工程は Job-Shop 対象外としてスキップする。
求解器は呼ばず、cpsat_runs / jobs / operations / candidates のみ書き込む。
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any, Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst_naive
from app.modules.cpsat.models import CpsatCandidate, CpsatJob, CpsatOperation, CpsatRun
from app.modules.cpsat.quantities import (
    due_sec_from_horizon,
    processing_sec_for_batch,
    reverse_batch_quantities,
    setup_min_to_sec,
    split_qty_into_lots,
)
from app.modules.cpsat.schemas import ExpandRunIn, ExpandWarningOut, QtySource
from app.modules.erp.models import OrderDaily
from app.modules.master.models import (
    Machine,
    Process,
    ProcessRouteStep,
    Product,
    ProductRouteStep,
    ProductRouteStepMachine,
)

# 倉庫・バッファ工程。設備割当の対象にしない
SKIP_PROCESS_CDS = frozenset({"KT13", "KT15", "KT16", "KT17"})


@dataclass
class _CandDraft:
    machine_cd: str
    machine_name: str
    process_time_sec: float
    setup_time_sec: int
    processing_sec: int = 0


@dataclass
class _OpDraft:
    step_no: int
    process_cd: str
    process_name: str
    yield_percent: float
    wait_sec_after: int
    q_input: int = 0
    q_output: int = 0
    candidates: list[_CandDraft] = field(default_factory=list)


@dataclass
class _JobDraft:
    source_id: int
    order_no: str
    product_cd: str
    product_name: str
    q_target: int
    q_start: int
    due_at: datetime
    due_sec: int
    lot_size: int = 0
    lot_index: int = 1
    lot_count: int = 1
    operations: list[_OpDraft] = field(default_factory=list)
    incomplete_no_machine: bool = False
    incomplete_zero_ptime: bool = False


@dataclass
class ExpandResult:
    run: CpsatRun
    warnings: ExpandWarningOut


def normalize_product_cd(cd: Optional[str]) -> str:
    """製品CDの末尾を '1' にそろえる（桁数に依存しない）。例: 90012 → 90011。"""
    s = (cd or "").strip()
    if not s:
        return ""
    return s[:-1] + "1"


def _sa_normalize_product_cd(column):
    return func.concat(func.substr(column, 1, func.length(column) - 1), "1")


@dataclass
class _AggOrder:
    source_id: int
    order_no: str
    product_cd: str
    product_name: str
    q_target: int
    delivery_date: date
    original_cds: set[str] = field(default_factory=set)


def _qty_from_order(row: OrderDaily, source: QtySource) -> int:
    confirmed = int(row.confirmed_units or 0)
    forecast = int(row.forecast_units or 0)
    if source == "forecast":
        return forecast
    if source == "confirmed_or_forecast":
        return confirmed if confirmed > 0 else forecast
    return confirmed


def aggregate_orders_by_product_day(
    rows: list[OrderDaily],
    source: QtySource,
) -> list[_AggOrder]:
    """末尾1正規化のあと、(製品CD, 交期) で日合計する。"""
    buckets: dict[tuple[str, date], _AggOrder] = {}
    for row in rows:
        due = row.delivery_date
        if due is None:
            continue
        orig = (row.product_cd or "").strip()
        pcd = normalize_product_cd(orig)
        if not pcd:
            continue
        qty = _qty_from_order(row, source)
        if qty <= 0:
            continue
        key = (pcd, due)
        name = (row.product_name or "").strip()
        order_no = str(row.monthly_order_id or row.shipping_no or row.id)
        cur = buckets.get(key)
        if cur is None:
            buckets[key] = _AggOrder(
                source_id=int(row.id),
                order_no=order_no,
                product_cd=pcd,
                product_name=name or pcd,
                q_target=qty,
                delivery_date=due,
                original_cds={orig} if orig else set(),
            )
            continue
        cur.q_target += qty
        cur.source_id = min(cur.source_id, int(row.id))
        if orig:
            cur.original_cds.add(orig)
        if orig.endswith("1") and name:
            cur.product_name = name
        elif name and (not cur.product_name or cur.product_name == pcd):
            cur.product_name = name
        if order_no and order_no not in cur.order_no:
            cur.order_no = f"{cur.order_no},{order_no}"
    return sorted(buckets.values(), key=lambda x: (x.delivery_date, x.product_cd, x.source_id))


def _to_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _resolve_yield_percent(
    step: ProductRouteStep,
    template_by_key: dict[tuple[str, str], ProcessRouteStep],
    process: Optional[Process],
) -> float:
    if step.yield_percent is not None:
        return _to_float(step.yield_percent, 100.0)
    tmpl = template_by_key.get((step.route_cd or "", step.process_cd or ""))
    if tmpl is not None and tmpl.yield_percent is not None:
        return _to_float(tmpl.yield_percent, 100.0)
    if process is not None and process.default_yield is not None:
        return _to_float(process.default_yield, 1.0) * 100.0
    return 100.0


def _resolve_wait_sec(
    step: ProductRouteStep,
    template_by_key: dict[tuple[str, str], ProcessRouteStep],
) -> int:
    if step.wait_sec_after is not None:
        return int(step.wait_sec_after)
    tmpl = template_by_key.get((step.route_cd or "", step.process_cd or ""))
    if tmpl is not None and tmpl.wait_sec_after is not None:
        return int(tmpl.wait_sec_after)
    return 0


def _clone_op(op: _OpDraft) -> _OpDraft:
    return _OpDraft(
        step_no=op.step_no,
        process_cd=op.process_cd,
        process_name=op.process_name,
        yield_percent=op.yield_percent,
        wait_sec_after=op.wait_sec_after,
    )


def _apply_qty_and_candidates(
    op_drafts: list[_OpDraft],
    q_target: int,
    *,
    product_cd: str,
    route_cd: str,
    machines_by_step: dict[tuple[str, str, int], list[ProductRouteStepMachine]],
    machine_by_cd: dict[str, Machine],
) -> int:
    q_start, pairs = reverse_batch_quantities(q_target, [op.yield_percent for op in op_drafts])
    for op, (qin, qout) in zip(op_drafts, pairs):
        op.q_input = qin
        op.q_output = qout
        for m in machines_by_step.get((product_cd, route_cd, op.step_no), []):
            mach = machine_by_cd.get(m.machine_cd)
            if not _machine_usable(mach):
                continue
            piece = _to_float(m.process_time_sec, 0.0)
            op.candidates.append(
                _CandDraft(
                    machine_cd=m.machine_cd,
                    machine_name=(
                        m.machine_name or (mach.machine_name if mach else None) or m.machine_cd
                    ),
                    process_time_sec=piece,
                    setup_time_sec=setup_min_to_sec(m.setup_time),
                    processing_sec=processing_sec_for_batch(piece, op.q_input),
                )
            )
    return q_start


def _machine_usable(machine: Optional[Machine]) -> bool:
    if machine is None:
        return True
    if machine.use_in_cpsat is False:
        return False
    if machine.is_active is False:
        return False
    status = (machine.status or "active").strip().lower()
    return status in ("active", "")


async def _next_run_code(db: AsyncSession, day: str) -> str:
    prefix = f"CPSAT-{day}-"
    q = select(CpsatRun.run_code).where(CpsatRun.run_code.like(f"{prefix}%"))
    rows = (await db.execute(q)).scalars().all()
    seq = 1
    for code in rows:
        try:
            seq = max(seq, int(str(code).rsplit("-", 1)[-1]) + 1)
        except (TypeError, ValueError):
            continue
    return f"{prefix}{seq:03d}"


async def expand_orders_to_run(
    db: AsyncSession,
    body: ExpandRunIn,
    *,
    created_by: Optional[str] = None,
) -> ExpandResult:
    if body.due_to < body.due_from:
        raise ValueError("due_to は due_from 以降を指定してください")

    horizon_start = datetime.combine(body.due_from, time.min)
    horizon_end = datetime.combine(body.due_to, time(23, 59, 59))
    warnings = ExpandWarningOut()

    orders_q = (
        select(OrderDaily)
        .where(
            OrderDaily.delivery_date >= body.due_from,
            OrderDaily.delivery_date <= body.due_to,
        )
        .order_by(OrderDaily.delivery_date, OrderDaily.id)
    )
    if body.product_cds:
        wanted = {normalize_product_cd(c) for c in body.product_cds if c and str(c).strip()}
        wanted.discard("")
        if wanted:
            orders_q = orders_q.where(
                _sa_normalize_product_cd(OrderDaily.product_cd).in_(list(wanted))
            )
    orders = (await db.execute(orders_q)).scalars().all()

    for row in orders:
        if row.delivery_date is None:
            warnings.skipped_no_due += 1
        elif _qty_from_order(row, body.qty_source) <= 0:
            warnings.skipped_no_qty += 1

    aggregated = aggregate_orders_by_product_day(orders, body.qty_source)
    max_jobs = int(body.max_jobs) if body.max_jobs else None

    product_cds = sorted({a.product_cd for a in aggregated})
    products = {}
    steps_by_product: dict[str, list[ProductRouteStep]] = defaultdict(list)
    machines_by_step: dict[tuple[str, str, int], list[ProductRouteStepMachine]] = defaultdict(list)
    template_by_key: dict[tuple[str, str], ProcessRouteStep] = {}
    process_by_cd: dict[str, Process] = {}
    machine_by_cd: dict[str, Machine] = {}

    if product_cds:
        prod_rows = (
            (await db.execute(select(Product).where(Product.product_cd.in_(product_cds))))
            .scalars()
            .all()
        )
        products = {p.product_cd: p for p in prod_rows}

        step_rows = (
            (
                await db.execute(
                    select(ProductRouteStep)
                    .where(ProductRouteStep.product_cd.in_(product_cds))
                    .order_by(ProductRouteStep.product_cd, ProductRouteStep.step_no)
                )
            )
            .scalars()
            .all()
        )
        route_cds = set()
        for s in step_rows:
            steps_by_product[s.product_cd].append(s)
            if s.route_cd:
                route_cds.add(s.route_cd)

        m_rows = (
            (
                await db.execute(
                    select(ProductRouteStepMachine).where(
                        ProductRouteStepMachine.product_cd.in_(product_cds)
                    )
                )
            )
            .scalars()
            .all()
        )
        for m in m_rows:
            machines_by_step[(m.product_cd, m.route_cd, int(m.step_no))].append(m)

        if route_cds:
            t_rows = (
                (
                    await db.execute(
                        select(ProcessRouteStep).where(
                            ProcessRouteStep.route_cd.in_(list(route_cds))
                        )
                    )
                )
                .scalars()
                .all()
            )
            for t in t_rows:
                key = (t.route_cd, t.process_cd)
                prev = template_by_key.get(key)
                if prev is None or int(t.step_no or 0) < int(prev.step_no or 0):
                    template_by_key[key] = t

        proc_rows = (await db.execute(select(Process))).scalars().all()
        process_by_cd = {p.process_cd: p for p in proc_rows}

        machine_rows = (await db.execute(select(Machine))).scalars().all()
        machine_by_cd = {m.machine_cd: m for m in machine_rows}

    drafts: list[_JobDraft] = []
    skipped_products: set[str] = set()
    for row in aggregated:
        pcd = row.product_cd
        product = products.get(pcd)
        product_name = (product.product_name if product else None) or row.product_name or pcd
        all_steps = steps_by_product.get(pcd) or []
        preferred_route = (product.route_cd if product else None) or (
            all_steps[0].route_cd if all_steps else None
        )
        if preferred_route:
            route_steps = [s for s in all_steps if s.route_cd == preferred_route]
            if not route_steps:
                route_steps = all_steps
        else:
            route_steps = all_steps
        route_steps = sorted(route_steps, key=lambda s: int(s.step_no or 0))

        if not route_steps:
            warnings.skipped_no_route += 1
            skipped_products.add(pcd)
            continue

        actual_route = route_steps[0].route_cd or ""

        op_templates: list[_OpDraft] = []
        for step in route_steps:
            pcd_step = (step.process_cd or "").strip()
            if pcd_step in SKIP_PROCESS_CDS:
                continue
            proc = process_by_cd.get(pcd_step)
            op_templates.append(
                _OpDraft(
                    step_no=int(step.step_no or 0),
                    process_cd=pcd_step,
                    process_name=(proc.process_name if proc else None) or pcd_step,
                    yield_percent=_resolve_yield_percent(step, template_by_key, proc),
                    wait_sec_after=_resolve_wait_sec(step, template_by_key),
                    candidates=[],
                )
            )

        if not op_templates:
            warnings.skipped_no_ops += 1
            skipped_products.add(pcd)
            continue

        lot_size = int(product.lot_size or 0) if product is not None else 0
        lots = split_qty_into_lots(int(row.q_target), lot_size)
        if not lots:
            continue
        lot_count = len(lots)
        lot_size_snap = lot_size if lot_size > 1 else 0
        due_at = datetime.combine(row.delivery_date, time(23, 59, 59))
        due_sec = due_sec_from_horizon(horizon_start, due_at) or 0

        for lot_index, lot_qty in lots:
            if max_jobs is not None and len(drafts) >= max_jobs:
                break
            op_drafts = [_clone_op(op) for op in op_templates]
            q_start = _apply_qty_and_candidates(
                op_drafts,
                lot_qty,
                product_cd=pcd,
                route_cd=actual_route,
                machines_by_step=machines_by_step,
                machine_by_cd=machine_by_cd,
            )
            incomplete_no_machine = any(not op.candidates for op in op_drafts)
            incomplete_zero_ptime = any(
                op.candidates and all(c.process_time_sec <= 0 for c in op.candidates)
                for op in op_drafts
            )
            if incomplete_no_machine:
                warnings.incomplete_no_machine += 1
            if incomplete_zero_ptime:
                warnings.incomplete_zero_ptime += 1
            drafts.append(
                _JobDraft(
                    source_id=int(row.source_id),
                    order_no=(row.order_no or "")[:50],
                    product_cd=pcd,
                    product_name=product_name,
                    q_target=lot_qty,
                    q_start=q_start,
                    due_at=due_at,
                    due_sec=due_sec,
                    lot_size=lot_size_snap,
                    lot_index=lot_index,
                    lot_count=lot_count,
                    operations=op_drafts,
                    incomplete_no_machine=incomplete_no_machine,
                    incomplete_zero_ptime=incomplete_zero_ptime,
                )
            )
        if max_jobs is not None and len(drafts) >= max_jobs:
            break

    warnings.skipped_product_cds = sorted(skipped_products)

    day = now_jst_naive().strftime("%Y%m%d")
    run = CpsatRun(
        run_code=await _next_run_code(db, day),
        name=body.name or f"{body.due_from.isoformat()}〜{body.due_to.isoformat()} 展開",
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        time_unit_sec=60,
        objective_type="tardiness",
        status="draft",
        job_count=len(drafts),
        operation_count=sum(len(j.operations) for j in drafts),
        error_message=_warning_text(warnings) or None,
        created_by=created_by,
    )
    db.add(run)
    await db.flush()

    for job_index, job in enumerate(drafts, start=1):
        job_row = CpsatJob(
            run_id=run.id,
            job_index=job_index,
            source_type="order_daily",
            source_id=job.source_id,
            order_no=job.order_no,
            product_cd=job.product_cd,
            product_name=job.product_name,
            q_target=job.q_target,
            q_start=job.q_start,
            due_at=job.due_at,
            due_sec=job.due_sec,
            lot_size=job.lot_size,
            lot_index=job.lot_index,
            lot_count=job.lot_count,
        )
        db.add(job_row)
        await db.flush()
        op_rows: list[tuple[CpsatOperation, _OpDraft]] = []
        for op_index, op in enumerate(job.operations, start=1):
            op_row = CpsatOperation(
                run_id=run.id,
                job_id=job_row.id,
                op_index=op_index,
                step_no=op.step_no,
                process_cd=op.process_cd,
                process_name=op.process_name,
                yield_percent=op.yield_percent,
                wait_sec_after=op.wait_sec_after,
                q_input=op.q_input,
                q_output=op.q_output,
            )
            db.add(op_row)
            op_rows.append((op_row, op))
        await db.flush()
        for op_row, op in op_rows:
            for cand in op.candidates:
                db.add(
                    CpsatCandidate(
                        run_id=run.id,
                        operation_id=op_row.id,
                        machine_cd=cand.machine_cd,
                        machine_name=cand.machine_name,
                        process_time_sec=cand.process_time_sec,
                        setup_time_sec=cand.setup_time_sec,
                        processing_sec=cand.processing_sec,
                        is_assigned=False,
                    )
                )

    await db.commit()
    await db.refresh(run)
    logger.info(
        "CP-SAT expand: run_id={} jobs={} ops={} skipped_route={} incomplete_machine={}",
        run.id,
        run.job_count,
        run.operation_count,
        warnings.skipped_no_route,
        warnings.incomplete_no_machine,
    )
    return ExpandResult(run=run, warnings=warnings)


def _warning_text(w: ExpandWarningOut) -> str:
    payload = {
        "skipped_no_qty": w.skipped_no_qty,
        "skipped_no_due": w.skipped_no_due,
        "skipped_no_route": w.skipped_no_route,
        "skipped_no_ops": w.skipped_no_ops,
        "incomplete_no_machine": w.incomplete_no_machine,
        "incomplete_zero_ptime": w.incomplete_zero_ptime,
        "skipped_product_cds": w.skipped_product_cds[:50],
    }
    if not any(
        [
            w.skipped_no_qty,
            w.skipped_no_due,
            w.skipped_no_route,
            w.skipped_no_ops,
            w.incomplete_no_machine,
            w.incomplete_zero_ptime,
        ]
    ):
        return ""
    return json.dumps(payload, ensure_ascii=False)


def parse_warning_text(raw: Optional[str]) -> Optional[ExpandWarningOut]:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return ExpandWarningOut(**data)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

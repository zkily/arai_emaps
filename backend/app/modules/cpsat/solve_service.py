"""CP-SAT 求解：スナップショットを読み、OR-Tools で解き、S/E/X を書き戻す。"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cpsat.calendar import load_forbidden_by_machine
from app.modules.cpsat.models import CpsatCandidate, CpsatJob, CpsatOperation, CpsatRun
from app.modules.cpsat.solver import (
    SolveCandidate,
    SolveInput,
    SolveJob,
    SolveOperation,
    SolveOutput,
    solve_model,
)


def _to_int(v, default: int = 0) -> int:
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _to_float(v, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


async def load_solve_input(db: AsyncSession, run: CpsatRun) -> SolveInput:
    jobs = (
        (
            await db.execute(
                select(CpsatJob).where(CpsatJob.run_id == run.id).order_by(CpsatJob.job_index)
            )
        )
        .scalars()
        .all()
    )
    ops = (
        (
            await db.execute(
                select(CpsatOperation)
                .where(CpsatOperation.run_id == run.id)
                .order_by(CpsatOperation.job_id, CpsatOperation.op_index)
            )
        )
        .scalars()
        .all()
    )
    cands = (
        (await db.execute(select(CpsatCandidate).where(CpsatCandidate.run_id == run.id)))
        .scalars()
        .all()
    )
    cands_by_op: dict[int, list[CpsatCandidate]] = {}
    for c in cands:
        cands_by_op.setdefault(int(c.operation_id), []).append(c)
    ops_by_job: dict[int, list[CpsatOperation]] = {}
    for op in ops:
        ops_by_job.setdefault(int(op.job_id), []).append(op)

    solve_jobs: list[SolveJob] = []
    for job in jobs:
        sops: list[SolveOperation] = []
        for op in ops_by_job.get(int(job.id), []):
            scands = [
                SolveCandidate(
                    candidate_id=int(c.id),
                    machine_cd=c.machine_cd,
                    machine_name=c.machine_name or c.machine_cd,
                    processing_sec=_to_int(c.processing_sec),
                    setup_time_sec=_to_int(c.setup_time_sec),
                )
                for c in cands_by_op.get(int(op.id), [])
            ]
            sops.append(
                SolveOperation(
                    operation_id=int(op.id),
                    op_index=int(op.op_index),
                    wait_sec_after=_to_int(op.wait_sec_after),
                    candidates=scands,
                )
            )
        solve_jobs.append(SolveJob(job_id=int(job.id), due_sec=job.due_sec, operations=sops))

    horizon_sec = 0
    if run.horizon_start and run.horizon_end:
        horizon_sec = int((run.horizon_end - run.horizon_start).total_seconds())
    machine_cds = {c.machine_cd for c in cands if c.machine_cd}
    forbidden: dict[str, list[tuple[int, int]]] = {}
    if run.horizon_start and horizon_sec > 0 and machine_cds:
        forbidden = await load_forbidden_by_machine(
            db,
            origin=run.horizon_start,
            horizon_sec=horizon_sec,
            machine_cds=machine_cds,
        )
        logger.info(
            "CP-SAT calendar: run_id={} machines={} forbidden_intervals={}",
            run.id,
            len(forbidden),
            sum(len(v) for v in forbidden.values()),
        )
    return SolveInput(
        time_unit_sec=_to_int(run.time_unit_sec, 60) or 60,
        horizon_sec=max(horizon_sec, 0),
        objective_type=run.objective_type or "tardiness",
        makespan_weight=_to_float(run.makespan_weight, 0.0),
        tardiness_weight=_to_float(run.tardiness_weight, 1.0),
        max_solve_seconds=float(_to_int(run.max_solve_seconds, 60) or 60),
        jobs=solve_jobs,
        forbidden_by_machine=forbidden,
    )


def apply_solution(
    run: CpsatRun,
    jobs: list[CpsatJob],
    ops: list[CpsatOperation],
    cands: list[CpsatCandidate],
    out: SolveOutput,
) -> None:
    by_op = {int(o.id): o for o in ops}
    by_job = {int(j.id): j for j in jobs}
    by_cand = {int(c.id): c for c in cands}
    for c in cands:
        c.is_assigned = False
    for op in ops:
        op.start_sec = None
        op.end_sec = None
        op.start_at = None
        op.end_at = None
        op.assigned_machine_cd = None
        op.assigned_machine_name = None
        op.processing_sec = None
        op.setup_sec = None
    for j in jobs:
        j.last_op_end_sec = None
        j.tardiness_sec = None

    origin = run.horizon_start
    for asg in out.assignments:
        op = by_op.get(asg.operation_id)
        cand = by_cand.get(asg.candidate_id)
        if op is None:
            continue
        op.start_sec = asg.start_sec
        op.end_sec = asg.end_sec
        op.assigned_machine_cd = asg.machine_cd
        op.assigned_machine_name = asg.machine_name
        op.processing_sec = asg.processing_sec
        op.setup_sec = asg.setup_sec
        if origin is not None:
            op.start_at = origin + timedelta(seconds=asg.start_sec)
            op.end_at = origin + timedelta(seconds=asg.end_sec)
        if cand is not None:
            cand.is_assigned = True
    for jr in out.jobs:
        job = by_job.get(jr.job_id)
        if job is None:
            continue
        job.last_op_end_sec = jr.last_op_end_sec
        job.tardiness_sec = jr.tardiness_sec

    run.status = out.status
    run.solver_status = out.solver_status
    run.wall_time_sec = out.wall_time_sec
    run.makespan_sec = out.makespan_sec
    run.total_tardiness_sec = out.total_tardiness_sec
    run.objective_value = out.objective_value
    if out.error_message:
        run.error_message = out.error_message


async def solve_run(
    db: AsyncSession,
    run_id: int,
    *,
    max_solve_seconds: Optional[float] = None,
    objective_type: Optional[str] = None,
) -> tuple[CpsatRun, SolveOutput]:
    run = (await db.execute(select(CpsatRun).where(CpsatRun.id == run_id))).scalar_one_or_none()
    if run is None:
        raise ValueError("求解実行が見つかりません")
    if objective_type:
        run.objective_type = objective_type
    inp = await load_solve_input(db, run)
    if objective_type:
        inp.objective_type = objective_type
    if max_solve_seconds is not None:
        inp.max_solve_seconds = float(max_solve_seconds)
        run.max_solve_seconds = int(max_solve_seconds)

    run.status = "running"
    await db.commit()
    await db.refresh(run)

    logger.info(
        "CP-SAT solve start: run_id={} jobs={} horizon_sec={}",
        run_id,
        len(inp.jobs),
        inp.horizon_sec,
    )
    try:
        out = await asyncio.to_thread(solve_model, inp)
    except Exception as e:
        logger.exception("CP-SAT solve failed: run_id={}", run_id)
        run.status = "error"
        run.solver_status = "ERROR"
        run.error_message = str(e)
        await db.commit()
        await db.refresh(run)
        raise

    jobs = (await db.execute(select(CpsatJob).where(CpsatJob.run_id == run.id))).scalars().all()
    ops = (
        (await db.execute(select(CpsatOperation).where(CpsatOperation.run_id == run.id)))
        .scalars()
        .all()
    )
    cands = (
        (await db.execute(select(CpsatCandidate).where(CpsatCandidate.run_id == run.id)))
        .scalars()
        .all()
    )
    apply_solution(run, list(jobs), list(ops), list(cands), out)
    await db.commit()
    await db.refresh(run)
    logger.info(
        "CP-SAT solve done: run_id={} status={} makespan={} tardiness={} wall={}s",
        run_id,
        out.status,
        out.makespan_sec,
        out.total_tardiness_sec,
        out.wall_time_sec,
    )
    return run, out

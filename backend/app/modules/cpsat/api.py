"""CP-SAT 作業展開 API（求解器は含まない）"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_aps_operation
from app.modules.cpsat.expand import expand_orders_to_run, parse_warning_text
from app.modules.cpsat.models import CpsatCandidate, CpsatJob, CpsatOperation, CpsatRun
from app.modules.cpsat.schemas import (
    CandidateOut,
    ExpandRunIn,
    JobOut,
    OperationOut,
    RunOut,
    SolveRunIn,
)

router = APIRouter()


def _run_to_out(run: CpsatRun, *, include_warnings: bool = True) -> RunOut:
    return RunOut(
        id=int(run.id),
        run_code=run.run_code,
        name=run.name,
        horizon_start=run.horizon_start,
        horizon_end=run.horizon_end,
        time_unit_sec=int(run.time_unit_sec or 60),
        objective_type=run.objective_type or "tardiness",
        status=run.status or "draft",
        solver_status=run.solver_status,
        wall_time_sec=float(run.wall_time_sec) if run.wall_time_sec is not None else None,
        makespan_sec=int(run.makespan_sec) if run.makespan_sec is not None else None,
        total_tardiness_sec=(
            int(run.total_tardiness_sec) if run.total_tardiness_sec is not None else None
        ),
        objective_value=float(run.objective_value) if run.objective_value is not None else None,
        job_count=int(run.job_count or 0),
        operation_count=int(run.operation_count or 0),
        error_message=run.error_message,
        created_by=run.created_by,
        created_at=run.created_at,
        warnings=parse_warning_text(run.error_message) if include_warnings else None,
    )


def _job_to_out(
    j: CpsatJob,
    *,
    operation_count: int = 0,
    incomplete: bool = False,
    operations: Optional[list[OperationOut]] = None,
) -> JobOut:
    return JobOut(
        id=int(j.id),
        job_index=int(j.job_index),
        source_type=j.source_type,
        source_id=j.source_id,
        order_no=j.order_no,
        product_cd=j.product_cd,
        product_name=j.product_name,
        q_target=int(j.q_target),
        q_start=int(j.q_start),
        lot_size=int(j.lot_size) if j.lot_size is not None else None,
        lot_index=int(j.lot_index) if j.lot_index is not None else None,
        lot_count=int(j.lot_count) if j.lot_count is not None else None,
        due_at=j.due_at,
        due_sec=j.due_sec,
        last_op_end_sec=j.last_op_end_sec,
        tardiness_sec=j.tardiness_sec,
        operation_count=operation_count,
        incomplete=incomplete,
        operations=operations,
    )


def _op_to_out(
    op: CpsatOperation,
    *,
    candidates: Optional[list[CpsatCandidate]] = None,
    candidate_count: Optional[int] = None,
) -> OperationOut:
    cands = candidates if candidates is not None else []
    count = candidate_count if candidate_count is not None else len(cands)
    return OperationOut(
        id=int(op.id),
        op_index=int(op.op_index),
        step_no=int(op.step_no),
        process_cd=op.process_cd,
        process_name=op.process_name,
        yield_percent=float(op.yield_percent or 100),
        wait_sec_after=int(op.wait_sec_after or 0),
        q_input=int(op.q_input or 0),
        q_output=int(op.q_output or 0),
        start_sec=op.start_sec,
        end_sec=op.end_sec,
        start_at=op.start_at,
        end_at=op.end_at,
        assigned_machine_cd=op.assigned_machine_cd,
        assigned_machine_name=op.assigned_machine_name,
        processing_sec=op.processing_sec,
        setup_sec=op.setup_sec,
        candidate_count=count,
        candidates=(
            [
                CandidateOut(
                    id=int(c.id),
                    machine_cd=c.machine_cd,
                    machine_name=c.machine_name,
                    process_time_sec=float(c.process_time_sec or 0),
                    setup_time_sec=int(c.setup_time_sec or 0),
                    processing_sec=int(c.processing_sec or 0),
                    is_assigned=bool(c.is_assigned),
                )
                for c in cands
            ]
            if candidates is not None
            else None
        ),
    )


@router.post("/runs/expand", response_model=RunOut)
async def expand_run(
    body: ExpandRunIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("create")),
):
    """日受注を製品ルートで工程展開し、CP-SAT スナップショットを作成する。"""
    try:
        result = await expand_orders_to_run(db, body, created_by=current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    out = _run_to_out(result.run)
    out.warnings = result.warnings
    return out


@router.post("/runs/{run_id}/solve", response_model=RunOut)
async def solve_existing_run(
    run_id: int,
    body: SolveRunIn = Body(default_factory=SolveRunIn),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("create")),
):
    """展開済みスナップショットを CP-SAT で求解し、S/E/X を書き戻す。"""
    from app.modules.cpsat.solve_service import solve_run

    try:
        run, _out = await solve_run(
            db,
            run_id,
            max_solve_seconds=body.max_solve_seconds,
            objective_type=body.objective_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"求解に失敗しました: {e}") from e
    return _run_to_out(run)


@router.get("/runs", response_model=list[RunOut])
async def list_runs(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(CpsatRun).order_by(CpsatRun.id.desc()).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [_run_to_out(r) for r in rows]


@router.delete("/runs/{run_id}")
async def delete_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_aps_operation("delete")),
):
    """実行履歴を削除する（ジョブ・工程・候補は CASCADE）。"""
    run = (await db.execute(select(CpsatRun).where(CpsatRun.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="求解実行が見つかりません")
    if (run.status or "") == "running":
        raise HTTPException(status_code=409, detail="求解中の実行は削除できません")
    await db.delete(run)
    await db.commit()
    return {"ok": True, "id": run_id}


@router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(
    run_id: int,
    sample_jobs: int = Query(5, ge=0, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    run = (await db.execute(select(CpsatRun).where(CpsatRun.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="求解実行が見つかりません")
    out = _run_to_out(run)
    if sample_jobs > 0:
        jobs = (
            (
                await db.execute(
                    select(CpsatJob)
                    .where(CpsatJob.run_id == run_id)
                    .order_by(CpsatJob.job_index)
                    .limit(sample_jobs)
                )
            )
            .scalars()
            .all()
        )
        op_counts = {
            int(jid): int(n)
            for jid, n in (
                await db.execute(
                    select(CpsatOperation.job_id, func.count())
                    .where(
                        CpsatOperation.run_id == run_id,
                        CpsatOperation.job_id.in_([j.id for j in jobs] or [0]),
                    )
                    .group_by(CpsatOperation.job_id)
                )
            ).all()
        }
        out.jobs = [_job_to_out(j, operation_count=op_counts.get(int(j.id), 0)) for j in jobs]
    return out


@router.get("/runs/{run_id}/jobs", response_model=list[JobOut])
async def list_jobs(
    run_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    run_exists = (
        await db.execute(select(CpsatRun.id).where(CpsatRun.id == run_id))
    ).scalar_one_or_none()
    if not run_exists:
        raise HTTPException(status_code=404, detail="求解実行が見つかりません")
    jobs = (
        (
            await db.execute(
                select(CpsatJob)
                .where(CpsatJob.run_id == run_id)
                .order_by(CpsatJob.job_index)
                .offset(skip)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    if not jobs:
        return []
    job_ids = [j.id for j in jobs]
    ops = (
        (
            await db.execute(
                select(CpsatOperation)
                .where(CpsatOperation.job_id.in_(job_ids))
                .order_by(CpsatOperation.job_id, CpsatOperation.op_index)
            )
        )
        .scalars()
        .all()
    )
    cand_counts = {
        int(oid): int(n)
        for oid, n in (
            await db.execute(
                select(CpsatCandidate.operation_id, func.count())
                .where(CpsatCandidate.operation_id.in_([o.id for o in ops] or [0]))
                .group_by(CpsatCandidate.operation_id)
            )
        ).all()
    }
    ops_by_job: dict[int, list[CpsatOperation]] = {}
    for op in ops:
        ops_by_job.setdefault(int(op.job_id), []).append(op)
    result: list[JobOut] = []
    for j in jobs:
        jops = ops_by_job.get(int(j.id), [])
        incomplete = any(cand_counts.get(int(op.id), 0) == 0 for op in jops)
        result.append(
            _job_to_out(
                j,
                operation_count=len(jops),
                incomplete=incomplete,
                operations=[
                    _op_to_out(op, candidate_count=cand_counts.get(int(op.id), 0)) for op in jops
                ],
            )
        )
    return result


@router.get("/runs/{run_id}/jobs/{job_id}", response_model=JobOut)
async def get_job(
    run_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    job = (
        await db.execute(select(CpsatJob).where(CpsatJob.id == job_id, CpsatJob.run_id == run_id))
    ).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")
    ops = (
        (
            await db.execute(
                select(CpsatOperation)
                .where(CpsatOperation.job_id == job_id)
                .order_by(CpsatOperation.op_index)
            )
        )
        .scalars()
        .all()
    )
    cands = (
        (
            await db.execute(
                select(CpsatCandidate)
                .where(CpsatCandidate.operation_id.in_([o.id for o in ops] or [0]))
                .order_by(CpsatCandidate.id)
            )
        )
        .scalars()
        .all()
    )
    by_op: dict[int, list[CpsatCandidate]] = {}
    for c in cands:
        by_op.setdefault(int(c.operation_id), []).append(c)
    op_outs = [_op_to_out(op, candidates=by_op.get(int(op.id), [])) for op in ops]
    incomplete = any(len(by_op.get(int(op.id), [])) == 0 for op in ops)
    return _job_to_out(
        job,
        operation_count=len(ops),
        incomplete=incomplete,
        operations=op_outs,
    )

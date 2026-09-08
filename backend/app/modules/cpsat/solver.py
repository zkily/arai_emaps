"""
CP-SAT コア（OR-Tools）。DB 非依存。

制約:
  各工程は候補設備のちょうど 1 台に割当（X）
  S + (P + setup) = E
  先行工程終了 + T_wait <= 後続開始
  同一設備の区間は非重複
  設備の非稼働区間（会社休・土日・時間帯外）とも非重複
目的:
  tardiness: min Σ max(0, E_last - D_i)
  makespan:  min C_max
  weighted:  min w_m * C_max + w_t * Σ T_i
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# ortools は solve_model() 内で遅延 import（アプリ起動時に載せない）


def sec_to_unit(sec: int | float | None, unit: int) -> int:
    if not sec or sec <= 0 or unit <= 0:
        return 0
    return int(math.ceil(float(sec) / unit))


def unit_to_sec(units: int, unit: int) -> int:
    return max(int(units), 0) * max(int(unit), 1)


@dataclass
class SolveCandidate:
    candidate_id: int
    machine_cd: str
    machine_name: str
    processing_sec: int
    setup_time_sec: int


@dataclass
class SolveOperation:
    operation_id: int
    op_index: int
    wait_sec_after: int
    candidates: list[SolveCandidate]


@dataclass
class SolveJob:
    job_id: int
    due_sec: int | None
    operations: list[SolveOperation]


@dataclass
class SolveInput:
    time_unit_sec: int
    horizon_sec: int
    objective_type: str
    makespan_weight: float
    tardiness_weight: float
    max_solve_seconds: float
    jobs: list[SolveJob]
    forbidden_by_machine: dict[str, list[tuple[int, int]]] = field(default_factory=dict)


@dataclass
class OpAssignment:
    operation_id: int
    start_sec: int
    end_sec: int
    candidate_id: int
    machine_cd: str
    machine_name: str
    processing_sec: int
    setup_sec: int


@dataclass
class JobResult:
    job_id: int
    last_op_end_sec: int
    tardiness_sec: int


@dataclass
class SolveOutput:
    status: str
    solver_status: str
    wall_time_sec: float
    makespan_sec: int | None = None
    total_tardiness_sec: int | None = None
    objective_value: float | None = None
    error_message: str | None = None
    skipped_job_ids: list[int] = field(default_factory=list)
    assignments: list[OpAssignment] = field(default_factory=list)
    jobs: list[JobResult] = field(default_factory=list)


def solve_model(inp: SolveInput) -> SolveOutput:
    from ortools.sat.python import cp_model

    status_map = {
        cp_model.OPTIMAL: "optimal",
        cp_model.FEASIBLE: "feasible",
        cp_model.INFEASIBLE: "infeasible",
        cp_model.MODEL_INVALID: "error",
        cp_model.UNKNOWN: "error",
    }

    unit = max(int(inp.time_unit_sec or 60), 1)
    jobs: list[SolveJob] = []
    skipped: list[int] = []
    for job in inp.jobs:
        ops = sorted(job.operations, key=lambda o: o.op_index)
        if not ops or any(not op.candidates for op in ops):
            skipped.append(job.job_id)
            continue
        jobs.append(SolveJob(job_id=job.job_id, due_sec=job.due_sec, operations=ops))
    if not jobs:
        return SolveOutput(
            status="error",
            solver_status="MODEL_INVALID",
            wall_time_sec=0.0,
            error_message="割当可能な工程があるジョブがありません",
            skipped_job_ids=skipped,
        )

    horizon_u = sec_to_unit(inp.horizon_sec, unit)
    min_needed = 0
    for job in jobs:
        for op in job.operations:
            min_dur = min(
                sec_to_unit(c.processing_sec + c.setup_time_sec, unit) for c in op.candidates
            )
            min_needed += min_dur
            min_needed += sec_to_unit(op.wait_sec_after, unit)
        if job.due_sec:
            horizon_u = max(horizon_u, sec_to_unit(job.due_sec, unit))
    horizon_u = max(horizon_u, min_needed, 1)

    model = cp_model.CpModel()
    start_vars: dict[int, cp_model.IntVar] = {}
    end_vars: dict[int, cp_model.IntVar] = {}
    last_ends: list[cp_model.IntVar] = []
    tardiness_vars: list[cp_model.IntVar] = []
    presence_by_cand: dict[int, cp_model.BoolVar] = {}
    intervals_by_machine: dict[str, list] = {}

    for job in jobs:
        job_starts: list[cp_model.IntVar] = []
        job_ends: list[cp_model.IntVar] = []
        for op in job.operations:
            start = model.NewIntVar(0, horizon_u, f"s_{op.operation_id}")
            end = model.NewIntVar(0, horizon_u, f"e_{op.operation_id}")
            start_vars[op.operation_id] = start
            end_vars[op.operation_id] = end
            job_starts.append(start)
            job_ends.append(end)
            presences: list[cp_model.BoolVar] = []
            for cand in op.candidates:
                dur = sec_to_unit(cand.processing_sec + cand.setup_time_sec, unit)
                pres = model.NewBoolVar(f"x_{op.operation_id}_{cand.candidate_id}")
                presence_by_cand[cand.candidate_id] = pres
                presences.append(pres)
                interval = model.NewOptionalIntervalVar(
                    start, dur, end, pres, f"iv_{op.operation_id}_{cand.candidate_id}"
                )
                intervals_by_machine.setdefault(cand.machine_cd, []).append(interval)
                model.Add(end == start + dur).OnlyEnforceIf(pres)
            model.AddExactlyOne(presences)
        for prev, nxt, prev_op in zip(job_ends, job_starts[1:], job.operations):
            wait_u = sec_to_unit(prev_op.wait_sec_after, unit)
            model.Add(prev + wait_u <= nxt)
        last_end = job_ends[-1]
        last_ends.append(last_end)
        due_u = sec_to_unit(job.due_sec, unit) if job.due_sec is not None else horizon_u
        tard = model.NewIntVar(0, horizon_u, f"t_{job.job_id}")
        model.Add(tard >= last_end - due_u)
        tardiness_vars.append(tard)

    for machine_cd, ivs in intervals_by_machine.items():
        dummy = []
        forbidden = list(inp.forbidden_by_machine.get(machine_cd) or [])
        if forbidden:
            extra_end = unit_to_sec(horizon_u, unit)
            if extra_end > inp.horizon_sec:
                forbidden.append((inp.horizon_sec, extra_end))
        for i, (s_sec, e_sec) in enumerate(forbidden):
            su = min(sec_to_unit(s_sec, unit), horizon_u)
            eu = min(sec_to_unit(e_sec, unit), horizon_u)
            if eu <= su:
                continue
            dummy.append(model.NewIntervalVar(su, eu - su, eu, f"off_{machine_cd}_{i}"))
        all_ivs = ivs + dummy
        if len(all_ivs) >= 2:
            model.AddNoOverlap(all_ivs)

    cmax = model.NewIntVar(0, horizon_u, "cmax")
    for e in last_ends:
        model.Add(cmax >= e)

    obj_type = (inp.objective_type or "tardiness").strip().lower()
    w_m = max(float(inp.makespan_weight or 0), 0.0)
    w_t = max(float(inp.tardiness_weight or 0), 0.0)
    scale = 10000
    sum_t = sum(tardiness_vars)
    if obj_type == "makespan":
        model.Minimize(cmax)
    elif obj_type == "weighted":
        wm = max(int(round(w_m * scale)), 0)
        wt = max(int(round(w_t * scale)), 0)
        if wm == 0 and wt == 0:
            wt = scale
        model.Minimize(wm * cmax + wt * sum_t)
    else:
        model.Minimize(sum_t)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(max(inp.max_solve_seconds, 1.0))
    solver.parameters.num_search_workers = 8
    status_code = solver.Solve(model)
    solver_name = solver.StatusName(status_code)
    status = status_map.get(status_code, "error")
    wall = float(solver.WallTime())

    if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        reason = (
            "実行不能（設備衝突または期間不足）"
            if status_code == cp_model.INFEASIBLE
            else "制限時間内に解が見つかりません"
        )
        return SolveOutput(
            status=status,
            solver_status=solver_name,
            wall_time_sec=round(wall, 3),
            error_message=reason,
            skipped_job_ids=skipped,
        )

    assignments: list[OpAssignment] = []
    job_results: list[JobResult] = []
    makespan_u = max(int(solver.Value(e)) for e in last_ends)
    total_tard_u = 0
    for job, tard_var in zip(jobs, tardiness_vars):
        last_op = job.operations[-1]
        last_end_u = int(solver.Value(end_vars[last_op.operation_id]))
        tard_u = int(solver.Value(tard_var))
        total_tard_u += tard_u
        job_results.append(
            JobResult(
                job_id=job.job_id,
                last_op_end_sec=unit_to_sec(last_end_u, unit),
                tardiness_sec=unit_to_sec(tard_u, unit),
            )
        )
        for op in job.operations:
            chosen: SolveCandidate | None = None
            for cand in op.candidates:
                if solver.Value(presence_by_cand[cand.candidate_id]):
                    chosen = cand
                    break
            if chosen is None:
                continue
            start_u = int(solver.Value(start_vars[op.operation_id]))
            end_u = int(solver.Value(end_vars[op.operation_id]))
            assignments.append(
                OpAssignment(
                    operation_id=op.operation_id,
                    start_sec=unit_to_sec(start_u, unit),
                    end_sec=unit_to_sec(end_u, unit),
                    candidate_id=chosen.candidate_id,
                    machine_cd=chosen.machine_cd,
                    machine_name=chosen.machine_name,
                    processing_sec=int(chosen.processing_sec),
                    setup_sec=int(chosen.setup_time_sec),
                )
            )

    obj_val = float(solver.ObjectiveValue())
    if obj_type == "weighted":
        obj_val = obj_val / scale
    return SolveOutput(
        status=status,
        solver_status=solver_name,
        wall_time_sec=round(wall, 3),
        makespan_sec=unit_to_sec(makespan_u, unit),
        total_tardiness_sec=unit_to_sec(total_tard_u, unit),
        objective_value=obj_val,
        skipped_job_ids=skipped,
        assignments=assignments,
        jobs=job_results,
    )

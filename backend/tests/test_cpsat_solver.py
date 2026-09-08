from app.modules.cpsat.solver import (
    SolveCandidate,
    SolveInput,
    SolveJob,
    SolveOperation,
    sec_to_unit,
    solve_model,
    unit_to_sec,
)


def test_time_unit_roundtrip():
    assert sec_to_unit(60, 60) == 1
    assert sec_to_unit(61, 60) == 2
    assert sec_to_unit(0, 60) == 0
    assert unit_to_sec(2, 60) == 120


def _two_jobs_one_machine() -> SolveInput:
    # 同一設備で 2 ジョブ × 2 工程。後工程は必ず先行完了後。
    def job(jid: int, due: int) -> SolveJob:
        return SolveJob(
            job_id=jid,
            due_sec=due,
            operations=[
                SolveOperation(
                    operation_id=jid * 10 + 1,
                    op_index=1,
                    wait_sec_after=60,
                    candidates=[
                        SolveCandidate(
                            candidate_id=jid * 10 + 1,
                            machine_cd="M1",
                            machine_name="cut",
                            processing_sec=120,
                            setup_time_sec=0,
                        )
                    ],
                ),
                SolveOperation(
                    operation_id=jid * 10 + 2,
                    op_index=2,
                    wait_sec_after=0,
                    candidates=[
                        SolveCandidate(
                            candidate_id=jid * 10 + 2,
                            machine_cd="M2",
                            machine_name="form",
                            processing_sec=180,
                            setup_time_sec=0,
                        )
                    ],
                ),
            ],
        )

    return SolveInput(
        time_unit_sec=60,
        horizon_sec=3600,
        objective_type="tardiness",
        makespan_weight=0,
        tardiness_weight=1,
        max_solve_seconds=10,
        jobs=[job(1, 2400), job(2, 2400)],
    )


def test_solver_precedence_and_no_overlap():
    out = solve_model(_two_jobs_one_machine())
    assert out.status in ("optimal", "feasible")
    assert len(out.assignments) == 4
    assert out.makespan_sec is not None and 0 < out.makespan_sec < 3600
    by_op = {a.operation_id: a for a in out.assignments}
    # ジョブ内順序: op1 終了 + wait(60s) <= op2 開始
    for jid in (1, 2):
        first = by_op[jid * 10 + 1]
        second = by_op[jid * 10 + 2]
        assert first.end_sec + 60 <= second.start_sec
        assert first.machine_cd == "M1"
        assert second.machine_cd == "M2"
    # M1 上の 2 件は非重複
    a, b = by_op[11], by_op[21]
    assert a.end_sec <= b.start_sec or b.end_sec <= a.start_sec


def test_solver_skips_job_without_candidates():
    inp = SolveInput(
        time_unit_sec=60,
        horizon_sec=600,
        objective_type="makespan",
        makespan_weight=1,
        tardiness_weight=0,
        max_solve_seconds=5,
        jobs=[
            SolveJob(
                job_id=1,
                due_sec=600,
                operations=[
                    SolveOperation(
                        operation_id=1,
                        op_index=1,
                        wait_sec_after=0,
                        candidates=[
                            SolveCandidate(1, "M1", "m", processing_sec=60, setup_time_sec=0)
                        ],
                    )
                ],
            ),
            SolveJob(
                job_id=2,
                due_sec=600,
                operations=[
                    SolveOperation(operation_id=2, op_index=1, wait_sec_after=0, candidates=[])
                ],
            ),
        ],
    )
    out = solve_model(inp)
    assert out.status in ("optimal", "feasible")
    assert out.skipped_job_ids == [2]
    assert len(out.assignments) == 1


def test_solver_respects_forbidden_intervals():
    inp = SolveInput(
        time_unit_sec=60,
        horizon_sec=3600,
        objective_type="makespan",
        makespan_weight=1,
        tardiness_weight=0,
        max_solve_seconds=5,
        forbidden_by_machine={"M1": [(0, 1800)]},
        jobs=[
            SolveJob(
                job_id=1,
                due_sec=3600,
                operations=[
                    SolveOperation(
                        operation_id=1,
                        op_index=1,
                        wait_sec_after=0,
                        candidates=[
                            SolveCandidate(1, "M1", "m", processing_sec=60, setup_time_sec=0)
                        ],
                    )
                ],
            )
        ],
    )
    out = solve_model(inp)
    assert out.status in ("optimal", "feasible")
    assert len(out.assignments) == 1
    assert out.assignments[0].start_sec >= 1800
    assert out.assignments[0].end_sec <= 3600

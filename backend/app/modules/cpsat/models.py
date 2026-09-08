"""
CP-SAT 自動排程のデータモデル。

入力主データ（製品ルート歩留・待ち、候補設備）は master 側。
本モジュールは求解実行のスナップショットと X/S/E 結果を保持する。
"""

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CpsatRun(Base):
    """CP-SAT 求解実行ヘッダ"""

    __tablename__ = "cpsat_runs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_code = Column(String(40), unique=True, nullable=True)
    name = Column(String(100), nullable=True)
    horizon_start = Column(DateTime, nullable=False)
    horizon_end = Column(DateTime, nullable=False)
    time_unit_sec = Column(Integer, nullable=False, default=60)
    objective_type = Column(String(20), nullable=False, default="tardiness")
    makespan_weight = Column(Numeric(8, 4), nullable=False, default=0)
    tardiness_weight = Column(Numeric(8, 4), nullable=False, default=1)
    max_solve_seconds = Column(Integer, nullable=False, default=60)
    status = Column(String(20), nullable=False, default="draft")
    solver_status = Column(String(40), nullable=True)
    wall_time_sec = Column(Numeric(10, 3), nullable=True)
    makespan_sec = Column(BigInteger, nullable=True)
    total_tardiness_sec = Column(BigInteger, nullable=True)
    objective_value = Column(Numeric(18, 4), nullable=True)
    job_count = Column(Integer, nullable=False, default=0)
    operation_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    jobs = relationship("CpsatJob", back_populates="run", cascade="all, delete-orphan")


class CpsatJob(Base):
    """注文ジョブ i（実行時スナップショット）"""

    __tablename__ = "cpsat_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(
        BigInteger, ForeignKey("cpsat_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_index = Column(Integer, nullable=False)
    source_type = Column(String(32), nullable=False)
    source_id = Column(Integer, nullable=True)
    order_no = Column(String(50), nullable=True)
    product_cd = Column(String(50), nullable=False)
    product_name = Column(String(100), nullable=True)
    q_target = Column(Integer, nullable=False)
    q_start = Column(Integer, nullable=False)
    lot_size = Column(Integer, nullable=False, default=0)
    lot_index = Column(Integer, nullable=False, default=1)
    lot_count = Column(Integer, nullable=False, default=1)
    due_at = Column(DateTime, nullable=True)
    due_sec = Column(Integer, nullable=True)
    last_op_end_sec = Column(Integer, nullable=True)
    tardiness_sec = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    run = relationship("CpsatRun", back_populates="jobs")
    operations = relationship("CpsatOperation", back_populates="job", cascade="all, delete-orphan")


class CpsatOperation(Base):
    """工程 j（S/E と割当結果）"""

    __tablename__ = "cpsat_operations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(
        BigInteger, ForeignKey("cpsat_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id = Column(
        BigInteger, ForeignKey("cpsat_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    op_index = Column(Integer, nullable=False)
    step_no = Column(Integer, nullable=False)
    process_cd = Column(String(20), nullable=False)
    process_name = Column(String(60), nullable=True)
    yield_percent = Column(Numeric(5, 2), nullable=False, default=100)
    wait_sec_after = Column(Integer, nullable=False, default=0)
    q_input = Column(Integer, nullable=False, default=0)
    q_output = Column(Integer, nullable=False, default=0)
    start_sec = Column(Integer, nullable=True)
    end_sec = Column(Integer, nullable=True)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    assigned_machine_cd = Column(String(50), nullable=True)
    assigned_machine_name = Column(String(100), nullable=True)
    processing_sec = Column(Integer, nullable=True)
    setup_sec = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    job = relationship("CpsatJob", back_populates="operations")
    candidates = relationship(
        "CpsatCandidate", back_populates="operation", cascade="all, delete-orphan"
    )


class CpsatCandidate(Base):
    """候補機ドメインと割当 X_{i,j,k}"""

    __tablename__ = "cpsat_candidates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(
        BigInteger, ForeignKey("cpsat_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    operation_id = Column(
        BigInteger,
        ForeignKey("cpsat_operations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    machine_cd = Column(String(50), nullable=False)
    machine_name = Column(String(100), nullable=True)
    process_time_sec = Column(Numeric(10, 2), nullable=False, default=0)
    setup_time_sec = Column(Integer, nullable=False, default=0)
    processing_sec = Column(Integer, nullable=False, default=0)
    is_assigned = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    operation = relationship("CpsatOperation", back_populates="candidates")

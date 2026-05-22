"""
累計単価スナップショット / 一括再計算 API

- `GET  /preview`              : 指定製品×ルートの累計単価を保存せずに計算
- `POST /`                     : 現在計算結果を保存（1 製品×ルート）
- `GET  /`                     : 履歴一覧（snapshot_id 単位）
- `GET  /latest`               : 最新1件（product_cd + route_cd）
- `GET  /{snapshot_id}`        : スナップショット詳細（行配列）
- `POST /recalc`               : 非同期一括再計算ジョブを起動
- `GET  /recalc/{job_id}`      : ジョブ進捗・結果
- `GET  /recalc`               : ジョブ一覧
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import (
    Product,
    ProductCostCumulativeSnapshot,
    ProductCostRecalcJob,
)
from app.modules.master.services.cumulative_cost_service import (
    compute_cumulative_rows,
    preload_all_masters,
)

router = APIRouter()

# マイグレーション未実行時の案内（1146 = テーブル不存在）
SCHEMA_MIGRATION_HINT = (
    "リポジトリルートで `py scripts/bootstrap_full_database.py` を実行するか、"
    "`backend/database/migrations/02_baseline_full_schema.sql` を対象データベースに適用してください。"
)


MODE_LITERAL = Literal["append_snapshot", "replace_current"]


# ---------------- Schemas ----------------


class PreviewQuery(BaseModel):
    product_cd: str
    route_cd: Optional[str] = None
    bom_header_id: Optional[int] = None


class SaveSnapshotIn(BaseModel):
    product_cd: str
    route_cd: Optional[str] = None
    bom_header_id: Optional[int] = None
    mode: MODE_LITERAL = "append_snapshot"
    remarks: Optional[str] = None


class RecalcItemIn(BaseModel):
    product_cd: str
    route_cd: Optional[str] = None
    bom_header_id: Optional[int] = None


class RecalcStartIn(BaseModel):
    scope: Literal["selected", "all"] = "selected"
    items: list[RecalcItemIn] = Field(default_factory=list)
    mode: MODE_LITERAL = "append_snapshot"


# ---------------- Helpers ----------------


def _is_undefined_table_error(exc: BaseException) -> bool:
    """MySQL 1146 等：スナップショット／ジョブテーブルが未作成のとき"""
    if isinstance(exc, ProgrammingError):
        for cand in (getattr(exc, "orig", None), getattr(exc, "__cause__", None)):
            if cand is not None and getattr(cand, "args", None) and cand.args and cand.args[0] == 1146:
                return True
        if "doesn't exist" in str(exc).lower() or "1146" in str(exc):
            return True
    return False


def _row_to_dict(r: ProductCostCumulativeSnapshot) -> dict[str, Any]:
    return {
        "id": int(r.id),
        "snapshot_id": r.snapshot_id,
        "product_cd": r.product_cd,
        "route_cd": r.route_cd,
        "bom_header_id": r.bom_header_id,
        "row_kind": r.row_kind,
        "row_order": int(r.row_order or 0),
        "step_no": r.step_no,
        "process_cd": r.process_cd,
        "stage_label": r.stage_label,
        "material_increment": float(r.material_increment or 0),
        "part_increment": float(r.part_increment or 0),
        "process_increment": float(r.process_increment or 0),
        "stage_increment": float(r.stage_increment or 0),
        "cumulative_unit_price": float(r.cumulative_unit_price or 0),
        "currency": r.currency,
        "is_latest": int(r.is_latest or 0),
        "source_job_id": r.source_job_id,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _job_to_dict(j: ProductCostRecalcJob) -> dict[str, Any]:
    result_ids: list[str] = []
    if j.result_snapshot_ids_json:
        try:
            result_ids = json.loads(j.result_snapshot_ids_json)
        except Exception:
            result_ids = []
    errors: list[dict[str, Any]] = []
    if j.error_log:
        try:
            errors = json.loads(j.error_log)
        except Exception:
            errors = []
    payload: dict[str, Any] = {}
    if j.payload_json:
        try:
            payload = json.loads(j.payload_json)
        except Exception:
            payload = {}
    total = int(j.total_items or 0)
    done = int(j.done_items or 0)
    pct = int(done * 100 / total) if total > 0 else (100 if j.status == "completed" else 0)
    return {
        "id": int(j.id),
        "status": j.status,
        "mode": j.mode,
        "scope": j.scope,
        "total_items": total,
        "done_items": done,
        "success_items": int(j.success_items or 0),
        "failed_items": int(j.failed_items or 0),
        "progress_percent": pct,
        "payload": payload,
        "errors": errors,
        "result_snapshot_ids": result_ids,
        "message": j.message,
        "created_by": j.created_by,
        "created_at": j.created_at.isoformat() if j.created_at else None,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "finished_at": j.finished_at.isoformat() if j.finished_at else None,
    }


async def _save_snapshot_rows(
    db: AsyncSession,
    *,
    product_cd: str,
    route_cd: str,
    bom_header_id: Optional[int],
    rows: list[dict[str, Any]],
    mode: str,
    username: Optional[str],
    source_job_id: Optional[int] = None,
) -> str:
    """1 製品×ルート分の行群を保存して snapshot_id を返す"""
    snap_id = str(uuid.uuid4())

    # 既存の is_latest をクリア
    await db.execute(
        update(ProductCostCumulativeSnapshot)
        .where(
            and_(
                ProductCostCumulativeSnapshot.product_cd == product_cd,
                ProductCostCumulativeSnapshot.route_cd == route_cd,
                ProductCostCumulativeSnapshot.is_latest == 1,
            )
        )
        .values(is_latest=0)
    )

    if mode == "replace_current":
        # 既存 active を全削除
        prev_q = select(ProductCostCumulativeSnapshot.snapshot_id).where(
            ProductCostCumulativeSnapshot.product_cd == product_cd,
            ProductCostCumulativeSnapshot.route_cd == route_cd,
        ).distinct()
        prev_ids = [r[0] for r in (await db.execute(prev_q)).all()]
        if prev_ids:
            from sqlalchemy import delete as sa_delete

            await db.execute(
                sa_delete(ProductCostCumulativeSnapshot).where(
                    ProductCostCumulativeSnapshot.snapshot_id.in_(prev_ids)
                )
            )

    for row in rows:
        r = ProductCostCumulativeSnapshot(
            snapshot_id=snap_id,
            product_cd=product_cd,
            route_cd=route_cd,
            bom_header_id=bom_header_id,
            row_kind=row["row_kind"],
            row_order=int(row.get("row_order") or 0),
            step_no=row.get("step_no"),
            process_cd=row.get("process_cd"),
            stage_label=row.get("stage_label"),
            material_increment=row["material_increment"],
            part_increment=row["part_increment"],
            process_increment=row["process_increment"],
            stage_increment=row["stage_increment"],
            cumulative_unit_price=row["cumulative_unit_price"],
            currency="JPY",
            is_latest=1,
            source_job_id=source_job_id,
            created_by=username,
        )
        db.add(r)
    await db.flush()
    return snap_id


# ---------------- Preview / Save ----------------


@router.get("/preview")
async def preview_snapshot(
    product_cd: str = Query(...),
    route_cd: Optional[str] = Query(None),
    bom_header_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """保存せずに累計単価の各段行を計算して返す（フロント computed の代替）"""
    result = await compute_cumulative_rows(
        db,
        product_cd=product_cd,
        route_cd=route_cd,
        bom_header_id=bom_header_id,
    )
    return {
        "success": True,
        "data": {
            "product_cd": result["product_cd"],
            "route_cd": result["route_cd"],
            "bom_header_id": result["bom_header_id"],
            "rows": [_normalize_row(r) for r in result["rows"]],
            "errors": result["errors"],
        },
    }


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    def _f(v: Any) -> float:
        if v is None:
            return 0.0
        if isinstance(v, Decimal):
            return float(v)
        return float(v)

    return {
        "row_kind": row["row_kind"],
        "row_order": int(row.get("row_order") or 0),
        "step_no": row.get("step_no"),
        "process_cd": row.get("process_cd"),
        "stage_label": row.get("stage_label"),
        "material_increment": _f(row["material_increment"]),
        "part_increment": _f(row["part_increment"]),
        "process_increment": _f(row["process_increment"]),
        "stage_increment": _f(row["stage_increment"]),
        "cumulative_unit_price": _f(row["cumulative_unit_price"]),
    }


@router.post("")
async def save_snapshot(
    body: SaveSnapshotIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """現在のマスタ・BOM・工程単価を使って 1 製品×ルートのスナップショットを保存"""
    result = await compute_cumulative_rows(
        db,
        product_cd=body.product_cd,
        route_cd=body.route_cd,
        bom_header_id=body.bom_header_id,
    )
    if not result["rows"] and result["errors"]:
        raise HTTPException(400, "; ".join(result["errors"]))
    try:
        snap_id = await _save_snapshot_rows(
            db,
            product_cd=result["product_cd"],
            route_cd=result["route_cd"],
            bom_header_id=result["bom_header_id"],
            rows=result["rows"],
            mode=body.mode,
            username=current_user.username if current_user else None,
        )
    except ProgrammingError as e:
        if _is_undefined_table_error(e):
            await db.rollback()
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                f"累計単価スナップショット用テーブルが未作成です。{SCHEMA_MIGRATION_HINT}",
            ) from e
        raise
    return {
        "success": True,
        "data": {
            "snapshot_id": snap_id,
            "product_cd": result["product_cd"],
            "route_cd": result["route_cd"],
            "bom_header_id": result["bom_header_id"],
            "rows": [_normalize_row(r) for r in result["rows"]],
            "errors": result["errors"],
        },
    }


# ---------------- List / Detail ----------------


@router.get("")
async def list_snapshots(
    product_cd: Optional[str] = Query(None),
    route_cd: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """スナップショット履歴（snapshot_id 単位に集約）"""
    conds = []
    if product_cd:
        conds.append(ProductCostCumulativeSnapshot.product_cd == product_cd)
    if route_cd:
        conds.append(ProductCostCumulativeSnapshot.route_cd == route_cd)

    group_q = (
        select(
            ProductCostCumulativeSnapshot.snapshot_id,
            ProductCostCumulativeSnapshot.product_cd,
            ProductCostCumulativeSnapshot.route_cd,
            ProductCostCumulativeSnapshot.bom_header_id,
            func.max(ProductCostCumulativeSnapshot.created_at).label("created_at"),
            func.max(ProductCostCumulativeSnapshot.created_by).label("created_by"),
            func.max(ProductCostCumulativeSnapshot.is_latest).label("is_latest"),
            func.max(ProductCostCumulativeSnapshot.cumulative_unit_price).label("max_cumulative"),
            func.count(ProductCostCumulativeSnapshot.id).label("row_count"),
        )
        .group_by(
            ProductCostCumulativeSnapshot.snapshot_id,
            ProductCostCumulativeSnapshot.product_cd,
            ProductCostCumulativeSnapshot.route_cd,
            ProductCostCumulativeSnapshot.bom_header_id,
        )
    )
    if conds:
        group_q = group_q.where(and_(*conds))

    try:
        total_sub = group_q.subquery()
        cnt = await db.execute(select(func.count()).select_from(total_sub))
        total = cnt.scalar() or 0

        group_q = group_q.order_by(func.max(ProductCostCumulativeSnapshot.created_at).desc())
        group_q = group_q.offset((page - 1) * limit).limit(limit)
        rows = (await db.execute(group_q)).all()
    except ProgrammingError as e:
        if _is_undefined_table_error(e):
            await db.rollback()
            return {
                "success": True,
                "data": {"list": [], "total": 0},
                "schema_pending": True,
                "detail": SCHEMA_MIGRATION_HINT,
            }
        raise
    items = []
    for snap_id, p_cd, r_cd, h_id, c_at, c_by, latest, max_cum, row_count in rows:
        items.append({
            "snapshot_id": snap_id,
            "product_cd": p_cd,
            "route_cd": r_cd,
            "bom_header_id": h_id,
            "created_at": c_at.isoformat() if c_at else None,
            "created_by": c_by,
            "is_latest": int(latest or 0),
            "cumulative_unit_price_final": float(max_cum or 0),
            "row_count": int(row_count or 0),
        })
    return {"success": True, "data": {"list": items, "total": total}}


@router.get("/latest")
async def get_latest_snapshot(
    product_cd: str = Query(...),
    route_cd: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """直近の最新スナップショット 1 件（行配列）"""
    q = (
        select(ProductCostCumulativeSnapshot)
        .where(
            ProductCostCumulativeSnapshot.product_cd == product_cd,
            ProductCostCumulativeSnapshot.route_cd == route_cd,
            ProductCostCumulativeSnapshot.is_latest == 1,
        )
        .order_by(ProductCostCumulativeSnapshot.row_order)
    )
    try:
        rows = (await db.execute(q)).scalars().all()
    except ProgrammingError as e:
        if _is_undefined_table_error(e):
            await db.rollback()
            return {"success": True, "data": None, "schema_pending": True, "detail": SCHEMA_MIGRATION_HINT}
        raise
    if not rows:
        return {"success": True, "data": None}
    return {
        "success": True,
        "data": {
            "snapshot_id": rows[0].snapshot_id,
            "product_cd": rows[0].product_cd,
            "route_cd": rows[0].route_cd,
            "bom_header_id": rows[0].bom_header_id,
            "created_at": rows[0].created_at.isoformat() if rows[0].created_at else None,
            "created_by": rows[0].created_by,
            "rows": [_row_to_dict(r) for r in rows],
        },
    }


# ---------------- 非同期 一括再計算（`/{snapshot_id}` より先に定義すること） ----------------


async def _resolve_job_items(
    db: AsyncSession, body: RecalcStartIn
) -> list[RecalcItemIn]:
    if body.scope == "all":
        # 全有効製品 × products.route_cd
        q = select(Product).where(
            Product.status == "active",
            Product.route_cd.isnot(None),
        )
        prods = (await db.execute(q)).scalars().all()
        items = []
        for p in prods:
            if not p.product_cd or not p.route_cd:
                continue
            items.append(RecalcItemIn(product_cd=p.product_cd, route_cd=p.route_cd))
        return items
    return body.items or []


@router.post("/recalc", status_code=status.HTTP_202_ACCEPTED)
async def start_recalc_job(
    body: RecalcStartIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """非同期一括再計算を起動。返却は `job_id`（完了状態は /recalc/{job_id} で確認）"""
    items = await _resolve_job_items(db, body)
    if not items:
        raise HTTPException(400, "対象製品が見つかりません")

    job = ProductCostRecalcJob(
        status="queued",
        mode=body.mode,
        scope=body.scope,
        total_items=len(items),
        done_items=0,
        success_items=0,
        failed_items=0,
        payload_json=json.dumps(
            {"items": [i.model_dump() for i in items], "mode": body.mode, "scope": body.scope},
            ensure_ascii=False,
        ),
        message="queued",
        created_by=current_user.username if current_user else None,
    )
    try:
        db.add(job)
        await db.flush()
        job_id = int(job.id)
    except ProgrammingError as e:
        if _is_undefined_table_error(e):
            await db.rollback()
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                f"再計算ジョブ用テーブルが未作成です。{SCHEMA_MIGRATION_HINT}",
            ) from e
        raise
    # セッションを必ずコミットさせてからワーカーを起動するため、
    # ここでは即座にタスクを投げるが、ワーカー側は独立セッションで再読込する
    username = current_user.username if current_user else None
    asyncio.create_task(_run_recalc_worker(job_id, username))
    return {"success": True, "data": {"job_id": job_id, "status": "queued", "total_items": len(items)}}


@router.get("/recalc/{job_id}")
async def get_recalc_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        j = await db.get(ProductCostRecalcJob, job_id)
    except ProgrammingError as e:
        if _is_undefined_table_error(e):
            await db.rollback()
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                f"再計算ジョブ用テーブルが未作成です。{SCHEMA_MIGRATION_HINT}",
            ) from e
        raise
    if not j:
        raise HTTPException(404, "ジョブが見つかりません")
    return {"success": True, "data": _job_to_dict(j)}


@router.get("/recalc")
async def list_recalc_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(ProductCostRecalcJob)
    if status_filter:
        q = q.where(ProductCostRecalcJob.status == status_filter)
    try:
        cnt = await db.execute(select(func.count()).select_from(q.subquery()))
        total = cnt.scalar() or 0
        q = q.order_by(ProductCostRecalcJob.id.desc())
        q = q.offset((page - 1) * limit).limit(limit)
        rows = (await db.execute(q)).scalars().all()
    except ProgrammingError as e:
        if _is_undefined_table_error(e):
            await db.rollback()
            return {
                "success": True,
                "data": {"list": [], "total": 0},
                "schema_pending": True,
                "detail": SCHEMA_MIGRATION_HINT,
            }
        raise
    return {
        "success": True,
        "data": {"list": [_job_to_dict(r) for r in rows], "total": total},
    }


@router.get("/{snapshot_id}")
async def get_snapshot_detail(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """snapshot_id 指定で行一覧を取得（UUID 形式を想定）"""
    q = (
        select(ProductCostCumulativeSnapshot)
        .where(ProductCostCumulativeSnapshot.snapshot_id == snapshot_id)
        .order_by(ProductCostCumulativeSnapshot.row_order)
    )
    try:
        rows = (await db.execute(q)).scalars().all()
    except ProgrammingError as e:
        if _is_undefined_table_error(e):
            await db.rollback()
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                f"累計単価スナップショット用テーブルが未作成です。{SCHEMA_MIGRATION_HINT}",
            ) from e
        raise
    if not rows:
        raise HTTPException(404, "スナップショットが見つかりません")
    head = rows[0]
    return {
        "success": True,
        "data": {
            "snapshot_id": snapshot_id,
            "product_cd": head.product_cd,
            "route_cd": head.route_cd,
            "bom_header_id": head.bom_header_id,
            "created_at": head.created_at.isoformat() if head.created_at else None,
            "created_by": head.created_by,
            "rows": [_row_to_dict(r) for r in rows],
        },
    }


# ---------------- Worker（独立セッション） ----------------


async def _run_recalc_worker(job_id: int, username: Optional[str]) -> None:
    """バックグラウンドで各アイテムを処理。

    1 アイテム = 1 製品×ルートのスナップショットを保存。
    マスタは一括プリロードして効率化。
    失敗しても他のアイテムに影響しない。
    """
    # ジョブをロード & running に遷移
    async with AsyncSessionLocal() as db:
        j = await db.get(ProductCostRecalcJob, job_id)
        if not j:
            return
        j.status = "running"
        j.started_at = datetime.now()
        j.message = "running"
        try:
            payload = json.loads(j.payload_json) if j.payload_json else {}
        except Exception:
            payload = {}
        items_raw: list[dict[str, Any]] = payload.get("items") or []
        mode: str = payload.get("mode") or j.mode or "append_snapshot"
        await db.commit()

    errors: list[dict[str, Any]] = []
    snapshot_ids: list[str] = []
    success_count = 0
    failed_count = 0
    done_count = 0

    # マスタ事前ロードは 1 回
    async with AsyncSessionLocal() as master_db:
        preloaded = await preload_all_masters(master_db)

    # 各アイテム処理（トランザクション独立）
    for idx, it in enumerate(items_raw):
        product_cd = (it.get("product_cd") or "").strip()
        route_cd = (it.get("route_cd") or None)
        bom_header_id = it.get("bom_header_id")
        try:
            async with AsyncSessionLocal() as db:
                result = await compute_cumulative_rows(
                    db,
                    product_cd=product_cd,
                    route_cd=route_cd,
                    bom_header_id=bom_header_id,
                    preloaded=preloaded,
                )
                if not result["rows"]:
                    raise RuntimeError(
                        "; ".join(result["errors"]) or "計算結果が空です"
                    )
                snap_id = await _save_snapshot_rows(
                    db,
                    product_cd=result["product_cd"],
                    route_cd=result["route_cd"],
                    bom_header_id=result["bom_header_id"],
                    rows=result["rows"],
                    mode=mode,
                    username=username,
                    source_job_id=job_id,
                )
                await db.commit()
                snapshot_ids.append(snap_id)
                success_count += 1
        except Exception as exc:
            failed_count += 1
            errors.append({
                "product_cd": product_cd,
                "route_cd": route_cd,
                "error": str(exc)[:400],
            })

        done_count += 1
        # 進捗反映（10件毎 or 最後）
        if done_count % 10 == 0 or done_count == len(items_raw):
            try:
                async with AsyncSessionLocal() as db:
                    j = await db.get(ProductCostRecalcJob, job_id)
                    if j:
                        j.done_items = done_count
                        j.success_items = success_count
                        j.failed_items = failed_count
                        j.result_snapshot_ids_json = json.dumps(snapshot_ids, ensure_ascii=False)
                        j.error_log = json.dumps(errors, ensure_ascii=False)
                        j.message = f"processing {done_count}/{len(items_raw)}"
                        await db.commit()
            except Exception:
                pass

    # 最終ステータス
    async with AsyncSessionLocal() as db:
        j = await db.get(ProductCostRecalcJob, job_id)
        if j:
            j.done_items = done_count
            j.success_items = success_count
            j.failed_items = failed_count
            j.result_snapshot_ids_json = json.dumps(snapshot_ids, ensure_ascii=False)
            j.error_log = json.dumps(errors, ensure_ascii=False)
            j.finished_at = datetime.now()
            if failed_count == 0:
                j.status = "completed"
                j.message = f"成功 {success_count} 件"
            elif success_count == 0:
                j.status = "failed"
                j.message = f"全件失敗 {failed_count} 件"
            else:
                j.status = "partial"
                j.message = f"成功 {success_count} / 失敗 {failed_count}"
            await db.commit()

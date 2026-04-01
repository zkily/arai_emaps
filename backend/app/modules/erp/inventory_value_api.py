"""
棚卸金額計算・照会 API
inventory_logs をもとに標準原価累計単価で金額を計算し、スナップショット保存
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import (
    ProductProcessUnitPrice,
    ProductRouteStep,
    Product,
    InventoryValueCalcRun,
    InventoryValueCalcDetail,
)

router = APIRouter(prefix="/inventory-value", tags=["棚卸金額"])


# ---------- Schemas ----------

class CalcRequest(BaseModel):
    start_date: str
    end_date: str
    process_cd: Optional[str] = None


# ---------- Helpers ----------

async def _get_cumulative_price(
    db: AsyncSession,
    product_cd: str,
    route_cd: str,
    step_no: int,
    target_date: date,
) -> tuple[Decimal, Optional[int]]:
    """指定ステップまでの累計単価を計算"""
    q = select(ProductProcessUnitPrice).where(
        ProductProcessUnitPrice.product_cd == product_cd,
        ProductProcessUnitPrice.route_cd == route_cd,
        ProductProcessUnitPrice.step_no <= step_no,
        ProductProcessUnitPrice.status == "active",
        (ProductProcessUnitPrice.effective_from.is_(None)) | (ProductProcessUnitPrice.effective_from <= target_date),
        (ProductProcessUnitPrice.effective_to.is_(None)) | (ProductProcessUnitPrice.effective_to > target_date),
    ).order_by(ProductProcessUnitPrice.step_no, ProductProcessUnitPrice.line_seq)
    rows = (await db.execute(q)).scalars().all()
    total = Decimal("0")
    last_id = None
    for r in rows:
        total += r.increment_unit_price or Decimal("0")
        last_id = r.id
    return total, last_id


async def _resolve_step_no(db: AsyncSession, product_cd: str, route_cd: str, process_cd: str) -> Optional[int]:
    """process_cd → step_no 解決"""
    q = select(ProductRouteStep.step_no).where(
        ProductRouteStep.product_cd == product_cd,
        ProductRouteStep.route_cd == route_cd,
        ProductRouteStep.process_cd == process_cd,
    ).limit(1)
    res = await db.execute(q)
    row = res.first()
    return row[0] if row else None


# ---------- 計算実行 ----------

@router.post("/calculate")
async def calculate_inventory_value(
    body: CalcRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """棚卸金額計算バッチ実行"""
    calc_date = date.today()
    start_dt = body.start_date
    end_dt = body.end_date

    run = InventoryValueCalcRun(
        calc_date=calc_date,
        start_date=start_dt,
        end_date=end_dt,
        process_cd=body.process_cd,
        status="running",
        executed_by=current_user.username if current_user else None,
    )
    db.add(run)
    await db.flush()

    log_sql = """
        SELECT id, product_cd, process_cd, item, quantity, log_date
        FROM inventory_logs
        WHERE log_date >= :start_date AND log_date <= :end_date
    """
    params: dict = {"start_date": start_dt, "end_date": end_dt}
    if body.process_cd:
        log_sql += " AND process_cd = :process_cd"
        params["process_cd"] = body.process_cd

    try:
        result = await db.execute(text(log_sql), params)
    except Exception:
        run.status = "failed"
        return {"success": False, "message": "inventory_logsテーブルの読み取りに失敗しました"}

    logs = result.fetchall()
    total_amount = Decimal("0")
    material_amount = Decimal("0")
    component_amount = Decimal("0")
    stay_amount = Decimal("0")
    total_rows = 0
    error_rows = 0

    product_cache: dict[str, Optional[Product]] = {}

    for log in logs:
        total_rows += 1
        log_id = log[0]
        p_cd = log[1]
        proc_cd = log[2]
        item_type = log[3]
        qty = Decimal(str(log[4])) if log[4] else Decimal("0")
        log_date = log[5]
        if isinstance(log_date, str):
            try:
                log_date = datetime.strptime(log_date[:10], "%Y-%m-%d").date()
            except Exception:
                log_date = calc_date

        if p_cd not in product_cache:
            pq = select(Product).where(Product.product_cd == p_cd)
            product_cache[p_cd] = (await db.execute(pq)).scalar_one_or_none()

        product = product_cache.get(p_cd)
        route_cd = product.route_cd if product and product.route_cd else None

        detail = InventoryValueCalcDetail(
            run_id=run.id,
            inventory_log_id=log_id,
            product_cd=p_cd,
            process_cd=proc_cd,
            item_type=item_type,
            quantity=qty,
        )

        if not route_cd:
            detail.error_code = "NO_ROUTE"
            detail.error_message = f"製品 {p_cd} にデフォルトルートが未設定"
            error_rows += 1
            db.add(detail)
            continue

        detail.route_cd = route_cd
        step_no = await _resolve_step_no(db, p_cd, route_cd, proc_cd) if proc_cd else None

        if proc_cd and step_no is None:
            detail.error_code = "NO_STEP"
            detail.error_message = f"工程 {proc_cd} がルート {route_cd} に存在しません"
            error_rows += 1
            db.add(detail)
            continue

        if step_no is None:
            max_step_q = select(func.max(ProductRouteStep.step_no)).where(
                ProductRouteStep.product_cd == p_cd,
                ProductRouteStep.route_cd == route_cd,
            )
            max_step = (await db.execute(max_step_q)).scalar()
            step_no = max_step or 9999

        detail.step_no = step_no
        cum_price, rule_id = await _get_cumulative_price(db, p_cd, route_cd, step_no, log_date)

        if cum_price == 0:
            detail.error_code = "NO_PRICE"
            detail.error_message = f"製品 {p_cd} ルート {route_cd} ステップ {step_no} の単価が未設定"
            error_rows += 1
            db.add(detail)
            continue

        amount = qty * cum_price
        detail.unit_price_snapshot = cum_price
        detail.amount = amount
        detail.price_rule_id = rule_id
        db.add(detail)

        if item_type and "材料" in item_type:
            material_amount += amount
        elif item_type and "部品" in item_type:
            component_amount += amount
        else:
            stay_amount += amount
        total_amount += amount

    run.total_amount = total_amount
    run.material_amount = material_amount
    run.component_amount = component_amount
    run.stay_amount = stay_amount
    run.total_rows = total_rows
    run.error_rows = error_rows
    run.status = "completed"

    return {
        "success": True,
        "data": {
            "run_id": run.id,
            "total_amount": float(total_amount),
            "material_amount": float(material_amount),
            "component_amount": float(component_amount),
            "stay_amount": float(stay_amount),
            "total_rows": total_rows,
            "error_rows": error_rows,
        },
    }


# ---------- 照会 ----------

@router.get("/summary")
async def get_value_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    process_cd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """最新計算結果のサマリー"""
    q = select(InventoryValueCalcRun).order_by(InventoryValueCalcRun.id.desc())
    if process_cd:
        q = q.where(InventoryValueCalcRun.process_cd == process_cd)
    q = q.limit(1)
    run = (await db.execute(q)).scalar_one_or_none()
    if not run:
        return {
            "success": True,
            "data": {
                "total": {"total_amount": 0, "material_amount": 0, "component_amount": 0, "stay_amount": 0},
                "byType": [],
                "byProcess": [],
            },
        }

    detail_by_type_q = (
        select(
            InventoryValueCalcDetail.item_type,
            func.sum(InventoryValueCalcDetail.amount),
            func.sum(InventoryValueCalcDetail.quantity),
            func.count(),
        )
        .where(InventoryValueCalcDetail.run_id == run.id, InventoryValueCalcDetail.error_code.is_(None))
        .group_by(InventoryValueCalcDetail.item_type)
    )
    by_type_rows = (await db.execute(detail_by_type_q)).fetchall()

    detail_by_process_q = (
        select(
            InventoryValueCalcDetail.process_cd,
            func.sum(InventoryValueCalcDetail.amount),
            func.count(),
        )
        .where(InventoryValueCalcDetail.run_id == run.id, InventoryValueCalcDetail.error_code.is_(None))
        .group_by(InventoryValueCalcDetail.process_cd)
    )
    by_process_rows = (await db.execute(detail_by_process_q)).fetchall()

    return {
        "success": True,
        "data": {
            "run_id": run.id,
            "calc_date": str(run.calc_date),
            "total": {
                "total_amount": float(run.total_amount),
                "material_amount": float(run.material_amount),
                "component_amount": float(run.component_amount),
                "stay_amount": float(run.stay_amount),
            },
            "total_rows": run.total_rows,
            "error_rows": run.error_rows,
            "byType": [
                {"item_type": r[0], "amount": float(r[1] or 0), "quantity": float(r[2] or 0), "count": r[3]}
                for r in by_type_rows
            ],
            "byProcess": [
                {"process_cd": r[0], "amount": float(r[1] or 0), "count": r[2]}
                for r in by_process_rows
            ],
        },
    }


@router.get("/details")
async def get_value_details(
    run_id: Optional[int] = Query(None),
    item_type: Optional[str] = Query(None),
    error_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """計算明細一覧"""
    if not run_id:
        latest = (
            await db.execute(select(InventoryValueCalcRun.id).order_by(InventoryValueCalcRun.id.desc()).limit(1))
        ).scalar()
        if not latest:
            return {"success": True, "data": {"list": [], "total": 0}}
        run_id = latest

    q = select(InventoryValueCalcDetail).where(InventoryValueCalcDetail.run_id == run_id)
    if item_type:
        q = q.where(InventoryValueCalcDetail.item_type == item_type)
    if error_only:
        q = q.where(InventoryValueCalcDetail.error_code.isnot(None))

    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.order_by(InventoryValueCalcDetail.id).offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(q)).scalars().all()

    return {
        "success": True,
        "data": {
            "list": [
                {
                    "id": r.id,
                    "inventory_log_id": r.inventory_log_id,
                    "product_cd": r.product_cd,
                    "process_cd": r.process_cd,
                    "item_type": r.item_type,
                    "quantity": float(r.quantity) if r.quantity else 0,
                    "route_cd": r.route_cd,
                    "step_no": r.step_no,
                    "unit_price": float(r.unit_price_snapshot) if r.unit_price_snapshot else None,
                    "amount": float(r.amount) if r.amount else None,
                    "error_code": r.error_code,
                    "error_message": r.error_message,
                }
                for r in rows
            ],
            "total": total,
        },
    }


@router.get("/runs")
async def get_calc_runs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """計算バッチ履歴"""
    q = select(InventoryValueCalcRun).order_by(InventoryValueCalcRun.id.desc())
    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return {
        "success": True,
        "data": {
            "list": [
                {
                    "id": r.id,
                    "calc_date": str(r.calc_date),
                    "start_date": str(r.start_date) if r.start_date else None,
                    "end_date": str(r.end_date) if r.end_date else None,
                    "process_cd": r.process_cd,
                    "total_amount": float(r.total_amount),
                    "total_rows": r.total_rows,
                    "error_rows": r.error_rows,
                    "status": r.status,
                    "executed_by": r.executed_by,
                    "created_at": str(r.created_at) if r.created_at else None,
                }
                for r in rows
            ],
            "total": total,
        },
    }


@router.get("/errors")
async def get_errors(
    run_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """エラー一覧（未定価・ルート未設定等）"""
    if not run_id:
        latest = (
            await db.execute(select(InventoryValueCalcRun.id).order_by(InventoryValueCalcRun.id.desc()).limit(1))
        ).scalar()
        if not latest:
            return {"success": True, "data": []}
        run_id = latest

    q = (
        select(InventoryValueCalcDetail)
        .where(InventoryValueCalcDetail.run_id == run_id, InventoryValueCalcDetail.error_code.isnot(None))
        .order_by(InventoryValueCalcDetail.error_code, InventoryValueCalcDetail.product_cd)
    )
    rows = (await db.execute(q)).scalars().all()
    return {
        "success": True,
        "data": [
            {
                "product_cd": r.product_cd,
                "process_cd": r.process_cd,
                "item_type": r.item_type,
                "error_code": r.error_code,
                "error_message": r.error_message,
            }
            for r in rows
        ],
    }

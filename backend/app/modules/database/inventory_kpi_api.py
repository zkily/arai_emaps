"""
在庫KPI API（設計書に基づく）
日数・回転日数は土日を除く稼働日ベース（_weekday_count）で統一。

- 在庫回転率: production_summarys のみ。回転日数 = 期間稼働日数 ÷ 回転率。
- 平均在庫日数: 現在在庫 ÷ 直近1稼働日あたり平均需要（期間forecast合計 ÷ 期間稼働日数）。
- 欠品アラート: 平均在庫日数 ≤ リードタイム＋安全余裕（1日平均も稼働日ベース）。
- 過剰アラート: 回転日数 = 期間稼働日数 ÷ 回転率。または 最終出荷からX日経過（shipping_items）。
- 発注点一覧: warehouse_inventory < safety_stock（日数計算なし）。
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Any

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.database.models import ProductionSummary
from app.modules.master.models import Product

logger = logging.getLogger(__name__)

router = APIRouter(tags=["在庫KPI"])


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _to_float(v: Any) -> float:
    """JSON 序列化用：Decimal/None を float に変換"""
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _to_int(v: Any) -> int:
    """JSON 序列化用：数量を int に変換"""
    if v is None:
        return 0
    if isinstance(v, Decimal):
        return int(v)
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _weekday_count(start_d: date, end_d: date) -> int:
    """期間内の稼働日数（土日を除く）。start_d 以上 end_d 以下をカウント。"""
    if start_d > end_d:
        start_d, end_d = end_d, start_d
    n = 0
    d = start_d
    while d <= end_d:
        # Python: Monday=0, Sunday=6 → 土曜=5, 日曜=6 を除外
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return max(1, n)


async def _get_allowed_product_cds(
    db: AsyncSession,
    product_cd: Optional[str] = None,
) -> list[str]:
    """
    在庫KPI用：products の product_type=量産品, status=active, destination_cd≠'N56' の product_cd 一覧。
    指定 product_cd がある場合はその1件が条件を満たすかだけ判定し、満たすなら [product_cd]、否則 []。
    """
    q = select(Product.product_cd).where(
        and_(
            Product.product_type == "量産品",
            Product.status == "active",
            or_(
                Product.destination_cd.is_(None),
                Product.destination_cd != "N56",
            ),
        )
    )
    if product_cd:
        q = q.where(Product.product_cd == product_cd)
    res = await db.execute(q)
    return [r.product_cd or "" for r in res.all() if r.product_cd]


# ---------- 在庫回転率 ----------
@router.get("/turnover")
async def get_inventory_turnover(
    start_date: Optional[str] = Query(None, description="期間開始 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="期間終了 YYYY-MM-DD"),
    period_type: Optional[str] = Query("month", description="month|quarter|year"),
    product_cd: Optional[str] = Query(None, description="品目（省略時は全体）"),
    by_amount: bool = Query(False, description="金額ベース（単価×数量）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    在庫回転率（production_summarys のみ）。
    期間中の forecast_quantity 合計 ÷ 期間平均在庫（期首・期末 warehouse_inventory の平均）。
    """
    try:
        return await _get_inventory_turnover_impl(
            start_date, end_date, period_type, product_cd, by_amount, db
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("inventory-kpi turnover error")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_inventory_turnover_impl(
    start_date: Optional[str],
    end_date: Optional[str],
    period_type: Optional[str],
    product_cd: Optional[str],
    by_amount: bool,
    db: AsyncSession,
):
    if not start_date or not end_date:
        end_d = date.today()
        if period_type == "year":
            start_d = end_d - timedelta(days=365)
        elif period_type == "quarter":
            start_d = end_d - timedelta(days=90)
        else:
            start_d = end_d - timedelta(days=30)
    else:
        start_d = _parse_date(start_date) or date.today()
        end_d = _parse_date(end_date) or date.today()
    if start_d > end_d:
        start_d, end_d = end_d, start_d

    allowed_product_cds = await _get_allowed_product_cds(db, product_cd)
    if not allowed_product_cds:
        return {
            "data": {
                "list": [],
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
                "by_amount": by_amount,
            },
        }

    # 期首・期末の日付（対象期間内の最初と最後の日付で production_summarys に存在する日を使う）
    # 品目別: 期首在庫・期末在庫・期間 forecast 合計
    q_base = (
        select(
            ProductionSummary.product_cd,
            ProductionSummary.product_name,
            func.sum(ProductionSummary.forecast_quantity).label("period_forecast"),
        )
        .where(
            and_(
                ProductionSummary.date >= start_d,
                ProductionSummary.date <= end_d,
                ProductionSummary.product_cd.isnot(None),
                ProductionSummary.product_cd != "",
                ProductionSummary.product_cd.in_(allowed_product_cds),
            )
        )
        .group_by(ProductionSummary.product_cd, ProductionSummary.product_name)
    )
    if product_cd:
        q_base = q_base.where(ProductionSummary.product_cd == product_cd)

    result = await db.execute(q_base)
    forecast_rows = result.all()

    # 期首在庫: 対象期間の先頭日付で品目別 warehouse_inventory
    q_opening = (
        select(
            ProductionSummary.product_cd,
            ProductionSummary.warehouse_inventory.label("opening"),
        )
        .where(
            and_(
                ProductionSummary.date == start_d,
                ProductionSummary.product_cd.isnot(None),
                ProductionSummary.product_cd != "",
                ProductionSummary.product_cd.in_(allowed_product_cds),
            )
        )
    )
    if product_cd:
        q_opening = q_opening.where(ProductionSummary.product_cd == product_cd)
    opening_result = await db.execute(q_opening)
    opening_map = {r.product_cd: (r.opening or 0) for r in opening_result.all()}

    # 期末在庫
    q_closing = (
        select(
            ProductionSummary.product_cd,
            ProductionSummary.warehouse_inventory.label("closing"),
        )
        .where(
            and_(
                ProductionSummary.date == end_d,
                ProductionSummary.product_cd.isnot(None),
                ProductionSummary.product_cd != "",
                ProductionSummary.product_cd.in_(allowed_product_cds),
            )
        )
    )
    if product_cd:
        q_closing = q_closing.where(ProductionSummary.product_cd == product_cd)
    closing_result = await db.execute(q_closing)
    closing_map = {r.product_cd: (r.closing or 0) for r in closing_result.all()}

    # 単価（金額ベース時）
    unit_prices: dict[str, float] = {}
    if by_amount:
        pq = select(Product.product_cd, Product.unit_price).where(
            and_(Product.product_cd.isnot(None), Product.product_cd.in_(allowed_product_cds))
        )
        if product_cd:
            pq = pq.where(Product.product_cd == product_cd)
        pr = await db.execute(pq)
        for r in pr.all():
            unit_prices[r.product_cd or ""] = _to_float(r.unit_price)

    # 回転日数計算用：土日を除いた期間の稼働日数
    period_days = _weekday_count(start_d, end_d)
    list_data = []
    for r in forecast_rows:
        pc = r.product_cd or ""
        period_fq = _to_float(r.period_forecast)
        opening = _to_int(opening_map.get(pc, 0))
        closing = _to_int(closing_map.get(pc, 0))
        avg_inv = (opening + closing) / 2.0 if (opening + closing) else 0.0
        if by_amount:
            price = unit_prices.get(pc, 0.0)
            period_demand = period_fq * price
            avg_inv_val = avg_inv * price
            turnover = (period_demand / avg_inv_val) if avg_inv_val else None
        else:
            turnover = (period_fq / avg_inv) if avg_inv else None
        # 回転日数 = 期間日数 ÷ 在庫回転率（「平均在庫が何日分で出るか」）
        turnover_days = (period_days / turnover) if turnover and turnover > 0 else None
        list_data.append({
            "product_cd": pc,
            "product_name": (r.product_name or ""),
            "period_forecast": int(period_fq),
            "opening_inventory": opening,
            "closing_inventory": closing,
            "avg_inventory": avg_inv,
            "turnover": round(turnover, 4) if turnover is not None else None,
            "turnover_days": round(turnover_days, 1) if turnover_days is not None else None,
        })

    return {
        "data": {
            "list": list_data,
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "by_amount": by_amount,
        },
    }


# ---------- 平均在庫日数 ----------
@router.get("/avg-inventory-days")
async def get_avg_inventory_days(
    as_of_date: Optional[str] = Query(None, description="基準日 YYYY-MM-DD（省略時は今日）"),
    recent_days: int = Query(30, ge=1, le=365, description="直近N日（1日あたり平均需要の算出用）"),
    product_cd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    平均在庫日数 = 現在在庫 ÷ 直近の1稼働日あたり平均需要。
    1稼働日あたり平均 = 直近N日間の forecast_quantity 合計 ÷ その期間の稼働日数（土日除く）。
    """
    base_d = _parse_date(as_of_date) or date.today()
    start_d = base_d - timedelta(days=recent_days)

    allowed_product_cds = await _get_allowed_product_cds(db, product_cd)
    if not allowed_product_cds:
        return {"data": {"list": [], "as_of_date": base_d.isoformat(), "recent_days": recent_days}}

    # 直近日の現在在庫（品目別、基準日以前で最も新しい日付の warehouse_inventory）
    # 基準日ちょうどまたはそれ以前の最新日を取得するため、サブクエリで「日付<=base_d の最大日」を品目別に取り、それと結合
    q_latest = (
        select(
            ProductionSummary.product_cd,
            ProductionSummary.product_name,
            func.max(ProductionSummary.date).label("latest_date"),
        )
        .where(
            and_(
                ProductionSummary.date <= base_d,
                ProductionSummary.product_cd.isnot(None),
                ProductionSummary.product_cd != "",
                ProductionSummary.product_cd.in_(allowed_product_cds),
            )
        )
        .group_by(ProductionSummary.product_cd, ProductionSummary.product_name)
    )
    if product_cd:
        q_latest = q_latest.where(ProductionSummary.product_cd == product_cd)
    res_latest = await db.execute(q_latest)
    latest_rows = res_latest.all()

    product_cds = [r.product_cd for r in latest_rows if r.product_cd]
    if not product_cds:
        return {"data": {"list": [], "as_of_date": base_d.isoformat(), "recent_days": recent_days}}

    # 直近日の在庫（product_cd, date -> warehouse_inventory）
    q_inv = select(
        ProductionSummary.product_cd,
        ProductionSummary.date,
        ProductionSummary.warehouse_inventory,
    ).where(
        and_(
            ProductionSummary.product_cd.in_(product_cds),
            ProductionSummary.date <= base_d,
        )
    )
    res_inv = await db.execute(q_inv)
    inv_by_pc_date = {}
    for row in res_inv.all():
        key = (row.product_cd, row.date)
        inv_by_pc_date[key] = row.warehouse_inventory or 0

    # 直近N日の forecast_quantity 合計（品目別）
    q_fc = (
        select(
            ProductionSummary.product_cd,
            func.sum(ProductionSummary.forecast_quantity).label("total_forecast"),
        )
        .where(
            and_(
                ProductionSummary.date >= start_d,
                ProductionSummary.date <= base_d,
                ProductionSummary.product_cd.in_(product_cds),
            )
        )
        .group_by(ProductionSummary.product_cd)
    )
    res_fc = await db.execute(q_fc)
    forecast_sum = {r.product_cd: (r.total_forecast or 0) for r in res_fc.all()}

    # 直近N日中の稼働日数（土日を除く）。1日あたり平均需要 = 期間forecast合計 ÷ 稼働日数
    work_days = _weekday_count(start_d, base_d)

    list_data = []
    for r in latest_rows:
        pc = r.product_cd or ""
        latest_d = r.latest_date
        current_inv = inv_by_pc_date.get((pc, latest_d), 0) if latest_d else 0
        total_fc = forecast_sum.get(pc, 0)
        avg_daily = total_fc / work_days if work_days else 0
        if avg_daily and avg_daily > 0:
            days_val = current_inv / avg_daily
        else:
            days_val = None  # 無限大 or 算出不可
        list_data.append({
            "product_cd": pc,
            "product_name": r.product_name or "",
            "current_inventory": current_inv,
            "avg_daily_demand": round(avg_daily, 2),
            "avg_inventory_days": round(days_val, 1) if days_val is not None else None,
            "latest_date": latest_d.isoformat() if latest_d else None,
        })

    return {
        "data": {
            "list": list_data,
            "as_of_date": base_d.isoformat(),
            "recent_days": recent_days,
        },
    }


# ---------- 欠品アラート ----------
@router.get("/shortage-alerts")
async def get_shortage_alerts(
    as_of_date: Optional[str] = Query(None),
    recent_days: int = Query(30, ge=1, le=365),
    safety_margin_days: int = Query(2, ge=0, description="安全余裕日数"),
    product_cd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    平均在庫日数 ≤ リードタイム＋安全余裕日数 の品目一覧。
    平均在庫日数は上記と同様 production_summarys のみで算出。リードタイムは products.lead_time。
    """
    base_d = _parse_date(as_of_date) or date.today()
    start_d = base_d - timedelta(days=recent_days)

    allowed_product_cds = await _get_allowed_product_cds(db, product_cd)
    if not allowed_product_cds:
        return {"data": {"list": [], "as_of_date": base_d.isoformat()}}

    q_latest = (
        select(
            ProductionSummary.product_cd,
            ProductionSummary.product_name,
            func.max(ProductionSummary.date).label("latest_date"),
        )
        .where(
            and_(
                ProductionSummary.date <= base_d,
                ProductionSummary.product_cd.isnot(None),
                ProductionSummary.product_cd != "",
                ProductionSummary.product_cd.in_(allowed_product_cds),
            )
        )
        .group_by(ProductionSummary.product_cd, ProductionSummary.product_name)
    )
    if product_cd:
        q_latest = q_latest.where(ProductionSummary.product_cd == product_cd)
    res_latest = await db.execute(q_latest)
    latest_rows = res_latest.all()
    product_cds = [r.product_cd for r in latest_rows if r.product_cd]
    if not product_cds:
        return {"data": {"list": [], "as_of_date": base_d.isoformat()}}

    q_inv = select(
        ProductionSummary.product_cd,
        ProductionSummary.date,
        ProductionSummary.warehouse_inventory,
    ).where(
        and_(ProductionSummary.product_cd.in_(product_cds), ProductionSummary.date <= base_d)
    )
    res_inv = await db.execute(q_inv)
    inv_by_pc_date = {(row.product_cd, row.date): (row.warehouse_inventory or 0) for row in res_inv.all()}

    q_fc = (
        select(
            ProductionSummary.product_cd,
            func.sum(ProductionSummary.forecast_quantity).label("total_forecast"),
        )
        .where(
            and_(
                ProductionSummary.date >= start_d,
                ProductionSummary.date <= base_d,
                ProductionSummary.product_cd.in_(product_cds),
            )
        )
        .group_by(ProductionSummary.product_cd)
    )
    res_fc = await db.execute(q_fc)
    forecast_sum = {r.product_cd: (r.total_forecast or 0) for r in res_fc.all()}

    # 直近N日中の稼働日数（土日を除く）。1日あたり平均需要 = 期間forecast合計 ÷ 稼働日数
    work_days = _weekday_count(start_d, base_d)

    # products から lead_time, safety_days
    q_pr = select(Product.product_cd, Product.lead_time, Product.safety_days).where(
        Product.product_cd.in_(product_cds)
    )
    res_pr = await db.execute(q_pr)
    product_master = {}
    for row in res_pr.all():
        product_master[row.product_cd or ""] = {
            "lead_time": row.lead_time if row.lead_time is not None else 0,
            "safety_days": row.safety_days if row.safety_days is not None else 0,
        }

    list_data = []
    for r in latest_rows:
        pc = r.product_cd or ""
        latest_d = r.latest_date
        current_inv = inv_by_pc_date.get((pc, latest_d), 0) if latest_d else 0
        total_fc = forecast_sum.get(pc, 0)
        avg_daily = total_fc / work_days if work_days else 0
        if avg_daily and avg_daily > 0:
            avg_days_val = current_inv / avg_daily
        else:
            avg_days_val = None
        pm = product_master.get(pc, {})
        lead_time = pm.get("lead_time") or 0
        threshold = lead_time + safety_margin_days
        is_shortage = avg_days_val is not None and avg_days_val <= threshold
        if not is_shortage:
            continue
        list_data.append({
            "product_cd": pc,
            "product_name": r.product_name or "",
            "current_inventory": current_inv,
            "avg_inventory_days": round(avg_days_val, 1) if avg_days_val is not None else None,
            "lead_time": lead_time,
            "safety_margin_days": safety_margin_days,
            "threshold_days": threshold,
        })

    return {"data": {"list": list_data, "as_of_date": base_d.isoformat()}}


# ---------- 過剰アラート ----------
@router.get("/overstock-alerts")
async def get_overstock_alerts(
    as_of_date: Optional[str] = Query(None),
    turnover_period_days: int = Query(365, ge=1),
    max_turnover_days: Optional[float] = Query(90, description="許容限界日数（回転日数がこれを超えると過剰）"),
    days_since_ship: Optional[int] = Query(60, description="最終出荷から何日で滞留とするか"),
    product_cd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    1) 在庫回転日数 ≥ 許容限界日数
    2) 最終出荷日から X 日以上経過（shipping_items の MAX(shipping_date) を品目別に取得）
    """
    try:
        return await _get_overstock_alerts_impl(
            as_of_date, turnover_period_days, max_turnover_days, days_since_ship, product_cd, db
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("inventory-kpi overstock-alerts error")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_overstock_alerts_impl(
    as_of_date: Optional[str],
    turnover_period_days: int,
    max_turnover_days: Optional[float],
    days_since_ship: Optional[int],
    product_cd: Optional[str],
    db: AsyncSession,
):
    base_d = _parse_date(as_of_date) or date.today()
    start_d = base_d - timedelta(days=turnover_period_days)

    allowed_product_cds = await _get_allowed_product_cds(db, product_cd)
    if not allowed_product_cds:
        return {
            "data": {
                "list": [],
                "as_of_date": base_d.isoformat(),
                "max_turnover_days": float(max_turnover_days) if max_turnover_days is not None else None,
                "days_since_ship": days_since_ship,
            },
        }

    # 回転率用: 期間 forecast 合計、期首・期末在庫
    q_fc = (
        select(
            ProductionSummary.product_cd,
            ProductionSummary.product_name,
            func.sum(ProductionSummary.forecast_quantity).label("period_forecast"),
        )
        .where(
            and_(
                ProductionSummary.date >= start_d,
                ProductionSummary.date <= base_d,
                ProductionSummary.product_cd.isnot(None),
                ProductionSummary.product_cd != "",
                ProductionSummary.product_cd.in_(allowed_product_cds),
            )
        )
        .group_by(ProductionSummary.product_cd, ProductionSummary.product_name)
    )
    if product_cd:
        q_fc = q_fc.where(ProductionSummary.product_cd == product_cd)
    res_fc = await db.execute(q_fc)
    forecast_rows = res_fc.all()

    product_cds = list({r.product_cd for r in forecast_rows if r.product_cd})
    opening_map = {}
    closing_map = {}
    if product_cds:
        q_op = select(ProductionSummary.product_cd, ProductionSummary.warehouse_inventory).where(
            and_(ProductionSummary.date == start_d, ProductionSummary.product_cd.in_(product_cds))
        )
        for row in (await db.execute(q_op)).all():
            opening_map[row.product_cd or ""] = row.warehouse_inventory or 0
        q_cl = select(ProductionSummary.product_cd, ProductionSummary.warehouse_inventory).where(
            and_(ProductionSummary.date == base_d, ProductionSummary.product_cd.in_(product_cds))
        )
        for row in (await db.execute(q_cl)).all():
            closing_map[row.product_cd or ""] = row.warehouse_inventory or 0

    # 最終出荷日（shipping_items）- 失敗時は last_ship_map を空にして続行
    last_ship_map: dict[str, Any] = {}
    if product_cds and days_since_ship is not None:
        try:
            placeholders = ", ".join([f":pc_{i}" for i in range(len(product_cds))])
            sql = text(
                f"SELECT product_cd, MAX(shipping_date) AS last_ship FROM shipping_items "
                f"WHERE product_cd IN ({placeholders}) AND shipping_date IS NOT NULL GROUP BY product_cd"
            )
            params = {f"pc_{i}": product_cds[i] for i in range(len(product_cds))}
            res_ship = await db.execute(sql, params)
            for row in res_ship.mappings().all():
                last_ship_map[row["product_cd"] or ""] = row["last_ship"]
        except Exception as e:
            logger.warning("overstock-alerts: shipping_items query failed: %s", e)

    # 期間の稼働日数（土日を除く）。回転日数 = 稼働日数 ÷ 回転率（在庫回転率APIと同一口径）
    period_work_days = _weekday_count(start_d, base_d)

    list_data = []
    for r in forecast_rows:
        pc = r.product_cd or ""
        period_fq = _to_float(r.period_forecast)
        opening = _to_int(opening_map.get(pc, 0))
        closing = _to_int(closing_map.get(pc, 0))
        avg_inv = (opening + closing) / 2.0 if (opening + closing) else 0.0
        turnover = (period_fq / avg_inv) if avg_inv else None
        turnover_days = (period_work_days / turnover) if turnover and turnover > 0 else None

        over_by_turnover = (
            max_turnover_days is not None
            and turnover_days is not None
            and turnover_days >= max_turnover_days
        )
        last_ship = last_ship_map.get(pc)
        days_ago: Optional[int] = None
        if last_ship is not None:
            d = last_ship.date() if hasattr(last_ship, "date") else last_ship
            days_ago = (base_d - d).days
        over_by_ship = (
            days_since_ship is not None
            and days_ago is not None
            and days_ago >= days_since_ship
        )
        if not over_by_turnover and not over_by_ship:
            continue
        # JSON 序列化可能な型に統一
        last_ship_date_str: Optional[str] = None
        if last_ship is not None:
            last_ship_date_str = last_ship.isoformat()[:10] if hasattr(last_ship, "isoformat") else str(last_ship)
        list_data.append({
            "product_cd": pc,
            "product_name": (r.product_name or ""),
            "current_inventory": _to_int(closing_map.get(pc, 0)),
            "turnover": round(float(turnover), 4) if turnover is not None else None,
            "turnover_days": round(float(turnover_days), 1) if turnover_days is not None else None,
            "last_ship_date": last_ship_date_str,
            "days_since_ship": days_ago,
            "over_by_turnover": over_by_turnover,
            "over_by_ship": over_by_ship,
        })

    return {
        "data": {
            "list": list_data,
            "as_of_date": base_d.isoformat(),
            "max_turnover_days": float(max_turnover_days) if max_turnover_days is not None else None,
            "days_since_ship": days_since_ship,
        },
    }


# ---------- 発注点一覧（warehouse_inventory < safety_stock） ----------
@router.get("/reorder-point")
async def get_reorder_point_list(
    as_of_date: Optional[str] = Query(None, description="基準日（省略時は今日）"),
    product_cd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    production_summarys のみ。直近日の warehouse_inventory が safety_stock を下回る品目を「発注点以下」として一覧。
    """
    base_d = _parse_date(as_of_date) or date.today()

    allowed_product_cds = await _get_allowed_product_cds(db, product_cd)
    if not allowed_product_cds:
        return {"data": {"list": [], "as_of_date": base_d.isoformat()}}

    # 品目別に基準日以前で最も新しい日付を取得
    q_latest = (
        select(
            ProductionSummary.product_cd,
            ProductionSummary.product_name,
            func.max(ProductionSummary.date).label("latest_date"),
        )
        .where(
            and_(
                ProductionSummary.date <= base_d,
                ProductionSummary.product_cd.isnot(None),
                ProductionSummary.product_cd != "",
                ProductionSummary.product_cd.in_(allowed_product_cds),
            )
        )
        .group_by(ProductionSummary.product_cd, ProductionSummary.product_name)
    )
    if product_cd:
        q_latest = q_latest.where(ProductionSummary.product_cd == product_cd)
    res_latest = await db.execute(q_latest)
    latest_rows = res_latest.all()
    product_cds = [r.product_cd for r in latest_rows if r.product_cd]
    if not product_cds:
        return {"data": {"list": [], "as_of_date": base_d.isoformat()}}

    # 直近日の warehouse_inventory, safety_stock を取得（product_cd + date で結合）
    q_ps = select(
        ProductionSummary.product_cd,
        ProductionSummary.product_name,
        ProductionSummary.date,
        ProductionSummary.warehouse_inventory,
        ProductionSummary.safety_stock,
    ).where(
        and_(
            ProductionSummary.product_cd.in_(product_cds),
            ProductionSummary.date <= base_d,
        )
    )
    res_ps = await db.execute(q_ps)
    rows_ps = res_ps.all()

    # 品目ごとの最新日のみを残す
    by_product = {}
    for row in rows_ps:
        pc = row.product_cd or ""
        d = row.date
        if pc not in by_product or (by_product[pc]["date"] and d and d > by_product[pc]["date"]):
            by_product[pc] = {
                "product_cd": pc,
                "product_name": row.product_name or "",
                "date": d,
                "warehouse_inventory": row.warehouse_inventory or 0,
                "safety_stock": row.safety_stock or 0,
            }

    list_data = []
    for pc, v in by_product.items():
        if v["warehouse_inventory"] >= v["safety_stock"]:
            continue
        list_data.append({
            "product_cd": v["product_cd"],
            "product_name": v["product_name"],
            "latest_date": v["date"].isoformat() if v["date"] else None,
            "warehouse_inventory": v["warehouse_inventory"],
            "safety_stock": v["safety_stock"],
            "below_reorder": True,
        })

    return {"data": {"list": list_data, "as_of_date": base_d.isoformat()}}

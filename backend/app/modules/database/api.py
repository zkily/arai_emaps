"""
production_summarys API（一覧・製品リスト・データ生成）
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, tuple_
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.database.models import ProductionSummary
from app.modules.master.models import Product

router = APIRouter(prefix="/production-summarys", tags=["production-summarys"])

DAY_OF_WEEK_JA = ("月", "火", "水", "木", "金", "土", "日")


def _row_to_dict(row) -> dict:
    """ORM 行を辞書に（日付は文字列）"""
    d = {}
    for c in row.__table__.columns:
        v = getattr(row, c.name)
        if hasattr(v, "isoformat"):
            d[c.name] = v.isoformat() if v else None
        else:
            d[c.name] = v
    return d


@router.get("")
async def get_production_summarys_list(
    page: int = Query(1, ge=1, description="ページ"),
    limit: int = Query(150, ge=1, le=500, description="件数"),
    startDate: Optional[str] = Query(None, description="開始日 YYYY-MM-DD"),
    endDate: Optional[str] = Query(None, description="終了日 YYYY-MM-DD"),
    productCd: Optional[str] = Query(None, description="製品CD"),
    keyword: Optional[str] = Query(None, description="製品名キーワード"),
    sortBy: Optional[str] = Query("product_name", description="ソート項目"),
    sortOrder: Optional[str] = Query("ASC", description="ASC/DESC"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産サマリー一覧（ページネーション）"""
    q = select(ProductionSummary)
    count_q = select(func.count()).select_from(ProductionSummary)
    conds = []
    if startDate:
        conds.append(ProductionSummary.date >= startDate)
    if endDate:
        conds.append(ProductionSummary.date <= endDate)
    if productCd:
        conds.append(ProductionSummary.product_cd == productCd)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        conds.append(
            or_(
                ProductionSummary.product_name.ilike(k),
                ProductionSummary.product_cd.ilike(k),
            )
        )
    if conds:
        q = q.where(and_(*conds))
        count_q = count_q.where(and_(*conds))
    # ソート
    sort_col = getattr(ProductionSummary, sortBy, None) or ProductionSummary.product_name
    if sortOrder == "DESC":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())
    # ページネーション
    offset = (page - 1) * limit
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    list_data = [_row_to_dict(r) for r in rows]
    return {
        "data": {
            "list": list_data,
            "pagination": {"total": total, "page": page, "limit": limit},
        }
    }


@router.get("/products")
async def get_production_summarys_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品一覧（product_cd + product_name の重複なし）"""
    q = (
        select(ProductionSummary.product_cd, ProductionSummary.product_name)
        .distinct()
        .where(
            ProductionSummary.product_cd.isnot(None),
            ProductionSummary.product_cd != "",
        )
        .order_by(ProductionSummary.product_name, ProductionSummary.product_cd)
    )
    result = await db.execute(q)
    rows = result.all()
    data = [
        {"product_cd": r.product_cd or "", "product_name": r.product_name or ""}
        for r in rows
    ]
    return {"data": data}


class GenerateBody(BaseModel):
    startDate: str
    endDate: str


@router.post("/generate")
async def generate_production_summarys(
    body: GenerateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定期間で production_summarys を生成。既存の (date, product_cd) はスキップ。
    製品は products テーブル（status='active'）から取得。
    """
    try:
        start = date.fromisoformat(body.startDate)
        end = date.fromisoformat(body.endDate)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効な日付形式（YYYY-MM-DD）")
    if start > end:
        raise HTTPException(status_code=400, detail="開始日は終了日以前にしてください")

    # 製品一覧（products テーブル）
    # 条件: product_cd 末尾が '1'、product_name に '加工'・'·加工'・'アーチ' を含まない、
    #       status が 'inactive' でない、product_type が '量産品'
    try:
        product_query = (
            select(Product)
            .where(Product.product_cd.isnot(None))
            .where(Product.product_cd.endswith("1"))
            .where(Product.status != "inactive")
            .where(Product.product_type == "量産品")
            .where(
                or_(
                    Product.product_name.is_(None),
                    and_(
                        ~Product.product_name.like("%加工%"),
                        ~Product.product_name.like("%·加工%"),
                        ~Product.product_name.like("%アーチ%"),
                    ),
                )
            )
        )
        product_result = await db.execute(product_query)
        products = product_result.scalars().all()
    except Exception:
        products = []

    if not products:
        return {"success": True, "message": "対象製品がありません", "inserted": 0, "skipped": 0}

    # 既存 (date, product_cd) を取得
    existing_query = select(ProductionSummary.date, ProductionSummary.product_cd).where(
        and_(
            ProductionSummary.date >= start,
            ProductionSummary.date <= end,
        )
    )
    existing_result = await db.execute(existing_query)
    existing_set = {(r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date), r.product_cd) for r in existing_result.all()}

    inserted = 0
    current = start
    while current <= end:
        dow = DAY_OF_WEEK_JA[current.weekday()]
        for p in products:
            key = (current.isoformat(), p.product_cd)
            if key in existing_set:
                continue
            row = ProductionSummary(
                route_cd=p.route_cd or None,
                product_cd=p.product_cd,
                product_name=p.product_name or None,
                date=current,
                day_of_week=dow,
                order_quantity=0,
                forecast_quantity=0,
            )
            db.add(row)
            inserted += 1
            existing_set.add(key)
        current += timedelta(days=1)

    await db.commit()
    return {"success": True, "message": "データ生成が完了しました", "inserted": inserted, "skipped": 0}


class UpdateFromOrderDailyBody(BaseModel):
    updateMode: str = "changed"  # 'all' | 'changed' | 'recent'
    days: int = 30
    clearBeforeUpdate: bool = False


@router.post("/update-from-order-daily")
async def update_production_summarys_from_order_daily(
    body: UpdateFromOrderDailyBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    order_daily の受注データから production_summarys の
    forecast_quantity / order_quantity を更新する。
    """
    from time import perf_counter
    from datetime import datetime, timedelta as _timedelta
    from app.modules.erp.models import OrderDaily

    start_time = perf_counter()

    mode = body.updateMode or "changed"
    if mode not in {"all", "changed", "recent"}:
        raise HTTPException(status_code=400, detail="updateMode は 'all' | 'changed' | 'recent' のいずれかを指定してください")

    days = body.days or 30
    if days <= 0:
        days = 30

    # 対象期間（recent モード用）
    recent_start_date = None
    if mode == "recent":
        today = datetime.utcnow().date()
        recent_start_date = today - _timedelta(days=days - 1)

    # order_daily から集計
    od = OrderDaily
    # product_cd の末尾を '1' にそろえる
    normalized_product_cd = func.concat(func.substr(od.product_cd, 1, func.length(od.product_cd) - 1), "1")

    agg_query = (
        select(
            normalized_product_cd.label("product_cd"),
            od.date.label("date"),
            func.sum(func.coalesce(od.forecast_units, 0)).label("forecast_quantity"),
            func.sum(func.coalesce(od.confirmed_units, 0)).label("order_quantity"),
        )
        .where(od.product_cd.isnot(None), od.product_cd != "")
    )
    if mode == "recent" and recent_start_date is not None:
        agg_query = agg_query.where(od.date >= recent_start_date)

    agg_query = agg_query.group_by(normalized_product_cd, od.date)

    agg_result = await db.execute(agg_query)
    agg_rows = agg_result.all()

    total = len(agg_rows)
    if total == 0:
        elapsed = perf_counter() - start_time
        return {
            "code": 200,
            "data": {
                "updated": 0,
                "skipped": 0,
                "unchanged": 0,
                "total": 0,
                "elapsedTime": round(elapsed, 2),
            },
            "message": "更新対象となる受注データがありませんでした。",
        }

    # 更新前クリア
    if body.clearBeforeUpdate:
        clear_stmt = update(ProductionSummary).values(order_quantity=0, forecast_quantity=0)
        if mode == "recent" and recent_start_date is not None:
            clear_stmt = clear_stmt.where(ProductionSummary.date >= recent_start_date)
        await db.execute(clear_stmt)

    # 既存の production_summarys を一括取得
    key_list = [(r.product_cd, r.date) for r in agg_rows]
    existing_stmt = select(ProductionSummary).where(
        tuple_(ProductionSummary.product_cd, ProductionSummary.date).in_(key_list)
    )
    existing_result = await db.execute(existing_stmt)
    existing_rows = existing_result.scalars().all()
    existing_map = {(r.product_cd, r.date): r for r in existing_rows}

    updated = 0
    skipped = 0
    unchanged = 0

    for r in agg_rows:
        key = (r.product_cd, r.date)
        ps = existing_map.get(key)
        if not ps:
            # production_summarys 側に存在しない (product_cd, date) はスキップ
            skipped += 1
            continue

        new_forecast = int(r.forecast_quantity or 0)
        new_order = int(r.order_quantity or 0)

        if mode == "changed":
            if ps.forecast_quantity == new_forecast and ps.order_quantity == new_order:
                unchanged += 1
                continue

        ps.forecast_quantity = new_forecast
        ps.order_quantity = new_order
        updated += 1

    await db.commit()

    elapsed = perf_counter() - start_time
    message = f"{updated}件のデータを更新しました（変更なし {unchanged} 件 / スキップ {skipped} 件）"

    return {
        "code": 200,
        "data": {
            "updated": updated,
            "skipped": skipped,
            "unchanged": unchanged,
            "total": total,
            "elapsedTime": round(elapsed, 2),
        },
        "message": message,
    }

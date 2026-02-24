"""
受注バッチ API
- GET /products: 納入先+年月で製品一覧（order_monthly と LEFT JOIN で forecast_units）
- GET /check-combination-exists: 納入先名・製品名・年月の組み合わせが既存か
- POST /batch-create-monthly: 一括登録（INSERT IGNORE 相当）
- POST /generate-daily: 日受注リスト生成（量産品のみ）
- PATCH /daily/update-shipping-no: 日订单に出荷Noを書戻し（产品+納入先+出荷日で定位、未填写の行のみ更新）
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from calendar import monthrange

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Product, ProductRouteStep
from app.modules.erp import models as erp_models
from app.modules.order.generate_daily_service import run_generate_daily

router = APIRouter()


def _monthly_summary_base_where(om, year, month, destination_cd, keyword):
    """月別サマリ・リスト共通の where 条件（product_name に「加工」を含む行は除外）"""
    cond = and_(
        (om.product_name.is_(None)) | (~om.product_name.like("%加工%")),
    )
    if year is not None:
        cond = and_(cond, om.year == year)
    if month is not None:
        cond = and_(cond, om.month == month)
    if destination_cd:
        cond = and_(cond, om.destination_cd == destination_cd)
    if keyword:
        k = f"%{keyword}%"
        cond = and_(
            cond,
            or_(
                om.destination_name.like(k),
                om.product_name.like(k),
                om.product_cd.like(k),
            ),
        )
    return cond


# ---------- GET /products ----------
@router.get("/products")
async def get_products_by_destination(
    destination_cd: str = Query(..., description="納入先CD"),
    year: int = Query(..., description="年"),
    month: int = Query(..., ge=1, le=12, description="月"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    納入先+年月で製品一覧を取得。
    products を destination_cd で絞り、order_monthly を LEFT JOIN して該当年月の forecast_units を取得（無い場合は 0）。
    """
    # products と order_monthly を LEFT JOIN（同一 destination_cd, product_cd, year, month）
    om = erp_models.OrderMonthly
    q = (
        select(
            Product.product_cd,
            Product.product_name,
            Product.product_type,
            func.coalesce(om.forecast_units, 0).label("forecast_units"),
        )
        .select_from(Product)
        .outerjoin(
            om,
            and_(
                Product.product_cd == om.product_cd,
                Product.destination_cd == om.destination_cd,
                om.year == year,
                om.month == month,
            ),
        )
        .where(Product.destination_cd == destination_cd)
        .where(Product.status == "active")
        .order_by(Product.product_cd)
    )
    result = await db.execute(q)
    rows = result.all()
    data = [
        {
            "product_cd": r.product_cd,
            "product_name": r.product_name or "",
            "product_type": r.product_type or "量産品",
            "forecast_units": int(r.forecast_units) if r.forecast_units is not None else 0,
        }
        for r in rows
    ]
    return {"success": True, "data": data}


# ---------- GET /check-exists ----------
@router.get("/check-exists")
async def check_monthly_order_exists(
    order_id: str = Query(..., description="月次注文ID（monthlyOrderId）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    order_monthly に指定 order_id が存在するか。
    返却: { exists: true/false, id?: number, order_id?: string }
    """
    om = erp_models.OrderMonthly
    q = select(om.id, om.order_id).where(om.order_id == order_id).limit(1)
    result = await db.execute(q)
    row = result.one_or_none()
    if row is None:
        return {"exists": False}
    return {"exists": True, "id": row.id, "order_id": row.order_id}


# ---------- POST /monthly/add ----------
@router.post("/monthly/add")
async def add_monthly_order(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    月次注文を作成する（日次追加時の自動作成用）。
    既に同一 order_id が存在する場合はスキップして既存を返す。
    """
    order_id = body.get("order_id", "")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id は必須です")

    # 既存チェック
    om = erp_models.OrderMonthly
    existing_q = select(om).where(om.order_id == order_id).limit(1)
    existing_result = await db.execute(existing_q)
    existing_row = existing_result.scalar_one_or_none()
    if existing_row:
        return {"ok": True, "order_id": existing_row.order_id, "created": False}

    row = erp_models.OrderMonthly(
        order_id=order_id,
        destination_cd=body.get("destination_cd", ""),
        destination_name=body.get("destination_name", ""),
        year=int(body.get("year", 0)),
        month=int(body.get("month", 0)),
        product_cd=body.get("product_cd", ""),
        product_name=body.get("product_name", ""),
        product_alias=body.get("product_alias", ""),
        product_type=body.get("product_type", "量産品"),
        forecast_units=int(body.get("forecast_units", 0)),
        forecast_total_units=int(body.get("forecast_total_units", 0)),
        forecast_diff=0,
    )
    try:
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return {"ok": True, "order_id": row.order_id, "created": True}
    except IntegrityError:
        await db.rollback()
        return {"ok": True, "order_id": order_id, "created": False}


# ---------- GET /check-combination-exists ----------
@router.get("/check-combination-exists")
async def check_combination_exists(
    destination_name: str = Query(..., description="納入先名"),
    product_name: str = Query(..., description="製品名"),
    year: int = Query(..., description="年"),
    month: int = Query(..., ge=1, le=12, description="月"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    order_monthly に同一 destination_name, product_name, year, month が存在するか。
    存在する場合 id, forecast_units を返し、数量更新に利用する。
    返却: { exists: true/false, id?: number, forecast_units?: number }
    """
    om = erp_models.OrderMonthly
    q = (
        select(om.id, om.forecast_units)
        .where(
            and_(
                om.destination_name == destination_name,
                om.product_name == product_name,
                om.year == year,
                om.month == month,
            )
        )
        .limit(1)
    )
    result = await db.execute(q)
    row = result.one_or_none()
    if row is None:
        return {"exists": False}
    return {"exists": True, "id": row.id, "forecast_units": row.forecast_units or 0}


# ---------- GET /monthly/summary ----------
@router.get("/monthly/summary")
async def get_monthly_summary(
    year: Optional[int] = Query(None, description="年"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月"),
    destination_cd: Optional[str] = Query(None, description="納入先CD"),
    keyword: Optional[str] = Query(None, description="製品・納入先検索"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    月別受注の合計（リストと同じ条件で集計）。
    内示本数・確定本数・内示差異・社内メッキ(KT05)・外注メッキ(KT06)・社内溶接(KT07)・外注溶接(KT08)・社内検査(KT09)・外注検査(KT10)。
    製品名に「加工」を含む行は除外。
    """
    om = erp_models.OrderMonthly
    od = erp_models.OrderDaily
    prs = ProductRouteStep
    base_where = _monthly_summary_base_where(om, year, month, destination_cd, keyword)

    # 内示本数: order_monthly.forecast_units 合計
    q_total = (
        select(func.coalesce(func.sum(om.forecast_units), 0).label("forecast_units"))
        .select_from(om)
        .where(base_where)
    )
    row_total = (await db.execute(q_total)).one()
    forecast_units = int(row_total.forecast_units or 0)

    # 確定本数: order_daily.confirmed_units の合計（該当月订单かつ期間内の日付に限定）
    if year is not None and month is not None:
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        subq = select(om.order_id).where(base_where)
        q_confirmed = (
            select(func.coalesce(func.sum(od.confirmed_units), 0))
            .select_from(od)
            .where(od.monthly_order_id.in_(subq))
            .where(od.date >= first_day)
            .where(od.date <= last_day)
        )
        forecast_total_units = int((await db.execute(q_confirmed)).scalar() or 0)
    else:
        q_total_units = (
            select(func.coalesce(func.sum(om.forecast_total_units), 0).label("forecast_total_units"))
            .select_from(om)
            .where(base_where)
        )
        forecast_total_units = int((await db.execute(q_total_units)).scalar() or 0)

    forecast_diff = forecast_total_units - forecast_units  # 内示差異 = 確定本数 - 内示本数

    # 工序別: 該当 process_cd を持つ製品の月订单のみ SUM（重複計上を防ぐため IN (DISTINCT product_cd) で結合）
    async def sum_by_process(process_cd: str):
        subq = select(prs.product_cd).where(prs.process_cd == process_cd).distinct()
        q = (
            select(func.coalesce(func.sum(om.forecast_units), 0))
            .select_from(om)
            .where(base_where)
            .where(om.product_cd.in_(subq))
        )
        r = (await db.execute(q)).scalar()
        return int(r or 0)

    plating_count = await sum_by_process("KT05")  # 社内メッキ
    external_plating_count = await sum_by_process("KT06")  # 外注メッキ
    internal_welding_count = await sum_by_process("KT07")  # 社内溶接
    external_welding_count = await sum_by_process("KT08")  # 外注溶接
    internal_inspection_count = await sum_by_process("KT09")  # 社内検査
    external_inspection_count = await sum_by_process("KT10")  # 外注検査

    return {
        "forecast_units": forecast_units,
        "forecast_total_units": forecast_total_units,
        "forecast_diff": forecast_diff,
        "plating_count": plating_count,
        "external_plating_count": external_plating_count,
        "internal_welding_count": internal_welding_count,
        "external_welding_count": external_welding_count,
        "internal_inspection_count": internal_inspection_count,
        "external_inspection_count": external_inspection_count,
    }


# ---------- POST /batch-create-monthly ----------
class BatchProductItem(BaseModel):
    product_cd: str
    forecast_units: int = 0


class BatchCreateMonthlyBody(BaseModel):
    year: int
    month: int
    destination_cd: str
    destination_name: str
    products: List[BatchProductItem]


@router.post("/batch-create-monthly")
async def batch_create_monthly(
    body: BatchCreateMonthlyBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    月別受注を一括登録。
    order_id = {year}{month2桁}{destination_cd}{product_cd}。
    INSERT 時に重複（同一 order_id）はスキップ。返却: inserted, total, skipped, message。
    """
    if not body.products:
        return {
            "inserted": 0,
            "total": 0,
            "skipped": 0,
            "message": "products が空です",
        }
    year = body.year
    month = body.month
    destination_cd = body.destination_cd
    destination_name = body.destination_name

    # 製品マスタから product_cd に対応する product_name, product_type を取得
    product_cds = [p.product_cd for p in body.products]
    pq = select(Product).where(Product.product_cd.in_(product_cds))
    presult = await db.execute(pq)
    product_map = {r.product_cd: r for r in presult.scalars().all()}

    inserted = 0
    total = len(body.products)
    for item in body.products:
        prod = product_map.get(item.product_cd)
        product_name = prod.product_name if prod else item.product_cd
        product_type = (prod.product_type or "量産品") if prod else "量産品"
        order_id = f"{year}{month:02d}{destination_cd}{item.product_cd}"
        row = erp_models.OrderMonthly(
            order_id=order_id,
            destination_cd=destination_cd,
            destination_name=destination_name,
            year=year,
            month=month,
            product_cd=item.product_cd,
            product_name=product_name,
            product_type=product_type,
            forecast_units=item.forecast_units,
            forecast_total_units=0,
            forecast_diff=0,
        )
        try:
            db.add(row)
            await db.commit()
            inserted += 1
        except IntegrityError:
            await db.rollback()
            # 重複はスキップ（INSERT IGNORE 相当）
            continue
    skipped = total - inserted
    return {
        "inserted": inserted,
        "total": total,
        "skipped": skipped,
        "message": f"{inserted}件登録、{skipped}件スキップ",
    }


# ---------- POST /generate-daily ----------
class GenerateDailyBody(BaseModel):
    year: int
    month: int
    productType: str = "量産品"
    destination_cd: Optional[str] = None


@router.post("/generate-daily")
async def generate_daily_orders(
    body: GenerateDailyBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    日受注リスト生成。year, month 必須。productType は '量産品' のみ対象。
    トランザクション内で実行し、成功時 commit、異常時 rollback。
    """
    if body.productType != "量産品":
        raise HTTPException(status_code=400, detail="productType は '量産品' のみ対応しています")
    try:
        result = await run_generate_daily(
            db,
            year=body.year,
            month=body.month,
            destination_cd=body.destination_cd,
        )
        if not result.get("success") and result.get("detail"):
            raise HTTPException(status_code=404, detail=result["detail"])
        await db.commit()
        return {
            "success": True,
            "insertedCount": result.get("insertedCount", 0),
            "updatedCount": result.get("updatedCount", 0),
            "total": result.get("total", 0),
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise


# ---------- POST /monthly/update-fields ----------
class UpdateOrderFieldsBody(BaseModel):
    startDate: str  # YYYY-MM-DD（年月のみ使用）
    updateProductInfo: bool = True


@router.post("/monthly/update-fields")
async def update_order_fields(
    body: UpdateOrderFieldsBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    開始日以降の月受注・日受注の製品情報を主データに合わせて一括更新。
    startDate の年月以降が対象。(year > startYear) OR (year = startYear AND month >= startMonth)
    updateProductInfo が True のとき、order_monthly の product_name/product_alias/product_type と
    order_daily の product_name/product_alias/product_type/unit_per_box を products 主データで更新。
    """
    from datetime import datetime

    try:
        dt = datetime.strptime(body.startDate.strip()[:10], "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="startDate は YYYY-MM-DD 形式で指定してください")
    start_year = dt.year
    start_month = dt.month

    updated_count = 0
    if body.updateProductInfo:
        om = erp_models.OrderMonthly
        od = erp_models.OrderDaily
        # 対象月订单: (year > startYear) OR (year = startYear AND month >= startMonth)
        q = (
            select(om.id, om.order_id, om.product_cd)
            .where(
                or_(
                    om.year > start_year,
                    and_(om.year == start_year, om.month >= start_month),
                )
            )
        )
        result = await db.execute(q)
        monthly_rows = result.all()
        product_cds = list({r.product_cd for r in monthly_rows})
        if product_cds:
            pq = select(Product).where(Product.product_cd.in_(product_cds))
            presult = await db.execute(pq)
            product_map = {p.product_cd: p for p in presult.scalars().all()}
        else:
            product_map = {}

        for row in monthly_rows:
            product = product_map.get(row.product_cd)
            if not product:
                continue
            product_name = product.product_name or row.product_cd
            product_alias = getattr(product, "product_alias", None) or None
            product_type = (product.product_type or "量産品") if product.product_type else "量産品"
            unit_per_box = product.unit_per_box if product.unit_per_box is not None else 0

            await db.execute(
                update(om).where(om.id == row.id).values(
                    product_name=product_name,
                    product_alias=product_alias,
                    product_type=product_type,
                )
            )
            await db.execute(
                update(od).where(od.monthly_order_id == row.order_id).values(
                    product_name=product_name,
                    product_alias=product_alias,
                    product_type=product_type,
                    unit_per_box=unit_per_box,
                )
            )
            updated_count += 1

        await db.commit()

    return {
        "updatedCount": updated_count,
        "message": f"{updated_count}件の受注情報を更新しました",
    }


# ---------- PATCH /daily/update-shipping-no ----------
class UpdateShippingNoItem(BaseModel):
    """日订单出荷No書戻しの1件（产品+納入先+出荷日で定位）"""
    product_cd: str
    destination_cd: str
    shipping_date: str  # 出荷日（order_daily.date に対応）
    shipping_no: str


@router.patch("/daily/update-shipping-no")
async def update_daily_shipping_no(
    body: List[UpdateShippingNoItem],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    前端 updatePayload に従い、「产品 + 納入先 + 出荷日」で order_daily を特定し、
    shipping_no を書戻す。只更新 shipping_no が空の行。
    """
    if not body:
        return {"success": True, "updatedCount": 0}
    od = erp_models.OrderDaily
    updated = 0
    for item in body:
        product_cd = (item.product_cd or "").strip()
        destination_cd = (item.destination_cd or "").strip()
        shipping_date_str = (item.shipping_date or "").strip()
        shipping_no = (item.shipping_no or "").strip()
        if not product_cd or not destination_cd or not shipping_date_str or not shipping_no:
            continue
        stmt = (
            update(od)
            .where(
                and_(
                    od.product_cd == product_cd,
                    od.destination_cd == destination_cd,
                    od.date == shipping_date_str,
                    or_(od.shipping_no.is_(None), od.shipping_no == ""),
                )
            )
            .values(shipping_no=shipping_no)
        )
        result = await db.execute(stmt)
        updated += result.rowcount
    await db.commit()
    return {"success": True, "updatedCount": updated}

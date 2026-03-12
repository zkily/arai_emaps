"""
材料在庫 API
  material_stock     → /api/material/stock
  material_stock_sub → /api/material/stock/sub
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct, update
from collections import defaultdict
from typing import Optional, Any
from datetime import date

from app.core.database import get_db

logger = logging.getLogger(__name__)


def _safe_float(v: Any) -> Optional[float]:
    """Decimal/int/float/None を float に安全変換"""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_date_iso(v: Any) -> Optional[str]:
    """date/datetime を ISO 文字列に。None は None"""
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import Material
from app.modules.material.models import MaterialStock, MaterialStockSub
from app.modules.material.schemas import (
    MaterialStockCreate,
    MaterialStockUpdate,
    MaterialStockResponse,
    MaterialStockSubCreate,
    MaterialStockSubUpdate,
    MaterialStockSubResponse,
)

router = APIRouter()


# ─────────────────────────────────────────────
# material_stock  メイン在庫
# ─────────────────────────────────────────────

def _stock_to_dict(r: MaterialStock) -> dict:
    return {
        "id": getattr(r, "id", None),
        "material_cd": getattr(r, "material_cd", None) or "",
        "material_name": getattr(r, "material_name", None) or "",
        "date": _safe_date_iso(getattr(r, "date", None)),
        "initial_stock": getattr(r, "initial_stock", None),
        "current_stock": getattr(r, "current_stock", None),
        "safety_stock": getattr(r, "safety_stock", None),
        "planned_usage": getattr(r, "planned_usage", None),
        "adjustment_quantity": getattr(r, "adjustment_quantity", None),
        "max_stock": getattr(r, "max_stock", None),
        "standard_spec": getattr(r, "standard_spec", None) or "",
        "unit": getattr(r, "unit", None),
        "unit_price": _safe_float(getattr(r, "unit_price", None)),
        "pieces_per_bundle": getattr(r, "pieces_per_bundle", None),
        "long_weight": _safe_float(getattr(r, "long_weight", None)),
        "supplier_cd": getattr(r, "supplier_cd", None),
        "supplier_name": getattr(r, "supplier_name", None),
        "lead_time": getattr(r, "lead_time", None),
        "bundle_quantity": getattr(r, "bundle_quantity", None),
        "bundle_weight": _safe_float(getattr(r, "bundle_weight", None)),
        "order_quantity": getattr(r, "order_quantity", None),
        "order_bundle_quantity": getattr(r, "order_bundle_quantity", None),
        "order_amount": _safe_float(getattr(r, "order_amount", None)),
        "remarks": getattr(r, "remarks", None) or "",
        "last_updated": _safe_date_iso(getattr(r, "last_updated", None)),
        "created_at": _safe_date_iso(getattr(r, "created_at", None)),
    }


@router.get("")
async def list_material_stocks(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=10000),
    keyword: Optional[str] = Query(None),
    material_cd: Optional[str] = Query(None),
    supplier_cd: Optional[str] = Query(None),
    suppliers: Optional[str] = Query(None, description="仕入先名称のカンマ区切り。指定時は supplier_name で IN 検索"),
    target_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料在庫一覧（materials.status=0 の材料は除外）"""
    try:
        # material_stock は utf8mb4_unicode_ci、materials は utf8mb4_0900_ai_ci のため COLLATE で揃える
        join_cond = MaterialStock.material_cd.collate("utf8mb4_unicode_ci") == Material.material_cd.collate("utf8mb4_unicode_ci")
        q = (
            select(MaterialStock)
            .join(Material, join_cond)
            .where(Material.status != 0)
        )
        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            q = q.where(
                or_(
                    MaterialStock.material_cd.ilike(kw),
                    MaterialStock.material_name.ilike(kw),
                    MaterialStock.supplier_name.ilike(kw),
                )
            )
        if material_cd:
            q = q.where(MaterialStock.material_cd == material_cd)
        if supplier_cd:
            q = q.where(MaterialStock.supplier_cd == supplier_cd)
        if suppliers and suppliers.strip():
            supplier_list = [s.strip() for s in suppliers.split(",") if s.strip()]
            if supplier_list:
                q = q.where(MaterialStock.supplier_name.in_(supplier_list))
        if target_date and target_date.strip():
            try:
                filter_date = date.fromisoformat(target_date.strip())
                q = q.where(MaterialStock.date == filter_date)
            except ValueError as e:
                logger.warning("list_material_stocks invalid target_date=%s: %s", target_date, e)
                raise HTTPException(status_code=400, detail=f"無効な日付: {target_date}") from e

        total_q = select(func.count()).select_from(q.subquery())
        total = (await db.execute(total_q)).scalar() or 0

        q = q.order_by(MaterialStock.material_cd, MaterialStock.date.desc())
        q = q.offset((page - 1) * pageSize).limit(pageSize)
        rows = (await db.execute(q)).scalars().all()

        return {"success": True, "data": {"list": [_stock_to_dict(r) for r in rows], "total": total}}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("list_material_stocks failed: %s", e)
        raise HTTPException(status_code=500, detail=f"材料在庫一覧の取得に失敗しました: {str(e)}") from e


@router.get("/latest")
async def get_latest_stocks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """各材料の最新在庫（material_cd ごとに最新日付。materials.status=0 は除外）"""
    join_cond = MaterialStock.material_cd.collate("utf8mb4_unicode_ci") == Material.material_cd.collate("utf8mb4_unicode_ci")
    subq = (
        select(MaterialStock.material_cd, func.max(MaterialStock.date).label("max_date"))
        .group_by(MaterialStock.material_cd)
        .subquery()
    )
    q = (
        select(MaterialStock)
        .join(Material, join_cond)
        .where(Material.status != 0)
        .join(
            subq,
            (MaterialStock.material_cd == subq.c.material_cd) & (MaterialStock.date == subq.c.max_date),
        )
    )
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": [_stock_to_dict(r) for r in rows]}


@router.post("/calculate")
async def calculate_material_stock(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    在庫計算: material_stock の current_stock を再計算する。
    全データ中で initial_stock > 0 の「最後」の日付を1つだけ求め、その日付を開始計算日とする。
    全材料ともこの開始計算日以降で計算する。
    空または 0 の項目はすべて 0 として計算に用いる。
    計算式: current_stock = initial_stock + order_quantity + adjustment_quantity - planned_usage + 前日の current_stock
    """
    q = select(MaterialStock).order_by(MaterialStock.material_cd, MaterialStock.date.asc())
    rows = (await db.execute(q)).scalars().all()
    if not rows:
        return {"success": True, "data": {"calculated_count": 0, "updated_count": 0}}

    # material_cd ごとにグループ化
    by_material: dict[str, list[MaterialStock]] = defaultdict(list)
    for r in rows:
        by_material[r.material_cd].append(r)

    # 開始計算日 = 全行のうち initial_stock > 0 である日の「最後」（最大日付）を1つ。全材料ともこの日から計算
    rows_with_initial = [r for r in rows if (r.initial_stock or 0) > 0]
    if not rows_with_initial:
        return {"success": True, "data": {"calculated_count": 0, "updated_count": 0}}
    global_start_date = max(r.date for r in rows_with_initial)

    # 開始計算日以降の current_stock を 0 にクリア
    stmt = update(MaterialStock).where(MaterialStock.date >= global_start_date).values(current_stock=0)
    await db.execute(stmt)
    await db.flush()

    updates: dict[int, int] = {}
    calculated_count = 0
    for material_cd, list_rows in by_material.items():
        # 全材料とも同じ global_start_date 以降の行を日付昇順で計算
        to_calc = sorted([r for r in list_rows if r.date >= global_start_date], key=lambda x: x.date)
        prev_current = 0
        for r in to_calc:
            # 空または 0 はすべて 0 として扱う
            init = int(r.initial_stock or 0)
            order_qty = int(r.order_quantity or 0)
            adj = int(r.adjustment_quantity or 0)
            usage = int(r.planned_usage or 0)
            new_current = init + order_qty + adj - usage + prev_current
            updates[r.id] = new_current
            prev_current = new_current
        if to_calc:
            calculated_count += 1

    # 一括更新
    updated_count = 0
    for row in rows:
        if row.id in updates and row.current_stock != updates[row.id]:
            row.current_stock = updates[row.id]
            updated_count += 1
    await db.commit()
    return {
        "success": True,
        "data": {"calculated_count": calculated_count, "updated_count": updated_count},
    }


@router.get("/summary")
async def get_stock_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫サマリー（総材料数・安全在庫以下・合計在庫金額）"""
    total_materials = (await db.execute(select(func.count(distinct(MaterialStock.material_cd))))).scalar() or 0
    below_safety = (
        await db.execute(
            select(func.count()).where(MaterialStock.current_stock <= MaterialStock.safety_stock)
        )
    ).scalar() or 0
    total_value_result = await db.execute(
        select(func.sum(MaterialStock.current_stock * MaterialStock.unit_price))
    )
    total_value = float(total_value_result.scalar() or 0)
    return {
        "success": True,
        "data": {
            "total_materials": total_materials,
            "below_safety": below_safety,
            "total_value": total_value,
        },
    }


@router.post("/sync-material-master")
async def sync_material_master_to_stock(
    body: dict | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    材料マスタ同期:
      material_stock.material_cd と materials.material_cd を結合し、
      material_stock の以下の項目を材料マスタから更新する:
        - material_name
        - safety_stock
        - supplier_cd
        - bundle_quantity
        - bundle_weight
        - standard_spec
        - unit_price
        - pieces_per_bundle
        - long_weight
    期間指定:
      body.start_date, body.end_date が指定された場合、その期間内 (date BETWEEN start_date AND end_date)
      の material_stock のみを更新対象とする。
      未指定の場合は全期間を更新対象とする。
    """
    try:
        start_date: Optional[date] = None
        end_date: Optional[date] = None
        if body:
            s = body.get("start_date")
            e = body.get("end_date")
            if isinstance(s, str) and s.strip():
                start_date = date.fromisoformat(s.strip()[:10])
            if isinstance(e, str) and e.strip():
                end_date = date.fromisoformat(e.strip()[:10])

        # 有効な材料マスタを取得（status=1）
        mat_stmt = (
            select(
                Material.material_cd,
                Material.material_name,
                Material.safety_stock,
                Material.supplier_cd,
                Material.standard_spec,
                Material.unit_price,
                Material.pieces_per_bundle,
                Material.long_weight,
            )
            .where(Material.status == 1)
        )
        mat_rows = (await db.execute(mat_stmt)).all()
        if not mat_rows:
            return {
                "success": True,
                "data": {
                    "updated_count": 0,
                },
            }

        # material_cd -> マスタ情報 のマップ
        master_map: dict[str, tuple] = {
            row[0]: row for row in mat_rows  # (material_cd, name, safety, supplier_cd, standard_spec, unit_price, pieces_per_bundle, long_weight)
        }

        # 対象となる material_stock 行を取得（materials.status=1 の material_cd のみ、必要なら期間で絞り込み）
        stock_stmt = select(MaterialStock).where(MaterialStock.material_cd.in_(master_map.keys()))
        if start_date:
            stock_stmt = stock_stmt.where(MaterialStock.date >= start_date)
        if end_date:
            stock_stmt = stock_stmt.where(MaterialStock.date <= end_date)
        stock_rows = (await db.execute(stock_stmt)).scalars().all()

        updated_count = 0
        for stock in stock_rows:
            m = master_map.get(stock.material_cd)
            if not m:
                continue
            _, material_name, safety_stock, supplier_cd, standard_spec, unit_price, pieces_per_bundle, long_weight = m

            # マスタの値で上書き（None や 0 は 0 として扱う）
            stock.material_name = material_name
            stock.safety_stock = int(safety_stock or 0)
            stock.supplier_cd = supplier_cd
            stock.standard_spec = (standard_spec or "").strip() or ""
            try:
                stock.unit_price = float(unit_price or 0)
            except (TypeError, ValueError):
                stock.unit_price = 0.0
            stock.pieces_per_bundle = int(pieces_per_bundle or 0)
            try:
                lw = float(long_weight or 0)
            except (TypeError, ValueError):
                lw = 0.0
            stock.long_weight = lw

            # 束本数・束重量は材料マスタから算出・同期
            # 束本数: pieces_per_bundle をそのまま利用
            stock.bundle_quantity = stock.pieces_per_bundle
            # 束重量: 一本重量(long_weight) × 束本数
            stock.bundle_weight = lw * stock.bundle_quantity

            updated_count += 1

        await db.commit()

        return {
            "success": True,
            "data": {
                "updated_count": updated_count,
            },
        }
    except Exception as e:
        logger.exception("sync_material_master_to_stock failed: %s", e)
        raise HTTPException(status_code=500, detail=f"材料マスタ同期に失敗しました: {str(e)}") from e


@router.post("")
async def create_material_stock(
    body: MaterialStockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料在庫登録"""
    row = MaterialStock(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _stock_to_dict(row)}


@router.put("/{item_id}")
async def update_material_stock(
    item_id: int,
    body: MaterialStockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料在庫更新"""
    result = await db.execute(select(MaterialStock).where(MaterialStock.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _stock_to_dict(row)}


@router.delete("/{item_id}")
async def delete_material_stock(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料在庫削除"""
    result = await db.execute(select(MaterialStock).where(MaterialStock.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}


# ─────────────────────────────────────────────
# material_stock_sub  手動注文サブ在庫
# ─────────────────────────────────────────────

def _sub_to_dict(r: MaterialStockSub) -> dict:
    return {
        "id": r.id,
        "material_cd": r.material_cd,
        "material_name": r.material_name,
        "date": r.date.isoformat() if r.date else None,
        "current_stock": float(r.current_stock) if r.current_stock is not None else None,
        "safety_stock": float(r.safety_stock) if r.safety_stock is not None else None,
        "max_stock": float(r.max_stock) if r.max_stock is not None else None,
        "unit": r.unit,
        "unit_price": float(r.unit_price) if r.unit_price is not None else None,
        "supplier_cd": r.supplier_cd,
        "supplier_name": r.supplier_name,
        "lead_time": r.lead_time,
        "planned_usage": float(r.planned_usage) if r.planned_usage is not None else None,
        "order_quantity": float(r.order_quantity) if r.order_quantity is not None else None,
        "order_bundle_quantity": float(r.order_bundle_quantity) if r.order_bundle_quantity is not None else None,
        "bundle_weight": float(r.bundle_weight) if r.bundle_weight is not None else None,
        "order_amount": float(r.order_amount) if r.order_amount is not None else None,
        "standard_spec": r.standard_spec,
        "pieces_per_bundle": r.pieces_per_bundle,
        "long_weight": float(r.long_weight) if r.long_weight is not None else None,
        "remarks": r.remarks,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "last_updated": r.last_updated.isoformat() if r.last_updated else None,
    }


@router.get("/sub")
async def list_stock_sub(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=500),
    keyword: Optional[str] = Query(None),
    suppliers: Optional[str] = Query(None, description="仕入先名称のカンマ区切り。指定時は supplier_name で IN 検索"),
    target_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サブ在庫一覧（materials.status=0 の材料は除外）"""
    join_cond = MaterialStockSub.material_cd.collate("utf8mb4_unicode_ci") == Material.material_cd.collate("utf8mb4_unicode_ci")
    q = (
        select(MaterialStockSub)
        .join(Material, join_cond)
        .where(Material.status != 0)
    )
    if keyword:
        kw = f"%{keyword}%"
        q = q.where(
            or_(
                MaterialStockSub.material_cd.ilike(kw),
                MaterialStockSub.material_name.ilike(kw),
            )
        )
    if suppliers:
        supplier_list = [s.strip() for s in suppliers.split(",") if s.strip()]
        if supplier_list:
            q = q.where(MaterialStockSub.supplier_name.in_(supplier_list))
    if target_date:
        q = q.where(MaterialStockSub.date == date.fromisoformat(target_date))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    q = q.order_by(MaterialStockSub.date.desc(), MaterialStockSub.material_cd)
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    rows = (await db.execute(q)).scalars().all()
    return {"success": True, "data": {"list": [_sub_to_dict(r) for r in rows], "total": total}}


@router.post("/sub")
async def create_stock_sub(
    body: MaterialStockSubCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サブ在庫登録"""
    row = MaterialStockSub(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _sub_to_dict(row)}


@router.put("/sub/{item_id}")
async def update_stock_sub(
    item_id: int,
    body: MaterialStockSubUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サブ在庫更新"""
    result = await db.execute(select(MaterialStockSub).where(MaterialStockSub.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _sub_to_dict(row)}


@router.delete("/sub/{item_id}")
async def delete_stock_sub(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """サブ在庫削除"""
    result = await db.execute(select(MaterialStockSub).where(MaterialStockSub.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}

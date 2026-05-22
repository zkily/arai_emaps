"""
設備能率管理 API（equipment_efficiency）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func, case, literal
from typing import Optional, Any, Dict
from decimal import Decimal

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import EquipmentEfficiency

router = APIRouter()


def _keyword_clause(keyword: Optional[str]):
    if not keyword or not str(keyword).strip():
        return None
    k = f"%{keyword.strip()}%"
    return or_(
        EquipmentEfficiency.machines_name.like(k),
        EquipmentEfficiency.product_name.like(k),
        EquipmentEfficiency.machine_cd.like(k),
        EquipmentEfficiency.product_cd.like(k),
    )


def _process_type_expr():
    """Vue EquipmentEfficiencyManagement.getProcessType と同優先度（CASE WHEN 順）"""
    mn = func.lower(func.coalesce(EquipmentEfficiency.machines_name, ""))
    mc = func.lower(func.coalesce(EquipmentEfficiency.machine_cd, ""))
    return case(
        (or_(mn.like("%面取%"), mn.like("%chamfer%"), mc.like("%chamfer%")), literal("chamfering")),
        (or_(mn.like("%成型%"), mn.like("%forming%"), mc.like("%forming%")), literal("forming")),
        (or_(mn.like("%溶接%"), mn.like("%welding%"), mc.like("%welding%")), literal("welding")),
        (or_(mn.like("%メッキ%"), mn.like("%plating%"), mc.like("%plating%")), literal("plating")),
        (or_(mn.like("%検査%"), mn.like("%inspection%"), mc.like("%inspection%")), literal("inspection")),
        (or_(mn.like("%切断%"), mn.like("%cutting%"), mc.like("%cutting%")), literal("cutting")),
        else_=literal("other"),
    )


def _list_where_clauses(keyword: Optional[str], process_type: Optional[str]) -> list:
    clauses = []
    kw = _keyword_clause(keyword)
    if kw is not None:
        clauses.append(kw)
    pt = (process_type or "").strip().lower()
    if pt and pt != "all":
        clauses.append(_process_type_expr() == pt)
    return clauses


async def _tab_counts(db: AsyncSession, keyword: Optional[str]) -> Dict[str, int]:
    kw = _keyword_clause(keyword)
    pt = _process_type_expr()
    stmt = select(pt.label("p"), func.count(EquipmentEfficiency.id)).select_from(EquipmentEfficiency)
    if kw is not None:
        stmt = stmt.where(kw)
    stmt = stmt.group_by(pt)
    result = await db.execute(stmt)
    rows = result.all()
    counts: Dict[str, int] = {
        "all": 0,
        "cutting": 0,
        "chamfering": 0,
        "forming": 0,
        "welding": 0,
        "plating": 0,
        "inspection": 0,
        "other": 0,
    }
    for p, n in rows:
        key = str(p) if p is not None else "other"
        if key in counts:
            counts[key] = int(n)
        else:
            counts["other"] += int(n)
    counts["all"] = sum(counts[k] for k in counts if k != "all")
    return counts


def _row_to_dict(row: EquipmentEfficiency) -> dict:
    eff = row.efficiency_rate
    if eff is not None and hasattr(eff, "__float__"):
        eff = float(eff)
    return {
        "id": row.id,
        "machine_cd": row.machine_cd,
        "machines_name": row.machines_name,
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "efficiency_rate": eff,
        "step_time": row.step_time,
        "unit": row.unit,
        "remarks": row.remarks,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def get_equipment_efficiency_list(
    keyword: Optional[str] = Query(None),
    process_type: Optional[str] = Query(None, alias="processType"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=99999, alias="pageSize"),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=99999,
        description="互換用: 指定時は page/pageSize を使わず先頭から最大 limit 件を返す",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備能率一覧（ページング。limit 指定時は従来どおり一括取得互換）"""
    clauses = _list_where_clauses(keyword, process_type)
    where_expr = and_(*clauses) if clauses else None

    count_stmt = select(func.count()).select_from(EquipmentEfficiency)
    if where_expr is not None:
        count_stmt = count_stmt.where(where_expr)
    total = (await db.execute(count_stmt)).scalar() or 0

    list_stmt = select(EquipmentEfficiency).order_by(
        EquipmentEfficiency.machines_name, EquipmentEfficiency.product_name
    )
    if where_expr is not None:
        list_stmt = list_stmt.where(where_expr)

    legacy = limit is not None
    if legacy:
        list_stmt = list_stmt.limit(limit)
    else:
        list_stmt = list_stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(list_stmt)
    rows = result.scalars().all()
    data_list = [_row_to_dict(r) for r in rows]

    payload: Dict[str, Any] = {
        "success": True,
        "data": {
            "list": data_list,
            "total": total,
        },
        "list": data_list,
        "total": total,
    }

    if not legacy:
        tab_counts = await _tab_counts(db, keyword)
        m_stmt = select(func.count(func.distinct(EquipmentEfficiency.machine_cd))).select_from(EquipmentEfficiency)
        p_stmt = select(func.count(func.distinct(EquipmentEfficiency.product_cd))).select_from(EquipmentEfficiency)
        if where_expr is not None:
            m_stmt = m_stmt.where(where_expr)
            p_stmt = p_stmt.where(where_expr)
        machine_distinct = (await db.execute(m_stmt)).scalar() or 0
        product_distinct = (await db.execute(p_stmt)).scalar() or 0
        payload["data"]["tab_counts"] = tab_counts
        payload["data"]["machine_distinct_count"] = int(machine_distinct)
        payload["data"]["product_distinct_count"] = int(product_distinct)
        payload["tab_counts"] = tab_counts
        payload["machine_distinct_count"] = int(machine_distinct)
        payload["product_distinct_count"] = int(product_distinct)

    return payload


@router.get("/{item_id:int}")
async def get_equipment_efficiency_by_id(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """IDで1件取得"""
    result = await db.execute(select(EquipmentEfficiency).where(EquipmentEfficiency.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備能率設定が見つかりません")
    return _row_to_dict(row)


@router.post("")
async def create_equipment_efficiency(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規登録"""
    machine_cd = body.get("machine_cd") or ""
    product_cd = body.get("product_cd") or ""
    if not machine_cd or not product_cd:
        raise HTTPException(status_code=400, detail="設備コードと製品コードは必須です")
    existing = await db.execute(
        select(EquipmentEfficiency).where(
            EquipmentEfficiency.machine_cd == machine_cd,
            EquipmentEfficiency.product_cd == product_cd,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="この設備・製品の組み合わせは既に登録されています")
    eff = body.get("efficiency_rate")
    if eff is not None and not isinstance(eff, (int, float, Decimal)):
        try:
            eff = float(eff)
        except (TypeError, ValueError):
            eff = 0.0
    row = EquipmentEfficiency(
        machine_cd=machine_cd,
        machines_name=body.get("machines_name"),
        product_cd=product_cd,
        product_name=body.get("product_name"),
        efficiency_rate=eff if eff is not None else 0.0,
        step_time=body.get("step_time"),
        unit=body.get("unit"),
        remarks=body.get("remarks"),
        status=body.get("status") if body.get("status") is not None else 1,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.put("/{item_id:int}")
async def update_equipment_efficiency(
    item_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """更新"""
    result = await db.execute(select(EquipmentEfficiency).where(EquipmentEfficiency.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備能率設定が見つかりません")
    machine_cd = body.get("machine_cd")
    product_cd = body.get("product_cd")
    if machine_cd is not None:
        row.machine_cd = machine_cd
    if product_cd is not None:
        row.product_cd = product_cd
    if "machines_name" in body:
        row.machines_name = body.get("machines_name")
    if "product_name" in body:
        row.product_name = body.get("product_name")
    if "efficiency_rate" in body:
        eff = body.get("efficiency_rate")
        if eff is not None and not isinstance(eff, (int, float, Decimal)):
            try:
                eff = float(eff)
            except (TypeError, ValueError):
                eff = 0.0
        row.efficiency_rate = eff if eff is not None else 0.0
    if "step_time" in body:
        row.step_time = body.get("step_time")
    if "unit" in body:
        row.unit = body.get("unit")
    if "remarks" in body:
        row.remarks = body.get("remarks")
    if "status" in body:
        row.status = body.get("status")
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{item_id:int}")
async def delete_equipment_efficiency(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """削除"""
    result = await db.execute(select(EquipmentEfficiency).where(EquipmentEfficiency.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備能率設定が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}

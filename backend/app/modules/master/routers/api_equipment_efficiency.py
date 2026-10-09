"""
設備能率管理 API（equipment_efficiency）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from typing import Optional, Any, Dict, List
from decimal import Decimal

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_master_operation
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.equipment_efficiency_current import (
    add_missing_from_productivity,
    find_missing_from_productivity,
    process_type_expr as _process_type_expr,
    refresh_current_efficiency_rates,
)
from app.modules.master.models import (
    EquipmentEfficiency,
    Material,
    Product,
    ProductBomHeader,
    ProductBomLine,
)

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


def _selection_clauses(
    keyword: Optional[str],
    machine_cd: Optional[str] = None,
    product_cd: Optional[str] = None,
) -> list:
    clauses = []
    kw = _keyword_clause(keyword)
    if kw is not None:
        clauses.append(kw)
    mc = (machine_cd or "").strip()
    if mc:
        clauses.append(EquipmentEfficiency.machine_cd == mc)
    pc = (product_cd or "").strip()
    if pc:
        clauses.append(EquipmentEfficiency.product_cd == pc)
    return clauses


def _list_where_clauses(
    keyword: Optional[str],
    process_type: Optional[str],
    machine_cd: Optional[str] = None,
    product_cd: Optional[str] = None,
) -> list:
    clauses = _selection_clauses(keyword, machine_cd, product_cd)
    pt = (process_type or "").strip().lower()
    if pt and pt != "all":
        clauses.append(_process_type_expr() == pt)
    return clauses


async def _tab_counts(
    db: AsyncSession,
    keyword: Optional[str],
    machine_cd: Optional[str] = None,
    product_cd: Optional[str] = None,
) -> Dict[str, int]:
    clauses = _selection_clauses(keyword, machine_cd, product_cd)
    pt = _process_type_expr()
    stmt = select(pt.label("p"), func.count(EquipmentEfficiency.id)).select_from(
        EquipmentEfficiency
    )
    if clauses:
        stmt = stmt.where(and_(*clauses))
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


def _as_float(value):
    if value is None:
        return None
    if hasattr(value, "__float__"):
        return float(value)
    return value


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
        "current_efficiency_rate": _as_float(row.current_efficiency_rate),
        "current_efficiency_updated_at": (
            row.current_efficiency_updated_at.isoformat()
            if row.current_efficiency_updated_at
            else None
        ),
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
    machine_cd: Optional[str] = Query(None, alias="machineCd"),
    product_cd: Optional[str] = Query(None, alias="productCd"),
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
    clauses = _list_where_clauses(keyword, process_type, machine_cd, product_cd)
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
        tab_counts = await _tab_counts(db, keyword, machine_cd, product_cd)
        m_stmt = select(func.count(func.distinct(EquipmentEfficiency.machine_cd))).select_from(
            EquipmentEfficiency
        )
        p_stmt = select(func.count(func.distinct(EquipmentEfficiency.product_cd))).select_from(
            EquipmentEfficiency
        )
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


@router.get("/filter-options")
async def get_equipment_efficiency_filter_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """絞込プルダウン用：登録済みの設備×製品の組み合わせ（重複なし、工程付き）"""
    stmt = (
        select(
            EquipmentEfficiency.machine_cd,
            EquipmentEfficiency.machines_name,
            EquipmentEfficiency.product_cd,
            EquipmentEfficiency.product_name,
            _process_type_expr().label("process_type"),
        )
        .distinct()
        .order_by(EquipmentEfficiency.machines_name, EquipmentEfficiency.product_name)
    )
    rows = (await db.execute(stmt)).all()
    pairs = [
        {
            "machine_cd": m_cd,
            "machines_name": m_name,
            "product_cd": p_cd,
            "product_name": p_name,
            "process_type": str(pt) if pt is not None else "other",
        }
        for m_cd, m_name, p_cd, p_name, pt in rows
        if m_cd or p_cd
    ]
    return {"success": True, "data": {"pairs": pairs}}


async def _product_materials_map(db: AsyncSession, product_cds: List[str]) -> Dict[str, List[dict]]:
    """製品CD → 使用材料一覧（製品マスタ material_cd 優先、無ければ明細BOMの材料行）"""
    if not product_cds:
        return {}
    material_cds_by_product: Dict[str, List[str]] = {}

    prod_rows = (
        await db.execute(
            select(Product.product_cd, Product.material_cd).where(
                Product.product_cd.in_(product_cds)
            )
        )
    ).all()
    for p_cd, m_cd in prod_rows:
        m = (m_cd or "").strip()
        if p_cd and m:
            material_cds_by_product[p_cd] = [m]

    missing = [cd for cd in product_cds if cd not in material_cds_by_product]
    if missing:
        bom_rows = (
            await db.execute(
                select(ProductBomHeader.parent_product_cd, ProductBomLine.component_material_cd)
                .join(ProductBomLine, ProductBomLine.header_id == ProductBomHeader.id)
                .where(
                    ProductBomHeader.parent_product_cd.in_(missing),
                    ProductBomHeader.status == "active",
                    ProductBomLine.component_material_cd.isnot(None),
                    ProductBomLine.component_material_cd != "",
                )
                .order_by(ProductBomHeader.parent_product_cd, ProductBomLine.line_no)
            )
        ).all()
        for p_cd, m_cd in bom_rows:
            lst = material_cds_by_product.setdefault(p_cd, [])
            if m_cd not in lst:
                lst.append(m_cd)

    all_material_cds = sorted({m for lst in material_cds_by_product.values() for m in lst})
    name_map: Dict[str, str] = {}
    if all_material_cds:
        mat_rows = (
            await db.execute(
                select(Material.material_cd, Material.material_name).where(
                    Material.material_cd.in_(all_material_cds)
                )
            )
        ).all()
        name_map = {cd: name for cd, name in mat_rows}

    return {
        p_cd: [{"material_cd": m, "material_name": name_map.get(m) or ""} for m in lst]
        for p_cd, lst in material_cds_by_product.items()
    }


_OVERVIEW_EXCLUDED_PRODUCT_TYPES = ("試作品", "補給品")


@router.get("/by-process")
async def get_equipment_efficiency_by_process(
    keyword: Optional[str] = Query(None),
    process_type: Optional[str] = Query(None, alias="processType"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程別一覧（設備ごとの製品・能率・使用材料）。無効・試作品・補給品・成型NC設備は対象外。"""
    clauses = _list_where_clauses(keyword, process_type)
    clauses.append(EquipmentEfficiency.status == 1)
    mn = func.upper(func.coalesce(EquipmentEfficiency.machines_name, ""))
    clauses.append(~and_(mn.like("%成型%"), mn.like("%NC%")))
    pt = _process_type_expr()
    stmt = select(EquipmentEfficiency, pt.label("process_type")).order_by(
        EquipmentEfficiency.machines_name,
        EquipmentEfficiency.machine_cd,
        EquipmentEfficiency.product_name,
    )
    if clauses:
        stmt = stmt.where(and_(*clauses))
    rows = (await db.execute(stmt)).all()

    product_cds = sorted({r.product_cd for r, _ in rows if r.product_cd})
    if product_cds:
        excluded = set(
            (
                await db.execute(
                    select(Product.product_cd).where(
                        Product.product_cd.in_(product_cds),
                        Product.product_type.in_(_OVERVIEW_EXCLUDED_PRODUCT_TYPES),
                    )
                )
            )
            .scalars()
            .all()
        )
        if excluded:
            rows = [(r, p) for r, p in rows if r.product_cd not in excluded]
            product_cds = [cd for cd in product_cds if cd not in excluded]
    materials_map = await _product_materials_map(db, product_cds)

    data_list = []
    for r, p in rows:
        item = _row_to_dict(r)
        item["process_type"] = str(p) if p is not None else "other"
        item["materials"] = materials_map.get(r.product_cd or "", [])
        data_list.append(item)

    return {"success": True, "data": {"list": data_list, "total": len(data_list)}}


@router.post("/refresh-current-rate")
async def refresh_equipment_current_rate(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    """直近3ヶ月の生産性から現在能率を一括更新する。能率は変更しない。"""
    return await refresh_current_efficiency_rates(db)


@router.get("/productivity-missing")
async def get_productivity_missing(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産性（直近3ヶ月）にあって未登録の 設備×製品 の候補一覧"""
    return await find_missing_from_productivity(db)


@router.post("/productivity-missing/add")
async def add_productivity_missing(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("create")),
):
    """候補を追加（能率＝現在能率）。items 未指定なら全候補。"""
    items = body.get("items")
    selected = None
    if items is not None:
        if not isinstance(items, list):
            raise HTTPException(status_code=400, detail="items は配列で指定してください")
        selected = [
            (str(i.get("machine_cd") or ""), str(i.get("product_cd") or ""))
            for i in items
            if isinstance(i, dict)
        ]
        if not selected:
            raise HTTPException(status_code=400, detail="追加対象が選択されていません")
    return await add_missing_from_productivity(db, selected)


@router.post("/{item_id:int}/apply-current-rate")
async def apply_equipment_current_rate(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    """現在能率を能率へ反映する。"""
    result = await db.execute(select(EquipmentEfficiency).where(EquipmentEfficiency.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備能率設定が見つかりません")
    if row.current_efficiency_rate is None:
        raise HTTPException(status_code=400, detail="現在能率が未算出のため反映できません")
    row.efficiency_rate = row.current_efficiency_rate
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


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
    current_user: User = Depends(require_master_operation("create")),
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
        raise HTTPException(
            status_code=400, detail="この設備・製品の組み合わせは既に登録されています"
        )
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
    current_user: User = Depends(require_master_operation("edit")),
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
    current_user: User = Depends(require_master_operation("delete")),
):
    """削除"""
    result = await db.execute(select(EquipmentEfficiency).where(EquipmentEfficiency.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備能率設定が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}

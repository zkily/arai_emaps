"""
標準原価マスタ・月次実績・差異（API）
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import Product
from app.modules.erp import standard_cost_models as m
from app.modules.erp import standard_cost_schemas as s

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/standard-cost", tags=["StandardCosting"])


def _f(x) -> float:
    if x is None:
        return 0.0
    return float(x)


def _dec(x) -> Decimal:
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def _rollup_mat_line(row: s.ProductStandardMaterialLineIn) -> Decimal:
    if _dec(row.amount) != 0:
        return _dec(row.amount)
    q = _dec(row.qty_per_unit)
    scrap = _dec(row.scrap_pct) / Decimal("100")
    adj_q = q * (Decimal("1") + scrap)
    return (adj_q * _dec(row.standard_unit_price)).quantize(Decimal("0.0001"))


def _rollup_lab_line(row: s.ProductStandardLaborLineIn) -> Decimal:
    if _dec(row.amount) != 0:
        return _dec(row.amount)
    h = _dec(row.std_hours) + _dec(row.setup_hours)
    return (h * _dec(row.labor_rate_per_hour)).quantize(Decimal("0.0001"))


def _rollup_oh_line(row: s.ProductStandardOverheadLineIn) -> Decimal:
    if _dec(row.amount) != 0:
        return _dec(row.amount)
    return (_dec(row.basis_qty_per_unit) * _dec(row.overhead_rate)).quantize(Decimal("0.0001"))


def _rollup_header_totals(
    material: List[s.ProductStandardMaterialLineIn],
    labor: List[s.ProductStandardLaborLineIn],
    overhead: List[s.ProductStandardOverheadLineIn],
    override_m: Optional[Decimal],
    override_l: Optional[Decimal],
    override_o: Optional[Decimal],
) -> Tuple[Decimal, Decimal, Decimal]:
    """明細優先。明細が空なら override、それも無ければ 0。"""
    if material:
        mt = sum((_rollup_mat_line(x) for x in material), Decimal("0"))
    elif override_m is not None:
        mt = _dec(override_m)
    else:
        mt = Decimal("0")
    if labor:
        lt = sum((_rollup_lab_line(x) for x in labor), Decimal("0"))
    elif override_l is not None:
        lt = _dec(override_l)
    else:
        lt = Decimal("0")
    if overhead:
        ot = sum((_rollup_oh_line(x) for x in overhead), Decimal("0"))
    elif override_o is not None:
        ot = _dec(override_o)
    else:
        ot = Decimal("0")
    return mt, lt, ot


async def _product_name(db: AsyncSession, product_cd: str) -> Optional[str]:
    r = await db.execute(select(Product.product_name).where(Product.product_cd == product_cd))
    return r.scalar_one_or_none()


async def _resolve_version_for_month(
    db: AsyncSession, year_month: str, explicit: Optional[int]
) -> Optional[int]:
    if explicit:
        r = await db.execute(select(m.CostStandardVersion).where(m.CostStandardVersion.id == explicit))
        if not r.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="指定の標準原価バージョンが存在しません")
        return explicit
    y = int(year_month[:4])
    r = await db.execute(
        select(m.CostStandardVersion.id)
        .where(
            m.CostStandardVersion.fiscal_year == y,
            m.CostStandardVersion.status == "active",
        )
        .order_by(m.CostStandardVersion.effective_from.desc())
        .limit(1)
    )
    return r.scalar_one_or_none()


async def _get_standard_unit_costs(
    db: AsyncSession, version_id: int, product_cd: str
) -> Optional[Tuple[Decimal, Decimal, Decimal]]:
    r = await db.execute(
        select(
            m.ProductStandardCost.material_cost_std,
            m.ProductStandardCost.labor_cost_std,
            m.ProductStandardCost.overhead_cost_std,
        ).where(
            m.ProductStandardCost.version_id == version_id,
            m.ProductStandardCost.product_cd == product_cd,
        )
    )
    row = r.one_or_none()
    if not row:
        return None
    return (_dec(row[0]), _dec(row[1]), _dec(row[2]))


def _period_line_to_out(row: m.CostPeriodProductCost) -> s.CostPeriodProductCostOut:
    am = row.actual_material_cost
    al = row.actual_labor_cost
    ao = row.actual_overhead_cost
    sm = row.standard_material_allowed
    sl = row.standard_labor_allowed
    so = row.standard_overhead_allowed
    vm = None
    vl = None
    vo = None
    vg = None
    if am is not None:
        vm = _f(am) - _f(sm)
    if al is not None:
        vl = _f(al) - _f(sl)
    if ao is not None:
        vo = _f(ao) - _f(so)
    if vm is not None and vl is not None and vo is not None:
        vg = vm + vl + vo
    return s.CostPeriodProductCostOut(
        id=row.id,
        period_id=row.period_id,
        version_id=row.version_id,
        product_cd=row.product_cd,
        product_name=row.product_name,
        finished_good_qty=_f(row.finished_good_qty),
        wip_equivalent_qty=_f(row.wip_equivalent_qty),
        actual_material_cost=_f(am) if am is not None else None,
        actual_labor_cost=_f(al) if al is not None else None,
        actual_overhead_cost=_f(ao) if ao is not None else None,
        standard_material_allowed=_f(sm),
        standard_labor_allowed=_f(sl),
        standard_overhead_allowed=_f(so),
        variance_material_price=_f(row.variance_material_price),
        variance_material_qty=_f(row.variance_material_qty),
        variance_labor_rate=_f(row.variance_labor_rate),
        variance_labor_efficiency=_f(row.variance_labor_efficiency),
        variance_moh_budget=_f(row.variance_moh_budget),
        variance_moh_capacity=_f(row.variance_moh_capacity),
        variance_moh_efficiency=_f(row.variance_moh_efficiency),
        remarks=row.remarks,
        updated_at=row.updated_at,
        variance_material_total=vm,
        variance_labor_total=vl,
        variance_overhead_total=vo,
        variance_grand_total=vg,
    )


# ---------------------------------------------------------------------------
# バージョン
# ---------------------------------------------------------------------------


@router.get("/versions", response_model=List[s.CostStandardVersionOut])
async def list_versions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(select(m.CostStandardVersion).order_by(m.CostStandardVersion.fiscal_year.desc(), m.CostStandardVersion.id.desc()))
    return list(r.scalars().all())


@router.post("/versions", response_model=s.CostStandardVersionOut)
async def create_version(
    body: s.CostStandardVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = m.CostStandardVersion(
        **body.model_dump(),
        created_by=current_user.username if current_user else None,
        updated_by=current_user.username if current_user else None,
    )
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="同一コードのバージョンが既に存在します")
    await db.refresh(row)
    return row


@router.put("/versions/{version_id}", response_model=s.CostStandardVersionOut)
async def update_version(
    version_id: int,
    body: s.CostStandardVersionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(select(m.CostStandardVersion).where(m.CostStandardVersion.id == version_id))
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="バージョンが見つかりません")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_by = current_user.username if current_user else None
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/versions/{version_id}")
async def delete_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(select(m.CostStandardVersion).where(m.CostStandardVersion.id == version_id))
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="バージョンが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# 製品標準原価
# ---------------------------------------------------------------------------


def _build_detail(row: m.ProductStandardCost) -> s.ProductStandardCostDetail:
    return s.ProductStandardCostDetail(
        id=row.id,
        version_id=row.version_id,
        product_cd=row.product_cd,
        product_name=row.product_name,
        material_cost_std=_f(row.material_cost_std),
        labor_cost_std=_f(row.labor_cost_std),
        overhead_cost_std=_f(row.overhead_cost_std),
        total_cost_std=_f(row.total_cost_std),
        currency=row.currency or "JPY",
        source=row.source or "manual",
        remarks=row.remarks,
        updated_at=row.updated_at,
        material_lines=[s.ProductStandardMaterialLineOut.model_validate(x) for x in row.material_lines],
        labor_lines=[s.ProductStandardLaborLineOut.model_validate(x) for x in row.labor_lines],
        overhead_lines=[s.ProductStandardOverheadLineOut.model_validate(x) for x in row.overhead_lines],
    )


@router.get("/products", response_model=s.ProductStandardCostListResponse)
async def list_product_standards(
    version_id: int = Query(...),
    product_cd: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(m.ProductStandardCost).where(m.ProductStandardCost.version_id == version_id)
    if product_cd and product_cd.strip():
        q = q.where(m.ProductStandardCost.product_cd.contains(product_cd.strip()))
    cnt_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(cnt_q)).scalar() or 0
    q = q.order_by(m.ProductStandardCost.product_cd.asc()).offset((page - 1) * page_size).limit(page_size)
    r = await db.execute(q)
    rows = list(r.scalars().all())
    items = [
        s.ProductStandardCostListItem(
            id=x.id,
            version_id=x.version_id,
            product_cd=x.product_cd,
            product_name=x.product_name,
            material_cost_std=_f(x.material_cost_std),
            labor_cost_std=_f(x.labor_cost_std),
            overhead_cost_std=_f(x.overhead_cost_std),
            total_cost_std=_f(x.total_cost_std),
            currency=x.currency or "JPY",
            source=x.source or "manual",
            remarks=x.remarks,
            updated_at=x.updated_at,
        )
        for x in rows
    ]
    return s.ProductStandardCostListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/products/{header_id}", response_model=s.ProductStandardCostDetail)
async def get_product_standard(
    header_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(
        select(m.ProductStandardCost)
        .options(
            selectinload(m.ProductStandardCost.material_lines),
            selectinload(m.ProductStandardCost.labor_lines),
            selectinload(m.ProductStandardCost.overhead_lines),
        )
        .where(m.ProductStandardCost.id == header_id)
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="標準原価が見つかりません")
    return _build_detail(row)


async def _persist_standard_cost(
    db: AsyncSession,
    body: s.ProductStandardCostCreate | s.ProductStandardCostUpdate,
    *,
    existing: Optional[m.ProductStandardCost],
    user: Optional[User],
    full_replace_lines: bool,
) -> m.ProductStandardCost:
    if isinstance(body, s.ProductStandardCostCreate):
        version_id = body.version_id
        product_cd = body.product_cd
        pname = body.product_name or (await _product_name(db, product_cd))
        mats = list(body.material_lines)
        labs = list(body.labor_lines)
        ovs = list(body.overhead_lines)
        mt, lt, ot = _rollup_header_totals(
            mats,
            labs,
            ovs,
            body.material_cost_std,
            body.labor_cost_std,
            body.overhead_cost_std,
        )
        tt = mt + lt + ot
        row = m.ProductStandardCost(
            version_id=version_id,
            product_cd=product_cd,
            product_name=pname,
            material_cost_std=mt,
            labor_cost_std=lt,
            overhead_cost_std=ot,
            total_cost_std=tt,
            currency=body.currency,
            source=body.source,
            remarks=body.remarks,
            created_by=user.username if user else None,
            updated_by=user.username if user else None,
        )
        db.add(row)
        await db.flush()
        for x in mats:
            amt = _rollup_mat_line(x)
            db.add(
                m.ProductStandardMaterialLine(
                    header_id=row.id,
                    line_no=x.line_no,
                    material_cd=x.material_cd,
                    material_name=x.material_name,
                    qty_per_unit=x.qty_per_unit,
                    scrap_pct=x.scrap_pct,
                    standard_unit_price=x.standard_unit_price,
                    amount=amt,
                    bom_line_id=x.bom_line_id,
                )
            )
        for x in labs:
            amt = _rollup_lab_line(x)
            db.add(
                m.ProductStandardLaborLine(
                    header_id=row.id,
                    line_no=x.line_no,
                    process_cd=x.process_cd,
                    process_name=x.process_name,
                    std_hours=x.std_hours,
                    setup_hours=x.setup_hours,
                    labor_rate_per_hour=x.labor_rate_per_hour,
                    cost_center_cd=x.cost_center_cd,
                    amount=amt,
                )
            )
        for x in ovs:
            amt = _rollup_oh_line(x)
            db.add(
                m.ProductStandardOverheadLine(
                    header_id=row.id,
                    line_no=x.line_no,
                    cost_center_cd=x.cost_center_cd,
                    allocation_basis=x.allocation_basis,
                    basis_qty_per_unit=x.basis_qty_per_unit,
                    overhead_rate=x.overhead_rate,
                    amount=amt,
                )
            )
        return row

    assert existing is not None
    data = body.model_dump(exclude_unset=True)
    mats = data.pop("material_lines", None)
    labs = data.pop("labor_lines", None)
    ovs = data.pop("overhead_lines", None)
    for k in ("material_cost_std", "labor_cost_std", "overhead_cost_std"):
        if k in data and data[k] is not None:
            pass
    if data.get("product_name") is None and data.get("product_cd"):
        data["product_name"] = await _product_name(db, existing.product_cd)
    for k, v in data.items():
        if v is not None and k not in ("material_cost_std", "labor_cost_std", "overhead_cost_std"):
            setattr(existing, k, v)

    if full_replace_lines and mats is not None and labs is not None and ovs is not None:
        await db.execute(
            delete(m.ProductStandardMaterialLine).where(m.ProductStandardMaterialLine.header_id == existing.id)
        )
        await db.execute(delete(m.ProductStandardLaborLine).where(m.ProductStandardLaborLine.header_id == existing.id))
        await db.execute(
            delete(m.ProductStandardOverheadLine).where(m.ProductStandardOverheadLine.header_id == existing.id)
        )
        mat_in = [s.ProductStandardMaterialLineIn.model_validate(x) for x in mats]
        lab_in = [s.ProductStandardLaborLineIn.model_validate(x) for x in labs]
        oh_in = [s.ProductStandardOverheadLineIn.model_validate(x) for x in ovs]
        mt, lt, ot = _rollup_header_totals(
            mat_in,
            lab_in,
            oh_in,
            body.material_cost_std,
            body.labor_cost_std,
            body.overhead_cost_std,
        )
        existing.material_cost_std = mt
        existing.labor_cost_std = lt
        existing.overhead_cost_std = ot
        existing.total_cost_std = mt + lt + ot
        existing.updated_by = user.username if user else None
        await db.flush()
        for x in mat_in:
            amt = _rollup_mat_line(x)
            db.add(
                m.ProductStandardMaterialLine(
                    header_id=existing.id,
                    line_no=x.line_no,
                    material_cd=x.material_cd,
                    material_name=x.material_name,
                    qty_per_unit=x.qty_per_unit,
                    scrap_pct=x.scrap_pct,
                    standard_unit_price=x.standard_unit_price,
                    amount=amt,
                    bom_line_id=x.bom_line_id,
                )
            )
        for x in lab_in:
            amt = _rollup_lab_line(x)
            db.add(
                m.ProductStandardLaborLine(
                    header_id=existing.id,
                    line_no=x.line_no,
                    process_cd=x.process_cd,
                    process_name=x.process_name,
                    std_hours=x.std_hours,
                    setup_hours=x.setup_hours,
                    labor_rate_per_hour=x.labor_rate_per_hour,
                    cost_center_cd=x.cost_center_cd,
                    amount=amt,
                )
            )
        for x in oh_in:
            amt = _rollup_oh_line(x)
            db.add(
                m.ProductStandardOverheadLine(
                    header_id=existing.id,
                    line_no=x.line_no,
                    cost_center_cd=x.cost_center_cd,
                    allocation_basis=x.allocation_basis,
                    basis_qty_per_unit=x.basis_qty_per_unit,
                    overhead_rate=x.overhead_rate,
                    amount=amt,
                )
            )
    else:
        # ヘッダ金額のみ部分更新
        if body.material_cost_std is not None:
            existing.material_cost_std = body.material_cost_std
        if body.labor_cost_std is not None:
            existing.labor_cost_std = body.labor_cost_std
        if body.overhead_cost_std is not None:
            existing.overhead_cost_std = body.overhead_cost_std
        existing.total_cost_std = _dec(existing.material_cost_std) + _dec(existing.labor_cost_std) + _dec(
            existing.overhead_cost_std
        )
        existing.updated_by = user.username if user else None
    return existing


@router.post("/products", response_model=s.ProductStandardCostDetail)
async def create_product_standard(
    body: s.ProductStandardCostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(
        select(m.ProductStandardCost).where(
            m.ProductStandardCost.version_id == body.version_id,
            m.ProductStandardCost.product_cd == body.product_cd,
        )
    )
    if r.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同一バージョン・品番の標準原価が既に存在します")
    row = await _persist_standard_cost(db, body, existing=None, user=current_user, full_replace_lines=False)
    await db.commit()
    await db.refresh(row)
    r2 = await db.execute(
        select(m.ProductStandardCost)
        .options(
            selectinload(m.ProductStandardCost.material_lines),
            selectinload(m.ProductStandardCost.labor_lines),
            selectinload(m.ProductStandardCost.overhead_lines),
        )
        .where(m.ProductStandardCost.id == row.id)
    )
    return _build_detail(r2.scalar_one())


@router.put("/products/{header_id}", response_model=s.ProductStandardCostDetail)
async def update_product_standard(
    header_id: int,
    body: s.ProductStandardCostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(
        select(m.ProductStandardCost).options(
            selectinload(m.ProductStandardCost.material_lines),
            selectinload(m.ProductStandardCost.labor_lines),
            selectinload(m.ProductStandardCost.overhead_lines),
        ).where(m.ProductStandardCost.id == header_id)
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="標準原価が見つかりません")
    full = (
        body.material_lines is not None
        and body.labor_lines is not None
        and body.overhead_lines is not None
    )
    await _persist_standard_cost(db, body, existing=row, user=current_user, full_replace_lines=full)
    await db.commit()
    r3 = await db.execute(
        select(m.ProductStandardCost)
        .options(
            selectinload(m.ProductStandardCost.material_lines),
            selectinload(m.ProductStandardCost.labor_lines),
            selectinload(m.ProductStandardCost.overhead_lines),
        )
        .where(m.ProductStandardCost.id == header_id)
    )
    return _build_detail(r3.scalar_one())


@router.delete("/products/{header_id}")
async def delete_product_standard(
    header_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(select(m.ProductStandardCost).where(m.ProductStandardCost.id == header_id))
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="標準原価が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# 会計期間・月次品目
# ---------------------------------------------------------------------------


@router.get("/periods", response_model=List[s.CostAccountingPeriodOut])
async def list_periods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(select(m.CostAccountingPeriod).order_by(m.CostAccountingPeriod.year_month.desc()))
    return list(r.scalars().all())


@router.post("/periods", response_model=s.CostAccountingPeriodOut)
async def create_period(
    body: s.CostAccountingPeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = m.CostAccountingPeriod(year_month=body.year_month, status=body.status, notes=body.notes)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="同一の年月の期間が既に存在します")
    await db.refresh(row)
    return row


@router.get("/periods/{period_id}/products", response_model=List[s.CostPeriodProductCostOut])
async def list_period_products(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(
        select(m.CostPeriodProductCost)
        .where(m.CostPeriodProductCost.period_id == period_id)
        .order_by(m.CostPeriodProductCost.product_cd.asc())
    )
    rows = list(r.scalars().all())
    return [_period_line_to_out(x) for x in rows]


@router.post("/periods/{period_id}/products", response_model=s.CostPeriodProductCostOut)
async def create_period_product(
    period_id: int,
    body: s.CostPeriodProductCostIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    pr = await db.execute(select(m.CostAccountingPeriod).where(m.CostAccountingPeriod.id == period_id))
    period = pr.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="会計期間が見つかりません")
    ym = period.year_month
    r = await db.execute(
        select(m.CostPeriodProductCost).where(
            m.CostPeriodProductCost.period_id == period_id,
            m.CostPeriodProductCost.product_cd == body.product_cd,
        )
    )
    if r.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同一品番の行が既に存在します")
    pname = body.product_name or (await _product_name(db, body.product_cd))
    row = m.CostPeriodProductCost(
        period_id=period_id,
        version_id=body.version_id,
        product_cd=body.product_cd,
        product_name=pname,
        finished_good_qty=body.finished_good_qty,
        wip_equivalent_qty=body.wip_equivalent_qty,
        actual_material_cost=body.actual_material_cost,
        actual_labor_cost=body.actual_labor_cost,
        actual_overhead_cost=body.actual_overhead_cost,
        variance_material_price=body.variance_material_price,
        variance_material_qty=body.variance_material_qty,
        variance_labor_rate=body.variance_labor_rate,
        variance_labor_efficiency=body.variance_labor_efficiency,
        variance_moh_budget=body.variance_moh_budget,
        variance_moh_capacity=body.variance_moh_capacity,
        variance_moh_efficiency=body.variance_moh_efficiency,
        remarks=body.remarks,
        updated_by=current_user.username if current_user else None,
    )
    db.add(row)
    await db.flush()
    try:
        await _apply_standard_allowed_to_line(db, row, ym, current_user)
    except HTTPException:
        await db.rollback()
        raise
    await db.commit()
    await db.refresh(row)
    return _period_line_to_out(row)


@router.put("/periods/{period_id}/products/{line_id}", response_model=s.CostPeriodProductCostOut)
async def update_period_product(
    period_id: int,
    line_id: int,
    body: s.CostPeriodProductCostIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(
        select(m.CostPeriodProductCost).where(
            m.CostPeriodProductCost.id == line_id,
            m.CostPeriodProductCost.period_id == period_id,
        )
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="行が見つかりません")
    for k, v in body.model_dump(exclude_unset=False).items():
        if k == "product_cd":
            continue
        setattr(row, k, v)
    row.updated_by = current_user.username if current_user else None
    await db.commit()
    await db.refresh(row)
    return _period_line_to_out(row)


@router.delete("/periods/{period_id}/products/{line_id}")
async def delete_period_product(
    period_id: int,
    line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(
        select(m.CostPeriodProductCost).where(
            m.CostPeriodProductCost.id == line_id,
            m.CostPeriodProductCost.period_id == period_id,
        )
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="行が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"ok": True}


async def _apply_standard_allowed_to_line(
    db: AsyncSession,
    line: m.CostPeriodProductCost,
    year_month: str,
    current_user: Optional[User],
) -> None:
    vid = await _resolve_version_for_month(db, year_month, line.version_id)
    if not vid:
        raise HTTPException(
            status_code=400,
            detail="該当年度のアクティブな標準原価バージョンがありません。version_id を指定するか、バージョンを active にしてください。",
        )
    costs = await _get_standard_unit_costs(db, vid, line.product_cd)
    if not costs:
        raise HTTPException(
            status_code=400,
            detail=f"品番 {line.product_cd} の標準原価がバージョン {vid} に存在しません",
        )
    sm, sl, so = costs
    eq = _dec(line.finished_good_qty) + _dec(line.wip_equivalent_qty)
    line.version_id = vid
    line.standard_material_allowed = (eq * sm).quantize(Decimal("0.01"))
    line.standard_labor_allowed = (eq * sl).quantize(Decimal("0.01"))
    line.standard_overhead_allowed = (eq * so).quantize(Decimal("0.01"))
    line.updated_by = current_user.username if current_user else None


@router.post("/periods/{period_id}/products/{line_id}/recalculate", response_model=s.CostPeriodProductCostOut)
async def api_recalculate_period_product(
    period_id: int,
    line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    r = await db.execute(
        select(m.CostPeriodProductCost, m.CostAccountingPeriod.year_month)
        .join(m.CostAccountingPeriod, m.CostAccountingPeriod.id == m.CostPeriodProductCost.period_id)
        .where(m.CostPeriodProductCost.id == line_id, m.CostPeriodProductCost.period_id == period_id)
    )
    tup = r.one_or_none()
    if not tup:
        raise HTTPException(status_code=404, detail="行が見つかりません")
    line, ym = tup
    await _apply_standard_allowed_to_line(db, line, ym, current_user)
    await db.commit()
    await db.refresh(line)
    return _period_line_to_out(line)

"""
材料マスタ API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import io
import csv

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Material, Supplier
from app.modules.master.schemas import MaterialCreate, MaterialUpdate

router = APIRouter()


def _row_to_dict(row: Material, supplier_name: Optional[str] = None) -> dict:
    d = {
        "id": row.id,
        "material_cd": row.material_cd,
        "material_name": row.material_name,
        "material_type": row.material_type,
        "standard_spec": row.standard_spec,
        "unit": row.unit,
        "diameter": float(row.diameter) if row.diameter is not None else None,
        "thickness": float(row.thickness) if row.thickness is not None else None,
        "length": float(row.length) if row.length is not None else None,
        "supply_classification": row.supply_classification,
        "pieces_per_bundle": row.pieces_per_bundle,
        "usegae": row.usegae,
        "supplier_cd": row.supplier_cd,
        "unit_price": float(row.unit_price) if row.unit_price is not None else None,
        "long_weight": float(row.long_weight) if row.long_weight is not None else None,
        "single_price": float(row.single_price) if row.single_price is not None else None,
        "safety_stock": row.safety_stock,
        "lead_time": row.lead_time,
        "storage_location": row.storage_location,
        "status": row.status,
        "tolerance_range": row.tolerance_range,
        "tolerance_1": float(row.tolerance_1) if row.tolerance_1 is not None else None,
        "tolerance_2": float(row.tolerance_2) if row.tolerance_2 is not None else None,
        "range_value": row.range_value,
        "min_value": float(row.min_value) if row.min_value is not None else None,
        "max_value": float(row.max_value) if row.max_value is not None else None,
        "actual_value_1": float(row.actual_value_1) if row.actual_value_1 is not None else None,
        "actual_value_2": float(row.actual_value_2) if row.actual_value_2 is not None else None,
        "actual_value_3": float(row.actual_value_3) if row.actual_value_3 is not None else None,
        "representative_model": row.representative_model,
        "note": row.note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
    if supplier_name is not None:
        d["supplier_name"] = supplier_name
    return d


@router.get("")
async def get_material_list(
    keyword: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    material_type: Optional[str] = Query(None),
    supply_classification: Optional[str] = Query(None),
    usegae: Optional[str] = Query(None),
    storage_location: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料一覧取得"""
    query = select(Material)
    if keyword:
        query = query.where(
            or_(
                Material.material_name.like(f"%{keyword}%"),
                Material.material_cd.like(f"%{keyword}%"),
                Material.standard_spec.like(f"%{keyword}%"),
                Material.supplier_cd.like(f"%{keyword}%"),
            )
        )
    if status is not None:
        query = query.where(Material.status == status)
    if material_type:
        query = query.where(Material.material_type == material_type)
    if supply_classification:
        query = query.where(Material.supply_classification == supply_classification)
    if usegae:
        query = query.where(Material.usegae == usegae)
    if storage_location:
        query = query.where(Material.storage_location.like(f"%{storage_location}%"))

    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()

    # 仕入先マスタから仕入先名を取得（supplier_cd -> supplier_name）
    supplier_cds = {r.supplier_cd for r in rows if r.supplier_cd}
    supp_map = {}
    if supplier_cds:
        supp_q = select(Supplier).where(Supplier.supplier_cd.in_(supplier_cds))
        supp_res = await db.execute(supp_q)
        for s in supp_res.scalars().all():
            supp_map[s.supplier_cd] = s.supplier_name

    return {
        "success": True,
        "data": {
            "list": [_row_to_dict(r, supp_map.get(r.supplier_cd) if r.supplier_cd else None) for r in rows],
            "total": total,
        },
    }


@router.get("/max-cd")
async def get_max_material_cd(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """最大材料CD取得"""
    q = select(Material.material_cd)
    res = await db.execute(q)
    codes = [r for r in res.scalars().all() if r and str(r).isdigit()]
    if not codes:
        return {"max_code": 10000}
    return {"max_code": max(int(c) for c in codes)}


@router.get("/{material_id}")
async def get_material_by_id(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料1件取得"""
    q = select(Material).where(Material.id == material_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="材料が見つかりません")
    supplier_name = None
    if row.supplier_cd:
        sq = select(Supplier).where(Supplier.supplier_cd == row.supplier_cd)
        sr = await db.execute(sq)
        sup = sr.scalar_one_or_none()
        if sup:
            supplier_name = sup.supplier_name
    return _row_to_dict(row, supplier_name)


@router.post("")
async def create_material(
    body: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料新規登録"""
    q = select(Material).where(Material.material_cd == body.material_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="材料CDは既に存在します")
    row = Material(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    supplier_name = None
    if row.supplier_cd:
        sq = select(Supplier).where(Supplier.supplier_cd == row.supplier_cd)
        sr = await db.execute(sq)
        sup = sr.scalar_one_or_none()
        if sup:
            supplier_name = sup.supplier_name
    return _row_to_dict(row, supplier_name)


@router.put("/{material_id}")
async def update_material(
    material_id: int,
    body: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料更新"""
    q = select(Material).where(Material.id == material_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="材料が見つかりません")
    for k, v in body.model_dump().items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    supplier_name = None
    if row.supplier_cd:
        sq = select(Supplier).where(Supplier.supplier_cd == row.supplier_cd)
        sr = await db.execute(sq)
        sup = sr.scalar_one_or_none()
        if sup:
            supplier_name = sup.supplier_name
    return _row_to_dict(row, supplier_name)


@router.delete("/{material_id}")
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料削除"""
    q = select(Material).where(Material.id == material_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="材料が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


class ExportCsvItem(BaseModel):
    material_cd: Optional[str] = None
    material_name: Optional[str] = None


@router.post("/export-csv")
async def export_materials_csv(
    body: list[ExportCsvItem],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """CSV出力"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["material_cd", "material_name"])
    for item in body:
        writer.writerow([item.material_cd or "", item.material_name or ""])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=materials.csv"},
    )

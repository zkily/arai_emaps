"""
材料受入ログ API（material_logs）
GET    /api/material/receiving              一覧取得（ページネーション・フィルタ）
GET    /api/material/receiving/{id}         詳細取得
POST   /api/material/receiving              新規登録
PUT    /api/material/receiving/{id}         更新
DELETE /api/material/receiving/{id}         削除
GET    /api/material/receiving/suppliers    仕入先一覧
GET    /api/material/receiving/materials    材料名一覧
POST   /api/material/receiving/import-csv  CSVインポート
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct
from typing import Optional, List
from datetime import date

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.material.models import MaterialLog
from app.modules.material.schemas import (
    MaterialLogCreate,
    MaterialLogUpdate,
    MaterialLogResponse,
)

router = APIRouter()


def _log_to_dict(r: MaterialLog) -> dict:
    return {
        "id": r.id,
        "item": r.item,
        "material_cd": r.material_cd,
        "material_name": r.material_name,
        "process_cd": r.process_cd,
        "log_date": r.log_date.isoformat() if r.log_date else None,
        "log_time": str(r.log_time) if r.log_time else None,
        "hd_no": r.hd_no,
        "pieces_per_bundle": r.pieces_per_bundle,
        "quantity": r.quantity,
        "bundle_quantity": r.bundle_quantity,
        "manufacture_no": r.manufacture_no,
        "manufacture_date": r.manufacture_date.isoformat() if r.manufacture_date else None,
        "length": r.length,
        "outer_diameter1": float(r.outer_diameter1) if r.outer_diameter1 is not None else None,
        "outer_diameter2": float(r.outer_diameter2) if r.outer_diameter2 is not None else None,
        "magnetic": r.magnetic,
        "appearance": r.appearance,
        "supplier": r.supplier,
        "material_quality": r.material_quality,
        "remarks": r.remarks,
        "note": r.note,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.get("/suppliers")
async def get_suppliers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """仕入先一覧（受入ログから抽出）"""
    q = select(distinct(MaterialLog.supplier)).where(MaterialLog.supplier.isnot(None)).order_by(MaterialLog.supplier)
    result = await db.execute(q)
    suppliers = [row[0] for row in result.all() if row[0]]
    return {"success": True, "data": suppliers}


@router.get("/materials")
async def get_material_names(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料名一覧（受入ログから抽出）"""
    q = (
        select(distinct(MaterialLog.material_cd), MaterialLog.material_name)
        .where(MaterialLog.material_cd.isnot(None))
        .order_by(MaterialLog.material_cd)
    )
    result = await db.execute(q)
    rows = result.all()
    return {
        "success": True,
        "data": [{"material_cd": r[0], "material_name": r[1]} for r in rows],
    }


@router.get("")
async def list_receiving_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=1000),
    keyword: Optional[str] = Query(None),
    material_cd: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ一覧取得"""
    q = select(MaterialLog)

    if keyword:
        kw = f"%{keyword}%"
        q = q.where(
            or_(
                MaterialLog.material_cd.ilike(kw),
                MaterialLog.material_name.ilike(kw),
                MaterialLog.manufacture_no.ilike(kw),
                MaterialLog.supplier.ilike(kw),
                MaterialLog.hd_no.ilike(kw),
            )
        )
    if material_cd:
        q = q.where(MaterialLog.material_cd == material_cd)
    if supplier:
        q = q.where(MaterialLog.supplier == supplier)
    if startDate:
        q = q.where(MaterialLog.log_date >= date.fromisoformat(startDate))
    if endDate:
        q = q.where(MaterialLog.log_date <= date.fromisoformat(endDate))

    total_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    q = q.order_by(MaterialLog.log_date.desc(), MaterialLog.log_time.desc(), MaterialLog.id.desc())
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "success": True,
        "data": {"list": [_log_to_dict(r) for r in rows], "total": total},
    }


@router.get("/{item_id}")
async def get_receiving_log(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ詳細"""
    result = await db.execute(select(MaterialLog).where(MaterialLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    return {"success": True, "data": _log_to_dict(row)}


@router.post("")
async def create_receiving_log(
    body: MaterialLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ新規登録"""
    row = MaterialLog(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _log_to_dict(row)}


@router.put("/{item_id}")
async def update_receiving_log(
    item_id: int,
    body: MaterialLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ更新"""
    result = await db.execute(select(MaterialLog).where(MaterialLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _log_to_dict(row)}


@router.delete("/{item_id}")
async def delete_receiving_log(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ削除"""
    result = await db.execute(select(MaterialLog).where(MaterialLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}


@router.post("/import-csv")
async def import_csv_logs(
    rows: List[MaterialLogCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """CSVデータ一括インポート"""
    created = 0
    for item in rows:
        row = MaterialLog(**item.model_dump())
        db.add(row)
        created += 1
    await db.commit()
    return {"success": True, "created": created}

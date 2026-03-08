"""
材料検品基準マスタ API（material_inspection_master）
GET    /api/material/inspection-master        一覧取得
POST   /api/material/inspection-master        新規登録
PUT    /api/material/inspection-master/{id}   更新
DELETE /api/material/inspection-master/{id}   削除
DELETE /api/material/inspection-master/batch  一括削除
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.material.models import MaterialInspectionMaster
from app.modules.material.schemas import (
    InspectionMasterCreate,
    InspectionMasterUpdate,
    InspectionMasterResponse,
)

router = APIRouter()


@router.get("")
async def list_inspection_masters(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検品基準一覧取得（キーワード検索・ページネーション）"""
    q = select(MaterialInspectionMaster)
    if keyword:
        q = q.where(
            or_(
                MaterialInspectionMaster.inspection_cd.ilike(f"%{keyword}%"),
                MaterialInspectionMaster.inspection_standard.ilike(f"%{keyword}%"),
            )
        )

    total_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    q = q.order_by(MaterialInspectionMaster.inspection_cd).offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "success": True,
        "data": {
            "list": [InspectionMasterResponse.model_validate(r) for r in rows],
            "total": total,
        },
    }


@router.post("")
async def create_inspection_master(
    body: InspectionMasterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検品基準新規登録"""
    existing = await db.execute(
        select(MaterialInspectionMaster).where(
            MaterialInspectionMaster.inspection_cd == body.inspection_cd
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"検験代码 '{body.inspection_cd}' は既に存在します")

    row = MaterialInspectionMaster(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": InspectionMasterResponse.model_validate(row)}


@router.put("/{item_id}")
async def update_inspection_master(
    item_id: int,
    body: InspectionMasterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検品基準更新"""
    result = await db.execute(
        select(MaterialInspectionMaster).where(MaterialInspectionMaster.id == item_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)

    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": InspectionMasterResponse.model_validate(row)}


@router.delete("/batch")
async def batch_delete_inspection_masters(
    ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """一括削除"""
    result = await db.execute(
        select(MaterialInspectionMaster).where(MaterialInspectionMaster.id.in_(ids))
    )
    rows = result.scalars().all()
    for row in rows:
        await db.delete(row)
    await db.commit()
    return {"success": True, "deleted": len(rows)}


@router.delete("/{item_id}")
async def delete_inspection_master(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検品基準削除"""
    result = await db.execute(
        select(MaterialInspectionMaster).where(MaterialInspectionMaster.id == item_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}

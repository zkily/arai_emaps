"""
外注工程製品マスタ API（outsourcing_process_products）
一覧・統計・CRUD・有効/無効切替
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, case, distinct
from typing import Optional, Any
from pydantic import BaseModel

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.outsourcing.models import OutsourcingProcessProduct

router = APIRouter()

PROCESS_TYPE_NAMES = {
    "cutting": "外注切断",
    "forming": "外注成型",
    "plating": "外注メッキ",
    "welding": "外注溶接",
    "inspection": "外注検査",
    "processing": "外注加工",
}


def _row_to_dict(r: OutsourcingProcessProduct) -> dict:
    out = {
        "id": r.id,
        "process_type": r.process_type,
        "process_type_name": PROCESS_TYPE_NAMES.get(r.process_type or "", r.process_type or ""),
        "supplier_cd": r.supplier_cd,
        "supplier_name": r.supplier_name,
        "product_cd": r.product_cd,
        "product_name": r.product_name,
        "specification": r.specification,
        "unit_price": float(r.unit_price) if r.unit_price is not None else 0,
        "delivery_lead_time": r.delivery_lead_time if r.delivery_lead_time is not None else 0,
        "delivery_location": r.delivery_location,
        "category": r.category,
        "content": r.content,
        "remarks": r.remarks,
        "is_active": r.is_active if r.is_active is not None else True,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }
    return out


# ----- 一覧（検索・ページネーション） -----
@router.get("")
async def get_process_products(
    processType: Optional[str] = Query(None, alias="processType", description="工程種別"),
    keyword: Optional[str] = Query(None, description="キーワード（外注先/品番/品名）"),
    supplierCd: Optional[str] = Query(None, alias="supplierCd", description="外注先コード"),
    productCd: Optional[str] = Query(None, alias="productCd", description="品番"),
    isActive: Optional[str] = Query(None, alias="isActive", description="有効フラグ: true/false/all"),
    page: int = Query(1, ge=1, description="ページ番号"),
    pageSize: int = Query(50, ge=1, le=500, alias="pageSize", description="1ページ件数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    外注工程製品一覧取得（オプション: 工程種別・キーワード・外注先・品番・有効フラグ・ページネーション）。
    従来の processType + supplierCd 必須の呼び出しにも対応（その場合は全件に近い絞り込み）。
    """
    q = select(OutsourcingProcessProduct)
    count_q = select(func.count()).select_from(OutsourcingProcessProduct)

    conditions = []
    if processType and processType != "all":
        conditions.append(OutsourcingProcessProduct.process_type == processType)
    if supplierCd:
        conditions.append(OutsourcingProcessProduct.supplier_cd == supplierCd)
    if productCd:
        conditions.append(OutsourcingProcessProduct.product_cd == productCd)
    if isActive and isActive != "all":
        if isActive == "true":
            conditions.append(OutsourcingProcessProduct.is_active == True)
        elif isActive == "false":
            conditions.append(OutsourcingProcessProduct.is_active == False)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                OutsourcingProcessProduct.supplier_cd.ilike(kw),
                OutsourcingProcessProduct.supplier_name.ilike(kw),
                OutsourcingProcessProduct.product_cd.ilike(kw),
                OutsourcingProcessProduct.product_name.ilike(kw),
            )
        )

    if conditions:
        q = q.where(and_(*conditions))
        count_q = count_q.where(and_(*conditions))

    # 総件数
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    q = q.order_by(
        OutsourcingProcessProduct.process_type,
        OutsourcingProcessProduct.supplier_cd,
        OutsourcingProcessProduct.product_cd,
    )
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()

    return {
        "success": True,
        "data": [_row_to_dict(r) for r in rows],
        "pagination": {
            "page": page,
            "pageSize": pageSize,
            "total": total,
        },
    }


# ----- 統計 -----
@router.get("/stats")
async def get_process_product_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注工程製品の統計（総数・有効数・外注先数・工程別件数）"""
    # 総件数・有効件数
    total_q = select(
        func.count(OutsourcingProcessProduct.id).label("total_count"),
        func.sum(case((OutsourcingProcessProduct.is_active == True, 1), else_=0)).label("active_count"),
        func.count(distinct(OutsourcingProcessProduct.supplier_cd)).label("supplier_count"),
    ).select_from(OutsourcingProcessProduct)
    total_row = (await db.execute(total_q)).one()
    total_count = total_row.total_count or 0
    active_count = total_row.active_count or 0
    supplier_count = total_row.supplier_count or 0

    # 工程別件数
    by_type_q = (
        select(
            OutsourcingProcessProduct.process_type,
            func.count(OutsourcingProcessProduct.id).label("total_count"),
        )
        .group_by(OutsourcingProcessProduct.process_type)
    )
    by_type_result = await db.execute(by_type_q)
    by_process_type = [
        {"process_type": r.process_type, "total_count": r.total_count}
        for r in by_type_result.all()
    ]

    return {
        "success": True,
        "data": {
            "total": {
                "total_count": total_count,
                "active_count": active_count,
                "supplier_count": supplier_count,
            },
            "byProcessType": by_process_type,
        },
    }


# ----- 単一取得（工程・外注先・品番で取得する既存用途用） -----
@router.get("/by-keys")
async def get_process_products_by_keys(
    processType: str = Query(..., description="工程種別"),
    supplierCd: str = Query(..., description="外注先コード"),
    isActive: Optional[bool] = Query(None, alias="isActive"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程種別・外注先で絞り込み（注文画面等で利用）"""
    q = select(OutsourcingProcessProduct).where(
        OutsourcingProcessProduct.process_type == processType,
        OutsourcingProcessProduct.supplier_cd == supplierCd,
    )
    if isActive is not None:
        q = q.where(OutsourcingProcessProduct.is_active == isActive)
    q = q.order_by(OutsourcingProcessProduct.product_cd)
    result = await db.execute(q)
    rows = result.scalars().all()
    return {"success": True, "data": [_row_to_dict(r) for r in rows]}


# ----- 新規作成 -----
class ProcessProductCreate(BaseModel):
    process_type: str
    supplier_cd: str
    supplier_name: Optional[str] = None
    product_cd: str
    product_name: Optional[str] = None
    specification: Optional[str] = None
    unit_price: Optional[float] = 0
    delivery_lead_time: Optional[int] = 7
    delivery_location: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = True


@router.post("")
async def create_process_product(
    body: ProcessProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注工程製品を新規登録"""
    existing = await db.execute(
        select(OutsourcingProcessProduct).where(
            OutsourcingProcessProduct.process_type == body.process_type,
            OutsourcingProcessProduct.supplier_cd == body.supplier_cd,
            OutsourcingProcessProduct.product_cd == body.product_cd,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="同じ工程種別・外注先・品番の組み合わせは既に登録されています。",
        )
    row = OutsourcingProcessProduct(
        process_type=body.process_type,
        supplier_cd=body.supplier_cd,
        supplier_name=body.supplier_name,
        product_cd=body.product_cd,
        product_name=body.product_name,
        specification=body.specification,
        unit_price=body.unit_price or 0,
        delivery_lead_time=body.delivery_lead_time if body.delivery_lead_time is not None else 7,
        delivery_location=body.delivery_location,
        category=body.category,
        content=body.content,
        remarks=body.remarks,
        is_active=body.is_active if body.is_active is not None else True,
        created_by=current_user.username if current_user else None,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _row_to_dict(row)}


# ----- 更新 -----
class ProcessProductUpdate(BaseModel):
    supplier_name: Optional[str] = None
    product_name: Optional[str] = None
    specification: Optional[str] = None
    unit_price: Optional[float] = None
    delivery_lead_time: Optional[int] = None
    delivery_location: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


@router.put("/{id}")
async def update_process_product(
    id: int,
    body: ProcessProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注工程製品を更新"""
    result = await db.execute(select(OutsourcingProcessProduct).where(OutsourcingProcessProduct.id == id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="対象の外注工程製品が見つかりません。")
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(row, k, v)
    row.updated_by = current_user.username if current_user else None
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _row_to_dict(row)}


# ----- 有効/無効切替 -----
@router.patch("/{id}/toggle")
async def toggle_process_product_status(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """有効フラグを反転"""
    result = await db.execute(select(OutsourcingProcessProduct).where(OutsourcingProcessProduct.id == id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="対象の外注工程製品が見つかりません。")
    row.is_active = not row.is_active if row.is_active else True
    row.updated_by = current_user.username if current_user else None
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _row_to_dict(row)}


# ----- 削除 -----
@router.delete("/{id}")
async def delete_process_product(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注工程製品を削除"""
    result = await db.execute(select(OutsourcingProcessProduct).where(OutsourcingProcessProduct.id == id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="対象の外注工程製品が見つかりません。")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}

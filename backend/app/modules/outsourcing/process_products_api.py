"""
外注工程製品マスタ API（outsourcing_process_products）
GET /api/outsourcing/process-products?processType=welding&supplierCd=OS-005&isActive=true
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.outsourcing.models import OutsourcingProcessProduct

router = APIRouter()


def _row_to_dict(r: OutsourcingProcessProduct) -> dict:
    return {
        "id": r.id,
        "process_type": r.process_type,
        "supplier_cd": r.supplier_cd,
        "supplier_name": r.supplier_name,
        "product_cd": r.product_cd,
        "product_name": r.product_name,
        "specification": r.specification,
        "unit_price": float(r.unit_price) if r.unit_price is not None else 0,
        "delivery_lead_time": r.delivery_lead_time or 0,
        "delivery_location": r.delivery_location,
        "category": r.category,
        "content": r.content,
        "remarks": r.remarks,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.get("")
async def get_process_products(
    processType: str = Query(..., description="工程種別（welding / plating 等）"),
    supplierCd: str = Query(..., description="外注先コード"),
    isActive: Optional[bool] = Query(None, alias="isActive"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外注工程製品一覧取得（工程種別・外注先で絞り込み）"""
    query = select(OutsourcingProcessProduct).where(
        OutsourcingProcessProduct.process_type == processType,
        OutsourcingProcessProduct.supplier_cd == supplierCd,
    )
    if isActive is not None:
        query = query.where(OutsourcingProcessProduct.is_active == isActive)
    query = query.order_by(OutsourcingProcessProduct.product_cd)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {"success": True, "data": [_row_to_dict(r) for r in rows]}

"""
外注在庫履歴 API（outsourcing_stock_transactions）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.outsourcing.models import OutsourcingStockTransaction

router = APIRouter()


@router.get("/history")
async def get_outsourcing_stock_history(
    processType: str = Query(..., alias="processType"),
    productCd: str = Query(..., alias="productCd"),
    supplierCd: str = Query(..., alias="supplierCd"),
    weldingType: Optional[str] = Query(None, alias="weldingType"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫変動履歴（outsourcing_stock_transactions）品番・外注先・工程種別で取得"""
    q = (
        select(OutsourcingStockTransaction)
        .where(OutsourcingStockTransaction.process_type == processType)
        .where(OutsourcingStockTransaction.product_cd == productCd)
        .where(OutsourcingStockTransaction.supplier_cd == supplierCd)
    )
    # 溶接の場合は welding_type でさらに絞る（履歴テーブルに welding_type が無い場合は無視）
    # outsourcing_stock_transactions には welding_type カラムは無いため、ここでは絞らない
    q = q.order_by(OutsourcingStockTransaction.transaction_date.desc(), OutsourcingStockTransaction.id.desc())
    q = q.limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    data = [
        {
            "id": r.id,
            "transaction_date": r.transaction_date.isoformat() if r.transaction_date else None,
            "transaction_type": r.transaction_type,
            "process_type": r.process_type,
            "product_cd": r.product_cd,
            "product_name": r.product_name or "",
            "supplier_cd": r.supplier_cd,
            "related_no": r.related_no or "",
            "quantity": r.quantity or 0,
            "stock_after": r.stock_after,
            "operator": r.operator or "",
            "remarks": r.remarks or "",
        }
        for r in rows
    ]
    return {"success": True, "data": data}

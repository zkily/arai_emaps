"""
生産実績管理 API（stock_transaction_logs を工程・製品名・設備名付きで取得、集計）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from typing import Optional, List
from decimal import Decimal

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.erp.stock_transaction_log_models import StockTransactionLog
from app.modules.master.models import Process, Product, Machine

router = APIRouter(prefix="/production-actual-logs", tags=["ProductionActual"])


def _apply_filters(query, keyword, date_from, date_to, process_cd, transaction_type):
    if keyword and keyword.strip():
        q = f"%{keyword.strip()}%"
        query = query.where(
            (StockTransactionLog.target_cd.like(q)) | (StockTransactionLog.remarks.like(q))
        )
    if date_from:
        query = query.where(StockTransactionLog.transaction_time >= date_from)
    if date_to:
        query = query.where(StockTransactionLog.transaction_time <= f"{date_to} 23:59:59")
    if process_cd and process_cd.strip():
        query = query.where(StockTransactionLog.process_cd == process_cd.strip())
    if transaction_type and transaction_type.strip():
        query = query.where(StockTransactionLog.transaction_type == transaction_type.strip())
    return query


@router.get("")
async def get_production_actual_logs(
    keyword: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    process_cd: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=10000),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query("DESC"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産実績一覧（工程名・製品名・設備名付き）、stats、typeSummary、pagination を返す"""
    base = select(StockTransactionLog).where(True)
    base = _apply_filters(base, keyword, date_from, date_to, process_cd, transaction_type)

    # total count
    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # list with joins (Process, Product, Machine)
    list_q = (
        select(
            StockTransactionLog,
            Process.process_name,
            Product.product_name,
            Machine.machine_name,
        )
        .select_from(StockTransactionLog)
        .outerjoin(Process, StockTransactionLog.process_cd == Process.process_cd)
        .outerjoin(Product, StockTransactionLog.target_cd == Product.product_cd)
        .outerjoin(Machine, StockTransactionLog.machine_cd == Machine.machine_cd)
    )
    list_q = _apply_filters(list_q, keyword, date_from, date_to, process_cd, transaction_type)

    order_col = getattr(StockTransactionLog, sort_by, None) if sort_by else StockTransactionLog.transaction_time
    if order_col is not None:
        if sort_order and str(sort_order).upper() == "ASC":
            list_q = list_q.order_by(order_col.asc())
        else:
            list_q = list_q.order_by(order_col.desc())
    else:
        list_q = list_q.order_by(StockTransactionLog.transaction_time.desc())

    list_q = list_q.offset((page - 1) * limit).limit(limit)
    list_result = await db.execute(list_q)
    list_rows = list_result.all()

    items = []
    for row in list_rows:
        stl, pname, tname, mname = row[0], row[1], row[2], row[3]
        items.append({
            "id": stl.id,
            "stock_type": stl.stock_type or "",
            "transaction_type": stl.transaction_type or "",
            "target_cd": stl.target_cd or "",
            "target_name": (tname or "") if tname else "",
            "location_cd": stl.location_cd or "",
            "lot_no": stl.lot_no,
            "process_cd": stl.process_cd or "",
            "process_name": (pname or "") if pname else "",
            "machine_cd": stl.machine_cd or "",
            "machine_name": (mname or "") if mname else "",
            "quantity": float(stl.quantity) if stl.quantity is not None else 0,
            "unit": stl.unit or "",
            "order_no": stl.order_no,
            "related_log_id": stl.related_log_id,
            "operator_id": stl.operator_id,
            "operator_name": stl.operator_name,
            "transaction_time": stl.transaction_time.isoformat() if stl.transaction_time else None,
            "created_at": stl.created_at.isoformat() if stl.created_at else None,
            "source_file": getattr(stl, "source_file", None),
            "remarks": stl.remarks,
            "related_doc_no": stl.order_no,
        })

    # stats: total_records, total_quantity, avg_quantity, product_count, active_days
    stats_q = select(
        func.count(StockTransactionLog.id).label("total_records"),
        func.coalesce(func.sum(StockTransactionLog.quantity), 0).label("total_quantity"),
        func.count(distinct(StockTransactionLog.target_cd)).label("product_count"),
        func.count(distinct(func.date(StockTransactionLog.transaction_time))).label("active_days"),
    ).select_from(StockTransactionLog)
    stats_q = _apply_filters(stats_q, keyword, date_from, date_to, process_cd, transaction_type)
    stats_result = await db.execute(stats_q)
    stats_row = stats_result.one()
    total_records = int(stats_row.total_records or 0)
    total_quantity = float(stats_row.total_quantity or 0)
    product_count = int(stats_row.product_count or 0)
    active_days = int(stats_row.active_days or 0)
    avg_quantity = total_quantity / total_records if total_records else 0

    stats = {
        "total_records": total_records,
        "total_quantity": total_quantity,
        "avg_quantity": round(avg_quantity, 4),
        "product_count": product_count,
        "active_days": active_days,
    }

    # typeSummary: transaction_type, record_count, total_quantity（同一筛选条件）
    type_q = (
        select(
            StockTransactionLog.transaction_type,
            func.count(StockTransactionLog.id).label("record_count"),
            func.coalesce(func.sum(StockTransactionLog.quantity), 0).label("total_quantity"),
        )
        .select_from(StockTransactionLog)
        .group_by(StockTransactionLog.transaction_type)
    )
    type_q = _apply_filters(type_q, keyword, date_from, date_to, process_cd, transaction_type)
    type_result = await db.execute(type_q)
    type_rows = type_result.all()
    type_summary = [
        {
            "transaction_type": r[0] or "",
            "record_count": int(r[1] or 0),
            "total_quantity": float(r[2] or 0),
        }
        for r in type_rows
    ]

    return {
        "success": True,
        "data": {
            "list": items,
            "stats": stats,
            "typeSummary": type_summary,
            "pagination": {"total": total},
        },
    }

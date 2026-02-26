"""
外注ダッシュボード API
メッキ・溶接の注文/受入集計・直近納期・外注先サマリー
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, timedelta
from typing import Optional

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.outsourcing.models import (
    OutsourcingSupplier,
    PlatingOrder,
    PlatingReceiving,
    WeldingOrder,
    WeldingReceiving,
)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ダッシュボード集計：本日注文・未完了・本日受入・在庫警告・納期遅延"""
    today = date.today()

    # 本日の注文数（order_date = today）
    plating_today_q = select(func.count(PlatingOrder.id)).where(PlatingOrder.order_date == today)
    welding_today_q = select(func.count(WeldingOrder.id)).where(WeldingOrder.order_date == today)
    plating_today = (await db.execute(plating_today_q)).scalar() or 0
    welding_today = (await db.execute(welding_today_q)).scalar() or 0

    # 未完了注文（pending / ordered / partial）
    pending_statuses = ["pending", "ordered", "partial"]
    plating_pending_q = select(func.count(PlatingOrder.id)).where(
        PlatingOrder.status.in_(pending_statuses)
    )
    welding_pending_q = select(func.count(WeldingOrder.id)).where(
        WeldingOrder.status.in_(pending_statuses)
    )
    plating_pending = (await db.execute(plating_pending_q)).scalar() or 0
    welding_pending = (await db.execute(welding_pending_q)).scalar() or 0

    # 本日の受入数（receiving_date = today）
    plating_rec_q = select(func.count(PlatingReceiving.id)).where(
        PlatingReceiving.receiving_date == today
    )
    welding_rec_q = select(func.count(WeldingReceiving.id)).where(
        WeldingReceiving.receiving_date == today
    )
    plating_receivings = (await db.execute(plating_rec_q)).scalar() or 0
    welding_receivings = (await db.execute(welding_rec_q)).scalar() or 0

    # 納期遅延（delivery_date < today かつ 未完了）
    plating_overdue_q = select(func.count(PlatingOrder.id)).where(
        and_(
            PlatingOrder.delivery_date.isnot(None),
            PlatingOrder.delivery_date < today,
            PlatingOrder.status.in_(pending_statuses),
        )
    )
    welding_overdue_q = select(func.count(WeldingOrder.id)).where(
        and_(
            WeldingOrder.delivery_date.isnot(None),
            WeldingOrder.delivery_date < today,
            WeldingOrder.status.in_(pending_statuses),
        )
    )
    plating_overdue = (await db.execute(plating_overdue_q)).scalar() or 0
    welding_overdue = (await db.execute(welding_overdue_q)).scalar() or 0

    # 在庫警告は現状未実装（0）
    return {
        "success": True,
        "data": {
            "todayOrders": {
                "plating_orders": plating_today,
                "welding_orders": welding_today,
            },
            "pendingOrders": {
                "plating_pending": plating_pending,
                "welding_pending": welding_pending,
            },
            "todayReceivings": {
                "plating_receivings": plating_receivings,
                "welding_receivings": welding_receivings,
            },
            "stockAlerts": {
                "plating_alerts": 0,
                "welding_alerts": 0,
                "material_alerts": 0,
            },
            "overdueOrders": {
                "plating_overdue": plating_overdue,
                "welding_overdue": welding_overdue,
            },
        },
    }


@router.get("/upcoming-deliveries")
async def get_upcoming_deliveries(
    days: int = Query(7, ge=1, le=30, description="何日以内の納期を表示するか"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """直近の納期一覧（メッキ・溶接、未完了かつ delivery_date が today ～ today+days）"""
    today = date.today()
    end_date = today + timedelta(days=days)
    pending_statuses = ["pending", "ordered", "partial"]

    # メッキ注文
    plating_q = (
        select(PlatingOrder, OutsourcingSupplier.supplier_name)
        .outerjoin(
            OutsourcingSupplier,
            PlatingOrder.supplier_cd == OutsourcingSupplier.supplier_cd,
        )
        .where(
            and_(
                PlatingOrder.delivery_date.isnot(None),
                PlatingOrder.delivery_date >= today,
                PlatingOrder.delivery_date <= end_date,
                PlatingOrder.status.in_(pending_statuses),
            )
        )
        .order_by(PlatingOrder.delivery_date.asc(), PlatingOrder.id.asc())
    )
    plating_rows = (await db.execute(plating_q)).all()

    # 溶接注文
    welding_q = (
        select(WeldingOrder, OutsourcingSupplier.supplier_name)
        .outerjoin(
            OutsourcingSupplier,
            WeldingOrder.supplier_cd == OutsourcingSupplier.supplier_cd,
        )
        .where(
            and_(
                WeldingOrder.delivery_date.isnot(None),
                WeldingOrder.delivery_date >= today,
                WeldingOrder.delivery_date <= end_date,
                WeldingOrder.status.in_(pending_statuses),
            )
        )
        .order_by(WeldingOrder.delivery_date.asc(), WeldingOrder.id.asc())
    )
    welding_rows = (await db.execute(welding_q)).all()

    result = []
    for row in plating_rows:
        order, supplier_name = row[0], row[1]
        d = order.delivery_date
        days_remaining = (d - today).days if d else 0
        result.append({
            "type": "plating",
            "order_no": order.order_no,
            "product_cd": order.product_cd,
            "product_name": order.product_name,
            "supplier_cd": order.supplier_cd,
            "supplier_name": supplier_name or order.supplier_cd,
            "quantity": order.quantity or 0,
            "received_qty": order.received_qty or 0,
            "delivery_date": d.isoformat() if d else None,
            "days_remaining": days_remaining,
        })
    for row in welding_rows:
        order, supplier_name = row[0], row[1]
        d = order.delivery_date
        days_remaining = (d - today).days if d else 0
        result.append({
            "type": "welding",
            "order_no": order.order_no,
            "product_cd": order.product_cd,
            "product_name": order.product_name,
            "supplier_cd": order.supplier_cd,
            "supplier_name": supplier_name or order.supplier_cd,
            "quantity": order.quantity or 0,
            "received_qty": order.received_qty or 0,
            "delivery_date": d.isoformat() if d else None,
            "days_remaining": days_remaining,
        })

    result.sort(key=lambda x: (x["delivery_date"] or "", x["order_no"]))
    return {"success": True, "data": result}

"""
在庫取引履歴 (stock_transaction_logs) API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from typing import Optional, List, Any
from decimal import Decimal
from datetime import datetime

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.erp.stock_transaction_log_models import StockTransactionLog

router = APIRouter(prefix="/stock-transaction-logs", tags=["StockTransactionLogs"])


def _log_to_dict(row: StockTransactionLog) -> dict:
    return {
        "id": row.id,
        "stock_type": row.stock_type,
        "transaction_type": row.transaction_type,
        "target_cd": row.target_cd,
        "location_cd": row.location_cd,
        "lot_no": row.lot_no,
        "process_cd": row.process_cd,
        "machine_cd": row.machine_cd,
        "quantity": float(row.quantity) if row.quantity is not None else 0,
        "unit": row.unit,
        "order_no": row.order_no,
        "related_log_id": row.related_log_id,
        "operator_id": row.operator_id,
        "operator_name": row.operator_name,
        "transaction_time": row.transaction_time.isoformat() if row.transaction_time else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "source_file": getattr(row, "source_file", None),
        "remarks": row.remarks,
    }


@router.get("")
async def get_stock_transaction_logs(
    stock_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    target_cd: Optional[str] = Query(None, description="対象CD（製品等）で完全一致筛选"),
    location_cd: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    process_cd: Optional[str] = Query(None),
    source_file: Optional[str] = Query(None, description="来源（手入力、文件名等）"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫取引履歴一覧取得"""
    query = select(StockTransactionLog)
    if stock_type:
        query = query.where(StockTransactionLog.stock_type == stock_type)
    if target_cd and target_cd.strip():
        query = query.where(StockTransactionLog.target_cd == target_cd.strip())
    if keyword:
        q = f"%{keyword}%"
        query = query.where(
            (StockTransactionLog.target_cd.like(q)) | (StockTransactionLog.remarks.like(q))
        )
    if location_cd:
        query = query.where(StockTransactionLog.location_cd == location_cd)
    if transaction_type:
        query = query.where(StockTransactionLog.transaction_type == transaction_type)
    if process_cd:
        query = query.where(StockTransactionLog.process_cd == process_cd)
    if source_file and source_file.strip():
        query = query.where(StockTransactionLog.source_file == source_file.strip())
    if date_start:
        query = query.where(StockTransactionLog.transaction_time >= date_start)
    if date_end:
        query = query.where(StockTransactionLog.transaction_time <= f"{date_end} 23:59:59")

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 全件で集計（総数量・入庫系・出庫系）同一筛选条件
    agg_query = select(
        func.coalesce(func.sum(StockTransactionLog.quantity), 0).label("total_quantity"),
        func.coalesce(
            func.sum(
                case(
                    (StockTransactionLog.transaction_type.in_(["入庫", "実績"]), func.abs(StockTransactionLog.quantity)),
                    else_=0,
                )
            ),
            0,
        ).label("inbound_quantity"),
        func.coalesce(
            func.sum(
                case(
                    (StockTransactionLog.transaction_type.in_(["出庫", "不良", "廃棄"]), func.abs(StockTransactionLog.quantity)),
                    else_=0,
                )
            ),
            0,
        ).label("outbound_quantity"),
    ).select_from(StockTransactionLog)
    if stock_type:
        agg_query = agg_query.where(StockTransactionLog.stock_type == stock_type)
    if target_cd and target_cd.strip():
        agg_query = agg_query.where(StockTransactionLog.target_cd == target_cd.strip())
    if keyword:
        q = f"%{keyword}%"
        agg_query = agg_query.where(
            (StockTransactionLog.target_cd.like(q)) | (StockTransactionLog.remarks.like(q))
        )
    if location_cd:
        agg_query = agg_query.where(StockTransactionLog.location_cd == location_cd)
    if transaction_type:
        agg_query = agg_query.where(StockTransactionLog.transaction_type == transaction_type)
    if process_cd:
        agg_query = agg_query.where(StockTransactionLog.process_cd == process_cd)
    if source_file and source_file.strip():
        agg_query = agg_query.where(StockTransactionLog.source_file == source_file.strip())
    if date_start:
        agg_query = agg_query.where(StockTransactionLog.transaction_time >= date_start)
    if date_end:
        agg_query = agg_query.where(StockTransactionLog.transaction_time <= f"{date_end} 23:59:59")
    agg_result = await db.execute(agg_query)
    agg_row = agg_result.first()

    query = query.order_by(StockTransactionLog.transaction_time.desc())
    query = query.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(query)
    rows = result.scalars().all()

    return {
        "list": [_log_to_dict(r) for r in rows],
        "total": total,
        "totalQuantity": float(agg_row.total_quantity) if agg_row else 0,
        "inboundQuantity": float(agg_row.inbound_quantity) if agg_row else 0,
        "outboundQuantity": float(agg_row.outbound_quantity) if agg_row else 0,
    }


@router.post("")
async def create_stock_transaction_log(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫取引履歴1件登録（初期在庫一括登録など）"""
    transaction_type = (body.get("transaction_type") or "").strip()
    process_cd = (body.get("process_cd") or "").strip()
    quantity = body.get("quantity")
    if quantity is None:
        raise HTTPException(status_code=400, detail="quantity は必須です")
    quantity = Decimal(str(quantity))
    transaction_time = body.get("transaction_time")
    if not transaction_time:
        raise HTTPException(status_code=400, detail="transaction_time は必須です")
    target_cd = (body.get("target_cd") or "").strip()
    if not target_cd:
        raise HTTPException(status_code=400, detail="target_cd は必須です")

    # 初期在庫用: 在庫種別・保管場所・単位を工程で決定
    if transaction_type == "初期":
        if process_cd == "KT13":
            stock_type = "製品"
            location_cd = "製品倉庫"
            unit = "本"
        elif process_cd == "KT15":
            stock_type = "製品"
            location_cd = "外注倉庫"
            unit = "本"
        else:
            stock_type = "仕掛品"
            location_cd = "工程中間在庫"
            unit = "本"
    else:
        stock_type = (body.get("stock_type") or "").strip() or "仕掛品"
        location_cd = (body.get("location_cd") or "").strip() or "工程中間在庫"
        unit = (body.get("unit") or "").strip() or "本"

    # 来源: 未传则视为手入力；监听文件写入时由调用方传 source_file 为文件名
    source_file = (body.get("source_file") or "").strip() or "手入力"
    row = StockTransactionLog(
        stock_type=stock_type,
        transaction_type=transaction_type or "入庫",
        target_cd=target_cd,
        location_cd=location_cd,
        lot_no=body.get("lot_no"),
        process_cd=process_cd or None,
        machine_cd=body.get("machine_cd"),
        quantity=quantity,
        unit=unit,
        order_no=body.get("order_no"),
        related_log_id=body.get("related_log_id"),
        operator_id=getattr(current_user, "user_id", None) or getattr(current_user, "id", None),
        operator_name=getattr(current_user, "username", None) or getattr(current_user, "name", None),
        transaction_time=transaction_time,
        source_file=source_file,
        remarks=body.get("remarks"),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return _log_to_dict(row)


@router.post("/batch-actual")
async def batch_actual_stock_transaction_logs(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    実績一括登録。transactions を逐条 INSERT（stock_type=仕掛品, location_cd=工程中間在庫, transaction_type=実績）。
    production_summarys は更新しない。実績は「実績データ更新」で logs から反映。
    """
    transactions = body.get("transactions")
    if not isinstance(transactions, list) or len(transactions) == 0:
        raise HTTPException(status_code=400, detail="実績データがありません")

    success = 0
    failed = 0
    errors: List[dict] = []

    for trans in transactions:
        product_cd = (trans.get("product_cd") or "").strip()
        process_cd = (trans.get("process_cd") or "").strip()
        quantity = trans.get("quantity")
        transaction_time = trans.get("transaction_time")
        if not product_cd or not process_cd or quantity is None or not transaction_time:
            failed += 1
            errors.append({"product_cd": product_cd, "process_cd": process_cd, "error": "必須項目が不足しています"})
            continue
        try:
            qty = Decimal(str(quantity))
        except Exception:
            failed += 1
            errors.append({"product_cd": product_cd, "process_cd": process_cd, "error": "数量が不正です"})
            continue
        if isinstance(transaction_time, str):
            try:
                transaction_time = datetime.strptime(transaction_time.strip()[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                failed += 1
                errors.append({"product_cd": product_cd, "process_cd": process_cd, "error": "日時が不正です"})
                continue
        try:
            row = StockTransactionLog(
                stock_type="仕掛品",
                target_cd=product_cd,
                location_cd="工程中間在庫",
                process_cd=process_cd,
                transaction_type="実績",
                quantity=qty,
                unit="本",
                transaction_time=transaction_time,
                source_file="手入力",
            )
            db.add(row)
            success += 1
        except Exception as e:
            failed += 1
            errors.append({"product_cd": product_cd, "process_cd": process_cd, "error": str(e)})

    await db.commit()

    if failed > 0:
        return {
            "success": True,
            "message": f"{success}件成功、{failed}件失敗",
            "data": {"success": success, "failed": failed, "errors": errors},
        }
    return {
        "success": True,
        "message": f"{success}件の実績データを登録しました",
        "data": {"success": success, "failed": 0, "errors": []},
    }


@router.get("/{log_id}")
async def get_stock_transaction_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫取引履歴1件取得"""
    result = await db.execute(select(StockTransactionLog).where(StockTransactionLog.id == log_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="在庫取引履歴が見つかりません")
    return _log_to_dict(row)


@router.put("/{log_id}")
async def update_stock_transaction_log(
    log_id: int,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫取引履歴更新"""
    result = await db.execute(select(StockTransactionLog).where(StockTransactionLog.id == log_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="在庫取引履歴が見つかりません")

    allowed = {
        "stock_type", "transaction_type", "target_cd", "location_cd", "lot_no",
        "process_cd", "machine_cd", "quantity", "unit", "order_no", "related_log_id",
        "operator_id", "operator_name", "transaction_time", "source_file", "remarks",
    }
    for key, value in body.items():
        if key in allowed and hasattr(row, key):
            if key == "quantity" and value is not None:
                setattr(row, key, Decimal(str(value)))
            else:
                setattr(row, key, value)
    await db.flush()
    await db.refresh(row)
    return _log_to_dict(row)


@router.delete("/{log_id}")
async def delete_stock_transaction_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫取引履歴削除"""
    result = await db.execute(select(StockTransactionLog).where(StockTransactionLog.id == log_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="在庫取引履歴が見つかりません")
    await db.delete(row)
    return {"message": "削除しました"}


@router.post("/batch-delete")
async def batch_delete_stock_transaction_logs(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫取引履歴一括削除"""
    ids = body.get("ids") or []
    if not ids:
        raise HTTPException(status_code=400, detail="ids を指定してください")
    result = await db.execute(select(StockTransactionLog).where(StockTransactionLog.id.in_(ids)))
    rows = result.scalars().all()
    for row in rows:
        await db.delete(row)
    return {"message": f"{len(rows)}件削除しました"}

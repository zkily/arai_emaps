"""
在庫取引履歴 (stock_transaction_logs) API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, or_
from typing import Optional, List, Any
from decimal import Decimal
from datetime import datetime
from calendar import monthrange

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_inventory_operation
from app.modules.auth.models import User
from app.modules.erp.stock_transaction_log_models import StockTransactionLog
from app.modules.master.models import Process, Product

router = APIRouter(prefix="/stock-transaction-logs", tags=["StockTransactionLogs"])

SOURCE_PROD_DATA_MGMT = "生産データ管理"
SOURCE_HAND_INPUT = "手入力"
# 社内検査（検査管理指標の非SD行と同じ工程）
INSPECTION_PROCESS_CD = "KT09"


def _exclude_hand_input_clause():
    """手入力来源の実績は統計対象外"""
    return or_(
        StockTransactionLog.source_file.is_(None),
        StockTransactionLog.source_file != SOURCE_HAND_INPUT,
    )


def _inspection_exclude_sd_clause():
    """検査工程(KT09): 製品名に SD を含むデータを統計から除外"""
    return or_(
        StockTransactionLog.process_cd != INSPECTION_PROCESS_CD,
        Product.product_name.is_(None),
        func.coalesce(func.upper(Product.product_name), "").notlike("%SD%"),
    )


def _parse_month(month: str) -> tuple[int, int]:
    parts = (month or "").strip().split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="month は YYYY-MM 形式で指定してください")
    try:
        y, m = int(parts[0]), int(parts[1])
    except ValueError as e:
        raise HTTPException(status_code=400, detail="month の形式が不正です") from e
    if m < 1 or m > 12:
        raise HTTPException(status_code=400, detail="month の月が不正です")
    return y, m


def _month_bounds(month: str) -> tuple[str, str]:
    y, m = _parse_month(month)
    last_day = monthrange(y, m)[1]
    ym = f"{y:04d}-{m:02d}"
    return f"{ym}-01", f"{ym}-{last_day:02d} 23:59:59"


def _shift_month(month: str, delta: int) -> str:
    y, m = _parse_month(month)
    m += delta
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return f"{y:04d}-{m:02d}"


def _month_list_end_month(end_month: str, count: int) -> list[str]:
    n = max(1, min(count, 24))
    months = []
    cur = end_month
    for _ in range(n):
        months.append(cur)
        cur = _shift_month(cur, -1)
    months.reverse()
    return months


def _ratio(part: float, whole: float) -> float:
    if whole <= 0:
        return 0.0
    return round(part / whole, 6)


def _change_rate(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None if current == 0 else 1.0
    return round((current - previous) / previous, 6)


def _summary_row_to_dict(row: Any) -> dict:
    prod_count = int(row.prod_count or 0)
    auto_count = int(row.auto_count or 0)
    total_count = int(row.total_count or 0)
    prod_qty = float(row.prod_qty or 0)
    auto_qty = float(row.auto_qty or 0)
    total_qty = float(row.total_qty or 0)
    return {
        "prodDataMgmt": {"count": prod_count, "quantity": prod_qty},
        "auto": {"count": auto_count, "quantity": auto_qty},
        "total": {"count": total_count, "quantity": total_qty},
        "prodDataMgmtCountRatio": _ratio(prod_count, total_count),
        "prodDataMgmtQuantityRatio": _ratio(prod_qty, total_qty),
    }


def _build_actual_filters(
    date_start: str,
    date_end: str,
    process_cd: Optional[str],
) -> list:
    filters = [
        StockTransactionLog.transaction_type == "実績",
        StockTransactionLog.transaction_time >= date_start,
        StockTransactionLog.transaction_time <= date_end,
    ]
    if process_cd and process_cd.strip():
        filters.append(StockTransactionLog.process_cd == process_cd.strip())
    return filters


def _manual_stats_filters(
    date_start: str,
    date_end: str,
    process_cd: Optional[str],
) -> list:
    return [
        *_build_actual_filters(date_start, date_end, process_cd),
        _exclude_hand_input_clause(),
        _inspection_exclude_sd_clause(),
    ]


def _summary_select():
    abs_qty = func.abs(StockTransactionLog.quantity)
    return select(
        func.count().label("total_count"),
        func.coalesce(func.sum(abs_qty), 0).label("total_qty"),
        func.coalesce(
            func.sum(case((StockTransactionLog.source_file == SOURCE_PROD_DATA_MGMT, 1), else_=0)),
            0,
        ).label("prod_count"),
        func.coalesce(
            func.sum(
                case((StockTransactionLog.source_file == SOURCE_PROD_DATA_MGMT, abs_qty), else_=0)
            ),
            0,
        ).label("prod_qty"),
        func.coalesce(
            func.sum(
                case(
                    (StockTransactionLog.source_file != SOURCE_PROD_DATA_MGMT, 1),
                    else_=0,
                )
            ),
            0,
        ).label("auto_count"),
        func.coalesce(
            func.sum(
                case(
                    (StockTransactionLog.source_file != SOURCE_PROD_DATA_MGMT, abs_qty),
                    else_=0,
                )
            ),
            0,
        ).label("auto_qty"),
    )


async def _fetch_by_process(
    db: AsyncSession,
    ym: str,
    proc: Optional[str],
) -> list:
    start, end = _month_bounds(ym)
    abs_qty = func.abs(StockTransactionLog.quantity)
    by_process_q = (
        select(
            StockTransactionLog.process_cd,
            Process.process_name,
            func.coalesce(
                func.sum(case((StockTransactionLog.source_file == SOURCE_PROD_DATA_MGMT, 1), else_=0)),
                0,
            ).label("prod_count"),
            func.coalesce(
                func.sum(
                    case((StockTransactionLog.source_file == SOURCE_PROD_DATA_MGMT, abs_qty), else_=0)
                ),
                0,
            ).label("prod_qty"),
            func.coalesce(
                func.sum(
                    case(
                        (StockTransactionLog.source_file != SOURCE_PROD_DATA_MGMT, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("auto_count"),
            func.coalesce(
                func.sum(
                    case(
                        (StockTransactionLog.source_file != SOURCE_PROD_DATA_MGMT, abs_qty),
                        else_=0,
                    )
                ),
                0,
            ).label("auto_qty"),
            func.count().label("total_count"),
            func.coalesce(func.sum(abs_qty), 0).label("total_qty"),
        )
        .select_from(StockTransactionLog)
        .outerjoin(Process, StockTransactionLog.process_cd == Process.process_cd)
        .outerjoin(Product, StockTransactionLog.target_cd == Product.product_cd)
        .where(and_(*_manual_stats_filters(start, end, proc)))
        .group_by(StockTransactionLog.process_cd, Process.process_name)
    )
    by_process_res = await db.execute(by_process_q)
    by_process = []
    for row in by_process_res.all():
        pcd = (row.process_cd or "").strip() or "(未設定)"
        pname = (row.process_name or "").strip() or pcd
        prod_c = int(row.prod_count or 0)
        total_c = int(row.total_count or 0)
        by_process.append(
            {
                "processCd": pcd,
                "processName": pname,
                "prodDataMgmt": {"count": prod_c, "quantity": float(row.prod_qty or 0)},
                "auto": {"count": int(row.auto_count or 0), "quantity": float(row.auto_qty or 0)},
                "total": {"count": total_c, "quantity": float(row.total_qty or 0)},
                "prodDataMgmtCountRatio": _ratio(prod_c, total_c),
            }
        )
    by_process.sort(key=lambda x: x["prodDataMgmt"]["count"], reverse=True)
    return by_process


def _log_to_dict(
    row: StockTransactionLog,
    process_name: Optional[str] = None,
    product_name: Optional[str] = None,
) -> dict:
    return {
        "id": row.id,
        "stock_type": row.stock_type,
        "transaction_type": row.transaction_type,
        "target_cd": row.target_cd,
        "product_name": (product_name or "").strip() or "",
        "location_cd": row.location_cd,
        "lot_no": row.lot_no,
        "process_cd": row.process_cd,
        "process_name": (process_name or "").strip() or (row.process_cd or ""),
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
    """在庫取引履歴一覧取得（processes を JOIN して process_name を返す）"""
    base = select(StockTransactionLog).where(True)
    if stock_type:
        base = base.where(StockTransactionLog.stock_type == stock_type)
    if target_cd and target_cd.strip():
        base = base.where(StockTransactionLog.target_cd == target_cd.strip())
    if keyword:
        q = f"%{keyword}%"
        base = base.where(
            (StockTransactionLog.target_cd.like(q)) | (StockTransactionLog.remarks.like(q))
        )
    if location_cd:
        base = base.where(StockTransactionLog.location_cd == location_cd)
    if transaction_type:
        base = base.where(StockTransactionLog.transaction_type == transaction_type)
    if process_cd:
        base = base.where(StockTransactionLog.process_cd == process_cd)
    if source_file and source_file.strip():
        base = base.where(StockTransactionLog.source_file == source_file.strip())
    if date_start:
        base = base.where(StockTransactionLog.transaction_time >= date_start)
    if date_end:
        base = base.where(StockTransactionLog.transaction_time <= f"{date_end} 23:59:59")

    count_query = select(func.count()).select_from(base.subquery())
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

    query = (
        select(StockTransactionLog, Process.process_name, Product.product_name)
        .select_from(StockTransactionLog)
        .outerjoin(Process, StockTransactionLog.process_cd == Process.process_cd)
        .outerjoin(Product, StockTransactionLog.target_cd == Product.product_cd)
        .where(True)
    )
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
    query = query.order_by(StockTransactionLog.transaction_time.desc())
    query = query.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(query)
    rows = result.all()

    return {
        "list": [_log_to_dict(r, pname, pprod_name) for r, pname, pprod_name in rows],
        "total": total,
        "totalQuantity": float(agg_row.total_quantity) if agg_row else 0,
        "inboundQuantity": float(agg_row.inbound_quantity) if agg_row else 0,
        "outboundQuantity": float(agg_row.outbound_quantity) if agg_row else 0,
    }


@router.post("")
async def create_stock_transaction_log(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("create")),
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
    current_user: User = Depends(require_inventory_operation("edit")),
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


@router.get("/manual-entry-statistics")
async def get_manual_entry_statistics(
    month: Optional[str] = Query(None, description="対象月 YYYY-MM（未指定時は当月）"),
    compare_month: Optional[str] = Query(None, description="比較月 YYYY-MM（未指定時は前月）"),
    trend_months: int = Query(6, ge=1, le=24, description="推移グラフの月数"),
    process_cd: Optional[str] = Query(None, description="工程コード"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    実績修正統計（操作種別=実績、手入力除外）。
    実績修正 vs 実績集計（MES・ファイル同期等）を月次比較。
    検査工程(KT09)は製品名に SD を含む行を除外。
    """
    now = datetime.now()
    target_month = (month or "").strip() or now.strftime("%Y-%m")
    cmp_month = (compare_month or "").strip() or _shift_month(target_month, -1)
    _parse_month(target_month)
    _parse_month(cmp_month)

    proc = (process_cd or "").strip() or None

    async def _fetch_summary(ym: str) -> dict:
        start, end = _month_bounds(ym)
        q = _summary_select().select_from(StockTransactionLog).outerjoin(
            Product, StockTransactionLog.target_cd == Product.product_cd
        ).where(and_(*_manual_stats_filters(start, end, proc)))
        res = await db.execute(q)
        row = res.first()
        if not row:
            return _summary_row_to_dict(
                type("R", (), {k: 0 for k in [
                    "total_count", "total_qty", "prod_count", "prod_qty",
                    "auto_count", "auto_qty",
                ]})()
            )
        return _summary_row_to_dict(row)

    current_summary = await _fetch_summary(target_month)
    compare_summary = await _fetch_summary(cmp_month)

    # by process
    by_process = await _fetch_by_process(db, target_month, proc)
    by_process_compare = await _fetch_by_process(db, cmp_month, proc)

    # monthly trend
    trend_list = _month_list_end_month(target_month, trend_months)
    trend_start, _ = _month_bounds(trend_list[0])
    _, trend_end = _month_bounds(target_month)
    period_expr = func.date_format(StockTransactionLog.transaction_time, "%Y-%m").label("period")
    abs_qty = func.abs(StockTransactionLog.quantity)
    trend_q = (
        select(
            period_expr,
            func.coalesce(
                func.sum(case((StockTransactionLog.source_file == SOURCE_PROD_DATA_MGMT, 1), else_=0)),
                0,
            ).label("prod_count"),
            func.coalesce(
                func.sum(
                    case(
                        (StockTransactionLog.source_file != SOURCE_PROD_DATA_MGMT, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("auto_count"),
            func.count().label("total_count"),
            func.coalesce(
                func.sum(
                    case((StockTransactionLog.source_file == SOURCE_PROD_DATA_MGMT, abs_qty), else_=0)
                ),
                0,
            ).label("prod_qty"),
            func.coalesce(
                func.sum(
                    case(
                        (StockTransactionLog.source_file != SOURCE_PROD_DATA_MGMT, abs_qty),
                        else_=0,
                    )
                ),
                0,
            ).label("auto_qty"),
            func.coalesce(func.sum(abs_qty), 0).label("total_qty"),
        )
        .select_from(StockTransactionLog)
        .outerjoin(Product, StockTransactionLog.target_cd == Product.product_cd)
        .where(
            and_(
                *_manual_stats_filters(trend_start, trend_end, proc),
            )
        )
        .group_by(period_expr)
        .order_by(period_expr)
    )
    trend_res = await db.execute(trend_q)
    trend_map = {r.period: r for r in trend_res.all()}
    by_month_trend = []
    for ym in trend_list:
        r = trend_map.get(ym)
        if r:
            prod_c = int(r.prod_count or 0)
            total_c = int(r.total_count or 0)
            prod_q = float(r.prod_qty or 0)
            total_q = float(r.total_qty or 0)
            by_month_trend.append(
                {
                    "month": ym,
                    "prodDataMgmtCount": prod_c,
                    "autoCount": int(r.auto_count or 0),
                    "totalCount": total_c,
                    "prodDataMgmtCountRatio": _ratio(prod_c, total_c),
                    "prodDataMgmtQuantity": prod_q,
                    "autoQuantity": float(r.auto_qty or 0),
                    "totalQuantity": total_q,
                    "prodDataMgmtQuantityRatio": _ratio(prod_q, total_q),
                }
            )
        else:
            by_month_trend.append(
                {
                    "month": ym,
                    "prodDataMgmtCount": 0,
                    "autoCount": 0,
                    "totalCount": 0,
                    "prodDataMgmtCountRatio": 0.0,
                    "prodDataMgmtQuantity": 0.0,
                    "autoQuantity": 0.0,
                    "totalQuantity": 0.0,
                    "prodDataMgmtQuantityRatio": 0.0,
                }
            )

    cur_p = current_summary["prodDataMgmt"]
    cmp_p = compare_summary["prodDataMgmt"]
    cur_a = current_summary["auto"]
    cmp_a = compare_summary["auto"]

    return {
        "month": target_month,
        "compareMonth": cmp_month,
        "trendMonths": trend_months,
        "transactionType": "実績",
        "current": current_summary,
        "compare": compare_summary,
        "monthOverMonth": {
            "prodDataMgmtCountChange": cur_p["count"] - cmp_p["count"],
            "prodDataMgmtCountChangeRate": _change_rate(cur_p["count"], cmp_p["count"]),
            "prodDataMgmtQuantityChange": round(cur_p["quantity"] - cmp_p["quantity"], 4),
            "prodDataMgmtQuantityChangeRate": _change_rate(cur_p["quantity"], cmp_p["quantity"]),
            "prodDataMgmtCountRatioChange": round(
                current_summary["prodDataMgmtCountRatio"] - compare_summary["prodDataMgmtCountRatio"],
                6,
            ),
            "prodDataMgmtQuantityRatioChange": round(
                current_summary["prodDataMgmtQuantityRatio"]
                - compare_summary["prodDataMgmtQuantityRatio"],
                6,
            ),
            "autoCountChange": cur_a["count"] - cmp_a["count"],
            "autoCountChangeRate": _change_rate(cur_a["count"], cmp_a["count"]),
            "autoQuantityChange": round(cur_a["quantity"] - cmp_a["quantity"], 4),
            "autoQuantityChangeRate": _change_rate(cur_a["quantity"], cmp_a["quantity"]),
        },
        "byProcess": by_process,
        "byProcessCompare": by_process_compare,
        "byMonthTrend": by_month_trend,
    }


@router.get("/{log_id}")
async def get_stock_transaction_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    """在庫取引履歴1件取得"""
    q = (
        select(StockTransactionLog, Process.process_name, Product.product_name)
        .select_from(StockTransactionLog)
        .outerjoin(Process, StockTransactionLog.process_cd == Process.process_cd)
        .outerjoin(Product, StockTransactionLog.target_cd == Product.product_cd)
        .where(StockTransactionLog.id == log_id)
    )
    result = await db.execute(q)
    row_tuple = result.one_or_none()
    if not row_tuple:
        raise HTTPException(status_code=404, detail="在庫取引履歴が見つかりません")
    row, pname, prod_name = row_tuple
    return _log_to_dict(row, pname, prod_name)


@router.put("/{log_id}")
async def update_stock_transaction_log(
    log_id: int,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
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
    current_user: User = Depends(require_inventory_operation("delete")),
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
    current_user: User = Depends(require_inventory_operation("delete")),
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

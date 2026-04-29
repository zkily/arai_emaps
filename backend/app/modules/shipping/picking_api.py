"""
ピッキング管理 API
- GET  /new-progress: 本日のピッキング進捗（shipping_items + picking_log_matched）
- GET  /history: ピッキング履歴（shipping_items）
- GET  /performance-by-destination: 担当者別パフォーマンス（shipping_items）
"""
import json
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam
from typing import Optional, List, Any
from datetime import date, timedelta

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.shipping.shipping_items_api import _shipping_item_to_picking_display_dict

logger = logging.getLogger(__name__)

router = APIRouter()

# shipping_log 突合せ後に picking_api / items API から再利用
REFRESH_SHIPPING_ITEMS_PICKING_LOG_MATCHED_SQL = text("""
UPDATE shipping_items si
LEFT JOIN (
    SELECT picking_no
    FROM shipping_log
    WHERE picking_no IS NOT NULL AND picking_no != ''
    GROUP BY picking_no
) sl ON sl.picking_no = si.shipping_no_p
SET si.picking_log_matched = IF(sl.picking_no IS NULL, 0, 1)
WHERE si.shipping_no_p IS NOT NULL AND si.shipping_no_p != ''
""")


def _parse_group_destinations(raw: Any) -> List[str]:
    """destination_groups.destinations の JSON から destination_cd のリストを取得"""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if isinstance(item, dict) and item.get("value"):
            out.append(str(item["value"]).strip())
        elif isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


# ---------- helpers ----------
def _safe_date(val) -> str:
    """日付を文字列に変換"""
    if val is None:
        return ""
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


# ================================================================
# 1. GET /new-progress  ─ ピッキング進捗（本日 or 指定期間）
# ================================================================
@router.get("/new-progress")
async def get_new_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
    start_date: Optional[str] = Query(None, description="期間開始日 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="期間終了日 YYYY-MM-DD"),
) -> dict:
    """shipping_items の picking_log_matched を完了判定として進捗を返す。"""

    use_range = start_date and end_date and start_date <= end_date
    base_where = "si.status != 'キャンセル' AND si.shipping_no_p IS NOT NULL AND si.shipping_no_p != ''"

    if use_range:
        pallet_result = await db.execute(
            text(f"""
            SELECT si.*
            FROM shipping_items si
            WHERE si.shipping_date BETWEEN :start_date AND :end_date
              AND {base_where}
            ORDER BY si.shipping_date ASC, si.picking_log_matched ASC, si.shipping_no_p ASC
        """),
            {"start_date": start_date, "end_date": end_date},
        )
        pallet_rows = pallet_result.mappings().all()
        total_tasks = len(pallet_rows)
        pending_today = sum(int(r.get("picking_log_matched") or 0) == 0 for r in pallet_rows)
        completed_today = sum(int(r.get("picking_log_matched") or 0) == 1 for r in pallet_rows)
        today_completion_rate = round(
            (completed_today / total_tasks * 100) if total_tasks > 0 else 0, 1
        )
    else:
        pt_result = await db.execute(text(f"""
            SELECT
                COUNT(*) AS total_tasks,
                SUM(CASE WHEN si.picking_log_matched = 0 THEN 1 ELSE 0 END) AS pending_count,
                SUM(CASE WHEN si.picking_log_matched = 1 THEN 1 ELSE 0 END) AS completed_count
            FROM shipping_items si
            WHERE si.shipping_date = CURDATE() AND {base_where}
        """))
        pt_row = pt_result.mappings().first()
        total_tasks = int(pt_row["total_tasks"] or 0) if pt_row else 0
        pending_today = int(pt_row["pending_count"] or 0) if pt_row else 0
        completed_today = int(pt_row["completed_count"] or 0) if pt_row else 0
        today_completion_rate = round(
            (completed_today / total_tasks * 100) if total_tasks > 0 else 0, 1
        )

        pallet_result = await db.execute(text(f"""
            SELECT si.*
            FROM shipping_items si
            WHERE si.shipping_date = CURDATE() AND {base_where}
            ORDER BY si.picking_log_matched ASC, si.shipping_no_p ASC
        """))
        pallet_rows = pallet_result.mappings().all()

    # --- 進捗推移トレンド用: 過去7日～未来3日、按出荷日分组、排除加工・アーチ・料金 ---
    trend_result = await db.execute(
        text(f"""
        SELECT
            si.shipping_date AS shipping_date,
            COUNT(*) AS total_count,
            SUM(CASE WHEN si.picking_log_matched = 0 THEN 1 ELSE 0 END) AS pending_count,
            SUM(CASE WHEN si.picking_log_matched = 1 THEN 1 ELSE 0 END) AS completed_count,
            ROUND(
                SUM(CASE WHEN si.picking_log_matched = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0),
                2
            ) AS completion_rate
        FROM shipping_items si
        WHERE si.shipping_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)
          AND {base_where}
          AND COALESCE(si.product_name, '') NOT LIKE '%加工%'
          AND COALESCE(si.product_name, '') NOT LIKE '%アーチ%'
          AND COALESCE(si.product_name, '') NOT LIKE '%料金%'
        GROUP BY si.shipping_date
        ORDER BY si.shipping_date
    """)
    )
    trend_rows = trend_result.mappings().all()
    progress_stats_list = [
        {
            "shipping_date": _safe_date(r.get("shipping_date")),
            "total_count": int(r.get("total_count") or 0),
            "pending_count": int(r.get("pending_count") or 0),
            "completed_count": int(r.get("completed_count") or 0),
            "completion_rate": float(r.get("completion_rate") or 0),
        }
        for r in trend_rows
    ]

    return {
        "todayOverview": {
            "total_today": total_tasks,
            "pending_today": pending_today,
            "completed_today": completed_today,
            "today_completion_rate": today_completion_rate,
        },
        "palletList": [_shipping_item_to_picking_display_dict(dict(r)) for r in pallet_rows],
        "progressStats": progress_stats_list,
    }


# ================================================================
# 2. GET /history  ─ ピッキング履歴
# ================================================================
@router.get("/history")
async def get_picking_history(
    start_date: Optional[str] = Query(None, description="開始日（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="終了日（YYYY-MM-DD）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """ピッキング履歴を期間指定で返す（shipping_items + picking_log_matched）。デフォルトは過去30日"""
    params: dict = {}
    if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date
        date_condition = "si.shipping_date BETWEEN :start_date AND :end_date"
    elif start_date:
        params["start_date"] = start_date
        date_condition = "si.shipping_date >= :start_date"
    elif end_date:
        params["end_date"] = end_date
        date_condition = "si.shipping_date <= :end_date"
    else:
        # デフォルト: 過去30日
        date_condition = "si.shipping_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"

    # 統計
    stats_q = text(f"""
        SELECT
            COUNT(*)                                              AS total,
            SUM(CASE WHEN si.picking_log_matched = 1 THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN si.picking_log_matched = 0 THEN 1 ELSE 0 END) AS pending,
            SUM(si.confirmed_boxes)                               AS total_boxes,
            SUM(CASE WHEN si.picking_log_matched = 1
                THEN COALESCE(si.confirmed_units, si.confirmed_boxes) ELSE 0 END) AS total_picked
        FROM shipping_items si
        WHERE {date_condition} AND si.status != 'キャンセル'
    """)
    stats_result = await db.execute(stats_q, params)
    stats_row = stats_result.mappings().first()

    total = int(stats_row["total"] or 0) if stats_row else 0
    completed = int(stats_row["completed"] or 0) if stats_row else 0
    pending = int(stats_row["pending"] or 0) if stats_row else 0
    total_boxes = int(stats_row["total_boxes"] or 0) if stats_row else 0
    total_picked = int(stats_row["total_picked"] or 0) if stats_row else 0

    # 一覧
    data_q = text(f"""
        SELECT si.*
        FROM shipping_items si
        WHERE {date_condition} AND si.status != 'キャンセル'
        ORDER BY si.shipping_date DESC, si.shipping_no_p ASC
    """)
    data_result = await db.execute(data_q, params)
    rows = data_result.mappings().all()

    return {
        "statistics": {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
            "total_boxes": total_boxes,
            "total_picked": total_picked,
        },
        "items": [_shipping_item_to_picking_display_dict(dict(r)) for r in rows],
    }


# ================================================================
# 3. GET /performance-by-destination  ─ 担当者別・納入先別パフォーマンス
# 担当者＝納入先グループ（destination_groups の group_name）。該当グループの destinations + 日期で shipping_items を集計
# ================================================================
@router.get("/performance-by-destination")
async def get_performance_by_destination(
    start_date: Optional[str] = Query(None, description="開始日"),
    end_date: Optional[str] = Query(None, description="終了日"),
    group_names: Optional[str] = Query(
        None,
        description="担当者＝グループ名（destination_groups.group_name）カンマ区切り。未指定時は全グループ",
    ),
    page_key: Optional[str] = Query(
        "picking_history",
        description="destination_groups の page_key",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """担当者＝納入先グループ（destination_groups の1行＝1つの group_name）。
    各担当者＝1グループ＝1組の納入先(destinations)。該当組の納入先＋日期範囲で shipping_items を集計。
    件数は出荷単位 COUNT(DISTINCT shipping_no_p)、完了は picking_log_matched = 1。品名 加工・アーチ・料金 除外。
    """
    params: dict = {}
    if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date
        date_condition = "si.shipping_date BETWEEN :start_date AND :end_date"
    elif start_date:
        params["start_date"] = start_date
        date_condition = "si.shipping_date >= :start_date"
    elif end_date:
        params["end_date"] = end_date
        date_condition = "si.shipping_date <= :end_date"
    else:
        date_condition = "si.shipping_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"

    # destination_groups から対象グループ取得（group_names 指定時はそのまま、未指定時は全件）
    group_q = text(
        "SELECT id, group_name, destinations FROM destination_groups WHERE page_key = :page_key ORDER BY id"
    )
    group_result = await db.execute(group_q, {"page_key": page_key or "picking_history"})
    group_rows = group_result.mappings().all()
    filter_names: Optional[List[str]] = None
    if group_names and group_names.strip():
        filter_names = [n.strip() for n in group_names.split(",") if n.strip()]
    groups_list = []
    for r in group_rows:
        gname = (r["group_name"] or "").strip()
        if not gname:
            continue
        if filter_names is not None and gname not in filter_names:
            continue
        dest_cds = _parse_group_destinations(r["destinations"])
        groups_list.append({"group_name": gname, "destination_cds": dest_cds})

    product_exclude = (
        " AND (si.product_name NOT LIKE '%加工%' AND si.product_name NOT LIKE '%アーチ%' AND si.product_name NOT LIKE '%料金%')"
    )
    completed_condition = "si.picking_log_matched = 1"
    out: List[dict] = []
    for grp in groups_list:
        gname = grp["group_name"]
        dest_cds = grp["destination_cds"]
        if not dest_cds:
            out.append({
                "picker_id": gname,
                "picker_name": gname,
                "destination_count": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "completion_rate": 0.0,
                "destinations": [],
            })
            continue
        q = text(f"""
            SELECT
                si.destination_cd,
                si.destination_name,
                COUNT(DISTINCT si.shipping_no_p) AS total_tasks,
                COUNT(DISTINCT CASE WHEN ({completed_condition}) THEN si.shipping_no_p END) AS completed_tasks
            FROM shipping_items si
            WHERE {date_condition}
              AND si.status != 'キャンセル'
            {product_exclude}
            AND si.destination_cd IN :dest_cds
            GROUP BY si.destination_cd, si.destination_name
            ORDER BY total_tasks DESC
        """).bindparams(bindparam("dest_cds", expanding=True))
        exec_params = {**params, "dest_cds": dest_cds}
        result = await db.execute(q, exec_params)
        rows = result.mappings().all()
        total_tasks = 0
        completed_tasks = 0
        destinations = []
        for r in rows:
            t = int(r["total_tasks"] or 0)
            c = int(r["completed_tasks"] or 0)
            rate = round((c / t * 100) if t > 0 else 0, 1)
            total_tasks += t
            completed_tasks += c
            destinations.append({
                "destination_cd": r["destination_cd"] or "",
                "destination_name": r["destination_name"] or "",
                "total_tasks": t,
                "completed_tasks": c,
                "completion_rate": rate,
            })
        completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
        out.append({
            "picker_id": gname,
            "picker_name": gname,
            "destination_count": len(destinations),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "destinations": destinations,
        })
    out.sort(key=lambda x: (-x["completion_rate"], -x["total_tasks"]))
    return {"success": True, "data": out}


# ================================================================
# 7. GET /shipping-logs  ─ 出荷ピッキングログ一覧
# ================================================================
@router.get("/shipping-logs")
async def get_shipping_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """shipping_log テーブルからログを取得"""
    conditions = []
    params: dict = {}
    if search:
        conditions.append(
            "(picking_no LIKE :search OR product_name LIKE :search OR product_code LIKE :search OR person_in_charge LIKE :search)"
        )
        params["search"] = f"%{search}%"
    where_sql = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * pageSize
    params["limit"] = pageSize
    params["offset"] = offset

    count_q = text(f"SELECT COUNT(*) AS cnt FROM shipping_log WHERE {where_sql}")
    count_result = await db.execute(count_q, params)
    total = int(count_result.scalar() or 0)

    data_q = text(f"""
        SELECT * FROM shipping_log
        WHERE {where_sql}
        ORDER BY id DESC
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(data_q, params)
    rows = result.mappings().all()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "pageSize": pageSize,
    }


# ================================================================
# 8. POST /cleanup-logs  ─ 古いログを削除
# ================================================================
@router.post("/cleanup-logs")
async def cleanup_shipping_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """30日以前の shipping_log を削除し、shipping_items.picking_log_matched を再計算"""
    result = await db.execute(text(
        "DELETE FROM shipping_log WHERE date < DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
    ))
    deleted = result.rowcount
    await db.execute(REFRESH_SHIPPING_ITEMS_PICKING_LOG_MATCHED_SQL)
    await db.commit()
    return {"success": True, "message": f"{deleted} 件の古いログを削除しました", "deleted": deleted}


# ================================================================
# 9. GET /duplicate-stats  ─ 重複データ統計
# ================================================================
@router.get("/duplicate-stats")
async def get_duplicate_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """shipping_log の重複データを集計"""
    q = text("""
        SELECT picking_no, product_code, COUNT(*) AS cnt
        FROM shipping_log
        GROUP BY picking_no, product_code
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 100
    """)
    result = await db.execute(q)
    rows = result.mappings().all()
    details = [{"picking_no": r["picking_no"], "product_code": r["product_code"], "count": int(r["cnt"])} for r in rows]
    unique_nos = len(set(d["picking_no"] for d in details))
    return {
        "total_duplicates": sum(d["count"] - 1 for d in details),
        "unique_picking_nos": unique_nos,
        "details": details,
    }


# ================================================================
# 10. POST /deduplicate  ─ 重複データの削除
# ================================================================
@router.post("/deduplicate")
async def perform_deduplicate(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """shipping_log の重複を削除（同じ picking_no, product_code, date で最新IDのみ残す）"""
    result = await db.execute(text("""
        DELETE sl FROM shipping_log sl
        INNER JOIN (
            SELECT picking_no, product_code, date, MAX(id) AS max_id
            FROM shipping_log
            GROUP BY picking_no, product_code, date
            HAVING COUNT(*) > 1
        ) dup ON sl.picking_no = dup.picking_no
                AND sl.product_code = dup.product_code
                AND sl.date = dup.date
                AND sl.id < dup.max_id
    """))
    deleted = result.rowcount
    await db.execute(REFRESH_SHIPPING_ITEMS_PICKING_LOG_MATCHED_SQL)
    await db.commit()
    return {"success": True, "message": f"{deleted} 件の重複を削除しました", "deleted": deleted}


# ================================================================
# 11. GET /sync-status  ─ 同期状態
# ================================================================
@router.get("/sync-status")
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """shipping_items と shipping_log の突合せ状態（picking_log_matched）を返す。"""

    try:
        si_result = await db.execute(text("""
            SELECT
                COUNT(*) AS cnt,
                SUM(CASE WHEN picking_log_matched = 1 THEN 1 ELSE 0 END) AS matched,
                MAX(updated_at) AS last_upd
            FROM shipping_items
            WHERE shipping_date >= CURDATE()
              AND status != 'キャンセル'
              AND shipping_no_p IS NOT NULL
              AND shipping_no_p != ''
        """))
        si_row = si_result.mappings().first()
        total_active_items = int(si_row["cnt"] or 0) if si_row else 0
        matched_items = int(si_row["matched"] or 0) if si_row else 0
        last_sync = str(si_row["last_upd"]) if si_row and si_row["last_upd"] else None
    except Exception:
        total_active_items = 0
        matched_items = 0
        last_sync = None

    try:
        sl_result = await db.execute(text("SELECT COUNT(*) AS cnt FROM shipping_log"))
        total_sl = int(sl_result.scalar() or 0)
    except Exception:
        total_sl = 0

    sync_rate = round((matched_items / total_active_items * 100) if total_active_items > 0 else 0, 1)
    completion_rate = sync_rate

    return {
        "totalPickingTasks": total_active_items,
        "completedPickingTasks": matched_items,
        "completionRate": completion_rate,
        "totalShippingLogs": total_sl,
        "totalActiveShippingItems": total_active_items,
        "lastSyncTime": last_sync,
        "tableExists": True,
        "availableForSync": total_active_items,
        "alreadySynced": matched_items,
        "syncRate": sync_rate,
    }


# ================================================================
# 12. GET /sync-debug  ─ 同期デバッグ情報
# ================================================================
@router.get("/sync-debug")
async def get_sync_debug_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """デバッグ用に各テーブルの件数と最新レコードを返す"""
    info: dict = {}
    for table in ["shipping_items", "shipping_log", "picking_list"]:
        try:
            r = await db.execute(text(f"SELECT COUNT(*) AS cnt FROM {table}"))
            cnt = int(r.scalar() or 0)
            r2 = await db.execute(text(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 3"))
            latest = [dict(row) for row in r2.mappings().all()]
            info[table] = {"count": cnt, "latest": latest}
        except Exception as e:
            info[table] = {"count": 0, "latest": [], "error": str(e)}
    return info

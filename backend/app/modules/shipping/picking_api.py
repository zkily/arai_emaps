"""
ピッキング管理 API
- GET  /new-progress: 本日のピッキング進捗
- POST /db/init: picking_tasks テーブル作成
- GET  /tasks/for-display: ピッキングタスク一覧
- POST /sync-data: shipping_items → picking_tasks 同期
- GET  /history: ピッキング履歴
- GET  /performance-by-destination: 担当者別・納入先別パフォーマンス（担当者＝納入先グループ）
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

logger = logging.getLogger(__name__)

router = APIRouter()


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


def _safe_datetime(val) -> str:
    """日時を文字列に変換"""
    if val is None:
        return ""
    return str(val)


def _task_row_to_dict(r) -> dict:
    """picking_tasks の行を辞書に変換。作業者表示用に users.full_name を picker_full_name で返す"""
    return {
        "id": r.get("id"),
        "shipping_no_p": r.get("shipping_no_p") or "",
        "shipping_no": r.get("shipping_no") or "",
        "shipping_date": _safe_date(r.get("shipping_date")),
        "product_cd": r.get("product_cd") or "",
        "product_name": r.get("product_name") or "",
        "confirmed_boxes": int(r.get("confirmed_boxes") or 0),
        "destination_cd": r.get("destination_cd") or "",
        "destination_name": r.get("destination_name") or "",
        "picked_quantity": int(r.get("picked_quantity") or 0),
        "picked_no": r.get("picked_no") or "",
        "location_cd": r.get("location_cd") or "",
        "picker_id": r.get("picker_id") or "",
        "picker_name": r.get("picker_name") or "",
        "picker_full_name": r.get("picker_full_name") or "",  # users.full_name（picker_id=username で JOIN）
        "status": r.get("status") or "pending",
        "start_time": _safe_datetime(r.get("start_time")),
        "complete_time": _safe_datetime(r.get("complete_time")),
        "created_at": _safe_datetime(r.get("created_at")),
        "updated_at": _safe_datetime(r.get("updated_at")),
    }


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
    """ピッキングタスクから進捗情報を返す。start_date/end_date を指定するとその期間の palletList を返す。"""

    use_range = start_date and end_date and start_date <= end_date

    if use_range:
        # --- 指定期間の pallet list（picking_tasks + users.full_name）---
        pallet_result = await db.execute(
            text("""
            SELECT pt.*, u.full_name AS picker_full_name
            FROM picking_tasks pt
            LEFT JOIN users u ON u.username = pt.picker_id
            WHERE pt.shipping_date BETWEEN :start_date AND :end_date
            ORDER BY pt.shipping_date ASC, pt.status ASC, pt.shipping_no_p ASC
        """),
            {"start_date": start_date, "end_date": end_date},
        )
        pallet_rows = pallet_result.mappings().all()
        # 期間内の集計（todayOverview / progressStats はこの期間のサマリ）
        total_tasks = len(pallet_rows)
        pending_today = sum(
            1 for r in pallet_rows if (r.get("status") or "") in ("pending", "picking")
        )
        completed_today = sum(1 for r in pallet_rows if (r.get("status") or "") == "completed")
        today_completion_rate = round(
            (completed_today / total_tasks * 100) if total_tasks > 0 else 0, 1
        )
        total_today = total_tasks
        completed_today_si = completed_today
    else:
        # --- 本日のみ（従来どおり）---
        si_result = await db.execute(text("""
            SELECT
                COUNT(DISTINCT shipping_no_p)                       AS total_today,
                SUM(CASE WHEN status = '完了' THEN 1 ELSE 0 END)  AS completed_today
            FROM shipping_items
            WHERE shipping_date = CURDATE()
              AND status != 'キャンセル'
              AND shipping_no_p IS NOT NULL
              AND shipping_no_p != ''
        """))
        si_row = si_result.mappings().first()
        total_today = int(si_row["total_today"] or 0) if si_row else 0
        completed_today_si = int(si_row["completed_today"] or 0) if si_row else 0

        pt_result = await db.execute(text("""
            SELECT
                COUNT(*) AS total_tasks,
                SUM(CASE WHEN status IN ('pending', 'picking') THEN 1 ELSE 0 END) AS pending_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count
            FROM picking_tasks
            WHERE shipping_date = CURDATE()
        """))
        pt_row = pt_result.mappings().first()
        total_tasks = int(pt_row["total_tasks"] or 0) if pt_row else 0
        pending_today = int(pt_row["pending_count"] or 0) if pt_row else 0
        completed_today = int(pt_row["completed_count"] or 0) if pt_row else 0
        today_completion_rate = round(
            (completed_today / total_tasks * 100) if total_tasks > 0 else 0, 1
        )

        pallet_result = await db.execute(text("""
            SELECT pt.*, u.full_name AS picker_full_name
            FROM picking_tasks pt
            LEFT JOIN users u ON u.username = pt.picker_id
            WHERE pt.shipping_date = CURDATE()
            ORDER BY pt.status ASC, pt.shipping_no_p ASC
        """))
        pallet_rows = pallet_result.mappings().all()

    # --- 進捗推移トレンド用: 過去7日～未来3日、按出荷日分组、排除加工・アーチ・料金 ---
    trend_result = await db.execute(
        text("""
        SELECT
            pt.shipping_date AS shipping_date,
            COUNT(*) AS total_count,
            SUM(CASE WHEN pt.status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
            SUM(CASE WHEN pt.status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
            ROUND(
                SUM(CASE WHEN pt.status = 'completed' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0),
                2
            ) AS completion_rate
        FROM picking_tasks pt
        WHERE pt.shipping_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)
          AND COALESCE(pt.product_name, '') NOT LIKE '%加工%'
          AND COALESCE(pt.product_name, '') NOT LIKE '%アーチ%'
          AND COALESCE(pt.product_name, '') NOT LIKE '%料金%'
        GROUP BY pt.shipping_date
        ORDER BY pt.shipping_date
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
            "total_today": total_tasks if use_range else total_today,
            "pending_today": pending_today,
            "completed_today": completed_today,
            "today_completion_rate": today_completion_rate,
        },
        "palletList": [_task_row_to_dict(r) for r in pallet_rows],
        "progressStats": progress_stats_list,
    }


# ================================================================
# 2. POST /db/init  ─ picking_tasks テーブル作成
# ================================================================
@router.post("/db/init")
async def init_picking_tasks_table(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """picking_tasks テーブルが存在しなければ作成する"""
    create_sql = text("""
        CREATE TABLE IF NOT EXISTS picking_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            shipping_no_p VARCHAR(50) NOT NULL,
            shipping_no VARCHAR(50) DEFAULT '',
            shipping_date DATE NULL,
            product_cd VARCHAR(50) DEFAULT '',
            product_name VARCHAR(200) DEFAULT '',
            confirmed_boxes INT DEFAULT 0,
            destination_cd VARCHAR(50) DEFAULT '',
            destination_name VARCHAR(200) DEFAULT '',
            picked_quantity INT DEFAULT 0,
            picked_no VARCHAR(100) DEFAULT '',
            location_cd VARCHAR(50) DEFAULT '',
            picker_id VARCHAR(50) DEFAULT '',
            picker_name VARCHAR(100) DEFAULT '',
            status VARCHAR(20) DEFAULT 'pending',
            start_time DATETIME NULL,
            complete_time DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_shipping_no_p (shipping_no_p),
            KEY idx_shipping_date (shipping_date),
            KEY idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    await db.execute(create_sql)
    await db.commit()
    logger.info("picking_tasks テーブルを初期化しました")
    return {"success": True, "message": "picking_tasks テーブルを作成（または既存を確認）しました"}


# ================================================================
# 3. GET /tasks/for-display  ─ ピッキングタスク一覧
# ================================================================
@router.get("/tasks/for-display")
async def get_tasks_for_display(
    date: Optional[str] = Query(None, description="対象日（YYYY-MM-DD）。省略時は本日"),
    start_date: Optional[str] = Query(None, description="開始日（範囲指定時）"),
    end_date: Optional[str] = Query(None, description="終了日（範囲指定時）"),
    status: Optional[str] = Query(None, description="ステータスでフィルタ"),
    product_cd: Optional[str] = Query(None, description="品番でフィルタ"),
    destination_cd: Optional[str] = Query(None, description="納入先コードでフィルタ"),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(50, ge=1, le=500, description="1ページあたりの件数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """ピッキングタスクを一覧で返す（shipping_items と結合して納入先情報を補完）"""
    conditions = []
    params: dict = {}

    # 日付: start_date/end_date があれば範囲、date があれば単日、なければ本日
    if start_date and end_date:
        conditions.append("pt.shipping_date BETWEEN :start_date AND :end_date")
        params["start_date"] = start_date
        params["end_date"] = end_date
    elif date:
        conditions.append("pt.shipping_date = :target_date")
        params["target_date"] = date
    else:
        conditions.append("pt.shipping_date = CURDATE()")

    if status:
        conditions.append("pt.status = :status")
        params["status"] = status
    if product_cd:
        conditions.append("pt.product_cd LIKE :product_cd")
        params["product_cd"] = f"%{product_cd}%"
    if destination_cd:
        conditions.append("pt.destination_cd = :destination_cd")
        params["destination_cd"] = destination_cd

    where_sql = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    # カウント
    count_q = text(f"""
        SELECT COUNT(*) AS cnt
        FROM picking_tasks pt
        WHERE {where_sql}
    """)
    count_result = await db.execute(count_q, params)
    total = int(count_result.scalar() or 0)

    # データ取得（shipping_items で destination 補完、users で作業者 full_name 取得）
    data_q = text(f"""
        SELECT
            pt.*,
            COALESCE(si.destination_name, pt.destination_name) AS destination_name,
            COALESCE(si.destination_cd, pt.destination_cd)     AS destination_cd,
            u.full_name AS picker_full_name
        FROM picking_tasks pt
        LEFT JOIN shipping_items si
            ON si.shipping_no_p = pt.shipping_no_p
        LEFT JOIN users u
            ON u.username = pt.picker_id
        WHERE {where_sql}
        ORDER BY pt.status ASC, pt.shipping_no_p ASC
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(data_q, params)
    rows = result.mappings().all()

    return {
        "items": [_task_row_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 1,
    }


# ================================================================
# 4. POST /sync-data  ─ shipping_items → picking_tasks 同期
# ================================================================
@router.post("/sync-data")
async def sync_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """shipping_items（出荷日が本日以降）を picking_tasks へ同期する"""
    sync_sql = text("""
        INSERT INTO picking_tasks
            (shipping_no_p, shipping_no, shipping_date, product_cd, product_name,
             confirmed_boxes, destination_cd, destination_name)
        SELECT
            si.shipping_no_p,
            si.shipping_no,
            si.shipping_date,
            si.product_cd,
            si.product_name,
            si.confirmed_boxes,
            si.destination_cd,
            si.destination_name
        FROM shipping_items si
        WHERE si.shipping_date >= CURDATE()
          AND si.status != 'キャンセル'
          AND si.shipping_no_p IS NOT NULL
          AND si.shipping_no_p != ''
        ON DUPLICATE KEY UPDATE
            shipping_no      = VALUES(shipping_no),
            shipping_date    = VALUES(shipping_date),
            product_cd       = VALUES(product_cd),
            product_name     = VALUES(product_name),
            confirmed_boxes  = VALUES(confirmed_boxes),
            destination_cd   = VALUES(destination_cd),
            destination_name = VALUES(destination_name)
    """)
    result = await db.execute(sync_sql)
    await db.commit()
    synced_count = result.rowcount

    logger.info("picking_tasks に %d 件同期しました", synced_count)
    return {
        "success": True,
        "message": f"picking_tasks に {synced_count} 件同期しました",
        "synced_count": synced_count,
    }


# ================================================================
# 5. GET /history  ─ ピッキング履歴
# ================================================================
@router.get("/history")
async def get_picking_history(
    start_date: Optional[str] = Query(None, description="開始日（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="終了日（YYYY-MM-DD）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """ピッキング履歴を期間指定で返す。デフォルトは過去30日"""
    params: dict = {}
    if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date
        date_condition = "shipping_date BETWEEN :start_date AND :end_date"
    elif start_date:
        params["start_date"] = start_date
        date_condition = "shipping_date >= :start_date"
    elif end_date:
        params["end_date"] = end_date
        date_condition = "shipping_date <= :end_date"
    else:
        # デフォルト: 過去30日
        date_condition = "shipping_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"

    # 統計
    stats_q = text(f"""
        SELECT
            COUNT(*)                                              AS total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status = 'pending'   THEN 1 ELSE 0 END) AS pending,
            SUM(confirmed_boxes)                                   AS total_boxes,
            SUM(picked_quantity)                                    AS total_picked
        FROM picking_tasks
        WHERE {date_condition}
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
        SELECT *
        FROM picking_tasks
        WHERE {date_condition}
        ORDER BY shipping_date DESC, shipping_no_p ASC
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
        "items": [_task_row_to_dict(r) for r in rows],
    }


# ================================================================
# 6. GET /performance-by-destination  ─ 担当者別・納入先別パフォーマンス
# 担当者＝納入先グループ（destination_groups の group_name）。該当グループの destinations + 日期で picking_tasks を集計
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
    各担当者＝1グループ＝1組の納入先(destinations)。該当組の納入先＋日期範囲で picking_tasks を集計。
    件数は出荷单维度 COUNT(DISTINCT shipping_no_p)、完了は status が completed/picked/完了 のみ。品名 加工・アーチ・料金 除外。
    """
    params: dict = {}
    if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date
        date_condition = "pt.shipping_date BETWEEN :start_date AND :end_date"
    elif start_date:
        params["start_date"] = start_date
        date_condition = "pt.shipping_date >= :start_date"
    elif end_date:
        params["end_date"] = end_date
        date_condition = "pt.shipping_date <= :end_date"
    else:
        date_condition = "pt.shipping_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"

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
        " AND (pt.product_name NOT LIKE '%加工%' AND pt.product_name NOT LIKE '%アーチ%' AND pt.product_name NOT LIKE '%料金%')"
    )
    completed_condition = (
        "LOWER(TRIM(COALESCE(pt.status,''))) IN ('completed','picked') OR TRIM(COALESCE(pt.status,'')) = '完了'"
    )
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
                pt.destination_cd,
                pt.destination_name,
                COUNT(DISTINCT pt.shipping_no_p) AS total_tasks,
                COUNT(DISTINCT CASE WHEN ({completed_condition}) THEN pt.shipping_no_p END) AS completed_tasks
            FROM picking_tasks pt
            WHERE {date_condition}
            {product_exclude}
            AND pt.destination_cd IN :dest_cds
            GROUP BY pt.destination_cd, pt.destination_name
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
    """90日以前の shipping_log を削除"""
    result = await db.execute(text(
        "DELETE FROM shipping_log WHERE date < DATE_SUB(CURDATE(), INTERVAL 90 DAY)"
    ))
    await db.commit()
    deleted = result.rowcount
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
    await db.commit()
    deleted = result.rowcount
    return {"success": True, "message": f"{deleted} 件の重複を削除しました", "deleted": deleted}


# ================================================================
# 11. GET /sync-status  ─ 同期状態
# ================================================================
@router.get("/sync-status")
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """picking_tasks の同期状態を返す"""
    try:
        pt_result = await db.execute(text(
            "SELECT COUNT(*) AS cnt, MAX(updated_at) AS last_sync FROM picking_tasks"
        ))
        pt_row = pt_result.mappings().first()
        total_pt = int(pt_row["cnt"] or 0) if pt_row else 0
        last_sync = str(pt_row["last_sync"]) if pt_row and pt_row["last_sync"] else None
        table_exists = True
    except Exception:
        total_pt = 0
        last_sync = None
        table_exists = False

    sl_result = await db.execute(text("SELECT COUNT(*) AS cnt FROM shipping_log"))
    total_sl = int(sl_result.scalar() or 0)

    return {
        "totalPickingTasks": total_pt,
        "totalShippingLogs": total_sl,
        "lastSyncTime": last_sync,
        "tableExists": table_exists,
        "availableForSync": total_sl,
        "alreadySynced": total_pt,
        "syncRate": round((total_pt / total_sl * 100) if total_sl > 0 else 0, 1),
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
    for table in ["shipping_items", "shipping_log", "picking_tasks", "picking_list"]:
        try:
            r = await db.execute(text(f"SELECT COUNT(*) AS cnt FROM {table}"))
            cnt = int(r.scalar() or 0)
            r2 = await db.execute(text(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 3"))
            latest = [dict(row) for row in r2.mappings().all()]
            info[table] = {"count": cnt, "latest": latest}
        except Exception as e:
            info[table] = {"count": 0, "latest": [], "error": str(e)}
    return info

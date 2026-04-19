"""
生産計画月次ベースライン API
- POST /generate: 集計して production_plan_baselines に登録。メッキ・検査は weekdayBaseline 指定時、平日のみ同一値・土日は任意入力時のみ行を作成
- DELETE /delete: ベースライン削除
- GET /comparison: 基準 vs 現行計画・実績の比較
- GET /records: 修正用レコード一覧
- PUT /plan-quantity: 計画数量の更新
- DELETE /record: ベースライン 1 件削除（基準月・計画日・工程）
- POST /export-pdf-to-folder: 工程別PDFを指定フォルダに保存
- GET /plan-operation-rate: production_plan_rate（操業度Excel取込）一覧・月・工程で絞り込み
"""
import logging
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Optional, Set, Tuple

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Excel 取込の production_plan_updates は別用途。生産サマリの日次 *_plan は update-plan が schedule_details を設備工程別に集計して反映する。
SUMMARY_PLAN_COLUMN_BY_PROCESS: dict[str, str] = {
    "成型": "molding_plan",
    "溶接": "welding_plan",
    "メッキ": "plating_plan",
    "切断": "cutting_plan",
    "面取": "chamfering_plan",
    "検査": "inspection_plan",
    "外注メッキ": "outsourced_plating_plan",
    "外注溶接": "outsourced_welding_plan",
}
ALLOWED_SUMMARY_PLAN_COLUMNS = frozenset(SUMMARY_PLAN_COLUMN_BY_PROCESS.values())

# メッキ・検査は「平日一律＋土日任意」の手入力ベースラインで生成する
FIXED_WEEKDAY_BASELINE_PROCESSES = frozenset({"メッキ", "検査"})


async def _rows_from_summary_plan_by_date(
    db: AsyncSession,
    start_date: str,
    end_date: str,
    process_name_filter: Optional[str],
    skip_keys: Set[Tuple[str, str]],
) -> list[dict[str, Any]]:
    """production_summarys を日付単位で *_plan 集計し、skip_keys に無い (plan_date, 工程名) だけ返す。"""
    out: list[dict[str, Any]] = []
    for proc_label, col in SUMMARY_PLAN_COLUMN_BY_PROCESS.items():
        if process_name_filter and proc_label != process_name_filter:
            continue
        if col not in ALLOWED_SUMMARY_PLAN_COLUMNS:
            continue
        q = text(
            f"""
            SELECT `date` AS plan_date, COALESCE(SUM(`{col}`), 0) AS plan_quantity
            FROM production_summarys
            WHERE `date` BETWEEN :start_date AND :end_date
            GROUP BY `date`
            HAVING COALESCE(SUM(`{col}`), 0) > 0
            """
        )
        res = await db.execute(q, {"start_date": start_date, "end_date": end_date})
        for r in res.mappings().fetchall():
            pd = _date_str(r.get("plan_date"))
            if not pd:
                continue
            if (pd, proc_label) in skip_keys:
                continue
            out.append({"plan_date": r.get("plan_date"), "process_name": proc_label, "plan_quantity": r.get("plan_quantity")})
    return out


async def _merge_current_plan_from_summary(
    db: AsyncSession,
    start_date: str,
    end_date: str,
    process_name_filter: Optional[str],
    current_plan_map: Dict[Tuple[str, str], float],
) -> None:
    """現行計画マップに production_summarys 由来の日次合計を補完（ppu に同一キーが無い場合のみ）。"""
    for proc_label, col in SUMMARY_PLAN_COLUMN_BY_PROCESS.items():
        if process_name_filter and proc_label != process_name_filter:
            continue
        if col not in ALLOWED_SUMMARY_PLAN_COLUMNS:
            continue
        q = text(
            f"""
            SELECT `date` AS plan_date, COALESCE(SUM(`{col}`), 0) AS plan_quantity
            FROM production_summarys
            WHERE `date` BETWEEN :start_date AND :end_date
            GROUP BY `date`
            HAVING COALESCE(SUM(`{col}`), 0) > 0
            """
        )
        res = await db.execute(q, {"start_date": start_date, "end_date": end_date})
        for r in res.mappings().fetchall():
            pd = _date_str(r.get("plan_date"))
            if not pd:
                continue
            key = (pd, proc_label)
            if key not in current_plan_map:
                current_plan_map[key] = _decimal_float(r.get("plan_quantity"))


def _date_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()[:10] if val else None
    return str(val)[:10]


def _decimal_float(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _optional_body_float(body: dict[str, Any], key: str) -> Optional[float]:
    if key not in body:
        return None
    v = body[key]
    if v is None:
        return None
    if isinstance(v, str) and not str(v).strip():
        return None
    return _decimal_float(v)


async def _generate_fixed_weekday_baseline(
    db: AsyncSession,
    *,
    month_start: str,
    process_name: str,
    start_date: str,
    end_date: str,
    weekday_baseline: float,
    saturday_baseline: Optional[float],
    sunday_baseline: Optional[float],
) -> int:
    """月内の各日について、平日は weekday_baseline。土日は値が指定されたときのみ INSERT。"""
    delete_sql = text("""
        DELETE FROM production_plan_baselines
        WHERE baseline_month = :baseline_month AND process_name = :process_name
    """)
    await db.execute(delete_sql, {"baseline_month": month_start, "process_name": process_name})

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    insert_sql = text("""
        INSERT INTO production_plan_baselines
        (baseline_month, snapshot_date, plan_date, machine_name, product_cd, product_name, process_name, plan_quantity, actual_quantity, created_at)
        VALUES (:baseline_month, :snapshot_date, :plan_date, '', '', '', :process_name, :plan_quantity, 0, :created_at)
    """)

    d0 = date.fromisoformat(start_date[:10])
    d1 = date.fromisoformat(end_date[:10])
    count = 0
    cur = d0
    while cur <= d1:
        wd = cur.weekday()  # 月=0 … 日=6
        plan_qty: Optional[float] = None
        if wd < 5:
            plan_qty = weekday_baseline
        elif wd == 5:
            if saturday_baseline is not None:
                plan_qty = saturday_baseline
        else:
            if sunday_baseline is not None:
                plan_qty = sunday_baseline
        if plan_qty is not None:
            plan_date_str = cur.isoformat()
            await db.execute(insert_sql, {
                "baseline_month": month_start,
                "snapshot_date": now,
                "plan_date": plan_date_str,
                "process_name": process_name,
                "plan_quantity": plan_qty,
                "created_at": now,
            })
            count += 1
        cur += timedelta(days=1)
    return count


@router.post("/generate")
async def generate_plan_baseline(
    body: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """対象月を集計し production_plan_baselines に登録（上書き）。ppu に無い工程は production_summarys の *_plan で補完。"""
    baseline_month = body.get("baselineMonth")
    process_name = body.get("processName") or None
    if not baseline_month:
        return {"success": False, "message": "baselineMonth を指定してください"}

    # baseline_month は YYYY-MM-DD（月初）想定
    month_start = _date_str(baseline_month)
    if not month_start:
        return {"success": False, "message": "baselineMonth の形式が不正です"}

    # 対象月の範囲（その月の1日〜月末）
    from sqlalchemy import text as sql_text
    range_sql = sql_text("""
        SELECT DATE(:month_start) AS start_date,
               LAST_DAY(DATE(:month_start)) AS end_date
    """)
    range_result = await db.execute(range_sql, {"month_start": month_start})
    range_row = range_result.mappings().fetchone()
    if not range_row:
        return {"success": False, "message": "日付の取得に失敗しました"}
    start_date = range_row["start_date"].isoformat()[:10] if hasattr(range_row["start_date"], "isoformat") else str(range_row["start_date"])[:10]
    end_date = range_row["end_date"].isoformat()[:10] if hasattr(range_row["end_date"], "isoformat") else str(range_row["end_date"])[:10]

    proc_fixed = (process_name or "").strip()
    if proc_fixed in FIXED_WEEKDAY_BASELINE_PROCESSES:
        wb_raw = body.get("weekdayBaseline")
        if wb_raw is None or (isinstance(wb_raw, str) and not str(wb_raw).strip()):
            return {"success": False, "message": "平日の基準計画数（weekdayBaseline）を入力してください"}
        weekday_baseline = _decimal_float(wb_raw)
        if weekday_baseline <= 0:
            return {"success": False, "message": "平日の基準計画数は 0 より大きい値にしてください"}
        sat = _optional_body_float(body, "saturdayBaseline")
        sun = _optional_body_float(body, "sundayBaseline")
        count = await _generate_fixed_weekday_baseline(
            db,
            month_start=month_start,
            process_name=proc_fixed,
            start_date=start_date,
            end_date=end_date,
            weekday_baseline=weekday_baseline,
            saturday_baseline=sat,
            sunday_baseline=sun,
        )
        await db.commit()
        return {"success": True, "message": "ベースラインを生成しました", "count": count}

    # production_plan_updates を plan_date, process_name で集計
    agg_sql = text("""
        SELECT plan_date, process_name,
               COALESCE(SUM(quantity), 0) AS plan_quantity
        FROM production_plan_updates
        WHERE plan_date BETWEEN :start_date AND :end_date
          AND (:process_name IS NULL OR process_name = :process_name)
          AND (product_name IS NOT NULL AND TRIM(product_name) != '')
          AND COALESCE(quantity, 0) > 0
        GROUP BY plan_date, process_name
    """)
    agg_result = await db.execute(agg_sql, {"start_date": start_date, "end_date": end_date, "process_name": process_name})
    rows = list(agg_result.mappings().fetchall())
    ppu_keys: Set[Tuple[str, str]] = set()
    for r in rows:
        pd = _date_str(r.get("plan_date"))
        pr = (r.get("process_name") or "").strip()
        if pd:
            ppu_keys.add((pd, pr))
    summary_extra = await _rows_from_summary_plan_by_date(db, start_date, end_date, process_name, ppu_keys)
    rows.extend(summary_extra)

    # 既存の該当ベースラインを削除
    if process_name:
        delete_sql = text("""
            DELETE FROM production_plan_baselines
            WHERE baseline_month = :baseline_month AND process_name = :process_name
        """)
        await db.execute(delete_sql, {"baseline_month": month_start, "process_name": process_name})
    else:
        delete_sql = text("DELETE FROM production_plan_baselines WHERE baseline_month = :baseline_month")
        await db.execute(delete_sql, {"baseline_month": month_start})

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    for r in rows:
        plan_date = _date_str(r.get("plan_date"))
        proc = (r.get("process_name") or "").strip() or ""
        plan_qty = _decimal_float(r.get("plan_quantity"))
        if not plan_date:
            continue
        insert_sql = text("""
            INSERT INTO production_plan_baselines
            (baseline_month, snapshot_date, plan_date, machine_name, product_cd, product_name, process_name, plan_quantity, actual_quantity, created_at)
            VALUES (:baseline_month, :snapshot_date, :plan_date, '', '', '', :process_name, :plan_quantity, 0, :created_at)
        """)
        await db.execute(insert_sql, {
            "baseline_month": month_start,
            "snapshot_date": now,
            "plan_date": plan_date,
            "process_name": proc,
            "plan_quantity": plan_qty,
            "created_at": now,
        })

    await db.commit()
    return {"success": True, "message": "ベースラインを生成しました", "count": len(rows)}


@router.delete("/delete")
async def delete_plan_baseline(
    baselineMonth: str = Query(..., description="基準月 YYYY-MM-DD（月初）"),
    processName: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定月（および工程）のベースラインを削除"""
    month_start = _date_str(baselineMonth) or baselineMonth[:10]
    if processName and str(processName).strip():
        sql = text("""
            DELETE FROM production_plan_baselines
            WHERE baseline_month = :baseline_month AND process_name = :process_name
        """)
        result = await db.execute(sql, {"baseline_month": month_start, "process_name": processName.strip()})
    else:
        sql = text("DELETE FROM production_plan_baselines WHERE baseline_month = :baseline_month")
        result = await db.execute(sql, {"baseline_month": month_start})
    await db.commit()
    return {"success": True, "message": "ベースラインを削除しました"}


def _row_to_comparison_item(row: dict) -> dict:
    plan_date = _date_str(row.get("plan_date"))
    baseline_plan = _decimal_float(row.get("baseline_plan"))
    current_plan = _decimal_float(row.get("current_plan"))
    current_actual = row.get("current_actual")
    if current_actual is not None and not isinstance(current_actual, (int, float)):
        current_actual = _decimal_float(current_actual)
    elif current_actual is None:
        current_actual = None
    else:
        current_actual = float(current_actual)
    plan_diff = current_plan - baseline_plan
    actual_diff = (baseline_plan - current_actual) if current_actual is not None else None
    return {
        "plan_date": plan_date,
        "process_name": row.get("process_name") or "",
        "baseline_plan": baseline_plan,
        "current_plan": current_plan,
        "plan_diff": plan_diff,
        "current_actual": current_actual,
        "actual_diff": actual_diff,
    }


def _empty_comparison_response(month_start: str) -> dict:
    return {
        "success": True,
        "baselineMonth": month_start,
        "summary": None,
        "items": [],
    }


@router.get("/comparison")
async def get_plan_baseline_comparison(
    baselineMonth: str = Query(..., description="基準月 YYYY-MM-DD（月初）"),
    processName: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """基準月ベースラインと現行計画・実績の比較を返す"""
    month_start = _date_str(baselineMonth) or (baselineMonth[:10] if baselineMonth else "")
    if not month_start:
        return _empty_comparison_response(month_start or "")

    try:
        range_sql = text("""
            SELECT DATE(:month_start) AS start_date, LAST_DAY(DATE(:month_start)) AS end_date
        """)
        range_result = await db.execute(range_sql, {"month_start": month_start})
        range_row = range_result.mappings().fetchone()
        if not range_row:
            return _empty_comparison_response(month_start)
        start_date = _date_str(range_row.get("start_date"))
        if not start_date and range_row.get("start_date") is not None:
            start_date = str(range_row["start_date"])[:10]
        end_date = _date_str(range_row.get("end_date"))
        if not end_date and range_row.get("end_date") is not None:
            end_date = str(range_row["end_date"])[:10]
        if not start_date or not end_date:
            return _empty_comparison_response(month_start)

        # 基準月の翌月1日（実績は [monthStart, nextMonthStart) で集計）
        _d = date.fromisoformat(month_start[:10])
        if _d.month == 12:
            next_month_first = date(_d.year + 1, 1, 1)
        else:
            next_month_first = date(_d.year, _d.month + 1, 1)
        next_month_start_str = next_month_first.isoformat()

        # ベースライン集計（日付×工程）
        base_sql = text("""
            SELECT plan_date, process_name, COALESCE(SUM(plan_quantity), 0) AS baseline_plan
            FROM production_plan_baselines
            WHERE baseline_month = :baseline_month
              AND (:process_name IS NULL OR process_name = :process_name)
            GROUP BY plan_date, process_name
        """)
        base_result = await db.execute(base_sql, {"baseline_month": month_start, "process_name": processName or None})
        base_rows = {(_date_str(r["plan_date"]), (r.get("process_name") or "").strip()): _decimal_float(r.get("baseline_plan")) for r in base_result.mappings().fetchall()}

        # 現行計画（production_plan_updates）を同じ月で集計
        curr_sql = text("""
            SELECT plan_date, process_name, COALESCE(SUM(quantity), 0) AS current_plan
            FROM production_plan_updates
            WHERE plan_date BETWEEN :start_date AND :end_date
              AND (:process_name IS NULL OR process_name = :process_name)
            GROUP BY plan_date, process_name
        """)
        curr_result = await db.execute(curr_sql, {"start_date": start_date, "end_date": end_date, "process_name": processName or None})
        curr_rows = list(curr_result.mappings().fetchall())
        current_plan_map = {(_date_str(r["plan_date"]), (r.get("process_name") or "").strip()): _decimal_float(r.get("current_plan")) for r in curr_rows}
        await _merge_current_plan_from_summary(db, start_date, end_date, processName or None, current_plan_map)

        # 現行実績：stock_transaction_logs を日付+工程で集計（transaction_type='実績'、[start_date, next_month_start)）
        actual_sql = text("""
            SELECT
                DATE(l.transaction_time) AS plan_date_value,
                COALESCE(pr.process_name, '') AS process_name_value,
                SUM(COALESCE(l.quantity, 0)) AS total_actual
            FROM stock_transaction_logs l
            LEFT JOIN processes pr ON l.process_cd = pr.process_cd
            WHERE l.transaction_time >= :start_date AND l.transaction_time < :next_month_start
              AND l.transaction_type = '実績'
              AND (:process_name IS NULL OR pr.process_name = :process_name)
            GROUP BY DATE(l.transaction_time), COALESCE(pr.process_name, '')
        """)
        actual_result = await db.execute(actual_sql, {
            "start_date": start_date,
            "next_month_start": next_month_start_str,
            "process_name": processName or None,
        })
        actual_map = {}
        for r in actual_result.mappings().fetchall():
            k = (_date_str(r.get("plan_date_value")), (r.get("process_name_value") or "").strip())
            actual_map[k] = _decimal_float(r.get("total_actual"))

        # dateKeys = 基準・現行計画・実績のキー和集合
        date_keys = set(base_rows.keys()) | set(current_plan_map.keys()) | set(actual_map.keys())
        today_str = date.today().isoformat()

        def _resolve_current_actual(plan_date: str, baseline_plan: float, current_plan: float, raw_actual: Optional[float]) -> Optional[float]:
            """現行実績の補正：過去日で計画あり実績なしの場合は 0、それ以外は raw のまま（今日・未来で実績なしは null）"""
            is_future = (plan_date or "") > today_str
            is_today = (plan_date or "") == today_str
            if raw_actual is not None:
                return raw_actual
            if not is_future and not is_today and (baseline_plan != 0 or current_plan != 0):
                return 0.0
            return None

        items = []
        for key in sorted(date_keys):
            plan_date, proc = key[0], key[1]
            if not plan_date:
                continue
            baseline_plan = base_rows.get(key, 0.0)
            current_plan = current_plan_map.get(key, 0.0)
            raw_actual = actual_map.get(key)  # 実績テーブルに無い場合は None
            current_actual = _resolve_current_actual(plan_date, baseline_plan, current_plan, raw_actual)
            plan_diff = current_plan - baseline_plan
            actual_diff = (current_actual - baseline_plan) if current_actual is not None else None
            items.append({
                "plan_date": plan_date,
                "process_name": proc,
                "baseline_plan": baseline_plan,
                "current_plan": current_plan,
                "plan_diff": plan_diff,
                "current_actual": current_actual,
                "actual_diff": actual_diff,
            })

        items.sort(key=lambda x: (x["plan_date"] or "", x["process_name"] or ""))

        baseline_total = sum(i["baseline_plan"] for i in items)
        current_plan_total = sum(i["current_plan"] for i in items)
        plan_diff_total = current_plan_total - baseline_total

        # 現行実績合計：currentActual !== null かつ 非未来日 のときのみ加算（今日実績なしは加算しない）
        # 計画対実績差：按日 (当日実績−当日基準計画)、非未来かつ実績ありの項のみ合計
        current_actual_total = 0
        plan_vs_actual_diff_total = 0
        for i in items:
            plan_date = i.get("plan_date") or ""
            if plan_date > today_str:
                continue
            if i.get("current_actual") is not None:
                current_actual_total += i["current_actual"]
                plan_vs_actual_diff_total += i["current_actual"] - i["baseline_plan"]
        has_any_actual = any(i.get("current_actual") is not None for i in items)
        actual_diff_total = plan_vs_actual_diff_total if has_any_actual else None

        summary = {
            "baselinePlanTotal": baseline_total,
            "currentPlanTotal": current_plan_total,
            "planDifference": plan_diff_total,
            "currentActualTotal": current_actual_total if items else None,
            "actualDifference": actual_diff_total,
        }

        return {
            "success": True,
            "baselineMonth": month_start,
            "summary": summary,
            "items": items,
        }
    except Exception as e:
        logger.exception("plan-baseline comparison failed: %s", e)
        return _empty_comparison_response(month_start)


@router.get("/records")
async def get_plan_baseline_records(
    baselineMonth: str = Query(...),
    processName: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """修正用：ベースラインのレコード一覧（日付×工程の plan_quantity を編集するため）"""
    month_start = _date_str(baselineMonth) or baselineMonth[:10]
    sql = text("""
        SELECT plan_date, process_name, plan_quantity, actual_quantity,
               machine_name, product_cd, product_name
        FROM production_plan_baselines
        WHERE baseline_month = :baseline_month
          AND (:process_name IS NULL OR process_name = :process_name)
        ORDER BY plan_date, process_name
    """)
    result = await db.execute(sql, {"baseline_month": month_start, "process_name": processName or None})
    rows = result.mappings().fetchall()
    records = []
    for r in rows:
        records.append({
            "plan_date": _date_str(r.get("plan_date")) or str(r.get("plan_date", ""))[:10],
            "process_name": r.get("process_name") or "",
            "plan_quantity": _decimal_float(r.get("plan_quantity")),
            "actual_quantity": _decimal_float(r.get("actual_quantity")),
            "machine_name": r.get("machine_name") or "",
            "product_cd": r.get("product_cd") or "",
            "product_name": r.get("product_name") or "",
        })
    return records


@router.put("/plan-quantity")
async def update_plan_baseline_plan_quantity(
    body: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ベースラインの計画数量を 1 件更新（日付×工程で一意）"""
    baseline_month = body.get("baselineMonth")
    plan_date = body.get("planDate")
    process_name = (body.get("processName") or "").strip()
    plan_quantity = body.get("planQuantity")
    if baseline_month is None or plan_date is None:
        return {"success": False, "message": "baselineMonth と planDate を指定してください"}
    try:
        plan_quantity = float(plan_quantity)
    except (TypeError, ValueError):
        return {"success": False, "message": "planQuantity は数値で指定してください"}

    month_start = _date_str(baseline_month) or str(baseline_month)[:10]
    plan_d = _date_str(plan_date) or str(plan_date)[:10]

    sql = text("""
        UPDATE production_plan_baselines
        SET plan_quantity = :plan_quantity
        WHERE baseline_month = :baseline_month AND plan_date = :plan_date AND process_name = :process_name
    """)
    result = await db.execute(sql, {
        "baseline_month": month_start,
        "plan_date": plan_d,
        "process_name": process_name,
        "plan_quantity": plan_quantity,
    })
    await db.commit()
    if result.rowcount == 0:
        return {"success": False, "message": "該当するベースラインがありません"}
    return {"success": True, "message": "更新しました"}


@router.delete("/record")
async def delete_plan_baseline_record(
    baselineMonth: str = Query(..., description="基準月 YYYY-MM-DD（月初）"),
    planDate: str = Query(..., description="計画日 YYYY-MM-DD"),
    processName: str = Query("", description="工程名（未指定は空文字で一致）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ベースライン 1 件削除（baseline_month + plan_date + process_name で一意）"""
    month_start = _date_str(baselineMonth) or baselineMonth[:10]
    plan_d = _date_str(planDate) or planDate[:10]
    proc = (processName or "").strip()
    sql = text("""
        DELETE FROM production_plan_baselines
        WHERE baseline_month = :baseline_month AND plan_date = :plan_date AND process_name = :process_name
    """)
    result = await db.execute(sql, {
        "baseline_month": month_start,
        "plan_date": plan_d,
        "process_name": proc,
    })
    await db.commit()
    if result.rowcount == 0:
        return {"success": False, "message": "該当するベースラインがありません"}
    return {"success": True, "message": "削除しました"}


def _plan_rate_display_process(file_name: str) -> str:
    if not file_name:
        return ""
    if "加工" in file_name:
        return "成型"
    if "溶接" in file_name:
        return "溶接"
    return ""


def _plan_rate_month_label(file_name: str) -> str:
    if not file_name:
        return ""
    m = re.search(r"[（(](\d{1,2})月[）)]", file_name)
    if m:
        return f"{int(m.group(1))}月"
    return ""


def _operation_variance_int_str(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""
    try:
        n = float(s.replace(",", "").replace("%", "").strip())
        if n != n:  # NaN
            return s
        return str(int(round(n)))
    except (TypeError, ValueError):
        return s


@router.get("/plan-operation-rate")
async def list_plan_operation_rate(
    monthNum: Optional[int] = Query(None, ge=1, le=12, description="ファイル名の「N月」で絞り込み"),
    processName: Optional[str] = Query(None, description="成型 / 溶接 / 省略で両方"),
    limit: int = Query(5000, ge=1, le=50000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """production_plan_rate を取得。加工→成型・溶接→溶接として表示用フィールドを付与。月はファイル名の（N月）／(N月) から判定。"""
    where_parts = ["(file_name LIKE '%加工%' OR file_name LIKE '%溶接%')"]
    params: dict[str, Any] = {"limit": limit}

    if monthNum is not None:
        where_parts.append("(file_name LIKE :fn_m1 OR file_name LIKE :fn_m2)")
        params["fn_m1"] = f"%({monthNum}月)%"
        params["fn_m2"] = f"%（{monthNum}月）%"

    proc = (processName or "").strip()
    if proc == "成型":
        where_parts.append("file_name LIKE '%加工%'")
    elif proc == "溶接":
        where_parts.append("file_name LIKE '%溶接%'")

    where_sql = " AND ".join(where_parts)
    sql = text(f"""
        SELECT id, file_name, processed_at, machine_cd, machine_name, operation_variance
        FROM production_plan_rate
        WHERE {where_sql}
        ORDER BY file_name, machine_name, id
        LIMIT :limit
    """)

    try:
        result = await db.execute(sql, params)
    except Exception as e:
        logger.exception("plan-operation-rate query failed: %s", e)
        return {"success": False, "message": str(e), "items": []}

    rows = result.mappings().fetchall()
    items = []
    for r in rows:
        row = dict(r)
        fn = (row.get("file_name") or "") or ""
        pat = row.get("processed_at")
        processed_at = None
        if pat is not None:
            if hasattr(pat, "isoformat"):
                processed_at = pat.isoformat(sep=" ", timespec="seconds") if pat else None
            else:
                processed_at = str(pat)[:19]
        items.append({
            "id": row.get("id"),
            "file_name": fn,
            "processed_at": processed_at,
            "machine_cd": row.get("machine_cd"),
            "machine_name": row.get("machine_name"),
            "operation_variance": _operation_variance_int_str(row.get("operation_variance")),
            "display_process": _plan_rate_display_process(fn),
            "display_month": _plan_rate_month_label(fn),
        })
    return {"success": True, "items": items, "count": len(items)}


# 工程別PDF保存先（社内共有フォルダ）
BASELINE_PDF_SAVE_DIR = Path(r"\\192.168.1.200\社内共有\02_生産管理部\Data\BT-data\保存データ")


@router.post("/export-pdf-to-folder")
async def export_pdf_to_folder(
    baselineMonth: str = Form(..., description="基準月 YYYY-MM-DD"),
    files: list[UploadFile] = File(..., description="工程別PDF（ファイル名が工程名.pdf）"),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程別PDFを指定フォルダに保存する。files は各工程のPDF（ファイル名例: 切断.pdf）"""
    if not baselineMonth or len(baselineMonth) < 7:
        return {"success": False, "message": "baselineMonth を指定してください"}
    month_label = baselineMonth[:7].replace("-", "")  # YYYYMM
    try:
        save_dir = BASELINE_PDF_SAVE_DIR
        save_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.exception("ベースラインPDF保存フォルダの作成に失敗: %s", e)
        return {"success": False, "message": f"保存フォルダにアクセスできません: {e}"}
    saved: list[str] = []
    errors: list[str] = []
    for f in files:
        if not f.filename or not f.filename.endswith(".pdf"):
            continue
        # ファイル名から拡張子を除いた部分を工程名として使用
        process_name = f.filename[:-4].strip() or "未指定"
        safe_name = "".join(c if c not in r'<>:"/\|?*' else "_" for c in process_name)
        out_name = f"ベースライン比較_{month_label}_{safe_name}.pdf"
        out_path = save_dir / out_name
        try:
            content = await f.read()
            out_path.write_bytes(content)
            saved.append(out_name)
        except Exception as e:
            logger.exception("PDF保存失敗 %s: %s", out_name, e)
            errors.append(f"{out_name}: {e}")
    if errors:
        return {"success": False, "message": "一部保存に失敗しました", "saved": saved, "errors": errors}
    return {"success": True, "message": f"{len(saved)}件のPDFを保存しました", "saved": saved}

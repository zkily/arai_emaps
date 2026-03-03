"""
生産計画月次ベースライン API
- POST /generate: production_plan_updates から対象月を集計して production_plan_baselines に登録
- DELETE /delete: ベースライン削除
- GET /comparison: 基準 vs 現行計画・実績の比較
- GET /records: 修正用レコード一覧
- PUT /plan-quantity: 計画数量の更新
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


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


@router.post("/generate")
async def generate_plan_baseline(
    body: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """対象月の production_plan_updates を集計し、production_plan_baselines に登録（上書き）"""
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
    rows = agg_result.mappings().fetchall()

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

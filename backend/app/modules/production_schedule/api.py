"""
生産状況・スケジュール API
- GET /processing-status: production_plan_schedules を file_name でフィルタして返す
- GET /schedule: 設備運行時間スロット（現状スタブ、必要に応じて production_plan_schedules 等から導出可能）
- GET /plan/batch/schedule-months: 生産月一覧
- GET /plan/batch/material-requirements-summary: instruction_plans を期間（start_date 優先）で集計し材料所要本数を返す
- POST /plan/batch/generate-from-schedule: 生産月で production_plan_schedules から切断指示計画(instruction_plans)を生成
"""
import logging
import re
from decimal import Decimal
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


async def _table_has_column(db: AsyncSession, table_name: str, column_name: str) -> bool:
    """現在の DB でテーブルが指定列を持つか（MySQL information_schema）。照会不可時は False（安全側の SQL にフォールバック）。"""
    try:
        r = await db.execute(
            text(
                """
                SELECT 1 FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table_name
                  AND COLUMN_NAME = :column_name
                LIMIT 1
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        )
        return r.first() is not None
    except Exception as e:
        logger.warning(
            "information_schema 照会失敗 (%s.%s): %s",
            table_name,
            column_name,
            e,
        )
        return False


class GenerateFromScheduleBody(BaseModel):
    month: str  # YYYY-MM e.g. "2025-01"


def _schedule_row_to_dict(row) -> dict:
    """production_plan_schedules 1行を辞書に（frontend の machine_name, product_name, production_order, planned_quantity 等）"""
    def _v(key, default=None):
        val = row.get(key) if hasattr(row, "get") else getattr(row, key, None)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val) if val is not None else default
        if hasattr(val, "isoformat"):
            return val.isoformat()[:10] if val else default
        return val

    return {
        "id": _v("id"),
        "file_name": _v("file_name"),
        "machine_name": _v("machine_name"),
        "product_name": _v("product_name"),
        "production_order": _v("production_order"),
        "planned_quantity": _v("planned_quantity"),
        "production_start_date": _v("production_start_date"),
        "production_end_date": _v("production_end_date"),
        "actual_production": _v("actual_production"),
        "variance": _v("variance"),
        "achievement_rate": _v("achievement_rate"),
        "total_production_time": _v("total_production_time"),
        "operation_variance": _v("operation_variance"),
        "material_lot_count": _v("material_lot_count"),
        "material_name": _v("material_name"),
    }


@router.get("/processing-status")
async def get_processing_status(
    fileName: Optional[str] = Query(None, description="file_name に含まれる文字（例: 1月 → 加工計画(1月).xlsm）"),
    limit: int = Query(100000, ge=1, le=100000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    production_plan_schedules を取得。段取予定発行で利用。
    fileName で file_name を LIKE 検索（例: "1月" で 1月 を含むファイルのレコードのみ）。
    """
    if not fileName or not fileName.strip():
        return {"success": True, "data": [], "message": "OK"}

    sql = text("""
        SELECT id, file_name, processed_at, machine_name, product_name, production_order,
               planned_quantity, production_start_date, production_end_date,
               actual_production, variance, achievement_rate, total_production_time,
               operation_variance, material_lot_count, material_name
        FROM production_plan_schedules
        WHERE file_name LIKE :pattern
        ORDER BY machine_name, product_name, production_order
        LIMIT :limit
    """)
    pattern = f"%{fileName.strip()}%"
    result = await db.execute(sql, {"pattern": pattern, "limit": limit})
    rows = result.mappings().fetchall()
    data = [_schedule_row_to_dict(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


@router.get("/operation-rate")
async def get_operation_rate(
    fileName: Optional[str] = Query(None, description="file_name に含まれる文字（例: 1月）。操業度は machine_name で紐づく"),
    limit: int = Query(10000, ge=1, le=100000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    production_plan_rate を取得。段取予定発行の操業度列用。
    fileName で file_name を LIKE 検索。同一 machine_name が複数ある場合は先頭を採用（必要なら集約可）。
    """
    if not fileName or not fileName.strip():
        return {"success": True, "data": [], "message": "OK"}

    sql = text("""
        SELECT id, file_name, machine_cd, machine_name, operation_variance
        FROM production_plan_rate
        WHERE file_name LIKE :pattern
        ORDER BY machine_name
        LIMIT :limit
    """)
    pattern = f"%{fileName.strip()}%"
    result = await db.execute(sql, {"pattern": pattern, "limit": limit})
    rows = result.mappings().fetchall()

    def _row_to_dict(r):
        row = dict(r)
        def _v(k, default=None):
            val = row.get(k)
            if val is None:
                return default
            if isinstance(val, Decimal):
                return float(val)
            if hasattr(val, "isoformat"):
                return val.isoformat()[:10] if val else default
            return val
        return {
            "machine_cd": _v("machine_cd"),
            "machine_name": _v("machine_name"),
            "operation_variance": _v("operation_variance"),
        }

    data = [_row_to_dict(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


@router.get("/schedule")
async def get_schedule(
    machine_cd: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    設備運行時間スロット取得。frontend は start_time / end_time を期待。
    production_plan_schedules には開始/終了時刻がないため、現状は空リストを返す。
    必要に応じて他テーブルや計算で導出可能。
    """
    # スタブ: 空リストで 404 を避ける
    return {"success": True, "data": {"list": []}, "message": "OK"}


def _parse_month(month: str) -> tuple[date, str]:
    """Parse 'YYYY-MM' -> (production_month date, file_name month label e.g. '1月')."""
    parts = month.strip().split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="month は YYYY-MM 形式で指定してください")
    try:
        y, m = int(parts[0]), int(parts[1])
        if not (1 <= m <= 12):
            raise ValueError("month must be 1-12")
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"無効な月: {month}") from e
    production_month = date(y, m, 1)
    month_label = f"{m}月"
    return production_month, month_label


def _to_int(x) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return int(x)
    try:
        return int(float(str(x).strip()))
    except (ValueError, TypeError):
        return None


def _to_decimal_val(x):
    if x is None:
        return None
    if hasattr(x, "isoformat"):
        return x
    if isinstance(x, (int, float)):
        return x
    try:
        return float(str(x).strip())
    except (ValueError, TypeError):
        return None


@router.get("/plan/batch/schedule-months")
async def get_schedule_months(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    生産月一覧: production_plan_schedules の file_name から月を抽出して返す。
    例: "加工計画(1月).xlsm" → 当年の 1月。該当なしの場合は当年 1月～12月を返す。
    """
    sql = text("""
        SELECT DISTINCT file_name FROM production_plan_schedules
        WHERE file_name IS NOT NULL AND file_name != ''
        ORDER BY file_name
        LIMIT 500
    """)
    result = await db.execute(sql)
    rows = result.mappings().fetchall()
    seen = set()
    out = []
    current_year = date.today().year
    for r in rows:
        fn = dict(r).get("file_name") if hasattr(r, "keys") else None
        if not fn:
            continue
        # "1月" or "01月" or "（1月）" 等を抽出
        m = re.search(r"(\d{1,2})月", str(fn))
        if m:
            month_num = int(m.group(1))
            if 1 <= month_num <= 12 and month_num not in seen:
                seen.add(month_num)
                value = f"{current_year}-{month_num:02d}"
                out.append({"value": value, "label": f"{month_num}月"})
    if not out:
        out = [{"value": f"{current_year}-{m:02d}", "label": f"{m}月"} for m in range(1, 13)]
    return {"success": True, "data": out, "message": "OK"}


@router.get("/plan/batch/list")
async def get_instruction_plans_list(
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    product_name: Optional[str] = Query(None, description="製品名（部分一致）"),
    equipment: Optional[str] = Query(None, description="設備/ライン（production_line 部分一致）"),
    limit: int = Query(5000, ge=1, le=50000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    生産ロット一覧: instruction_plans を取得する。
    """
    conditions = ["1=1"]
    params = {"limit": limit}
    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    params["production_month"] = date(y, m, 1)
                    conditions.append("production_month = :production_month")
        except (ValueError, IndexError):
            pass
    if product_name and product_name.strip():
        conditions.append("product_name LIKE :product_name")
        params["product_name"] = f"%{product_name.strip()}%"
    if equipment and equipment.strip():
        conditions.append("production_line LIKE :equipment")
        params["equipment"] = f"%{equipment.strip()}%"

    sql = text(f"""
        SELECT id, production_month, production_line, priority_order, product_cd, product_name,
               planned_quantity, start_date, end_date, production_lot_size, lot_number,
               is_cutting_instructed, has_chamfering_process, is_chamfering_instructed,
               has_sw_process, is_sw_instructed, management_code, actual_production_quantity,
               take_count, cutting_length, chamfering_length, developed_length, scrap_length,
               material_name, material_manufacturer, standard_specification,
               use_material_stock_sub, usage_count,
               created_at, updated_at
        FROM instruction_plans
        WHERE {" AND ".join(conditions)}
        ORDER BY production_month DESC, production_line, priority_order,
                 CAST(COALESCE(lot_number, '0') AS UNSIGNED),
                 lot_number
        LIMIT :limit
    """)
    result = await db.execute(sql, params)
    rows = result.mappings().fetchall()

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()[:19] if val else default
        return val

    def _row_to_dict(r):
        row = dict(r)
        return {
            "id": row.get("id"),
            "production_month": _v(row, "production_month"),
            "production_line": _v(row, "production_line"),
            "priority_order": row.get("priority_order"),
            "product_cd": _v(row, "product_cd"),
            "product_name": _v(row, "product_name"),
            "planned_quantity": row.get("planned_quantity"),
            "start_date": _v(row, "start_date"),
            "end_date": _v(row, "end_date"),
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": _v(row, "lot_number"),
            "is_cutting_instructed": row.get("is_cutting_instructed"),
            "has_chamfering_process": row.get("has_chamfering_process"),
            "is_chamfering_instructed": row.get("is_chamfering_instructed"),
            "has_sw_process": row.get("has_sw_process"),
            "is_sw_instructed": row.get("is_sw_instructed"),
            "management_code": _v(row, "management_code"),
            "actual_production_quantity": row.get("actual_production_quantity"),
            "take_count": row.get("take_count"),
            "cutting_length": _v(row, "cutting_length"),
            "chamfering_length": _v(row, "chamfering_length"),
            "developed_length": _v(row, "developed_length"),
            "scrap_length": _v(row, "scrap_length"),
            "material_name": _v(row, "material_name"),
            "material_manufacturer": _v(row, "material_manufacturer"),
            "standard_specification": _v(row, "standard_specification"),
            "use_material_stock_sub": row.get("use_material_stock_sub"),
            "usage_count": _v(row, "usage_count", 1),
            "created_at": _v(row, "created_at"),
            "updated_at": _v(row, "updated_at"),
        }

    data = [_row_to_dict(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


@router.get("/plan/batch/material-requirements-summary")
async def get_material_requirements_summary_from_instruction_plans(
    date_start: Optional[str] = Query(None, description="集計開始日 YYYY-MM-DD（DATE(start_date) で判定、start_date 未設定行は対象外）"),
    date_end: Optional[str] = Query(None, description="集計終了日 YYYY-MM-DD（含む）"),
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM（date_start/date_end 未指定時にその月の全日を期間として使用）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    instruction_plans を期間で絞り、材料ごとに件数（行数）を集計する。
    - start_date が NULL の行は集計対象外
    - 期間キー: DATE(start_date)
    - 指標: COUNT(*)（planned_quantity / actual_production_quantity / usage_count は使わない）
    """
    d_start = _parse_date_ymd(date_start) if date_start else None
    d_end = _parse_date_ymd(date_end) if date_end else None

    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    if d_start is None:
                        d_start = date(y, m, 1)
                    if d_end is None:
                        if m == 12:
                            d_end = date(y, 12, 31)
                        else:
                            d_end = date(y, m + 1, 1) - timedelta(days=1)
        except (ValueError, IndexError):
            pass

    if d_start is None or d_end is None:
        raise HTTPException(
            status_code=400,
            detail="date_start と date_end を指定するか、production_month（YYYY-MM）を指定してください。",
        )
    if d_start > d_end:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下にしてください。")

    conditions = [
        "start_date IS NOT NULL",
        "DATE(start_date) >= :d_start",
        "DATE(start_date) <= :d_end",
    ]
    params = {"d_start": d_start, "d_end": d_end}

    sql = text(f"""
        SELECT
            COALESCE(NULLIF(TRIM(material_name), ''), '(未設定)') AS material_name,
            COALESCE(NULLIF(TRIM(material_manufacturer), ''), '') AS material_manufacturer,
            COALESCE(NULLIF(TRIM(standard_specification), ''), '') AS standard_specification,
            COUNT(*) AS piece_count
        FROM instruction_plans
        WHERE {" AND ".join(conditions)}
        GROUP BY
            COALESCE(NULLIF(TRIM(material_name), ''), '(未設定)'),
            COALESCE(NULLIF(TRIM(material_manufacturer), ''), ''),
            COALESCE(NULLIF(TRIM(standard_specification), ''), '')
        ORDER BY material_manufacturer ASC, material_name ASC, standard_specification ASC
    """)

    try:
        result = await db.execute(sql, params)
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="instruction_plans テーブルが存在しません。",
            ) from e
        logger.exception("material-requirements-summary 集計失敗")
        raise HTTPException(status_code=500, detail="材料需要量の集計に失敗しました。") from e

    def _icount(v) -> int:
        if v is None:
            return 0
        if isinstance(v, Decimal):
            return int(v)
        return int(v)

    items = []
    total_pieces = 0
    for r in rows:
        rd = dict(r)
        c = _icount(rd.get("piece_count"))
        total_pieces += c
        items.append(
            {
                "material_name": rd.get("material_name"),
                "material_manufacturer": rd.get("material_manufacturer"),
                "standard_specification": rd.get("standard_specification"),
                "piece_count": c,
            }
        )

    # 日別×材料の二次元表用（期間が長すぎると列数過多のため上限）
    _DAY_MATRIX_MAX_DAYS = 186
    span_days = (d_end - d_start).days + 1
    daily_matrix: Optional[dict] = None
    daily_matrix_omitted = span_days > _DAY_MATRIX_MAX_DAYS

    if not daily_matrix_omitted:
        daily_sql = text(f"""
            SELECT
                DATE(start_date) AS eff_date,
                COALESCE(NULLIF(TRIM(material_name), ''), '(未設定)') AS material_name,
                COALESCE(NULLIF(TRIM(material_manufacturer), ''), '') AS material_manufacturer,
                COALESCE(NULLIF(TRIM(standard_specification), ''), '') AS standard_specification,
                COUNT(*) AS cnt
            FROM instruction_plans
            WHERE {" AND ".join(conditions)}
            GROUP BY
                DATE(start_date),
                COALESCE(NULLIF(TRIM(material_name), ''), '(未設定)'),
                COALESCE(NULLIF(TRIM(material_manufacturer), ''), ''),
                COALESCE(NULLIF(TRIM(standard_specification), ''), '')
            ORDER BY eff_date, material_manufacturer ASC, material_name ASC, standard_specification ASC
        """)
        try:
            dr = await db.execute(daily_sql, params)
            drows = dr.mappings().fetchall()
        except Exception as e:
            msg = str(e).lower()
            if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
                raise HTTPException(
                    status_code=503,
                    detail="instruction_plans テーブルが存在しません。",
                ) from e
            logger.exception("material-requirements daily 集計失敗")
            raise HTTPException(status_code=500, detail="日別材料需要量の集計に失敗しました。") from e

        date_list: list[str] = []
        cur = d_start
        while cur <= d_end:
            date_list.append(cur.isoformat())
            cur = cur + timedelta(days=1)

        pivot: dict[tuple, dict[str, int]] = {}
        for r in drows:
            rd = dict(r)
            ed = rd.get("eff_date")
            if ed is None:
                continue
            if hasattr(ed, "isoformat"):
                ds = ed.isoformat()[:10]
            else:
                ds = str(ed)[:10]
            key = (
                rd.get("material_name"),
                rd.get("material_manufacturer"),
                rd.get("standard_specification"),
            )
            if key not in pivot:
                pivot[key] = {d: 0 for d in date_list}
            qv = _icount(rd.get("cnt"))
            if ds in pivot[key]:
                pivot[key][ds] += qv

        # 合計表にのみ存在する材料も日別表に行として出す（該当日が無ければ 0）
        for it in items:
            k = (it.get("material_name"), it.get("material_manufacturer"), it.get("standard_specification"))
            if k not in pivot:
                pivot[k] = {d: 0 for d in date_list}

        matrix_rows = []
        # pivot key (material_name, material_manufacturer, standard_specification) → 表示順: メーカー・材料名・規格 昇順
        for key in sorted(pivot.keys(), key=lambda k: (k[1] or "", k[0] or "", k[2] or "")):
            mn, mf, sp = key
            by_date = pivot[key]
            row_total = sum(by_date.values())
            matrix_rows.append(
                {
                    "material_name": mn,
                    "material_manufacturer": mf,
                    "standard_specification": sp,
                    "by_date": {d: by_date[d] for d in date_list},
                    "row_total": row_total,
                }
            )

        daily_matrix = {
            "dates": date_list,
            "rows": matrix_rows,
        }

    return {
        "success": True,
        "message": "OK",
        "data": {
            "items": items,
            "daily_matrix": daily_matrix,
            "summary": {
                "date_start": d_start.isoformat(),
                "date_end": d_end.isoformat(),
                "production_month_filter": production_month.strip() if production_month and production_month.strip() else None,
                "total_material_kinds": len(items),
                "total_piece_count": total_pieces,
                "effective_date_note": "start_date が設定されている行のみ対象。日別は DATE(start_date) ごとの材料別ロット件数（COUNT(*)）です。",
                "daily_matrix_omitted": daily_matrix_omitted,
                "daily_matrix_max_days": _DAY_MATRIX_MAX_DAYS,
            },
        },
    }


@router.get("/plan/batch/component-requirements-summary")
async def get_component_requirements_summary_from_instruction_plans(
    date_start: Optional[str] = Query(None, description="集計開始日 YYYY-MM-DD（DATE(start_date) で判定、start_date 未設定行は対象外）"),
    date_end: Optional[str] = Query(None, description="集計終了日 YYYY-MM-DD（含む）"),
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM（date_start/date_end 未指定時にその月の全日を期間として使用）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    instruction_plans と product_bom_lines から、部品（component_product_cd）所要量を集計する。
    - start_date が NULL の instruction_plans は対象外
    - 期間キー: DATE(instruction_plans.start_date)
    - 指標: SUM(actual_production_quantity * qty_per / base_quantity * (1 + scrap_rate/100))
    """
    d_start = _parse_date_ymd(date_start) if date_start else None
    d_end = _parse_date_ymd(date_end) if date_end else None

    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    if d_start is None:
                        d_start = date(y, m, 1)
                    if d_end is None:
                        if m == 12:
                            d_end = date(y, 12, 31)
                        else:
                            d_end = date(y, m + 1, 1) - timedelta(days=1)
        except (ValueError, IndexError):
            pass

    if d_start is None or d_end is None:
        today = datetime.utcnow().date()
        d_start = d_start or today.replace(day=1)
        d_end = d_end or today

    if d_start > d_end:
        raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

    conditions = [
        "start_date IS NOT NULL",
        "DATE(start_date) >= :d_start",
        "DATE(start_date) <= :d_end",
    ]
    params = {"d_start": d_start, "d_end": d_end}

    sql = text(f"""
        SELECT
            COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)') AS component_cd,
            COALESCE(NULLIF(TRIM(p.part_name), ''), '') AS component_name,
            COALESCE(NULLIF(TRIM(p.uom), ''), COALESCE(NULLIF(TRIM(l.uom), ''), '個')) AS component_uom,
            COUNT(DISTINCT ip.id) AS source_lot_count,
            SUM(
                COALESCE(ip.actual_production_quantity, 0)
                * COALESCE(l.qty_per, 0)
                / NULLIF(COALESCE(h.base_quantity, 1), 0)
                * (1 + COALESCE(l.scrap_rate, 0) / 100)
            ) AS required_qty
        FROM instruction_plans ip
        JOIN product_bom_headers h
          ON h.id = (
              SELECT h2.id
              FROM product_bom_headers h2
              WHERE h2.parent_product_cd = ip.product_cd
                AND h2.status = 'active'
                AND (h2.effective_from IS NULL OR h2.effective_from <= DATE(ip.start_date))
                AND (h2.effective_to IS NULL OR h2.effective_to >= DATE(ip.start_date))
              ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
              LIMIT 1
          )
        JOIN product_bom_lines l
          ON l.header_id = h.id
         AND l.component_product_cd IS NOT NULL
         AND TRIM(l.component_product_cd) <> ''
         AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
        LEFT JOIN parts p
          ON p.part_cd = l.component_product_cd
        WHERE {" AND ".join(conditions)}
        GROUP BY
            COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)'),
            COALESCE(NULLIF(TRIM(p.part_name), ''), ''),
            COALESCE(NULLIF(TRIM(p.uom), ''), COALESCE(NULLIF(TRIM(l.uom), ''), '個'))
        ORDER BY component_cd ASC
    """)

    try:
        result = await db.execute(sql, params)
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="instruction_plans テーブルが存在しません。",
            ) from e
        if "product_bom_headers" in msg or "product_bom_lines" in msg:
            raise HTTPException(
                status_code=503,
                detail="product_bom_headers / product_bom_lines テーブルが存在しないため集計できません。",
            ) from e
        logger.exception("component-requirements-summary 集計失敗")
        raise HTTPException(status_code=500, detail="部品需要量の集計に失敗しました。") from e

    def _fnum(v) -> float:
        if v is None:
            return 0.0
        if isinstance(v, Decimal):
            return float(v)
        return float(v)

    def _inum(v) -> int:
        if v is None:
            return 0
        if isinstance(v, Decimal):
            return int(v)
        return int(v)

    items = []
    total_required_qty = 0.0
    for r in rows:
        rd = dict(r)
        rq = _fnum(rd.get("required_qty"))
        total_required_qty += rq
        items.append(
            {
                "component_cd": rd.get("component_cd"),
                "component_name": rd.get("component_name"),
                "component_uom": rd.get("component_uom"),
                "source_lot_count": _inum(rd.get("source_lot_count")),
                "required_qty": round(rq, 6),
            }
        )

    # 日別×部品の二次元表（期間が長すぎると列数過多のため上限）
    _DAY_MATRIX_MAX_DAYS = 186
    span_days = (d_end - d_start).days + 1
    daily_matrix: Optional[dict] = None
    daily_matrix_omitted = span_days > _DAY_MATRIX_MAX_DAYS

    if not daily_matrix_omitted:
        dsql = text(f"""
            SELECT
                DATE(ip.start_date) AS eff_date,
                COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)') AS component_cd,
                COALESCE(NULLIF(TRIM(p.part_name), ''), '') AS component_name,
                COALESCE(NULLIF(TRIM(p.uom), ''), COALESCE(NULLIF(TRIM(l.uom), ''), '個')) AS component_uom,
                SUM(
                    COALESCE(ip.actual_production_quantity, 0)
                    * COALESCE(l.qty_per, 0)
                    / NULLIF(COALESCE(h.base_quantity, 1), 0)
                    * (1 + COALESCE(l.scrap_rate, 0) / 100)
                ) AS required_qty
            FROM instruction_plans ip
            JOIN product_bom_headers h
              ON h.id = (
                  SELECT h2.id
                  FROM product_bom_headers h2
                  WHERE h2.parent_product_cd = ip.product_cd
                    AND h2.status = 'active'
                    AND (h2.effective_from IS NULL OR h2.effective_from <= DATE(ip.start_date))
                    AND (h2.effective_to IS NULL OR h2.effective_to >= DATE(ip.start_date))
                  ORDER BY COALESCE(h2.effective_from, DATE('1900-01-01')) DESC, h2.id DESC
                  LIMIT 1
              )
            JOIN product_bom_lines l
              ON l.header_id = h.id
             AND l.component_product_cd IS NOT NULL
             AND TRIM(l.component_product_cd) <> ''
             AND COALESCE(NULLIF(TRIM(l.component_type), ''), 'material') <> 'material'
            LEFT JOIN parts p
              ON p.part_cd = l.component_product_cd
            WHERE {" AND ".join(conditions)}
            GROUP BY
                DATE(ip.start_date),
                COALESCE(NULLIF(TRIM(l.component_product_cd), ''), '(未設定)'),
                COALESCE(NULLIF(TRIM(p.part_name), ''), ''),
                COALESCE(NULLIF(TRIM(p.uom), ''), COALESCE(NULLIF(TRIM(l.uom), ''), '個'))
            ORDER BY
                DATE(ip.start_date) ASC,
                component_cd ASC
        """)
        dresult = await db.execute(dsql, params)
        drows = dresult.mappings().fetchall()

        date_list = [(d_start + timedelta(days=i)).isoformat() for i in range(span_days)]
        pivot: dict[tuple, dict[str, float]] = {}
        for r in drows:
            rd = dict(r)
            ed = rd.get("eff_date")
            if ed is None:
                continue
            if hasattr(ed, "isoformat"):
                ds = ed.isoformat()[:10]
            else:
                ds = str(ed)[:10]
            key = (
                rd.get("component_cd"),
                rd.get("component_name"),
                rd.get("component_uom"),
            )
            if key not in pivot:
                pivot[key] = {d: 0.0 for d in date_list}
            qv = _fnum(rd.get("required_qty"))
            if ds in pivot[key]:
                pivot[key][ds] += qv

        for it in items:
            k = (it.get("component_cd"), it.get("component_name"), it.get("component_uom"))
            if k not in pivot:
                pivot[k] = {d: 0.0 for d in date_list}

        matrix_rows = []
        for key in sorted(pivot.keys(), key=lambda k: (k[0] or "", k[1] or "", k[2] or "")):
            cc, cn, cu = key
            by_date = pivot[key]
            row_total = sum(by_date.values())
            matrix_rows.append(
                {
                    "component_cd": cc,
                    "component_name": cn,
                    "component_uom": cu,
                    "by_date": {d: round(by_date[d], 6) for d in date_list},
                    "row_total": round(row_total, 6),
                }
            )

        daily_matrix = {
            "dates": date_list,
            "rows": matrix_rows,
        }

    return {
        "success": True,
        "message": "OK",
        "data": {
            "items": items,
            "daily_matrix": daily_matrix,
            "summary": {
                "date_start": d_start.isoformat(),
                "date_end": d_end.isoformat(),
                "production_month_filter": production_month.strip() if production_month and production_month.strip() else None,
                "total_component_kinds": len(items),
                "total_required_qty": round(total_required_qty, 6),
                "effective_date_note": "start_date が設定されている instruction_plans を対象に、actual_production_quantity × BOM構成比（qty_per/base_quantity）× 歩留補正（1+scrap_rate）で集計しています。",
                "daily_matrix_omitted": daily_matrix_omitted,
                "daily_matrix_max_days": _DAY_MATRIX_MAX_DAYS,
            },
        },
    }


class UpdatePlanBody(BaseModel):
    """生産ロット（instruction_plans）1件の更新（テーブル全項目対応）"""
    production_month: Optional[str] = None  # YYYY-MM-DD
    production_line: Optional[str] = None
    priority_order: Optional[int] = None
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    planned_quantity: Optional[int] = None
    actual_production_quantity: Optional[int] = None
    lot_number: Optional[str] = None
    production_lot_size: Optional[int] = None
    material_name: Optional[str] = None
    material_manufacturer: Optional[str] = None
    standard_specification: Optional[str] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    is_cutting_instructed: Optional[int] = None  # 0/1
    has_chamfering_process: Optional[int] = None
    is_chamfering_instructed: Optional[int] = None
    has_sw_process: Optional[int] = None
    is_sw_instructed: Optional[int] = None
    management_code: Optional[str] = None
    take_count: Optional[int] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    scrap_length: Optional[float] = None
    use_material_stock_sub: Optional[int] = None  # 0/1
    usage_count: Optional[float] = None  # 1=1本, <1=按分


class CreatePlanBody(BaseModel):
    """新規ロット追加（instruction_plans 1件 INSERT）"""
    production_month: Optional[str] = None  # YYYY-MM
    production_line: Optional[str] = None
    priority_order: Optional[int] = None
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    material_name: Optional[str] = None
    material_manufacturer: Optional[str] = None
    standard_specification: Optional[str] = None
    planned_quantity: Optional[int] = None
    production_lot_size: Optional[int] = None
    lot_number: Optional[str] = None
    actual_production_quantity: Optional[int] = None
    take_count: Optional[int] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    scrap_length: Optional[float] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    has_chamfering_process: Optional[int] = None  # 0/1
    has_sw_process: Optional[int] = None  # 0/1
    use_material_stock_sub: Optional[int] = None  # 0/1
    usage_count: Optional[float] = None  # 1=1本, <1=按分


def _parse_date_ymd(s: Optional[str]):
    """Parse YYYY-MM-DD or YYYY-MM to date."""
    if s is None or len(str(s).strip()) < 7:
        return None
    try:
        parts = str(s).strip()[:10].replace("-", " ").split()
        if len(parts) >= 2:
            y, m = int(parts[0]), int(parts[1])
            d = int(parts[2]) if len(parts) >= 3 else 1
            if 1 <= m <= 12:
                return date(y, m, d)
    except (ValueError, IndexError):
        pass
    return None


def _parse_datetime_plan(s: Optional[str]):
    """Parse YYYY-MM-DD to datetime."""
    if s is None or len(str(s).strip()) < 10:
        return None
    try:
        parts = str(s).strip()[:10].split("-")
        if len(parts) == 3:
            return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


@router.post("/plan/batch/create")
async def create_instruction_plan(
    body: CreatePlanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """instruction_plans に1件新規追加。management_code はトリガーで自動設定。"""
    production_month = _parse_date_ymd(body.production_month)
    if not production_month:
        raise HTTPException(status_code=400, detail="production_month (YYYY-MM) を指定してください")
    product_cd = (body.product_cd or "").strip() or None
    product_name = (body.product_name or "").strip() or None
    if not product_cd or not product_name:
        raise HTTPException(status_code=400, detail="product_cd と product_name は必須です")
    production_line = (body.production_line or "").strip() or ""
    priority_order = body.priority_order if body.priority_order is not None else 0
    planned_quantity = body.planned_quantity if body.planned_quantity is not None else 0
    production_lot_size = body.production_lot_size if body.production_lot_size is not None else None
    lot_number = (body.lot_number or "").strip() or None
    actual_production_quantity = body.actual_production_quantity if body.actual_production_quantity is not None else 0
    take_count = body.take_count if body.take_count is not None else None
    cutting_length = body.cutting_length
    chamfering_length = body.chamfering_length
    developed_length = body.developed_length
    scrap_length = body.scrap_length
    material_name = (body.material_name or "").strip() or None
    material_manufacturer = (body.material_manufacturer or "").strip() or None
    standard_specification = (body.standard_specification or "").strip() or None
    start_date = _parse_datetime_plan(body.start_date)
    end_date = _parse_datetime_plan(body.end_date)
    has_chamfering_process = 1 if (body.has_chamfering_process == 1) else 0
    has_sw_process = 1 if (body.has_sw_process == 1) else 0

    use_material_stock_sub = 1 if getattr(body, "use_material_stock_sub", 0) == 1 else 0
    usage_count_val = getattr(body, "usage_count", None)
    if usage_count_val is None:
        usage_count_val = 1.0
    try:
        usage_count_val = float(usage_count_val)
    except (TypeError, ValueError):
        usage_count_val = 1.0
    if usage_count_val <= 0:
        usage_count_val = 1.0

    sql = text("""
        INSERT INTO instruction_plans (
            production_month, production_line, priority_order, product_cd, product_name,
            planned_quantity, start_date, end_date, production_lot_size, lot_number,
            is_cutting_instructed, has_chamfering_process, is_chamfering_instructed,
            has_sw_process, is_sw_instructed, actual_production_quantity,
            take_count, cutting_length, chamfering_length, developed_length, scrap_length,
            material_name, material_manufacturer, standard_specification,
            use_material_stock_sub, usage_count
        ) VALUES (
            :production_month, :production_line, :priority_order, :product_cd, :product_name,
            :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
            0, :has_chamfering_process, 0, :has_sw_process, 0, :actual_production_quantity,
            :take_count, :cutting_length, :chamfering_length, :developed_length, :scrap_length,
            :material_name, :material_manufacturer, :standard_specification,
            :use_material_stock_sub, :usage_count
        )
    """)
    params = {
        "production_month": production_month,
        "production_line": production_line,
        "priority_order": priority_order,
        "product_cd": product_cd,
        "product_name": product_name,
        "planned_quantity": planned_quantity,
        "start_date": start_date,
        "end_date": end_date,
        "production_lot_size": production_lot_size,
        "lot_number": lot_number,
        "actual_production_quantity": actual_production_quantity,
        "take_count": take_count,
        "cutting_length": cutting_length,
        "chamfering_length": chamfering_length,
        "developed_length": developed_length,
        "scrap_length": scrap_length,
        "material_name": material_name,
        "material_manufacturer": material_manufacturer,
        "standard_specification": standard_specification,
        "has_chamfering_process": has_chamfering_process,
        "has_sw_process": has_sw_process,
        "use_material_stock_sub": use_material_stock_sub,
        "usage_count": usage_count_val,
    }
    await db.execute(sql, params)
    await db.commit()
    return {"success": True, "message": "レコードを追加しました"}


@router.patch("/plan/batch/{plan_id}")
async def update_instruction_plan(
    plan_id: int,
    body: UpdatePlanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産ロット1件を更新。management_code は未送信時のみ再計算。"""
    updates = []
    params = {"plan_id": plan_id}

    def _parse_date(s: Optional[str]):
        if s is None or len(str(s).strip()) < 10:
            return None
        try:
            parts = str(s).strip()[:10].split("-")
            if len(parts) == 3:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass
        return None

    def _parse_datetime(s: Optional[str]):
        if s is None or len(str(s).strip()) < 10:
            return None
        try:
            parts = str(s).strip()[:10].split("-")
            if len(parts) == 3:
                return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass
        return None

    if body.production_month is not None:
        v = _parse_date(body.production_month)
        if v is not None:
            updates.append("production_month = :production_month")
            params["production_month"] = v
    if body.production_line is not None:
        updates.append("production_line = :production_line")
        params["production_line"] = body.production_line.strip() if body.production_line else ""
    if body.priority_order is not None:
        updates.append("priority_order = :priority_order")
        params["priority_order"] = body.priority_order
    if body.product_cd is not None:
        updates.append("product_cd = :product_cd")
        params["product_cd"] = body.product_cd.strip() if body.product_cd else ""
    if body.product_name is not None:
        updates.append("product_name = :product_name")
        params["product_name"] = body.product_name.strip() if body.product_name else ""
    if body.planned_quantity is not None:
        updates.append("planned_quantity = :planned_quantity")
        params["planned_quantity"] = body.planned_quantity
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = body.actual_production_quantity
    if body.lot_number is not None:
        updates.append("lot_number = :lot_number")
        params["lot_number"] = str(body.lot_number).strip() if body.lot_number else ""
    if body.production_lot_size is not None:
        updates.append("production_lot_size = :production_lot_size")
        params["production_lot_size"] = body.production_lot_size
    if body.material_name is not None:
        updates.append("material_name = :material_name")
        params["material_name"] = body.material_name.strip() if body.material_name else None
    if body.material_manufacturer is not None:
        updates.append("material_manufacturer = :material_manufacturer")
        params["material_manufacturer"] = body.material_manufacturer.strip() if body.material_manufacturer else None
    if body.standard_specification is not None:
        updates.append("standard_specification = :standard_specification")
        params["standard_specification"] = body.standard_specification.strip() if body.standard_specification else None
    if body.start_date is not None:
        v = _parse_datetime(body.start_date)
        if v is not None:
            updates.append("start_date = :start_date")
            params["start_date"] = v
    if body.end_date is not None:
        v = _parse_datetime(body.end_date)
        if v is not None:
            updates.append("end_date = :end_date")
            params["end_date"] = v
    if body.is_cutting_instructed is not None:
        updates.append("is_cutting_instructed = :is_cutting_instructed")
        params["is_cutting_instructed"] = 1 if body.is_cutting_instructed else 0
    if body.has_chamfering_process is not None:
        updates.append("has_chamfering_process = :has_chamfering_process")
        params["has_chamfering_process"] = 1 if body.has_chamfering_process else 0
    if body.is_chamfering_instructed is not None:
        updates.append("is_chamfering_instructed = :is_chamfering_instructed")
        params["is_chamfering_instructed"] = 1 if body.is_chamfering_instructed else 0
    if body.has_sw_process is not None:
        updates.append("has_sw_process = :has_sw_process")
        params["has_sw_process"] = 1 if body.has_sw_process else 0
    if body.is_sw_instructed is not None:
        updates.append("is_sw_instructed = :is_sw_instructed")
        params["is_sw_instructed"] = 1 if body.is_sw_instructed else 0
    if body.management_code is not None:
        updates.append("management_code = :management_code")
        params["management_code"] = body.management_code.strip() if body.management_code else None
    if body.take_count is not None:
        updates.append("take_count = :take_count")
        params["take_count"] = body.take_count
    if body.cutting_length is not None:
        updates.append("cutting_length = :cutting_length")
        params["cutting_length"] = body.cutting_length
    if body.chamfering_length is not None:
        updates.append("chamfering_length = :chamfering_length")
        params["chamfering_length"] = body.chamfering_length
    if body.developed_length is not None:
        updates.append("developed_length = :developed_length")
        params["developed_length"] = body.developed_length
    if body.scrap_length is not None:
        updates.append("scrap_length = :scrap_length")
        params["scrap_length"] = body.scrap_length
    if body.use_material_stock_sub is not None:
        updates.append("use_material_stock_sub = :use_material_stock_sub")
        params["use_material_stock_sub"] = 1 if body.use_material_stock_sub == 1 else 0
    if body.usage_count is not None:
        try:
            uc = float(body.usage_count)
            if uc > 0:
                updates.append("usage_count = :usage_count")
                params["usage_count"] = uc
        except (TypeError, ValueError):
            pass

    if not updates:
        return {"success": True, "message": "変更なし"}

    set_clause = ", ".join(updates)
    await db.execute(text(f"UPDATE instruction_plans SET {set_clause} WHERE id = :plan_id"), params)
    # management_code を送っていない場合のみ再計算
    if body.management_code is None:
        await db.execute(
            text("""
                UPDATE instruction_plans SET management_code = CONCAT(
                    RIGHT(YEAR(production_month), 2), LPAD(MONTH(production_month), 2, '0'),
                    COALESCE(product_cd, ''), RIGHT(COALESCE(production_line, ''), 2),
                    LPAD(COALESCE(priority_order, 0), 2, '0'), '-',
                    LPAD(COALESCE(production_lot_size, 0), 2, '0'), '-',
                    LPAD(COALESCE(lot_number, ''), 2, '0')
                ) WHERE id = :plan_id
            """),
            {"plan_id": plan_id},
        )
    await db.commit()
    return {"success": True, "message": "更新しました"}


@router.delete("/plan/batch/{plan_id}")
async def delete_instruction_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産ロット1件を削除（instruction_plans のみ。切断指示へ移行済みの場合は一覧に無いため対象外）。"""
    result = await db.execute(text("DELETE FROM instruction_plans WHERE id = :plan_id"), {"plan_id": plan_id})
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="該当するロットがありません")
    return {"success": True, "message": "削除しました"}


@router.get("/plan/cutting-management/list")
async def get_cutting_management_list(
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    production_line: Optional[str] = Query(None, description="ライン（部分一致）"),
    cutting_machine: Optional[str] = Query(None, description="切断機（完全一致でフィルタ）"),
    limit: int = Query(2000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    切断指示一覧: cutting_management を取得。
    並び: 生産日 → 切断機 → 生産順（同一天同一设备内で 1,2,3... の順）。
    """
    conditions = ["1=1"]
    params = {"limit": limit}
    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    params["production_month"] = date(y, m, 1)
                    conditions.append("production_month = :production_month")
        except (ValueError, IndexError):
            pass
    if production_day and production_day.strip():
        try:
            parts = production_day.strip().split("-")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                params["production_day"] = date(y, m, d)
                conditions.append("production_day = :production_day")
        except (ValueError, IndexError):
            pass
    if production_line and production_line.strip():
        conditions.append("production_line LIKE :production_line")
        params["production_line"] = f"%{production_line.strip()}%"
    if cutting_machine is not None and cutting_machine.strip():
        conditions.append("cutting_machine = :cutting_machine")
        params["cutting_machine"] = cutting_machine.strip()

    # WHERE は修飾なし（cutting_management のみ該当列を持つため曖昧でない）。:param の誤置換を防ぐ
    where_clause = " AND ".join(conditions)
    # 生産時間を実時計算: product_cd + 切断機(cutting_machine)=machines_name で equipment_efficiency を結合し efficiency_rate を取得、生産数/能率
    sql = text(f"""
        SELECT `cutting_management`.id, `cutting_management`.production_month, `cutting_management`.production_day,
               `cutting_management`.production_line, `cutting_management`.cutting_machine, `cutting_management`.production_sequence,
               `cutting_management`.priority_order, `cutting_management`.product_cd, `cutting_management`.product_name,
               `cutting_management`.planned_quantity, `cutting_management`.start_date, `cutting_management`.end_date,
               `cutting_management`.production_lot_size, `cutting_management`.lot_number,
               `cutting_management`.is_cutting_instructed, `cutting_management`.has_chamfering_process,
               `cutting_management`.is_chamfering_instructed, `cutting_management`.has_sw_process, `cutting_management`.is_sw_instructed,
               `cutting_management`.management_code, `cutting_management`.actual_production_quantity, `cutting_management`.defect_qty, `cutting_management`.take_count,
               `cutting_management`.cutting_length, `cutting_management`.chamfering_length, `cutting_management`.developed_length,
               `cutting_management`.scrap_length, `cutting_management`.material_name, `cutting_management`.material_manufacturer,
               `cutting_management`.standard_specification, `cutting_management`.production_completed_check, `cutting_management`.material_usage_reflected,
               `cutting_management`.use_material_stock_sub, `cutting_management`.usage_count,
               `cutting_management`.cd,
               `cutting_management`.created_at, `cutting_management`.updated_at, `cutting_management`.remarks,
               `equipment_efficiency`.efficiency_rate AS efficiency_rate
        FROM `cutting_management`
        LEFT JOIN `equipment_efficiency`
          ON `cutting_management`.product_cd = `equipment_efficiency`.product_cd
         AND `cutting_management`.cutting_machine = `equipment_efficiency`.machines_name
        WHERE {where_clause}
        ORDER BY `cutting_management`.production_day ASC, `cutting_management`.cutting_machine ASC, `cutting_management`.production_sequence ASC
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, params)
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "cutting_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="cutting_management テーブルが存在しません。マイグレーション 053_cutting_management.sql を実行してください。",
            ) from e
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e), "message": "切断指示一覧の取得に失敗しました"},
        )

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()[:19] if val else default
        return val

    def _v_date(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if hasattr(val, "isoformat"):
            return val.isoformat()[:10] if val else default
        return str(val)[:10] if val else default

    def _cm_row(r):
        row = dict(r)
        # 生産時間 = 生産数 / efficiency_rate（equipment_efficiency を product_cd・切断機=machines_name で結合）
        qty = row.get("actual_production_quantity")
        rate = row.get("efficiency_rate")
        if qty is not None and rate is not None:
            try:
                q = float(qty) if not isinstance(qty, (int, float)) else qty
                r = float(rate) if not isinstance(rate, (int, float)) else rate
                production_time = round(q / r, 1) if r > 0 else None
            except (TypeError, ValueError):
                production_time = None
        else:
            production_time = None
        return {
            "id": row.get("id"),
            "production_month": _v_date(row, "production_month"),
            "production_day": _v_date(row, "production_day"),
            "production_line": row.get("production_line"),
            "cutting_machine": row.get("cutting_machine"),
            "production_sequence": row.get("production_sequence"),
            "priority_order": row.get("priority_order"),
            "product_cd": row.get("product_cd"),
            "product_name": row.get("product_name"),
            "planned_quantity": row.get("planned_quantity"),
            "start_date": _v(row, "start_date"),
            "end_date": _v(row, "end_date"),
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": row.get("lot_number"),
            "is_cutting_instructed": row.get("is_cutting_instructed"),
            "has_chamfering_process": row.get("has_chamfering_process"),
            "is_chamfering_instructed": row.get("is_chamfering_instructed"),
            "has_sw_process": row.get("has_sw_process"),
            "is_sw_instructed": row.get("is_sw_instructed"),
            "management_code": row.get("management_code"),
            "actual_production_quantity": row.get("actual_production_quantity"),
            "defect_qty": row.get("defect_qty"),
            "take_count": row.get("take_count"),
            "cutting_length": _v(row, "cutting_length"),
            "chamfering_length": _v(row, "chamfering_length"),
            "developed_length": _v(row, "developed_length"),
            "scrap_length": _v(row, "scrap_length"),
            "material_name": row.get("material_name"),
            "material_manufacturer": row.get("material_manufacturer"),
            "standard_specification": row.get("standard_specification"),
            "production_completed_check": row.get("production_completed_check"),
            "material_usage_reflected": row.get("material_usage_reflected") or "未反映",
            "use_material_stock_sub": row.get("use_material_stock_sub"),
            "usage_count": _v(row, "usage_count", 1),
            "cd": row.get("cd"),
            "created_at": _v(row, "created_at"),
            "updated_at": _v(row, "updated_at"),
            "remarks": row.get("remarks"),
            "production_time": production_time,
        }

    try:
        data = [_cm_row(dict(r)) for r in rows]
        return {"success": True, "data": data, "message": "OK"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e), "message": "切断指示一覧の取得に失敗しました"},
        )


@router.post("/plan/cutting-management/confirm-actual")
async def confirm_cutting_actual(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    cutting_machine: Optional[str] = Query(None, description="切断機（省略時は全機）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    切断指示-今日の「実績確定」: production_completed_check=1 の cutting_management を
    stock_transaction_logs に保存する。去重复：同一生産日（および同一切断機フィルタ）の
    既存 cutting_management 実績を先に削除してから挿入する（先删除再插入）。
    """
    try:
        parts = production_day.strip().split("-")
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="production_day は YYYY-MM-DD で指定してください")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        prod_day = date(y, m, d)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="production_day の形式が不正です") from e

    # 去重复：同一範囲の既存実績を削除（source_file=cutting_management & 同日 & 同一切断機なら削除）
    del_params: dict = {"production_day": prod_day}
    del_conditions = [
        "source_file = 'cutting_management'",
        "DATE(transaction_time) = :production_day",
    ]
    if cutting_machine and cutting_machine.strip():
        del_conditions.append("machine_cd = :cutting_machine")
        del_params["cutting_machine"] = cutting_machine.strip()
    del_sql = text("DELETE FROM stock_transaction_logs WHERE " + " AND ".join(del_conditions))
    await db.execute(del_sql, del_params)

    conditions = ["production_day = :production_day", "production_completed_check = 1"]
    params: dict = {"production_day": prod_day}
    if cutting_machine and cutting_machine.strip():
        conditions.append("cutting_machine = :cutting_machine")
        params["cutting_machine"] = cutting_machine.strip()
    sel = text("""
        SELECT id, product_cd, management_code, cutting_machine, actual_production_quantity, defect_qty, production_day
        FROM cutting_management
        WHERE """ + " AND ".join(conditions))
    res = await db.execute(sel, params)
    rows = res.mappings().fetchall()
    if not rows:
        await db.commit()
        return {"success": True, "message": "対象データがありません（既存分は削除済み）", "inserted": 0, "total_quantity": 0, "deleted": True}
    # transaction_time: date → datetime (00:00:00)
    ins = text("""
        INSERT INTO stock_transaction_logs (
            stock_type, transaction_type, target_cd, location_cd, lot_no, process_cd, machine_cd,
            quantity, unit, transaction_time, source_file
        ) VALUES (
            '仕掛品', :transaction_type, :target_cd, '工程中間在庫', :lot_no, 'KT01', :machine_cd,
            :quantity, '本', :transaction_time, 'cutting_management'
        )
    """)
    inserted = 0
    total_quantity = 0
    for row in rows:
        r = dict(row)
        product_cd = (r.get("product_cd") or "").strip()
        if not product_cd:
            continue
        prod_day_val = r.get("production_day")
        if hasattr(prod_day_val, "isoformat"):
            tx_time = datetime.combine(prod_day_val, datetime.min.time()) if prod_day_val else datetime.now()
        else:
            tx_time = datetime.now()
        qty = r.get("actual_production_quantity")
        if qty is None:
            qty = 0
        # 良品：transaction_type='実績'
        await db.execute(ins, {
            "target_cd": product_cd,
            "lot_no": r.get("management_code"),
            "machine_cd": r.get("cutting_machine"),
            "quantity": qty,
            "transaction_time": tx_time,
            "transaction_type": "実績",
        })
        inserted += 1
        total_quantity += int(qty)
        # 不良数：transaction_type='不良'
        defect_qty = r.get("defect_qty")
        if defect_qty is not None and int(defect_qty) > 0:
            await db.execute(ins, {
                "target_cd": product_cd,
                "lot_no": r.get("management_code"),
                "machine_cd": r.get("cutting_machine"),
                "quantity": int(defect_qty),
                "transaction_time": tx_time,
                "transaction_type": "不良",
            })
            inserted += 1
    await db.commit()
    return {
        "success": True,
        "message": f"実績を {inserted} 件登録しました",
        "inserted": inserted,
        "total_quantity": total_quantity,
    }


class MoveBatchToCuttingBody(BaseModel):
    """生産ロット1件を切断指示へ移行するリクエスト"""
    plan_id: int
    production_month: str  # YYYY-MM
    production_line: str
    product_cd: str
    product_name: str
    actual_production_quantity: Optional[int] = 0
    material_name: Optional[str] = None
    management_code: Optional[str] = None
    production_day: Optional[str] = None  # 生成日（手動指定）YYYY-MM-DD、未指定時は今日
    start_date: Optional[str] = None  # 旧パラメータ・production_day の別名
    priority_order: Optional[int] = None  # → production_order（ロット側順位）
    cutting_machine: str = ""  # 切断機（手動指定）
    has_chamfering_process: Optional[bool] = False  # 面取工程ありなら面取指示へ自動登録


@router.post("/plan/cutting-management/move-from-batch")
async def move_batch_to_cutting_management(
    body: MoveBatchToCuttingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    生産ロット（instruction_plans）1件を切断指示（cutting_management）へ移行する。
    - cutting_management に INSERT
    - has_chamfering_process が True なら chamfering_plans（面取ロット一覧）に自動 INSERT
    - 第一工程のため kanban_issuance に status=pending で1件 INSERT（後で手動発行）
    - instruction_plans から該当 id を DELETE
    """
    try:
        parts = body.production_month.strip().split("-")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="production_month は YYYY-MM 形式で指定してください")
        y, m = int(parts[0]), int(parts[1])
        if not (1 <= m <= 12):
            raise ValueError("month")
        production_month_date = date(y, m, 1)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="production_month の形式が不正です") from e

    # 生成日（手動指定）: production_day または start_date、未指定時は今日
    day_str = (body.production_day or body.start_date or "").strip()[:10]
    if day_str and len(day_str) == 10:
        try:
            parts = day_str.split("-")
            if len(parts) == 3:
                production_day_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                production_day_date = date.today()
        except (ValueError, IndexError):
            production_day_date = date.today()
    else:
        production_day_date = date.today()

    cutting_machine = (body.cutting_machine or "").strip()
    if not cutting_machine:
        raise HTTPException(status_code=400, detail="切断機を指定してください")

    has_chamfering = bool(body.has_chamfering_process)

    # ロット（instruction_plans）1件を取得し、cutting_management に全項目コピー
    plan_res = await db.execute(
        text("""
            SELECT production_month, production_line, priority_order, product_cd, product_name,
                   planned_quantity, start_date, end_date, production_lot_size, lot_number,
                   is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
                   management_code, actual_production_quantity, take_count, cutting_length, chamfering_length,
                   developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
                   use_material_stock_sub, usage_count
            FROM instruction_plans WHERE id = :plan_id
        """),
        {"plan_id": body.plan_id},
    )
    plan_row = plan_res.mappings().fetchone()
    if not plan_row:
        raise HTTPException(status_code=404, detail="指定のロットが見つかりません")

    plan = dict(plan_row)
    production_line = (plan.get("production_line") or body.production_line or "").strip() or ""
    product_cd = (plan.get("product_cd") or body.product_cd or "").strip() or ""
    product_name = (plan.get("product_name") or body.product_name or "").strip() or ""
    if not product_cd or not product_name:
        raise HTTPException(status_code=400, detail="product_cd と product_name は必須です")
    if not production_line:
        raise HTTPException(status_code=400, detail="production_line は必須です")

    # 同一切断機内の次 生産順（自動採番）
    order_res = await db.execute(
        text("SELECT COALESCE(MAX(production_sequence), 0) + 1 AS next_order FROM cutting_management WHERE cutting_machine = :cm"),
        {"cm": cutting_machine},
    )
    order_row = order_res.mappings().fetchone()
    production_sequence = int(order_row["next_order"]) if order_row and order_row.get("next_order") is not None else 1

    insert_cutting_sql = text("""
        INSERT INTO cutting_management (
            production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
            product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
            is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
            management_code, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length, developed_length, scrap_length,
            material_name, material_manufacturer, standard_specification, production_completed_check,
            use_material_stock_sub, usage_count
        ) VALUES (
            :production_month, :production_day, :production_line, :cutting_machine, :production_sequence, :priority_order,
            :product_cd, :product_name, :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
            :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
            :management_code, :actual_production_quantity, 0, :take_count, :cutting_length, :chamfering_length, :developed_length, :scrap_length,
            :material_name, :material_manufacturer, :standard_specification, 0,
            :use_material_stock_sub, :usage_count
        )
    """)
    def _to_date(v):
        if v is None:
            return None
        try:
            s = str(v).strip()[:10]
            if len(s) == 10:
                return datetime(int(s[:4]), int(s[5:7]), int(s[8:10]))
        except (ValueError, IndexError):
            pass
        return None

    cutting_params = {
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": production_line,
        "cutting_machine": cutting_machine,
        "production_sequence": production_sequence,
        "priority_order": plan.get("priority_order"),
        "product_cd": product_cd,
        "product_name": product_name,
        "planned_quantity": plan.get("planned_quantity"),
        "start_date": _to_date(plan.get("start_date")),
        "end_date": _to_date(plan.get("end_date")),
        "production_lot_size": plan.get("production_lot_size"),
        "lot_number": (plan.get("lot_number") or "").strip() or None,
        "is_cutting_instructed": 1 if plan.get("is_cutting_instructed") else 0,
        "has_chamfering_process": 1 if plan.get("has_chamfering_process") else 0,
        "is_chamfering_instructed": 1 if plan.get("is_chamfering_instructed") else 0,
        "has_sw_process": 1 if plan.get("has_sw_process") else 0,
        "is_sw_instructed": 1 if plan.get("is_sw_instructed") else 0,
        "management_code": (plan.get("management_code") or "").strip() or None,
        "actual_production_quantity": plan.get("actual_production_quantity") if plan.get("actual_production_quantity") is not None else 0,
        "take_count": plan.get("take_count"),
        "cutting_length": float(plan["cutting_length"]) if plan.get("cutting_length") is not None else None,
        "chamfering_length": float(plan["chamfering_length"]) if plan.get("chamfering_length") is not None else None,
        "developed_length": float(plan["developed_length"]) if plan.get("developed_length") is not None else None,
        "scrap_length": float(plan["scrap_length"]) if plan.get("scrap_length") is not None else None,
        "material_name": (plan.get("material_name") or "").strip() or None,
        "material_manufacturer": (plan.get("material_manufacturer") or "").strip() or None,
        "standard_specification": (plan.get("standard_specification") or "").strip() or None,
        "use_material_stock_sub": 1 if plan.get("use_material_stock_sub") == 1 else 0,
        "usage_count": float(plan["usage_count"]) if plan.get("usage_count") is not None else 1.0,
    }

    try:
        await db.execute(insert_cutting_sql, cutting_params)
        # 新規 cutting_management.id 取得
        rid = await db.execute(text("SELECT LAST_INSERT_ID() AS id"))
        row = rid.mappings().fetchone()
        cutting_id = row.get("id") if row else None
        if not cutting_id:
            await db.rollback()
            raise HTTPException(status_code=500, detail="切断指示の登録に失敗しました")
        cutting_id = int(cutting_id)

        if has_chamfering:
            ins_cham = text("""
                INSERT INTO chamfering_plans (
                    cutting_management_id, production_month, production_day, production_line, production_order,
                    product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
                    cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
                ) VALUES (
                    :cutting_management_id, :production_month, :production_day, :production_line, :production_order,
                    :product_cd, :product_name, :actual_production_quantity, :production_lot_size, :lot_number,
                    :cutting_length, :chamfering_length, :developed_length, :material_name, :management_code, :has_sw_process
                )
            """)
            await db.execute(ins_cham, {
                "cutting_management_id": cutting_id,
                "production_month": production_month_date,
                "production_day": production_day_date,
                "production_line": production_line,
                "production_order": cutting_params["priority_order"],
                "product_cd": product_cd,
                "product_name": product_name,
                "actual_production_quantity": cutting_params["actual_production_quantity"],
                "production_lot_size": cutting_params.get("production_lot_size"),
                "lot_number": cutting_params.get("lot_number"),
                "cutting_length": cutting_params.get("cutting_length"),
                "chamfering_length": cutting_params.get("chamfering_length"),
                "developed_length": cutting_params.get("developed_length"),
                "material_name": cutting_params["material_name"],
                "management_code": cutting_params["management_code"],
                "has_sw_process": 1 if cutting_params.get("has_sw_process") else 0,
            })

        # 第一工程のカンバン：待発行で1件登録（手動発行用）。切断現品票に必要な全フィールドを保存する
        ins_kanban = text("""
            INSERT INTO kanban_issuance (
                process_type, source_id, kanban_no, issue_date, status,
                product_cd, product_name, production_line, cutting_machine,
                material_name, standard_specification, management_code,
                start_date, end_date, planned_quantity, production_lot_size,
                actual_production_quantity, take_count,
                cutting_length, chamfering_length, developed_length,
                has_chamfering_process, lot_number, production_day
            ) VALUES (
                'cutting', :source_id, NULL, NULL, 'pending',
                :product_cd, :product_name, :production_line, :cutting_machine,
                :material_name, :standard_specification, :management_code,
                :start_date, :end_date, :planned_quantity, :production_lot_size,
                :actual_production_quantity, :take_count,
                :cutting_length, :chamfering_length, :developed_length,
                :has_chamfering_process, :lot_number, :production_day
            )
        """)
        await db.execute(ins_kanban, {
            "source_id": cutting_id,
            "product_cd": cutting_params["product_cd"],
            "product_name": cutting_params["product_name"],
            "production_line": cutting_params["production_line"],
            "cutting_machine": cutting_params["cutting_machine"],
            "material_name": cutting_params["material_name"],
            "standard_specification": cutting_params["standard_specification"],
            "management_code": cutting_params["management_code"],
            "start_date": cutting_params["start_date"].date() if isinstance(cutting_params.get("start_date"), datetime) else cutting_params.get("start_date"),
            "end_date": cutting_params["end_date"].date() if isinstance(cutting_params.get("end_date"), datetime) else cutting_params.get("end_date"),
            "planned_quantity": cutting_params["planned_quantity"],
            "production_lot_size": cutting_params["production_lot_size"],
            "actual_production_quantity": cutting_params["actual_production_quantity"],
            "take_count": cutting_params["take_count"],
            "cutting_length": cutting_params["cutting_length"],
            "chamfering_length": cutting_params["chamfering_length"],
            "developed_length": cutting_params["developed_length"],
            "has_chamfering_process": 1 if cutting_params.get("has_chamfering_process") else 0,
            "lot_number": cutting_params["lot_number"],
            "production_day": production_day_date.date() if isinstance(production_day_date, datetime) else production_day_date,
        })

        await db.execute(text("DELETE FROM instruction_plans WHERE id = :plan_id"), {"plan_id": body.plan_id})
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        msg = str(e).lower()
        if "cutting_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="cutting_management テーブルが存在しません。マイグレーション 053_cutting_management.sql を実行してください。",
            ) from e
        if "chamfering_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="chamfering_management テーブルが存在しません。") from e
        if "chamfering_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="chamfering_plans テーブルが存在しません。マイグレーション 063_chamfering_batch.sql を実行してください。") from e
        if "kanban_issuance" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="kanban_issuance テーブルが存在しません。") from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"success": True, "message": "切断指示に登録し、ロットから削除しました"}


class MoveCuttingToBatchBody(BaseModel):
    """切断指示1件を生産ロットへ戻すリクエスト"""
    cutting_id: int
    production_month: str  # YYYY-MM
    production_line: str
    product_cd: str
    product_name: str
    actual_production_quantity: Optional[int] = 0
    material_name: Optional[str] = None
    management_code: Optional[str] = None
    production_day: Optional[str] = None  # YYYY-MM-DD → start_date/end_date
    production_order: Optional[int] = None  # → priority_order


@router.post("/plan/batch/move-from-cutting")
async def move_cutting_to_batch(
    body: MoveCuttingToBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    切断指示1件を生産ロットへ戻す。
    処理順: ①切断指示を読取 ②カンバン発行削除 ③面取指示削除 ④面取ロット一覧（chamfering_plans）削除 ⑤切断指示削除 ⑥instruction_plans に INSERT。
    """
    # ① 切断指示1件を取得（削除前に全項目コピー用。cutting_machine/production_day は削除後の生産順リナンバ用）
    cut_sel = text("""
        SELECT production_month, production_line, priority_order, product_cd, product_name,
               planned_quantity, start_date, end_date, production_lot_size, lot_number,
               is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
               management_code, actual_production_quantity, take_count, cutting_length, chamfering_length,
               developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
               use_material_stock_sub, usage_count,
               cutting_machine, production_day
        FROM cutting_management WHERE id = :cid
    """)
    cut_res = await db.execute(cut_sel, {"cid": body.cutting_id})
    cut_row = cut_res.mappings().fetchone()
    if not cut_row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    cut = dict(cut_row)

    def _to_dt(v):
        if v is None:
            return None
        try:
            s = str(v).strip()[:19]
            if len(s) >= 10:
                parts = s[:10].split("-")
                if len(parts) == 3:
                    return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass
        return None

    def _to_float(v):
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    insert_sql = text("""
        INSERT INTO instruction_plans (
            production_month, production_line, priority_order, product_cd, product_name,
            planned_quantity, start_date, end_date, production_lot_size, lot_number,
            is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
            management_code, actual_production_quantity, take_count, cutting_length, chamfering_length, developed_length, scrap_length,
            material_name, material_manufacturer, standard_specification,
            use_material_stock_sub, usage_count
        ) VALUES (
            :production_month, :production_line, :priority_order, :product_cd, :product_name,
            :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
            :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
            :management_code, :actual_production_quantity, :take_count, :cutting_length, :chamfering_length, :developed_length, :scrap_length,
            :material_name, :material_manufacturer, :standard_specification,
            :use_material_stock_sub, :usage_count
        )
    """)
    pm = cut.get("production_month")
    production_month_date = pm if isinstance(pm, date) else date.fromisoformat(str(pm)[:10]) if pm and len(str(pm)) >= 10 else date.today()
    insert_params = {
        "production_month": production_month_date,
        "production_line": (cut.get("production_line") or "").strip() or "",
        "priority_order": cut.get("priority_order"),
        "product_cd": (cut.get("product_cd") or "").strip() or "",
        "product_name": (cut.get("product_name") or "").strip() or "",
        "planned_quantity": cut.get("planned_quantity"),
        "start_date": _to_dt(cut.get("start_date")),
        "end_date": _to_dt(cut.get("end_date")),
        "production_lot_size": cut.get("production_lot_size"),
        "lot_number": (cut.get("lot_number") or "").strip() or None,
        "is_cutting_instructed": 1 if cut.get("is_cutting_instructed") else 0,
        "has_chamfering_process": 1 if cut.get("has_chamfering_process") else 0,
        "is_chamfering_instructed": 1 if cut.get("is_chamfering_instructed") else 0,
        "has_sw_process": 1 if cut.get("has_sw_process") else 0,
        "is_sw_instructed": 1 if cut.get("is_sw_instructed") else 0,
        "management_code": (cut.get("management_code") or "").strip() or None,
        "actual_production_quantity": cut.get("actual_production_quantity") if cut.get("actual_production_quantity") is not None else 0,
        "take_count": cut.get("take_count"),
        "cutting_length": _to_float(cut.get("cutting_length")),
        "chamfering_length": _to_float(cut.get("chamfering_length")),
        "developed_length": _to_float(cut.get("developed_length")),
        "scrap_length": _to_float(cut.get("scrap_length")),
        "material_name": (cut.get("material_name") or "").strip() or None,
        "material_manufacturer": (cut.get("material_manufacturer") or "").strip() or None,
        "standard_specification": (cut.get("standard_specification") or "").strip() or None,
        "use_material_stock_sub": 1 if cut.get("use_material_stock_sub") == 1 else 0,
        "usage_count": _to_float(cut.get("usage_count")) if cut.get("usage_count") is not None else 1.0,
    }

    try:
        # ② この切断に紐づく面取指示IDを取得（カンバン削除用）
        chamfering_res = await db.execute(
            text("SELECT id FROM chamfering_management WHERE cutting_management_id = :cid"),
            {"cid": body.cutting_id},
        )
        chamfering_ids = [r[0] for r in chamfering_res.fetchall() if r[0] is not None]

        # ③ カンバン発行を削除（切断由来 + 面取由来）
        await db.execute(
            text("DELETE FROM kanban_issuance WHERE process_type = 'cutting' AND source_id = :cid"),
            {"cid": body.cutting_id},
        )
        for chamfering_id in chamfering_ids:
            await db.execute(
                text("DELETE FROM kanban_issuance WHERE process_type = 'chamfering' AND source_id = :sid"),
                {"sid": chamfering_id},
            )

        # ④ 面取指示を削除
        await db.execute(
            text("DELETE FROM chamfering_management WHERE cutting_management_id = :cid"),
            {"cid": body.cutting_id},
        )

        # ④' 面取ロット一覧（chamfering_plans）の該当データを削除
        await db.execute(
            text("DELETE FROM chamfering_plans WHERE cutting_management_id = :cid"),
            {"cid": body.cutting_id},
        )

        # ⑤ 切断指示を削除
        await db.execute(text("DELETE FROM cutting_management WHERE id = :cid"), {"cid": body.cutting_id})

        # ⑤' 同一切断機・同一生産日の残り行の生産順を 1,2,3... にリナンバ
        cm = (cut.get("cutting_machine") or "").strip()
        pd = cut.get("production_day")
        if cm and pd is not None:
            pd_str = str(pd)[:10] if pd else None
            if pd_str:
                remain = await db.execute(
                    text("""
                        SELECT id FROM cutting_management
                        WHERE cutting_machine = :cm AND production_day = :pd
                        ORDER BY production_sequence ASC, id ASC
                    """),
                    {"cm": cm, "pd": pd_str},
                )
                remain_ids = [r[0] for r in remain.fetchall() if r[0] is not None]
                for seq, rid in enumerate(remain_ids, start=1):
                    await db.execute(
                        text("UPDATE cutting_management SET production_sequence = :seq WHERE id = :id"),
                        {"seq": seq, "id": rid},
                    )

        # ⑥ 生産ロットへ挿入（cutting の全共通項目をコピー）
        await db.execute(insert_sql, insert_params)

        # ⑥' 追加情報を補完
        # - APS ロットとの紐付けを復元（aps_batch_plan_id）
        # - 「切断→ロット戻し」を撤回イベントとして記録（release_cancelled_*）
        ins_id_res = await db.execute(text("SELECT LAST_INSERT_ID() AS id"))
        ins_id_row = ins_id_res.mappings().fetchone()
        ins_id = int(ins_id_row["id"]) if ins_id_row and ins_id_row.get("id") is not None else None
        if ins_id is not None:
            lot_no = (insert_params.get("lot_number") or "").strip() if insert_params.get("lot_number") else ""
            pcd = (insert_params.get("product_cd") or "").strip()
            pline = (insert_params.get("production_line") or "").strip()

            aps_batch_plan_id = None
            if lot_no and pcd:
                aps_q = await db.execute(
                    text(
                        "SELECT id FROM aps_batch_plans "
                        "WHERE lot_number = :lot_no AND product_cd = :pcd "
                        "AND (:pline = '' OR production_line = :pline) "
                        "ORDER BY id DESC LIMIT 1"
                    ),
                    {"lot_no": lot_no, "pcd": pcd, "pline": pline},
                )
                aps_batch_plan_id = aps_q.scalar()

            if aps_batch_plan_id is not None:
                await db.execute(
                    text("UPDATE instruction_plans SET aps_batch_plan_id = :bid WHERE id = :iid"),
                    {"bid": int(aps_batch_plan_id), "iid": ins_id},
                )

            rollback_by = (
                (getattr(current_user, "user_cd", None) or "")
                or (getattr(current_user, "username", None) or "")
                or (getattr(current_user, "name", None) or "")
                or "system"
            )
            try:
                await db.execute(
                    text(
                        "UPDATE instruction_plans SET "
                        "release_cancelled_at = :ts, "
                        "release_cancel_reason = :reason, "
                        "release_cancel_by = :rb "
                        "WHERE id = :iid"
                    ),
                    {
                        "ts": datetime.now(),
                        "reason": "cutting_management から instruction_plans へ戻し",
                        "rb": str(rollback_by)[:64],
                        "iid": ins_id,
                    },
                )
            except Exception:
                # 旧スキーマ（103 未適用）では列が存在しないためスキップ
                pass

        await db.commit()
    except Exception as e:
        await db.rollback()
        msg = str(e).lower()
        if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="instruction_plans テーブルが存在しません。") from e
        if "cutting_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(status_code=503, detail="cutting_management テーブルが存在しません。") from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"success": True, "message": "生産ロットに戻しました（切断・面取・カンバンを削除済み）"}


class ReorderCuttingBody(BaseModel):
    """切断指示の生成順を変更するリクエスト（同一切断機内）"""
    cutting_machine: str
    ordered_ids: list[int]  # この順に production_sequence を 1,2,3,... で更新（最小1）


@router.post("/plan/cutting-management/reorder")
async def reorder_cutting_management(
    body: ReorderCuttingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    切断指示の生産順（production_sequence）を、同一切断機内で指定した ID 順に更新する。
    """
    cutting_machine = (body.cutting_machine or "").strip()
    if not cutting_machine:
        raise HTTPException(status_code=400, detail="切断機を指定してください")
    if not body.ordered_ids:
        return {"success": True, "message": "変更なし"}

    try:
        for idx, row_id in enumerate(body.ordered_ids):
            await db.execute(
                text("""
                    UPDATE cutting_management
                    SET production_sequence = :production_sequence
                    WHERE id = :id AND cutting_machine = :cutting_machine
                """),
                {"production_sequence": idx + 1, "id": row_id, "cutting_machine": cutting_machine},
            )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "生成順を更新しました"}


class UpdateCuttingManagementBody(BaseModel):
    """切断指示1件の部分更新（完了切替・編集用）"""
    production_day: Optional[str] = None  # YYYY-MM-DD
    cutting_machine: Optional[str] = None
    actual_production_quantity: Optional[int] = None
    production_sequence: Optional[int] = None
    production_completed_check: Optional[bool] = None
    remarks: Optional[str] = None
    defect_qty: Optional[int] = None
    use_material_stock_sub: Optional[int] = None  # 0/1
    usage_count: Optional[float] = None  # 1=1本, <1=按分


@router.patch("/plan/cutting-management/{cutting_id}")
async def update_cutting_management(
    cutting_id: int,
    body: UpdateCuttingManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """切断指示1件を更新（切断機・生産数・生産順・完了・備考）。"""
    updates: list[str] = []
    params: dict = {"cid": cutting_id}
    if body.production_day is not None:
        _pd = body.production_day.strip()[:10] if body.production_day and len(body.production_day.strip()) >= 10 else None
        if _pd:
            try:
                parts = _pd.split("-")
                if len(parts) == 3:
                    params["production_day"] = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    updates.append("production_day = :production_day")
            except (ValueError, IndexError):
                pass
    if body.cutting_machine is not None:
        updates.append("cutting_machine = :cutting_machine")
        params["cutting_machine"] = (body.cutting_machine or "").strip() or None
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = body.actual_production_quantity
    if body.production_sequence is not None:
        updates.append("production_sequence = :production_sequence")
        params["production_sequence"] = body.production_sequence
    if body.production_completed_check is not None:
        updates.append("production_completed_check = :production_completed_check")
        params["production_completed_check"] = 1 if body.production_completed_check else 0
    if body.remarks is not None:
        updates.append("remarks = :remarks")
        params["remarks"] = (body.remarks or "").strip() or None
    if body.defect_qty is not None:
        updates.append("defect_qty = :defect_qty")
        params["defect_qty"] = max(0, body.defect_qty)
    if body.use_material_stock_sub is not None:
        updates.append("use_material_stock_sub = :use_material_stock_sub")
        params["use_material_stock_sub"] = 1 if body.use_material_stock_sub == 1 else 0
    if body.usage_count is not None:
        try:
            uc = float(body.usage_count)
            if uc > 0:
                updates.append("usage_count = :usage_count")
                params["usage_count"] = uc
        except (TypeError, ValueError):
            pass
    if not updates:
        return {"success": True, "message": "変更なし"}
    try:
        await db.execute(
            text(f"""
                UPDATE cutting_management
                SET {", ".join(updates)}
                WHERE id = :cid
            """),
            params,
        )
        # 面取ロット一覧（chamfering_plans）の同期: production_day / actual_production_quantity を更新
        chamfering_updates: list[str] = []
        chamfering_params: dict = {"cid": cutting_id}
        if "production_day" in params:
            chamfering_updates.append("production_day = :production_day")
            chamfering_params["production_day"] = params["production_day"]
        if "actual_production_quantity" in params:
            chamfering_updates.append("actual_production_quantity = :actual_production_quantity")
            chamfering_params["actual_production_quantity"] = params["actual_production_quantity"]
        if chamfering_updates:
            await db.execute(
                text(f"""
                    UPDATE chamfering_plans
                    SET {", ".join(chamfering_updates)}
                    WHERE cutting_management_id = :cid
                """),
                chamfering_params,
            )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


class SplitToNextDayBody(BaseModel):
    """生産数未完了分を翌日へ順延する時のリクエスト"""
    today_quantity: int  # 当日完成数（この数だけ当日に残し、残りを翌日へ）
    next_day: Optional[str] = None  # 翌日とする日付 YYYY-MM-DD（省略時は production_day + 1 日）


@router.post("/plan/cutting-management/{cutting_id}/split-to-next-day")
async def split_cutting_to_next_day(
    cutting_id: int,
    body: SplitToNextDayBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    切断指示1件の生産数を「当日分」と「翌日分」に分割する。
    - 当日行: actual_production_quantity = today_quantity に更新
    - 翌日行: 新規INSERT（同一製品・同一切断機、production_day=翌日、actual_production_quantity=残り）
    """
    if body.today_quantity < 0:
        raise HTTPException(status_code=400, detail="当日完成数は0以上を指定してください")
    sel = text("""
        SELECT production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
               product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
               is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
               management_code, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
               developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
               production_completed_check, remarks, use_material_stock_sub, usage_count
        FROM cutting_management WHERE id = :cid
    """)
    res = await db.execute(sel, {"cid": cutting_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    r = dict(row)
    total = int(r.get("actual_production_quantity") or 0)
    if body.today_quantity >= total:
        raise HTTPException(
            status_code=400,
            detail=f"当日完成数は、現在の生産数（{total}）より少ない値を指定してください（未完了分が翌日へコピーされます）",
        )
    remainder = total - body.today_quantity

    # 翌日日付
    try:
        pd = r.get("production_day")
        if hasattr(pd, "isoformat"):
            pd_str = pd.isoformat()[:10]
        else:
            pd_str = str(pd)[:10] if pd else ""
        if body.next_day and len((body.next_day or "").strip()) >= 10:
            next_day_str = body.next_day.strip()[:10]
        else:
            if pd:
                if hasattr(pd, "year"):
                    next_d = pd + timedelta(days=1)
                else:
                    parts = pd_str.split("-")
                    if len(parts) == 3:
                        next_d = date(int(parts[0]), int(parts[1]), int(parts[2])) + timedelta(days=1)
                    else:
                        raise HTTPException(status_code=400, detail="生産日が不正です")
                next_day_str = next_d.isoformat()[:10]
            else:
                raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
        parts = next_day_str.split("-")
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="翌日日付の形式は YYYY-MM-DD です")
        next_day_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"日付が不正です: {e}") from e

    # 翌日の production_month（その月の1日）
    next_month_date = date(next_day_date.year, next_day_date.month, 1)
    cm = (r.get("cutting_machine") or "").strip()
    if not cm:
        raise HTTPException(status_code=400, detail="切断機が空のため順延できません")

    try:
        # 1) 当日行を「当日完成数」に更新
        await db.execute(
            text("""
                UPDATE cutting_management
                SET actual_production_quantity = :qty
                WHERE id = :cid
            """),
            {"cid": cutting_id, "qty": body.today_quantity},
        )
        # 1') 面取ロット一覧（chamfering_plans）の生産数も同期
        await db.execute(
            text("UPDATE chamfering_plans SET actual_production_quantity = :qty WHERE cutting_management_id = :cid"),
            {"cid": cutting_id, "qty": body.today_quantity},
        )
        # 2) 翌日・同一切断機の既存行の production_sequence を +1 して、順延行を先頭（1）に挿入
        await db.execute(
            text("""
                UPDATE cutting_management
                SET production_sequence = production_sequence + 1
                WHERE cutting_machine = :cm AND production_day = :nd
            """),
            {"cm": cm, "nd": next_day_date},
        )
        next_seq = 1  # 順延データを翌日の先頭に
        # 3) 翌日行を INSERT（残り数量、生産順=1）
        params = {k: r.get(k) for k in (
            "production_line", "cutting_machine", "priority_order",
            "product_cd", "product_name", "planned_quantity", "start_date", "end_date", "production_lot_size", "lot_number",
            "is_cutting_instructed", "has_chamfering_process", "is_chamfering_instructed", "has_sw_process", "is_sw_instructed",
            "management_code", "take_count", "cutting_length", "chamfering_length",
            "developed_length", "scrap_length", "material_name", "material_manufacturer", "standard_specification", "remarks",
            "use_material_stock_sub", "usage_count"
        )}
        params["production_month"] = next_month_date
        params["production_day"] = next_day_date
        params["production_sequence"] = next_seq
        params["actual_production_quantity"] = remainder
        params["defect_qty"] = r.get("defect_qty") or 0
        if params.get("use_material_stock_sub") is None:
            params["use_material_stock_sub"] = 0
        if params.get("usage_count") is None:
            params["usage_count"] = 1.0
        ins = text("""
            INSERT INTO cutting_management (
                production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
                product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
                is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
                management_code, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
                developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
                production_completed_check, remarks, use_material_stock_sub, usage_count
            ) VALUES (
                :production_month, :production_day, :production_line, :cutting_machine, :production_sequence, :priority_order,
                :product_cd, :product_name, :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
                :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
                :management_code, :actual_production_quantity, :defect_qty, :take_count, :cutting_length, :chamfering_length,
                :developed_length, :scrap_length, :material_name, :material_manufacturer, :standard_specification,
                0, :remarks, :use_material_stock_sub, :usage_count
            )
        """)
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "順延しました（当日分を更新し、残りを翌日へ追加しました）"}


@router.post("/plan/cutting-management/{cutting_id}/duplicate")
async def duplicate_cutting_management(
    cutting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """切断指示1件を複製し、同一切断機内で直下に挿入する。"""
    sel = text("""
        SELECT production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
               product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
               is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
               management_code, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
               developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
               production_completed_check, remarks, use_material_stock_sub, usage_count
        FROM cutting_management WHERE id = :cid
    """)
    res = await db.execute(sel, {"cid": cutting_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    r = dict(row)
    cm = (r.get("cutting_machine") or "").strip()
    if not cm:
        raise HTTPException(status_code=400, detail="切断機が空のため複製できません")
    current_seq = int(r.get("production_sequence") or 0)

    try:
        await db.execute(
            text("""
                UPDATE cutting_management SET production_sequence = production_sequence + 1
                WHERE cutting_machine = :cm AND production_sequence > :seq
            """),
            {"cm": cm, "seq": current_seq},
        )
        ins = text("""
            INSERT INTO cutting_management (
                production_month, production_day, production_line, cutting_machine, production_sequence, priority_order,
                product_cd, product_name, planned_quantity, start_date, end_date, production_lot_size, lot_number,
                is_cutting_instructed, has_chamfering_process, is_chamfering_instructed, has_sw_process, is_sw_instructed,
                management_code, actual_production_quantity, defect_qty, take_count, cutting_length, chamfering_length,
                developed_length, scrap_length, material_name, material_manufacturer, standard_specification,
                production_completed_check, remarks, use_material_stock_sub, usage_count
            ) VALUES (
                :production_month, :production_day, :production_line, :cutting_machine, :production_sequence, :priority_order,
                :product_cd, :product_name, :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
                :is_cutting_instructed, :has_chamfering_process, :is_chamfering_instructed, :has_sw_process, :is_sw_instructed,
                :management_code, :actual_production_quantity, :defect_qty, :take_count, :cutting_length, :chamfering_length,
                :developed_length, :scrap_length, :material_name, :material_manufacturer, :standard_specification,
                0, :remarks, :use_material_stock_sub, :usage_count
            )
        """)
        params = {k: r.get(k) for k in (
            "production_month", "production_day", "production_line", "cutting_machine", "priority_order",
            "product_cd", "product_name", "planned_quantity", "start_date", "end_date", "production_lot_size", "lot_number",
            "is_cutting_instructed", "has_chamfering_process", "is_chamfering_instructed", "has_sw_process", "is_sw_instructed",
            "management_code", "actual_production_quantity", "defect_qty", "take_count", "cutting_length", "chamfering_length",
            "developed_length", "scrap_length", "material_name", "material_manufacturer", "standard_specification", "remarks",
            "use_material_stock_sub", "usage_count"
        )}
        params["production_sequence"] = current_seq + 1
        if params.get("use_material_stock_sub") is None:
            params["use_material_stock_sub"] = 0
        if params.get("usage_count") is None:
            params["usage_count"] = 1.0
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "複製しました"}


@router.delete("/plan/cutting-management/{cutting_id}")
async def delete_cutting_management(
    cutting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """切断指示1件を削除する（紐づく面取・面取ロット・カンバン発行も削除）。"""
    try:
        chamfering_res = await db.execute(
            text("SELECT id FROM chamfering_management WHERE cutting_management_id = :cid"),
            {"cid": cutting_id},
        )
        chamfering_ids = [r[0] for r in chamfering_res.fetchall() if r[0] is not None]
        await db.execute(
            text("DELETE FROM kanban_issuance WHERE process_type = 'cutting' AND source_id = :cid"),
            {"cid": cutting_id},
        )
        for sid in chamfering_ids:
            await db.execute(
                text("DELETE FROM kanban_issuance WHERE process_type = 'chamfering' AND source_id = :sid"),
                {"sid": sid},
            )
        await db.execute(text("DELETE FROM chamfering_management WHERE cutting_management_id = :cid"), {"cid": cutting_id})
        await db.execute(text("DELETE FROM chamfering_plans WHERE cutting_management_id = :cid"), {"cid": cutting_id})
        await db.execute(text("DELETE FROM cutting_management WHERE id = :cid"), {"cid": cutting_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "削除しました"}


# ---------- 面取ロット一覧（chamfering_plans）----------
@router.get("/plan/chamfering-plans/list")
async def get_chamfering_plans_list(
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    production_line: Optional[str] = Query(None, description="ライン（部分一致）"),
    limit: int = Query(5000, ge=1, le=50000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取ロット一覧: chamfering_plans を取得（切断指示登録時・面取工程ありで自動登録された待機データ）。"""
    conditions = ["1=1"]
    params = {"limit": limit}
    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    params["production_month"] = date(y, m, 1)
                    conditions.append("production_month = :production_month")
        except (ValueError, IndexError):
            pass
    if production_day and production_day.strip():
        try:
            parts = production_day.strip().split("-")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                params["production_day"] = date(y, m, d)
                conditions.append("production_day = :production_day")
        except (ValueError, IndexError):
            pass
    if production_line and production_line.strip():
        conditions.append("production_line LIKE :production_line")
        params["production_line"] = f"%{production_line.strip()}%"

    sql = text(f"""
        SELECT id, cutting_management_id, production_month, production_day, production_line, production_order,
               product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
               cutting_length, chamfering_length, developed_length, material_name, management_code, cd, has_sw_process, created_at
        FROM chamfering_plans
        WHERE {" AND ".join(conditions)}
        ORDER BY production_month DESC, production_day DESC, production_line, production_order
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, params)
    except Exception as e:
        msg = str(e).lower()
        if "chamfering_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="chamfering_plans テーブルが存在しません。マイグレーション 063_chamfering_batch.sql を実行してください。",
            ) from e
        raise
    rows = result.mappings().fetchall()

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()[:19] if val else default
        return val

    def _row(r):
        row = dict(r)
        pm = _v(row, "production_month")
        pd = _v(row, "production_day")
        return {
            "id": row.get("id"),
            "cutting_management_id": row.get("cutting_management_id"),
            "production_month": (str(pm)[:10] if pm else None),
            "production_day": (str(pd)[:10] if pd else None),
            "production_line": row.get("production_line"),
            "production_order": row.get("production_order"),
            "product_cd": row.get("product_cd"),
            "product_name": row.get("product_name"),
            "actual_production_quantity": row.get("actual_production_quantity"),
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": row.get("lot_number"),
            "cutting_length": _v(row, "cutting_length"),
            "chamfering_length": _v(row, "chamfering_length"),
            "developed_length": _v(row, "developed_length"),
            "material_name": row.get("material_name"),
            "management_code": row.get("management_code"),
            "cd": row.get("cd") or (str(row.get("management_code") or "")[-5:] or None),
            "has_sw_process": 1 if row.get("has_sw_process") else 0,
            "created_at": _v(row, "created_at"),
        }
    data = [_row(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


class CreateChamferingPlanBody(BaseModel):
    """面取ロット一覧：新規追加（chamfering_plans に1件INSERT、cutting_management_id は NULL）"""
    production_month: str  # YYYY-MM
    production_day: str  # YYYY-MM-DD
    production_line: str  # ライン（面取機）
    production_order: Optional[int] = None
    product_cd: str
    product_name: str
    actual_production_quantity: Optional[int] = 0
    production_lot_size: Optional[int] = None
    lot_number: Optional[str] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    material_name: Optional[str] = None
    has_sw_process: Optional[int] = 0


@router.post("/plan/chamfering-plans")
async def create_chamfering_plan(
    body: CreateChamferingPlanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取ロット一覧に新規1件追加（cutting_management_id は NULL）。management_code / cd はトリガーで自動設定。"""
    production_month_date = _parse_date_ymd(body.production_month)
    production_day_date = _parse_date_ymd(body.production_day)
    if production_month_date is None:
        raise HTTPException(status_code=400, detail="生産月（production_month）を YYYY-MM 形式で指定してください")
    if production_day_date is None:
        raise HTTPException(status_code=400, detail="生産日（production_day）を YYYY-MM-DD 形式で指定してください")
    line = (body.production_line or "").strip()
    if not line:
        raise HTTPException(status_code=400, detail="ラインを指定してください")
    product_cd = (body.product_cd or "").strip()
    product_name = (body.product_name or "").strip()
    if not product_cd or not product_name:
        raise HTTPException(status_code=400, detail="製品CD・製品名を指定してください")

    ins = text("""
        INSERT INTO chamfering_plans (
            cutting_management_id, production_month, production_day, production_line, production_order,
            product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
            cutting_length, chamfering_length, developed_length, material_name, has_sw_process
        ) VALUES (
            NULL, :production_month, :production_day, :production_line, :production_order,
            :product_cd, :product_name, :actual_production_quantity, :production_lot_size, :lot_number,
            :cutting_length, :chamfering_length, :developed_length, :material_name, :has_sw_process
        )
    """)
    params = {
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": line,
        "production_order": body.production_order,
        "product_cd": product_cd,
        "product_name": product_name,
        "actual_production_quantity": body.actual_production_quantity if body.actual_production_quantity is not None else 0,
        "production_lot_size": body.production_lot_size,
        "lot_number": (body.lot_number or "").strip() or None,
        "cutting_length": body.cutting_length,
        "chamfering_length": body.chamfering_length,
        "developed_length": body.developed_length,
        "material_name": (body.material_name or "").strip() or None,
        "has_sw_process": 1 if body.has_sw_process else 0,
    }
    try:
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "登録しました"}


class MoveChamferingPlanToChamferingBody(BaseModel):
    """面取ロット1件を面取指示へ移行（オプションで生産日・ライン指定。SW時は production_line_2 で2件登録）"""
    chamfering_plan_id: int
    production_day: Optional[str] = None  # YYYY-MM-DD、指定時はこれを使用
    production_line: Optional[str] = None  # ライン/面取機、指定時はこれを使用
    production_line_2: Optional[str] = None  # SW時用の2台目面取機、指定時は2件INSERT


@router.post("/plan/chamfering-plans/move-to-chamfering")
async def move_chamfering_plan_to_chamfering(
    body: MoveChamferingPlanToChamferingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取ロット1件を面取指示（chamfering_management）へ移行し、chamfering_plans から削除。production_line_2 指定時は2件登録。"""
    res = await db.execute(
        text("""
            SELECT id, cutting_management_id, production_month, production_day, production_line, production_order,
                   product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
                   cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process, no_count
            FROM chamfering_plans WHERE id = :bid
        """),
        {"bid": body.chamfering_plan_id},
    )
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="指定の面取ロットが見つかりません")
    row = dict(row)

    def _to_date(v):
        if v is None:
            return None
        if hasattr(v, "date"):
            return v.date()
        s = str(v).strip()[:10]
        if len(s) == 10:
            try:
                return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
            except (ValueError, IndexError):
                pass
        return date.today()

    if body.production_day and str(body.production_day).strip()[:10]:
        production_day_date = _to_date(str(body.production_day).strip()[:10]) or date.today()
    else:
        production_day_val = row.get("production_day")
        production_day_date = _to_date(production_day_val) or date.today()

    production_month_val = row.get("production_month")
    production_month_date = _to_date(production_month_val) or date.today()

    production_line_val = (body.production_line and str(body.production_line).strip()) or (row.get("production_line") or "").strip() or ""
    production_line_2_val = (body.production_line_2 and str(body.production_line_2).strip()) or None

    def _params(pl: str, chamfering_machine_val: str, production_sequence_val: int):
        return {
            "cutting_management_id": row.get("cutting_management_id"),
            "production_month": production_month_date,
            "production_day": production_day_date,
            "production_line": (row.get("production_line") or "").strip() or "",  # ライン：面取ロットのラインをそのまま使用（面取機ではない）
            "chamfering_machine": chamfering_machine_val or pl,
            "production_order": row.get("production_order"),
            "production_sequence": production_sequence_val,
            "product_cd": (row.get("product_cd") or "").strip() or "",
            "product_name": (row.get("product_name") or "").strip() or "",
            "actual_production_quantity": row.get("actual_production_quantity") or 0,
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": (row.get("lot_number") or "").strip() or None,
            "cutting_length": float(row["cutting_length"]) if row.get("cutting_length") is not None else None,
            "chamfering_length": float(row["chamfering_length"]) if row.get("chamfering_length") is not None else None,
            "developed_length": float(row["developed_length"]) if row.get("developed_length") is not None else None,
            "production_time": None,
            "material_name": (row.get("material_name") or "").strip() or None,
            "management_code": (row.get("management_code") or "").strip() or None,
            "has_sw_process": 1 if row.get("has_sw_process") else 0,
            "remarks": None,
            "no_count": 1 if row.get("no_count") else 0,
        }

    ins = text("""
        INSERT INTO chamfering_management (
            cutting_management_id, production_month, production_day, production_line, chamfering_machine, production_order, production_sequence,
            product_cd, product_name, actual_production_quantity, defect_qty, production_lot_size, lot_number,
            cutting_length, chamfering_length, developed_length, production_time, material_name, management_code, has_sw_process, production_completed_check, no_count, remarks
        ) VALUES (
            :cutting_management_id, :production_month, :production_day, :production_line, :chamfering_machine, :production_order, :production_sequence,
            :product_cd, :product_name, :actual_production_quantity, 0, :production_lot_size, :lot_number,
            :cutting_length, :chamfering_length, :developed_length, :production_time, :material_name, :management_code, :has_sw_process, 0, :no_count, :remarks
        )
    """)
    try:
        order_res = await db.execute(
            text("""
                SELECT COALESCE(MAX(production_sequence), 0) + 1 AS next_seq
                FROM chamfering_management
                WHERE chamfering_machine = :cm AND production_day = :pd
            """),
            {"cm": production_line_val, "pd": production_day_date},
        )
        next_seq_1 = int(order_res.scalar() or 1)
        await db.execute(ins, _params(production_line_val, production_line_val, next_seq_1))
        if production_line_2_val:
            order_res2 = await db.execute(
                text("""
                    SELECT COALESCE(MAX(production_sequence), 0) + 1 AS next_seq
                    FROM chamfering_management
                    WHERE chamfering_machine = :cm AND production_day = :pd
                """),
                {"cm": production_line_2_val, "pd": production_day_date},
            )
            next_seq_2 = int(order_res2.scalar() or 1)
            await db.execute(ins, _params(production_line_2_val, production_line_2_val, next_seq_2))
        await db.execute(text("DELETE FROM chamfering_plans WHERE id = :bid"), {"bid": body.chamfering_plan_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "面取指示に登録しました"}


class UpdateChamferingPlanSwBody(BaseModel):
    """面取ロットのSW工程フラグ更新"""
    has_sw_process: bool


class UpdateChamferingPlanContentBody(BaseModel):
    """面取ロット内容編集（ロット内容編集窗体と同様の項目のうち chamfering_plans に存在するもの）"""
    production_month: Optional[str] = None
    production_day: Optional[str] = None
    production_line: Optional[str] = None
    production_order: Optional[int] = None
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    actual_production_quantity: Optional[int] = None
    production_lot_size: Optional[int] = None
    lot_number: Optional[str] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    material_name: Optional[str] = None
    has_sw_process: Optional[bool] = None


@router.patch("/plan/chamfering-plans/{plan_id}")
async def update_chamfering_plan_sw(
    plan_id: int,
    body: UpdateChamferingPlanSwBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取ロット1件のhas_sw_processを更新。"""
    try:
        await db.execute(
            text("UPDATE chamfering_plans SET has_sw_process = :v WHERE id = :pid"),
            {"v": 1 if body.has_sw_process else 0, "pid": plan_id},
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


@router.delete("/plan/chamfering-plans/{plan_id}")
async def delete_chamfering_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取ロット1件を削除。"""
    res = await db.execute(
        text("SELECT id FROM chamfering_plans WHERE id = :pid"),
        {"pid": plan_id},
    )
    if not res.scalar():
        raise HTTPException(status_code=404, detail="指定の面取ロットが見つかりません")
    try:
        await db.execute(text("DELETE FROM chamfering_plans WHERE id = :pid"), {"pid": plan_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "削除しました"}


@router.put("/plan/chamfering-plans/{plan_id}/content")
async def update_chamfering_plan_content(
    plan_id: int,
    body: UpdateChamferingPlanContentBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取ロット1件の内容を更新（ロット内容編集と同様の項目）。"""
    res = await db.execute(
        text("SELECT id FROM chamfering_plans WHERE id = :pid"),
        {"pid": plan_id},
    )
    if not res.scalar():
        raise HTTPException(status_code=404, detail="指定の面取ロットが見つかりません")
    updates = []
    params = {"pid": plan_id}
    if body.production_month is not None:
        d = _parse_date_ymd(body.production_month)
        if d is not None:
            updates.append("production_month = :production_month")
            params["production_month"] = d
    if body.production_day is not None:
        d = _parse_date_ymd(body.production_day)
        if d is not None:
            updates.append("production_day = :production_day")
            params["production_day"] = d
    if body.production_line is not None:
        updates.append("production_line = :production_line")
        params["production_line"] = body.production_line.strip() or None
    if body.production_order is not None:
        updates.append("production_order = :production_order")
        params["production_order"] = body.production_order
    if body.product_cd is not None:
        updates.append("product_cd = :product_cd")
        params["product_cd"] = body.product_cd.strip() or None
    if body.product_name is not None:
        updates.append("product_name = :product_name")
        params["product_name"] = body.product_name.strip() or None
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = body.actual_production_quantity
    if body.production_lot_size is not None:
        updates.append("production_lot_size = :production_lot_size")
        params["production_lot_size"] = body.production_lot_size
    if body.lot_number is not None:
        updates.append("lot_number = :lot_number")
        params["lot_number"] = body.lot_number.strip() or None
    if body.cutting_length is not None:
        updates.append("cutting_length = :cutting_length")
        params["cutting_length"] = body.cutting_length
    if body.chamfering_length is not None:
        updates.append("chamfering_length = :chamfering_length")
        params["chamfering_length"] = body.chamfering_length
    if body.developed_length is not None:
        updates.append("developed_length = :developed_length")
        params["developed_length"] = body.developed_length
    if body.material_name is not None:
        updates.append("material_name = :material_name")
        params["material_name"] = body.material_name.strip() or None
    if body.has_sw_process is not None:
        updates.append("has_sw_process = :has_sw_process")
        params["has_sw_process"] = 1 if body.has_sw_process else 0
    if not updates:
        return {"success": True, "message": "変更なし"}
    set_clause = ", ".join(updates)
    try:
        await db.execute(
            text(f"UPDATE chamfering_plans SET {set_clause} WHERE id = :pid"),
            params,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "保存しました"}


@router.post("/plan/chamfering-plans/{plan_id}/copy")
async def copy_chamfering_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取ロット1件を複製（同内容で新規1件追加）。"""
    res = await db.execute(
        text("""
            SELECT cutting_management_id, production_month, production_day, production_line, production_order,
                   product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
                   cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
            FROM chamfering_plans WHERE id = :pid
        """),
        {"pid": plan_id},
    )
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="指定の面取ロットが見つかりません")
    row = dict(row)

    def _to_date(v):
        if v is None:
            return None
        if hasattr(v, "date"):
            return v.date()
        s = str(v).strip()[:10]
        if len(s) == 10:
            try:
                return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
            except (ValueError, IndexError):
                pass
        return date.today()

    production_month_date = _to_date(row.get("production_month")) or date.today()
    production_day_date = _to_date(row.get("production_day")) or date.today()

    ins = text("""
        INSERT INTO chamfering_plans (
            cutting_management_id, production_month, production_day, production_line, production_order,
            product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
            cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
        ) VALUES (
            :cutting_management_id, :production_month, :production_day, :production_line, :production_order,
            :product_cd, :product_name, :actual_production_quantity, :production_lot_size, :lot_number,
            :cutting_length, :chamfering_length, :developed_length, :material_name, :management_code, :has_sw_process
        )
    """)
    params = {
        "cutting_management_id": row.get("cutting_management_id"),
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": (row.get("production_line") or "").strip() or "",
        "production_order": row.get("production_order"),
        "product_cd": (row.get("product_cd") or "").strip() or "",
        "product_name": (row.get("product_name") or "").strip() or "",
        "actual_production_quantity": row.get("actual_production_quantity") or 0,
        "production_lot_size": row.get("production_lot_size"),
        "lot_number": (row.get("lot_number") or "").strip() or None,
        "cutting_length": float(row["cutting_length"]) if row.get("cutting_length") is not None else None,
        "chamfering_length": float(row["chamfering_length"]) if row.get("chamfering_length") is not None else None,
        "developed_length": float(row["developed_length"]) if row.get("developed_length") is not None else None,
        "material_name": (row.get("material_name") or "").strip() or None,
        "management_code": (row.get("management_code") or "").strip() or None,
        "has_sw_process": 1 if row.get("has_sw_process") else 0,
    }
    try:
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "複製しました"}


class MoveChamferingManagementToBatchBody(BaseModel):
    """面取指示1件を面取ロット一覧へ戻す"""
    chamfering_management_id: int


@router.post("/plan/chamfering-plans/move-from-chamfering")
async def move_chamfering_management_to_batch(
    body: MoveChamferingManagementToBatchBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示1件を面取ロット一覧（chamfering_plans）へ戻し、chamfering_management から削除。"""
    res = await db.execute(
        text("""
            SELECT id, cutting_management_id, production_month, production_day, production_line, production_order,
                   product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
                   cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
            FROM chamfering_management WHERE id = :mid
        """),
        {"mid": body.chamfering_management_id},
    )
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="指定の面取指示が見つかりません")
    row = dict(row)

    def _to_date(v):
        if v is None:
            return None
        if hasattr(v, "date"):
            return v.date()
        s = str(v).strip()[:10]
        if len(s) == 10:
            try:
                return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
            except (ValueError, IndexError):
                pass
        return date.today()

    production_month_date = _to_date(row.get("production_month")) or date.today()
    production_day_date = _to_date(row.get("production_day")) or date.today()

    ins = text("""
        INSERT INTO chamfering_plans (
            cutting_management_id, production_month, production_day, production_line, production_order,
            product_cd, product_name, actual_production_quantity, production_lot_size, lot_number,
            cutting_length, chamfering_length, developed_length, material_name, management_code, has_sw_process
        ) VALUES (
            :cutting_management_id, :production_month, :production_day, :production_line, :production_order,
            :product_cd, :product_name, :actual_production_quantity, :production_lot_size, :lot_number,
            :cutting_length, :chamfering_length, :developed_length, :material_name, :management_code, :has_sw_process
        )
    """)
    params = {
        "cutting_management_id": row.get("cutting_management_id"),
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": (row.get("production_line") or "").strip() or "",
        "production_order": row.get("production_order"),
        "product_cd": (row.get("product_cd") or "").strip() or "",
        "product_name": (row.get("product_name") or "").strip() or "",
        "actual_production_quantity": row.get("actual_production_quantity") or 0,
        "production_lot_size": row.get("production_lot_size"),
        "lot_number": (row.get("lot_number") or "").strip() or None,
        "cutting_length": float(row["cutting_length"]) if row.get("cutting_length") is not None else None,
        "chamfering_length": float(row["chamfering_length"]) if row.get("chamfering_length") is not None else None,
        "developed_length": float(row["developed_length"]) if row.get("developed_length") is not None else None,
        "material_name": (row.get("material_name") or "").strip() or None,
        "management_code": (row.get("management_code") or "").strip() or None,
        "has_sw_process": 1 if row.get("has_sw_process") else 0,
    }
    try:
        await db.execute(ins, params)
        await db.execute(
            text("DELETE FROM kanban_issuance WHERE process_type = 'chamfering' AND source_id = :sid"),
            {"sid": body.chamfering_management_id},
        )
        await db.execute(text("DELETE FROM chamfering_management WHERE id = :mid"), {"mid": body.chamfering_management_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "面取ロット一覧に戻しました"}


# ---------- 面取指示（chamfering_management）----------
@router.get("/plan/chamfering-management/list")
async def get_chamfering_management_list(
    production_month: Optional[str] = Query(None, description="生産月 YYYY-MM"),
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    production_line: Optional[str] = Query(None, description="ライン（部分一致）"),
    chamfering_machine: Optional[str] = Query(None, description="面取機（完全一致）"),
    limit: int = Query(2000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示一覧: chamfering_management を取得する。"""
    conditions = ["1=1"]
    params = {"limit": limit}
    if production_month and production_month.strip():
        try:
            parts = production_month.strip().split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if 1 <= m <= 12:
                    params["production_month"] = date(y, m, 1)
                    conditions.append("production_month = :production_month")
        except (ValueError, IndexError):
            pass
    if production_day and production_day.strip():
        try:
            parts = production_day.strip().split("-")
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                params["production_day"] = date(y, m, d)
                conditions.append("production_day = :production_day")
        except (ValueError, IndexError):
            pass
    if production_line and production_line.strip():
        conditions.append("production_line LIKE :production_line")
        params["production_line"] = f"%{production_line.strip()}%"
    if chamfering_machine is not None and chamfering_machine.strip():
        conditions.append("chamfering_machine = :chamfering_machine")
        params["chamfering_machine"] = chamfering_machine.strip()

    sql = text(f"""
        SELECT id, cutting_management_id, production_month, production_day, production_line, chamfering_machine,
               production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty, production_lot_size, lot_number,
               cutting_length, chamfering_length, developed_length, production_time, material_name, management_code, has_sw_process,
               production_completed_check, no_count, remarks, cd, created_at
        FROM chamfering_management
        WHERE {" AND ".join(conditions)}
        ORDER BY production_day DESC, chamfering_machine ASC, production_sequence ASC
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, params)
    except Exception as e:
        msg = str(e).lower()
        if "chamfering_management" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="chamfering_management テーブルが存在しません。マイグレーション 054_chamfering_management.sql を実行してください。",
            ) from e
        raise
    rows = result.mappings().fetchall()

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if isinstance(val, Decimal):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()[:19] if val else default
        return val

    def _cham_row(r):
        row = dict(r)
        pm = _v(row, "production_month")
        pd = _v(row, "production_day")
        return {
            "id": row.get("id"),
            "cutting_management_id": row.get("cutting_management_id"),
            "production_month": (str(pm)[:10] if pm else None),
            "production_day": (str(pd)[:10] if pd else None),
            "production_line": row.get("production_line"),
            "chamfering_machine": row.get("chamfering_machine"),
            "production_order": row.get("production_order"),
            "production_sequence": row.get("production_sequence"),
            "product_cd": row.get("product_cd"),
            "product_name": row.get("product_name"),
            "actual_production_quantity": row.get("actual_production_quantity"),
            "defect_qty": row.get("defect_qty"),
            "production_lot_size": row.get("production_lot_size"),
            "lot_number": row.get("lot_number"),
            "cutting_length": _v(row, "cutting_length"),
            "chamfering_length": _v(row, "chamfering_length"),
            "developed_length": _v(row, "developed_length"),
            "production_time": _v(row, "production_time"),
            "material_name": row.get("material_name"),
            "management_code": row.get("management_code"),
            "has_sw_process": 1 if row.get("has_sw_process") else 0,
            "production_completed_check": row.get("production_completed_check"),
            "no_count": 1 if row.get("no_count") else 0,
            "remarks": row.get("remarks"),
            "cd": row.get("cd"),
            "created_at": _v(row, "created_at"),
        }
    data = [_cham_row(dict(r)) for r in rows]
    return {"success": True, "data": data, "message": "OK"}


@router.post("/plan/chamfering-management/confirm-actual")
async def confirm_chamfering_actual(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD（筛选日期）"),
    chamfering_machine: Optional[str] = Query(None, description="面取機（省略時は全機）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    面取指示-今日の「実績確定」: production_completed_check=1 かつ no_count=0 の chamfering_management を
    stock_transaction_logs に保存する。去重复：同一範囲の既存 chamfering_management 実績を先に削除してから挿入。
    """
    try:
        parts = production_day.strip().split("-")
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="production_day は YYYY-MM-DD で指定してください")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        prod_day = date(y, m, d)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="production_day の形式が不正です") from e

    # 去重复：同一範囲の既存実績を削除
    del_params: dict = {"production_day": prod_day}
    del_conditions = [
        "source_file = 'chamfering_management'",
        "DATE(transaction_time) = :production_day",
    ]
    if chamfering_machine and chamfering_machine.strip():
        del_conditions.append("machine_cd = :chamfering_machine")
        del_params["chamfering_machine"] = chamfering_machine.strip()
    del_sql = text("DELETE FROM stock_transaction_logs WHERE " + " AND ".join(del_conditions))
    await db.execute(del_sql, del_params)

    conditions = [
        "production_day = :production_day",
        "production_completed_check = 1",
        "(no_count IS NULL OR no_count = 0)",
    ]
    params = {"production_day": prod_day}
    if chamfering_machine and chamfering_machine.strip():
        conditions.append("chamfering_machine = :chamfering_machine")
        params["chamfering_machine"] = chamfering_machine.strip()
    sel = text("""
        SELECT id, product_cd, management_code, chamfering_machine, actual_production_quantity, defect_qty, production_day
        FROM chamfering_management
        WHERE """ + " AND ".join(conditions))
    res = await db.execute(sel, params)
    rows = res.mappings().fetchall()
    if not rows:
        await db.commit()
        return {"success": True, "message": "対象データがありません（既存分は削除済み）", "inserted": 0, "total_quantity": 0, "deleted": True}
    ins = text("""
        INSERT INTO stock_transaction_logs (
            stock_type, transaction_type, target_cd, location_cd, lot_no, process_cd, machine_cd,
            quantity, unit, transaction_time, source_file
        ) VALUES (
            '仕掛品', :transaction_type, :target_cd, '工程中間在庫', :lot_no, 'KT02', :machine_cd,
            :quantity, '本', :transaction_time, 'chamfering_management'
        )
    """)
    inserted = 0
    total_quantity = 0
    for row in rows:
        r = dict(row)
        product_cd = (r.get("product_cd") or "").strip()
        if not product_cd:
            continue
        prod_day_val = r.get("production_day")
        if hasattr(prod_day_val, "isoformat"):
            tx_time = datetime.combine(prod_day_val, datetime.min.time()) if prod_day_val else datetime.now()
        else:
            tx_time = datetime.now()
        qty = r.get("actual_production_quantity")
        if qty is None:
            qty = 0
        # 良品：transaction_type='実績'
        await db.execute(ins, {
            "target_cd": product_cd,
            "lot_no": r.get("management_code"),
            "machine_cd": r.get("chamfering_machine"),
            "quantity": qty,
            "transaction_time": tx_time,
            "transaction_type": "実績",
        })
        inserted += 1
        total_quantity += int(qty)
        # 不良数：transaction_type='不良'
        defect_qty = r.get("defect_qty")
        if defect_qty is not None and int(defect_qty) > 0:
            await db.execute(ins, {
                "target_cd": product_cd,
                "lot_no": r.get("management_code"),
                "machine_cd": r.get("chamfering_machine"),
                "quantity": int(defect_qty),
                "transaction_time": tx_time,
                "transaction_type": "不良",
            })
            inserted += 1
    await db.commit()
    return {
        "success": True,
        "message": f"実績を {inserted} 件登録しました",
        "inserted": inserted,
        "total_quantity": total_quantity,
    }


@router.delete("/plan/chamfering-management/{chamfering_id}")
async def delete_chamfering_management(
    chamfering_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示1件を削除。関連するカンバン発行も削除。"""
    res = await db.execute(
        text("SELECT id FROM chamfering_management WHERE id = :mid"),
        {"mid": chamfering_id},
    )
    if not res.scalar():
        raise HTTPException(status_code=404, detail="指定の面取指示が見つかりません")
    try:
        await db.execute(
            text("DELETE FROM kanban_issuance WHERE process_type = 'chamfering' AND source_id = :sid"),
            {"sid": chamfering_id},
        )
        await db.execute(text("DELETE FROM chamfering_management WHERE id = :mid"), {"mid": chamfering_id})
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "削除しました"}


class CreateChamferingManagementBody(BaseModel):
    """面取指示の新規追加（chamfering_management 1件挿入）"""
    production_day: str  # YYYY-MM-DD
    production_line: str = ""
    chamfering_machine: str = ""
    product_cd: str = ""
    product_name: str = ""
    actual_production_quantity: Optional[int] = 0
    production_sequence: Optional[int] = None  # 省略時は同一面取機・同一生産日の最大+1
    material_name: Optional[str] = None
    management_code: Optional[str] = None
    remarks: Optional[str] = None


@router.post("/plan/chamfering-management")
async def create_chamfering_management(
    body: CreateChamferingManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示を1件新規追加。production_month は production_day の年月の初日に設定。"""
    production_day_s = (body.production_day or "").strip()[:10]
    if len(production_day_s) != 10:
        raise HTTPException(status_code=400, detail="生産日は YYYY-MM-DD で指定してください")
    try:
        y, m, d = int(production_day_s[:4]), int(production_day_s[5:7]), int(production_day_s[8:10])
        prod_day = date(y, m, d)
        production_month = date(y, m, 1)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail="生産日の形式が不正です") from e
    chamfering_machine = (body.chamfering_machine or "").strip() or None
    if not chamfering_machine:
        raise HTTPException(status_code=400, detail="面取機を指定してください")
    product_cd = (body.product_cd or "").strip() or ""
    product_name = (body.product_name or "").strip() or ""
    if not product_cd or not product_name:
        raise HTTPException(status_code=400, detail="製品CD・製品名は必須です")
    production_line = (body.production_line or "").strip() or ""
    production_sequence = body.production_sequence
    if production_sequence is None:
        next_seq = await db.execute(
            text(
                "SELECT COALESCE(MAX(production_sequence), 0) + 1 AS n FROM chamfering_management "
                "WHERE chamfering_machine = :cm AND production_day = :pd"
            ),
            {"cm": chamfering_machine, "pd": prod_day},
        )
        production_sequence = next_seq.scalar() or 1
    # 管理コード未指定時は自動生成（YYMM + product_cd + ライン下2桁 + 生産順2桁、不足は0埋め）
    management_code_val = (body.management_code or "").strip() or None
    if not management_code_val:
        yy = str(prod_day.year)[-2:]
        mm = str(prod_day.month).zfill(2)
        line_suffix = (production_line or "").strip()[-2:] if (production_line or "").strip() else "00"
        if len(line_suffix) < 2:
            line_suffix = line_suffix.ljust(2, "0")
        seq_s = str(production_sequence).zfill(2)
        management_code_val = f"{yy}{mm}{product_cd}{line_suffix}{seq_s}"
    try:
        ins = text("""
            INSERT INTO chamfering_management (
                cutting_management_id, production_month, production_day, production_line, chamfering_machine,
                production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
                production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
                has_sw_process, production_completed_check, no_count, remarks
            ) VALUES (
                NULL, :production_month, :production_day, :production_line, :chamfering_machine,
                NULL, :production_sequence, :product_cd, :product_name, :actual_production_quantity, 0,
                NULL, NULL, NULL, NULL, NULL, NULL, :material_name, :management_code,
                0, 0, 0, :remarks
            )
        """)
        params = {
            "production_month": production_month,
            "production_day": prod_day,
            "production_line": production_line,
            "chamfering_machine": chamfering_machine,
            "production_sequence": production_sequence,
            "product_cd": product_cd,
            "product_name": product_name,
            "actual_production_quantity": body.actual_production_quantity or 0,
            "material_name": (body.material_name or "").strip() or None,
            "management_code": management_code_val,
            "remarks": (body.remarks or "").strip() or None,
        }
        await db.execute(ins, params)
        await db.commit()
        res = await db.execute(text("SELECT LAST_INSERT_ID() AS id"))
        new_id = res.scalar()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "登録しました", "id": new_id}


class UpdateChamferingManagementBody(BaseModel):
    """面取指示1件の部分更新（完了・カウント無・面取機・生産数・不良数・生産順・備考・生産日）"""
    production_completed_check: Optional[bool] = None
    no_count: Optional[bool] = None
    chamfering_machine: Optional[str] = None
    actual_production_quantity: Optional[int] = None
    defect_qty: Optional[int] = None
    production_sequence: Optional[int] = None
    remarks: Optional[str] = None
    production_day: Optional[str] = None  # YYYY-MM-DD


@router.patch("/plan/chamfering-management/{chamfering_id}")
async def update_chamfering_management(
    chamfering_id: int,
    body: UpdateChamferingManagementBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示1件の production_completed_check / no_count / chamfering_machine / actual_production_quantity / production_sequence / remarks を更新。"""
    res = await db.execute(
        text("SELECT id FROM chamfering_management WHERE id = :mid"),
        {"mid": chamfering_id},
    )
    if not res.scalar():
        raise HTTPException(status_code=404, detail="指定の面取指示が見つかりません")
    updates = []
    params: dict = {"mid": chamfering_id}
    if body.production_completed_check is not None:
        updates.append("production_completed_check = :production_completed_check")
        params["production_completed_check"] = 1 if body.production_completed_check else 0
    if body.no_count is not None:
        updates.append("no_count = :no_count")
        params["no_count"] = 1 if body.no_count else 0
    if body.chamfering_machine is not None:
        updates.append("chamfering_machine = :chamfering_machine")
        params["chamfering_machine"] = body.chamfering_machine.strip() or None
    if body.actual_production_quantity is not None:
        updates.append("actual_production_quantity = :actual_production_quantity")
        params["actual_production_quantity"] = body.actual_production_quantity
    if body.defect_qty is not None:
        updates.append("defect_qty = :defect_qty")
        params["defect_qty"] = max(0, body.defect_qty)
    if body.production_sequence is not None:
        updates.append("production_sequence = :production_sequence")
        params["production_sequence"] = body.production_sequence
    if body.remarks is not None:
        updates.append("remarks = :remarks")
        params["remarks"] = body.remarks.strip() or None
    if body.production_day is not None:
        d = _parse_date_ymd(body.production_day)
        if d is not None:
            updates.append("production_month = :production_month")
            params["production_month"] = d.replace(day=1)  # production_month = 当月1日
            updates.append("production_day = :production_day")
            params["production_day"] = d
    if not updates:
        return {"success": True, "message": "変更なし"}
    try:
        await db.execute(
            text(f"UPDATE chamfering_management SET {', '.join(updates)} WHERE id = :mid"),
            params,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "更新しました"}


class SplitToNextDayChamferingBody(BaseModel):
    """面取指示の未完了分を翌日へ順延するリクエスト"""
    today_quantity: int  # 当日完成数
    next_day: Optional[str] = None  # 翌日 YYYY-MM-DD（省略時は production_day + 1 日）


@router.post("/plan/chamfering-management/{chamfering_id}/split-to-next-day")
async def split_chamfering_to_next_day(
    chamfering_id: int,
    body: SplitToNextDayChamferingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示1件の生産数を当日分と翌日分に分割。当日行は完了にし、翌日行を新規追加。"""
    if body.today_quantity < 0:
        raise HTTPException(status_code=400, detail="当日完成数は0以上を指定してください")
    sel = text("""
        SELECT id, cutting_management_id, production_month, production_day, production_line, chamfering_machine,
               production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
               production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
               has_sw_process, production_completed_check, no_count, remarks
        FROM chamfering_management WHERE id = :mid
    """)
    res = await db.execute(sel, {"mid": chamfering_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="面取指示が見つかりません")
    r = dict(row)
    total = int(r.get("actual_production_quantity") or 0)
    if body.today_quantity >= total:
        raise HTTPException(
            status_code=400,
            detail=f"当日完成数は、現在の生産数（{total}）より少ない値を指定してください",
        )
    remainder = total - body.today_quantity

    pd = r.get("production_day")
    if hasattr(pd, "isoformat"):
        pd_str = pd.isoformat()[:10]
    else:
        pd_str = str(pd)[:10] if pd else ""
    if body.next_day and len((body.next_day or "").strip()) >= 10:
        next_day_str = body.next_day.strip()[:10]
    else:
        if pd:
            if hasattr(pd, "year"):
                next_d = pd + timedelta(days=1)
                next_day_str = next_d.isoformat()[:10]
            else:
                parts = pd_str.split("-")
                if len(parts) == 3:
                    next_d = date(int(parts[0]), int(parts[1]), int(parts[2])) + timedelta(days=1)
                    next_day_str = next_d.isoformat()[:10]
                else:
                    raise HTTPException(status_code=400, detail="生産日が不正です")
        else:
            raise HTTPException(status_code=400, detail="生産日が空のため翌日を算出できません")
    parts = next_day_str.split("-")
    if len(parts) != 3:
        raise HTTPException(status_code=400, detail="翌日の形式は YYYY-MM-DD です")
    next_day_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
    next_month_date = date(next_day_date.year, next_day_date.month, 1)
    cm = (r.get("chamfering_machine") or "").strip()
    if not cm:
        raise HTTPException(status_code=400, detail="面取機が空のため順延できません")

    try:
        await db.execute(
            text("""
                UPDATE chamfering_management
                SET actual_production_quantity = :qty, production_completed_check = 1
                WHERE id = :mid
            """),
            {"mid": chamfering_id, "qty": body.today_quantity},
        )
        # 翌日行は順位1で挿入し、既存の翌日行の production_sequence を +1 して自動ソート
        params = {
            "cutting_management_id": r.get("cutting_management_id"),
            "production_month": next_month_date,
            "production_day": next_day_date,
            "production_line": r.get("production_line") or "",
            "chamfering_machine": cm,
            "production_order": r.get("production_order"),
            "production_sequence": 1,
            "product_cd": r.get("product_cd") or "",
            "product_name": r.get("product_name") or "",
            "actual_production_quantity": remainder,
            "defect_qty": r.get("defect_qty") or 0,
            "production_lot_size": r.get("production_lot_size"),
            "lot_number": r.get("lot_number"),
            "cutting_length": r.get("cutting_length"),
            "chamfering_length": r.get("chamfering_length"),
            "developed_length": r.get("developed_length"),
            "production_time": r.get("production_time"),
            "material_name": r.get("material_name"),
            "management_code": r.get("management_code"),
            "has_sw_process": 1 if r.get("has_sw_process") else 0,
            "no_count": 1 if r.get("no_count") else 0,
            "remarks": r.get("remarks"),
        }
        ins = text("""
            INSERT INTO chamfering_management (
                cutting_management_id, production_month, production_day, production_line, chamfering_machine,
                production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
                production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
                has_sw_process, production_completed_check, no_count, remarks
            ) VALUES (
                :cutting_management_id, :production_month, :production_day, :production_line, :chamfering_machine,
                :production_order, :production_sequence, :product_cd, :product_name, :actual_production_quantity, :defect_qty,
                :production_lot_size, :lot_number, :cutting_length, :chamfering_length, :developed_length, :production_time, :material_name, :management_code,
                :has_sw_process, 0, :no_count, :remarks
            )
        """)
        await db.execute(ins, params)
        lid_res = await db.execute(text("SELECT LAST_INSERT_ID() AS new_id"))
        lid_row = lid_res.mappings().fetchone()
        new_id = int(lid_row["new_id"]) if lid_row and lid_row.get("new_id") is not None else None
        if new_id is not None:
            await db.execute(
                text("""
                    UPDATE chamfering_management
                    SET production_sequence = production_sequence + 1
                    WHERE chamfering_machine = :cm AND production_day = :nd AND id != :new_id
                """),
                {"cm": cm, "nd": next_day_date, "new_id": new_id},
            )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "順延しました（当日分を完了にし、残りを翌日へ追加しました）"}


@router.post("/plan/chamfering-management/{chamfering_id}/duplicate")
async def duplicate_chamfering_management(
    chamfering_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示1件を複製し、同一面取機・同一生産日内で直下に挿入。"""
    sel = text("""
        SELECT id, cutting_management_id, production_month, production_day, production_line, chamfering_machine,
               production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
               production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
               has_sw_process, production_completed_check, no_count, remarks
        FROM chamfering_management WHERE id = :mid
    """)
    res = await db.execute(sel, {"mid": chamfering_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="面取指示が見つかりません")
    r = dict(row)
    cm = (r.get("chamfering_machine") or "").strip()
    pd = r.get("production_day")
    if not cm:
        raise HTTPException(status_code=400, detail="面取機が空のため複製できません")
    if hasattr(pd, "isoformat"):
        pd_date = pd
    else:
        s = str(pd)[:10] if pd else ""
        if len(s) != 10:
            raise HTTPException(status_code=400, detail="生産日が不正です")
        pd_date = date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    current_seq = int(r.get("production_sequence") or 0)

    try:
        await db.execute(
            text("""
                UPDATE chamfering_management SET production_sequence = production_sequence + 1
                WHERE chamfering_machine = :cm AND production_day = :pd AND production_sequence > :seq
            """),
            {"cm": cm, "pd": pd_date, "seq": current_seq},
        )
        params = {
            "cutting_management_id": r.get("cutting_management_id"),
            "production_month": r.get("production_month"),
            "production_day": pd_date,
            "production_line": r.get("production_line") or "",
            "chamfering_machine": cm,
            "production_order": r.get("production_order"),
            "production_sequence": current_seq + 1,
            "product_cd": r.get("product_cd") or "",
            "product_name": r.get("product_name") or "",
            "actual_production_quantity": r.get("actual_production_quantity") or 0,
            "defect_qty": r.get("defect_qty") or 0,
            "production_lot_size": r.get("production_lot_size"),
            "lot_number": r.get("lot_number"),
            "cutting_length": r.get("cutting_length"),
            "chamfering_length": r.get("chamfering_length"),
            "developed_length": r.get("developed_length"),
            "production_time": r.get("production_time"),
            "material_name": r.get("material_name"),
            "management_code": r.get("management_code"),
            "has_sw_process": 1 if r.get("has_sw_process") else 0,
            "no_count": 1 if r.get("no_count") else 0,
            "remarks": r.get("remarks"),
        }
        ins = text("""
            INSERT INTO chamfering_management (
                cutting_management_id, production_month, production_day, production_line, chamfering_machine,
                production_order, production_sequence, product_cd, product_name, actual_production_quantity, defect_qty,
                production_lot_size, lot_number, cutting_length, chamfering_length, developed_length, production_time, material_name, management_code,
                has_sw_process, production_completed_check, no_count, remarks
            ) VALUES (
                :cutting_management_id, :production_month, :production_day, :production_line, :chamfering_machine,
                :production_order, :production_sequence, :product_cd, :product_name, :actual_production_quantity, :defect_qty,
                :production_lot_size, :lot_number, :cutting_length, :chamfering_length, :developed_length, :production_time, :material_name, :management_code,
                :has_sw_process, 0, :no_count, :remarks
            )
        """)
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "複製しました"}


class ReorderChamferingBody(BaseModel):
    """面取指示の生産順を変更するリクエスト（同一面取機・同一生産日内）"""
    chamfering_machine: str
    production_day: str  # YYYY-MM-DD
    ordered_ids: list[int]


@router.post("/plan/chamfering-management/reorder")
async def reorder_chamfering_management(
    body: ReorderChamferingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """面取指示の生産順（production_sequence）を、同一面取機・同一生産日内で指定した ID 順に更新する。"""
    chamfering_machine = (body.chamfering_machine or "").strip()
    if not chamfering_machine:
        raise HTTPException(status_code=400, detail="面取機を指定してください")
    production_day_s = (body.production_day or "").strip()[:10]
    if len(production_day_s) != 10:
        raise HTTPException(status_code=400, detail="生産日を指定してください（YYYY-MM-DD）")
    try:
        production_day_date = date(
            int(production_day_s[:4]), int(production_day_s[5:7]), int(production_day_s[8:10])
        )
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="生産日の形式が不正です")
    if not body.ordered_ids:
        return {"success": True, "message": "変更なし"}

    try:
        for idx, row_id in enumerate(body.ordered_ids):
            await db.execute(
                text("""
                    UPDATE chamfering_management
                    SET production_sequence = :production_sequence
                    WHERE id = :id AND chamfering_machine = :chamfering_machine AND production_day = :production_day
                """),
                {
                    "production_sequence": idx + 1,
                    "id": row_id,
                    "chamfering_machine": chamfering_machine,
                    "production_day": production_day_date,
                },
            )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "生産順を更新しました"}


class GenerateChamferingFromCuttingBody(BaseModel):
    """切断指示から面取指示を1件生成"""
    cutting_management_id: int


@router.post("/plan/chamfering-management/generate-from-cutting")
async def generate_chamfering_from_cutting(
    body: GenerateChamferingFromCuttingBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """切断指示1件から面取指示を1件生成する。cutting_management を読んで chamfering_management に挿入。"""
    sel = text("""
        SELECT id, production_month, production_day, production_line, priority_order,
               product_cd, product_name, actual_production_quantity, material_name, management_code
        FROM cutting_management
        WHERE id = :cid
    """)
    res = await db.execute(sel, {"cid": body.cutting_management_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="切断指示が見つかりません")
    row = dict(row)
    production_month_val = row.get("production_month")
    production_day_val = row.get("production_day")
    if production_month_val is not None and hasattr(production_month_val, "isoformat"):
        production_month_date = production_month_val.date() if hasattr(production_month_val, "date") else production_month_val
    else:
        s = str(production_month_val or "")[:10]
        production_month_date = date.fromisoformat(s) if len(s) == 10 else date.today()
    if production_day_val is not None and hasattr(production_day_val, "isoformat"):
        production_day_date = production_day_val.date() if hasattr(production_day_val, "date") else production_day_val
    else:
        s = str(production_day_val or "")[:10]
        production_day_date = date.fromisoformat(s) if len(s) == 10 else date.today()
    ins = text("""
        INSERT INTO chamfering_management (
            cutting_management_id, production_month, production_day, production_line, production_order,
            product_cd, product_name, actual_production_quantity, material_name, management_code, production_completed_check
        ) VALUES (
            :cutting_management_id, :production_month, :production_day, :production_line, :production_order,
            :product_cd, :product_name, :actual_production_quantity, :material_name, :management_code, 0
        )
    """)
    params = {
        "cutting_management_id": body.cutting_management_id,
        "production_month": production_month_date,
        "production_day": production_day_date,
        "production_line": row.get("production_line") or "",
        "production_order": row.get("priority_order"),
        "product_cd": row.get("product_cd") or "",
        "product_name": row.get("product_name") or "",
        "actual_production_quantity": row.get("actual_production_quantity") or 0,
        "material_name": row.get("material_name"),
        "management_code": row.get("management_code"),
    }
    try:
        await db.execute(ins, params)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "面取指示を生成しました"}


# ---------- カンバン発行（kanban_issuance）----------
@router.get("/plan/kanban-issuance/list")
async def get_kanban_issuance_list(
    process_type: Optional[str] = Query(None, description="工程 cutting / chamfering"),
    issue_date: Optional[str] = Query(None, description="発行日 YYYY-MM-DD"),
    production_day: Optional[str] = Query(None, description="生産日 YYYY-MM-DD"),
    status: Optional[str] = Query(None, description="状態 pending / issued / completed"),
    product_name: Optional[str] = Query(None, description="製品名（部分一致）"),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """カンバン発行一覧（instruction_plans と同様の項目を cutting/chamfering から結合）"""
    conditions = ["1=1"]
    params = {"limit": limit}
    if process_type and process_type.strip():
        params["process_type"] = process_type.strip()
        conditions.append("k.process_type = :process_type")
    if issue_date and len(issue_date.strip()) >= 10:
        try:
            params["issue_date"] = date.fromisoformat(issue_date.strip()[:10])
            conditions.append("k.issue_date = :issue_date")
        except ValueError:
            pass
    if production_day and len(production_day.strip()) >= 10:
        try:
            params["production_day"] = date.fromisoformat(production_day.strip()[:10])
            conditions.append("k.production_day = :production_day")
        except ValueError:
            pass
    if status and status.strip():
        params["status"] = status.strip().lower()
        conditions.append("k.status = :status")
    if product_name and product_name.strip():
        params["product_name"] = f"%{product_name.strip()}%"
        conditions.append("k.product_name LIKE :product_name")
    sql = text(f"""
        SELECT
            k.id, k.process_type, k.source_id, k.kanban_no, k.issue_date, k.status, k.created_at,
            k.product_cd, k.product_name, k.production_line, k.cutting_machine,
            k.material_name, k.standard_specification, k.management_code,
            k.start_date, k.end_date, k.planned_quantity, k.production_lot_size,
            k.actual_production_quantity, k.take_count,
            k.cutting_length, k.chamfering_length, k.developed_length,
            k.has_chamfering_process, k.lot_number, k.production_day
        FROM kanban_issuance k
        WHERE {" AND ".join(conditions)}
        ORDER BY
            k.production_day ASC,
            k.cutting_machine ASC,
            k.source_id ASC,
            k.id ASC
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, params)
    except Exception as e:
        msg = str(e).lower()
        if "kanban_issuance" in msg and ("doesn't exist" in msg or "not exist" in msg or "unknown table" in msg):
            raise HTTPException(
                status_code=503,
                detail="kanban_issuance テーブルが存在しません。マイグレーション 055_kanban_issuance.sql を実行してください。",
            ) from e
        raise
    rows = result.mappings().fetchall()

    def _v(row, k, default=None):
        val = row.get(k)
        if val is None:
            return default
        if hasattr(val, "isoformat"):
            return val.isoformat()[:10] if val else default
        return val

    data = [
        {
            "id": r.get("id"),
            "process_type": r.get("process_type"),
            "source_id": r.get("source_id"),
            "kanban_no": r.get("kanban_no"),
            "issue_date": _v(r, "issue_date"),
            "status": r.get("status"),
            "created_at": _v(dict(r), "created_at"),
            "product_cd": r.get("product_cd"),
            "product_name": r.get("product_name"),
            "production_line": r.get("production_line"),
            "cutting_machine": r.get("cutting_machine"),
            "material_name": r.get("material_name"),
            "standard_specification": r.get("standard_specification"),
            "management_code": r.get("management_code"),
            "start_date": _v(r, "start_date"),
            "end_date": _v(r, "end_date"),
            "planned_quantity": r.get("planned_quantity"),
            "production_lot_size": r.get("production_lot_size"),
            "actual_production_quantity": r.get("actual_production_quantity"),
            "take_count": r.get("take_count"),
            "cutting_length": float(r["cutting_length"]) if r.get("cutting_length") is not None else None,
            "chamfering_length": float(r["chamfering_length"]) if r.get("chamfering_length") is not None else None,
            "developed_length": float(r["developed_length"]) if r.get("developed_length") is not None else None,
            "has_chamfering_process": bool(r.get("has_chamfering_process")),
            "lot_number": r.get("lot_number"),
            "production_day": _v(r, "production_day"),
        }
        for r in rows
    ]
    return {"success": True, "data": data, "message": "OK"}


@router.get("/plan/kanban-issuance/product-names")
async def get_kanban_issuance_product_names(
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """カンバン発行一覧で使用されている製品名の一覧（製品名下拉用）"""
    sql = text("""
        SELECT DISTINCT product_name
        FROM kanban_issuance
        WHERE product_name IS NOT NULL AND TRIM(product_name) != ''
        ORDER BY product_name
        LIMIT :limit
    """)
    try:
        result = await db.execute(sql, {"limit": limit})
        rows = result.mappings().fetchall()
    except Exception as e:
        msg = str(e).lower()
        if "kanban_issuance" in msg:
            return {"success": True, "data": []}
        raise
    data = [r.get("product_name") for r in rows if r.get("product_name")]
    return {"success": True, "data": data}


class IssueKanbanBody(BaseModel):
    process_type: str  # cutting / chamfering
    source_id: int


class BatchIssueKanbanBody(BaseModel):
    kanban_ids: list[int]


class UpdateKanbanIssuanceBody(BaseModel):
    """カンバン発行1件の更新（全項目任意）"""
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    production_line: Optional[str] = None
    cutting_machine: Optional[str] = None
    material_name: Optional[str] = None
    standard_specification: Optional[str] = None
    management_code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    planned_quantity: Optional[int] = None
    production_lot_size: Optional[int] = None
    actual_production_quantity: Optional[int] = None
    take_count: Optional[int] = None
    cutting_length: Optional[float] = None
    chamfering_length: Optional[float] = None
    developed_length: Optional[float] = None
    has_chamfering_process: Optional[bool] = None
    lot_number: Optional[str] = None
    production_day: Optional[str] = None


@router.patch("/plan/kanban-issuance/{kanban_id:int}")
async def update_kanban_issuance(
    kanban_id: int,
    body: UpdateKanbanIssuanceBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """カンバン発行1件のデータを更新する。"""
    res = await db.execute(text("SELECT id FROM kanban_issuance WHERE id = :kid"), {"kid": kanban_id})
    if not res.mappings().fetchone():
        raise HTTPException(status_code=404, detail="カンバンが見つかりません")
    body_dict = body.model_dump(exclude_unset=True)
    if not body_dict:
        return {"success": True, "message": "変更なし"}
    set_parts = []
    params = {"kid": kanban_id}
    date_fields = ("start_date", "end_date", "production_day")
    for k, v in body_dict.items():
        if k in date_fields and v is not None:
            try:
                params[k] = date.fromisoformat(str(v).strip()[:10])
            except ValueError:
                continue
        else:
            params[k] = v
        set_parts.append(f"`{k}` = :{k}")
    if not set_parts:
        return {"success": True, "message": "変更なし"}
    if "has_chamfering_process" in params and isinstance(params["has_chamfering_process"], bool):
        params["has_chamfering_process"] = 1 if params["has_chamfering_process"] else 0
    sql = text(f"UPDATE kanban_issuance SET {', '.join(set_parts)} WHERE id = :kid")
    await db.execute(sql, params)
    await db.commit()
    return {"success": True, "message": "更新しました"}


@router.post("/plan/kanban-issuance/issue")
async def issue_kanban(
    body: IssueKanbanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """カンバン発行を1件登録。kanban_no は自動採番（process_type + source_id + 日時等）でよいが、ここでは簡易で source_id ベース。"""
    pt = (body.process_type or "").strip()
    if pt not in ("cutting", "chamfering"):
        raise HTTPException(status_code=400, detail="process_type は cutting または chamfering を指定してください")
    today = date.today()
    kanban_no = f"{pt.upper()}-{body.source_id}-{today.isoformat().replace('-', '')}"
    ins = text("""
        INSERT INTO kanban_issuance (process_type, source_id, kanban_no, issue_date, status)
        VALUES (:process_type, :source_id, :kanban_no, :issue_date, 'issued')
    """)
    try:
        await db.execute(ins, {
            "process_type": pt,
            "source_id": body.source_id,
            "kanban_no": kanban_no,
            "issue_date": today,
        })
        await db.commit()
    except Exception as e:
        await db.rollback()
        msg = str(e).lower()
        if "kanban_issuance" in msg:
            raise HTTPException(status_code=503, detail="kanban_issuance テーブルが存在しません。") from e
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"success": True, "message": "カンバンを発行しました", "kanban_no": kanban_no}


@router.post("/plan/kanban-issuance/{kanban_id:int}/issue")
async def issue_pending_kanban(
    kanban_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """待発行（pending）のカンバンを発行する。kanban_no と issue_date を設定し status を issued に更新。"""
    sel = text("SELECT id, process_type, source_id, status FROM kanban_issuance WHERE id = :kid")
    res = await db.execute(sel, {"kid": kanban_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="カンバンが見つかりません")
    row = dict(row)
    if (row.get("status") or "").strip().lower() != "pending":
        raise HTTPException(status_code=400, detail="待発行のカンバンのみ発行できます")
    today = date.today()
    pt = (row.get("process_type") or "cutting").strip()
    src_id = row.get("source_id") or 0
    kanban_no = f"{pt.upper()}-{src_id}-{today.isoformat().replace('-', '')}"
    upd = text("""
        UPDATE kanban_issuance SET kanban_no = :kanban_no, issue_date = :issue_date, status = 'issued'
        WHERE id = :kid
    """)
    await db.execute(upd, {"kanban_no": kanban_no, "issue_date": today, "kid": kanban_id})
    await db.commit()
    return {"success": True, "message": "カンバンを発行しました", "kanban_no": kanban_no}


@router.post("/plan/kanban-issuance/{kanban_id:int}/reissue")
async def reissue_kanban(
    kanban_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """発行済のカンバンを再発行する（現場で紛失した場合など）。新しい kanban_no と issue_date で更新。"""
    sel = text("SELECT id, process_type, source_id, status FROM kanban_issuance WHERE id = :kid")
    res = await db.execute(sel, {"kid": kanban_id})
    row = res.mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="カンバンが見つかりません")
    row = dict(row)
    status = (row.get("status") or "").strip().lower()
    if status not in ("pending", "issued"):
        raise HTTPException(
            status_code=400,
            detail="待発行または発行済のカンバンのみ再発行できます（完了済は再発行不可）",
        )
    today = date.today()
    pt = (row.get("process_type") or "cutting").strip()
    src_id = row.get("source_id") or 0
    kanban_no = f"{pt.upper()}-{src_id}-{today.isoformat().replace('-', '')}"
    upd = text("""
        UPDATE kanban_issuance SET kanban_no = :kanban_no, issue_date = :issue_date, status = 'issued'
        WHERE id = :kid
    """)
    await db.execute(upd, {"kanban_no": kanban_no, "issue_date": today, "kid": kanban_id})
    await db.commit()
    return {"success": True, "message": "カンバンを再発行しました", "kanban_no": kanban_no}


@router.post("/plan/kanban-issuance/sync-production-day")
async def sync_kanban_production_day(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """kanban_issuance の production_day を source_id で cutting_management / chamfering_management から取得して更新する。"""
    # process_type='cutting' → source_id = cutting_management.id
    upd_cutting = text("""
        UPDATE kanban_issuance k
        INNER JOIN cutting_management c ON k.source_id = c.id AND k.process_type = 'cutting'
        SET k.production_day = c.production_day
    """)
    # process_type='chamfering' → source_id = chamfering_management.id, production_day は chamfering_management から
    upd_chamfering = text("""
        UPDATE kanban_issuance k
        INNER JOIN chamfering_management ch ON k.source_id = ch.id AND k.process_type = 'chamfering'
        SET k.production_day = ch.production_day
    """)
    try:
        r1 = await db.execute(upd_cutting)
        r2 = await db.execute(upd_chamfering)
        await db.commit()
        # rowcount は DB によっては UPDATE 件数が返らない場合がある
        updated = getattr(r1, "rowcount", None) or 0
        updated += getattr(r2, "rowcount", None) or 0
        return {"success": True, "message": "生産日を更新しました", "updated": updated}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/plan/kanban-issuance/batch-issue")
async def batch_issue_pending_kanban(
    body: BatchIssueKanbanBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """待発行（pending）・発行済（issued）のカンバンを一括発行する。発行済は再発行扱いで新 kanban_no を付与。"""
    if not body.kanban_ids:
        return {"success": True, "message": "発行対象がありません", "issued": 0, "skipped": 0, "errors": [], "issued_items": []}
    today = date.today()
    sel = text("SELECT id, process_type, source_id, status FROM kanban_issuance WHERE id = :kid")
    upd = text("""
        UPDATE kanban_issuance SET kanban_no = :kanban_no, issue_date = :issue_date, status = 'issued'
        WHERE id = :kid
    """)
    issued = 0
    skipped = 0
    errors = []
    issued_items: list[dict] = []
    for kid in body.kanban_ids:
        res = await db.execute(sel, {"kid": kid})
        row = res.mappings().fetchone()
        if not row:
            errors.append(f"id={kid}: カンバンが見つかりません")
            continue
        row = dict(row)
        status = (row.get("status") or "").strip().lower()
        if status not in ("pending", "issued"):
            skipped += 1
            continue
        pt = (row.get("process_type") or "cutting").strip()
        src_id = row.get("source_id") or 0
        kanban_no = f"{pt.upper()}-{src_id}-{today.isoformat().replace('-', '')}"
        try:
            await db.execute(upd, {"kanban_no": kanban_no, "issue_date": today, "kid": kid})
            issued += 1
            issued_items.append({"id": kid, "kanban_no": kanban_no})
        except Exception as e:
            errors.append(f"id={kid}: {e}")
    await db.commit()
    return {
        "success": True,
        "message": f"一括発行完了（発行: {issued} 件、スキップ: {skipped} 件）",
        "issued": issued,
        "skipped": skipped,
        "errors": errors,
        "issued_items": issued_items,
    }


@router.post("/plan/batch/sync-lengths-from-products")
async def sync_batch_lengths_from_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    products の cut_length / chamfer_length / developed_length を、同一 product_cd の
    instruction_plans・cutting_management・chamfering_plans・chamfering_management・
    kanban_issuance（product_cd がある行）へ反映する。
    chamfering_plans / chamfering_management に cutting_length・developed_length が無い環境
    （マイグレーション 208 未実行）では、chamfering_length のみ同期する。
    """
    cp_has_cut = await _table_has_column(db, "chamfering_plans", "cutting_length")
    cm_has_cut = await _table_has_column(db, "chamfering_management", "cutting_length")
    kanban_has_lengths = await _table_has_column(db, "kanban_issuance", "cutting_length")

    # products 列が utf8mb4_0900_ai_ci、他テーブルが utf8mb4_unicode_ci の環境で JOIN 時に 1267 を避ける
    _pc = "p.product_cd COLLATE utf8mb4_unicode_ci = {alias}.product_cd COLLATE utf8mb4_unicode_ci"

    stmts: list[tuple[str, object]] = [
        (
            "instruction_plans",
            text(f"""
                UPDATE instruction_plans ip
                INNER JOIN products p ON {_pc.format(alias="ip")}
                SET ip.cutting_length = p.cut_length,
                    ip.chamfering_length = p.chamfer_length,
                    ip.developed_length = p.developed_length
            """),
        ),
        (
            "cutting_management",
            text(f"""
                UPDATE cutting_management cm
                INNER JOIN products p ON {_pc.format(alias="cm")}
                SET cm.cutting_length = p.cut_length,
                    cm.chamfering_length = p.chamfer_length,
                    cm.developed_length = p.developed_length
            """),
        ),
    ]
    if cp_has_cut:
        stmts.append(
            (
                "chamfering_plans",
                text(f"""
                    UPDATE chamfering_plans cp
                    INNER JOIN products p ON {_pc.format(alias="cp")}
                    SET cp.cutting_length = p.cut_length,
                        cp.chamfering_length = p.chamfer_length,
                        cp.developed_length = p.developed_length
                """),
            )
        )
    else:
        stmts.append(
            (
                "chamfering_plans",
                text(f"""
                    UPDATE chamfering_plans cp
                    INNER JOIN products p ON {_pc.format(alias="cp")}
                    SET cp.chamfering_length = p.chamfer_length
                """),
            )
        )
    if cm_has_cut:
        stmts.append(
            (
                "chamfering_management",
                text(f"""
                    UPDATE chamfering_management ch
                    INNER JOIN products p ON {_pc.format(alias="ch")}
                    SET ch.cutting_length = p.cut_length,
                        ch.chamfering_length = p.chamfer_length,
                        ch.developed_length = p.developed_length
                """),
            )
        )
    else:
        stmts.append(
            (
                "chamfering_management",
                text(f"""
                    UPDATE chamfering_management ch
                    INNER JOIN products p ON {_pc.format(alias="ch")}
                    SET ch.chamfering_length = p.chamfer_length
                """),
            )
        )
    if kanban_has_lengths:
        stmts.append(
            (
                "kanban_issuance",
                text(f"""
                    UPDATE kanban_issuance k
                    INNER JOIN products p ON {_pc.format(alias="k")}
                    SET k.cutting_length = p.cut_length,
                        k.chamfering_length = p.chamfer_length,
                        k.developed_length = p.developed_length
                    WHERE k.product_cd IS NOT NULL AND TRIM(k.product_cd) != ''
                """),
            )
        )

    counts: dict[str, int] = {}
    notes: list[str] = []
    if not cp_has_cut or not cm_has_cut:
        notes.append(
            "chamfering_plans / chamfering_management はマイグレーション 208 未適用のため、"
            "面取長（chamfering_length）のみ同期しました。切断長・展開長も反映する場合は 208_chamfering_plans_management_length_fields.sql を実行してください。"
        )
    if not kanban_has_lengths:
        notes.append(
            "kanban_issuance に寸法列が無いためスキップしました（マイグレーション 067 等を確認してください）。"
        )

    try:
        for name, sql in stmts:
            res = await db.execute(sql)
            counts[name] = int(res.rowcount or 0)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("sync-lengths-from-products failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"同期に失敗しました: {e!s}",
        ) from e
    total = sum(counts.values())
    msg = f"製品マスタの寸法を反映しました（更新行数合計: {total}）"
    if notes:
        msg += " " + " ".join(notes)
    return {
        "success": True,
        "message": msg,
        "data": {"counts": counts, "notes": notes},
    }


@router.post("/plan/batch/generate-from-schedule")
async def generate_cutting_plans_from_schedule(
    body: GenerateFromScheduleBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定月でロット生成: production_plan_schedules の file_name に生産月を含み、
    '溶接' を含まない行を取得し、material_lot_count 回分ループして
    instruction_plans に挿入する。
    products / materials を product_name / material_name で結合して
    product_cd, lot_size, cut_length 等を取得する。
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        production_month, month_label = _parse_month(body.month)
        pattern = f"%{month_label}%"

        # 1) production_plan_schedules から取得（file_name に生産月を含む、'溶接' を除く）
        sql_schedules = text("""
            SELECT machine_name, product_name, production_order, planned_quantity,
                   production_start_date, production_end_date, material_lot_count, material_name
            FROM production_plan_schedules
            WHERE file_name LIKE :pattern
              AND file_name NOT LIKE '%溶接%'
            ORDER BY machine_name, product_name, production_order
        """)
        result = await db.execute(sql_schedules, {"pattern": pattern})
        rows = result.mappings().fetchall()

        if not rows:
            return {
                "success": True,
                "data": {"inserted": 0},
                "message": f"該当する計画データがありません（file_name に「{month_label}」を含み「溶接」を含まないもの）",
            }

        # 2) products を product_name で取得（同一製品名で複数ある場合は product_cd 末尾が '1' のものを優先）
        product_names = list({str(r.get("product_name") or "").strip() for r in rows if r.get("product_name")})
        product_map = {}
        if product_names:
            placeholders = ", ".join([f":p{i}" for i in range(len(product_names))])
            sql_products = text(f"""
                SELECT product_cd, product_name, lot_size, cut_length, chamfer_length,
                       developed_length, scrap_length, take_count
                FROM products
                WHERE product_name IN ({placeholders})
            """)
            params_products = {f"p{i}": name for i, name in enumerate(product_names)}
            res_p = await db.execute(sql_products, params_products)
            for r in res_p.mappings().fetchall():
                pname = (r.get("product_name") or "").strip()
                if pname not in product_map:
                    product_map[pname] = dict(r)
                else:
                    cd = (r.get("product_cd") or "").strip()
                    if cd and str(cd)[-1:] == "1":
                        product_map[pname] = dict(r)

        # 3) product_route_steps で KT01/KT02/KT03 を取得（has_cutting / has_chamfering / has_sw）
        product_cds = list({(v.get("product_cd") or "").strip() for v in product_map.values() if (v.get("product_cd") or "").strip()})
        route_step_map = {}
        if product_cds:
            placeholders = ", ".join([f":c{i}" for i in range(len(product_cds))])
            sql_steps = text(f"""
                SELECT product_cd, process_cd FROM product_route_steps
                WHERE product_cd IN ({placeholders}) AND process_cd IN ('KT01', 'KT02', 'KT03')
            """)
            params_steps = {f"c{i}": cd for i, cd in enumerate(product_cds)}
            res_s = await db.execute(sql_steps, params_steps)
            for r in res_s.mappings().fetchall():
                cd = (r.get("product_cd") or "").strip()
                proc = (r.get("process_cd") or "").strip()
                if cd not in route_step_map:
                    route_step_map[cd] = set()
                route_step_map[cd].add(proc)

        # 4) materials を material_name で取得（standard_spec -> standard_specification, supplier_cd -> material_manufacturer）
        material_names = list({str(r.get("material_name") or "").strip() for r in rows if r.get("material_name")})
        material_map = {}
        if material_names:
            placeholders = ", ".join([f":m{i}" for i in range(len(material_names))])
            sql_materials = text(f"""
                SELECT material_name, standard_spec, supplier_cd
                FROM materials
                WHERE material_name IN ({placeholders})
            """)
            params_materials = {f"m{i}": name for i, name in enumerate(material_names)}
            res_m = await db.execute(sql_materials, params_materials)
            for r in res_m.mappings().fetchall():
                material_map[(r.get("material_name") or "").strip()] = dict(r)

        # 5) 同一生産月の既存データを削除
        await db.execute(
            text("DELETE FROM instruction_plans WHERE production_month = :pm"),
            {"pm": production_month},
        )

        # 6) 行ごとに material_lot_count 回ループして挿入（lot_number は 1, 2, ... material_lot_count）
        inserted = 0
        for r in rows:
            row_dict = dict(r) if hasattr(r, "keys") else r
            machine_name = (row_dict.get("machine_name") or "").strip() or ""
            product_name = (row_dict.get("product_name") or "").strip() or ""
            production_order = _to_int(row_dict.get("production_order"))
            planned_quantity = _to_int(row_dict.get("planned_quantity")) or 0
            start_d = row_dict.get("production_start_date")
            end_d = row_dict.get("production_end_date")
            lot_count = _to_int(row_dict.get("material_lot_count")) or 1
            if lot_count < 1:
                lot_count = 1
            material_name = (row_dict.get("material_name") or "").strip() or ""

            prod = product_map.get(product_name) or {}
            product_cd = (prod.get("product_cd") or "").strip() or ""
            actual_qty = _to_int(prod.get("lot_size")) or 0
            cut_len = _to_decimal_val(prod.get("cut_length"))
            chamfer_len = _to_decimal_val(prod.get("chamfer_length"))
            developed_len = _to_decimal_val(prod.get("developed_length"))
            scrap_len = _to_decimal_val(prod.get("scrap_length"))
            take_count = _to_int(prod.get("take_count"))

            steps = route_step_map.get(product_cd) or set()
            has_cutting = 1 if "KT01" in steps else 0
            has_chamfering = 1 if "KT02" in steps else 0
            has_sw = 1 if "KT03" in steps else 0

            mat = material_map.get(material_name) or {}
            standard_spec = (mat.get("standard_spec") or "").strip() or None
            supplier_cd = (mat.get("supplier_cd") or "").strip() or None

            start_ts = None
            if start_d:
                if hasattr(start_d, "year"):
                    start_ts = datetime(start_d.year, start_d.month, start_d.day)
                else:
                    start_ts = start_d
            end_ts = None
            if end_d:
                if hasattr(end_d, "year"):
                    end_ts = datetime(end_d.year, end_d.month, end_d.day)
                else:
                    end_ts = end_d

            for lot_idx in range(1, lot_count + 1):
                lot_number = str(lot_idx)
                await db.execute(
                    text("""
                        INSERT INTO instruction_plans (
                            production_month, production_line, priority_order, product_cd, product_name,
                            planned_quantity, start_date, end_date, production_lot_size, lot_number,
                            is_cutting_instructed, has_chamfering_process, has_sw_process,
                            actual_production_quantity, take_count, cutting_length, chamfering_length,
                            developed_length, scrap_length, material_name, material_manufacturer, standard_specification
                        ) VALUES (
                            :production_month, :production_line, :priority_order, :product_cd, :product_name,
                            :planned_quantity, :start_date, :end_date, :production_lot_size, :lot_number,
                            :is_cutting_instructed, :has_chamfering_process, :has_sw_process,
                            :actual_production_quantity, :take_count, :cutting_length, :chamfering_length,
                            :developed_length, :scrap_length, :material_name, :material_manufacturer, :standard_specification
                        )
                    """),
                    {
                        "production_month": production_month,
                        "production_line": machine_name,
                        "priority_order": production_order,
                        "product_cd": product_cd,
                        "product_name": product_name,
                        "planned_quantity": planned_quantity,
                        "start_date": start_ts,
                        "end_date": end_ts,
                        "production_lot_size": lot_count,
                        "lot_number": lot_number,
                        "is_cutting_instructed": has_cutting,
                        "has_chamfering_process": has_chamfering,
                        "has_sw_process": has_sw,
                        "actual_production_quantity": actual_qty,
                        "take_count": take_count,
                        "cutting_length": cut_len,
                        "chamfering_length": chamfer_len,
                        "developed_length": developed_len,
                        "scrap_length": scrap_len,
                        "material_name": material_name or None,
                        "material_manufacturer": supplier_cd,
                        "standard_specification": standard_spec,
                    },
                )
                inserted += 1

        return {
            "success": True,
            "data": {"inserted": inserted},
            "message": f"切断指示計画を {inserted} 件生成しました（生産月: {body.month}）",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("generate-from-schedule failed")
        msg = str(e)
        if "instruction_plans" in msg and ("doesn't exist" in msg or "not exist" in msg or "Unknown table" in msg):
            msg = "instruction_plans テーブルが存在しません。マイグレーション 052_cutting_instruction_plans.sql を実行してください。"
        raise HTTPException(status_code=500, detail=msg)

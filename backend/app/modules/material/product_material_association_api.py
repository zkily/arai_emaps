"""
製品ー材料照会 API（kanban_issuance ベース）
GET  /api/material/product-material-association          一覧取得（ページネーション・フィルタ）
GET  /api/material/product-material-association/products 製品名ドロップダウン用
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

router = APIRouter()

# 看板発行日がこの日より前の行は一覧から除外（NULL は残す）
MIN_KANBAN_ISSUE_DATE = date(2026, 4, 1)

_TABLE_MISSING_DETAIL = (
    "kanban_issuance テーブルが存在しません。"
    "マイグレーション 055_kanban_issuance.sql を実行してください。"
)


def _is_table_missing(e: Exception) -> bool:
    msg = str(e).lower()
    return "kanban_issuance" in msg and (
        "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
    )


# kanban の管理コードに対応する切断ログの log_date（一覧の「切断開始日付」と同一ロジック）
_CUTTING_LOG_DATE_SQL = """(
    SELECT m.log_date
    FROM material_cutting_logs m
    WHERE k.management_code IS NOT NULL AND k.management_code <> ''
        AND m.management_code = k.management_code
    ORDER BY m.log_date DESC, m.log_time DESC, m.id DESC
    LIMIT 1
)"""


@router.get("")
async def list_product_material_association(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=20000),
    keyword: Optional[str] = Query(None),
    product_cd: Optional[str] = Query(None),
    management_code: Optional[str] = Query(None),
    material_name: Optional[str] = Query(None),
    process_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None, description="切断開始日付（material_cutting_logs.log_date）開始 YYYY-MM-DD"),
    endDate: Optional[str] = Query(None, description="切断開始日付 終了 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品ー材料照会（kanban_issuance 明細一覧）"""
    conditions = ["1=1"]
    params: dict = {"min_issue_date": MIN_KANBAN_ISSUE_DATE}
    conditions.append("(k.issue_date IS NULL OR k.issue_date >= :min_issue_date)")

    if keyword and keyword.strip():
        params["kw"] = f"%{keyword.strip()}%"
        conditions.append(
            "(k.product_cd LIKE :kw OR k.product_name LIKE :kw"
            " OR k.material_name LIKE :kw OR k.management_code LIKE :kw"
            " OR k.kanban_no LIKE :kw)"
        )
    if product_cd and product_cd.strip():
        params["product_cd"] = product_cd.strip()
        conditions.append("k.product_cd = :product_cd")
    if management_code and management_code.strip():
        params["mgmt"] = f"%{management_code.strip()}%"
        conditions.append("k.management_code LIKE :mgmt")
    if material_name and material_name.strip():
        params["mat"] = f"%{material_name.strip()}%"
        conditions.append("k.material_name LIKE :mat")
    if process_type and process_type.strip():
        params["pt"] = process_type.strip()
        conditions.append("k.process_type = :pt")
    if status and status.strip():
        params["st"] = status.strip().lower()
        conditions.append("k.status = :st")
    if startDate and len(startDate.strip()) >= 10:
        try:
            params["sd"] = date.fromisoformat(startDate.strip()[:10])
            conditions.append(f"{_CUTTING_LOG_DATE_SQL} >= :sd")
        except ValueError:
            pass
    if endDate and len(endDate.strip()) >= 10:
        try:
            params["ed"] = date.fromisoformat(endDate.strip()[:10])
            conditions.append(f"{_CUTTING_LOG_DATE_SQL} <= :ed")
        except ValueError:
            pass

    where = " AND ".join(conditions)

    count_sql = text(f"SELECT COUNT(*) FROM kanban_issuance k WHERE {where}")
    # 管理コード → material_cutting_logs（最新1件の manufacture_no）→ material_logs（manufacture_no で最新1件）
    data_sql = text(f"""
        SELECT
            k.id, k.process_type, k.source_id, k.kanban_no,
            k.issue_date, k.status, k.created_at,
            k.product_cd, k.product_name, k.production_line,
            k.cutting_machine, k.material_name, k.standard_specification,
            k.management_code, k.start_date, k.end_date,
            k.planned_quantity, k.production_lot_size,
            k.actual_production_quantity, k.take_count,
            k.cutting_length, k.chamfering_length, k.developed_length,
            k.has_chamfering_process, k.lot_number, k.production_day,
            (
                SELECT m.manufacture_no
                FROM material_cutting_logs m
                WHERE k.management_code IS NOT NULL AND k.management_code <> ''
                    AND m.management_code = k.management_code
                ORDER BY m.log_date DESC, m.log_time DESC, m.id DESC
                LIMIT 1
            ) AS cutting_log_manufacture_no,
            (
                SELECT m.log_date
                FROM material_cutting_logs m
                WHERE k.management_code IS NOT NULL AND k.management_code <> ''
                    AND m.management_code = k.management_code
                ORDER BY m.log_date DESC, m.log_time DESC, m.id DESC
                LIMIT 1
            ) AS cutting_log_date,
            (
                SELECT m.log_time
                FROM material_cutting_logs m
                WHERE k.management_code IS NOT NULL AND k.management_code <> ''
                    AND m.management_code = k.management_code
                ORDER BY m.log_date DESC, m.log_time DESC, m.id DESC
                LIMIT 1
            ) AS cutting_log_time,
            (
                SELECT ml.manufacture_date
                FROM material_logs ml
                WHERE ml.manufacture_no = (
                    SELECT m.manufacture_no
                    FROM material_cutting_logs m
                    WHERE k.management_code IS NOT NULL AND k.management_code <> ''
                        AND m.management_code = k.management_code
                    ORDER BY m.log_date DESC, m.log_time DESC, m.id DESC
                    LIMIT 1
                )
                ORDER BY ml.log_date DESC, ml.id DESC
                LIMIT 1
            ) AS material_log_manufacture_date,
            (
                SELECT ml.supplier
                FROM material_logs ml
                WHERE ml.manufacture_no = (
                    SELECT m.manufacture_no
                    FROM material_cutting_logs m
                    WHERE k.management_code IS NOT NULL AND k.management_code <> ''
                        AND m.management_code = k.management_code
                    ORDER BY m.log_date DESC, m.log_time DESC, m.id DESC
                    LIMIT 1
                )
                ORDER BY ml.log_date DESC, ml.id DESC
                LIMIT 1
            ) AS material_log_supplier
        FROM kanban_issuance k
        WHERE {where}
        ORDER BY
            (cutting_log_date IS NULL) ASC,
            cutting_log_date ASC,
            (cutting_log_time IS NULL) ASC,
            cutting_log_time ASC,
            k.id ASC
        LIMIT :lim OFFSET :off
    """)

    params["lim"] = pageSize
    params["off"] = (page - 1) * pageSize

    try:
        total_result = await db.execute(count_sql, params)
        total = total_result.scalar() or 0

        result = await db.execute(data_sql, params)
        rows = result.mappings().fetchall()
    except Exception as e:
        if _is_table_missing(e):
            raise HTTPException(status_code=503, detail=_TABLE_MISSING_DETAIL) from e
        msg = str(e).lower()
        if "material_cutting_logs" in msg and (
            "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
        ):
            raise HTTPException(
                status_code=503,
                detail="material_cutting_logs テーブルが存在しません。",
            ) from e
        if "material_logs" in msg and (
            "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
        ):
            raise HTTPException(
                status_code=503,
                detail="material_logs テーブルが存在しません。",
            ) from e
        if "material_cutting_logs" in msg and (
            "manufacture_no" in msg and ("unknown column" in msg or "doesn't exist" in msg)
        ):
            raise HTTPException(
                status_code=503,
                detail="material_cutting_logs に manufacture_no 列がありません。マイグレーション 213 を実行してください。",
            ) from e
        raise

    def _v(row, key):
        val = row.get(key)
        if val is None:
            return None
        if hasattr(val, "isoformat"):
            return val.isoformat()[:10]
        return val

    data = [
        {
            "id": r.get("id"),
            "process_type": r.get("process_type"),
            "source_id": r.get("source_id"),
            "kanban_no": r.get("kanban_no"),
            "issue_date": _v(r, "issue_date"),
            "status": r.get("status"),
            "created_at": _v(r, "created_at"),
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
            "cutting_log_manufacture_no": (
                str(r["cutting_log_manufacture_no"])
                if r.get("cutting_log_manufacture_no") is not None
                else None
            ),
            "cutting_log_date": _v(r, "cutting_log_date"),
            "cutting_log_time": (
                str(r["cutting_log_time"]) if r.get("cutting_log_time") is not None else None
            ),
            "material_log_manufacture_date": _v(r, "material_log_manufacture_date"),
            "material_log_supplier": r.get("material_log_supplier"),
        }
        for r in rows
    ]

    return {"success": True, "data": {"list": data, "total": total}}


@router.get("/products")
async def get_product_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品一覧（kanban_issuance の product_cd / product_name 去重、ドロップダウン用）"""
    sql = text("""
        SELECT DISTINCT product_cd, product_name
        FROM kanban_issuance
        WHERE product_cd IS NOT NULL AND product_cd <> ''
          AND (issue_date IS NULL OR issue_date >= :min_issue_date)
        ORDER BY product_cd
    """)
    try:
        result = await db.execute(sql, {"min_issue_date": MIN_KANBAN_ISSUE_DATE})
        rows = result.mappings().fetchall()
    except Exception as e:
        if _is_table_missing(e):
            raise HTTPException(status_code=503, detail=_TABLE_MISSING_DETAIL) from e
        raise

    return {
        "success": True,
        "data": [
            {"product_cd": r["product_cd"], "product_name": r.get("product_name")}
            for r in rows
        ],
    }

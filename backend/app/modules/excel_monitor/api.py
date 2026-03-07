"""
Excel監視・計画データ API
成型指示画面: plan-data は production_plan_updates を読み、能率・段取は equipment_efficiency と結合。
"""
from decimal import Decimal
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

router = APIRouter()


def _row_to_plan_record(row: Any) -> dict:
    """DB行を計画データ1件の辞書に変換（frontend の product_name, quantity, efficiency_rate, setup_time 等）"""
    def _val(key: str, default=None):
        v = row.get(key) if hasattr(row, "get") else getattr(row, key, None)
        if v is None:
            return default
        if isinstance(v, Decimal):
            return float(v) if v is not None else default
        return v

    plan_date = _val("plan_date")
    if hasattr(plan_date, "isoformat"):
        plan_date = plan_date.isoformat()[:10] if plan_date else None
    return {
        "id": _val("id"),
        "plan_date": plan_date,
        "quantity": _val("quantity", 0),
        "machine_name": _val("machine_name"),
        "machine_cd": _val("machine_cd"),
        "process_name": _val("process_name"),
        "operator": _val("operator"),
        "product_name": _val("product_name"),
        "product_cd": _val("product_cd"),
        "efficiency_rate": _val("efficiency_rate"),
        "setup_time": _val("setup_time"),
    }


@router.get("/plan-data")
async def get_plan_data(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    processName: Optional[str] = Query(None),
    machineName: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    計画データ取得。production_plan_updates を読み、equipment_efficiency で能率・段取時間を補完。
    """
    if not startDate or not endDate:
        return {
            "success": True,
            "data": {"records": [], "total": 0},
            "message": "OK",
        }
    # production_plan_updates LEFT JOIN equipment_efficiency (machine_cd + product_cd)
    sql = text("""
        SELECT ppu.id, ppu.plan_date, ppu.quantity, ppu.machine_name, ppu.machine_cd,
               ppu.process_name, ppu.operator, ppu.product_name, ppu.product_cd,
               ee.efficiency_rate, ee.step_time AS setup_time
        FROM production_plan_updates ppu
        LEFT JOIN equipment_efficiency ee
          ON ppu.machine_cd = ee.machine_cd AND ppu.product_cd = ee.product_cd
        WHERE ppu.plan_date BETWEEN :start_date AND :end_date
          AND (:process_name IS NULL OR ppu.process_name = :process_name)
          AND (:machine_name IS NULL OR ppu.machine_name = :machine_name)
          AND (
            :keyword IS NULL OR :keyword = ''
            OR ppu.product_name LIKE :kw_like
            OR ppu.product_cd LIKE :kw_like
          )
        ORDER BY ppu.plan_date, ppu.machine_name, ppu.product_name
        LIMIT :limit OFFSET :offset
    """)
    kw = keyword.strip() if keyword else ""
    offset = (page - 1) * limit
    params = {
        "start_date": startDate,
        "end_date": endDate,
        "process_name": processName or None,
        "machine_name": machineName or None,
        "keyword": kw or None,
        "kw_like": f"%{kw}%" if kw else "%",
        "limit": limit,
        "offset": offset,
    }
    # 総件数
    count_sql = text("""
        SELECT COUNT(*) AS cnt FROM production_plan_updates ppu
        WHERE ppu.plan_date BETWEEN :start_date AND :end_date
          AND (:process_name IS NULL OR ppu.process_name = :process_name)
          AND (:machine_name IS NULL OR ppu.machine_name = :machine_name)
          AND (
            :keyword IS NULL OR :keyword = ''
            OR ppu.product_name LIKE :kw_like
            OR ppu.product_cd LIKE :kw_like
          )
    """)
    count_result = await db.execute(count_sql, {k: v for k, v in params.items() if k in ("start_date", "end_date", "process_name", "machine_name", "keyword", "kw_like")})
    total = (count_result.scalar() or 0) or 0
    if hasattr(total, "__int__"):
        total = int(total)
    result = await db.execute(sql, params)
    rows = result.mappings().fetchall()
    records = [_row_to_plan_record(dict(r)) for r in rows]

    return {
        "success": True,
        "data": {"records": records, "total": total},
        "message": "OK",
    }


@router.put("/plan-data/remarks")
async def update_plan_data_remarks(
    body: dict[str, Any] = Body(...),
    current_user: User = Depends(verify_token_and_get_user),
):
    """備考更新（スタブ）"""
    return {"success": True, "message": "OK"}


@router.post("/update-efficiency-and-setup-time")
async def update_efficiency_and_setup_time(
    body: dict[str, Any] = Body(...),
    current_user: User = Depends(verify_token_and_get_user),
):
    """能率・段取時間一括更新（スタブ）"""
    return {
        "success": True,
        "data": {
            "machineCdUpdated": 0,
            "efficiencyUpdated": 0,
            "duration": "0s",
        },
        "message": "OK",
    }

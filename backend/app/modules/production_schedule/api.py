"""
生産状況・スケジュール API
- GET /processing-status: production_plan_schedules を file_name でフィルタして返す
- GET /schedule: 設備運行時間スロット（現状スタブ、必要に応じて production_plan_schedules 等から導出可能）
"""
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

router = APIRouter()


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

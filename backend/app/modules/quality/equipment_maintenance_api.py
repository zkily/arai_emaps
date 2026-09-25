"""設備保全管理 API（品質管理 > 設備関係）

GET    /api/quality/equipment-maintenance/equipments
POST   /api/quality/equipment-maintenance/equipments
PUT    /api/quality/equipment-maintenance/equipments/{id}
DELETE /api/quality/equipment-maintenance/equipments/{id}
POST   /api/quality/equipment-maintenance/equipments/import-machines
GET    /api/quality/equipment-maintenance/records
POST   /api/quality/equipment-maintenance/records
PUT    /api/quality/equipment-maintenance/records/{id}
DELETE /api/quality/equipment-maintenance/records/{id}
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_quality_operation

router = APIRouter()

PROCESS_MACHINE_TYPE = {
    "cutting": "切断",
    "chamfering": "面取",
    "forming": "成型",
    "welding": "溶接",
    "plating": "メッキ",
}
WORK_TYPES = {"maintenance", "repair"}
STATUSES = {"planned", "done", "cancelled"}


class EquipmentBody(BaseModel):
    process_code: str
    machine_cd: Optional[str] = None
    equipment_name: str
    asset_no: Optional[str] = None
    location: Optional[str] = None
    cycle_days: Optional[int] = Field(default=None, ge=1, le=3650)
    note: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class RecordBody(BaseModel):
    equipment_id: int
    work_type: str
    status: str = "planned"
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    title: Optional[str] = None
    content: Optional[str] = None
    assignee: Optional[str] = None
    work_hours: Optional[float] = Field(default=None, ge=0, le=9999.99)
    note: Optional[str] = None


class ImportMachinesBody(BaseModel):
    process_code: Optional[str] = None


def _reraise_table_missing(e: Exception) -> None:
    msg = str(e).lower()
    if "quality_equipment_maintenance" in msg and (
        "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
    ):
        raise HTTPException(
            status_code=503,
            detail="設備保全テーブルが存在しません。"
            "マイグレーション 152_quality_equipment_maintenance.sql を実行してください。",
        ) from e


def _date_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    return str(value)[:10]


def _dt_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _clean(value: Optional[str], limit: int) -> Optional[str]:
    text_value = (value or "").strip()
    if not text_value:
        return None
    if len(text_value) > limit:
        raise HTTPException(status_code=400, detail=f"{limit}文字以内で入力してください")
    return text_value


def _require_process(code: str) -> str:
    key = (code or "").strip()
    if key not in PROCESS_MACHINE_TYPE:
        raise HTTPException(status_code=400, detail="工程を選択してください")
    return key


def _validate_record(body: RecordBody) -> None:
    if body.work_type not in WORK_TYPES:
        raise HTTPException(status_code=400, detail="区分は保全または修理を選択してください")
    if body.status not in STATUSES:
        raise HTTPException(status_code=400, detail="状態が不正です")
    # planned は予定日未定（NULL）を許可。件名または内容のどちらかは推奨だが必須にしない
    if body.status == "done" and body.actual_date is None:
        raise HTTPException(status_code=400, detail="実施日を入力してください")
    if body.status == "planned" and not (
        body.planned_date or (body.title or "").strip() or (body.content or "").strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="予定日未定の場合は件名または内容を入力してください",
        )


def _equipment_row(r: Any) -> dict:
    return {
        "id": int(r["id"]),
        "process_code": r["process_code"],
        "machine_cd": r["machine_cd"],
        "equipment_name": r["equipment_name"],
        "asset_no": r["asset_no"],
        "location": r["location"],
        "cycle_days": r["cycle_days"],
        "note": r["note"],
        "is_active": bool(r["is_active"]),
        "sort_order": int(r["sort_order"] or 0),
        "last_maintenance_date": _date_str(r["last_maintenance_date"]),
        "last_repair_date": _date_str(r["last_repair_date"]),
        "next_planned_date": _date_str(r["next_planned_date"]),
        "open_plan_count": int(r["open_plan_count"] or 0),
        "undetermined_plan_count": int(r["undetermined_plan_count"] or 0),
        "created_by": r["created_by"],
        "updated_by": r["updated_by"],
        "created_at": _dt_str(r["created_at"]),
        "updated_at": _dt_str(r["updated_at"]),
    }


def _record_row(r: Any) -> dict:
    return {
        "id": int(r["id"]),
        "equipment_id": int(r["equipment_id"]),
        "process_code": r["process_code"],
        "equipment_name": r["equipment_name"],
        "machine_cd": r["machine_cd"],
        "work_type": r["work_type"],
        "status": r["status"],
        "planned_date": _date_str(r["planned_date"]),
        "actual_date": _date_str(r["actual_date"]),
        "title": r["title"],
        "content": r["content"],
        "assignee": r["assignee"],
        "work_hours": float(r["work_hours"]) if r["work_hours"] is not None else None,
        "note": r["note"],
        "created_by": r["created_by"],
        "updated_by": r["updated_by"],
        "created_at": _dt_str(r["created_at"]),
        "updated_at": _dt_str(r["updated_at"]),
    }


EQUIPMENT_SELECT = """
SELECT
  e.id, e.process_code, e.machine_cd, e.equipment_name, e.asset_no, e.location,
  e.cycle_days, e.note, e.is_active, e.sort_order, e.created_by, e.updated_by,
  e.created_at, e.updated_at,
  (
    SELECT MAX(r.actual_date) FROM quality_equipment_maintenance_records r
    WHERE r.equipment_id = e.id AND r.work_type = 'maintenance' AND r.status = 'done'
  ) AS last_maintenance_date,
  (
    SELECT MAX(r.actual_date) FROM quality_equipment_maintenance_records r
    WHERE r.equipment_id = e.id AND r.work_type = 'repair' AND r.status = 'done'
  ) AS last_repair_date,
  (
    SELECT MIN(r.planned_date) FROM quality_equipment_maintenance_records r
    WHERE r.equipment_id = e.id AND r.status = 'planned' AND r.planned_date IS NOT NULL
  ) AS next_planned_date,
  (
    SELECT COUNT(*) FROM quality_equipment_maintenance_records r
    WHERE r.equipment_id = e.id AND r.status = 'planned'
  ) AS open_plan_count,
  (
    SELECT COUNT(*) FROM quality_equipment_maintenance_records r
    WHERE r.equipment_id = e.id AND r.status = 'planned' AND r.planned_date IS NULL
  ) AS undetermined_plan_count
FROM quality_equipment_maintenance e
"""


async def _sync_machines_from_master(
    db: AsyncSession,
    codes: list[str],
    actor: Optional[str],
) -> int:
    """machines から工程別設備を保全台帳へ自動取込（未登録分のみ）。"""
    inserted = 0
    for code in codes:
        result = await db.execute(
            text(
                """
                INSERT INTO quality_equipment_maintenance
                  (process_code, machine_cd, equipment_name, note, is_active, created_by, updated_by)
                SELECT :process_code, m.machine_cd, m.machine_name, m.note, 1, :actor, :actor
                FROM machines m
                WHERE m.machine_type = :machine_type
                  AND (m.status IS NULL OR m.status IN ('active', 'maintenance'))
                  AND NOT EXISTS (
                    SELECT 1 FROM quality_equipment_maintenance e
                    WHERE e.machine_cd = m.machine_cd
                  )
                """
            ),
            {
                "process_code": code,
                "machine_type": PROCESS_MACHINE_TYPE[code],
                "actor": actor,
            },
        )
        inserted += int(result.rowcount or 0)
        # 既に紐付いている設備名をマスタに合わせて更新
        await db.execute(
            text(
                """
                UPDATE quality_equipment_maintenance e
                INNER JOIN machines m ON m.machine_cd = e.machine_cd
                SET e.equipment_name = m.machine_name,
                    e.updated_by = COALESCE(:actor, e.updated_by)
                WHERE e.process_code = :process_code
                  AND m.machine_type = :machine_type
                  AND e.equipment_name <> m.machine_name
                """
            ),
            {
                "process_code": code,
                "machine_type": PROCESS_MACHINE_TYPE[code],
                "actor": actor,
            },
        )
    return inserted


@router.get("/equipment-maintenance/equipments")
async def list_equipments(
    process_code: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    auto_sync: bool = Query(True, description="設備マスタから当該工程の設備を自動取込"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    actor = getattr(current_user, "username", None)
    sync_codes = (
        [_require_process(process_code)] if process_code else list(PROCESS_MACHINE_TYPE)
    )
    synced = 0
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if process_code:
        clauses.append("e.process_code = :process_code")
        params["process_code"] = _require_process(process_code)
    if not include_inactive:
        clauses.append("e.is_active = 1")
    kw = (keyword or "").strip()
    if kw:
        clauses.append(
            "(e.equipment_name LIKE :kw OR e.machine_cd LIKE :kw OR e.asset_no LIKE :kw OR e.location LIKE :kw)"
        )
        params["kw"] = f"%{kw}%"
    sql = (
        EQUIPMENT_SELECT
        + " WHERE "
        + " AND ".join(clauses)
        + " ORDER BY FIELD(e.process_code, 'cutting','chamfering','forming','welding','plating'),"
        + " e.sort_order, e.equipment_name, e.id"
    )
    try:
        if auto_sync:
            synced = await _sync_machines_from_master(db, sync_codes, actor)
            await db.commit()
        rows = (await db.execute(text(sql), params)).mappings().fetchall()
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("設備保全一覧の取得に失敗")
        raise HTTPException(status_code=500, detail="設備一覧の取得に失敗しました") from e
    items = [_equipment_row(r) for r in rows]
    msg = "OK" if synced == 0 else f"設備マスタから{synced}件を自動取込しました"
    return {
        "success": True,
        "data": {"list": items, "total": len(items), "synced": synced},
        "message": msg,
    }


@router.post("/equipment-maintenance/equipments")
async def create_equipment(
    body: EquipmentBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("create")),
):
    process_code = _require_process(body.process_code)
    name = _clean(body.equipment_name, 100)
    if not name:
        raise HTTPException(status_code=400, detail="設備名を入力してください")
    actor = getattr(current_user, "username", None)
    try:
        await db.execute(
            text(
                """
                INSERT INTO quality_equipment_maintenance
                  (process_code, machine_cd, equipment_name, asset_no, location, cycle_days,
                   note, is_active, sort_order, created_by, updated_by)
                VALUES
                  (:process_code, :machine_cd, :equipment_name, :asset_no, :location, :cycle_days,
                   :note, :is_active, :sort_order, :actor, :actor)
                """
            ),
            {
                "process_code": process_code,
                "machine_cd": _clean(body.machine_cd, 50),
                "equipment_name": name,
                "asset_no": _clean(body.asset_no, 50),
                "location": _clean(body.location, 100),
                "cycle_days": body.cycle_days,
                "note": _clean(body.note, 2000),
                "is_active": 1 if body.is_active else 0,
                "sort_order": body.sort_order,
                "actor": actor,
            },
        )
        new_id = (await db.execute(text("SELECT LAST_INSERT_ID() AS id"))).scalar()
        await db.commit()
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("設備保全の登録に失敗")
        raise HTTPException(status_code=500, detail="設備の登録に失敗しました") from e
    return {"success": True, "data": {"id": int(new_id or 0)}, "message": "登録しました"}


@router.put("/equipment-maintenance/equipments/{equipment_id}")
async def update_equipment(
    equipment_id: int,
    body: EquipmentBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    process_code = _require_process(body.process_code)
    name = _clean(body.equipment_name, 100)
    if not name:
        raise HTTPException(status_code=400, detail="設備名を入力してください")
    actor = getattr(current_user, "username", None)
    try:
        result = await db.execute(
            text(
                """
                UPDATE quality_equipment_maintenance
                SET process_code = :process_code,
                    machine_cd = :machine_cd,
                    equipment_name = :equipment_name,
                    asset_no = :asset_no,
                    location = :location,
                    cycle_days = :cycle_days,
                    note = :note,
                    is_active = :is_active,
                    sort_order = :sort_order,
                    updated_by = :actor
                WHERE id = :id
                """
            ),
            {
                "id": equipment_id,
                "process_code": process_code,
                "machine_cd": _clean(body.machine_cd, 50),
                "equipment_name": name,
                "asset_no": _clean(body.asset_no, 50),
                "location": _clean(body.location, 100),
                "cycle_days": body.cycle_days,
                "note": _clean(body.note, 2000),
                "is_active": 1 if body.is_active else 0,
                "sort_order": body.sort_order,
                "actor": actor,
            },
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="設備が見つかりません")
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("設備保全の更新に失敗")
        raise HTTPException(status_code=500, detail="設備の更新に失敗しました") from e
    return {"success": True, "message": "更新しました"}


@router.delete("/equipment-maintenance/equipments/{equipment_id}")
async def delete_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("delete")),
):
    try:
        result = await db.execute(
            text("DELETE FROM quality_equipment_maintenance WHERE id = :id"),
            {"id": equipment_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="設備が見つかりません")
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("設備保全の削除に失敗")
        raise HTTPException(status_code=500, detail="設備の削除に失敗しました") from e
    return {"success": True, "message": "削除しました"}


@router.post("/equipment-maintenance/equipments/import-machines")
async def import_machines(
    body: ImportMachinesBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("create")),
):
    codes = [_require_process(body.process_code)] if body.process_code else list(PROCESS_MACHINE_TYPE)
    actor = getattr(current_user, "username", None)
    try:
        inserted = await _sync_machines_from_master(db, codes, actor)
        await db.commit()
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("設備マスタ取込に失敗")
        raise HTTPException(status_code=500, detail="設備マスタの取込に失敗しました") from e
    return {"success": True, "data": {"inserted": inserted}, "message": f"{inserted}件を取り込みました"}


RECORD_SELECT = """
SELECT
  r.id, r.equipment_id, e.process_code, e.equipment_name, e.machine_cd,
  r.work_type, r.status, r.planned_date, r.actual_date, r.title, r.content,
  r.assignee, r.work_hours, r.note, r.created_by, r.updated_by, r.created_at, r.updated_at
FROM quality_equipment_maintenance_records r
INNER JOIN quality_equipment_maintenance e ON e.id = r.equipment_id
"""


@router.get("/equipment-maintenance/records")
async def list_records(
    equipment_id: Optional[int] = Query(None),
    process_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    work_type: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if equipment_id:
        clauses.append("r.equipment_id = :equipment_id")
        params["equipment_id"] = equipment_id
    if process_code:
        clauses.append("e.process_code = :process_code")
        params["process_code"] = _require_process(process_code)
    if status:
        if status not in STATUSES:
            raise HTTPException(status_code=400, detail="状態が不正です")
        clauses.append("r.status = :status")
        params["status"] = status
    if work_type:
        if work_type not in WORK_TYPES:
            raise HTTPException(status_code=400, detail="区分が不正です")
        clauses.append("r.work_type = :work_type")
        params["work_type"] = work_type
    if from_date and to_date:
        clauses.append(
            "((r.planned_date BETWEEN :from_date AND :to_date)"
            " OR (r.actual_date BETWEEN :from_date AND :to_date))"
        )
        params["from_date"] = from_date
        params["to_date"] = to_date
    sql = RECORD_SELECT + " WHERE " + " AND ".join(clauses) + " ORDER BY COALESCE(r.planned_date, r.actual_date), r.id"
    try:
        rows = (await db.execute(text(sql), params)).mappings().fetchall()
    except Exception as e:
        _reraise_table_missing(e)
        logger.exception("保全記録の取得に失敗")
        raise HTTPException(status_code=500, detail="保全記録の取得に失敗しました") from e
    items = [_record_row(r) for r in rows]
    return {"success": True, "data": {"list": items, "total": len(items)}, "message": "OK"}


def _record_params(body: RecordBody, actor: Optional[str], record_id: Optional[int] = None) -> dict:
    _validate_record(body)
    title = _clean(body.title, 200)
    params = {
        "equipment_id": body.equipment_id,
        "work_type": body.work_type,
        "status": body.status,
        "planned_date": body.planned_date,
        "actual_date": body.actual_date,
        "title": title,
        "content": _clean(body.content, 4000),
        "assignee": _clean(body.assignee, 100),
        "work_hours": body.work_hours,
        "note": _clean(body.note, 2000),
        "actor": actor,
    }
    if record_id is not None:
        params["id"] = record_id
    return params


@router.post("/equipment-maintenance/records")
async def create_record(
    body: RecordBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("create")),
):
    actor = getattr(current_user, "username", None)
    params = _record_params(body, actor)
    try:
        exists = (
            await db.execute(
                text("SELECT id FROM quality_equipment_maintenance WHERE id = :id"),
                {"id": body.equipment_id},
            )
        ).scalar()
        if not exists:
            raise HTTPException(status_code=404, detail="設備が見つかりません")
        await db.execute(
            text(
                """
                INSERT INTO quality_equipment_maintenance_records
                  (equipment_id, work_type, status, planned_date, actual_date, title, content,
                   assignee, work_hours, note, created_by, updated_by)
                VALUES
                  (:equipment_id, :work_type, :status, :planned_date, :actual_date, :title, :content,
                   :assignee, :work_hours, :note, :actor, :actor)
                """
            ),
            params,
        )
        new_id = (await db.execute(text("SELECT LAST_INSERT_ID() AS id"))).scalar()
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("保全記録の登録に失敗")
        raise HTTPException(status_code=500, detail="記録の登録に失敗しました") from e
    return {"success": True, "data": {"id": int(new_id or 0)}, "message": "登録しました"}


@router.put("/equipment-maintenance/records/{record_id}")
async def update_record(
    record_id: int,
    body: RecordBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    actor = getattr(current_user, "username", None)
    params = _record_params(body, actor, record_id)
    try:
        result = await db.execute(
            text(
                """
                UPDATE quality_equipment_maintenance_records
                SET equipment_id = :equipment_id,
                    work_type = :work_type,
                    status = :status,
                    planned_date = :planned_date,
                    actual_date = :actual_date,
                    title = :title,
                    content = :content,
                    assignee = :assignee,
                    work_hours = :work_hours,
                    note = :note,
                    updated_by = :actor
                WHERE id = :id
                """
            ),
            params,
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="記録が見つかりません")
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("保全記録の更新に失敗")
        raise HTTPException(status_code=500, detail="記録の更新に失敗しました") from e
    return {"success": True, "message": "更新しました"}


@router.delete("/equipment-maintenance/records/{record_id}")
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("delete")),
):
    try:
        result = await db.execute(
            text("DELETE FROM quality_equipment_maintenance_records WHERE id = :id"),
            {"id": record_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="記録が見つかりません")
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("保全記録の削除に失敗")
        raise HTTPException(status_code=500, detail="記録の削除に失敗しました") from e
    return {"success": True, "message": "削除しました"}

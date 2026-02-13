"""
設備運行時間設定 API
- GET /machines: machines テーブルから設備一覧（下拉用）
- GET/POST/DELETE /work-time-config: machine_work_time_config テーブル
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import Machine, MachineWorkTimeConfig

router = APIRouter()


@router.get("/machines")
async def get_machines_for_work_time(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備一覧（設備運行時間設定ダイアログの設備下拉用）。machines テーブルを読む。"""
    q = select(Machine).order_by(Machine.machine_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {"machine_cd": r.machine_cd, "machine_name": r.machine_name or r.machine_cd or ""}
        for r in rows
    ]


def _config_to_item(row: MachineWorkTimeConfig) -> dict:
    return {
        "id": row.id,
        "machine_cd": row.machine_cd,
        "machine_name": row.machine_name or "",
        "time_slot_17_19": 1 if row.time_slot_17_19 else 0,
        "time_slot_19_21": 1 if row.time_slot_19_21 else 0,
        "time_slot_6_8": 1 if row.time_slot_6_8 else 0,
    }


@router.get("/work-time-config")
async def get_work_time_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """設備運行時間設定一覧。machine_work_time_config テーブルを読む。"""
    q = select(MachineWorkTimeConfig).order_by(MachineWorkTimeConfig.machine_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [_config_to_item(r) for r in rows]


@router.post("/work-time-config")
async def save_work_time_config(
    body: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """一括保存。configs の machine_cd で upsert。"""
    configs: List[dict] = body.get("configs") or []
    count = 0
    for c in configs:
        machine_cd = (c.get("machine_cd") or "").strip()
        machine_name = (c.get("machine_name") or "").strip()
        if not machine_cd:
            continue
        q = select(MachineWorkTimeConfig).where(MachineWorkTimeConfig.machine_cd == machine_cd)
        res = await db.execute(q)
        row = res.scalar_one_or_none()
        t17 = 1 if c.get("time_slot_17_19") else 0
        t19 = 1 if c.get("time_slot_19_21") else 0
        t6 = 1 if c.get("time_slot_6_8") else 0
        if row:
            row.machine_name = machine_name
            row.time_slot_17_19 = t17
            row.time_slot_19_21 = t19
            row.time_slot_6_8 = t6
            count += 1
        else:
            db.add(
                MachineWorkTimeConfig(
                    machine_cd=machine_cd,
                    machine_name=machine_name,
                    time_slot_17_19=t17,
                    time_slot_19_21=t19,
                    time_slot_6_8=t6,
                )
            )
            count += 1
    await db.commit()
    return {"success": True, "data": {"count": count}, "message": "OK"}


@router.post("/work-time-config/single")
async def save_single_work_time_config(
    body: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """1件保存。machine_cd で upsert。"""
    machine_cd = (body.get("machine_cd") or "").strip()
    machine_name = (body.get("machine_name") or "").strip()
    if not machine_cd:
        raise HTTPException(status_code=400, detail="machine_cd は必須です")
    q = select(MachineWorkTimeConfig).where(MachineWorkTimeConfig.machine_cd == machine_cd)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    t17 = 1 if body.get("time_slot_17_19") else 0
    t19 = 1 if body.get("time_slot_19_21") else 0
    t6 = 1 if body.get("time_slot_6_8") else 0
    if row:
        row.machine_name = machine_name
        row.time_slot_17_19 = t17
        row.time_slot_19_21 = t19
        row.time_slot_6_8 = t6
    else:
        row = MachineWorkTimeConfig(
            machine_cd=machine_cd,
            machine_name=machine_name,
            time_slot_17_19=t17,
            time_slot_19_21=t19,
            time_slot_6_8=t6,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _config_to_item(row), "message": "OK"}


@router.delete("/work-time-config/{config_id}")
async def delete_work_time_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """1件削除。"""
    q = select(MachineWorkTimeConfig).where(MachineWorkTimeConfig.id == config_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設定が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}

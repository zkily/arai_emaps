"""
部品受入ログ API（part_logs）
GET    /api/part/receiving              一覧取得（ページネーション・フィルタ）
GET    /api/part/receiving/{id}         詳細取得
POST   /api/part/receiving              新規登録
PUT    /api/part/receiving/{id}         更新
DELETE /api/part/receiving/{id}         削除
GET    /api/part/receiving/suppliers    仕入先一覧
POST   /api/part/receiving/import-csv  CSVインポート（空 body 時は .env で解決した部品 CSV パスを読込）
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct
from typing import Optional, List, Set
from datetime import date

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_purchase_operation
from app.modules.auth.models import User
from app.modules.master.models import PartMaster
from app.modules.part.models import PartLog
from app.modules.part.schemas import PartLogCreate, PartLogUpdate
from app.services.file_watcher.sync_services import sync_part_csv_files_from_watch_folder

router = APIRouter()


def _escape_like_pattern(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _resolve_part_cd_from_master(r: PartLog, name_to_cd: dict[str, str]) -> str:
    name = (r.part_name or "").strip()
    if name and name in name_to_cd:
        return name_to_cd[name]
    return (r.part_cd or "").strip()


async def _part_name_to_cd_map(db: AsyncSession, names: Set[str]) -> dict[str, str]:
    cleaned = {n.strip() for n in names if n and str(n).strip()}
    if not cleaned:
        return {}
    out: dict[str, str] = {}
    name_list = list(cleaned)
    chunk_size = 1500
    for i in range(0, len(name_list), chunk_size):
        chunk = name_list[i : i + chunk_size]
        res = await db.execute(
            select(PartMaster.part_name, PartMaster.part_cd, PartMaster.id)
            .where(PartMaster.part_name.in_(chunk))
            .order_by(PartMaster.id.asc())
        )
        for name, cd, _mid in res.all():
            key = (name or "").strip()
            if not key or key in out:
                continue
            c = (cd or "").strip()
            if c:
                out[key] = c
    return out


def _log_to_dict(r: PartLog) -> dict:
    return {
        "id": r.id,
        "item": r.item,
        "part_cd": r.part_cd,
        "part_name": r.part_name,
        "process_cd": r.process_cd,
        "log_date": r.log_date.isoformat() if r.log_date else None,
        "log_time": str(r.log_time) if r.log_time else None,
        "hd_no": r.hd_no,
        "pieces_per_bundle": r.pieces_per_bundle,
        "quantity": r.quantity,
        "bundle_quantity": r.bundle_quantity,
        "manufacture_no": r.manufacture_no,
        "manufacture_date": r.manufacture_date.isoformat() if r.manufacture_date else None,
        "length": r.length,
        "outer_diameter1": float(r.outer_diameter1) if r.outer_diameter1 is not None else None,
        "outer_diameter2": float(r.outer_diameter2) if r.outer_diameter2 is not None else None,
        "magnetic": r.magnetic,
        "appearance": r.appearance,
        "supplier": r.supplier,
        "part_quality": r.part_quality,
        "remarks": r.remarks,
        "note": r.note,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.get("/suppliers")
async def get_suppliers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(distinct(PartLog.supplier)).where(PartLog.supplier.isnot(None)).order_by(PartLog.supplier)
    result = await db.execute(q)
    suppliers = [row[0] for row in result.all() if row[0]]
    return {"success": True, "data": suppliers}


@router.get("")
async def list_receiving_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=20000),
    keyword: Optional[str] = Query(None),
    partNameExact: Optional[str] = Query(None, description="部品名完全一致"),
    part_cd: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(PartLog)

    exact_name = (partNameExact or "").strip()
    if exact_name:
        q = q.where(PartLog.part_name == exact_name)
    elif keyword and keyword.strip():
        kw = f"%{_escape_like_pattern(keyword.strip())}%"
        q = q.where(
            or_(
                PartLog.part_cd.ilike(kw, escape="\\"),
                PartLog.part_name.ilike(kw, escape="\\"),
                PartLog.manufacture_no.ilike(kw, escape="\\"),
                PartLog.supplier.ilike(kw, escape="\\"),
                PartLog.hd_no.ilike(kw, escape="\\"),
            )
        )
    if part_cd:
        q = q.where(PartLog.part_cd == part_cd)
    if supplier:
        parts = [p.strip() for p in supplier.split(",") if p and p.strip()]
        if len(parts) == 1:
            q = q.where(PartLog.supplier == parts[0])
        elif len(parts) > 1:
            q = q.where(PartLog.supplier.in_(parts))
    if startDate:
        q = q.where(PartLog.log_date >= date.fromisoformat(startDate))
    if endDate:
        q = q.where(PartLog.log_date <= date.fromisoformat(endDate))

    total_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    q = q.order_by(PartLog.log_date.desc(), PartLog.log_time.desc(), PartLog.id.desc())
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()

    name_keys: Set[str] = set()
    for r in rows:
        if r.part_name:
            n = (r.part_name or "").strip()
            if n:
                name_keys.add(n)
    name_to_cd = await _part_name_to_cd_map(db, name_keys)

    def row_to_dict(r: PartLog) -> dict:
        d = _log_to_dict(r)
        d["part_cd"] = _resolve_part_cd_from_master(r, name_to_cd)
        return d

    return {
        "success": True,
        "data": {"list": [row_to_dict(r) for r in rows], "total": total},
    }


@router.get("/{item_id}")
async def get_receiving_log(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(select(PartLog).where(PartLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    name_to_cd = await _part_name_to_cd_map(
        db, {(row.part_name or "").strip()} if row.part_name else set()
    )
    d = _log_to_dict(row)
    d["part_cd"] = _resolve_part_cd_from_master(row, name_to_cd)
    return {"success": True, "data": d}


@router.post("")
async def create_receiving_log(
    body: PartLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("create")),
):
    row = PartLog(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    name_to_cd = await _part_name_to_cd_map(
        db, {(row.part_name or "").strip()} if row.part_name else set()
    )
    d = _log_to_dict(row)
    d["part_cd"] = _resolve_part_cd_from_master(row, name_to_cd)
    return {"success": True, "data": d}


@router.put("/{item_id}")
async def update_receiving_log(
    item_id: int,
    body: PartLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("edit")),
):
    result = await db.execute(select(PartLog).where(PartLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    name_to_cd = await _part_name_to_cd_map(
        db, {(row.part_name or "").strip()} if row.part_name else set()
    )
    d = _log_to_dict(row)
    d["part_cd"] = _resolve_part_cd_from_master(row, name_to_cd)
    return {"success": True, "data": d}


@router.delete("/{item_id}")
async def delete_receiving_log(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("delete")),
):
    result = await db.execute(select(PartLog).where(PartLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}


@router.post("/import-csv")
async def import_csv_logs(
    rows: List[PartLogCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_purchase_operation("export")),
):
    if not rows:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_part_csv_files_from_watch_folder)

    created = 0
    for item in rows:
        row = PartLog(**item.model_dump())
        db.add(row)
        created += 1
    await db.commit()
    return {"success": True, "created": created}

"""
材料受入ログ API（material_logs）
GET    /api/material/receiving              一覧取得（ページネーション・フィルタ）
GET    /api/material/receiving/{id}         詳細取得
POST   /api/material/receiving              新規登録
PUT    /api/material/receiving/{id}         更新
DELETE /api/material/receiving/{id}         削除
GET    /api/material/receiving/suppliers    仕入先一覧
GET    /api/material/receiving/materials    材料名一覧
POST   /api/material/receiving/import-csv  CSVインポート（空 body 時は .env で解決した材料 CSV パスを読込）
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, distinct
from typing import Optional, List, Set
from datetime import date

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.master.models import Material
from app.modules.material.models import MaterialCuttingLog, MaterialLog
from app.modules.material.schemas import (
    MaterialLogCreate,
    MaterialLogUpdate,
    MaterialLogResponse,
)
from app.services.file_watcher.sync_services import sync_material_csv_files_from_watch_folder

router = APIRouter()


def _escape_like_pattern(text: str) -> str:
    """LIKE 検索で % _ \\ をリテラル化"""
    return (
        text.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _resolve_material_cd_from_master(
    r: MaterialLog, name_to_cd: dict[str, str]
) -> str:
    """
    materials テーブルと材料名（完全一致・trim）で突合し material_cd を採用。
    マスタに無い・空のときは material_logs.material_cd をそのまま用いる。
    """
    name = (r.material_name or "").strip()
    if name and name in name_to_cd:
        return name_to_cd[name]
    return (r.material_cd or "").strip()


async def _material_name_to_cd_map(
    db: AsyncSession, names: Set[str]
) -> dict[str, str]:
    """materials.material_name -> material_cd（同一材料名は id 昇順で先頭のみ）"""
    cleaned = {n.strip() for n in names if n and str(n).strip()}
    if not cleaned:
        return {}
    out: dict[str, str] = {}
    name_list = list(cleaned)
    chunk_size = 1500
    for i in range(0, len(name_list), chunk_size):
        chunk = name_list[i : i + chunk_size]
        res = await db.execute(
            select(Material.material_name, Material.material_cd, Material.id)
            .where(Material.material_name.in_(chunk))
            .order_by(Material.id.asc())
        )
        for name, cd, _mid in res.all():
            key = (name or "").strip()
            if not key or key in out:
                continue
            c = (cd or "").strip()
            if c:
                out[key] = c
    return out


def _log_to_dict(r: MaterialLog) -> dict:
    return {
        "id": r.id,
        "item": r.item,
        "material_cd": r.material_cd,
        "material_name": r.material_name,
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
        "material_quality": r.material_quality,
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
    """仕入先一覧（material_logs の supplier から抽出。ここには仕入先名称が格納される）"""
    q = select(distinct(MaterialLog.supplier)).where(MaterialLog.supplier.isnot(None)).order_by(MaterialLog.supplier)
    result = await db.execute(q)
    suppliers = [row[0] for row in result.all() if row[0]]
    return {"success": True, "data": suppliers}


@router.get("/materials")
async def get_material_names(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """材料名一覧（受入ログから抽出）"""
    q = (
        select(distinct(MaterialLog.material_cd), MaterialLog.material_name)
        .where(MaterialLog.material_cd.isnot(None))
        .order_by(MaterialLog.material_cd)
    )
    result = await db.execute(q)
    rows = result.all()
    return {
        "success": True,
        "data": [{"material_cd": r[0], "material_name": r[1]} for r in rows],
    }


@router.get("")
async def list_receiving_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=20000),
    keyword: Optional[str] = Query(None),
    materialNameExact: Optional[str] = Query(
        None,
        description="材料名完全一致（材料詳細ダイアログ等。keyword より優先）",
    ),
    material_cd: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    includeCuttingUsage: bool = Query(
        False,
        description="True のとき material_cutting_logs.manufacture_no と突合し used_in_cutting を付与",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ一覧取得"""
    q = select(MaterialLog)

    exact_name = (materialNameExact or "").strip()
    if exact_name:
        q = q.where(MaterialLog.material_name == exact_name)
    elif keyword and keyword.strip():
        kw = f"%{_escape_like_pattern(keyword.strip())}%"
        q = q.where(
            or_(
                MaterialLog.material_cd.ilike(kw, escape="\\"),
                MaterialLog.material_name.ilike(kw, escape="\\"),
                MaterialLog.manufacture_no.ilike(kw, escape="\\"),
                MaterialLog.supplier.ilike(kw, escape="\\"),
                MaterialLog.hd_no.ilike(kw, escape="\\"),
            )
        )
    if material_cd:
        q = q.where(MaterialLog.material_cd == material_cd)
    if supplier:
        # 複数仕入先対応: カンマ区切りなら IN 条件、単一なら等号
        parts = [p.strip() for p in supplier.split(",") if p and p.strip()]
        if len(parts) == 1:
            q = q.where(MaterialLog.supplier == parts[0])
        elif len(parts) > 1:
            q = q.where(MaterialLog.supplier.in_(parts))
    if startDate:
        q = q.where(MaterialLog.log_date >= date.fromisoformat(startDate))
    if endDate:
        q = q.where(MaterialLog.log_date <= date.fromisoformat(endDate))

    total_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    q = q.order_by(MaterialLog.log_date.desc(), MaterialLog.log_time.desc(), MaterialLog.id.desc())
    q = q.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(q)
    rows = result.scalars().all()

    name_keys: Set[str] = set()
    for r in rows:
        if r.material_name:
            n = (r.material_name or "").strip()
            if n:
                name_keys.add(n)
    name_to_cd = await _material_name_to_cd_map(db, name_keys)

    used_manufacture_nos: set[str] = set()
    if includeCuttingUsage and rows:
        nos = list({r.manufacture_no for r in rows if r.manufacture_no})
        if nos:
            cq = (
                select(distinct(MaterialCuttingLog.manufacture_no))
                .where(
                    MaterialCuttingLog.manufacture_no.isnot(None),
                    MaterialCuttingLog.manufacture_no.in_(nos),
                )
            )
            cres = await db.execute(cq)
            used_manufacture_nos = {row[0] for row in cres.all() if row[0]}

    def row_to_dict(r: MaterialLog) -> dict:
        d = _log_to_dict(r)
        d["material_cd"] = _resolve_material_cd_from_master(r, name_to_cd)
        if includeCuttingUsage:
            mn = r.manufacture_no
            d["used_in_cutting"] = bool(mn and mn in used_manufacture_nos)
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
    """受入ログ詳細"""
    result = await db.execute(select(MaterialLog).where(MaterialLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    name_to_cd = await _material_name_to_cd_map(
        db, {(row.material_name or "").strip()} if row.material_name else set()
    )
    d = _log_to_dict(row)
    d["material_cd"] = _resolve_material_cd_from_master(row, name_to_cd)
    return {"success": True, "data": d}


@router.post("")
async def create_receiving_log(
    body: MaterialLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ新規登録"""
    row = MaterialLog(**body.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    name_to_cd = await _material_name_to_cd_map(
        db, {(row.material_name or "").strip()} if row.material_name else set()
    )
    d = _log_to_dict(row)
    d["material_cd"] = _resolve_material_cd_from_master(row, name_to_cd)
    return {"success": True, "data": d}


@router.put("/{item_id}")
async def update_receiving_log(
    item_id: int,
    body: MaterialLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ更新"""
    result = await db.execute(select(MaterialLog).where(MaterialLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    name_to_cd = await _material_name_to_cd_map(
        db, {(row.material_name or "").strip()} if row.material_name else set()
    )
    d = _log_to_dict(row)
    d["material_cd"] = _resolve_material_cd_from_master(row, name_to_cd)
    return {"success": True, "data": d}


@router.delete("/{item_id}")
async def delete_receiving_log(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """受入ログ削除"""
    result = await db.execute(select(MaterialLog).where(MaterialLog.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "message": "削除しました"}


@router.post("/import-csv")
async def import_csv_logs(
    rows: List[MaterialLogCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """CSV 一括インポート。body が空のときは .env（MATERIAL_RECEIVING_CSV_PATHS 等）で解決した材料 CSV を読み取り DB へ同期。"""
    if not rows:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_material_csv_files_from_watch_folder)

    created = 0
    for item in rows:
        row = MaterialLog(**item.model_dump())
        db.add(row)
        created += 1
    await db.commit()
    return {"success": True, "created": created}

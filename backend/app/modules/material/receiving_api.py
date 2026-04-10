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
from sqlalchemy import select, func, or_, distinct, delete
from typing import Optional, List, Set
from datetime import date, datetime, timedelta, timezone

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
        "cutting_used_manual": bool(getattr(r, "cutting_used_manual", False)),
        "cutting_used_manual_at": (
            r.cutting_used_manual_at.isoformat() if getattr(r, "cutting_used_manual_at", None) else None
        ),
        "cutting_used_manual_by": getattr(r, "cutting_used_manual_by", None),
        "cutting_used_manual_note": getattr(r, "cutting_used_manual_note", None),
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
            from_log = bool(mn and mn in used_manufacture_nos)
            manual = bool(getattr(r, "cutting_used_manual", False))
            d["used_in_cutting_from_log"] = from_log
            d["used_in_cutting"] = from_log or manual
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


_MANUAL_CUTTING_PREFIX = "manual:material_log"


def _pop_manual_cutting_fields(data: dict) -> tuple[Optional[bool], Optional[str], Optional[str]]:
    """PUT ボディから手動切断フラグ・備考・管理コードを取り出し（残りは通常更新用）"""
    manual = data.pop("cutting_used_manual", None)
    note = data.pop("cutting_used_manual_note", None)
    mc = data.pop("manual_cutting_management_code", None)
    return manual, note, mc


_JST = timezone(timedelta(hours=9))


async def _delete_manual_cutting_logs_for_material_log(db: AsyncSession, material_log_id: int) -> int:
    """手動連携で追加した切断ログのみ削除（source_file プレフィックス判定）"""
    pat = f"{_MANUAL_CUTTING_PREFIX}:{material_log_id}:%"
    r = await db.execute(delete(MaterialCuttingLog).where(MaterialCuttingLog.source_file.like(pat)))
    return int(r.rowcount or 0)


async def _insert_manual_cutting_log_for_receiving(
    db: AsyncSession,
    material_log: MaterialLog,
    management_code: str,
    material_log_id: int,
) -> MaterialCuttingLog:
    """
    手動「使用済」で material_cutting_logs に1件追加。
    material_cd が空だと DB トリガーで manufacture_no が落ちるため、
    受入の材料CDが無いときは製造番号を material_cd に入れる（ビジネス上の「材料未連携」行として扱う）。
    """
    mfg = (material_log.manufacture_no or "").strip()
    if not mfg:
        raise HTTPException(
            status_code=400,
            detail="製造番号が空のため切断ログ（material_cutting_logs）へ連携できません",
        )
    mc = (management_code or "").strip()[:255]
    if not mc:
        raise HTTPException(status_code=400, detail="管理コードが空です")

    now = datetime.now(_JST)
    log_date = now.date()
    log_time = now.time().replace(microsecond=0)
    recv_cd = (material_log.material_cd or "").strip()
    # トリガー tg_material_cutting_logs_manufacture_no_bi 対策
    material_cd_val = (recv_cd or mfg)[:255]

    raw = f"切断材料使用,{log_date},{log_time},手動入力,9999,{material_cd_val},{mfg},{mc}"
    source_file = f"{_MANUAL_CUTTING_PREFIX}:{material_log_id}:{int(now.timestamp() * 1000)}"

    rec = MaterialCuttingLog(
        item="切断材料使用",
        log_date=log_date,
        log_time=log_time,
        hd_no="手動入力",
        operator_name="9999",
        material_cd=material_cd_val,
        management_code=mc,
        raw_line=raw[:65535] if len(raw) > 65535 else raw,
        source_file=source_file[:500],
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec


def _apply_cutting_used_manual_fields(
    row: MaterialLog,
    manual: Optional[bool],
    note: Optional[str],
    current_user: User,
) -> None:
    """cutting_used_manual の更新（True=確定、False=取消、None=触らない）。備考のみ更新も可。"""
    if manual is True:
        row.cutting_used_manual = True
        row.cutting_used_manual_at = datetime.now()
        row.cutting_used_manual_by = (current_user.username or "")[:100] or None
        if note is not None:
            row.cutting_used_manual_note = (note.strip()[:500] if note and note.strip() else None)
    elif manual is False:
        row.cutting_used_manual = False
        row.cutting_used_manual_at = None
        row.cutting_used_manual_by = None
        row.cutting_used_manual_note = None
    elif note is not None and getattr(row, "cutting_used_manual", False):
        row.cutting_used_manual_note = note.strip()[:500] if note.strip() else None


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
    data = body.model_dump(exclude_unset=True)
    manual, manual_note, manual_mc = _pop_manual_cutting_fields(data)
    _apply_cutting_used_manual_fields(row, manual, manual_note, current_user)
    for field, value in data.items():
        setattr(row, field, value)

    await db.flush()

    material_cutting_log_id: Optional[int] = None
    if manual is False:
        await _delete_manual_cutting_logs_for_material_log(db, item_id)
    elif manual is True and manual_mc is not None and str(manual_mc).strip():
        cutting_row = await _insert_manual_cutting_log_for_receiving(
            db, row, str(manual_mc).strip(), item_id
        )
        material_cutting_log_id = cutting_row.id

    await db.commit()
    await db.refresh(row)
    name_to_cd = await _material_name_to_cd_map(
        db, {(row.material_name or "").strip()} if row.material_name else set()
    )
    d = _log_to_dict(row)
    d["material_cd"] = _resolve_material_cd_from_master(row, name_to_cd)
    out: dict = {"success": True, "data": d}
    if material_cutting_log_id is not None:
        out["material_cutting_log_id"] = material_cutting_log_id
    return out


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

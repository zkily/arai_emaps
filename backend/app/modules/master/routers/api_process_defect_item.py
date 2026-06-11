"""
工程別不良項目マスタ API（process_defect_items）
収集工程（detection_process_cd）ごとに MES で選択可能な不良項目を管理する。
帰属工程（attributable_process_cd）で後工程発見時の責任工程を指定する。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List
from pydantic import BaseModel, Field

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.operation_deps import require_master_operation
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import ProcessDefectItem, Process

router = APIRouter()


class DefectItemIn(BaseModel):
    detection_process_cd: str = Field(..., min_length=1, max_length=20)
    attributable_process_cd: str = Field(..., min_length=1, max_length=20)
    defect_cd: str = Field(..., min_length=1, max_length=50)
    defect_name: str = Field(..., min_length=1, max_length=100)
    sort_order: int = Field(0, ge=0)
    status: str = Field("active", max_length=20)
    remarks: Optional[str] = None


def _item_dict(
    row: ProcessDefectItem,
    detection_name: Optional[str] = None,
    attributable_name: Optional[str] = None,
) -> dict:
    d = {
        "id": row.id,
        "detection_process_cd": row.detection_process_cd,
        "attributable_process_cd": row.attributable_process_cd,
        "defect_cd": row.defect_cd,
        "defect_name": row.defect_name,
        "sort_order": row.sort_order or 0,
        "status": row.status or "active",
        "remarks": row.remarks,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
    if detection_name is not None:
        d["detection_process_name"] = detection_name
    if attributable_name is not None:
        d["attributable_process_name"] = attributable_name
    return d


async def _process_name_map(db: AsyncSession, cds: List[str]) -> dict[str, str]:
    if not cds:
        return {}
    uniq = list({c.strip() for c in cds if c and str(c).strip()})
    if not uniq:
        return {}
    pr = await db.execute(
        select(Process.process_cd, Process.process_name).where(Process.process_cd.in_(uniq))
    )
    return {cd: (name or cd) for cd, name in pr.all()}


def _apply_filters(
    q,
    detection_process_cd: Optional[str],
    attributable_process_cd: Optional[str],
    keyword: Optional[str],
    status: Optional[str],
    active_only: bool,
):
    if detection_process_cd and detection_process_cd.strip():
        q = q.where(ProcessDefectItem.detection_process_cd == detection_process_cd.strip())
    if attributable_process_cd and attributable_process_cd.strip():
        q = q.where(ProcessDefectItem.attributable_process_cd == attributable_process_cd.strip())
    if status and status.strip():
        q = q.where(ProcessDefectItem.status == status.strip())
    elif active_only:
        q = q.where(ProcessDefectItem.status == "active")
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                ProcessDefectItem.defect_cd.like(k),
                ProcessDefectItem.defect_name.like(k),
                ProcessDefectItem.remarks.like(k),
            )
        )
    return q


@router.get("")
async def list_process_defect_items(
    detection_process_cd: Optional[str] = Query(
        None, alias="detectionProcessCd", description="収集・表示工程CD（MES呼び出し時は必須推奨）"
    ),
    attributable_process_cd: Optional[str] = Query(
        None, alias="attributableProcessCd", description="帰属工程CDで絞り込み"
    ),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    active_only: bool = Query(False, alias="activeOnly"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=2000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(ProcessDefectItem)
    q = _apply_filters(q, detection_process_cd, attributable_process_cd, keyword, status, active_only)
    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.order_by(
        ProcessDefectItem.detection_process_cd,
        ProcessDefectItem.sort_order,
        ProcessDefectItem.defect_cd,
    )
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    proc_cds: List[str] = []
    for r in rows:
        proc_cds.append(r.detection_process_cd)
        proc_cds.append(r.attributable_process_cd)
    names = await _process_name_map(db, proc_cds)
    items = [
        _item_dict(
            r,
            names.get(r.detection_process_cd),
            names.get(r.attributable_process_cd),
        )
        for r in rows
    ]
    return {"success": True, "data": {"list": items, "total": total}}


@router.get("/options")
async def get_process_defect_item_options(
    detection_process_cd: str = Query(..., alias="detectionProcessCd", min_length=1),
    attributable_process_cd: Optional[str] = Query(None, alias="attributableProcessCd"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """MES等：収集工程に紐づく有効な不良項目のみ（表示順）"""
    q = select(ProcessDefectItem).where(
        and_(
            ProcessDefectItem.detection_process_cd == detection_process_cd.strip(),
            ProcessDefectItem.status == "active",
        )
    )
    if attributable_process_cd and attributable_process_cd.strip():
        q = q.where(ProcessDefectItem.attributable_process_cd == attributable_process_cd.strip())
    q = q.order_by(ProcessDefectItem.sort_order, ProcessDefectItem.defect_cd)
    rows = (await db.execute(q)).scalars().all()
    proc_cds: List[str] = []
    for r in rows:
        proc_cds.append(r.detection_process_cd)
        proc_cds.append(r.attributable_process_cd)
    names = await _process_name_map(db, proc_cds)
    return {
        "success": True,
        "data": [
            _item_dict(
                r,
                names.get(r.detection_process_cd),
                names.get(r.attributable_process_cd),
            )
            for r in rows
        ],
    }


@router.get("/{item_id}")
async def get_process_defect_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = await db.get(ProcessDefectItem, item_id)
    if not row:
        raise HTTPException(404, "不良項目が見つかりません")
    names = await _process_name_map(
        db, [row.detection_process_cd, row.attributable_process_cd]
    )
    return {
        "success": True,
        "data": _item_dict(
            row,
            names.get(row.detection_process_cd),
            names.get(row.attributable_process_cd),
        ),
    }


@router.post("")
async def create_process_defect_item(
    body: DefectItemIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("create")),
):
    det = body.detection_process_cd.strip()
    att = body.attributable_process_cd.strip()
    cd = body.defect_cd.strip()
    dup = await db.execute(
        select(ProcessDefectItem).where(
            and_(
                ProcessDefectItem.detection_process_cd == det,
                ProcessDefectItem.defect_cd == cd,
            )
        )
    )
    if dup.scalars().first():
        raise HTTPException(400, "同一収集工程・不良項目CDが既に存在します")
    row = ProcessDefectItem(
        detection_process_cd=det,
        attributable_process_cd=att,
        defect_cd=cd,
        defect_name=body.defect_name.strip(),
        sort_order=body.sort_order,
        status=body.status or "active",
        remarks=body.remarks,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    names = await _process_name_map(db, [det, att])
    return {"success": True, "data": _item_dict(row, names.get(det), names.get(att))}


@router.put("/{item_id}")
async def update_process_defect_item(
    item_id: int,
    body: DefectItemIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("edit")),
):
    row = await db.get(ProcessDefectItem, item_id)
    if not row:
        raise HTTPException(404, "不良項目が見つかりません")
    det = body.detection_process_cd.strip()
    att = body.attributable_process_cd.strip()
    cd = body.defect_cd.strip()
    dup = await db.execute(
        select(ProcessDefectItem).where(
            and_(
                ProcessDefectItem.detection_process_cd == det,
                ProcessDefectItem.defect_cd == cd,
                ProcessDefectItem.id != item_id,
            )
        )
    )
    if dup.scalars().first():
        raise HTTPException(400, "同一収集工程・不良項目CDが既に存在します")
    row.detection_process_cd = det
    row.attributable_process_cd = att
    row.defect_cd = cd
    row.defect_name = body.defect_name.strip()
    row.sort_order = body.sort_order
    row.status = body.status or "active"
    row.remarks = body.remarks
    await db.flush()
    await db.refresh(row)
    names = await _process_name_map(db, [det, att])
    return {"success": True, "data": _item_dict(row, names.get(det), names.get(att))}


@router.delete("/{item_id}")
async def delete_process_defect_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master_operation("delete")),
):
    row = await db.get(ProcessDefectItem, item_id)
    if not row:
        raise HTTPException(404, "不良項目が見つかりません")
    await db.delete(row)
    return {"success": True, "message": "削除しました"}

"""
明細BOM API（product_bom_headers / product_bom_lines）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_
from typing import Optional, List
from pydantic import BaseModel
from datetime import date

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import Product, ProductBomHeader, ProductBomLine

router = APIRouter()


# ---------- Schemas ----------

class BomLineIn(BaseModel):
    parent_line_id: Optional[int] = None
    line_no: int = 10
    component_type: str = "material"
    component_product_cd: Optional[str] = None
    component_material_cd: Optional[str] = None
    qty_per: float = 1.0
    uom: str = "個"
    scrap_rate: float = 0.0
    consume_process_cd: Optional[str] = None
    consume_step_no: Optional[int] = None
    remarks: Optional[str] = None


class BomHeaderIn(BaseModel):
    parent_product_cd: str
    bom_type: str = "production"
    revision: str = "1"
    status: str = "active"
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    base_quantity: float = 1.0
    uom: str = "個"
    remarks: Optional[str] = None
    lines: Optional[List[BomLineIn]] = None


# ---------- Helpers ----------

def _header_dict(h: ProductBomHeader, parent_product_name: Optional[str] = None) -> dict:
    return {
        "id": h.id,
        "parent_product_cd": h.parent_product_cd,
        "parent_product_name": parent_product_name,
        "bom_type": h.bom_type,
        "revision": h.revision,
        "status": h.status,
        "effective_from": str(h.effective_from) if h.effective_from else None,
        "effective_to": str(h.effective_to) if h.effective_to else None,
        "base_quantity": float(h.base_quantity) if h.base_quantity else 1,
        "uom": h.uom,
        "remarks": h.remarks,
        "created_by": h.created_by,
        "updated_by": h.updated_by,
    }


def _line_dict(l: ProductBomLine) -> dict:
    return {
        "id": l.id,
        "header_id": l.header_id,
        "parent_line_id": l.parent_line_id,
        "line_no": l.line_no,
        "component_type": l.component_type,
        "component_product_cd": l.component_product_cd,
        "component_material_cd": l.component_material_cd,
        "qty_per": float(l.qty_per) if l.qty_per else 1,
        "uom": l.uom,
        "scrap_rate": float(l.scrap_rate) if l.scrap_rate else 0,
        "consume_process_cd": l.consume_process_cd,
        "consume_step_no": l.consume_step_no,
        "remarks": l.remarks,
    }


async def _check_cycle(db: AsyncSession, header_id: int, component_product_cd: str, parent_product_cd: str):
    """BOM循環参照チェック（子品目→親品目が既存BOMの親になっていないか）"""
    if not component_product_cd:
        return
    if component_product_cd == parent_product_cd:
        raise HTTPException(400, "循環参照: 子品目が親製品と同一です")

    visited = {parent_product_cd}
    queue = [component_product_cd]
    while queue:
        current = queue.pop(0)
        if current in visited:
            raise HTTPException(400, f"循環参照を検出: {current}")
        visited.add(current)
        q = (
            select(ProductBomLine.component_product_cd)
            .join(ProductBomHeader, ProductBomHeader.id == ProductBomLine.header_id)
            .where(
                ProductBomHeader.parent_product_cd == current,
                ProductBomHeader.status == "active",
                ProductBomLine.component_product_cd.isnot(None),
            )
        )
        res = await db.execute(q)
        for (child_cd,) in res.fetchall():
            if child_cd:
                queue.append(child_cd)


# ---------- Header CRUD ----------

@router.get("")
async def list_bom_headers(
    parent_product_cd: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """BOMヘッダ一覧（親製品名は products と LEFT JOIN）"""
    conds = []
    if parent_product_cd:
        conds.append(ProductBomHeader.parent_product_cd == parent_product_cd)
    if status:
        conds.append(ProductBomHeader.status == status)
    if keyword and keyword.strip():
        conds.append(ProductBomHeader.parent_product_cd.like(f"%{keyword.strip()}%"))

    count_base = select(ProductBomHeader)
    if conds:
        count_base = count_base.where(and_(*conds))
    cnt = await db.execute(select(func.count()).select_from(count_base.subquery()))
    total = cnt.scalar() or 0

    list_q = select(ProductBomHeader, Product.product_name).outerjoin(
        Product, Product.product_cd == ProductBomHeader.parent_product_cd
    )
    if conds:
        list_q = list_q.where(and_(*conds))
    list_q = list_q.order_by(ProductBomHeader.parent_product_cd, ProductBomHeader.id.desc()).offset(
        (page - 1) * limit
    ).limit(limit)
    rows = await db.execute(list_q)
    items = [_header_dict(h, pname) for h, pname in rows.all()]
    return {"success": True, "data": {"list": items, "total": total}}


@router.get("/{header_id}")
async def get_bom_header(
    header_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """BOMヘッダ＋行取得"""
    h = await db.get(ProductBomHeader, header_id)
    if not h:
        raise HTTPException(404, "BOMヘッダが見つかりません")
    lines_q = select(ProductBomLine).where(ProductBomLine.header_id == header_id).order_by(ProductBomLine.line_no)
    lines = (await db.execute(lines_q)).scalars().all()
    data = _header_dict(h)
    data["lines"] = [_line_dict(l) for l in lines]
    return {"success": True, "data": data}


@router.post("")
async def create_bom_header(
    body: BomHeaderIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """BOMヘッダ作成（行も一括保存可）"""
    h = ProductBomHeader(
        parent_product_cd=body.parent_product_cd,
        bom_type=body.bom_type,
        revision=body.revision,
        status=body.status,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        base_quantity=body.base_quantity,
        uom=body.uom,
        remarks=body.remarks,
        created_by=current_user.username if current_user else None,
        updated_by=current_user.username if current_user else None,
    )
    db.add(h)
    await db.flush()

    created_lines = []
    if body.lines:
        for ln in body.lines:
            await _check_cycle(db, h.id, ln.component_product_cd, body.parent_product_cd)
            line = ProductBomLine(
                header_id=h.id,
                parent_line_id=ln.parent_line_id,
                line_no=ln.line_no,
                component_type=ln.component_type,
                component_product_cd=ln.component_product_cd,
                component_material_cd=ln.component_material_cd,
                qty_per=ln.qty_per,
                uom=ln.uom,
                scrap_rate=ln.scrap_rate,
                consume_process_cd=ln.consume_process_cd,
                consume_step_no=ln.consume_step_no,
                remarks=ln.remarks,
            )
            db.add(line)
            await db.flush()
            created_lines.append(line)

    data = _header_dict(h)
    data["lines"] = [_line_dict(l) for l in created_lines]
    return {"success": True, "data": data}


@router.put("/{header_id}")
async def update_bom_header(
    header_id: int,
    body: BomHeaderIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """BOMヘッダ更新（行は差し替え）"""
    h = await db.get(ProductBomHeader, header_id)
    if not h:
        raise HTTPException(404, "BOMヘッダが見つかりません")
    h.parent_product_cd = body.parent_product_cd
    h.bom_type = body.bom_type
    h.revision = body.revision
    h.status = body.status
    h.effective_from = body.effective_from
    h.effective_to = body.effective_to
    h.base_quantity = body.base_quantity
    h.uom = body.uom
    h.remarks = body.remarks
    h.updated_by = current_user.username if current_user else None

    if body.lines is not None:
        await db.execute(delete(ProductBomLine).where(ProductBomLine.header_id == header_id))
        await db.flush()
        for ln in body.lines:
            await _check_cycle(db, h.id, ln.component_product_cd, body.parent_product_cd)
            line = ProductBomLine(
                header_id=h.id,
                parent_line_id=ln.parent_line_id,
                line_no=ln.line_no,
                component_type=ln.component_type,
                component_product_cd=ln.component_product_cd,
                component_material_cd=ln.component_material_cd,
                qty_per=ln.qty_per,
                uom=ln.uom,
                scrap_rate=ln.scrap_rate,
                consume_process_cd=ln.consume_process_cd,
                consume_step_no=ln.consume_step_no,
                remarks=ln.remarks,
            )
            db.add(line)

    return {"success": True, "message": "更新しました"}


@router.delete("/{header_id}")
async def delete_bom_header(
    header_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """BOMヘッダ削除（行もCASCADE）"""
    h = await db.get(ProductBomHeader, header_id)
    if not h:
        raise HTTPException(404, "BOMヘッダが見つかりません")
    await db.delete(h)
    return {"success": True, "message": "削除しました"}


# ---------- Tree / Explode ----------

@router.get("/{header_id}/tree")
async def get_bom_tree(
    header_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """BOM行をツリー構造で返す"""
    h = await db.get(ProductBomHeader, header_id)
    if not h:
        raise HTTPException(404, "BOMヘッダが見つかりません")
    lines_q = select(ProductBomLine).where(ProductBomLine.header_id == header_id).order_by(ProductBomLine.line_no)
    all_lines = (await db.execute(lines_q)).scalars().all()
    line_map: dict[int, dict] = {}
    for l in all_lines:
        d = _line_dict(l)
        d["children"] = []
        line_map[l.id] = d

    roots = []
    for l in all_lines:
        d = line_map[l.id]
        if l.parent_line_id and l.parent_line_id in line_map:
            line_map[l.parent_line_id]["children"].append(d)
        else:
            roots.append(d)

    return {"success": True, "data": {"header": _header_dict(h), "tree": roots}}

"""
ローラーBOM API（roller_bom）
"""
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, or_, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import RollerBom

router = APIRouter()


class IdsPayload(BaseModel):
    ids: List[int]


def _row_to_dict(row: RollerBom) -> dict:
    return {
        "id": row.id,
        "roller_cd": row.roller_cd,
        "roller_type": row.roller_type,
        "product_cd": row.product_cd,
        "machine_cd": row.machine_cd,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _keyword_clause(keyword: Optional[str]):
    if not keyword or not str(keyword).strip():
        return None
    k = f"%{keyword.strip()}%"
    return or_(
        RollerBom.roller_cd.like(k),
        RollerBom.roller_type.like(k),
        RollerBom.product_cd.like(k),
        RollerBom.machine_cd.like(k),
    )


def _list_where(
    keyword: Optional[str],
    machine_cd: Optional[str],
    product_cd: Optional[str],
):
    clauses = []
    kw = _keyword_clause(keyword)
    if kw is not None:
        clauses.append(kw)
    if machine_cd and str(machine_cd).strip():
        clauses.append(RollerBom.machine_cd == machine_cd.strip())
    if product_cd and str(product_cd).strip():
        clauses.append(RollerBom.product_cd == product_cd.strip())
    return and_(*clauses) if clauses else None


@router.get("")
async def list_roller_bom(
    keyword: Optional[str] = Query(None),
    machine_cd: Optional[str] = Query(None),
    product_cd: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ローラーBOM一覧（ページング）"""
    where_expr = _list_where(keyword, machine_cd, product_cd)

    count_stmt = select(func.count()).select_from(RollerBom)
    if where_expr is not None:
        count_stmt = count_stmt.where(where_expr)
    total = (await db.execute(count_stmt)).scalar() or 0

    list_stmt = (
        select(RollerBom)
        .order_by(RollerBom.machine_cd, RollerBom.product_cd, RollerBom.roller_cd)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if where_expr is not None:
        list_stmt = list_stmt.where(where_expr)
    result = await db.execute(list_stmt)
    rows = result.scalars().all()
    data_list = [_row_to_dict(r) for r in rows]

    r_stmt = select(func.count(func.distinct(RollerBom.roller_cd))).select_from(RollerBom)
    p_stmt = select(func.count(func.distinct(RollerBom.product_cd))).select_from(RollerBom)
    m_stmt = select(func.count(func.distinct(RollerBom.machine_cd))).select_from(RollerBom)
    if where_expr is not None:
        r_stmt = r_stmt.where(where_expr)
        p_stmt = p_stmt.where(where_expr)
        m_stmt = m_stmt.where(where_expr)
    roller_distinct_count = int((await db.execute(r_stmt)).scalar() or 0)
    product_distinct_count = int((await db.execute(p_stmt)).scalar() or 0)
    machine_distinct_count = int((await db.execute(m_stmt)).scalar() or 0)

    payload: Dict[str, Any] = {
        "success": True,
        "data": {
            "list": data_list,
            "total": total,
            "roller_distinct_count": roller_distinct_count,
            "product_distinct_count": product_distinct_count,
            "machine_distinct_count": machine_distinct_count,
        },
        "list": data_list,
        "total": total,
        "roller_distinct_count": roller_distinct_count,
        "product_distinct_count": product_distinct_count,
        "machine_distinct_count": machine_distinct_count,
    }
    return payload


@router.post("/batch-delete")
async def batch_delete_roller_bom(
    body: IdsPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """複数IDを一括削除"""
    ids = [i for i in body.ids if isinstance(i, int) and i > 0]
    if not ids:
        raise HTTPException(status_code=400, detail="ids が空です")
    await db.execute(delete(RollerBom).where(RollerBom.id.in_(ids)))
    await db.commit()
    return {"message": f"{len(ids)} 件削除しました", "deleted": len(ids)}


@router.get("/{item_id:int}")
async def get_roller_bom_by_id(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(select(RollerBom).where(RollerBom.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ローラーBOMが見つかりません")
    return _row_to_dict(row)


@router.post("")
async def create_roller_bom(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    roller_cd = (body.get("roller_cd") or "").strip()
    product_cd = (body.get("product_cd") or "").strip()
    machine_cd = (body.get("machine_cd") or "").strip()
    if not roller_cd or not product_cd or not machine_cd:
        raise HTTPException(status_code=400, detail="ローラーCD・製品CD・設備CDは必須です")
    dup = await db.execute(
        select(RollerBom.id).where(
            RollerBom.roller_cd == roller_cd,
            RollerBom.product_cd == product_cd,
            RollerBom.machine_cd == machine_cd,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同一のローラーCD・製品CD・設備CDの組み合わせが既に登録されています")
    rt_raw = body.get("roller_type")
    roller_type_val = None
    if rt_raw is not None and str(rt_raw).strip():
        roller_type_val = str(rt_raw).strip()
    row = RollerBom(
        roller_cd=roller_cd,
        roller_type=roller_type_val,
        product_cd=product_cd,
        machine_cd=machine_cd,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.put("/{item_id:int}")
async def update_roller_bom(
    item_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(select(RollerBom).where(RollerBom.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ローラーBOMが見つかりません")

    roller_cd = body.get("roller_cd")
    product_cd = body.get("product_cd")
    machine_cd = body.get("machine_cd")
    new_rc = (roller_cd if roller_cd is not None else row.roller_cd) or ""
    new_pc = (product_cd if product_cd is not None else row.product_cd) or ""
    new_mc = (machine_cd if machine_cd is not None else row.machine_cd) or ""
    if not new_rc.strip() or not new_pc.strip() or not new_mc.strip():
        raise HTTPException(status_code=400, detail="ローラーCD・製品CD・設備CDは必須です")

    dup = await db.execute(
        select(RollerBom.id).where(
            RollerBom.roller_cd == new_rc.strip(),
            RollerBom.product_cd == new_pc.strip(),
            RollerBom.machine_cd == new_mc.strip(),
            RollerBom.id != item_id,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同一のローラーCD・製品CD・設備CDの組み合わせが既に登録されています")

    row.roller_cd = new_rc.strip()
    row.product_cd = new_pc.strip()
    row.machine_cd = new_mc.strip()
    if "roller_type" in body:
        v = body.get("roller_type")
        row.roller_type = str(v).strip() if v is not None and str(v).strip() else None

    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{item_id:int}")
async def delete_roller_bom(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(select(RollerBom).where(RollerBom.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ローラーBOMが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}

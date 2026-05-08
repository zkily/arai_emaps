"""
ローラーマスタ API（roller_master）
"""

import re
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, or_, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import RollerMaster

router = APIRouter()


class IdsPayload(BaseModel):
    ids: List[int]


def _to_optional_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    try:
        s = str(v).strip()
        if s == "":
            return None
        return int(float(s))
    except (TypeError, ValueError):
        return None


def _keyword_clause(keyword: Optional[str]):
    if not keyword or not str(keyword).strip():
        return None
    k = f"%{keyword.strip()}%"
    return or_(
        RollerMaster.roller_cd.like(k),
        RollerMaster.roller_name.like(k),
        RollerMaster.category.like(k),
        RollerMaster.machine_cd.like(k),
    )


_ROLLER_CD_A_NUM = re.compile(r"^A(\d+)$")


def _next_roller_cd_a_series(codes: List[str]) -> str:
    """既存の roller_cd のうち A + 数字 の最大値の次（3桁ゼロ埋め、例: A001）"""
    max_n = 0
    for raw in codes:
        cd = (raw or "").strip()
        m = _ROLLER_CD_A_NUM.match(cd)
        if not m:
            continue
        try:
            n = int(m.group(1))
        except ValueError:
            continue
        if n > max_n:
            max_n = n
    return f"A{max_n + 1:03d}"


def _row_to_dict(row: RollerMaster) -> dict:
    return {
        "id": row.id,
        "roller_cd": row.roller_cd,
        "roller_name": row.roller_name,
        "exchange_freq_qty": row.exchange_freq_qty,
        "exchange_freq_month": row.exchange_freq_month,
        "cleaning_freq_month": row.cleaning_freq_month,
        "category": row.category,
        "note": row.note,
        "machine_cd": row.machine_cd,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("")
async def list_roller_master(
    keyword: Optional[str] = Query(None),
    machine_cd: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=5000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ローラーマスタ一覧（ページング）"""
    where_expr = _keyword_clause(keyword)

    clauses = []
    if where_expr is not None:
        clauses.append(where_expr)
    if machine_cd is not None and str(machine_cd).strip():
        clauses.append(RollerMaster.machine_cd == str(machine_cd).strip())
    if category is not None and str(category).strip():
        clauses.append(RollerMaster.category == str(category).strip())

    if clauses:
        where_expr = and_(*clauses)
    else:
        where_expr = None

    count_stmt = select(func.count()).select_from(RollerMaster)
    if where_expr is not None:
        count_stmt = count_stmt.where(where_expr)
    total = (await db.execute(count_stmt)).scalar() or 0

    list_stmt = (
        select(RollerMaster)
        .order_by(RollerMaster.roller_cd)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if where_expr is not None:
        list_stmt = list_stmt.where(where_expr)

    result = await db.execute(list_stmt)
    rows = result.scalars().all()
    data_list = [_row_to_dict(r) for r in rows]

    return {
        "success": True,
        "data": {"list": data_list, "total": total},
        "list": data_list,
        "total": total,
    }


@router.get("/next-roller-cd")
async def get_next_roller_cd(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規用: roller_cd を A001 形式で自動採番（既存の A+数字 の最大 +1）"""
    stmt = select(RollerMaster.roller_cd)
    result = await db.execute(stmt)
    codes = [str(r[0]) for r in result.all() if r[0] is not None]
    roller_cd = _next_roller_cd_a_series(codes)
    return {"success": True, "roller_cd": roller_cd}


@router.get("/{item_id:int}")
async def get_roller_master_by_id(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """IDで1件取得"""
    result = await db.execute(select(RollerMaster).where(RollerMaster.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ローラーマスタが見つかりません")
    return _row_to_dict(row)


@router.post("")
async def create_roller_master(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """新規登録"""
    roller_cd = (body.get("roller_cd") or "").strip()
    if not roller_cd:
        raise HTTPException(status_code=400, detail="roller_cd は必須です")

    existing = await db.execute(select(RollerMaster.id).where(RollerMaster.roller_cd == roller_cd))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="この roller_cd は既に登録されています")

    row = RollerMaster(
        roller_cd=roller_cd,
        roller_name=(body.get("roller_name") or None) and str(body.get("roller_name")).strip() or None,
        exchange_freq_qty=_to_optional_int(body.get("exchange_freq_qty")),
        exchange_freq_month=_to_optional_int(body.get("exchange_freq_month")),
        cleaning_freq_month=_to_optional_int(body.get("cleaning_freq_month")),
        category=(body.get("category") or None) and str(body.get("category")).strip() or None,
        note=body.get("note"),
        machine_cd=(body.get("machine_cd") or None) and str(body.get("machine_cd")).strip() or None,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.put("/{item_id:int}")
async def update_roller_master(
    item_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """更新"""
    result = await db.execute(select(RollerMaster).where(RollerMaster.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ローラーマスタが見つかりません")

    if "roller_cd" in body:
        new_cd = (body.get("roller_cd") or "").strip()
        if not new_cd:
            raise HTTPException(status_code=400, detail="roller_cd は必須です")
        if new_cd != row.roller_cd:
            dup = await db.execute(select(RollerMaster.id).where(RollerMaster.roller_cd == new_cd))
            if dup.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="この roller_cd は既に登録されています")
            row.roller_cd = new_cd

    if "roller_name" in body:
        v = body.get("roller_name")
        row.roller_name = (str(v).strip() if v is not None and str(v).strip() else None)  # type: ignore[assignment]

    if "exchange_freq_qty" in body:
        row.exchange_freq_qty = _to_optional_int(body.get("exchange_freq_qty"))
    if "exchange_freq_month" in body:
        row.exchange_freq_month = _to_optional_int(body.get("exchange_freq_month"))
    if "cleaning_freq_month" in body:
        row.cleaning_freq_month = _to_optional_int(body.get("cleaning_freq_month"))

    if "category" in body:
        v = body.get("category")
        row.category = (str(v).strip() if v is not None and str(v).strip() else None)  # type: ignore[assignment]
    if "note" in body:
        row.note = body.get("note")
    if "machine_cd" in body:
        v = body.get("machine_cd")
        row.machine_cd = (str(v).strip() if v is not None and str(v).strip() else None)  # type: ignore[assignment]

    await db.commit()
    await db.refresh(row)
    return _row_to_dict(row)


@router.delete("/{item_id:int}")
async def delete_roller_master(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """削除"""
    result = await db.execute(select(RollerMaster).where(RollerMaster.id == item_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ローラーマスタが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


@router.post("/batch-delete")
async def batch_delete_roller_master(
    body: IdsPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """複数IDを一括削除"""
    ids = [i for i in body.ids if isinstance(i, int) and i > 0]
    if not ids:
        raise HTTPException(status_code=400, detail="ids が空です")
    await db.execute(delete(RollerMaster).where(RollerMaster.id.in_(ids)))
    await db.commit()
    return {"message": f"{len(ids)} 件削除しました", "deleted": len(ids)}

"""
工程ルートマスタ API（ルート一覧・CRUD、ステップCRUD・順序更新）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from typing import Optional, List

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import ProcessRoute, ProcessRouteStep
from app.modules.master.schemas import ProcessRouteCreate, ProcessRouteUpdate

router = APIRouter()


def _route_to_dict(row: ProcessRoute) -> dict:
    return {
        "id": row.id,
        "route_cd": row.route_cd,
        "route_name": row.route_name,
        "description": row.description,
        "is_active": bool(row.is_active),
        "is_default": bool(row.is_default),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _step_to_dict(row: ProcessRouteStep, process_name: Optional[str] = None) -> dict:
    d = {
        "id": row.id,
        "product_cd": row.product_cd,
        "route_cd": row.route_cd,
        "step_no": row.step_no,
        "process_cd": row.process_cd,
        "machine_id": row.machine_id,
        "standard_cycle_time": float(row.standard_cycle_time) if row.standard_cycle_time is not None else None,
        "setup_time": float(row.setup_time) if row.setup_time is not None else None,
        "remarks": row.remarks,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
    d["process_name"] = process_name if process_name is not None else row.process_cd
    return d


# ========== ルート一覧・CRUD ==========

@router.get("")
async def get_route_list(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=10000, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程ルート一覧取得"""
    query = select(ProcessRoute)
    if keyword:
        query = query.where(
            or_(
                ProcessRoute.route_cd.like(f"%{keyword}%"),
                ProcessRoute.route_name.like(f"%{keyword}%"),
                ProcessRoute.description.like(f"%{keyword}%"),
            )
        )
    count_q = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "success": True,
        "data": {
            "list": [_route_to_dict(r) for r in rows],
            "total": total,
        },
    }


@router.get("/by-cd/{route_cd}")
async def get_route_by_cd(
    route_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ルートCDで1件取得（ステップ編集画面用）"""
    q = select(ProcessRoute).where(ProcessRoute.route_cd == route_cd)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ルートが見つかりません")
    return _route_to_dict(row)


@router.get("/{route_id}")
async def get_route_by_id(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ルートIDで1件取得"""
    q = select(ProcessRoute).where(ProcessRoute.id == route_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ルートが見つかりません")
    return _route_to_dict(row)


@router.post("")
async def create_route(
    body: ProcessRouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程ルート新規登録"""
    q = select(ProcessRoute).where(ProcessRoute.route_cd == body.route_cd)
    ex = await db.execute(q)
    if ex.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="ルートCDは既に存在します")
    row = ProcessRoute(
        route_cd=body.route_cd,
        route_name=body.route_name,
        description=body.description,
        is_active=1 if body.is_active else 0,
        is_default=1 if body.is_default else 0,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _route_to_dict(row)


@router.put("/{route_id}")
async def update_route(
    route_id: int,
    body: ProcessRouteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程ルート更新"""
    q = select(ProcessRoute).where(ProcessRoute.id == route_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ルートが見つかりません")
    if body.route_cd is not None:
        row.route_cd = body.route_cd
    if body.route_name is not None:
        row.route_name = body.route_name
    if body.description is not None:
        row.description = body.description
    if hasattr(body, "is_active"):
        row.is_active = 1 if body.is_active else 0
    row.is_default = 1 if body.is_default else 0
    await db.commit()
    await db.refresh(row)
    return _route_to_dict(row)


@router.delete("/{route_id}")
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程ルート削除（ステップはCASCADEで削除）"""
    q = select(ProcessRoute).where(ProcessRoute.id == route_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ルートが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}


# ========== ステップ（product_cd + route_cd ベース） ==========


@router.get("/by-cd/{route_cd}/steps")
async def get_route_steps(
    route_cd: str,
    product_cd: str = Query(..., alias="productCd"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品別ルートのステップ一覧取得"""
    q = (
        select(ProcessRouteStep)
        .where(
            ProcessRouteStep.route_cd == route_cd,
            ProcessRouteStep.product_cd == product_cd,
        )
        .order_by(ProcessRouteStep.step_no)
    )
    res = await db.execute(q)
    rows = res.scalars().all()
    return [_step_to_dict(r) for r in rows]


class StepOrderItem(BaseModel):
    id: int
    step_no: int


@router.put("/by-cd/{route_cd}/steps/order")
async def update_step_order(
    route_cd: str,
    body: List[StepOrderItem],
    product_cd: str = Query(..., alias="productCd"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ステップ順序一括更新"""
    for item in body:
        q = select(ProcessRouteStep).where(
            ProcessRouteStep.id == item.id,
            ProcessRouteStep.route_cd == route_cd,
            ProcessRouteStep.product_cd == product_cd,
        )
        res = await db.execute(q)
        row = res.scalar_one_or_none()
        if row:
            row.step_no = item.step_no
    await db.commit()
    return {"message": "順序を更新しました"}


@router.post("/by-cd/{route_cd}/steps")
async def create_route_step(
    route_cd: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ステップ追加（body に product_cd 必須）"""
    product_cd = str(body.get("product_cd") or "")
    if not product_cd:
        raise HTTPException(status_code=400, detail="product_cd は必須です")
    step = ProcessRouteStep(
        product_cd=product_cd,
        route_cd=route_cd,
        step_no=int(body.get("step_no", 1)),
        process_cd=str(body.get("process_cd", "")),
        machine_id=body.get("machine_id"),
        standard_cycle_time=float(body["standard_cycle_time"]) if body.get("standard_cycle_time") is not None else None,
        setup_time=float(body["setup_time"]) if body.get("setup_time") is not None else None,
        remarks=body.get("remarks"),
    )
    db.add(step)
    await db.commit()
    await db.refresh(step)
    return _step_to_dict(step)


@router.put("/steps/{step_id}")
async def update_route_step(
    step_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ステップ更新"""
    q = select(ProcessRouteStep).where(ProcessRouteStep.id == step_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ステップが見つかりません")
    if "step_no" in body:
        row.step_no = int(body["step_no"])
    if "process_cd" in body:
        row.process_cd = str(body["process_cd"])
    if "machine_id" in body:
        row.machine_id = body["machine_id"]
    if "standard_cycle_time" in body:
        row.standard_cycle_time = float(body["standard_cycle_time"]) if body["standard_cycle_time"] is not None else None
    if "setup_time" in body:
        row.setup_time = float(body["setup_time"]) if body["setup_time"] is not None else None
    if "remarks" in body:
        row.remarks = body["remarks"]
    await db.commit()
    await db.refresh(row)
    return _step_to_dict(row)


@router.delete("/by-cd/{route_cd}/steps/{step_id}")
async def delete_route_step(
    route_cd: str,
    step_id: int,
    product_cd: str = Query(..., alias="productCd"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ステップ削除"""
    q = select(ProcessRouteStep).where(
        ProcessRouteStep.id == step_id,
        ProcessRouteStep.route_cd == route_cd,
        ProcessRouteStep.product_cd == product_cd,
    )
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="ステップが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}

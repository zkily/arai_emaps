"""
製品別工程ルートステップ API（product_route_steps / product_route_step_machines）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional, List, Any

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import (
    Product,
    ProcessRoute,
    Process,
    ProductRouteStep,
    ProductRouteStepMachine,
    Machine,
    Destination,
)

router = APIRouter()


# ========== 工程一覧（ダイアログ用） ==========


@router.get("")
async def get_process_list_for_routes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程一覧（製品別ルートの工程選択ダイアログ用）"""
    q = select(Process).order_by(Process.process_cd)
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {"process_cd": r.process_cd, "process_name": r.process_name}
        for r in rows
    ]


# ========== 製品ルート情報 ==========


@router.get("/{product_cd}")
async def get_product_route_info(
    product_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品の工程ルート情報（製品CD・名称・ルートCD・ルート名・納入先名）"""
    q = select(Product).where(Product.product_cd == product_cd)
    res = await db.execute(q)
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="製品が見つかりません")
    route_cd = product.route_cd
    route_name = ""
    if route_cd:
        rq = select(ProcessRoute).where(ProcessRoute.route_cd == route_cd)
        rr = await db.execute(rq)
        route = rr.scalar_one_or_none()
        if route:
            route_name = route.route_name or ""
    delivery_destination_name = ""
    if product.destination_cd:
        dq = select(Destination).where(Destination.destination_cd == product.destination_cd)
        dr = await db.execute(dq)
        dest = dr.scalar_one_or_none()
        if dest:
            delivery_destination_name = dest.destination_name or ""
    return {
        "product_cd": product.product_cd,
        "product_name": product.product_name,
        "route_cd": route_cd or "",
        "route_name": route_name,
        "delivery_destination_name": delivery_destination_name,
    }


# ========== 製品別工程ステップ一覧（設備含む） ==========


@router.get("/{product_cd}/{route_cd}")
async def get_product_route_steps(
    product_cd: str,
    route_cd: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品・ルートに紐づく工程ステップ一覧（設備付き）"""
    q = (
        select(ProductRouteStep, Process.process_name)
        .outerjoin(Process, Process.process_cd == ProductRouteStep.process_cd)
        .where(
            ProductRouteStep.product_cd == product_cd,
            ProductRouteStep.route_cd == route_cd,
        )
        .order_by(ProductRouteStep.step_no)
    )
    res = await db.execute(q)
    rows = res.all()
    step_ids = [r[0].id for r in rows]
    machines_q = (
        select(ProductRouteStepMachine)
        .where(
            ProductRouteStepMachine.product_cd == product_cd,
            ProductRouteStepMachine.route_cd == route_cd,
        )
    )
    machines_res = await db.execute(machines_q)
    machines_rows = machines_res.scalars().all()
    machines_by_step: dict[int, list] = {}
    for m in machines_rows:
        key = (m.step_no,)
        if key not in machines_by_step:
            machines_by_step[key] = []
        machines_by_step[key].append({
            "id": m.id,
            "machine_cd": m.machine_cd,
            "machine_name": m.machine_name or "",
            "process_time_sec": float(m.process_time_sec) if m.process_time_sec is not None else 0,
            "setup_time": int(m.setup_time) if m.setup_time is not None else 0,
        })
    result = []
    for step_row, process_name in rows:
        step_no = step_row.step_no
        result.append({
            "id": step_row.id,
            "product_cd": step_row.product_cd,
            "route_cd": step_row.route_cd,
            "step_no": step_no,
            "process_cd": step_row.process_cd,
            "process_name": process_name or step_row.process_cd,
            "machines": machines_by_step.get((step_no,), []),
        })
    return result


# ========== ステップ一括保存 ==========


class MachineItem(BaseModel):
    machine_cd: str = ""
    machine_name: Optional[str] = None
    process_time_sec: float = 0
    setup_time: float = 0


class StepItem(BaseModel):
    id: Optional[int] = None
    product_cd: str
    route_cd: str
    step_no: int
    process_cd: str
    process_name: Optional[str] = None
    machines: Optional[List[MachineItem]] = None


@router.post("/bulk")
async def save_product_route_steps_bulk(
    body: List[StepItem],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品別工程ステップ一括保存（ステップ＋設備）"""
    if not body:
        return {"message": "OK"}
    product_cd = body[0].product_cd
    route_cd = body[0].route_cd
    # 既存ステップ・設備を削除してから再登録
    await db.execute(
        delete(ProductRouteStepMachine).where(
            ProductRouteStepMachine.product_cd == product_cd,
            ProductRouteStepMachine.route_cd == route_cd,
        )
    )
    await db.execute(
        delete(ProductRouteStep).where(
            ProductRouteStep.product_cd == product_cd,
            ProductRouteStep.route_cd == route_cd,
        )
    )
    for item in body:
        step = ProductRouteStep(
            product_cd=item.product_cd,
            route_cd=item.route_cd,
            step_no=item.step_no,
            process_cd=item.process_cd,
        )
        db.add(step)
        await db.flush()
        for m in item.machines or []:
            if not m.machine_cd:
                continue
            db.add(
                ProductRouteStepMachine(
                    product_cd=item.product_cd,
                    route_cd=item.route_cd,
                    step_no=item.step_no,
                    machine_cd=m.machine_cd,
                    machine_name=m.machine_name or "",
                    process_time_sec=m.process_time_sec,
                    setup_time=int(m.setup_time),
                )
            )
    await db.commit()
    return {"message": "保存しました"}


# ========== 設備 1件追加 ==========


class MachineCreate(BaseModel):
    product_cd: str
    route_cd: str
    step_no: int
    machine_cd: str
    machine_name: Optional[str] = None
    process_time_sec: float = 0
    setup_time: float = 0


@router.post("/machines")
async def create_product_route_step_machine(
    body: MachineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品別工程ステップに設備1件追加"""
    row = ProductRouteStepMachine(
        product_cd=body.product_cd,
        route_cd=body.route_cd,
        step_no=body.step_no,
        machine_cd=body.machine_cd,
        machine_name=body.machine_name or "",
        process_time_sec=body.process_time_sec,
        setup_time=int(body.setup_time),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "message": "追加しました"}


# ========== 設備 1件更新 ==========


@router.put("/machines/{machine_id}")
async def update_product_route_step_machine(
    machine_id: int,
    body: MachineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品別工程ステップ設備1件更新"""
    q = select(ProductRouteStepMachine).where(ProductRouteStepMachine.id == machine_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備レコードが見つかりません")
    row.machine_cd = body.machine_cd
    row.machine_name = body.machine_name or ""
    row.process_time_sec = body.process_time_sec
    row.setup_time = int(body.setup_time)
    await db.commit()
    return {"message": "更新しました"}


# ========== 設備 1件削除 ==========


@router.delete("/machines/{machine_id}")
async def delete_product_route_step_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品別工程ステップ設備1件削除"""
    q = select(ProductRouteStepMachine).where(ProductRouteStepMachine.id == machine_id)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="設備レコードが見つかりません")
    await db.delete(row)
    await db.commit()
    return {"message": "削除しました"}

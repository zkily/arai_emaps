"""工場レイアウト API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_mes_operation
from app.modules.factory_layout.models import FactoryLayout, FactoryLayoutObject
from app.modules.factory_layout.schemas import (
    LayoutCreate,
    LayoutDetail,
    LayoutObjectIn,
    LayoutObjectOut,
    LayoutObjectsReplace,
    LayoutStatusResponse,
    LayoutSummary,
    LayoutUpdate,
    ObjectStatusOut,
    StatusUpdate,
)
from app.modules.factory_layout.status_provider import MockStatusProvider, StatusRejected
from app.modules.master.models import Material

router = APIRouter()

_MISSING_TABLE = (
    "factory_layout テーブルがありません。"
    "backend/database/migrations/147_factory_layout.sql を適用してください。"
)


def _missing_table(exc: Exception) -> bool:
    text = str(getattr(exc, "orig", exc))
    return "1146" in text or "doesn't exist" in text or "does not exist" in text


async def _execute(db: AsyncSession, stmt):
    try:
        return await db.execute(stmt)
    except (ProgrammingError, OperationalError) as exc:
        if _missing_table(exc):
            raise HTTPException(status_code=503, detail=_MISSING_TABLE) from exc
        raise


def _clean_ref(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _apply_object_fields(row: FactoryLayoutObject, item: LayoutObjectIn) -> None:
    row.object_type = item.object_type
    row.x = item.x
    row.y = item.y
    row.width = item.width
    row.height = item.height
    row.label = item.label.strip()
    row.ref_cd = _clean_ref(item.ref_cd)
    row.z_index = item.z_index
    row.rotation = item.rotation
    row.locked = item.locked
    row.group_key = _clean_ref(item.group_key)
    row.fill_color = item.fill_color
    row.border_color = item.border_color
    row.opacity = item.opacity
    row.child_layout_id = item.child_layout_id


async def _clean_child(db: AsyncSession, layout_id: int, child_id: int | None) -> int | None:
    if not child_id or child_id == layout_id:
        return None
    result = await _execute(db, select(FactoryLayout.id).where(FactoryLayout.id == child_id))
    if result.scalar_one_or_none() is None:
        return None
    return child_id


def _summary(row: FactoryLayout) -> LayoutSummary:
    return LayoutSummary.model_validate(row)


def _detail(row: FactoryLayout, objects: list[FactoryLayoutObject]) -> LayoutDetail:
    base = _summary(row)
    return LayoutDetail(
        **base.model_dump(),
        objects=[_object_out(obj) for obj in objects],
    )


def _object_out(row: FactoryLayoutObject) -> LayoutObjectOut:
    return LayoutObjectOut.model_validate(row)


async def _get_layout(db: AsyncSession, layout_id: int) -> FactoryLayout:
    result = await _execute(db, select(FactoryLayout).where(FactoryLayout.id == layout_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="レイアウトが見つかりません")
    return row


async def _objects_of(db: AsyncSession, layout_id: int) -> list[FactoryLayoutObject]:
    result = await _execute(
        db,
        select(FactoryLayoutObject)
        .where(FactoryLayoutObject.layout_id == layout_id)
        .order_by(FactoryLayoutObject.z_index, FactoryLayoutObject.id),
    )
    return list(result.scalars().all())


@router.get("/layouts", response_model=list[LayoutSummary])
async def list_layouts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await _execute(db, select(FactoryLayout).order_by(FactoryLayout.id))
    return [_summary(row) for row in result.scalars().all()]


@router.post("/layouts", response_model=LayoutDetail)
async def create_layout(
    body: LayoutCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("create")),
):
    parent_id = body.parent_id
    if body.kind == "site":
        parent_id = None
    elif parent_id is not None:
        await _get_layout(db, parent_id)
    row = FactoryLayout(
        name=body.name.strip(),
        canvas_width=body.canvas_width,
        canvas_height=body.canvas_height,
        grid_size=body.grid_size,
        kind=body.kind,
        parent_id=parent_id,
    )
    db.add(row)
    try:
        await db.commit()
    except (ProgrammingError, OperationalError) as exc:
        await db.rollback()
        if _missing_table(exc):
            raise HTTPException(status_code=503, detail=_MISSING_TABLE) from exc
        raise
    await db.refresh(row)
    return _detail(row, [])


@router.get("/storage-locations", response_model=list[str])
async def list_storage_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await _execute(
        db,
        select(Material.storage_location)
        .where(Material.storage_location.is_not(None))
        .where(func.trim(Material.storage_location) != "")
        .distinct()
        .order_by(Material.storage_location)
        .limit(500),
    )
    return [str(value) for value in result.scalars().all() if value]


@router.get("/layouts/{layout_id}", response_model=LayoutDetail)
async def get_layout(
    layout_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    layout = await _get_layout(db, layout_id)
    objects = await _objects_of(db, layout_id)
    return _detail(layout, objects)


@router.put("/layouts/{layout_id}", response_model=LayoutSummary)
async def update_layout(
    layout_id: int,
    body: LayoutUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    layout = await _get_layout(db, layout_id)
    if body.name is not None:
        layout.name = body.name.strip()
    if body.canvas_width is not None:
        layout.canvas_width = body.canvas_width
    if body.canvas_height is not None:
        layout.canvas_height = body.canvas_height
    if body.grid_size is not None:
        layout.grid_size = body.grid_size
    await db.commit()
    await db.refresh(layout)
    return _summary(layout)


@router.delete("/layouts/{layout_id}")
async def delete_layout(
    layout_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("delete")),
):
    layout = await _get_layout(db, layout_id)
    await db.delete(layout)
    await db.commit()
    return {"message": "deleted"}


@router.put("/layouts/{layout_id}/objects", response_model=list[LayoutObjectOut])
async def replace_objects(
    layout_id: int,
    body: LayoutObjectsReplace,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    await _get_layout(db, layout_id)
    existing_rows = await _objects_of(db, layout_id)
    existing = {row.id: row for row in existing_rows}
    keep_ids: set[int] = set()
    for item in body.objects:
        item.child_layout_id = await _clean_child(db, layout_id, item.child_layout_id)
    for item in body.objects:
        if item.id and item.id in existing:
            keep_ids.add(item.id)
            _apply_object_fields(existing[item.id], item)
    for object_id, row in existing.items():
        if object_id not in keep_ids:
            await db.delete(row)
    await db.flush()
    for item in body.objects:
        if item.id and item.id in existing:
            continue
        db.add(
            FactoryLayoutObject(
                layout_id=layout_id,
                object_type=item.object_type,
                x=item.x,
                y=item.y,
                width=item.width,
                height=item.height,
                label=item.label.strip(),
                ref_cd=_clean_ref(item.ref_cd),
                z_index=item.z_index,
                rotation=item.rotation,
                locked=item.locked,
                group_key=_clean_ref(item.group_key),
                fill_color=item.fill_color,
                border_color=item.border_color,
                opacity=item.opacity,
                child_layout_id=item.child_layout_id,
            )
        )
    await db.commit()
    saved = await _objects_of(db, layout_id)
    return [_object_out(obj) for obj in saved]


@router.get("/layouts/{layout_id}/status", response_model=LayoutStatusResponse)
async def get_layout_status(
    layout_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    await _get_layout(db, layout_id)
    objects = await _objects_of(db, layout_id)
    provider = MockStatusProvider(db)
    try:
        statuses = await provider.statuses_for(objects)
    except (ProgrammingError, OperationalError) as exc:
        if _missing_table(exc):
            raise HTTPException(status_code=503, detail=_MISSING_TABLE) from exc
        raise
    return LayoutStatusResponse(statuses=statuses)


@router.put("/objects/{object_id}/status", response_model=ObjectStatusOut)
async def update_object_status(
    object_id: int,
    body: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_mes_operation("edit")),
):
    result = await _execute(
        db, select(FactoryLayoutObject).where(FactoryLayoutObject.id == object_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="オブジェクトが見つかりません")
    provider = MockStatusProvider(db)
    try:
        row = await provider.set_mock_status(obj, body.status.strip(), body.message)
    except StatusRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except (ProgrammingError, OperationalError) as exc:
        await db.rollback()
        if _missing_table(exc):
            raise HTTPException(status_code=503, detail=_MISSING_TABLE) from exc
        raise
    payload = row.payload if isinstance(row.payload, dict) else None
    return ObjectStatusOut(
        status=row.status,
        message=row.message or "",
        updated_at=row.updated_at,
        source=row.source or "mock",
        payload=payload,
    )

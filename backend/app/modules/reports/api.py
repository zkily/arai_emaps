"""レポート配信 API（定義・プレビュー・手動送信・スケジュール・履歴）"""
from __future__ import annotations

import io
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.reports.models import ReportDefinition, ReportSchedule, ReportSendLog
from app.modules.reports.definition_defaults import (
    apply_cutting_report_defaults,
    cutting_report_needs_default_sync,
)
from app.modules.reports.schemas import (
    ReportDefinitionResponse,
    ReportDownloadRequest,
    ReportPreviewRequest,
    ReportScheduleCreate,
    ReportScheduleResponse,
    ReportScheduleUpdate,
    ReportSendLogResponse,
    ReportSendRequest,
)

router = APIRouter()


async def _sync_definition_defaults(db: AsyncSession, definitions: list[ReportDefinition]) -> None:
    changed = False
    for definition in definitions:
        if cutting_report_needs_default_sync(definition):
            apply_cutting_report_defaults(definition)
            changed = True
    if changed:
        await db.commit()


@router.get("/definitions", response_model=list[ReportDefinitionResponse])
async def list_report_definitions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(
        select(ReportDefinition).where(ReportDefinition.is_active.is_(True)).order_by(ReportDefinition.id)
    )
    definitions = list(result.scalars().all())
    await _sync_definition_defaults(db, definitions)
    return definitions


@router.get("/definitions/{report_code}", response_model=ReportDefinitionResponse)
async def get_report_definition(
    report_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    result = await db.execute(
        select(ReportDefinition).where(ReportDefinition.report_code == report_code)
    )
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="レポート定義が見つかりません")
    await _sync_definition_defaults(db, [definition])
    return definition


@router.post("/{report_code}/preview")
async def preview_report(
    report_code: str,
    body: ReportPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    from app.services.report_delivery_service import get_report_preview

    return await get_report_preview(db, report_code=report_code, parameters=body.parameters)


@router.post("/{report_code}/download")
async def download_report(
    report_code: str,
    body: ReportDownloadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    from app.services.report_delivery_service import generate_report

    _, report, _ = await generate_report(
        db, report_code=report_code, parameters=body.parameters, fmt=body.format
    )
    if not report.attachments:
        raise HTTPException(status_code=400, detail="ダウンロード可能なファイルがありません")
    attachment = report.attachments[0]
    filename_encoded = quote(attachment.filename)
    return StreamingResponse(
        io.BytesIO(attachment.content),
        media_type=attachment.mime_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"},
    )


@router.post("/{report_code}/send")
async def send_report_endpoint(
    report_code: str,
    body: ReportSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    from app.services.report_delivery_service import send_report

    return await send_report(
        db,
        report_code=report_code,
        parameters=body.parameters,
        fmt=body.format,
        trigger="manual",
        current_user=current_user,
    )


# ========== スケジュール ==========

@router.get("/schedules", response_model=list[ReportScheduleResponse])
async def list_schedules(
    report_code: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    stmt = select(ReportSchedule).order_by(ReportSchedule.id.desc())
    if report_code:
        stmt = stmt.where(ReportSchedule.report_code == report_code)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/schedules", response_model=ReportScheduleResponse)
async def create_schedule(
    body: ReportScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    definition = (
        await db.execute(select(ReportDefinition).where(ReportDefinition.report_code == body.report_code))
    ).scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=400, detail="存在しないレポートコードです")

    from app.services.report_scheduler_service import refresh_schedule_next_run_at

    schedule = ReportSchedule(
        report_code=body.report_code,
        schedule_type=body.schedule_type,
        schedule_time=body.schedule_time,
        schedule_config=body.schedule_config,
        parameters=body.parameters,
        format=body.format,
        is_active=body.is_active,
        created_by=current_user.id,
    )
    db.add(schedule)
    await db.flush()
    await refresh_schedule_next_run_at(db, schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.put("/schedules/{schedule_id}", response_model=ReportScheduleResponse)
async def update_schedule(
    schedule_id: int,
    body: ReportScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    schedule = (
        await db.execute(select(ReportSchedule).where(ReportSchedule.id == schedule_id))
    ).scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")

    from app.services.report_scheduler_service import refresh_schedule_next_run_at

    schedule_fields = body.model_dump(exclude_unset=True)
    for field_name, value in schedule_fields.items():
        setattr(schedule, field_name, value)
    if schedule_fields.keys() & {
        "schedule_type",
        "schedule_time",
        "schedule_config",
        "is_active",
    }:
        await refresh_schedule_next_run_at(db, schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    schedule = (
        await db.execute(select(ReportSchedule).where(ReportSchedule.id == schedule_id))
    ).scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")
    await db.delete(schedule)
    await db.commit()
    return {"success": True}


# ========== 送信履歴 ==========

@router.get("/send-logs")
async def list_send_logs(
    report_code: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    base = select(ReportSendLog)
    if report_code:
        base = base.where(ReportSendLog.report_code == report_code)
    base = base.order_by(ReportSendLog.id.desc())
    rows = (await db.execute(base.offset((page - 1) * limit).limit(limit))).scalars().all()
    return {
        "success": True,
        "data": [ReportSendLogResponse.model_validate(r) for r in rows],
        "page": page,
        "limit": limit,
    }

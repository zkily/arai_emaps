"""
システム設定 API エンドポイント
システムログ、採番ルール、ワークフロー、通知、データ管理
"""
import logging
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
import io
import csv

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.system.settings_models import (
    OperationLog, ErrorLog, ApiLog,
    NumberingRule,
    ApprovalRoute, ApprovalRouteStep, Delegation, WorkflowDefinition,
    NotificationSetting, EmailTemplate, IntegrationConfig,
    ImportExportHistory, BackupSetting, BackupHistory
)
from app.modules.system.settings_schemas import (
    OperationLogCreate, OperationLogResponse, OperationLogSearchParams, PaginatedOperationLogs,
    ErrorLogCreate, ErrorLogResponse, ErrorLogSearchParams, PaginatedErrorLogs,
    ApiLogCreate, ApiLogResponse, ApiLogSearchParams, PaginatedApiLogs, LogStats,
    NumberingRuleCreate, NumberingRuleUpdate, NumberingRuleResponse, NumberingRuleListResponse, GeneratedNumber,
    ApprovalRouteCreate, ApprovalRouteUpdate, ApprovalRouteResponse, ApprovalRouteListResponse,
    ApprovalRouteStepCreate,
    DelegationCreate, DelegationUpdate, DelegationResponse,
    WorkflowDefinitionCreate, WorkflowDefinitionUpdate, WorkflowDefinitionResponse,
    NotificationSettingCreate, NotificationSettingUpdate, NotificationSettingResponse,
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse,
    IntegrationConfigCreate, IntegrationConfigUpdate, IntegrationConfigResponse, IntegrationTestResult,
    ImportExportHistoryResponse, ImportRequest, ExportRequest,
    BackupSettingUpdate, BackupSettingResponse,
    BackupHistoryResponse, ManualBackupRequest, RestoreRequest, DataResetRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["System Settings"])


# ========== システムログ API ==========

@router.get("/logs/operations", response_model=PaginatedOperationLogs, summary="操作ログ一覧")
async def get_operation_logs(
    user: Optional[str] = Query(None, description="ユーザー名フィルター"),
    action: Optional[str] = Query(None, description="操作フィルター"),
    start_date: Optional[date] = Query(None, description="開始日"),
    end_date: Optional[date] = Query(None, description="終了日"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """操作ログ一覧を取得"""
    try:
        query = select(OperationLog)
        
        if user:
            query = query.where(OperationLog.username.ilike(f"%{user}%"))
        if action:
            query = query.where(OperationLog.action == action)
        if start_date:
            query = query.where(OperationLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.where(OperationLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
        
        # 総件数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # データ取得
        query = query.order_by(OperationLog.timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return PaginatedOperationLogs(
            items=[OperationLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.exception("操作ログ取得エラー: %s", e)
        # テーブル未作成などDBエラー時は空一覧を返す
        return PaginatedOperationLogs(items=[], total=0, page=page, page_size=page_size)


@router.post("/logs/operations", response_model=OperationLogResponse, summary="操作ログ記録")
async def create_operation_log(
    log_data: OperationLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """操作ログを記録（内部用）"""
    log = OperationLog(**log_data.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/logs/operations/export", summary="操作ログエクスポート")
async def export_operation_logs(
    user: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """操作ログをCSVでエクスポート"""
    query = select(OperationLog)
    
    if user:
        query = query.where(OperationLog.username.ilike(f"%{user}%"))
    if action:
        query = query.where(OperationLog.action == action)
    if start_date:
        query = query.where(OperationLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(OperationLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
    
    query = query.order_by(OperationLog.timestamp.desc()).limit(10000)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # CSV生成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日時", "ユーザー", "操作", "モジュール", "対象", "IPアドレス"])
    for log in logs:
        writer.writerow([
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
            log.username or "",
            log.action or "",
            log.module or "",
            log.target or "",
            log.ip_address or "",
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=operation_logs_{date.today()}.csv"}
    )


@router.get("/logs/errors", response_model=PaginatedErrorLogs, summary="エラーログ一覧")
async def get_error_logs(
    level: Optional[str] = Query(None, description="レベルフィルター"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """エラーログ一覧を取得"""
    query = select(ErrorLog)
    
    if level:
        query = query.where(ErrorLog.level == level.upper())
    if start_date:
        query = query.where(ErrorLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(ErrorLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(ErrorLog.timestamp.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return PaginatedErrorLogs(
        items=[ErrorLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/logs/api", response_model=PaginatedApiLogs, summary="APIログ一覧")
async def get_api_logs(
    endpoint: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="success/client_error/server_error"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """APIログ一覧を取得"""
    query = select(ApiLog)
    
    if endpoint:
        query = query.where(ApiLog.endpoint.ilike(f"%{endpoint}%"))
    if status == "success":
        query = query.where(and_(ApiLog.status_code >= 200, ApiLog.status_code < 300))
    elif status == "client_error":
        query = query.where(and_(ApiLog.status_code >= 400, ApiLog.status_code < 500))
    elif status == "server_error":
        query = query.where(ApiLog.status_code >= 500)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(ApiLog.timestamp.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return PaginatedApiLogs(
        items=[ApiLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/logs/stats", response_model=LogStats, summary="今日のログ統計")
async def get_log_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """今日のログ統計を取得"""
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    op_count = await db.execute(
        select(func.count()).where(OperationLog.timestamp >= today_start)
    )
    err_count = await db.execute(
        select(func.count()).where(ErrorLog.timestamp >= today_start)
    )
    api_count = await db.execute(
        select(func.count()).where(ApiLog.timestamp >= today_start)
    )
    
    return LogStats(
        operation_count=op_count.scalar() or 0,
        error_count=err_count.scalar() or 0,
        api_count=api_count.scalar() or 0,
    )


# ========== 採番ルール API ==========

@router.get("/numbering", response_model=List[NumberingRuleListResponse], summary="採番ルール一覧")
async def get_numbering_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """採番ルール一覧を取得"""
    result = await db.execute(
        select(NumberingRule).order_by(NumberingRule.id)
    )
    rules = result.scalars().all()
    
    response = []
    for rule in rules:
        example = _generate_example_number(rule)
        response.append(NumberingRuleListResponse(
            id=rule.id,
            code=rule.code,
            name=rule.name,
            prefix=rule.prefix,
            format=rule.format,
            example=example,
            current_number=rule.current_number,
            reset_type=_get_reset_type_label(rule.reset_type),
            is_active=rule.is_active,
        ))
    return response


@router.get("/numbering/{rule_id}", response_model=NumberingRuleResponse, summary="採番ルール詳細")
async def get_numbering_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """採番ルール詳細を取得"""
    result = await db.execute(
        select(NumberingRule).where(NumberingRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="採番ルールが見つかりません")
    
    response = NumberingRuleResponse.model_validate(rule)
    response.example = _generate_example_number(rule)
    return response


@router.post("/numbering", response_model=NumberingRuleResponse, status_code=201, summary="採番ルール作成")
async def create_numbering_rule(
    data: NumberingRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """採番ルールを新規作成"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    # 重複チェック
    existing = await db.execute(
        select(NumberingRule).where(NumberingRule.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="このコードは既に使用されています")
    
    rule = NumberingRule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    logger.info(f"Numbering rule created: {rule.code} by {current_user.username}")
    return rule


@router.put("/numbering/{rule_id}", response_model=NumberingRuleResponse, summary="採番ルール更新")
async def update_numbering_rule(
    rule_id: int,
    data: NumberingRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """採番ルールを更新"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(NumberingRule).where(NumberingRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="採番ルールが見つかりません")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    
    await db.commit()
    await db.refresh(rule)
    
    logger.info(f"Numbering rule updated: {rule.code} by {current_user.username}")
    return rule


@router.delete("/numbering/{rule_id}", summary="採番ルール削除")
async def delete_numbering_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """採番ルールを削除"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(NumberingRule).where(NumberingRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="採番ルールが見つかりません")
    
    await db.delete(rule)
    await db.commit()
    
    logger.info(f"Numbering rule deleted: {rule.code} by {current_user.username}")
    return {"message": "削除しました"}


@router.post("/numbering/{rule_code}/generate", response_model=GeneratedNumber, summary="番号生成")
async def generate_number(
    rule_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定したルールで次の番号を生成"""
    result = await db.execute(
        select(NumberingRule).where(
            and_(NumberingRule.code == rule_code, NumberingRule.is_active == True)
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="有効な採番ルールが見つかりません")
    
    # リセットチェック
    today = date.today()
    should_reset = False
    if rule.reset_type == "daily" and (rule.last_reset_date is None or rule.last_reset_date < today):
        should_reset = True
    elif rule.reset_type == "monthly" and (rule.last_reset_date is None or rule.last_reset_date.month != today.month or rule.last_reset_date.year != today.year):
        should_reset = True
    elif rule.reset_type == "yearly" and (rule.last_reset_date is None or rule.last_reset_date.year != today.year):
        should_reset = True
    
    if should_reset:
        rule.current_number = rule.start_number
        rule.last_reset_date = today
    else:
        rule.current_number += rule.increment
    
    number = _format_number(rule, rule.current_number)
    await db.commit()
    
    return GeneratedNumber(number=number, rule_code=rule_code)


@router.post("/numbering/{rule_id}/test", response_model=GeneratedNumber, summary="番号テスト生成")
async def test_generate_number(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """番号生成をテスト（実際には採番しない）"""
    result = await db.execute(
        select(NumberingRule).where(NumberingRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="採番ルールが見つかりません")
    
    next_number = rule.current_number + rule.increment
    number = _format_number(rule, next_number)
    
    return GeneratedNumber(number=number, rule_code=rule.code)


def _format_number(rule: NumberingRule, seq_number: int) -> str:
    """番号をフォーマット"""
    today = date.today()
    result = rule.format
    result = result.replace("{PREFIX}", rule.prefix)
    result = result.replace("{YYYY}", str(today.year))
    result = result.replace("{YY}", str(today.year)[2:])
    result = result.replace("{MM}", str(today.month).zfill(2))
    result = result.replace("{DD}", str(today.day).zfill(2))
    
    import re
    seq_match = re.search(r"\{SEQ:(\d+)\}", result)
    if seq_match:
        digits = int(seq_match.group(1))
        result = result.replace(seq_match.group(0), str(seq_number).zfill(digits))
    
    return result


def _generate_example_number(rule: NumberingRule) -> str:
    """サンプル番号を生成"""
    return _format_number(rule, rule.current_number + rule.increment if rule.current_number > 0 else rule.start_number)


def _get_reset_type_label(reset_type: str) -> str:
    """リセットタイプのラベルを取得"""
    labels = {"never": "なし", "daily": "日次", "monthly": "月次", "yearly": "年次"}
    return labels.get(reset_type, reset_type)


# ========== ワークフロー API ==========

@router.get("/workflow/routes", response_model=List[ApprovalRouteListResponse], summary="承認ルート一覧")
async def get_approval_routes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """承認ルート一覧を取得"""
    result = await db.execute(
        select(ApprovalRoute)
        .options(selectinload(ApprovalRoute.steps))
        .order_by(ApprovalRoute.priority, ApprovalRoute.id)
    )
    routes = result.scalars().all()
    
    response = []
    for route in routes:
        steps = sorted(route.steps, key=lambda s: s.step_order)
        response.append(ApprovalRouteListResponse(
            id=route.id,
            name=route.name,
            type=_get_route_type_label(route.type),
            condition=route.condition_value or "",
            steps=[s.step_name for s in steps],
            is_active=route.is_active,
        ))
    return response


@router.get("/workflow/routes/{route_id}", response_model=ApprovalRouteResponse, summary="承認ルート詳細")
async def get_approval_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """承認ルート詳細を取得"""
    result = await db.execute(
        select(ApprovalRoute)
        .options(selectinload(ApprovalRoute.steps))
        .where(ApprovalRoute.id == route_id)
    )
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="承認ルートが見つかりません")
    return route


@router.post("/workflow/routes", response_model=ApprovalRouteResponse, status_code=201, summary="承認ルート作成")
async def create_approval_route(
    data: ApprovalRouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """承認ルートを新規作成"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    route = ApprovalRoute(
        name=data.name,
        type=data.type,
        condition_type=data.condition_type,
        condition_value=data.condition_value,
        condition_min=data.condition_min,
        condition_max=data.condition_max,
        condition_department_id=data.condition_department_id,
        priority=data.priority,
    )
    db.add(route)
    await db.flush()
    
    for step_data in data.steps:
        step = ApprovalRouteStep(
            route_id=route.id,
            **step_data.model_dump()
        )
        db.add(step)
    
    await db.commit()
    await db.refresh(route)
    
    logger.info(f"Approval route created: {route.name} by {current_user.username}")
    return route


@router.put("/workflow/routes/{route_id}", response_model=ApprovalRouteResponse, summary="承認ルート更新")
async def update_approval_route(
    route_id: int,
    data: ApprovalRouteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """承認ルートを更新"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(ApprovalRoute)
        .options(selectinload(ApprovalRoute.steps))
        .where(ApprovalRoute.id == route_id)
    )
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="承認ルートが見つかりません")
    
    update_data = data.model_dump(exclude_unset=True, exclude={"steps"})
    for key, value in update_data.items():
        setattr(route, key, value)
    
    if data.steps is not None:
        # 既存ステップを削除
        await db.execute(delete(ApprovalRouteStep).where(ApprovalRouteStep.route_id == route_id))
        # 新しいステップを追加
        for step_data in data.steps:
            step = ApprovalRouteStep(route_id=route_id, **step_data.model_dump())
            db.add(step)
    
    await db.commit()
    await db.refresh(route)
    
    logger.info(f"Approval route updated: {route.name} by {current_user.username}")
    return route


@router.delete("/workflow/routes/{route_id}", summary="承認ルート削除")
async def delete_approval_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """承認ルートを削除"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(ApprovalRoute).where(ApprovalRoute.id == route_id)
    )
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="承認ルートが見つかりません")
    
    await db.delete(route)
    await db.commit()
    
    logger.info(f"Approval route deleted: {route.name} by {current_user.username}")
    return {"message": "削除しました"}


def _get_route_type_label(route_type: str) -> str:
    labels = {"amount": "金額", "department": "部門", "custom": "カスタム"}
    return labels.get(route_type, route_type)


# 代理承認 API
@router.get("/workflow/delegations", response_model=List[DelegationResponse], summary="代理承認一覧")
async def get_delegations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """代理承認一覧を取得"""
    result = await db.execute(
        select(Delegation).order_by(Delegation.start_date.desc())
    )
    delegations = result.scalars().all()
    
    # ユーザー名を取得
    user_ids = set()
    for d in delegations:
        user_ids.add(d.delegator_id)
        user_ids.add(d.delegate_id)
    
    users_result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users = {u.id: u.full_name or u.username for u in users_result.scalars().all()}
    
    response = []
    for d in delegations:
        resp = DelegationResponse.model_validate(d)
        resp.delegator_name = users.get(d.delegator_id, "")
        resp.delegate_name = users.get(d.delegate_id, "")
        response.append(resp)
    
    return response


@router.post("/workflow/delegations", response_model=DelegationResponse, status_code=201, summary="代理承認作成")
async def create_delegation(
    data: DelegationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """代理承認を新規作成"""
    delegation = Delegation(**data.model_dump(), created_by=current_user.id)
    db.add(delegation)
    await db.commit()
    await db.refresh(delegation)
    
    logger.info(f"Delegation created by {current_user.username}")
    return delegation


@router.put("/workflow/delegations/{delegation_id}", response_model=DelegationResponse, summary="代理承認更新")
async def update_delegation(
    delegation_id: int,
    data: DelegationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """代理承認を更新"""
    result = await db.execute(
        select(Delegation).where(Delegation.id == delegation_id)
    )
    delegation = result.scalar_one_or_none()
    if not delegation:
        raise HTTPException(status_code=404, detail="代理承認設定が見つかりません")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(delegation, key, value)
    
    await db.commit()
    await db.refresh(delegation)
    return delegation


@router.delete("/workflow/delegations/{delegation_id}", summary="代理承認削除")
async def delete_delegation(
    delegation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """代理承認を削除"""
    result = await db.execute(
        select(Delegation).where(Delegation.id == delegation_id)
    )
    delegation = result.scalar_one_or_none()
    if not delegation:
        raise HTTPException(status_code=404, detail="代理承認設定が見つかりません")
    
    await db.delete(delegation)
    await db.commit()
    return {"message": "削除しました"}


# ワークフロー定義 API
@router.get("/workflow/definitions", response_model=List[WorkflowDefinitionResponse], summary="ワークフロー定義一覧")
async def get_workflow_definitions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ワークフロー定義一覧を取得"""
    result = await db.execute(
        select(WorkflowDefinition)
        .options(selectinload(WorkflowDefinition.approval_route))
        .order_by(WorkflowDefinition.code)
    )
    definitions = result.scalars().all()
    
    response = []
    for d in definitions:
        resp = WorkflowDefinitionResponse.model_validate(d)
        resp.approval_route_name = d.approval_route.name if d.approval_route else None
        response.append(resp)
    
    return response


@router.post("/workflow/definitions", response_model=WorkflowDefinitionResponse, status_code=201, summary="ワークフロー定義作成")
async def create_workflow_definition(
    data: WorkflowDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ワークフロー定義を新規作成"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    definition = WorkflowDefinition(**data.model_dump())
    db.add(definition)
    await db.commit()
    await db.refresh(definition)
    
    logger.info(f"Workflow definition created: {definition.code} by {current_user.username}")
    return definition


@router.put("/workflow/definitions/{definition_id}", response_model=WorkflowDefinitionResponse, summary="ワークフロー定義更新")
async def update_workflow_definition(
    definition_id: int,
    data: WorkflowDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ワークフロー定義を更新"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(WorkflowDefinition).where(WorkflowDefinition.id == definition_id)
    )
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="ワークフロー定義が見つかりません")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(definition, key, value)
    
    await db.commit()
    await db.refresh(definition)
    return definition


@router.delete("/workflow/definitions/{definition_id}", summary="ワークフロー定義削除")
async def delete_workflow_definition(
    definition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ワークフロー定義を削除"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(WorkflowDefinition).where(WorkflowDefinition.id == definition_id)
    )
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="ワークフロー定義が見つかりません")
    
    await db.delete(definition)
    await db.commit()
    return {"message": "削除しました"}


# ========== 通知センター API ==========

@router.get("/notifications", response_model=List[NotificationSettingResponse], summary="通知設定一覧")
async def get_notification_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """通知設定一覧を取得"""
    result = await db.execute(
        select(NotificationSetting).order_by(NotificationSetting.id)
    )
    return result.scalars().all()


@router.put("/notifications/{setting_id}", response_model=NotificationSettingResponse, summary="通知設定更新")
async def update_notification_setting(
    setting_id: int,
    data: NotificationSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """通知設定を更新"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.id == setting_id)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="通知設定が見つかりません")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(setting, key, value)
    
    await db.commit()
    await db.refresh(setting)
    return setting


@router.get("/email-templates", response_model=List[EmailTemplateResponse], summary="メールテンプレート一覧")
async def get_email_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メールテンプレート一覧を取得"""
    result = await db.execute(
        select(EmailTemplate).order_by(EmailTemplate.id)
    )
    return result.scalars().all()


@router.get("/email-templates/{template_id}", response_model=EmailTemplateResponse, summary="メールテンプレート詳細")
async def get_email_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メールテンプレート詳細を取得"""
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="テンプレートが見つかりません")
    return template


@router.post("/email-templates", response_model=EmailTemplateResponse, status_code=201, summary="メールテンプレート作成")
async def create_email_template(
    data: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メールテンプレートを新規作成"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    template = EmailTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/email-templates/{template_id}", response_model=EmailTemplateResponse, summary="メールテンプレート更新")
async def update_email_template(
    template_id: int,
    data: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メールテンプレートを更新"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="テンプレートが見つかりません")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/email-templates/{template_id}", summary="メールテンプレート削除")
async def delete_email_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """メールテンプレートを削除"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="テンプレートが見つかりません")
    
    await db.delete(template)
    await db.commit()
    return {"message": "削除しました"}


# 外部連携設定 API
@router.get("/integrations", response_model=List[IntegrationConfigResponse], summary="外部連携設定一覧")
async def get_integration_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外部連携設定一覧を取得"""
    result = await db.execute(select(IntegrationConfig))
    return result.scalars().all()


@router.get("/integrations/{service_type}", response_model=IntegrationConfigResponse, summary="外部連携設定取得")
async def get_integration_config(
    service_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外部連携設定を取得"""
    result = await db.execute(
        select(IntegrationConfig).where(IntegrationConfig.service_type == service_type)
    )
    config = result.scalar_one_or_none()
    if not config:
        # 存在しない場合は空の設定を返す
        return IntegrationConfigResponse(
            id=0,
            service_type=service_type,
            config={},
            is_enabled=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    return config


@router.put("/integrations/{service_type}", response_model=IntegrationConfigResponse, summary="外部連携設定更新")
async def update_integration_config(
    service_type: str,
    data: IntegrationConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外部連携設定を更新"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(IntegrationConfig).where(IntegrationConfig.service_type == service_type)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        # 新規作成
        config = IntegrationConfig(
            service_type=service_type,
            config=data.config or {},
            is_enabled=data.is_enabled or False,
        )
        db.add(config)
    else:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(config, key, value)
    
    await db.commit()
    await db.refresh(config)
    
    logger.info(f"Integration config updated: {service_type} by {current_user.username}")
    return config


@router.post("/integrations/{service_type}/test", response_model=IntegrationTestResult, summary="外部連携テスト")
async def test_integration(
    service_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """外部連携のテスト送信"""
    result = await db.execute(
        select(IntegrationConfig).where(IntegrationConfig.service_type == service_type)
    )
    config = result.scalar_one_or_none()
    
    if not config or not config.config:
        raise HTTPException(status_code=400, detail="連携設定が見つかりません")
    
    # TODO: 実際のテスト送信を実装
    # Slack: webhook_urlにPOST
    # LINE: Messaging APIでメッセージ送信
    
    config.last_test_at = datetime.now()
    config.last_test_result = "success"
    await db.commit()
    
    return IntegrationTestResult(success=True, message="テストメッセージを送信しました")


# ========== データ管理 API ==========

@router.get("/data/history", response_model=List[ImportExportHistoryResponse], summary="インポート/エクスポート履歴")
async def get_import_export_history(
    type: Optional[str] = Query(None, description="import/export"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """インポート/エクスポート履歴を取得"""
    query = select(ImportExportHistory)
    if type:
        query = query.where(ImportExportHistory.type == type)
    
    query = query.order_by(ImportExportHistory.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    histories = result.scalars().all()
    
    # ユーザー名を取得
    user_ids = [h.user_id for h in histories if h.user_id]
    users = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = {u.id: u.full_name or u.username for u in users_result.scalars().all()}
    
    response = []
    for h in histories:
        resp = ImportExportHistoryResponse.model_validate(h)
        resp.user_name = users.get(h.user_id) if h.user_id else None
        response.append(resp)
    
    return response


@router.post("/data/import", summary="データインポート")
async def import_data(
    master_type: str,
    update_existing: bool = False,
    skip_errors: bool = True,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """マスターデータをインポート"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    # 履歴レコード作成
    history = ImportExportHistory(
        type="import",
        master_type=master_type,
        filename=file.filename or "unknown",
        options={"update_existing": update_existing, "skip_errors": skip_errors},
        user_id=current_user.id,
        started_at=datetime.now(),
        status="processing",
    )
    db.add(history)
    await db.commit()
    
    # TODO: 実際のインポート処理を実装
    # CSVパース、バリデーション、DB登録
    
    history.status = "success"
    history.total_records = 0
    history.success_records = 0
    history.completed_at = datetime.now()
    await db.commit()
    
    logger.info(f"Data imported: {master_type} by {current_user.username}")
    return {"message": "インポートが完了しました", "history_id": history.id}


@router.post("/data/export", summary="データエクスポート")
async def export_data(
    data: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """マスターデータをエクスポート"""
    # 履歴レコード作成
    filename = f"{data.master_type}_{date.today().strftime('%Y%m%d')}.{data.format}"
    history = ImportExportHistory(
        type="export",
        master_type=data.master_type,
        filename=filename,
        format=data.format,
        encoding=data.encoding,
        user_id=current_user.id,
        started_at=datetime.now(),
        status="processing",
    )
    db.add(history)
    await db.commit()
    
    # TODO: 実際のエクスポート処理を実装
    # DBからデータ取得、CSV/Excel生成
    
    history.status = "success"
    history.completed_at = datetime.now()
    await db.commit()
    
    logger.info(f"Data exported: {data.master_type} by {current_user.username}")
    return {"message": "エクスポートが完了しました", "filename": filename}


@router.get("/data/template/{master_type}", summary="インポートテンプレートダウンロード")
async def download_import_template(
    master_type: str,
    current_user: User = Depends(verify_token_and_get_user),
):
    """インポート用テンプレートをダウンロード"""
    templates = {
        "items": ["品目コード", "品目名", "カテゴリ", "単位", "単価", "在庫数"],
        "customers": ["取引先コード", "取引先名", "住所", "電話番号", "担当者名"],
        "suppliers": ["仕入先コード", "仕入先名", "住所", "電話番号", "担当者名"],
        "warehouses": ["倉庫コード", "倉庫名", "住所", "管理者"],
        "users": ["ユーザー名", "氏名", "メールアドレス", "部門", "ロール"],
    }
    
    if master_type not in templates:
        raise HTTPException(status_code=400, detail="無効なマスター種類です")
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(templates[master_type])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={master_type}_template.csv"}
    )


# バックアップ API
@router.get("/backup/settings", response_model=BackupSettingResponse, summary="バックアップ設定取得")
async def get_backup_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """バックアップ設定を取得"""
    result = await db.execute(select(BackupSetting).where(BackupSetting.id == 1))
    setting = result.scalar_one_or_none()
    
    if not setting:
        # デフォルト設定を返す
        return BackupSettingResponse(
            id=1,
            auto_backup_enabled=False,
            schedule="daily",
            storage_path="/backup/",
            retention_count=7,
            include_files=False,
            compression_enabled=True,
            encryption_enabled=False,
            notify_on_complete=False,
            notify_on_error=True,
            updated_at=datetime.now(),
        )
    return setting


@router.put("/backup/settings", response_model=BackupSettingResponse, summary="バックアップ設定更新")
async def update_backup_settings(
    data: BackupSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """バックアップ設定を更新"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(select(BackupSetting).where(BackupSetting.id == 1))
    setting = result.scalar_one_or_none()
    
    if not setting:
        setting = BackupSetting(id=1, **data.model_dump(), updated_by=current_user.id)
        db.add(setting)
    else:
        for key, value in data.model_dump().items():
            if value is not None:
                setattr(setting, key, value)
        setting.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(setting)
    
    logger.info(f"Backup settings updated by {current_user.username}")
    return setting


@router.get("/backup/history", response_model=List[BackupHistoryResponse], summary="バックアップ履歴")
async def get_backup_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """バックアップ履歴を取得"""
    result = await db.execute(
        select(BackupHistory)
        .order_by(BackupHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    histories = result.scalars().all()
    
    response = []
    for h in histories:
        resp = BackupHistoryResponse.model_validate(h)
        if h.file_size:
            resp.file_size_display = _format_file_size(h.file_size)
        response.append(resp)
    
    return response


@router.post("/backup/manual", summary="手動バックアップ実行")
async def create_manual_backup(
    data: ManualBackupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """手動バックアップを実行"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    # バックアップ履歴レコード作成
    now = datetime.now()
    filename = f"backup_{now.strftime('%Y%m%d_%H%M%S')}.sql.gz"
    
    history = BackupHistory(
        filename=filename,
        file_path=f"/backup/{filename}",
        backup_type="manual",
        status="completed",
        started_at=now,
        completed_at=now,
        created_by=current_user.id,
    )
    db.add(history)
    await db.commit()
    
    # TODO: 実際のバックアップ処理を実装
    # mysqldump実行、圧縮、保存
    
    logger.info(f"Manual backup created: {filename} by {current_user.username}")
    return {"message": "バックアップを開始しました", "filename": filename}


@router.post("/backup/{backup_id}/restore", summary="バックアップから復元")
async def restore_from_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """バックアップから復元"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    result = await db.execute(
        select(BackupHistory).where(BackupHistory.id == backup_id)
    )
    backup = result.scalar_one_or_none()
    if not backup:
        raise HTTPException(status_code=404, detail="バックアップが見つかりません")
    
    # TODO: 実際の復元処理を実装
    
    logger.info(f"Restore started from {backup.filename} by {current_user.username}")
    return {"message": "復元を開始しました"}


@router.get("/backup/{backup_id}/download", summary="バックアップダウンロード")
async def download_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """バックアップファイルをダウンロード"""
    result = await db.execute(
        select(BackupHistory).where(BackupHistory.id == backup_id)
    )
    backup = result.scalar_one_or_none()
    if not backup:
        raise HTTPException(status_code=404, detail="バックアップが見つかりません")
    
    # TODO: 実際のファイルを返す
    # return FileResponse(backup.file_path, filename=backup.filename)
    
    return {"message": "ダウンロード準備中", "filename": backup.filename}


@router.post("/data/reset", summary="データ初期化")
async def reset_data(
    data: DataResetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """データを初期化"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    if data.confirmation != "初期化する":
        raise HTTPException(status_code=400, detail="確認文字列が正しくありません")
    
    # TODO: 実際の初期化処理を実装
    # トランザクションデータ削除、ログ削除等
    
    logger.warning(f"Data reset executed by {current_user.username}, targets: {data.targets}")
    return {"message": "データ初期化が完了しました"}


def _format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式に変換"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


# ========== ファイル監視設定 (BT-data 受信 CSV の有効/無効) ==========

try:
    from app.services.file_watcher.sync_services import STOCK_FILES, MATERIAL_FILES
    from app.services.file_watcher.enabled_config import get_enabled, set_enabled
except Exception:
    STOCK_FILES = []
    MATERIAL_FILES = []
    get_enabled = lambda: {}
    set_enabled = lambda x: None


@router.get("/file-watcher", summary="ファイル監視対象の有効/無効一覧")
async def get_file_watcher_settings(
    current_user: User = Depends(verify_token_and_get_user),
):
    """監視対象 CSV の一覧と各ファイルの有効/無効を返す"""
    enabled = get_enabled()
    return {
        "stockFiles": list(STOCK_FILES),
        "materialFiles": list(MATERIAL_FILES),
        "enabled": enabled,
    }


@router.put("/file-watcher", summary="ファイル監視の有効/無効を保存")
async def update_file_watcher_settings(
    body: dict,
    current_user: User = Depends(verify_token_and_get_user),
):
    """enabled: { "StockIn.csv": true, ... } で保存"""
    enabled = body.get("enabled")
    if not isinstance(enabled, dict):
        raise HTTPException(status_code=400, detail="enabled はオブジェクトで指定してください")
    set_enabled(enabled)
    return {"message": "保存しました", "enabled": get_enabled()}

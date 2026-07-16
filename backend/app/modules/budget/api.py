"""予算管理 API"""
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_sales_operation
from app.modules.budget import service as budget_service
from app.modules.budget.models import BudgetImportBatch
from app.modules.budget.schemas import (
    BudgetImportBatchOut,
    BudgetMonthlyOut,
    BudgetProcessWorkingDaysBatchUpdate,
    BudgetWorkingDaysBatchUpdate,
)

router = APIRouter()


@router.get("/months")
async def list_months(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """取込済み年月一覧"""
    _ = current_user
    months = await budget_service.get_available_months(db)
    return {"success": True, "data": months}


@router.get("/working-days")
async def get_working_days(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    月次稼働日数。
    data = { defaults, process_options, process_overrides }
    """
    _ = current_user
    data = await budget_service.list_working_days_bundle(db, year)
    return {"success": True, "data": data}


@router.put("/working-days")
async def put_working_days(
    body: BudgetWorkingDaysBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("edit")),
):
    """共通の月次稼働日数を一括保存（同月は上書き）"""
    try:
        uploaded_by = getattr(current_user, "username", None) or getattr(
            current_user, "full_name", None
        )
        data = await budget_service.upsert_working_days(
            db,
            items=[it.model_dump() for it in body.items],
            updated_by=uploaded_by,
        )
        return {
            "success": True,
            "data": data,
            "message": f"{len(body.items)}件の共通稼働日を保存しました",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/working-days/process")
async def put_process_working_days(
    body: BudgetProcessWorkingDaysBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("edit")),
):
    """工程別稼働日を保存。working_days=null で共通デフォルトに戻す"""
    try:
        uploaded_by = getattr(current_user, "username", None) or getattr(
            current_user, "full_name", None
        )
        data = await budget_service.upsert_process_working_days(
            db,
            items=[it.model_dump() for it in body.items],
            updated_by=uploaded_by,
        )
        return {
            "success": True,
            "data": data,
            "message": f"{len(body.items)}件の工程別稼働日を保存しました",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/summary")
async def budget_summary(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    data = await budget_service.get_summary(db, year, month)
    return {"success": True, "data": data}


@router.get("/list")
async def budget_list(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    keyword: Optional[str] = Query(None),
    match_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    result = await budget_service.list_budget(
        db,
        year=year,
        month=month,
        keyword=keyword,
        match_status=match_status,
        page=page,
        page_size=page_size,
    )
    items = [BudgetMonthlyOut.model_validate(r).model_dump() for r in result["items"]]
    return {
        "success": True,
        "data": {
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "items": items,
        },
    }


@router.get("/imports")
async def list_imports(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    rows = (
        await db.execute(
            select(BudgetImportBatch).order_by(BudgetImportBatch.id.desc()).limit(limit)
        )
    ).scalars().all()
    return {
        "success": True,
        "data": [BudgetImportBatchOut.model_validate(r).model_dump() for r in rows],
    }


@router.post("/upload")
async def upload_budget_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("create")),
):
    """
    見直し予算CSVを取込。
    品番 → 製品マスタ（product_cd 末尾が1）を紐付。
    同月・同品番は上書き更新。
    """
    filename = file.filename or "budget.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSVファイルを指定してください")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空のファイルです")
    try:
        uploaded_by = getattr(current_user, "username", None) or getattr(
            current_user, "full_name", None
        )
        result = await budget_service.import_budget_csv(
            db, raw=raw, file_name=filename, uploaded_by=uploaded_by
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("予算CSV取込失敗")
        raise HTTPException(status_code=500, detail=f"取込に失敗しました: {e}") from e


@router.get("/analysis/trend")
async def analysis_trend(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    data = await budget_service.analyze_monthly_trend(db, year)
    return {"success": True, "data": data}


@router.get("/analysis/process-trend")
async def analysis_process_trend(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """工程別の予算数量月次推移"""
    _ = current_user
    data = await budget_service.analyze_process_monthly_trend(db, year)
    return {"success": True, "data": data}


@router.get("/analysis/process")
async def analysis_process(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    data = await budget_service.analyze_process_load(db, year, month)
    return {"success": True, "data": data}


@router.get("/analysis/equipment")
async def analysis_equipment(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    data = await budget_service.analyze_equipment_load(db, year, month)
    return {"success": True, "data": data}


@router.get("/analysis/cost")
async def analysis_cost(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    _ = current_user
    data = await budget_service.analyze_cost(db, year, month)
    return {"success": True, "data": data}


@router.delete("/month")
async def delete_budget_month(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("delete")),
):
    _ = current_user
    deleted = await budget_service.delete_month_data(db, year, month)
    return {"success": True, "deleted": deleted, "message": f"{year}/{month:02d} を {deleted} 件削除しました"}

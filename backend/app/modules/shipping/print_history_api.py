"""
印刷履歴 API（出荷報告・カレンダー印刷履歴）
- GET /print/history: 一覧
- GET /print/history/stats: 統計
- POST /print/history: 記録登録
- DELETE /print/history/{id}: 1件削除
- DELETE /print/history/batch/{ids}: 一括削除
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db

router = APIRouter()


class RecordPrintHistoryBody(BaseModel):
    report_type: str
    report_title: Optional[str] = None
    filters: Optional[dict] = None
    record_count: int = 0
    status: Optional[str] = None
    error_message: Optional[str] = None


@router.get("/history")
async def list_print_history(
    report_type: Optional[str] = Query(None),
    user_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """印刷履歴一覧"""
    try:
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if report_type:
            conditions.append("report_type = :report_type")
            params["report_type"] = report_type
        if user_name:
            conditions.append("user_name LIKE :user_name")
            params["user_name"] = f"%{user_name}%"
        if date_from:
            conditions.append("DATE(printed_at) >= :date_from")
            params["date_from"] = date_from
        if date_to:
            conditions.append("DATE(printed_at) <= :date_to")
            params["date_to"] = date_to
        
        # Build WHERE clause - if no conditions, use "1=1" to make query valid
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Construct query with proper WHERE clause
        query_str = f"""
            SELECT id, report_type, report_title, filters, record_count, status, error_message, user_name, printed_at
            FROM print_history 
            WHERE {where_clause}
            ORDER BY printed_at DESC 
            LIMIT :limit OFFSET :offset
        """
        
        q = text(query_str)
        result = await db.execute(q, params)
        rows = result.mappings().all()
        
        def _fmt(d):
            if d is None:
                return ""
            return d.isoformat() if hasattr(d, "isoformat") else str(d)

        return {
            "success": True,
            "list": [
                {
                    "id": r["id"],
                    "report_type": r["report_type"],
                    "report_title": r["report_title"] or "",
                    "filters": r["filters"],
                    "record_count": r["record_count"],
                    "status": r["status"],
                    "error_message": r["error_message"],
                    "user_name": r["user_name"],
                    "print_date": _fmt(r.get("printed_at")),
                    "printed_at": _fmt(r.get("printed_at")),
                }
                for r in rows
            ],
            "total": len(rows)
        }
    except Exception as e:
        import traceback
        print(f"❌ Error in list_print_history: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"印刷履歴の取得に失敗しました: {str(e)}")


@router.get("/history/stats")
async def get_print_history_stats(
    report_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """印刷履歴統計"""
    try:
        conditions = []
        params = {}
        
        if report_type:
            conditions.append("report_type = :report_type")
            params["report_type"] = report_type
        if date_from:
            conditions.append("DATE(printed_at) >= :date_from")
            params["date_from"] = date_from
        if date_to:
            conditions.append("DATE(printed_at) <= :date_to")
            params["date_to"] = date_to
        
        # Build WHERE clause
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query_str = f"""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status = '成功' THEN 1 ELSE 0 END) AS success_count,
                   SUM(CASE WHEN status IN ('失败', '失敗') THEN 1 ELSE 0 END) AS fail_count,
                   SUM(CASE WHEN status = '取消' THEN 1 ELSE 0 END) AS cancel_count
            FROM print_history 
            WHERE {where_clause}
        """
        
        q = text(query_str)
        result = await db.execute(q, params)
        row = result.mappings().first()
        
        return {
            "success": True,
            "total": row["total"] or 0,
            "success_count": row["success_count"] or 0,
            "fail_count": row["fail_count"] or 0,
            "cancel_count": row["cancel_count"] or 0,
        }
    except Exception as e:
        import traceback
        print(f"❌ Error in get_print_history_stats: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"印刷履歴統計の取得に失敗しました: {str(e)}")


@router.post("/history")
async def record_print_history(
    body: RecordPrintHistoryBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """印刷履歴を1件登録（テーブル: printed_at, report_title 等）"""
    import json
    filters_json = json.dumps(body.filters, ensure_ascii=False) if body.filters else None
    report_title = body.report_title or ""
    user_name = getattr(current_user, "username", None) or getattr(current_user, "name", None)
    q = text("""
        INSERT INTO print_history (report_type, report_title, user_name, filters, record_count, status, error_message)
        VALUES (:report_type, :report_title, :user_name, :filters, :record_count, :status, :error_message)
    """)
    await db.execute(q, {
        "report_type": body.report_type,
        "report_title": report_title,
        "user_name": user_name,
        "filters": filters_json,
        "record_count": body.record_count,
        "status": body.status or "成功",
        "error_message": body.error_message,
    })
    await db.commit()
    return {"success": True}


@router.delete("/history/{item_id}")
async def delete_print_history(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """印刷履歴1件削除"""
    r = await db.execute(text("DELETE FROM print_history WHERE id = :id"), {"id": item_id})
    await db.commit()
    if r.rowcount == 0:
        raise HTTPException(status_code=404, detail="レコードが見つかりません")
    return {"success": True}


@router.delete("/history/batch/{ids}")
async def delete_print_history_batch(
    ids: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """印刷履歴一括削除（カンマ区切りID）"""
    id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    if not id_list:
        raise HTTPException(status_code=400, detail="id を指定してください")
    placeholders = ", ".join([str(i) for i in id_list])
    await db.execute(text(f"DELETE FROM print_history WHERE id IN ({placeholders})"))
    await db.commit()
    return {"success": True}

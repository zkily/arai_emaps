"""生産注意事項 API（品質管理 > 製品関連）

GET    /api/quality/process-cautions
POST   /api/quality/process-cautions
PUT    /api/quality/process-cautions/{id}
PATCH  /api/quality/process-cautions/{id}/active  有効/無効切替
DELETE /api/quality/process-cautions/{id}
GET    /api/quality/process-cautions/lookup  工程・製品で有効な注意事項を取得（指示画面用）
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_quality_operation

router = APIRouter()

PROCESS_CODES = {
    "cutting",
    "chamfering",
    "forming",
    "welding",
    "plating",
    "inspection",
}
PROCESS_ORDER = "FIELD(process_code, 'cutting','chamfering','forming','welding','plating','inspection')"


class CautionBody(BaseModel):
    process_code: str
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    caution_text: str
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=99999)


class ActiveBody(BaseModel):
    is_active: bool


def _reraise_table_missing(e: Exception) -> None:
    msg = str(e).lower()
    if "quality_product_process_cautions" in msg and (
        "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
    ):
        raise HTTPException(
            status_code=503,
            detail="生産注意事項テーブルが存在しません。"
            "マイグレーション 154_quality_product_process_cautions.sql を実行してください。",
        ) from e


def _dt_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _clean(value: Optional[str], limit: int) -> Optional[str]:
    text_value = (value or "").strip()
    if not text_value:
        return None
    if len(text_value) > limit:
        raise HTTPException(status_code=400, detail=f"{limit}文字以内で入力してください")
    return text_value


def _require_process(code: str) -> str:
    key = (code or "").strip()
    if key not in PROCESS_CODES:
        raise HTTPException(status_code=400, detail="工程を選択してください")
    return key


def _row(r: Any) -> dict:
    return {
        "id": int(r["id"]),
        "process_code": r["process_code"],
        "product_cd": r["product_cd"],
        "product_name": r["product_name"],
        "caution_text": r["caution_text"],
        "is_active": bool(r["is_active"]),
        "sort_order": int(r["sort_order"] or 0),
        "created_by": r["created_by"],
        "updated_by": r["updated_by"],
        "created_at": _dt_str(r["created_at"]),
        "updated_at": _dt_str(r["updated_at"]),
    }


SELECT_SQL = """
SELECT id, process_code, product_cd, product_name, caution_text,
       is_active, sort_order, created_by, updated_by, created_at, updated_at
FROM quality_product_process_cautions
"""


async def _assert_no_duplicate(
    db: AsyncSession,
    *,
    process_code: str,
    product_cd: Optional[str],
    caution_text: str,
    exclude_id: Optional[int] = None,
) -> None:
    params: dict[str, Any] = {
        "process_code": process_code,
        "caution_text": caution_text,
    }
    if product_cd:
        params["product_cd"] = product_cd
        product_clause = "product_cd = :product_cd"
    else:
        product_clause = "product_cd IS NULL"
    exclude_clause = ""
    if exclude_id is not None:
        params["exclude_id"] = exclude_id
        exclude_clause = " AND id <> :exclude_id"
    result = await db.execute(
        text(
            f"""
            SELECT id FROM quality_product_process_cautions
            WHERE process_code = :process_code
              AND {product_clause}
              AND caution_text = :caution_text
              {exclude_clause}
            LIMIT 1
            """
        ),
        params,
    )
    if result.first():
        raise HTTPException(
            status_code=400,
            detail="同じ工程・製品・注意内容が既に登録されています",
        )


@router.get("/process-cautions")
async def list_cautions(
    process_code: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    scope: Optional[str] = Query(None, description="all|product|common"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産注意事項一覧。"""
    _ = current_user
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if process_code:
        clauses.append("process_code = :process_code")
        params["process_code"] = _require_process(process_code)
    if not include_inactive:
        clauses.append("is_active = 1")
    scope_key = (scope or "").strip().lower()
    if scope_key == "product":
        clauses.append("product_cd IS NOT NULL")
    elif scope_key == "common":
        clauses.append("product_cd IS NULL")
    kw = (keyword or "").strip()
    if kw:
        clauses.append(
            "(product_cd LIKE :kw OR product_name LIKE :kw OR caution_text LIKE :kw)"
        )
        params["kw"] = f"%{kw}%"
    sql = (
        SELECT_SQL
        + " WHERE "
        + " AND ".join(clauses)
        + f" ORDER BY {PROCESS_ORDER}, sort_order, product_name, id"
    )
    try:
        rows = (await db.execute(text(sql), params)).mappings().fetchall()
    except Exception as e:
        _reraise_table_missing(e)
        logger.exception("生産注意事項一覧の取得に失敗")
        raise HTTPException(status_code=500, detail="一覧の取得に失敗しました") from e
    items = [_row(r) for r in rows]
    active_count = sum(1 for i in items if i["is_active"])
    return {
        "success": True,
        "data": {
            "list": items,
            "total": len(items),
            "active_count": active_count,
            "inactive_count": len(items) - active_count,
        },
        "message": "OK",
    }


@router.get("/process-cautions/lookup")
async def lookup_cautions(
    process_code: str = Query(..., description="工程コード"),
    product_cd: Optional[str] = Query(None, description="製品CD（任意）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指示画面向け：指定工程の有効注意事項（工程共通 + 当該製品）。"""
    _ = current_user
    code = _require_process(process_code)
    cd = _clean(product_cd, 50)
    params: dict[str, Any] = {"process_code": code}
    if cd:
        params["product_cd"] = cd
        where = """
          process_code = :process_code
          AND is_active = 1
          AND (product_cd IS NULL OR product_cd = :product_cd)
        """
    else:
        where = """
          process_code = :process_code
          AND is_active = 1
          AND product_cd IS NULL
        """
    sql = (
        SELECT_SQL
        + f" WHERE {where}"
        + " ORDER BY (product_cd IS NULL), sort_order, id"
    )
    try:
        rows = (await db.execute(text(sql), params)).mappings().fetchall()
    except Exception as e:
        _reraise_table_missing(e)
        logger.exception("生産注意事項 lookup 失敗")
        raise HTTPException(status_code=500, detail="注意事項の取得に失敗しました") from e
    items = [_row(r) for r in rows]
    return {"success": True, "data": {"list": items, "total": len(items)}, "message": "OK"}


@router.post("/process-cautions")
async def create_caution(
    body: CautionBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("create")),
):
    process_code = _require_process(body.process_code)
    caution_text = _clean(body.caution_text, 500)
    if not caution_text:
        raise HTTPException(status_code=400, detail="注意事項を入力してください")
    product_cd = _clean(body.product_cd, 50)
    product_name = _clean(body.product_name, 200)
    actor = getattr(current_user, "username", None)
    try:
        await _assert_no_duplicate(
            db,
            process_code=process_code,
            product_cd=product_cd,
            caution_text=caution_text,
        )
        result = await db.execute(
            text(
                """
                INSERT INTO quality_product_process_cautions
                  (process_code, product_cd, product_name, caution_text,
                   is_active, sort_order, created_by, updated_by)
                VALUES
                  (:process_code, :product_cd, :product_name, :caution_text,
                   :is_active, :sort_order, :actor, :actor)
                """
            ),
            {
                "process_code": process_code,
                "product_cd": product_cd,
                "product_name": product_name,
                "caution_text": caution_text,
                "is_active": 1 if body.is_active else 0,
                "sort_order": int(body.sort_order or 0),
                "actor": actor,
            },
        )
        await db.commit()
        new_id = int(result.lastrowid or 0)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("生産注意事項の追加に失敗")
        raise HTTPException(status_code=500, detail="追加に失敗しました") from e
    return {"success": True, "data": {"id": new_id}, "message": "追加しました"}


@router.put("/process-cautions/{caution_id}")
async def update_caution(
    caution_id: int,
    body: CautionBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    process_code = _require_process(body.process_code)
    caution_text = _clean(body.caution_text, 500)
    if not caution_text:
        raise HTTPException(status_code=400, detail="注意事項を入力してください")
    product_cd = _clean(body.product_cd, 50)
    product_name = _clean(body.product_name, 200)
    actor = getattr(current_user, "username", None)
    try:
        await _assert_no_duplicate(
            db,
            process_code=process_code,
            product_cd=product_cd,
            caution_text=caution_text,
            exclude_id=caution_id,
        )
        result = await db.execute(
            text(
                """
                UPDATE quality_product_process_cautions
                SET process_code = :process_code,
                    product_cd = :product_cd,
                    product_name = :product_name,
                    caution_text = :caution_text,
                    is_active = :is_active,
                    sort_order = :sort_order,
                    updated_by = :actor
                WHERE id = :id
                """
            ),
            {
                "id": caution_id,
                "process_code": process_code,
                "product_cd": product_cd,
                "product_name": product_name,
                "caution_text": caution_text,
                "is_active": 1 if body.is_active else 0,
                "sort_order": int(body.sort_order or 0),
                "actor": actor,
            },
        )
        if int(result.rowcount or 0) == 0:
            raise HTTPException(status_code=404, detail="対象が見つかりません")
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("生産注意事項の更新に失敗")
        raise HTTPException(status_code=500, detail="更新に失敗しました") from e
    return {"success": True, "message": "更新しました"}


@router.patch("/process-cautions/{caution_id}/active")
async def set_caution_active(
    caution_id: int,
    body: ActiveBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    actor = getattr(current_user, "username", None)
    try:
        result = await db.execute(
            text(
                """
                UPDATE quality_product_process_cautions
                SET is_active = :is_active, updated_by = :actor
                WHERE id = :id
                """
            ),
            {
                "id": caution_id,
                "is_active": 1 if body.is_active else 0,
                "actor": actor,
            },
        )
        if int(result.rowcount or 0) == 0:
            raise HTTPException(status_code=404, detail="対象が見つかりません")
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("生産注意事項の有効切替に失敗")
        raise HTTPException(status_code=500, detail="更新に失敗しました") from e
    return {
        "success": True,
        "message": "有効にしました" if body.is_active else "無効にしました",
    }


@router.delete("/process-cautions/{caution_id}")
async def delete_caution(
    caution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("delete")),
):
    _ = current_user
    try:
        result = await db.execute(
            text("DELETE FROM quality_product_process_cautions WHERE id = :id"),
            {"id": caution_id},
        )
        if int(result.rowcount or 0) == 0:
            raise HTTPException(status_code=404, detail="対象が見つかりません")
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        _reraise_table_missing(e)
        logger.exception("生産注意事項の削除に失敗")
        raise HTTPException(status_code=500, detail="削除に失敗しました") from e
    return {"success": True, "message": "削除しました"}

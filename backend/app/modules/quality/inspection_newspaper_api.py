"""検査新聞紙通知 API（品質管理）

GET    /api/quality/inspection-newspaper/products        対象製品一覧
POST   /api/quality/inspection-newspaper/products        対象製品追加
DELETE /api/quality/inspection-newspaper/products/{id}   対象製品削除
GET    /api/quality/inspection-newspaper/setting         通知設定取得
PUT    /api/quality/inspection-newspaper/setting         通知設定更新（自動送信 ON/OFF）
GET    /api/quality/inspection-newspaper/preview         送信プレビュー（生産日指定）
POST   /api/quality/inspection-newspaper/send            手動送信（再送信）
GET    /api/quality/inspection-newspaper/history         送信履歴
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_quality_operation
from app.modules.system.settings_models import EmailSendLog, NotificationSetting
from app.services.inspection_newspaper_notification import (
    INSPECTION_NEWSPAPER_EVENT,
    get_inspection_newspaper_preview,
    send_inspection_newspaper_notification,
)

router = APIRouter()

PRODUCT_CD_MAX_LEN = 50
PRODUCT_NAME_MAX_LEN = 200


class NewspaperProductCreateBody(BaseModel):
    product_cd: str
    product_name: Optional[str] = None


class NewspaperSettingUpdateBody(BaseModel):
    is_active: Optional[bool] = None
    email_enabled: Optional[bool] = None


def _reraise_table_missing(e: Exception) -> None:
    msg = str(e).lower()
    if "quality_inspection_newspaper_products" in msg and (
        "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
    ):
        raise HTTPException(
            status_code=503,
            detail="quality_inspection_newspaper_products テーブルが存在しません。"
            "マイグレーション 134_quality_inspection_newspaper_notify.sql を実行してください。",
        ) from e


def _dt_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


# ============================
# 対象製品 CRUD
# ============================


@router.get("/inspection-newspaper/products")
async def list_newspaper_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検査新聞紙通知の対象製品一覧。"""
    try:
        rows = (
            await db.execute(
                text(
                    """
                    SELECT id, product_cd, product_name, updated_by, created_at, updated_at
                    FROM quality_inspection_newspaper_products
                    ORDER BY
                      (product_name IS NULL OR TRIM(product_name) = '') ASC,
                      product_name ASC,
                      product_cd ASC
                    """
                )
            )
        ).mappings().fetchall()
    except Exception as e:
        _reraise_table_missing(e)
        logger.exception("quality_inspection_newspaper_products 読取失敗")
        raise HTTPException(status_code=500, detail="対象製品の取得に失敗しました") from e

    items = [
        {
            "id": int(r["id"]),
            "product_cd": r["product_cd"],
            "product_name": r["product_name"],
            "updated_by": r["updated_by"],
            "created_at": _dt_str(r["created_at"]),
            "updated_at": _dt_str(r["updated_at"]),
        }
        for r in rows
    ]
    return {"success": True, "data": {"list": items}, "message": "OK"}


@router.post("/inspection-newspaper/products")
async def create_newspaper_product(
    body: NewspaperProductCreateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("create")),
):
    """検査新聞紙通知の対象製品を追加。"""
    product_cd = (body.product_cd or "").strip()
    if not product_cd:
        raise HTTPException(status_code=400, detail="製品CDを指定してください")
    if len(product_cd) > PRODUCT_CD_MAX_LEN:
        raise HTTPException(
            status_code=400, detail=f"製品CDは{PRODUCT_CD_MAX_LEN}文字以内で指定してください"
        )
    product_name = (body.product_name or "").strip() or None
    if product_name and len(product_name) > PRODUCT_NAME_MAX_LEN:
        raise HTTPException(
            status_code=400, detail=f"製品名は{PRODUCT_NAME_MAX_LEN}文字以内で指定してください"
        )
    updater = getattr(current_user, "username", None)
    try:
        await db.execute(
            text(
                """
                INSERT INTO quality_inspection_newspaper_products (product_cd, product_name, updated_by)
                VALUES (:product_cd, :product_name, :updated_by)
                """
            ),
            {"product_cd": product_cd, "product_name": product_name, "updated_by": updater},
        )
        item_id = (await db.execute(text("SELECT LAST_INSERT_ID() AS id"))).scalar()
        await db.commit()
    except IntegrityError:
        try:
            await db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=409, detail="この製品CDは既に登録されています") from None
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        _reraise_table_missing(e)
        logger.exception("quality_inspection_newspaper_products 追加失敗")
        raise HTTPException(status_code=500, detail="対象製品の追加に失敗しました") from e

    return {
        "success": True,
        "data": {"id": int(item_id or 0), "product_cd": product_cd, "product_name": product_name},
        "message": "OK",
    }


@router.delete("/inspection-newspaper/products/{item_id}")
async def delete_newspaper_product(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("delete")),
):
    """検査新聞紙通知の対象製品を削除。"""
    try:
        result = await db.execute(
            text("DELETE FROM quality_inspection_newspaper_products WHERE id = :id"),
            {"id": item_id},
        )
        await db.commit()
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        _reraise_table_missing(e)
        logger.exception("quality_inspection_newspaper_products 削除失敗")
        raise HTTPException(status_code=500, detail="対象製品の削除に失敗しました") from e

    if (result.rowcount or 0) < 1:
        raise HTTPException(status_code=404, detail="対象製品が見つかりません")
    return {"success": True, "data": {"id": item_id}, "message": "OK"}


# ============================
# 通知設定（自動送信 ON/OFF）
# ============================


async def _get_setting(db: AsyncSession) -> NotificationSetting | None:
    res = await db.execute(
        select(NotificationSetting).where(
            NotificationSetting.event_code == INSPECTION_NEWSPAPER_EVENT
        )
    )
    return res.scalar_one_or_none()


@router.get("/inspection-newspaper/setting")
async def get_newspaper_setting(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検査新聞紙通知の通知設定を取得。"""
    setting = await _get_setting(db)
    if setting is None:
        raise HTTPException(
            status_code=503,
            detail="通知イベント INSPECTION_NEWSPAPER_ALERT が未登録です。"
            "マイグレーション 134_quality_inspection_newspaper_notify.sql を実行してください。",
        )
    return {
        "success": True,
        "data": {
            "event_code": setting.event_code,
            "event_name": setting.event_name,
            "is_active": bool(setting.is_active),
            "email_enabled": bool(setting.email_enabled),
        },
        "message": "OK",
    }


@router.put("/inspection-newspaper/setting")
async def update_newspaper_setting(
    body: NewspaperSettingUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    """検査新聞紙通知の自動送信 ON/OFF を更新。"""
    setting = await _get_setting(db)
    if setting is None:
        raise HTTPException(status_code=503, detail="通知イベントが未登録です")
    if body.is_active is not None:
        setting.is_active = body.is_active
    if body.email_enabled is not None:
        setting.email_enabled = body.email_enabled
    await db.commit()
    return {
        "success": True,
        "data": {
            "is_active": bool(setting.is_active),
            "email_enabled": bool(setting.email_enabled),
        },
        "message": "OK",
    }


# ============================
# プレビュー・手動送信・履歴
# ============================


@router.get("/inspection-newspaper/preview")
async def preview_newspaper_notification(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定生産日の送信プレビュー（管理コード前13桁の計画数・初回検知）。"""
    try:
        return await get_inspection_newspaper_preview(db, production_day=production_day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        _reraise_table_missing(e)
        logger.exception("検査新聞紙通知プレビュー失敗")
        raise HTTPException(status_code=500, detail="プレビューの取得に失敗しました") from e


@router.post("/inspection-newspaper/send")
async def send_newspaper_notification(
    production_day: str = Query(..., description="生産日 YYYY-MM-DD"),
    force: bool = Query(False, description="送信済みでも再送信する"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_quality_operation("edit")),
):
    """検査新聞紙通知を手動送信（送信済みバッチは force=true で再送信）。"""
    try:
        result = await send_inspection_newspaper_notification(
            db,
            production_day=production_day,
            confirmed_by=(current_user.full_name or current_user.username or ""),
            sent_by_user_id=current_user.id,
            force=force,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        _reraise_table_missing(e)
        logger.exception("検査新聞紙通知の手動送信失敗")
        raise HTTPException(status_code=500, detail="送信に失敗しました") from e

    if result.get("skipped"):
        return {
            "success": bool(result.get("success")),
            "data": result,
            "message": result.get("reason") or "送信をスキップしました",
        }
    return {"success": bool(result.get("success")), "data": result, "message": result.get("message")}


@router.get("/inspection-newspaper/history")
async def list_newspaper_send_history(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """検査新聞紙通知の送信履歴（新しい順）。"""
    res = await db.execute(
        select(EmailSendLog)
        .where(EmailSendLog.event_code == INSPECTION_NEWSPAPER_EVENT)
        .order_by(EmailSendLog.sent_at.desc(), EmailSendLog.id.desc())
        .limit(limit)
    )
    logs = res.scalars().all()
    items = [
        {
            "id": log.id,
            "reference_key": log.reference_key,
            "recipient_email": log.recipient_email,
            "subject": log.subject,
            "status": log.status,
            "error_message": log.error_message,
            "sent_at": _dt_str(log.sent_at),
        }
        for log in logs
    ]
    return {"success": True, "data": {"list": items}, "message": "OK"}

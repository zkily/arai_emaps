"""
印刷記録 API (shipping_records テーブル)
- POST /print-record: 出荷番号の印刷記録を保存
"""
import asyncio
import logging
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional

from app.modules.auth.operation_deps import require_sales_operation
from app.modules.auth.models import User
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

_INSERT_RECORD = text(
    "INSERT INTO shipping_records (shipping_no, status) VALUES (:shipping_no, '印刷済') "
    "ON DUPLICATE KEY UPDATE status = '印刷済'"
)
_UPDATE_ITEM_STATUS = text(
    "UPDATE shipping_items SET status = '発行済' "
    "WHERE shipping_no = :shipping_no "
    "AND COALESCE(status, '') NOT IN ('発行済', 'キャンセル')"
)
_LOCK_WAIT_TIMEOUT_SEC = 3
_TX_RETRIES = 5
# MySQL: 1205 = Lock wait timeout, 1213 = Deadlock
_RETRYABLE_LOCK_ERRNOS = {1205, 1213}


class PrintRecordBody(BaseModel):
    shipping_numbers: List[str]


def _mysql_errno(exc: OperationalError) -> Optional[int]:
    orig = getattr(exc, "orig", None)
    args = getattr(orig, "args", ())
    if args and isinstance(args[0], int):
        return args[0]
    return None


def _is_retryable_lock_error(exc: OperationalError) -> bool:
    return _mysql_errno(exc) in _RETRYABLE_LOCK_ERRNOS


async def _set_lock_wait_timeout(db: AsyncSession) -> None:
    # OperationalError 後に接続が張り直されると SESSION 設定が消えるため、試行ごとに再設定する
    await db.execute(
        text(f"SET SESSION innodb_lock_wait_timeout = {_LOCK_WAIT_TIMEOUT_SEC}")
    )


async def _sleep_lock_backoff(attempt: int) -> None:
    await asyncio.sleep(0.15 * (2**attempt) + random.uniform(0, 0.25))


@router.post("")
async def save_print_record(
    body: PrintRecordBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sales_operation("export")),
):
    """出荷番号の印刷記録を shipping_records に保存し、該当 shipping_items の status を「発行済」に更新"""
    if not body.shipping_numbers:
        return {"success": True, "count": 0}
    numbers = [str(n).strip() for n in body.shipping_numbers if n and str(n).strip()]
    # 同一番号の重複を除き、ロック取得順を安定させる
    numbers = sorted(dict.fromkeys(numbers))
    if not numbers:
        return {"success": True, "count": 0}

    try:
        # 1) shipping_records に印刷済を保存（先にコミットし、shipping_items のロック待ちと分離）
        for attempt in range(_TX_RETRIES):
            try:
                await _set_lock_wait_timeout(db)
                for no in numbers:
                    await db.execute(_INSERT_RECORD, {"shipping_no": no})
                await db.commit()
                break
            except OperationalError as exc:
                await db.rollback()
                if _is_retryable_lock_error(exc) and attempt < _TX_RETRIES - 1:
                    logger.warning(
                        "print-record shipping_records ロック競合 (errno=%s) 再試行 %s/%s",
                        _mysql_errno(exc),
                        attempt + 1,
                        _TX_RETRIES,
                    )
                    await _sleep_lock_backoff(attempt)
                    continue
                raise

        # 2) 出荷番号ごとに短トランザクションで status 更新（全番号一括 UPDATE で広い行ロックを取らない）
        failed_nos: List[str] = []
        for no in numbers:
            updated = False
            for attempt in range(_TX_RETRIES):
                try:
                    await _set_lock_wait_timeout(db)
                    await db.execute(_UPDATE_ITEM_STATUS, {"shipping_no": no})
                    await db.commit()
                    updated = True
                    break
                except OperationalError as exc:
                    await db.rollback()
                    if _is_retryable_lock_error(exc) and attempt < _TX_RETRIES - 1:
                        logger.warning(
                            "print-record shipping_items ロック競合 (errno=%s) shipping_no=%s 再試行 %s/%s",
                            _mysql_errno(exc),
                            no,
                            attempt + 1,
                            _TX_RETRIES,
                        )
                        await _sleep_lock_backoff(attempt)
                        continue
                    if _is_retryable_lock_error(exc):
                        failed_nos.append(no)
                        break
                    raise
            if not updated and no not in failed_nos:
                failed_nos.append(no)

        if failed_nos:
            return {
                "success": True,
                "count": len(numbers),
                "status_updated": False,
                "failed_shipping_numbers": failed_nos,
                "warning": (
                    "印刷記録は保存しましたが、出荷状態の更新が他処理のロック競合で"
                    f"一部未完了です（{len(failed_nos)}件）。"
                    "一覧を更新するか、しばらくしてから再度お試しください。"
                ),
            }
        return {"success": True, "count": len(numbers), "status_updated": True}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"印刷記録の保存に失敗しました: {type(e).__name__}: {e}",
        ) from e

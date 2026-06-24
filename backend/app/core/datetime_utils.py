"""
日本時刻ユーティリティ
プロジェクト全体で日本標準時（JST, Asia/Tokyo）を統一して使用する。
"""
from datetime import datetime, timedelta, timezone

import pytz

from app.core.config import settings

_JST_CACHE = None


def _resolve_jst():
    """Asia/Tokyo（Windows で tzdata が無い場合は固定 UTC+9）。"""
    global _JST_CACHE
    if _JST_CACHE is not None:
        return _JST_CACHE
    try:
        _JST_CACHE = pytz.timezone(settings.TIMEZONE or "Asia/Tokyo")
    except Exception:
        _JST_CACHE = timezone(timedelta(hours=9))
    return _JST_CACHE


# 日本標準時（Asia/Tokyo）
JST = _resolve_jst()


def now_jst() -> datetime:
    """現在時刻を日本標準時で返す。DB保存・API返却はすべてJSTで統一。"""
    return datetime.now(JST)


def now_jst_naive() -> datetime:
    """スケジューラ用の JST 壁時計（tzinfo なし）。"""
    return now_jst().replace(tzinfo=None)

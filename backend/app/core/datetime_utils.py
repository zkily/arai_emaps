"""
日本時刻ユーティリティ
プロジェクト全体で日本標準時（JST, Asia/Tokyo）を統一して使用する。
"""
from datetime import datetime
import pytz

from app.core.config import settings

# 日本標準時（Asia/Tokyo）
JST = pytz.timezone(settings.TIMEZONE)


def now_jst() -> datetime:
    """現在時刻を日本標準時で返す。DB保存・API返却はすべてJSTで統一。"""
    return datetime.now(JST)

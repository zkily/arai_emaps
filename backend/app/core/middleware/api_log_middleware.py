"""
API連携ログ記録ミドルウェア
/api/* へのリクエストを api_logs テーブルに記録する
"""
import logging
import time
from typing import TYPE_CHECKING
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip[:45]
    if request.client:
        return (request.client.host or "")[:45]
    return ""


def _client_ua(request: Request) -> str:
    return (request.headers.get("user-agent") or "")[:100]


async def _get_user_id_from_request(request: Request, db: "AsyncSession") -> int | None:
    """Authorization ヘッダから user_id を取得（既存セッション使用）"""
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    try:
        from sqlalchemy import select
        from app.modules.auth.models import User
        r = await db.execute(select(User.id).where(User.username == username))
        return r.scalar_one_or_none()
    except Exception as e:
        logger.debug("API log user_id resolve: %s", e)
        return None


class ApiLogMiddleware(BaseHTTPMiddleware):
    """API リクエストを api_logs に記録するミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        # /api/ 以外は記録しない
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        # 記録は非同期で行い、失敗してもレスポンスは返す
        try:
            from app.modules.system.settings_models import ApiLog
            async with AsyncSessionLocal() as db:
                user_id = await _get_user_id_from_request(request, db)
                log = ApiLog(
                    method=request.method[:10],
                    endpoint=path[:500],
                    status_code=response.status_code,
                    duration=duration_ms,
                    client=_client_ua(request) or None,
                    user_id=user_id,
                    ip_address=_client_ip(request) or None,
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            logger.warning("API連携ログの記録に失敗しました: %s", e)
            try:
                async with AsyncSessionLocal() as db:
                    await db.rollback()
            except Exception:
                pass

        return response

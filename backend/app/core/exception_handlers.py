"""FastAPI のグローバル例外ハンドラ群。

統一されたエラーレスポンス形式：
{
  "success": false,
  "error": {
    "code": "<HTTP code or symbolic>",
    "message": "<user-facing message>",
    "details": <optional, dict|list|str|null>
  }
}
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 想定内のクライアントエラー（権限なし・未認証・未找到など）は DEBUG に落とし、
# ログイン/ログアウトの INFO が埋もれないようにする。
_EXPECTED_CLIENT_STATUSES = frozenset({401, 403, 404})


def _payload(code: Any, message: str, details: Any | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"success": False, "error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """FastAPI アプリに例外ハンドラを登録する。"""

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = str(exc.detail) if exc.detail else ""
        if exc.status_code >= 500:
            logger.error(
                "HTTPException {} {} -> {} | {}",
                request.method,
                request.url.path,
                exc.status_code,
                detail or "-",
            )
        elif exc.status_code in _EXPECTED_CLIENT_STATUSES:
            # 権限拒否・トークン失効などは通常運用で頻発するため DEBUG
            logger.debug(
                "HTTPException {} {} -> {} | {}",
                request.method,
                request.url.path,
                exc.status_code,
                detail or "-",
            )
        else:
            logger.warning(
                "HTTPException {} {} -> {} | {}",
                request.method,
                request.url.path,
                exc.status_code,
                detail or "-",
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.status_code, detail if detail else "HTTP error"),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(
            "ValidationError {} {}: {}",
            request.method,
            request.url.path,
            exc.errors(),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_payload(
                "validation_error",
                "リクエスト形式が正しくありません。",
                details=exc.errors(),
            ),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_exc(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.error(
            "IntegrityError {} {}: {}",
            request.method,
            request.url.path,
            exc.orig,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_payload(
                "integrity_error",
                "データ整合性に違反しました（重複・参照制約など）。",
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def _sqla_exc(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("SQLAlchemyError {} {}", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_payload(
                "database_error",
                "データベース処理でエラーが発生しました。",
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # 想定外例外はスタックトレース付きで記録
        logger.exception("Unhandled {} {}: {}", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_payload("internal_error", "サーバ内部エラーが発生しました。"),
        )


__all__ = ["register_exception_handlers"]

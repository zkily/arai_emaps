"""Loguru ベースの統一ロガー設定。

- JST タイムゾーン
- コンソール（人間可読）+ ファイル（JSON 構造化）の二系統出力
- 標準 logging を Loguru に転送するブリッジ付き
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from loguru import logger


class _InterceptHandler(logging.Handler):
    """標準 logging のレコードを Loguru に転送する。"""

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(
    level: str = "INFO",
    log_file: str | None = "logs/app.log",
    *,
    json_file: bool = True,
    rotation: str = "20 MB",
    retention: str = "30 days",
) -> None:
    """Loguru を初期化し、標準 logging も統合する。

    Parameters
    ----------
    level: str
        ルートログレベル（DEBUG/INFO/WARNING/ERROR/CRITICAL）
    log_file: str | None
        ログファイルのパス（None の場合はコンソールのみ）
    json_file: bool
        ファイル出力を JSON 構造化形式にするか
    """
    logger.remove()

    # コンソール出力（人間可読、色付き）
    logger.add(
        sys.stdout,
        level=level,
        colorize=True,
        backtrace=False,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level:<8}</level> "
            "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>"
        ),
    )

    # ファイル出力（JSON 構造化、ローテーション付き）
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            level=level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=False,
            serialize=json_file,
        )

    # 標準 logging を Loguru に流す
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "sqlalchemy.engine"):
        logging.getLogger(noisy).handlers = [_InterceptHandler()]
        logging.getLogger(noisy).propagate = False


__all__ = ["setup_logging", "logger"]

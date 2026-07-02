# coding: utf-8
"""メッキ管理指標 Excel 変更 → plating_production_indicator 全件置換同期（file watcher 用）"""
import logging
import os

from app.services.file_watcher.plating_excel_processor import is_plating_excel_file
from app.services.plating_production_indicator_import import (
    REMARKS_PREFIX_EXCEL,
    ImportSyncResult,
    sync_plating_source_file,
)
from app.services.file_watcher.sync_services import get_db_connection

logger = logging.getLogger(__name__)


def sync_plating_excel_to_indicator(filepath: str) -> ImportSyncResult:
    """
    生産管理指標(YYYY年度-メッキ).xlsx を plating_production_indicator に同期。
    同一 source_file の既存行を削除してから全件再投入する。
    """
    filename = os.path.basename(filepath or "")
    if not is_plating_excel_file(filename):
        logger.warning("メッキ MES 同期: ファイル名が対象外です: %s", filename)
        return ImportSyncResult(errors=[f"unsupported filename: {filename}"])

    return sync_plating_source_file(
        filepath,
        get_db_connection,
        dry_run=False,
        remarks_prefix=REMARKS_PREFIX_EXCEL,
    )

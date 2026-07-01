# coding: utf-8
"""成形管理指標 Excel 変更 → forming_production_indicator 全件置換同期（file watcher 用）"""
import logging
import os

from app.services.forming_production_indicator_import import (
    REMARKS_PREFIX_EXCEL,
    ImportSyncResult,
    sync_forming_source_file,
)
from app.services.file_watcher.forming_excel_processor import is_forming_excel_file
from app.services.file_watcher.sync_services import get_db_connection

logger = logging.getLogger(__name__)


def sync_forming_excel_to_indicator(filepath: str) -> ImportSyncResult:
    """
    生産管理指標(YYYY年度-成形).xlsx を forming_production_indicator に同期。
    同一 source_file の既存行を削除してから全件再投入する。
    """
    filename = os.path.basename(filepath or "")
    if not is_forming_excel_file(filename):
        logger.warning("成形 MES 同期: ファイル名が対象外です: %s", filename)
        return ImportSyncResult(errors=[f"unsupported filename: {filename}"])

    return sync_forming_source_file(
        filepath,
        get_db_connection,
        dry_run=False,
        remarks_prefix=REMARKS_PREFIX_EXCEL,
    )

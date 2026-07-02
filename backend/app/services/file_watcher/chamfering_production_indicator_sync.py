# coding: utf-8
"""面取管理指標 Excel 変更 → chamfering_production_indicator 全件置換同期（file watcher 用）"""
import logging
import os

from app.services.chamfering_production_indicator_import import (
    REMARKS_PREFIX_EXCEL,
    ImportSyncResult,
    sync_chamfering_source_file,
)
from app.services.file_watcher.chamfering_excel_processor import is_chamfering_excel_file
from app.services.file_watcher.sync_services import get_db_connection

logger = logging.getLogger(__name__)


def sync_chamfering_excel_to_indicator(filepath: str) -> ImportSyncResult:
    """
    生産管理指標(YYYY年度-面取).xlsx を chamfering_production_indicator に同期。
    同一 source_file の既存行を削除してから全件再投入する。
    """
    filename = os.path.basename(filepath or "")
    if not is_chamfering_excel_file(filename):
        logger.warning("面取 MES 同期: ファイル名が対象外です: %s", filename)
        return ImportSyncResult(errors=[f"unsupported filename: {filename}"])

    return sync_chamfering_source_file(
        filepath,
        get_db_connection,
        dry_run=False,
        remarks_prefix=REMARKS_PREFIX_EXCEL,
    )

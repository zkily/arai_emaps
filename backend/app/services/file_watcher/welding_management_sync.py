# coding: utf-8
"""溶接管理指標 Excel 変更 → welding_management 增量同期（file watcher 用）"""
import logging
import os

from app.services.file_watcher.sync_services import get_db_connection
from app.services.file_watcher.welding_excel_processor import is_welding_excel_file
from app.services.welding_management_import import (
    REMARKS_PREFIX_EXCEL,
    ImportSyncResult,
    sync_welding_source_file,
)

logger = logging.getLogger(__name__)


def sync_welding_excel_to_management(filepath: str) -> ImportSyncResult:
    """
    生産管理指標(YYYY年度-溶接).xlsx の「入力」を welding_management に同期。
    - 内容ハッシュ (external_sync_key) で重複 INSERT を防止
    - 作業者名は users.full_name 完全一致を最優先で mes_operator_user_id に紐付け
    """
    filename = os.path.basename(filepath or "")
    if not is_welding_excel_file(filename):
        logger.warning("溶接 MES 同期: ファイル名が対象外です: %s", filename)
        return ImportSyncResult(errors=[f"unsupported filename: {filename}"])

    return sync_welding_source_file(
        filepath,
        get_db_connection,
        dry_run=False,
        skip_unmapped_operator=False,
        remarks_prefix=REMARKS_PREFIX_EXCEL,
    )

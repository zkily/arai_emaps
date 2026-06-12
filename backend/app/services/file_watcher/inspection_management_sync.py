# coding: utf-8
"""検査管理指標 Excel 変更 → inspection_management 增量同期（file watcher 用）"""
import logging
import os

from app.services.file_watcher.inspection_excel_processor import is_inspection_excel_file
from app.services.file_watcher.sync_services import get_db_connection
from app.services.inspection_management_import import (
    REMARKS_PREFIX_EXCEL,
    ImportSyncResult,
    sync_inspection_source_file,
)

logger = logging.getLogger(__name__)


def sync_inspection_excel_to_management(filepath: str) -> ImportSyncResult:
    """
    生産管理指標(YYYY年度-検査).xlsx を inspection_management に同期。
    - 内容ハッシュ (external_sync_key) で重複 INSERT を防止
    - 作業者名は users.full_name 完全一致を最優先で mes_inspector_user_id に紐付け
    """
    filename = os.path.basename(filepath or "")
    if not is_inspection_excel_file(filename):
        logger.warning("検査 MES 同期: ファイル名が対象外です: %s", filename)
        return ImportSyncResult(errors=[f"unsupported filename: {filename}"])

    return sync_inspection_source_file(
        filepath,
        get_db_connection,
        dry_run=False,
        skip_unmapped_inspector=False,
        remarks_prefix=REMARKS_PREFIX_EXCEL,
    )

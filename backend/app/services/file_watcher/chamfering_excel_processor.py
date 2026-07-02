# coding: utf-8
"""面取管理指標 Excel ファイル名判定"""
import re

CHAMFERING_EXCEL_FILENAME_PATTERN = re.compile(r"^生産管理指標\(\d{4}年度-面取\)\.xlsx$")


def is_chamfering_excel_file(filename: str) -> bool:
    normalized = (filename or "").strip()
    if normalized.startswith("~$"):
        return False
    return CHAMFERING_EXCEL_FILENAME_PATTERN.match(normalized) is not None

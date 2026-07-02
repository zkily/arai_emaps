# coding: utf-8
"""メッキ管理指標 Excel ファイル名判定"""
import re

PLATING_EXCEL_FILENAME_PATTERN = re.compile(r"^生産管理指標\(\d{4}年度-メッキ\)\.xlsx$")


def is_plating_excel_file(filename: str) -> bool:
    normalized = (filename or "").strip()
    if normalized.startswith("~$"):
        return False
    return PLATING_EXCEL_FILENAME_PATTERN.match(normalized) is not None

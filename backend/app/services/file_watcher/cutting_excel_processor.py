# coding: utf-8
"""切断管理指標 Excel ファイル名判定"""
import re

CUTTING_EXCEL_FILENAME_PATTERN = re.compile(r"^生産管理指標\(\d{4}年度-切断\)\.xlsx$")


def is_cutting_excel_file(filename: str) -> bool:
    """ファイル名が切断管理指標 Excel かどうか"""
    if not filename:
        return False
    normalized = filename.replace("\uFF08", "(").replace("\uFF09", ")")
    return CUTTING_EXCEL_FILENAME_PATTERN.match(normalized) is not None

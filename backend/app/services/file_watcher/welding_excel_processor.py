# coding: utf-8
"""溶接管理指標 Excel ファイル名判定"""
import re

WELDING_EXCEL_FILENAME_PATTERN = re.compile(r"^生産管理指標\(\d{4}年度-溶接\)\.xlsx$")


def is_welding_excel_file(filename: str) -> bool:
    """ファイル名が溶接管理指標 Excel かどうか"""
    if not filename:
        return False
    normalized = filename.replace("\uFF08", "(").replace("\uFF09", ")")
    return WELDING_EXCEL_FILENAME_PATTERN.match(normalized) is not None

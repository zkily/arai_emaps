# coding: utf-8
"""成形管理指標 Excel ファイル名判定"""
import re

FORMING_EXCEL_FILENAME_PATTERN = re.compile(r"^生産管理指標\(\d{4}年度-成形\)\.xlsx$")


def is_forming_excel_file(filename: str) -> bool:
    """ファイル名が成形管理指標 Excel かどうか"""
    if not filename:
        return False
    normalized = filename.replace("\uFF08", "(").replace("\uFF09", ")")
    return FORMING_EXCEL_FILENAME_PATTERN.match(normalized) is not None

# coding: utf-8
"""ファイル監視用ユーティリティ：エンコーディング読取、日時正規化、ファイル安定待機"""
import csv
import os
import re
import time
from datetime import datetime


def wait_for_file_stable(filepath, timeout=10, poll_interval=0.5, stable_count=3):
    """ファイル書込完了を待つ：poll_interval 秒ごとに確認し、stable_count 回連続でサイズ不変かつ>0 なら安定とみなす"""
    if not filepath or not os.path.exists(filepath):
        return
    last_size = -1
    same_count = 0
    start = time.time()
    while time.time() - start < timeout:
        try:
            if not os.path.isfile(filepath):
                return
            size = os.path.getsize(filepath)
            if size == last_size and size > 0:
                same_count += 1
                if same_count >= stable_count:
                    return
            else:
                same_count = 0
            last_size = size
            time.sleep(poll_interval)
        except OSError:
            time.sleep(poll_interval)


def read_csv_content(filepath, encoding_list=None):
    """尝试多种编码读取 CSV"""
    if encoding_list is None:
        encoding_list = ["shift_jis", "cp932", "utf-8", "euc-jp"]
    for enc in encoding_list:
        try:
            with open(filepath, "r", encoding=enc) as f:
                return list(csv.reader(f))
        except (UnicodeDecodeError, OSError):
            continue
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return list(csv.reader(f))


def normalize_date_str(date_str):
    """统一日期格式为 YYYY-MM-DD"""
    s = (date_str or "").strip()
    if not s:
        return ""
    try:
        if re.match(r"^\d{4}-\d{1,2}-\d{1,2}$", s):
            return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
        if re.match(r"^\d{4}/\d{1,2}/\d{1,2}$", s):
            return datetime.strptime(s, "%Y/%m/%d").strftime("%Y-%m-%d")
        if re.match(r"^\d{8}$", s):
            return datetime.strptime(s, "%Y%m%d").strftime("%Y-%m-%d")
        if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", s):
            return datetime.strptime(s, "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        pass
    return s


def normalize_time_str(time_str):
    """统一时间格式 HH:MM:SS"""
    s = (time_str or "").strip()
    if not s:
        return "00:00:00"
    parts = s.split(":")
    if len(parts) >= 2:
        try:
            h = int(parts[0])
            m = int(parts[1])
            sec = int(parts[2]) if len(parts) > 2 else 0
            return f"{h:02d}:{m:02d}:{sec:02d}"
        except (ValueError, TypeError):
            pass
    return "00:00:00"

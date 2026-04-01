# coding: utf-8
"""検査管理指標 Excel → stock_transaction_logs（4 パターン同期）
ファイル: 生産管理指標(20XX年度-検査).xlsx
処理:
  Part1: 非SD → 製品/実績/KT09 (quantity=E列)
  Part2: SD   → 仕掛品/実績/KT11 (quantity=E列)
  Part3: SD   → 仕掛品/不良/KT11 (quantity=AE列)
  Part4: 非SD → 製品/不良/KT09 (quantity=AE列)
"""
import os
import re
import logging
import warnings
from datetime import datetime, timedelta, date

from app.services.file_watcher.sync_services import get_db_connection

logger = logging.getLogger(__name__)

INSPECTION_EXCEL_FILENAME_PATTERN = re.compile(r"^生産管理指標\(\d{4}年度-検査\)\.xlsx$")
SOURCE_FILE_LABEL = "検査管理指標"
DATE_CUTOFF = date(2026, 3, 1)

COL_A = 0    # target_cd
COL_C = 2    # machine_cd
COL_D = 3    # SD filter
COL_E = 4    # quantity（実績）
COL_AE = 30  # quantity（不良）
COL_AG = 32  # transaction_time

BATCH_SIZE = 500
INCREMENTAL_DAYS = 7


def is_inspection_excel_file(filename):
    """ファイル名が検査管理指標 Excel かどうか"""
    if not filename:
        return False
    normalized = filename.replace("\uFF08", "(").replace("\uFF09", ")")
    return INSPECTION_EXCEL_FILENAME_PATTERN.match(normalized) is not None


def _parse_date(value):
    """Excel 日付を date オブジェクトに変換"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return (datetime(1899, 12, 30) + timedelta(days=float(value))).date()
        except Exception:
            return None
    if isinstance(value, str):
        s = value.strip()[:10]
        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return None


def _parse_number(value):
    """数値に変換。空・非数は None"""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value if value == value else None  # NaN check
    try:
        n = float(value)
        return n if n == n else None
    except (ValueError, TypeError):
        return None


class InspectionExcelProcessor:
    """検査管理指標 Excel → stock_transaction_logs"""

    def is_target_file(self, filename):
        return is_inspection_excel_file(filename)

    def process_file(self, filepath):
        try:
            import openpyxl
        except ImportError:
            logger.error("openpyxl が未インストールです")
            raise

        filename = os.path.basename(filepath)
        logger.info("検査管理指標 Excel 処理開始: %s", filename)

        wb = None
        conn = None
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Print area cannot be set to Defined name")
                wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)

            sheet = wb.active
            if sheet is None:
                logger.warning("Excel にシートがありません: %s", filename)
                return

            non_sd_rows, sd_rows = self._read_and_classify_rows(sheet)
            logger.info("検査管理指標: 非SD %s 行, SD %s 行 (フィルタ後)", len(non_sd_rows), len(sd_rows))

            all_records = self._build_insert_records(non_sd_rows, sd_rows)
            if not all_records:
                logger.info("検査管理指標: 挿入対象レコードなし")
                return

            conn = get_db_connection()
            conn.autocommit = False
            cursor = conn.cursor()
            try:
                deleted, inserted = self._sync_to_db(cursor, all_records)
                conn.commit()
                logger.info("検査管理指標 処理完了: 削除 %s 件, 挿入 %s 件", deleted, inserted)
            except Exception as e:
                conn.rollback()
                logger.error("検査管理指標 DB エラー: %s", e, exc_info=True)
            finally:
                cursor.close()
        except Exception as e:
            logger.error("検査管理指標 Excel 処理失敗 %s: %s", filename, e, exc_info=True)
        finally:
            if wb:
                try:
                    wb.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _read_and_classify_rows(self, sheet):
        """Excel シートを読み取り、SD/非SD に分類"""
        non_sd_rows = []
        sd_rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            row = list(row) if row else []
            if len(row) <= COL_AG:
                continue

            qty_e = _parse_number(row[COL_E])
            if qty_e is None or qty_e <= 0:
                continue

            ag_date = _parse_date(row[COL_AG])
            if ag_date is None or ag_date <= DATE_CUTOFF:
                continue

            target_cd = str(row[COL_A]).strip() if row[COL_A] is not None else ""
            machine_cd = str(row[COL_C]).strip() if len(row) > COL_C and row[COL_C] is not None else ""
            qty_ae = _parse_number(row[COL_AE]) if len(row) > COL_AE else None
            transaction_time = datetime.combine(ag_date, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")

            parsed = {
                "target_cd": target_cd,
                "machine_cd": machine_cd,
                "qty_e": qty_e,
                "qty_ae": qty_ae if qty_ae is not None else 0,
                "transaction_time": transaction_time,
            }

            d_val = str(row[COL_D]) if row[COL_D] is not None else ""
            if "SD" in d_val.upper():
                sd_rows.append(parsed)
            else:
                non_sd_rows.append(parsed)
        return non_sd_rows, sd_rows

    def _build_insert_records(self, non_sd_rows, sd_rows):
        """4 パターンの INSERT レコードを構築"""
        records = []
        # Part 1: 非SD → 製品/実績/KT09, quantity=E
        for r in non_sd_rows:
            records.append((
                '製品', '実績', r['target_cd'], '仕上倉庫', 'KT09',
                r['machine_cd'], r['qty_e'], '本', r['transaction_time'], SOURCE_FILE_LABEL,
            ))
        # Part 2: SD → 仕掛品/実績/KT11, quantity=E
        for r in sd_rows:
            records.append((
                '仕掛品', '実績', r['target_cd'], '仕上倉庫', 'KT11',
                r['machine_cd'], r['qty_e'], '本', r['transaction_time'], SOURCE_FILE_LABEL,
            ))
        # Part 3: SD → 仕掛品/不良/KT11, quantity=AE
        for r in sd_rows:
            if r['qty_ae'] and r['qty_ae'] > 0:
                records.append((
                    '仕掛品', '不良', r['target_cd'], '仕上倉庫', 'KT11',
                    r['machine_cd'], r['qty_ae'], '本', r['transaction_time'], SOURCE_FILE_LABEL,
                ))
        # Part 4: 非SD → 製品/不良/KT09, quantity=AE
        for r in non_sd_rows:
            if r['qty_ae'] and r['qty_ae'] > 0:
                records.append((
                    '製品', '不良', r['target_cd'], '仕上倉庫', 'KT09',
                    r['machine_cd'], r['qty_ae'], '本', r['transaction_time'], SOURCE_FILE_LABEL,
                ))
        return records

    def _sync_to_db(self, cursor, all_records):
        """增量同期: 既存データがあれば過去7日分のみ更新、なければ全量挿入"""
        cursor.execute(
            "SELECT COUNT(*) FROM stock_transaction_logs WHERE source_file = %s",
            (SOURCE_FILE_LABEL,),
        )
        has_existing = cursor.fetchone()[0] > 0
        seven_days_ago = (datetime.now() - timedelta(days=INCREMENTAL_DAYS)).strftime("%Y-%m-%d 00:00:00")

        if has_existing:
            cursor.execute(
                "DELETE FROM stock_transaction_logs WHERE source_file = %s AND transaction_time >= %s",
                (SOURCE_FILE_LABEL, seven_days_ago),
            )
            deleted = cursor.rowcount
            records_to_insert = [r for r in all_records if r[8] >= seven_days_ago]
        else:
            deleted = 0
            records_to_insert = all_records

        insert_sql = """
            INSERT INTO stock_transaction_logs
            (stock_type, transaction_type, target_cd, location_cd, process_cd,
             machine_cd, quantity, unit, transaction_time, source_file)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        inserted = 0
        if records_to_insert:
            for i in range(0, len(records_to_insert), BATCH_SIZE):
                batch = records_to_insert[i:i + BATCH_SIZE]
                cursor.executemany(insert_sql, batch)
            inserted = len(records_to_insert)
        return deleted, inserted

# coding: utf-8
"""在庫取引・材料ログ同期サービス（MySQL へ同期）"""
import hashlib
import logging
import os
import random
import threading
import time
from datetime import date, timedelta

import mysql.connector
from mysql.connector import pooling

from app.core.config import settings
from app.services.file_watcher.utils import read_csv_content, normalize_date_str, normalize_time_str

logger = logging.getLogger(__name__)

_STOCK_SYNC_LOCK = threading.Lock()
_STOCK_SYNC_FINGERPRINT: dict[str, str] = {}
_DB_POOL: pooling.MySQLConnectionPool | None = None
_DB_POOL_LOCK = threading.Lock()

# 在庫取引ファイル → stock_transaction_logs
STOCK_FILES = [
    "StockIn.csv",
    "StockOut.csv",
    "MoldingRecord.csv",
    "CutRecord.csv",
    "ChamferingRecord.csv",
    "WeldingRecord.csv",
    "PlatingRecord.csv",
    "InspectionRecord.csv",
    "PreWeldingInspection.csv",
    "ChamferingNG.csv",
    "InspectionNG.csv",
]

# 材料ログ → material_logs（実パスは .env: MATERIAL_RECEIVING_CSV_PATHS / MATERIAL_RECEIVING_WATCH_BASE_PATH 等）
MATERIAL_FILES = list(settings.get_material_receiving_watch_filenames())

# 部品ログ → part_logs（実パスは .env: PART_RECEIVING_CSV_PATHS 等）
PART_FILES = list(settings.get_part_receiving_watch_filenames())

# ピッキングログファイル → shipping_log（fileWatcherService.js と同等）
# Partslog.csv も同一フォーマットで配置された場合に監視し、取込後は対象 picking_no 分の picking_log_matched を更新
PICKING_FILES = [
    "PickingLog.csv",
    "Partslog.csv",
]

# 突合再計算時に shipping_items を長時間ロックしないよう id 範囲で分割コミット
_PICKING_MATCHED_REFRESH_CHUNK = 800
# shipping_log ホットテーブル保持日数（CSV 取込スキップ・アーカイブ・突合再計算で共有）
SHIPPING_LOG_RETENTION_DAYS = 30
_SHIPPING_LOG_ARCHIVE_CHUNK = 200
_SHIPPING_LOG_ARCHIVE_LOCK_WAIT_TIMEOUT_SEC = 30
_SHIPPING_LOG_ARCHIVE_BATCH_PAUSE_SEC = 0.05
# shipping_log 書込のプロセス間排他（file-watcher と API の同時取込で 1205 を防ぐ）
_SHIPPING_LOG_LOCK_NAME = "smartemap_shipping_log_sync"
_SHIPPING_LOG_LOCK_WAIT_SEC = 180
_SHIPPING_LOG_INSERT_CHUNK = 200
_SHIPPING_LOG_TX_RETRIES = 5
_SHIPPING_LOG_LOCK_WAIT_TIMEOUT_SEC = 5
_RETRYABLE_LOCK_ERRNOS = {1205, 1213}
_SHIPPING_LOG_THREAD_LOCK = threading.Lock()

# 材料切断ログ（MATERIAL_CUTTING_CSV_PATH / materialCutting.csv）→ material_cutting_logs
MATERIAL_CUTTING_CSV_BASENAME = "materialCutting.csv"


def _get_db_pool() -> pooling.MySQLConnectionPool:
    global _DB_POOL
    if _DB_POOL is not None:
        return _DB_POOL
    with _DB_POOL_LOCK:
        if _DB_POOL is None:
            pool_size = max(4, int(getattr(settings, "FILE_WATCH_EXCEL_WORKERS", 3)) + 2)
            _DB_POOL = pooling.MySQLConnectionPool(
                pool_name="file_watcher_pool",
                pool_size=pool_size,
                pool_reset_session=True,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
            )
        return _DB_POOL


def get_db_connection():
    """プロジェクト設定の同期用 MySQL 接続（ファイル監視用・コネクションプール）"""
    return _get_db_pool().get_connection()


def _stock_values_fingerprint(filepath: str, values: list) -> str:
    """解析後データの指紋（DB 同期スキップ判定用）"""
    try:
        st = os.stat(filepath)
        mtime_ns, size = st.st_mtime_ns, st.st_size
    except OSError:
        mtime_ns, size = 0, 0
    h = hashlib.blake2b(digest_size=16)
    h.update(str(mtime_ns).encode())
    h.update(str(size).encode())
    h.update(str(len(values)).encode())
    if values:
        h.update(repr(values[0]).encode())
        h.update(repr(values[-1]).encode())
        if len(values) > 2:
            h.update(repr(values[len(values) // 2]).encode())
    return h.hexdigest()


def _stock_sync_should_skip(path_key: str, fingerprint: str) -> bool:
    if not getattr(settings, "FILE_WATCH_STOCK_SKIP_UNCHANGED", True):
        return False
    with _STOCK_SYNC_LOCK:
        return _STOCK_SYNC_FINGERPRINT.get(path_key) == fingerprint


def _stock_sync_mark_done(path_key: str, fingerprint: str) -> None:
    with _STOCK_SYNC_LOCK:
        _STOCK_SYNC_FINGERPRINT[path_key] = fingerprint


def _stock_replace_days() -> int:
    try:
        return int(getattr(settings, "FILE_WATCH_STOCK_REPLACE_DAYS", 7))
    except (TypeError, ValueError):
        return 7


def _stock_replace_cutoff_str() -> str | None:
    """
    直近 N 日（本日含む）の起点日時。N<=0 のとき None（全件置換モード）。
    例: N=7 → 6 日前 00:00:00 以降を置換対象。
    """
    days = _stock_replace_days()
    if days <= 0:
        return None
    start = date.today() - timedelta(days=days - 1)
    return f"{start.isoformat()} 00:00:00"


def _stock_row_in_replace_window(transaction_time: str, cutoff: str | None) -> bool:
    if cutoff is None:
        return True
    return (transaction_time or "") >= cutoff


# ---------- StockService: 滚动窗口 / 全量镜像同步 ----------


class MaterialCuttingCsvService:
    """materialCutting.csv → material_cutting_logs（file_watcher / API と同じ取込ルール）"""

    def sync(self, filepath, filename):
        from app.modules.material.cutting_import_sync import sync_material_cutting_csv

        try:
            result = sync_material_cutting_csv(filepath)
            logger.info(
                "材料切断CSV 取込完了 %s: imported=%s prune_del=%s window_del=%s err=%s",
                filename,
                result.get("imported"),
                result.get("deleted_prune"),
                result.get("deleted_window"),
                result.get("errors_count"),
            )
            errs = result.get("errors") or []
            if errs:
                logger.warning("材料切断CSV 取込エラー例: %s", errs[:3])
        except Exception as e:
            logger.exception("材料切断CSV 取込失敗 %s: %s", filename, e)


class StockService:
    """
    在庫 CSV → stock_transaction_logs。
    既定: 同一 source_file の「直近 N 日」だけ DELETE 後に CSV の同窗口行を INSERT（N=FILE_WATCH_STOCK_REPLACE_DAYS）。
    N<=0 のとき従来どおり source_file 全削除→全行 INSERT。
    """

    def sync(self, filepath, filename):
        rows = read_csv_content(filepath)
        if not rows or len(rows) < 2:
            return
        data_rows = rows[1:]
        parse_kind = self._parse_kind_for_filename(filename)
        values = []
        for row in data_rows:
            vals = self._parse_row(parse_kind, filename, row)
            if vals:
                values.append(vals)
        cutoff = _stock_replace_cutoff_str()
        replace_days = _stock_replace_days()
        to_insert = [
            v
            for v in values
            if _stock_row_in_replace_window(v[7], cutoff)  # transaction_time
        ]
        skipped_parse = len(data_rows) - len(values)
        skipped_old_csv = len(values) - len(to_insert)
        path_key = os.path.normpath(os.path.abspath(filepath))
        fingerprint = _stock_values_fingerprint(filepath, to_insert if cutoff else values)
        if _stock_sync_should_skip(path_key, fingerprint):
            logger.info(
                "%s 内容未変のため DB 同期をスキップ（窗口 %s 行）",
                filename,
                len(to_insert),
            )
            return
        batch_size = max(100, int(getattr(settings, "FILE_WATCH_STOCK_INSERT_BATCH", 2000)))
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        try:
            if cutoff is None:
                cursor.execute(
                    "DELETE FROM stock_transaction_logs WHERE source_file = %s",
                    (filename,),
                )
            else:
                cursor.execute(
                    """
                    DELETE FROM stock_transaction_logs
                    WHERE source_file = %s AND transaction_time >= %s
                    """,
                    (filename, cutoff),
                )
            deleted = cursor.rowcount
            sql = """
                INSERT INTO stock_transaction_logs
                (stock_type, target_cd, location_cd, process_cd, transaction_type,
                 quantity, unit, transaction_time, order_no, machine_cd, remarks, source_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            inserted = 0
            if to_insert:
                for i in range(0, len(to_insert), batch_size):
                    chunk = to_insert[i : i + batch_size]
                    cursor.executemany(sql, chunk)
                    inserted += cursor.rowcount or len(chunk)
            conn.commit()
            _stock_sync_mark_done(path_key, fingerprint)
            if cutoff:
                logger.info(
                    "%s 処理完了（直近%s日）: DELETE %s, INSERT %s, CSV窗口外 %s, 解析スキップ %s, 起点>=%s",
                    filename,
                    replace_days,
                    deleted,
                    inserted,
                    skipped_old_csv,
                    skipped_parse,
                    cutoff,
                )
            else:
                logger.info(
                    "%s 処理完了（全件置換）: DELETE %s, INSERT %s, 解析スキップ %s",
                    filename,
                    deleted,
                    inserted,
                    skipped_parse,
                )
        except Exception as e:
            conn.rollback()
            logger.error("❌ [Stock] エラー %s: %s", filename, e)
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def _parse_kind_for_filename(filename: str) -> str:
        if "PlatingRecord" in filename:
            return "plating"
        if "Stock" in filename:
            return "stock"
        if "Molding" in filename:
            return "molding"
        if "Welding" in filename:
            return "welding"
        return "default"

    def _parse_row(self, parse_kind: str, filename: str, cols):
        try:
            stock_type, unit, doc_no, machine = "仕掛品", "本", None, None
            if parse_kind == "plating":
                if len(cols) < 9:
                    return None
                date_s, time_s, doc_no, target = cols[1], cols[2], cols[3], cols[5]
                qty = float(cols[7] or 0) * float(cols[8] or 0)
                loc, proc, trans = "工程中間在庫", "KT05", "実績"
            elif parse_kind == "stock":
                if len(cols) < 9:
                    return None
                trans, date_s, time_s = cols[0], cols[1], cols[2]
                doc_no, target = cols[4], cols[5]
                qty = float(cols[7] or 0) * float(cols[8] or 0)
                stock_type, loc, proc = "製品", "製品倉庫", "KT13"
            elif parse_kind in ("molding", "welding"):
                if len(cols) < 9:
                    return None
                date_s, time_s = cols[1], cols[2]
                doc_no, machine, target = cols[4], cols[5], cols[6]
                qty = float(cols[8] or 0)
                trans, loc = "実績", "工程中間在庫"
                proc = "KT04" if parse_kind == "molding" else "KT07"
            else:
                if len(cols) < 9:
                    return None
                target, loc, proc, stk_temp, trans = cols[0], cols[2], cols[3], cols[4], cols[5]
                stock_type = stk_temp if stk_temp in ["製品", "材料", "部品", "仕掛品"] else "仕掛品"
                qty, unit = float(cols[6] or 0), cols[7]
                dt_raw = cols[8]
                date_s = dt_raw.split(" ")[0] if " " in dt_raw else dt_raw
                time_s = dt_raw.split(" ")[1] if " " in dt_raw else "00:00:00"
                if len(cols) > 9:
                    machine = cols[9]
            d = normalize_date_str(date_s)
            t = normalize_time_str(time_s)
            if not d:
                d = "1970-01-01"
            full_time = f"{d} {t}"
            unique_str = f"{target}_{full_time}_{trans}_{proc}_{machine or ''}_{doc_no or ''}"
            return (
                stock_type,
                target,
                loc,
                proc,
                trans,
                qty,
                unit,
                full_time,
                doc_no,
                machine,
                unique_str,
                filename,
            )
        except Exception:
            return None


# ---------- MaterialService: 材料日志 → material_logs ----------

# material_logs 列長（02_baseline / マイグレーション 17 と一致）
_MATERIAL_LOG_STR_LIMITS: dict[str, int] = {
    "item": 100,
    "log_time": 20,
    "hd_no": 50,
    "remarks": 500,
    "material_cd": 50,
    "material_name": 200,
    "process_cd": 50,
    # 既定 100（baseline）。17 番マイグレーション適用後は config で 255 に拡張可
    "manufacture_no": 100,
    "length": 50,
    "supplier": 200,
    "material_quality": 100,
    "note": 500,
}


def _clamp_material_str(value, max_len: int) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if len(s) <= max_len:
        return s
    return s[:max_len]


def _material_manufacture_no_max_len() -> int:
    try:
        return max(1, int(getattr(settings, "MATERIAL_LOG_MANUFACTURE_NO_MAX", 100)))
    except (TypeError, ValueError):
        return 100


def _normalize_manufacture_no(raw) -> str:
    """CSV 製造番号を DB 向けに正規化（指数表記・小数 → 整数文字列、列長で切り詰め）"""
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    if "." in s or "e" in s.lower():
        try:
            s = str(float(s)).split(".")[0]
        except (ValueError, TypeError):
            pass
    return _clamp_material_str(s, _material_manufacture_no_max_len())


def _sanitize_material_log_record(record: dict) -> int:
    """INSERT 前に文字列列を切り詰め。戻り値は切り詰めたフィールド数。"""
    n = 0
    m_no_limits = {**_MATERIAL_LOG_STR_LIMITS, "manufacture_no": _material_manufacture_no_max_len()}
    for field, max_len in m_no_limits.items():
        if field == "manufacture_no":
            continue
        if field not in record:
            continue
        val = record.get(field)
        if val is None or not isinstance(val, str):
            continue
        clipped = _clamp_material_str(val, max_len)
        if clipped != val:
            record[field] = clipped
            n += 1
    m_no = _normalize_manufacture_no(record.get("manufacture_no"))
    if m_no != (record.get("manufacture_no") or ""):
        record["manufacture_no"] = m_no
        n += 1
    record["log_time"] = normalize_time_str(record.get("log_time"))
    t_clipped = _clamp_material_str(record["log_time"], _MATERIAL_LOG_STR_LIMITS["log_time"])
    if t_clipped != record["log_time"]:
        record["log_time"] = t_clipped
        n += 1
    return n


def _log_time_key_for_material_sync(t) -> str:
    """DB / CSV の時刻を material_logs 突合用キーに正規化（HH:MM:SS）"""
    if t is None:
        return "00:00:00"
    if isinstance(t, str):
        return normalize_time_str(t)
    if hasattr(t, "hour") and hasattr(t, "minute"):
        sec = getattr(t, "second", 0) or 0
        return f"{int(t.hour):02d}:{int(t.minute):02d}:{int(sec):02d}"
    if hasattr(t, "total_seconds"):
        secs = int(t.total_seconds()) % 86400
        h, r = divmod(secs, 3600)
        m, s = divmod(r, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    return normalize_time_str(str(t))


def _material_log_manual_key(log_date, log_time, manufacture_no) -> tuple:
    if log_date is not None and hasattr(log_date, "isoformat"):
        dstr = log_date.isoformat()[:10]
    else:
        dstr = str(log_date or "")[:10]
    return (dstr, _log_time_key_for_material_sync(log_time), (manufacture_no or "").strip())


def _fetch_material_manual_snapshot(cursor, keys: list[tuple]) -> dict:
    """
    CSV 同期で削除される可能性がある行のうち、手動「切断使用済」を付けた行だけスナップショット。
    keys: (log_date, log_time, manufacture_no)（CSV 解析結果と同じ）
    """
    if not keys:
        return {}
    seen: list[tuple] = []
    dedup = set()
    for k in keys:
        if k in dedup:
            continue
        dedup.add(k)
        seen.append(k)
    out: dict = {}
    batch_size = 300
    for i in range(0, len(seen), batch_size):
        batch = seen[i : i + batch_size]
        placeholders = ",".join(["(%s,%s,%s)"] * len(batch))
        flat = [x for t in batch for x in t]
        try:
            cursor.execute(
                f"""
                SELECT log_date, log_time, manufacture_no, cutting_used_manual_at,
                       cutting_used_manual_by, cutting_used_manual_note
                FROM material_logs
                WHERE cutting_used_manual = 1
                  AND (log_date, log_time, manufacture_no) IN ({placeholders})
                """,
                flat,
            )
        except mysql.connector.Error as e:
            err = str(e)
            if "Unknown column" in err or "doesn't exist" in err.lower():
                logger.debug("material_logs に手動切断列なし、スキップ: %s", err)
                return {}
            raise
        for row in cursor.fetchall():
            mk = _material_log_manual_key(
                row["log_date"], row["log_time"], row["manufacture_no"]
            )
            out[mk] = {
                "at": row["cutting_used_manual_at"],
                "by": row["cutting_used_manual_by"],
                "note": row["cutting_used_manual_note"],
            }
    return out


def _fetch_material_manual_snapshot_by_item(cursor, item: str) -> dict:
    try:
        cursor.execute(
            """
            SELECT log_date, log_time, manufacture_no, cutting_used_manual_at,
                   cutting_used_manual_by, cutting_used_manual_note
            FROM material_logs
            WHERE item = %s AND cutting_used_manual = 1
            """,
            (item,),
        )
    except mysql.connector.Error as e:
        err = str(e)
        if "Unknown column" in err or "doesn't exist" in err.lower():
            return {}
        raise
    out: dict = {}
    for row in cursor.fetchall():
        mk = _material_log_manual_key(
            row["log_date"], row["log_time"], row["manufacture_no"]
        )
        out[mk] = {
            "at": row["cutting_used_manual_at"],
            "by": row["cutting_used_manual_by"],
            "note": row["cutting_used_manual_note"],
        }
    return out


def _restore_material_manual_flags(cursor, final_list: list, manual_map: dict) -> int:
    """INSERT 後、同一业务键に手動フラグを戻す"""
    if not manual_map or not final_list:
        return 0
    restored = 0
    for d in final_list:
        mk = _material_log_manual_key(
            d.get("log_date"), d.get("log_time"), d.get("manufacture_no")
        )
        if mk not in manual_map:
            continue
        m = manual_map[mk]
        try:
            cursor.execute(
                """
                UPDATE material_logs SET
                    cutting_used_manual = 1,
                    cutting_used_manual_at = %s,
                    cutting_used_manual_by = %s,
                    cutting_used_manual_note = %s
                WHERE item = %s AND log_date = %s AND log_time = %s AND manufacture_no <=> %s
                """,
                (
                    m["at"],
                    m["by"],
                    m["note"],
                    d.get("item"),
                    d.get("log_date"),
                    d.get("log_time"),
                    d.get("manufacture_no"),
                ),
            )
            restored += int(cursor.rowcount or 0)
        except mysql.connector.Error as e:
            if "Unknown column" in str(e):
                return restored
            raise
    return restored


class MaterialService:
    """材料 CSV → material_logs（解析、补全、按业务键删除后插入）"""

    def sync(self, filepath, filename):
        """CSV を material_logs に同期。戻り値は API 用（file_watcher ワーカーは無視してよい）。"""
        rows = read_csv_content(filepath, encoding_list=["shift_jis", "cp932"])
        if not rows or len(rows) < 2:
            return {"success": True, "processedCount": 0, "error": None}
        data_rows = rows[1:]
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)
        try:
            parsed_data = []
            for row in data_rows:
                if len(row) < 6:
                    continue
                item = self._parse_single_row(filename, row)
                if item:
                    parsed_data.append(item)
            if not parsed_data:
                logger.warning("⚠️ [Material] %s 解析後に有効データなし", filename)
                return {"success": True, "processedCount": 0, "error": None}
            self._enrich_data(cursor, parsed_data, filename)
            deleted_count = 0
            manual_snapshot: dict = {}
            if "Maruiti" in filename:
                keys = [
                    (d["log_date"], d["log_time"], d["manufacture_no"])
                    for d in parsed_data
                ]
                manual_snapshot = _fetch_material_manual_snapshot(cursor, keys)
                batch_size = 500
                for i in range(0, len(keys), batch_size):
                    batch = keys[i : i + batch_size]
                    if not batch:
                        continue
                    placeholders = ",".join(["(%s, %s, %s)"] * len(batch))
                    flat = [x for t in batch for x in t]
                    cursor.execute(
                        "DELETE FROM material_logs WHERE (log_date, log_time, manufacture_no) IN ("
                        + placeholders
                        + ")",
                        flat,
                    )
                    deleted_count += cursor.rowcount
            else:
                target_item = parsed_data[0]["item"]
                manual_snapshot = _fetch_material_manual_snapshot_by_item(cursor, target_item)
                cursor.execute("DELETE FROM material_logs WHERE item = %s", (target_item,))
                deleted_count = cursor.rowcount
            unique_map = {}
            for d in parsed_data:
                key = f"{d['log_date']}_{d['log_time']}_{d['manufacture_no']}"
                if key not in unique_map:
                    d["note"] = key
                    unique_map[key] = d
            final_list = list(unique_map.values())
            truncated_fields = 0
            for d in final_list:
                if d.get("log_date") == "":
                    d["log_date"] = "1970-01-01"
                if d.get("manufacture_date") == "":
                    d["manufacture_date"] = None
                truncated_fields += _sanitize_material_log_record(d)
            if truncated_fields > 0:
                logger.warning(
                    "⚠️ [Material] %s: %s フィールドを列長に合わせて切り詰め（manufacture_no 上限 %s）",
                    filename,
                    truncated_fields,
                    _material_manufacture_no_max_len(),
                )
            insert_sql = """
                INSERT INTO material_logs (
                    item, log_date, log_time, hd_no, remarks,
                    material_cd, material_name, process_cd,
                    manufacture_no, manufacture_date, pieces_per_bundle,
                    length, quantity, bundle_quantity, magnetic, appearance,
                    outer_diameter1, outer_diameter2, supplier, material_quality, note
                ) VALUES (
                    %(item)s, %(log_date)s, %(log_time)s, %(hd_no)s, %(remarks)s,
                    %(material_cd)s, %(material_name)s, %(process_cd)s,
                    %(manufacture_no)s, %(manufacture_date)s, %(pieces_per_bundle)s,
                    %(length)s, %(quantity)s, %(bundle_quantity)s, %(magnetic)s, %(appearance)s,
                    %(outer_diameter1)s, %(outer_diameter2)s, %(supplier)s, %(material_quality)s, %(note)s
                )
            """
            if final_list:
                cursor.executemany(insert_sql, final_list)
                inserted_count = cursor.rowcount
                if manual_snapshot:
                    n_rest = _restore_material_manual_flags(
                        cursor, final_list, manual_snapshot
                    )
                    if n_rest > 0:
                        logger.info(
                            "📌 [Material] %s 手動切断使用済を %s 行復元（CSV 同期後）",
                            filename,
                            n_rest,
                        )
            else:
                inserted_count = 0
            conn.commit()
            skipped = len(data_rows) - inserted_count
            logger.info("%s 処理完了: %s件処理, %s件スキップ", filename, inserted_count, skipped)
            return {"success": True, "processedCount": int(inserted_count), "error": None}
        except Exception as e:
            conn.rollback()
            logger.error("❌ [Material] エラー %s: %s", filename, e, exc_info=True)
            return {"success": False, "processedCount": 0, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

    def _parse_single_row(self, filename, row):
        try:
            base = {
                "item": row[0],
                "log_date": normalize_date_str(row[1]),
                "log_time": row[2],
                "hd_no": row[3],
                "remarks": row[4],
                "magnetic": 1,
                "appearance": 1,
                "bundle_quantity": 1,
                "outer_diameter1": 0,
                "outer_diameter2": 0,
                "note": "",
            }
            if "Nagoya" in filename:
                m_no = _normalize_manufacture_no(row[5] if len(row) > 5 else "")
                base.update(
                    {
                        "material_cd": "10040",
                        "manufacture_no": m_no,
                        "manufacture_date": base["log_date"],
                        "pieces_per_bundle": 300,
                        "length": "5345",
                        "material_name": "14.0×1.00×5345",
                        "process_cd": "KT19",
                        "quantity": 300,
                        "supplier": "名古屋 ﾊﾟｲﾌﾟ",
                        "material_quality": "H800",
                    }
                )
            elif "JFE" in filename:
                base.update(
                    {
                        "material_cd": "10087",
                        "manufacture_no": _normalize_manufacture_no(row[5] if len(row) > 5 else ""),
                        "manufacture_date": base["log_date"],
                        "pieces_per_bundle": 250,
                        "length": "4730",
                        "material_name": "14.0×2.30×4730",
                        "process_cd": "KT19",
                        "quantity": 250,
                        "supplier": "JFE溶接鋼管",
                        "material_quality": "INOAC55",
                    }
                )
            elif "Okajima" in filename:
                col5 = row[5]
                m_name, length, pieces = "", 0, 0
                if len(col5) >= 26:
                    right26 = col5[-26:]
                    try:
                        v1 = float(right26[0:3]) / 10
                        v2 = float(right26[5:8]) / 100
                        v3 = int(right26[12:16])
                        m_name = f"{v1:.1f}×{v2:.2f}×{v3}"
                        length = v3
                        pieces = int(right26[21:24])
                    except Exception:
                        pass
                base.update(
                    {
                        "material_cd": "",
                        "manufacture_no": _normalize_manufacture_no(row[6] if len(row) > 6 else ""),
                        "manufacture_date": base["log_date"],
                        "pieces_per_bundle": pieces,
                        "length": str(length),
                        "material_name": m_name,
                        "process_cd": "KT19",
                        "quantity": pieces,
                        "supplier": "",
                        "material_quality": "",
                    }
                )
            elif "Maruiti" in filename:
                col6 = row[5]
                m_cd = col6[32:35] if len(col6) >= 35 else ""
                m_no = _normalize_manufacture_no(col6[0:8] if len(col6) >= 8 else "")
                pieces = (
                    int(col6[66:69])
                    if len(col6) >= 69 and col6[66:69].isdigit()
                    else 0
                )
                length = (
                    int(col6[53:57])
                    if len(col6) >= 57 and col6[53:57].isdigit()
                    else 0
                )
                m_date = ""
                if len(col6) >= 9:
                    rp = col6[-9:]
                    yyyy, mm, dd = rp[0:4], rp[4:6], rp[6:8]
                    if yyyy.isdigit() and mm.isdigit() and dd.isdigit():
                        m_date = f"{yyyy}-{mm}-{dd}"
                base.update(
                    {
                        "material_cd": m_cd,
                        "manufacture_no": m_no,
                        "manufacture_date": m_date,
                        "pieces_per_bundle": pieces,
                        "length": str(length),
                        "material_name": "",
                        "process_cd": "KT19",
                        "quantity": pieces,
                        "supplier": "",
                        "material_quality": "",
                    }
                )
            return base
        except Exception as e:
            logger.warning("行の解析に失敗: %s", e)
            return None

    def _enrich_data(self, cursor, data_list, filename):
        m_names = set(d["material_name"] for d in data_list if d.get("material_name"))
        m_cds = set(d["material_cd"] for d in data_list if d.get("material_cd"))
        mat_info_map = {}
        if m_names:
            fmt = ",".join(["%s"] * len(m_names))
            cursor.execute(
                """
                SELECT m.material_name, m.material_cd, m.standard_spec, m.min_value, m.max_value, s.supplier_name, m.supplier_cd
                FROM materials m
                LEFT JOIN suppliers s ON m.supplier_cd = s.supplier_cd
                WHERE m.material_name IN ("""
                + fmt
                + ")",
                list(m_names),
            )
            for row in cursor.fetchall():
                mat_info_map[row["material_name"]] = row
        ins_std_map = {}
        if "Maruiti" in filename and m_cds:
            try:
                fmt = ",".join(["%s"] * len(m_cds))
                cursor.execute(
                    "SELECT inspection_cd, inspection_standard FROM material_inspection_master WHERE inspection_cd IN ("
                    + fmt
                    + ")",
                    list(m_cds),
                )
                for row in cursor.fetchall():
                    ins_std_map[row["inspection_cd"]] = row["inspection_standard"]
            except Exception:
                pass
        for d in data_list:
            if "Maruiti" in filename:
                std = ins_std_map.get(d["material_cd"], d["material_cd"])
                d["material_name"] = f"{std}{d['length']}"
        if "Maruiti" in filename:
            new_names = set(d["material_name"] for d in data_list if d.get("material_name"))
            if new_names:
                fmt = ",".join(["%s"] * len(new_names))
                cursor.execute(
                    """
                    SELECT m.material_name, s.supplier_name, m.standard_spec, m.min_value, m.max_value
                    FROM materials m
                    LEFT JOIN suppliers s ON m.supplier_cd = s.supplier_cd
                    WHERE m.material_name IN ("""
                    + fmt
                    + ")",
                    list(new_names),
                )
                for row in cursor.fetchall():
                    mat_info_map[row["material_name"]] = row
        for d in data_list:
            info = mat_info_map.get(d["material_name"], {})
            if "Okajima" in filename:
                d["material_cd"] = info.get("material_cd", "")
                d["supplier"] = info.get("supplier_name", "")
                d["material_quality"] = info.get("standard_spec", "")
            if "Maruiti" in filename:
                d["supplier"] = info.get("supplier_name", "")
                d["material_quality"] = info.get("standard_spec", "")
            min_v = float(info.get("min_value") or 0)
            max_v = float(info.get("max_value") or 0)
            if max_v > min_v:
                d["outer_diameter1"] = round(random.uniform(min_v, max_v), 3)
                d["outer_diameter2"] = round(random.uniform(min_v, max_v), 3)
            else:
                d["outer_diameter1"] = 0
                d["outer_diameter2"] = 0


def _material_parsed_row_to_part(row: dict) -> dict:
    """MaterialService の解析結果を part_logs 向け dict に変換"""
    return {
        "item": row.get("item"),
        "log_date": row.get("log_date"),
        "log_time": row.get("log_time"),
        "hd_no": row.get("hd_no"),
        "remarks": row.get("remarks"),
        "part_cd": row.get("material_cd") or "",
        "part_name": row.get("material_name") or "",
        "process_cd": row.get("process_cd") or "",
        "manufacture_no": row.get("manufacture_no"),
        "manufacture_date": row.get("manufacture_date"),
        "pieces_per_bundle": row.get("pieces_per_bundle"),
        "length": row.get("length"),
        "quantity": row.get("quantity"),
        "bundle_quantity": row.get("bundle_quantity"),
        "magnetic": row.get("magnetic"),
        "appearance": row.get("appearance"),
        "outer_diameter1": row.get("outer_diameter1"),
        "outer_diameter2": row.get("outer_diameter2"),
        "supplier": row.get("supplier"),
        "part_quality": row.get("material_quality"),
        "note": row.get("note") or "",
    }


class PartService:
    """部品 CSV → part_logs（MaterialService と同一 CSV 形式・部品マスタで補完）"""

    def sync(self, filepath, filename):
        rows = read_csv_content(filepath, encoding_list=["shift_jis", "cp932"])
        if not rows or len(rows) < 2:
            return {"success": True, "processedCount": 0, "error": None}
        data_rows = rows[1:]
        mat_svc = MaterialService()
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)
        try:
            parsed_data = []
            for row in data_rows:
                if len(row) < 6:
                    continue
                item = mat_svc._parse_single_row(filename, row)
                if item:
                    parsed_data.append(_material_parsed_row_to_part(item))
            if not parsed_data:
                logger.warning("⚠️ [Part] %s 解析後に有効データなし", filename)
                return {"success": True, "processedCount": 0, "error": None}
            self._enrich_data(cursor, parsed_data, filename)
            deleted_count = 0
            if "Maruiti" in filename:
                keys = [
                    (d["log_date"], d["log_time"], d["manufacture_no"])
                    for d in parsed_data
                ]
                batch_size = 500
                for i in range(0, len(keys), batch_size):
                    batch = keys[i : i + batch_size]
                    if not batch:
                        continue
                    placeholders = ",".join(["(%s, %s, %s)"] * len(batch))
                    flat = [x for t in batch for x in t]
                    cursor.execute(
                        "DELETE FROM part_logs WHERE (log_date, log_time, manufacture_no) IN ("
                        + placeholders
                        + ")",
                        flat,
                    )
                    deleted_count += cursor.rowcount
            else:
                target_item = parsed_data[0]["item"]
                cursor.execute("DELETE FROM part_logs WHERE item = %s", (target_item,))
                deleted_count = cursor.rowcount
            unique_map = {}
            for d in parsed_data:
                key = f"{d['log_date']}_{d['log_time']}_{d['manufacture_no']}"
                if key not in unique_map:
                    d["note"] = key
                    unique_map[key] = d
            final_list = list(unique_map.values())
            for d in final_list:
                if d.get("log_date") == "":
                    d["log_date"] = "1970-01-01"
                if d.get("manufacture_date") == "":
                    d["manufacture_date"] = None
                d["log_time"] = normalize_time_str(d.get("log_time"))
            insert_sql = """
                INSERT INTO part_logs (
                    item, log_date, log_time, hd_no, remarks,
                    part_cd, part_name, process_cd,
                    manufacture_no, manufacture_date, pieces_per_bundle,
                    length, quantity, bundle_quantity, magnetic, appearance,
                    outer_diameter1, outer_diameter2, supplier, part_quality, note
                ) VALUES (
                    %(item)s, %(log_date)s, %(log_time)s, %(hd_no)s, %(remarks)s,
                    %(part_cd)s, %(part_name)s, %(process_cd)s,
                    %(manufacture_no)s, %(manufacture_date)s, %(pieces_per_bundle)s,
                    %(length)s, %(quantity)s, %(bundle_quantity)s, %(magnetic)s, %(appearance)s,
                    %(outer_diameter1)s, %(outer_diameter2)s, %(supplier)s, %(part_quality)s, %(note)s
                )
            """
            inserted_count = 0
            if final_list:
                cursor.executemany(insert_sql, final_list)
                inserted_count = cursor.rowcount
            conn.commit()
            skipped = len(data_rows) - inserted_count
            logger.info("%s 処理完了: %s件処理, %s件スキップ", filename, inserted_count, skipped)
            return {"success": True, "processedCount": int(inserted_count), "error": None}
        except Exception as e:
            conn.rollback()
            logger.error("❌ [Part] エラー %s: %s", filename, e, exc_info=True)
            return {"success": False, "processedCount": 0, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

    def _enrich_data(self, cursor, data_list, filename):
        p_names = set(d["part_name"] for d in data_list if d.get("part_name"))
        p_cds = set(d["part_cd"] for d in data_list if d.get("part_cd"))
        part_info_map = {}
        if p_names:
            fmt = ",".join(["%s"] * len(p_names))
            cursor.execute(
                """
                SELECT p.part_name, p.part_cd, p.category, s.supplier_name, p.supplier_cd
                FROM parts p
                LEFT JOIN suppliers s ON p.supplier_cd = s.supplier_cd
                WHERE p.part_name IN ("""
                + fmt
                + ")",
                list(p_names),
            )
            for row in cursor.fetchall():
                part_info_map[row["part_name"]] = row
        for d in data_list:
            info = part_info_map.get(d["part_name"], {})
            if "Okajima" in filename:
                d["part_cd"] = info.get("part_cd", d.get("part_cd") or "")
                d["supplier"] = info.get("supplier_name", d.get("supplier") or "")
                d["part_quality"] = info.get("category", d.get("part_quality") or "")
            if "Maruiti" in filename:
                d["supplier"] = info.get("supplier_name", d.get("supplier") or "")
                d["part_quality"] = info.get("category", d.get("part_quality") or "")


# ---------- PickingLogService: PickingLog.csv → shipping_log（fileWatcherService.js と同等）----------


def _picking_int(v):
    """数値に変換。空・非数は 0。"""
    if v is None or str(v).strip() == "":
        return 0
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return 0


def _picking_format_date(s):
    """日付を YYYY-MM-DD に正規化。空は None。"""
    if not s or not str(s).strip():
        return None
    out = normalize_date_str(str(s).strip())
    return out if out else None


def _picking_format_datetime(dt_str, date_str=None):
    """日時を YYYY-MM-DD HH:MM:SS に。時間のみの場合は date_str と結合。"""
    if not dt_str or not str(dt_str).strip():
        return None
    s = str(dt_str).strip()
    # 既に日付+時間
    if " " in s or "T" in s or ("-" in s and ":" in s):
        try:
            from datetime import datetime as dt
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
                try:
                    return dt.strptime(s[:19], fmt).strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
        except Exception:
            pass
    # 時間のみ → date と結合
    if ":" in s:
        parts = s.split(":")
        if len(parts) >= 2:
            try:
                h = int(parts[0])
                m = int(parts[1])
                sec = int(parts[2]) if len(parts) > 2 else 0
                if 0 <= h <= 23 and 0 <= m <= 59 and 0 <= sec <= 59:
                    date_part = _picking_format_date(date_str) if date_str else None
                    if not date_part:
                        from datetime import date as date_type
                        date_part = date_type.today().strftime("%Y-%m-%d")
                    return f"{date_part} {h:02d}:{m:02d}:{sec:02d}"
            except (ValueError, TypeError):
                pass
    return None


def _is_picking_header_row(row) -> bool:
    """判定是否为 PickingLog/Partslog 的表头行（含重复表头）。"""
    if not row:
        return False
    vals = [str(c or "").strip().lower() for c in row]
    # 常见表头关键词（中日英混在内）
    header_tokens = {
        "project", "date", "datetime", "model_no", "person_in_charge",
        "picking_no", "product_name", "product_code", "product_name_2",
        "quantity", "shipping_quantity",
        "プロジェクト", "日付", "日時", "型式", "担当者", "ピッキングno",
        "品名", "品番", "数量", "出荷数量",
    }
    # 任一关键列命中即可判定为表头；避免误判普通数据，要求至少命中2列
    hit = sum(1 for v in vals if v in header_tokens)
    return hit >= 2


def _is_retryable_lock_error(exc: BaseException) -> bool:
    errno = getattr(exc, "errno", None)
    if errno in _RETRYABLE_LOCK_ERRNOS:
        return True
    msg = str(exc)
    return "1205" in msg or "1213" in msg or "Lock wait timeout" in msg or "Deadlock" in msg


def _sleep_lock_backoff(attempt: int) -> None:
    time.sleep(0.15 * (2**attempt) + random.uniform(0, 0.25))


def _acquire_shipping_log_lock(cursor, timeout_sec: int = _SHIPPING_LOG_LOCK_WAIT_SEC) -> bool:
    """GET_LOCK で shipping_log 同期をプロセス間直列化する。取得できなければ False。"""
    deadline = time.monotonic() + max(1, int(timeout_sec))
    warned = False
    while True:
        remaining = max(0, int(deadline - time.monotonic()))
        wait_sec = min(5, remaining)
        cursor.execute("SELECT GET_LOCK(%s, %s)", (_SHIPPING_LOG_LOCK_NAME, wait_sec))
        row = cursor.fetchone()
        got = 0
        if row is not None:
            val = row[0] if not isinstance(row, dict) else next(iter(row.values()))
            try:
                got = int(val or 0)
            except (TypeError, ValueError):
                got = 0
        if got == 1:
            return True
        if time.monotonic() >= deadline:
            return False
        if not warned:
            logger.info("shipping_log 同期ロック待ち（他プロセスの取込完了を待機）")
            warned = True


def _release_shipping_log_lock(cursor) -> None:
    try:
        cursor.execute("SELECT RELEASE_LOCK(%s)", (_SHIPPING_LOG_LOCK_NAME,))
        cursor.fetchone()
    except Exception:
        pass


def _set_shipping_log_lock_wait_timeout(cursor) -> None:
    cursor.execute(
        f"SET SESSION innodb_lock_wait_timeout = {_SHIPPING_LOG_LOCK_WAIT_TIMEOUT_SEC}"
    )


_SHIPPING_LOG_INSERT_SQL = """
    INSERT INTO shipping_log
    (project, date, datetime, model_no, person_in_charge, picking_no, product_name, product_code, product_name_2, quantity, shipping_quantity)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    project = VALUES(project),
    date = VALUES(date),
    datetime = VALUES(datetime),
    model_no = VALUES(model_no),
    person_in_charge = VALUES(person_in_charge),
    product_name = VALUES(product_name),
    product_code = VALUES(product_code),
    product_name_2 = VALUES(product_name_2),
    quantity = VALUES(quantity),
    shipping_quantity = VALUES(shipping_quantity),
    updated_at = CURRENT_TIMESTAMP
"""


def _shipping_log_row_values(rec: dict) -> tuple:
    return (
        rec["project"],
        rec["date"],
        rec["datetime"],
        rec["model_no"],
        rec["person_in_charge"],
        rec["picking_no"],
        rec["product_name"],
        rec["product_code"],
        rec["product_name_2"],
        rec["quantity"],
        rec["shipping_quantity"],
    )


def _insert_shipping_log_rows(cursor, conn, records: list) -> tuple[int, int, list]:
    """shipping_log をチャンク単位で INSERT/UPDATE し、都度 COMMIT して行ロックを短くする。"""
    inserted, updated = 0, 0
    synced: list = []
    for i in range(0, len(records), _SHIPPING_LOG_INSERT_CHUNK):
        chunk = records[i : i + _SHIPPING_LOG_INSERT_CHUNK]
        vals = [_shipping_log_row_values(rec) for rec in chunk]
        written = False
        for attempt in range(_SHIPPING_LOG_TX_RETRIES):
            try:
                _set_shipping_log_lock_wait_timeout(cursor)
                cursor.executemany(_SHIPPING_LOG_INSERT_SQL, vals)
                conn.commit()
                synced.extend(chunk)
                written = True
                # executemany の rowcount はドライバにより合計値が不安定なため件数はチャンク長で概算しない
                break
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                if _is_retryable_lock_error(e) and attempt < _SHIPPING_LOG_TX_RETRIES - 1:
                    logger.warning(
                        "shipping_log チャンク書込でロック競合 (errno=%s) 再試行 %s/%s",
                        getattr(e, "errno", None),
                        attempt + 1,
                        _SHIPPING_LOG_TX_RETRIES,
                    )
                    _sleep_lock_backoff(attempt)
                    continue
                break
        if written:
            continue
        for rec, row_vals in zip(chunk, vals):
            for attempt in range(_SHIPPING_LOG_TX_RETRIES):
                try:
                    _set_shipping_log_lock_wait_timeout(cursor)
                    cursor.execute(_SHIPPING_LOG_INSERT_SQL, row_vals)
                    rc = int(cursor.rowcount or 0)
                    conn.commit()
                    if rc == 1:
                        inserted += 1
                    elif rc == 2:
                        updated += 1
                    synced.append(rec)
                    break
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    if _is_retryable_lock_error(e) and attempt < _SHIPPING_LOG_TX_RETRIES - 1:
                        _sleep_lock_backoff(attempt)
                        continue
                    logger.warning("shipping_log 挿入/更新失敗: %s", e)
                    break
    return inserted, updated, synced


class PickingLogService:
    """PickingLog.csv → shipping_log（重複は (picking_no, product_code, date) で ON DUPLICATE KEY UPDATE）。"""

    def sync(self, filepath, filename, *, raise_on_error: bool = False):
        rows = read_csv_content(filepath)
        if not rows or len(rows) < 2:
            return
        # 先頭行がヘッダーならスキップ（project, date 等）
        start = 0
        if rows and rows[0] and len(rows[0]) > 0:
            first = str(rows[0][0]).strip().lower()
            if first in ("project", "date", "プロジェクト", "日付"):
                start = 1
        data_rows = [r for r in rows[start:] if r and len(r) >= 8]
        records = []
        cutoff_date = date.today() - timedelta(days=SHIPPING_LOG_RETENTION_DAYS)
        skipped_old = 0
        for r in data_rows:
            if _is_picking_header_row(r):
                continue
            # 列: project, date, datetime, model_no, person_in_charge, picking_no, product_name, product_code, product_name_2, quantity, shipping_quantity
            rec = {
                "project": (r[0] or "").strip() if len(r) > 0 else "",
                "date": _picking_format_date(r[1]) if len(r) > 1 else None,
                "datetime": _picking_format_datetime(r[2] if len(r) > 2 else None, r[1] if len(r) > 1 else None),
                "model_no": (r[3] or "").strip() if len(r) > 3 else "",
                "person_in_charge": (r[4] or "").strip() if len(r) > 4 else "",
                "picking_no": (r[5] or "").strip() if len(r) > 5 else "",
                "product_name": (r[6] or "").strip() if len(r) > 6 else "",
                "product_code": (r[7] or "").strip() if len(r) > 7 else "",
                "product_name_2": (r[8] or "").strip() if len(r) > 8 else "",
                "quantity": _picking_int(r[9]) if len(r) > 9 else 0,
                "shipping_quantity": _picking_int(r[10]) if len(r) > 10 else 0,
            }
            # 保持期間外のログは再取込しない（ホットテーブルは直近 SHIPPING_LOG_RETENTION_DAYS 日）
            rec_date = rec["date"]
            if rec_date:
                try:
                    y, m, d = str(rec_date).split("-")
                    dval = date(int(y), int(m), int(d))
                    if dval < cutoff_date:
                        skipped_old += 1
                        continue
                except Exception:
                    # 日付変換失敗時は従来どおり処理対象に残す
                    pass
            if rec["picking_no"] or rec["product_code"]:
                records.append(rec)
        if not records:
            logger.warning(
                "⚠️ [PickingLog] %s 有効レコードなし（%s日超過スキップ: %s）",
                filename,
                SHIPPING_LOG_RETENTION_DAYS,
                skipped_old,
            )
            return
        # 同一ファイル内で (picking_no, product_code, date) 重複除去
        seen = set()
        unique_records = []
        for rec in records:
            key = (rec["picking_no"] or "", rec["product_code"] or "", rec["date"] or "")
            if key in seen:
                continue
            seen.add(key)
            unique_records.append(rec)
        with _SHIPPING_LOG_THREAD_LOCK:
            conn = get_db_connection()
            conn.autocommit = False
            cursor = conn.cursor()
            lock_held = False
            try:
                if not _acquire_shipping_log_lock(cursor):
                    msg = "shipping_log 同期ロックを取得できませんでした。他プロセスの取込完了後に再試行してください。"
                    logger.warning("%s: %s", filename, msg)
                    if raise_on_error:
                        raise RuntimeError(msg)
                    return
                lock_held = True
                _set_shipping_log_lock_wait_timeout(cursor)
                _, _, records_to_sync_pt = _insert_shipping_log_rows(
                    cursor, conn, unique_records
                )
                logger.info(
                    "%s 処理完了: shipping_log 取込 %s 件",
                    filename,
                    len(records_to_sync_pt),
                )
                if skipped_old > 0:
                    logger.info(
                        "%s 取込時に %s日超過レコード %s 件をスキップ",
                        filename,
                        SHIPPING_LOG_RETENTION_DAYS,
                        skipped_old,
                    )
                self._refresh_shipping_items_picking_log_matched_for_batch(
                    cursor, conn, records_to_sync_pt
                )
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.error("❌ [PickingLog] エラー %s: %s", filename, e, exc_info=True)
                if raise_on_error:
                    raise
            finally:
                if lock_held:
                    _release_shipping_log_lock(cursor)
                cursor.close()
                conn.close()

    def _refresh_shipping_items_picking_log_matched_for_batch(self, cursor, conn, source_records):
        """PickingLog 取込後、当該 picking_no に対応する shipping_items.picking_log_matched を 1 にする。

        picking_no は通常 shipping_no_p。パレット番号（shipping_no）のみのログは品番でも突合する。
        shipping_log への EXISTS 相関は行ロックを広げるため使わない（取込成功分は突合済みとみなす）。
        """
        if not source_records:
            return
        pns: list[str] = []
        empty_pc_pns: list[str] = []
        product_pairs: list[tuple[str, str]] = []
        for r in source_records:
            pn = (r.get("picking_no") or "").strip()
            if not pn:
                continue
            if pn not in pns:
                pns.append(pn)
            pc = (r.get("product_code") or "").strip()
            if not pc:
                if pn not in empty_pc_pns:
                    empty_pc_pns.append(pn)
            else:
                pair = (pn, pc)
                if pair not in product_pairs:
                    product_pairs.append(pair)
        if not pns:
            return

        def _exec_update(sql: str, params: tuple) -> None:
            for attempt in range(_SHIPPING_LOG_TX_RETRIES):
                try:
                    _set_shipping_log_lock_wait_timeout(cursor)
                    cursor.execute(sql, params)
                    conn.commit()
                    return
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    if _is_retryable_lock_error(e) and attempt < _SHIPPING_LOG_TX_RETRIES - 1:
                        logger.warning(
                            "picking_log_matched 更新でロック競合 (errno=%s) 再試行 %s/%s",
                            getattr(e, "errno", None),
                            attempt + 1,
                            _SHIPPING_LOG_TX_RETRIES,
                        )
                        _sleep_lock_backoff(attempt)
                        continue
                    logger.warning("picking_log_matched 一括更新失敗: %s", e)
                    return

        chunk = _SHIPPING_LOG_INSERT_CHUNK
        for i in range(0, len(pns), chunk):
            part = pns[i : i + chunk]
            placeholders = ",".join(["%s"] * len(part))
            _exec_update(
                f"""
                UPDATE shipping_items s
                SET s.picking_log_matched = 1
                WHERE s.shipping_no_p IN ({placeholders})
                """,
                tuple(part),
            )
        for i in range(0, len(empty_pc_pns), chunk):
            part = empty_pc_pns[i : i + chunk]
            placeholders = ",".join(["%s"] * len(part))
            _exec_update(
                f"""
                UPDATE shipping_items s
                SET s.picking_log_matched = 1
                WHERE s.shipping_no IN ({placeholders})
                """,
                tuple(part),
            )
        for i in range(0, len(product_pairs), chunk):
            part = product_pairs[i : i + chunk]
            placeholders = ",".join(["(%s, %s)"] * len(part))
            params: list = []
            for pn, pc in part:
                params.extend((pn, pc))
            _exec_update(
                f"""
                UPDATE shipping_items s
                SET s.picking_log_matched = 1
                WHERE (s.shipping_no, s.product_cd) IN ({placeholders})
                """,
                tuple(params),
            )


def _shipping_log_archive_table_exists(cursor) -> bool:
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'shipping_log_archive'
        """
    )
    row = cursor.fetchone()
    val = row[0] if row and not isinstance(row, dict) else (next(iter(row.values())) if row else 0)
    return int(val or 0) > 0


def _prepare_shipping_log_keep_picking_nos(cursor, days: int) -> None:
    """直近ウィンドウの出荷明細が参照する picking_no を一時表に載せる（アーカイブ対象から除外）。"""
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS tmp_shipping_log_keep_picking_nos")
    cursor.execute(
        """
        CREATE TEMPORARY TABLE tmp_shipping_log_keep_picking_nos (
            picking_no VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
            PRIMARY KEY (picking_no)
        )
        """
    )
    cursor.execute(
        f"""
        INSERT IGNORE INTO tmp_shipping_log_keep_picking_nos (picking_no)
        SELECT DISTINCT CONVERT(TRIM(si.shipping_no_p) USING utf8mb4) COLLATE utf8mb4_unicode_ci
        FROM shipping_items si
        WHERE si.shipping_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
          AND si.shipping_no_p IS NOT NULL
          AND TRIM(si.shipping_no_p) != ''
        """
    )
    cursor.execute(
        f"""
        INSERT IGNORE INTO tmp_shipping_log_keep_picking_nos (picking_no)
        SELECT DISTINCT CONVERT(TRIM(si.shipping_no) USING utf8mb4) COLLATE utf8mb4_unicode_ci
        FROM shipping_items si
        WHERE si.shipping_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
          AND si.shipping_no IS NOT NULL
          AND TRIM(si.shipping_no) != ''
        """
    )


def _set_shipping_log_archive_lock_wait_timeout(cursor) -> None:
    cursor.execute(
        f"SET SESSION innodb_lock_wait_timeout = {_SHIPPING_LOG_ARCHIVE_LOCK_WAIT_TIMEOUT_SEC}"
    )


def archive_old_shipping_logs_sync(progress_cb=None) -> dict:
    """保持期間を過ぎた shipping_log を shipping_log_archive へ移動する。

    picking_log_matched は再計算しない（過去の完了フラグを 0 に戻さない）。
    直近ウィンドウの shipping_items が参照する picking_no はホットテーブルに残す。
    ファイル監視との競合を避けるため、小さなチャンク＋短いトランザクション＋再試行する。

    progress_cb(percent: int, message: str, archived: int, total: int) を渡すと進捗通知する。
    """
    days = int(SHIPPING_LOG_RETENTION_DAYS)
    chunk = int(_SHIPPING_LOG_ARCHIVE_CHUNK)
    archived = 0
    total_candidates = 0

    def _notify(percent: int, message: str) -> None:
        if progress_cb is None:
            return
        try:
            progress_cb(int(percent), str(message), int(archived), int(total_candidates))
        except Exception:
            pass

    with _SHIPPING_LOG_THREAD_LOCK:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        lock_held = False
        try:
            if not _shipping_log_archive_table_exists(cursor):
                raise RuntimeError(
                    "shipping_log_archive テーブルが存在しません。"
                    "backend/database/migrations/125_shipping_log_archive.sql を適用してください。"
                )

            _notify(2, "保持対象の picking_no を集計中")
            # 保持対象の集計は GET_LOCK 外で行い、CSV 取込を長くブロックしない
            _prepare_shipping_log_keep_picking_nos(cursor, days)
            conn.commit()

            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM shipping_log sl
                LEFT JOIN tmp_shipping_log_keep_picking_nos k
                  ON k.picking_no = sl.picking_no
                WHERE k.picking_no IS NULL
                  AND (
                    (sl.date IS NOT NULL AND sl.date < DATE_SUB(CURDATE(), INTERVAL {days} DAY))
                    OR (sl.date IS NULL AND sl.created_at < DATE_SUB(NOW(), INTERVAL {days} DAY))
                  )
                """
            )
            row = cursor.fetchone()
            total_candidates = int((row[0] if row and not isinstance(row, dict) else 0) or 0)
            _notify(
                5,
                f"退避対象 {total_candidates} 件を処理開始" if total_candidates else "退避対象なし",
            )
            if total_candidates <= 0:
                _notify(100, "退避対象なし")
                return {"archived": 0, "retention_days": days, "total_candidates": 0}

            last_id = 0
            while True:
                ids: list[int] = []
                moved = False
                for attempt in range(_SHIPPING_LOG_TX_RETRIES):
                    try:
                        if not _acquire_shipping_log_lock(cursor):
                            raise RuntimeError(
                                "shipping_log 同期ロックを取得できませんでした。"
                                "他プロセスの取込完了後に再試行してください。"
                            )
                        lock_held = True
                        _set_shipping_log_archive_lock_wait_timeout(cursor)
                        cursor.execute(
                            f"""
                            SELECT sl.id
                            FROM shipping_log sl
                            LEFT JOIN tmp_shipping_log_keep_picking_nos k
                              ON k.picking_no = sl.picking_no
                            WHERE sl.id > %s
                              AND k.picking_no IS NULL
                              AND (
                                (sl.date IS NOT NULL
                                  AND sl.date < DATE_SUB(CURDATE(), INTERVAL {days} DAY))
                                OR (sl.date IS NULL
                                  AND sl.created_at < DATE_SUB(NOW(), INTERVAL {days} DAY))
                              )
                            ORDER BY sl.id
                            LIMIT {chunk}
                            """,
                            (last_id,),
                        )
                        ids = [int(r[0]) for r in cursor.fetchall() if r and r[0] is not None]
                        if not ids:
                            conn.commit()
                            break

                        placeholders = ",".join(["%s"] * len(ids))
                        cursor.execute(
                            f"""
                            INSERT IGNORE INTO shipping_log_archive (
                                id, project, date, datetime, model_no, person_in_charge,
                                picking_no, product_name, product_code, product_name_2,
                                quantity, shipping_quantity, created_at, updated_at
                            )
                            SELECT
                                id, project, date, datetime, model_no, person_in_charge,
                                picking_no, product_name, product_code, product_name_2,
                                quantity, shipping_quantity, created_at, updated_at
                            FROM shipping_log
                            WHERE id IN ({placeholders})
                            """,
                            ids,
                        )
                        cursor.execute(
                            f"DELETE FROM shipping_log WHERE id IN ({placeholders})",
                            ids,
                        )
                        conn.commit()
                        archived += len(ids)
                        last_id = ids[-1]
                        moved = True
                        if total_candidates > 0:
                            pct = min(99, 5 + int(archived * 94 / total_candidates))
                        else:
                            pct = 99
                        _notify(pct, f"{archived} / {total_candidates} 件を退避中")
                        break
                    except Exception as e:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        if _is_retryable_lock_error(e) and attempt < _SHIPPING_LOG_TX_RETRIES - 1:
                            logger.warning(
                                "shipping_log アーカイブでロック競合 (errno=%s) 再試行 %s/%s（退避済み: %s）",
                                getattr(e, "errno", None),
                                attempt + 1,
                                _SHIPPING_LOG_TX_RETRIES,
                                archived,
                            )
                            _sleep_lock_backoff(attempt)
                            continue
                        raise
                    finally:
                        if lock_held:
                            _release_shipping_log_lock(cursor)
                            lock_held = False

                if not ids:
                    break
                if not moved:
                    raise RuntimeError("shipping_log アーカイブのチャンク処理に失敗しました")
                if _SHIPPING_LOG_ARCHIVE_BATCH_PAUSE_SEC > 0:
                    time.sleep(_SHIPPING_LOG_ARCHIVE_BATCH_PAUSE_SEC)

            logger.info(
                "shipping_log アーカイブ完了: %s 件を shipping_log_archive へ退避（保持日数: %s）",
                archived,
                days,
            )
            _notify(100, f"{archived} 件の退避が完了しました")
            return {
                "archived": archived,
                "retention_days": days,
                "total_candidates": total_candidates,
            }
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(
                "shipping_log アーカイブ失敗（退避済み: %s）: %s",
                archived,
                e,
                exc_info=True,
            )
            raise
        finally:
            try:
                cursor.execute("DROP TEMPORARY TABLE IF EXISTS tmp_shipping_log_keep_picking_nos")
            except Exception:
                pass
            if lock_held:
                _release_shipping_log_lock(cursor)
            cursor.close()
            conn.close()


def execute_full_picking_log_matched_refresh_sync() -> int:
    """shipping_items.picking_log_matched を直近保持期間分だけ再計算。

    出荷日が保持期間より古い行は更新しない（アーカイブ後に完了フラグが 0 へ戻るのを防ぐ）。
    突合せ結果を一時表に載せ、id 範囲ごとに短トランザクションで更新する。
    """
    days = int(SHIPPING_LOG_RETENTION_DAYS)
    with _SHIPPING_LOG_THREAD_LOCK:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        affected = 0
        lock_held = False
        try:
            if not _acquire_shipping_log_lock(cursor):
                raise RuntimeError(
                    "shipping_log 同期ロックを取得できませんでした。他プロセスの取込完了後に再試行してください。"
                )
            lock_held = True
            _set_shipping_log_lock_wait_timeout(cursor)
            cursor.execute("DROP TEMPORARY TABLE IF EXISTS tmp_shipping_matched_picking_nos")
            cursor.execute(
                """
                CREATE TEMPORARY TABLE tmp_shipping_matched_picking_nos (
                    picking_no VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    product_code VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
                    PRIMARY KEY (picking_no, product_code)
                )
                """
            )
            cursor.execute(
                """
                INSERT IGNORE INTO tmp_shipping_matched_picking_nos (picking_no, product_code)
                SELECT DISTINCT TRIM(picking_no), IFNULL(TRIM(product_code), '')
                FROM shipping_log
                WHERE picking_no IS NOT NULL AND TRIM(picking_no) != ''
                """
            )
            conn.commit()

            cursor.execute(
                f"""
                SELECT COALESCE(MIN(id), 0), COALESCE(MAX(id), 0)
                FROM shipping_items
                WHERE shipping_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
                """
            )
            row = cursor.fetchone() or (0, 0)
            min_id, max_id = int(row[0] or 0), int(row[1] or 0)
            if max_id <= 0:
                return 0

            start = min_id
            while start <= max_id:
                end = start + _PICKING_MATCHED_REFRESH_CHUNK - 1
                cursor.execute(
                    f"""
                    UPDATE shipping_items si
                    SET si.picking_log_matched = CASE WHEN EXISTS (
                        SELECT 1 FROM tmp_shipping_matched_picking_nos m
                        WHERE m.picking_no = CONVERT(TRIM(si.shipping_no_p) USING utf8mb4) COLLATE utf8mb4_unicode_ci
                           OR (
                             m.picking_no = CONVERT(TRIM(si.shipping_no) USING utf8mb4) COLLATE utf8mb4_unicode_ci
                             AND (
                               m.product_code = ''
                               OR m.product_code = CONVERT(TRIM(si.product_cd) USING utf8mb4) COLLATE utf8mb4_unicode_ci
                             )
                           )
                    ) THEN 1 ELSE 0 END
                    WHERE si.id BETWEEN %s AND %s
                      AND si.shipping_date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
                      AND si.shipping_no_p IS NOT NULL
                      AND si.shipping_no_p != ''
                    """,
                    (start, end),
                )
                affected += int(cursor.rowcount or 0)
                conn.commit()
                start = end + 1

            logger.info(
                "picking_log_matched 再計算完了（更新行数: %s, id範囲: %s-%s, 出荷日>=%s日以内）",
                affected,
                min_id,
                max_id,
                days,
            )
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error("picking_log_matched 再計算失敗: %s", e, exc_info=True)
            raise
        finally:
            try:
                cursor.execute("DROP TEMPORARY TABLE IF EXISTS tmp_shipping_matched_picking_nos")
            except Exception:
                pass
            if lock_held:
                _release_shipping_log_lock(cursor)
            cursor.close()
            conn.close()
        return affected


def run_picking_sync_and_refresh_matched(filepath: str, filename: str) -> None:
    """
    PickingLog.csv / Partslog.csv 変更時：CSV を shipping_log に取り込む。

    picking_log_matched は sync 内で当該 picking_no（shipping_no_p または shipping_no）分だけ更新する。
    全件 UPDATE は shipping_items を長時間ロックし印刷記録保存と競合するため行わない。
    全件整合が必要な場合は POST /items/refresh-picking-log-matched を使う。
    """
    svc = PickingLogService()
    svc.sync(filepath, filename, raise_on_error=False)


def sync_material_csv_files_from_watch_folder() -> dict:
    """
    .env で解決した材料受入 CSV（get_material_receiving_csv_entries）をすべて DB に取り込む。
    手動「データ読取」API と同一ロジック。戻りはフロントの fileResults 形式に合わせる。
    """
    import os

    from app.services.file_watcher.enabled_config import is_file_enabled

    entries = list(settings.get_material_receiving_csv_entries())
    if not entries:
        return {
            "success": False,
            "message": (
                "材料受入 CSV のパスが解決できません。.env に MATERIAL_RECEIVING_CSV_PATHS（フルパス・カンマ区切り）、"
                "または MATERIAL_RECEIVING_WATCH_BASE_PATH / FILE_WATCH_BASE_PATH とファイル名を設定してください。"
            ),
            "data": {"fileResults": [], "totalProcessed": 0},
        }

    svc = MaterialService()
    file_results: list = []
    total_processed = 0

    for fp, fn in entries:
        if not is_file_enabled(fn):
            file_results.append(
                {
                    "fileName": fn,
                    "path": fp,
                    "success": True,
                    "processedCount": 0,
                    "error": None,
                    "skipped": True,
                }
            )
            continue
        if not os.path.isfile(fp):
            file_results.append(
                {
                    "fileName": fn,
                    "path": fp,
                    "success": False,
                    "processedCount": 0,
                    "error": "ファイルが見つかりません",
                }
            )
            continue
        try:
            r = svc.sync(fp, fn) or {}
            ok = r.get("success", False)
            n = int(r.get("processedCount") or 0)
            err = r.get("error")
            if ok:
                total_processed += n
            file_results.append(
                {
                    "fileName": fn,
                    "path": fp,
                    "success": bool(ok),
                    "processedCount": n,
                    "error": err,
                }
            )
        except Exception as e:
            logger.exception("材料 CSV 同期エラー %s", fn)
            file_results.append(
                {
                    "fileName": fn,
                    "path": fp,
                    "success": False,
                    "processedCount": 0,
                    "error": str(e),
                }
            )

    any_fail = any(not fr.get("success") for fr in file_results if not fr.get("skipped"))
    return {
        "success": not any_fail,
        "message": "材料ログ CSV の取込が完了しました" if not any_fail else "一部ファイルの取込に失敗しました",
        "data": {"fileResults": file_results, "totalProcessed": total_processed},
    }


def sync_part_csv_files_from_watch_folder() -> dict:
    """部品受入 CSV を part_logs に取り込む（手動「データ読取」API 用）。"""
    import os

    from app.services.file_watcher.enabled_config import is_file_enabled

    entries = list(settings.get_part_receiving_csv_entries())
    if not entries:
        return {
            "success": False,
            "message": (
                "部品受入 CSV のパスが解決できません。.env に PART_RECEIVING_CSV_PATHS（フルパス・カンマ区切り）、"
                "または PART_RECEIVING_WATCH_BASE_PATH / FILE_WATCH_BASE_PATH とファイル名を設定してください。"
            ),
            "data": {"fileResults": [], "totalProcessed": 0},
        }

    svc = PartService()
    file_results: list = []
    total_processed = 0

    for fp, fn in entries:
        if not is_file_enabled(fn):
            file_results.append(
                {
                    "fileName": fn,
                    "path": fp,
                    "success": True,
                    "processedCount": 0,
                    "error": None,
                    "skipped": True,
                }
            )
            continue
        if not os.path.isfile(fp):
            file_results.append(
                {
                    "fileName": fn,
                    "path": fp,
                    "success": False,
                    "processedCount": 0,
                    "error": "ファイルが見つかりません",
                }
            )
            continue
        try:
            r = svc.sync(fp, fn) or {}
            ok = r.get("success", False)
            n = int(r.get("processedCount") or 0)
            err = r.get("error")
            if ok:
                total_processed += n
            file_results.append(
                {
                    "fileName": fn,
                    "path": fp,
                    "success": bool(ok),
                    "processedCount": n,
                    "error": err,
                }
            )
        except Exception as e:
            logger.exception("部品 CSV 同期エラー %s", fn)
            file_results.append(
                {
                    "fileName": fn,
                    "path": fp,
                    "success": False,
                    "processedCount": 0,
                    "error": str(e),
                }
            )

    any_fail = any(not fr.get("success") for fr in file_results if not fr.get("skipped"))
    return {
        "success": not any_fail,
        "message": "部品ログ CSV の取込が完了しました" if not any_fail else "一部ファイルの取込に失敗しました",
        "data": {"fileResults": file_results, "totalProcessed": total_processed},
    }

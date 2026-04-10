# coding: utf-8
"""在庫取引・材料ログ同期サービス（MySQL へ同期）"""
import logging
import random
import mysql.connector
from app.core.config import settings
from app.services.file_watcher.utils import read_csv_content, normalize_date_str, normalize_time_str

logger = logging.getLogger(__name__)

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

# ピッキングログファイル → shipping_log（fileWatcherService.js と同等）
PICKING_FILES = [
    "PickingLog.csv",
]

# 材料切断ログ（MATERIAL_CUTTING_CSV_PATH / materialCutting.csv）→ material_cutting_logs
MATERIAL_CUTTING_CSV_BASENAME = "materialCutting.csv"


def get_db_connection():
    """プロジェクト設定の同期用 MySQL 接続（ファイル監視用）"""
    return mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )


# ---------- StockService: 全量镜像同步 ----------


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
    """库存交易 CSV → stock_transaction_logs（按 source_file 删除旧数据后插入）"""

    def sync(self, filepath, filename):
        rows = read_csv_content(filepath)
        if not rows or len(rows) < 2:
            return
        data_rows = rows[1:]
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM stock_transaction_logs WHERE source_file = %s",
                (filename,),
            )
            deleted = cursor.rowcount
            sql = """
                INSERT INTO stock_transaction_logs
                (stock_type, target_cd, location_cd, process_cd, transaction_type,
                 quantity, unit, transaction_time, order_no, machine_cd, remarks, source_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = []
            for row in data_rows:
                vals = self._parse_row(filename, row)
                if vals:
                    values.append(vals)
            if values:
                cursor.executemany(sql, values)
                inserted = cursor.rowcount
            else:
                inserted = 0
            conn.commit()
            skipped = len(data_rows) - len(values)
            logger.info("%s 処理完了: %s件処理, %s件スキップ", filename, inserted, skipped)
        except Exception as e:
            conn.rollback()
            logger.error("❌ [Stock] エラー %s: %s", filename, e)
        finally:
            cursor.close()
            conn.close()

    def _parse_row(self, filename, cols):
        try:
            stock_type, unit, doc_no, machine = "仕掛品", "本", None, None
            if "PlatingRecord" in filename:
                if len(cols) < 9:
                    return None
                date_s, time_s, doc_no, target = cols[1], cols[2], cols[3], cols[5]
                qty = float(cols[7] or 0) * float(cols[8] or 0)
                loc, proc, trans = "工程中間在庫", "KT05", "実績"
            elif "Stock" in filename:
                if len(cols) < 9:
                    return None
                trans, date_s, time_s = cols[0], cols[1], cols[2]
                doc_no, target = cols[4], cols[5]
                qty = float(cols[7] or 0) * float(cols[8] or 0)
                stock_type, loc, proc = "製品", "製品倉庫", "KT13"
            elif "Molding" in filename or "Welding" in filename:
                if len(cols) < 9:
                    return None
                date_s, time_s = cols[1], cols[2]
                doc_no, machine, target = cols[4], cols[5], cols[6]
                qty = float(cols[8] or 0)
                trans, loc = "実績", "工程中間在庫"
                proc = "KT04" if "Molding" in filename else "KT07"
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
            for d in final_list:
                if d.get("log_date") == "":
                    d["log_date"] = "1970-01-01"
                if d.get("manufacture_date") == "":
                    d["manufacture_date"] = None
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
                m_no = row[5]
                try:
                    if m_no and "." in m_no:
                        m_no = str(float(m_no)).split(".")[0]
                except Exception:
                    pass
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
                        "manufacture_no": row[5],
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
                        "manufacture_no": row[6] if len(row) > 6 else "",
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
                m_no = col6[0:8] if len(col6) >= 8 else ""
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


class PickingLogService:
    """PickingLog.csv → shipping_log（重複は (picking_no, product_code, date) で ON DUPLICATE KEY UPDATE）。続けて picking_tasks を更新。"""

    def sync(self, filepath, filename):
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
        for r in data_rows:
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
            if rec["picking_no"] or rec["product_code"]:
                records.append(rec)
        if not records:
            logger.warning("⚠️ [PickingLog] %s 有効レコードなし", filename)
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
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor(dictionary=True)
        try:
            # 既存一括チェック（DB に既にあるものはスキップして新規のみ INSERT、ただし JS は ON DUPLICATE で常に挿入/更新）
            # ここでは JS と同様に全件 INSERT ON DUPLICATE KEY UPDATE で投入
            insert_sql = """
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
            inserted, updated = 0, 0
            records_to_sync_pt = []
            for rec in unique_records:
                if not rec["picking_no"] and not rec["product_code"]:
                    continue
                vals = (
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
                try:
                    cursor.execute(insert_sql, vals)
                    if cursor.rowcount == 1:
                        inserted += 1
                        records_to_sync_pt.append(rec)
                    elif cursor.rowcount == 2:
                        updated += 1
                        records_to_sync_pt.append(rec)
                except Exception as e:
                    logger.warning("shipping_log 挿入/更新失敗: %s", e)
            conn.commit()
            logger.info("%s 処理完了: shipping_log 新規 %s 件, 更新 %s 件", filename, inserted, updated)
            if records_to_sync_pt:
                self._sync_to_picking_tasks(cursor, records_to_sync_pt)
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("❌ [PickingLog] エラー %s: %s", filename, e, exc_info=True)
        finally:
            cursor.close()
            conn.close()

    def _sync_to_picking_tasks(self, cursor, records):
        """挿入/更新したレコードで picking_tasks を更新（shipping_no_p = picking_no）。テーブルが無い場合はスキップ。"""
        if not records:
            return
        # picking_no があるもののみ
        valid = [r for r in records if r.get("picking_no")]
        if not valid:
            return
        update_sql = """
            UPDATE picking_tasks
            SET start_time = %s, picker_id = %s, product_name = %s, product_cd = %s,
                picked_quantity = %s, picked_no = %s, status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE shipping_no_p = %s
        """
        try:
            for rec in valid:
                cursor.execute(
                    update_sql,
                    (
                        rec.get("datetime"),
                        rec.get("person_in_charge", ""),
                        rec.get("product_name", ""),
                        rec.get("product_code", ""),
                        rec.get("quantity", 0),
                        rec.get("picking_no", ""),
                        rec.get("picking_no", ""),
                    ),
                )
        except Exception as e:
            # picking_tasks が存在しない等
            logger.debug("picking_tasks 更新スキップ（テーブル未作成の可能性）: %s", e)


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

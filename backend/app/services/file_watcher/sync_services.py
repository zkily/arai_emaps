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

# 材料ログファイル → material_logs
MATERIAL_FILES = [
    "Material_Maruiti.csv",
    "Material_Nagoya.csv",
    "Material_JFE.csv",
    "Material_Okajima.csv",
]


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


class MaterialService:
    """材料 CSV → material_logs（解析、补全、按业务键删除后插入）"""

    def sync(self, filepath, filename):
        rows = read_csv_content(filepath, encoding_list=["shift_jis", "cp932"])
        if not rows or len(rows) < 2:
            return
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
                return
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
                        "DELETE FROM material_logs WHERE (log_date, log_time, manufacture_no) IN ("
                        + placeholders
                        + ")",
                        flat,
                    )
                    deleted_count += cursor.rowcount
            else:
                target_item = parsed_data[0]["item"]
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
            else:
                inserted_count = 0
            conn.commit()
            skipped = len(data_rows) - inserted_count
            logger.info("%s 処理完了: %s件処理, %s件スキップ", filename, inserted_count, skipped)
        except Exception as e:
            conn.rollback()
            logger.error("❌ [Material] エラー %s: %s", filename, e, exc_info=True)
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
                        "supplier": "川崎INOAC",
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

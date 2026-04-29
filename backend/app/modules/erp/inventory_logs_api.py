"""
在庫棚卸ログ（inventory_logs）API

原始ロジックは root の `inventory.js` に準拠。
"""

from __future__ import annotations

import asyncio
import csv
import os
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User


router = APIRouter(prefix="/inventory-logs", tags=["Inventory Logs"])


# ネットワーク共有（inventory.js 参照）
BASE_PATH = r"\\192.168.1.200\社内共有\02_生産管理部\Data\BT-data\受信"

INVENTORY_LOG_CSV = "InventoryLog.csv"
PARTS_LOG_CSV = "Partslog.csv"
MATERIAL_LOG_CSV = "Materiallog.csv"


CREATE_TABLE_SQL = r"""
CREATE TABLE `inventory_logs`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '棚卸ログID',
  `item` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '項目（材料棚卸/部品棚卸/製品棚卸）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品/材料/部品CD',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品/材料/部品名',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '工程CD',
  `log_date` date NOT NULL COMMENT '日付',
  `log_time` time NOT NULL COMMENT '時間',
  `hd_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'HDNo',
  `pack_qty` int NULL DEFAULT NULL COMMENT '入数（箱/パック単位）',
  `case_qty` int NULL DEFAULT NULL COMMENT 'ケース数',
  `quantity` int NOT NULL COMMENT '数量',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '担当者CDなど',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_log_date`(`log_date` ASC) USING BTREE,
  INDEX `idx_process_date`(`process_cd` ASC, `log_date` ASC) USING BTREE,
  INDEX `idx_item_date_time`(`item` ASC, `log_date` ASC, `log_time` ASC) USING BTREE,
  INDEX `idx_dup_key`(`item` ASC, `product_cd` ASC, `product_name` ASC, `log_date` ASC, `log_time` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5866 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '棚卸ログ' ROW_FORMAT = DYNAMIC
"""

CREATE_TABLE_IF_NOT_EXISTS_SQL = CREATE_TABLE_SQL.replace(
    "CREATE TABLE `inventory_logs`",
    "CREATE TABLE IF NOT EXISTS `inventory_logs`",
)


DROP_TABLE_SQL = r"DROP TABLE IF EXISTS `inventory_logs`"

# inventory_logs 列は utf8mb4_0900_ai_ci、processes / users は多くが utf8mb4_unicode_ci。
# COALESCE の引数同士で照合順序が混在すると MySQL がエラーになるため、常に unicode_ci に揃える。
SQL_EXPR_PROCESS_NAME = (
    "COALESCE(p.process_name COLLATE utf8mb4_unicode_ci, i.process_cd COLLATE utf8mb4_unicode_ci)"
)
SQL_EXPR_WORKER_NAME = (
    "COALESCE(u.full_name COLLATE utf8mb4_unicode_ci, i.remarks COLLATE utf8mb4_unicode_ci)"
)


INSERT_SQL = r"""
INSERT INTO inventory_logs (
  item, product_cd, product_name, process_cd, log_date, log_time,
  hd_no, pack_qty, case_qty, quantity, remarks
) VALUES (
  :item, :product_cd, :product_name, :process_cd, :log_date, :log_time,
  :hd_no, :pack_qty, :case_qty, :quantity, :remarks
);
"""


SELECT_BY_ID_SQL = f"""
SELECT
  i.id,
  i.item,
  i.product_cd,
  i.product_name,
  i.process_cd,
  {SQL_EXPR_PROCESS_NAME} as process_name,
  i.log_date,
  i.log_time,
  i.hd_no,
  i.pack_qty,
  i.case_qty,
  i.quantity,
  i.remarks,
  {SQL_EXPR_WORKER_NAME} as worker_name,
  i.created_at,
  i.updated_at
FROM inventory_logs i
LEFT JOIN processes p ON i.process_cd COLLATE utf8mb4_unicode_ci = p.process_cd COLLATE utf8mb4_unicode_ci
LEFT JOIN users u ON i.remarks COLLATE utf8mb4_unicode_ci = u.username COLLATE utf8mb4_unicode_ci
WHERE i.id = :id
"""


def _mysql_errno_from_sqlalchemy(exc: BaseException) -> Optional[int]:
    """pymysql / aiomysql が orig に (errno, message) を載せる想定。"""
    o = getattr(exc, "orig", None)
    if o is None:
        return None
    args = getattr(o, "args", None)
    if isinstance(args, tuple) and len(args) >= 1:
        try:
            return int(args[0])
        except (TypeError, ValueError):
            return None
    return None


def _is_missing_inventory_logs_table(exc: BaseException) -> bool:
    if _mysql_errno_from_sqlalchemy(exc) == 1146:
        return True
    msg = str(exc).lower()
    return "inventory_logs" in msg and (
        "doesn't exist" in msg
        or "does not exist" in msg
        or "doesnt exist" in msg
        or "unknown table" in msg
        or "不存在" in str(exc)
    )


def _sql_eq_col_bind_unicode_ci(column_sql: str, bind_name: str) -> str:
    """inventory_logs が utf8mb4_0900_ai_ci のとき、バインド値が接続既定 collation と異なると '=' でエラーになるため揃える。"""
    return (
        f"{column_sql} COLLATE utf8mb4_unicode_ci = "
        f"CAST(:{bind_name} AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci"
    )


def _sql_like_col_bind_unicode_ci(column_sql: str, bind_name: str) -> str:
    return (
        f"{column_sql} COLLATE utf8mb4_unicode_ci LIKE "
        f"CAST(:{bind_name} AS CHAR CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci"
    )


def _serialize_log_mapping_row(row: Any) -> Dict[str, Any]:
    """生の Result row を JSON 応答向けに変換（time・Decimal 等）。"""
    d = dict(row)
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat(timespec="seconds")
        elif isinstance(v, date):
            out[k] = v.isoformat()
        elif isinstance(v, time):
            out[k] = v.isoformat(timespec="seconds")
        elif isinstance(v, Decimal):
            out[k] = int(v) if v == v.to_integral_value() else float(v)
        else:
            out[k] = v
    return out


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    try:
        # 桁区切りのカンマ（例: "1,000"）を除去してパース
        s = s.replace(",", "")
        return int(float(s))
    except (ValueError, TypeError):
        return default


async def ensure_table_exists(db: AsyncSession) -> None:
    # 既存が無いケースで GET/POST/DELETE が落ちないようにする
    await db.execute(text(CREATE_TABLE_IF_NOT_EXISTS_SQL))
    await db.commit()


async def drop_and_recreate_table(db: AsyncSession) -> None:
    await db.execute(text(DROP_TABLE_SQL))
    # `CREATE TABLE IF NOT EXISTS` ではなく、ユーザー指定の通り DROP/CREATE
    await db.execute(text(CREATE_TABLE_SQL))
    await db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    await db.commit()


def _read_csv_rows_sync(csv_path: str) -> List[Dict[str, str]]:
    if not os.path.exists(csv_path):
        return []

    # inventory.js と同様に shift_jis を優先。環境により cp932 が必要なことがあるためフォールバック。
    for enc in ("shift_jis", "cp932"):
        try:
            with open(csv_path, "r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return [row for row in reader]
        except UnicodeDecodeError:
            continue

    # 最後まで読めない場合は明示エラー
    raise UnicodeDecodeError("csv", b"", 0, 1, "Unable to decode CSV with shift_jis/cp932")


async def process_csv_file(
    db: AsyncSession,
    csv_path: str,
    file_name: str,
    seen_keys: set[Tuple[str, str, str, str, str]],
    product_unit_cache: dict[str, Optional[int]],
) -> Dict[str, Any]:
    # 戻り値は inventory.js と UI の期待構造に合わせる
    if not os.path.exists(csv_path):
        return {
            "totalProcessed": 0,
            "newRecords": 0,
            "duplicates": 0,
            "errors": 0,
            "fileExists": False,
        }

    rows = await asyncio.to_thread(_read_csv_rows_sync, csv_path)
    total_processed = len(rows)

    duplicates = 0
    new_records = 0
    errors = 0

    for row in rows:
        try:
            original_process_cd = (row.get("工程CD") or "").strip()
            padded_process_cd = original_process_cd.zfill(2)
            process_cd = f"KT{padded_process_cd}"

            item = (row.get("項目") or "").strip()
            product_cd = (row.get("製品CD") or "").strip()
            product_name = (row.get("製品名") or "").strip()
            log_date = (row.get("日付") or "").strip()
            log_time = (row.get("時間") or "").strip()
            hd_no_raw = (row.get("HDNo") or "").strip()
            hd_no = hd_no_raw if hd_no_raw else None
            remarks_raw = (row.get("担当者CD") or "").strip()
            remarks = remarks_raw if remarks_raw else None

            raw_quantity = _safe_int(row.get("数量"), default=0)

            case_qty: Optional[int] = None
            pack_qty: Optional[int] = None
            quantity: int

            if original_process_cd == "13":
                case_qty = raw_quantity

                if product_cd in product_unit_cache:
                    unit_per_box = product_unit_cache[product_cd]
                else:
                    pr = await db.execute(
                        text("SELECT unit_per_box FROM products WHERE product_cd = :product_cd"),
                        {"product_cd": product_cd},
                    )
                    unit_row = pr.first()
                    unit_per_box = int(unit_row[0]) if unit_row and unit_row[0] is not None else None
                    product_unit_cache[product_cd] = unit_per_box

                if unit_per_box:
                    pack_qty = unit_per_box
                    quantity = case_qty * pack_qty
                else:
                    # JS のデフォルト値: 1
                    pack_qty = 1
                    quantity = case_qty
            else:
                quantity = raw_quantity

            # 必須フィールド検証
            if not item or not product_cd or not product_name or not log_date:
                errors += 1
                continue

            key = (item, product_cd, product_name, log_date, log_time)
            if key in seen_keys:
                duplicates += 1
                continue

            try:
                await db.execute(
                    text(INSERT_SQL),
                    {
                        "item": item,
                        "product_cd": product_cd,
                        "product_name": product_name,
                        "process_cd": process_cd,
                        "log_date": log_date,
                        "log_time": log_time,
                        "hd_no": hd_no,
                        "pack_qty": pack_qty,
                        "case_qty": case_qty,
                        "quantity": quantity,
                        "remarks": remarks,
                    },
                )
                await db.commit()
                new_records += 1
                seen_keys.add(key)
            except SQLAlchemyError:
                errors += 1
                await db.rollback()
                continue
        except Exception:
            errors += 1
            await db.rollback()
            continue

    return {
        "totalProcessed": total_processed,
        "newRecords": new_records,
        "duplicates": duplicates,
        "errors": errors,
        "fileExists": True,
        "file": file_name,
    }


class InventoryLogCreate(BaseModel):
    item: str
    product_cd: str
    product_name: str
    process_cd: str
    log_date: str
    log_time: str
    hd_no: Optional[str] = None
    pack_qty: Optional[int] = None
    case_qty: Optional[int] = None
    quantity: int
    remarks: Optional[str] = None
    # process_name は UI が送ってくることがあるが、DBには無いので無視する
    process_name: Optional[str] = None


@router.get("")
async def get_inventory_logs(
    item: Optional[str] = Query(None),
    keyword: str = Query(""),
    dateRange: Optional[List[str]] = Query(None),
    monthPicker: Optional[str] = Query(None),
    stageType: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=500),
    sortBy: str = Query("log_date"),
    sortOrder: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    if item:
        conditions.append(_sql_eq_col_bind_unicode_ci("i.item", "item"))
        params["item"] = item

    if keyword:
        conditions.append(
            "("
            + _sql_like_col_bind_unicode_ci("i.product_cd", "kw")
            + " OR "
            + _sql_like_col_bind_unicode_ci("i.product_name", "kw")
            + ")"
        )
        params["kw"] = f"%{keyword}%"

    if dateRange and len(dateRange) == 2 and all(dateRange):
        conditions.append("i.log_date BETWEEN :date_a AND :date_b")
        params["date_a"] = dateRange[0]
        params["date_b"] = dateRange[1]

    if monthPicker:
        # YYYY-MM を想定
        month = monthPicker[:7]
        year = int(month[:4])
        mon = int(month[5:7])
        next_month = datetime(year + 1, 1, 1) if mon == 12 else datetime(year, mon + 1, 1)
        month_start = datetime(year, mon, 1).strftime("%Y-%m-%d")
        month_end = next_month.strftime("%Y-%m-%d")
        conditions.append("i.log_date >= :month_start AND i.log_date < :month_end")
        params["month_start"] = month_start
        params["month_end"] = month_end

    if stageType and stageType != "all":
        stage_type_map = {
            "cutting": "KT01",
            "surface": "KT02",
            "sw": "KT03",
            "forming": "KT04",
            "plating": "KT05",
            "welding": "KT07",
            "inspection": "KT09",
            "warehouse": "KT13",
            "outsource_plating": "KT06",
            "outsource_welding": "KT08",
            "pre_welding_inspection": "KT11",
            "pre_outsource_inspection": "KT10",
            "pre_outsource_delivery": "KT10",
            "part_process": "KT18",  # 部品棚卸・部品工程（部品倉庫）
        }
        process_cd = stage_type_map.get(stageType)
        if process_cd:
            conditions.append(_sql_eq_col_bind_unicode_ci("i.process_cd", "stage_process_cd"))
            params["stage_process_cd"] = process_cd

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sort_field_map = {
        "product_name": "i.product_name",
        "product_cd": "i.product_cd",
        "log_date": "i.log_date",
        "quantity": "i.quantity",
        "process_name": SQL_EXPR_PROCESS_NAME,
        "created_at": "i.created_at",
        "updated_at": "i.updated_at",
    }
    valid_sort_by = sort_field_map.get(sortBy, "i.log_date")
    valid_sort_order = "ASC" if sortOrder.lower() == "asc" else "DESC"

    try:
        count_sql = f"SELECT COUNT(*) as total FROM inventory_logs i {where_clause}"
        count_res = await db.execute(text(count_sql), params)
        count_row = count_res.first()
        total = count_row[0] if count_row else 0

        data_sql = f"""
          SELECT
            i.id,
            i.item,
            i.product_cd,
            i.product_name,
            i.process_cd,
            {SQL_EXPR_PROCESS_NAME} as process_name,
            i.log_date,
            i.log_time,
            i.hd_no,
            i.pack_qty,
            i.case_qty,
            i.quantity,
            i.remarks,
            {SQL_EXPR_WORKER_NAME} as worker_name,
            i.created_at,
            i.updated_at
          FROM inventory_logs i
          LEFT JOIN processes p ON i.process_cd COLLATE utf8mb4_unicode_ci = p.process_cd COLLATE utf8mb4_unicode_ci
          LEFT JOIN users u ON i.remarks COLLATE utf8mb4_unicode_ci = u.username COLLATE utf8mb4_unicode_ci
          {where_clause}
          ORDER BY {valid_sort_by} {valid_sort_order}, i.id DESC
          LIMIT :limit OFFSET :offset
        """
        params_with_page = {**params, "limit": pageSize, "offset": (page - 1) * pageSize}
        list_res = await db.execute(text(data_sql), params_with_page)
        rows = [_serialize_log_mapping_row(r) for r in list_res.mappings().all()]

        total_quantity_sql = f"""
          SELECT COALESCE(SUM(i.quantity), 0) as totalQuantity
          FROM inventory_logs i
          {where_clause}
        """
        total_qty_res = await db.execute(text(total_quantity_sql), params)
        total_qty_row = total_qty_res.first()
        total_quantity = total_qty_row[0] if total_qty_row else 0
    except SQLAlchemyError as e:
        # execute 失敗後はセッションが中途半端なため rollback しないと get_db の commit が落ちて 500 になる
        await db.rollback()
        if _is_missing_inventory_logs_table(e):
            return {
                "success": True,
                "message": "データ取得成功",
                "data": {"list": [], "total": 0, "totalQuantity": 0},
            }
        raise

    return {
        "success": True,
        "message": "データ取得成功",
        "data": {
            "list": rows or [],
            "total": int(total or 0),
            "totalQuantity": int(total_quantity or 0),
        },
    }


@router.get("/recent")
async def get_recent_inventory_logs(
    limit: int = Query(50, ge=1, le=500),
    hd_no: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    conditions: List[str] = []
    params: Dict[str, Any] = {}
    if hd_no:
        conditions.append(_sql_eq_col_bind_unicode_ci("i.hd_no", "hd_no"))
        params["hd_no"] = hd_no

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
      SELECT
        i.id,
        i.item,
        i.product_cd,
        i.product_name,
        i.process_cd,
        {SQL_EXPR_PROCESS_NAME} as process_name,
        i.log_date,
        i.log_time,
        i.hd_no,
        i.pack_qty,
        i.case_qty,
        i.quantity,
        i.remarks,
        {SQL_EXPR_WORKER_NAME} as worker_name,
        i.created_at,
        i.updated_at
      FROM inventory_logs i
      LEFT JOIN processes p ON i.process_cd COLLATE utf8mb4_unicode_ci = p.process_cd COLLATE utf8mb4_unicode_ci
      LEFT JOIN users u ON i.remarks COLLATE utf8mb4_unicode_ci = u.username COLLATE utf8mb4_unicode_ci
      {where_clause}
      ORDER BY i.updated_at DESC, i.id DESC
      LIMIT :limit
    """
    params["limit"] = limit
    try:
        res = await db.execute(text(sql), params)
        rows = [_serialize_log_mapping_row(r) for r in res.mappings().all()]
        return {"success": True, "message": "recent ok", "data": rows or []}
    except SQLAlchemyError as e:
        await db.rollback()
        if _is_missing_inventory_logs_table(e):
            return {"success": True, "message": "recent ok", "data": []}
        raise


@router.post("")
async def create_inventory_log(
    payload: InventoryLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    process_cd = payload.process_cd
    if not process_cd.startswith("KT"):
        process_cd = f"KT{process_cd.zfill(2)}"

    if not payload.item or not payload.product_cd or not payload.product_name or not payload.process_cd:
        raise HTTPException(status_code=400, detail="必須フィールドが不足しています")
    if not payload.log_date or not payload.log_time or payload.quantity is None:
        raise HTTPException(status_code=400, detail="必須フィールドが不足しています")

    try:
        insert_res = await db.execute(
            text(INSERT_SQL),
            {
                "item": payload.item,
                "product_cd": payload.product_cd,
                "product_name": payload.product_name,
                "process_cd": process_cd,
                "log_date": payload.log_date,
                "log_time": payload.log_time,
                "hd_no": payload.hd_no,
                "pack_qty": payload.pack_qty,
                "case_qty": payload.case_qty,
                "quantity": payload.quantity,
                "remarks": payload.remarks,
            },
        )
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    new_id = getattr(insert_res, "lastrowid", None)
    if not new_id:
        # fallback（driverによっては lastrowid が取れない場合がある）
        id_res = await db.execute(text("SELECT LAST_INSERT_ID() as id"))
        new_id = id_res.first()[0]

    rec_res = await db.execute(text(SELECT_BY_ID_SQL), {"id": new_id})
    rec = rec_res.mappings().first()
    if not rec:
        raise HTTPException(status_code=500, detail="挿入直後の取得に失敗しました")

    return {"success": True, "message": "库存记录创建成功", "data": _serialize_log_mapping_row(rec)}


@router.delete("/{id}")
async def delete_inventory_log(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    try:
        res = await db.execute(text("DELETE FROM inventory_logs WHERE id = :id"), {"id": id})
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # SQLAlchemy の rowcount は方言依存のため、簡易的に判定する
    deleted = getattr(res, "rowcount", None)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="指定されたデータが見つかりません")

    return {"success": True, "message": "データを削除しました"}


@router.post("/import")
async def import_inventory_logs_from_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    # DDL はユーザー指定通り、常に DROP/CREATE する
    await drop_and_recreate_table(db)

    seen_keys: set[Tuple[str, str, str, str, str]] = set()
    product_unit_cache: dict[str, Optional[int]] = {}

    async def run_one(csv_file: str, label: str):
        csv_path = os.path.join(BASE_PATH, csv_file)
        return await process_csv_file(
            db=db,
            csv_path=csv_path,
            file_name=label,
            seen_keys=seen_keys,
            product_unit_cache=product_unit_cache,
        )

    # 同一 AsyncSession を共有しているため、ここでは逐次実行にする（重複カウントも安定）
    inventory_result = await run_one(INVENTORY_LOG_CSV, "InventoryLog.csv")
    parts_result = await run_one(PARTS_LOG_CSV, "Partslog.csv")
    material_result = await run_one(MATERIAL_LOG_CSV, "Materiallog.csv")

    total_processed = (
        int(inventory_result["totalProcessed"])
        + int(parts_result["totalProcessed"])
        + int(material_result["totalProcessed"])
    )
    total_new_records = (
        int(inventory_result["newRecords"]) + int(parts_result["newRecords"]) + int(material_result["newRecords"])
    )
    total_duplicates = (
        int(inventory_result["duplicates"])
        + int(parts_result["duplicates"])
        + int(material_result["duplicates"])
    )
    total_errors = int(inventory_result["errors"]) + int(parts_result["errors"]) + int(material_result["errors"])

    missing_files: List[str] = []
    if not inventory_result["fileExists"]:
        missing_files.append("InventoryLog.csv")
    if not parts_result["fileExists"]:
        missing_files.append("Partslog.csv")
    if not material_result["fileExists"]:
        missing_files.append("Materiallog.csv")

    response_message = (
        f"CSVデータの取込が完了しました（注意: {', '.join(missing_files)} が見つかりませんでした）"
        if missing_files
        else "CSVデータの取込が完了しました"
    )

    return {
        "success": True,
        "message": response_message,
        "data": {
            "totalProcessed": total_processed,
            "newRecords": total_new_records,
            "duplicates": total_duplicates,
            "errors": total_errors,
            "summary": {
                "totalProcessed": total_processed,
                "newRecords": total_new_records,
                "duplicates": total_duplicates,
                "skipped": total_errors,
            },
            "fileDetails": {
                "inventoryLog": {
                    "file": INVENTORY_LOG_CSV,
                    "processed": inventory_result["totalProcessed"],
                    "newRecords": inventory_result["newRecords"],
                    "duplicates": inventory_result["duplicates"],
                    "errors": inventory_result["errors"],
                    "exists": inventory_result["fileExists"],
                },
                "partsLog": {
                    "file": PARTS_LOG_CSV,
                    "processed": parts_result["totalProcessed"],
                    "newRecords": parts_result["newRecords"],
                    "duplicates": parts_result["duplicates"],
                    "errors": parts_result["errors"],
                    "exists": parts_result["fileExists"],
                },
                "materialLog": {
                    "file": MATERIAL_LOG_CSV,
                    "processed": material_result["totalProcessed"],
                    "newRecords": material_result["newRecords"],
                    "duplicates": material_result["duplicates"],
                    "errors": material_result["errors"],
                    "exists": material_result["fileExists"],
                },
            },
        },
    }


"""
ピッキングCSVエクスポート API
POST /export/export-picking-csv: shipping_items（出荷日≥当日）を picking_list に同期し、CSV 用データを返す。
CSV は既定で社内共有フォルダに PickingMaster.csv として出力する。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from typing import Optional
import csv
import io
import os

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db

router = APIRouter()

# 既定の出力先（社内共有フォルダ）。環境変数 PICKING_CSV_OUTPUT_DIR で上書き可
_DEFAULT_PICKING_CSV_DIR = "//192.168.1.200/社内共有/02_生産管理部/Data/BT-data/送信"
PICKING_CSV_OUTPUT_DIR = os.environ.get("PICKING_CSV_OUTPUT_DIR", _DEFAULT_PICKING_CSV_DIR)
PICKING_CSV_FILENAME = "PickingMaster.csv"


def _escape_csv_cell(value) -> str:
    if value is None:
        return ""
    s = str(value)
    if any(c in s for c in '",\r\n'):
        return '"' + s.replace('"', '""') + '"'
    return s


@router.post("/export-picking-csv")
async def export_picking_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    出荷日が当日以降の shipping_items を picking_list に同期し、
    picking_list ベースで CSV 用データを取得。オプションでファイル出力。
    リクエスト body は不要。データ範囲は DB の CURDATE() で決まる。
    """
    try:
        # 1) picking_list が無ければ作成
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS picking_list (
                id INT NOT NULL AUTO_INCREMENT,
                shipping_no_p VARCHAR(50) NOT NULL,
                shipping_no VARCHAR(50) NOT NULL,
                product_cd VARCHAR(50) NOT NULL,
                product_name VARCHAR(100) NULL,
                confirmed_boxes INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uk_shipping_product (shipping_no_p, product_cd),
                KEY idx_shipping_no (shipping_no),
                KEY idx_product_cd (product_cd)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        await db.commit()

        # 2) 出荷日≥当日・キー項目非 null の shipping_items を取得
        sel = text("""
            SELECT shipping_no_p, shipping_no, product_cd, product_name, confirmed_boxes
            FROM shipping_items
            WHERE shipping_no_p IS NOT NULL AND shipping_no IS NOT NULL AND product_cd IS NOT NULL
              AND DATE(shipping_date) >= CURDATE()
            ORDER BY shipping_no, product_cd
        """)
        result = await db.execute(sel)
        rows = result.mappings().all()

        copied_count = 0
        ins = text("""
            INSERT IGNORE INTO picking_list (shipping_no_p, shipping_no, product_cd, product_name, confirmed_boxes)
            VALUES (:shipping_no_p, :shipping_no, :product_cd, :product_name, :confirmed_boxes)
        """)
        for row in rows:
            r = await db.execute(ins, dict(row))
            if r.rowcount and r.rowcount > 0:
                copied_count += 1
        await db.commit()

        # 3) picking_list JOIN shipping_items で当日以降のデータを取得（CSV 用）
        join_sel = text("""
            SELECT pl.shipping_no_p, pl.shipping_no, pl.product_cd, pl.product_name, pl.confirmed_boxes
            FROM picking_list pl
            INNER JOIN shipping_items si
              ON pl.shipping_no_p = si.shipping_no_p AND pl.product_cd = si.product_cd
            WHERE DATE(si.shipping_date) >= CURDATE()
            ORDER BY pl.shipping_no, pl.product_cd
        """)
        join_result = await db.execute(join_sel)
        csv_rows = join_result.mappings().all()
        total_data_count = len(csv_rows)

        csv_path: Optional[str] = None
        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if total_data_count > 0 and PICKING_CSV_OUTPUT_DIR:
            # 4) CSV 生成（ヘッダ: shipping_no_p, shipping_no, product_cd, product_name, confirmed_boxes）
            buf = io.StringIO()
            buf.write("\uFEFF")  # UTF-8 BOM
            writer = csv.writer(buf, lineterminator="\r\n")
            writer.writerow(["shipping_no_p", "shipping_no", "product_cd", "product_name", "confirmed_boxes"])
            for r in csv_rows:
                writer.writerow([
                    _escape_csv_cell(r.get("shipping_no_p")),
                    _escape_csv_cell(r.get("shipping_no")),
                    _escape_csv_cell(r.get("product_cd")),
                    _escape_csv_cell(r.get("product_name")),
                    _escape_csv_cell(r.get("confirmed_boxes")),
                ])
            content = buf.getvalue()

            # 5) ディレクトリ存在確認・ファイル書き込み
            os.makedirs(PICKING_CSV_OUTPUT_DIR, exist_ok=True)
            out_path = os.path.join(PICKING_CSV_OUTPUT_DIR, PICKING_CSV_FILENAME)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            csv_path = out_path

        return {
            "success": True,
            "message": "ピッキングデータのエクスポートが完了しました",
            "copiedCount": copied_count,
            "totalDataCount": total_data_count,
            "fileName": PICKING_CSV_FILENAME if total_data_count > 0 else None,
            "csvFilePath": csv_path,
            "exportTime": export_time,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

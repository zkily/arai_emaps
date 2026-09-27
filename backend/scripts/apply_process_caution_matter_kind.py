"""Apply migration 156_process_caution_matter_kind.sql (idempotent)."""
from __future__ import annotations

import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv
import os

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")


def main() -> None:
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "eams_db"),
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SHOW COLUMNS FROM quality_product_process_cautions LIKE 'matter_kind'"
            )
            if cur.fetchone():
                print("matter_kind already exists")
                return
            cur.execute(
                """
                ALTER TABLE quality_product_process_cautions
                ADD COLUMN matter_kind VARCHAR(20) NOT NULL DEFAULT 'caution'
                  COMMENT 'caution=注意事項 quality=品質事項'
                  AFTER caution_text
                """
            )
        conn.commit()
        print("matter_kind added")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

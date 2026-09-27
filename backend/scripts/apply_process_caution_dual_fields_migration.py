"""Apply migration 157_process_caution_dual_fields.sql (idempotent)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv

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
        autocommit=False,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SHOW COLUMNS FROM quality_product_process_cautions LIKE 'quality_text'"
            )
            if not cur.fetchone():
                cur.execute(
                    """
                    ALTER TABLE quality_product_process_cautions
                    ADD COLUMN quality_text VARCHAR(500) NULL
                      COMMENT '品質事項（App表示）'
                      AFTER caution_text
                    """
                )
                print("OK: quality_text added")
            else:
                print("skip: quality_text exists")

            cur.execute(
                """
                ALTER TABLE quality_product_process_cautions
                MODIFY COLUMN caution_text VARCHAR(500) NULL
                  COMMENT '注意事項（App表示）'
                """
            )
            print("OK: caution_text nullable")

            # merge quality-kind into sibling caution rows
            cur.execute(
                """
                UPDATE quality_product_process_cautions c
                INNER JOIN quality_product_process_cautions q
                  ON q.matter_kind = 'quality'
                 AND q.process_code = c.process_code
                 AND q.id <> c.id
                 AND (
                   (c.product_cd IS NULL AND q.product_cd IS NULL)
                   OR (c.product_cd IS NOT NULL AND c.product_cd = q.product_cd)
                 )
                SET c.quality_text = CASE
                  WHEN c.quality_text IS NULL OR TRIM(c.quality_text) = '' THEN q.caution_text
                  WHEN q.caution_text IS NULL OR TRIM(q.caution_text) = '' THEN c.quality_text
                  ELSE CONCAT(c.quality_text, '\\n', q.caution_text)
                END
                WHERE (c.matter_kind IS NULL OR c.matter_kind = '' OR c.matter_kind = 'caution')
                """
            )
            print(f"OK: merged into caution rows ({cur.rowcount})")

            cur.execute(
                """
                DELETE q FROM quality_product_process_cautions q
                INNER JOIN quality_product_process_cautions c
                  ON c.process_code = q.process_code
                 AND c.id <> q.id
                 AND (c.matter_kind IS NULL OR c.matter_kind = '' OR c.matter_kind = 'caution')
                 AND (
                   (c.product_cd IS NULL AND q.product_cd IS NULL)
                   OR (c.product_cd IS NOT NULL AND c.product_cd = q.product_cd)
                 )
                WHERE q.matter_kind = 'quality'
                """
            )
            print(f"OK: deleted merged quality rows ({cur.rowcount})")

            cur.execute(
                """
                UPDATE quality_product_process_cautions
                SET quality_text = caution_text,
                    caution_text = NULL
                WHERE matter_kind = 'quality'
                  AND (quality_text IS NULL OR TRIM(quality_text) = '')
                """
            )
            print(f"OK: converted remaining quality-only rows ({cur.rowcount})")

        conn.commit()
        print("157_process_caution_dual_fields applied")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

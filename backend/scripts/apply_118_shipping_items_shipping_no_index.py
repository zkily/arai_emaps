"""Apply 118_shipping_items_shipping_no_index.sql"""
from pathlib import Path

import mysql.connector

from app.core.config import settings

conn = mysql.connector.connect(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME,
)
cur = conn.cursor()

cur.execute(
    """
    SELECT COUNT(1)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'shipping_items'
      AND INDEX_NAME = 'idx_shipping_items_shipping_no'
    """
)
exists = int((cur.fetchone() or (0,))[0] or 0)
if exists == 0:
    cur.execute(
        "CREATE INDEX `idx_shipping_items_shipping_no` ON `shipping_items` (`shipping_no`)"
    )
    conn.commit()
    print("created idx_shipping_items_shipping_no")
else:
    print("index already exists")

cur.execute(
    """
    SELECT INDEX_NAME
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'shipping_items'
      AND INDEX_NAME = 'idx_shipping_items_shipping_no'
    """
)
print("index:", cur.fetchall())
cur.close()
conn.close()
print("migration ok")

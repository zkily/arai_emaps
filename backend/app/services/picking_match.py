"""shipping_log と shipping_items のピッキング突合条件。

shipping_log.picking_no は utf8mb4_unicode_ci、shipping_items.shipping_no_p は utf8mb4_bin。
照合は shipping_items 側を unicode_ci に寄せ、shipping_log.idx_picking_no を使えるようにする。

FastAPI の shipping パッケージ（__init__ が router を読む）とは独立させ、
file_watcher.sync_services との循環 import を避ける。
"""

# スキャン番号（QR）は shipping_no_p（出荷番号_品番）。パレット番号のみのログは shipping_no + product_code で補完。


def _si_no_p_ci(si_alias: str) -> str:
    return f"CONVERT(TRIM({si_alias}.shipping_no_p) USING utf8mb4) COLLATE utf8mb4_unicode_ci"


def _si_no_ci(si_alias: str) -> str:
    return f"CONVERT(TRIM({si_alias}.shipping_no) USING utf8mb4) COLLATE utf8mb4_unicode_ci"


def _si_cd_ci(si_alias: str) -> str:
    return f"CONVERT(TRIM({si_alias}.product_cd) USING utf8mb4) COLLATE utf8mb4_unicode_ci"


def shipping_log_exists_sql(si_alias: str = "si", sl_alias: str = "l") -> str:
    """shipping_log に突合行があるか。l.picking_no は変換せずインデックスを維持する。"""
    si_no_p = _si_no_p_ci(si_alias)
    si_no = _si_no_ci(si_alias)
    si_cd = _si_cd_ci(si_alias)
    return f"""EXISTS (
        SELECT 1 FROM shipping_log {sl_alias}
        WHERE {sl_alias}.picking_no IS NOT NULL
          AND {sl_alias}.picking_no != ''
          AND (
            {sl_alias}.picking_no = {si_no_p}
            OR (
              {sl_alias}.picking_no = {si_no}
              AND (
                IFNULL(TRIM({sl_alias}.product_code), '') = ''
                OR TRIM({sl_alias}.product_code) = {si_cd}
              )
            )
          )
        LIMIT 1
    )"""


def picking_matched_sql(si_alias: str = "si") -> str:
    """完了判定：保存済みフラグまたは shipping_log のライブ突合。"""
    return f"(({si_alias}.picking_log_matched = 1) OR {shipping_log_exists_sql(si_alias)})"

"""
生産管理指標(YYYY年度-検査).csv/.xlsx → inspection_management 取込（CLI）

用法（仓库根目录，需 backend/.env 中 DB_* 已配置）:

    py scripts/import_inspection_management_csv.py --dry-run
    py scripts/import_inspection_management_csv.py --csv "frontend/生産管理指標(2026年度-検査).csv"
    py scripts/import_inspection_management_csv.py --replace
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

try:
    import mysql.connector
except ImportError as e:
    raise SystemExit("需要 mysql-connector-python") from e

from app.services.inspection_management_import import (  # noqa: E402
    REMARKS_PREFIX_CSV,
    delete_rows_by_remarks_prefix,
    load_user_rows,
    parse_rows_from_source,
    sync_parsed_rows_to_db,
    build_defect_map,
)
from scripts.bootstrap_full_database import load_db_settings  # noqa: E402

DEFAULT_CSV = ROOT / "frontend" / "生産管理指標(2026年度-検査).csv"


def _connection_factory(host, port, user, password, db_name):
    def _connect():
        return mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            charset="utf8mb4",
        )

    return _connect


def main() -> int:
    parser = argparse.ArgumentParser(description="CSV/Excel → inspection_management")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="CSV 或 xlsx 路径")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace", action="store_true", help="删除 CSV_IMPORT 旧记录后全量重导")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-unmapped", action="store_true")
    parser.add_argument("--env", type=Path, default=None)
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    source = args.csv if args.csv.is_absolute() else ROOT / args.csv
    if not source.is_file():
        raise SystemExit(f"文件不存在: {source}")

    host, port, user, password, db_name = load_db_settings(args.env)
    connect = _connection_factory(host, port, user, password, db_name)
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        defect_map = build_defect_map(cur)
        user_rows = load_user_rows(cur)
        rows, errors = parse_rows_from_source(
            str(source),
            defect_name_map=defect_map,
            user_rows=user_rows,
            skip_unmapped_inspector=args.skip_unmapped,
            remarks_prefix=REMARKS_PREFIX_CSV,
        )
        if args.limit > 0:
            rows = rows[: args.limit]

        deleted = 0
        if args.replace:
            deleted = delete_rows_by_remarks_prefix(cur, REMARKS_PREFIX_CSV, dry_run=args.dry_run)

        result = sync_parsed_rows_to_db(cur, rows, dry_run=args.dry_run)
        result.errors.extend(errors)

        if not args.dry_run:
            conn.commit()

        print(f"来源: {source}")
        print(f"解析: {result.parsed} 行")
        if args.replace:
            print(f"删除旧 CSV_IMPORT: {deleted} 行")
        print(f"{'将插入' if args.dry_run else '已插入'}: {result.inserted} 行")
        print(f"重复跳过: {result.skipped_duplicate} 行")
        if result.unmapped_inspectors:
            print("未匹配作業者:")
            for name, cnt in sorted(result.unmapped_inspectors.items(), key=lambda x: -x[1]):
                print(f"  - {name}: {cnt} 行")
        if result.errors:
            print(f"警告/跳过: {len(result.errors)} 条")
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

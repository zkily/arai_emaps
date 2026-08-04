"""実績修正統計 PPT を生成し、デスクトップへ保存する。

Usage:
  python scripts/generate_manual_entry_statistics_ppt.py
  python scripts/generate_manual_entry_statistics_ppt.py --month 2026-07 --compare-month 2026-06 --trend-months 6
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import AsyncSessionLocal
from app.modules.erp.manual_entry_statistics_ppt import build_manual_entry_statistics_pptx
from app.modules.erp.stock_transaction_log_api import fetch_manual_entry_statistics


def _desktop_dir() -> Path:
    home = Path.home()
    desktop = home / "Desktop"
    if desktop.is_dir():
        return desktop
    # OneDrive Desktop fallback
    for candidate in (home / "OneDrive" / "Desktop", home / "OneDrive" / "デスクトップ"):
        if candidate.is_dir():
            return candidate
    return home


async def _run(args: argparse.Namespace) -> Path:
    async with AsyncSessionLocal() as db:
        data = await fetch_manual_entry_statistics(
            db,
            month=args.month,
            compare_month=args.compare_month,
            trend_months=args.trend_months,
            process_cd=args.process_cd,
        )

    month = data.get("month") or datetime.now().strftime("%Y-%m")
    out_dir = Path(args.output) if args.output else _desktop_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"実績修正統計_{month.replace('-', '')}.pptx"

    content = build_manual_entry_statistics_pptx(data)
    out_path.write_bytes(content)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 実績修正統計 PPT to Desktop")
    parser.add_argument("--month", default=None, help="対象月 YYYY-MM")
    parser.add_argument("--compare-month", default=None, help="比較月 YYYY-MM")
    parser.add_argument("--trend-months", type=int, default=6, help="推移月数")
    parser.add_argument("--process-cd", default=None, help="工程コード")
    parser.add_argument("--output", default=None, help="出力ディレクトリ（未指定時はデスクトップ）")
    args = parser.parse_args()

    out = asyncio.run(_run(args))
    print(f"OK: {out}")


if __name__ == "__main__":
    main()

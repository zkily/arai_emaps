"""在庫推移レポート生成器（production_summarys の工程別在庫を期間集計）"""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    PDF_MIME,
    XLSX_MIME,
    GeneratedReport,
    ReportAttachment,
    ReportGenerator,
    build_pdf,
    build_xlsx,
    resolve_date_range,
)

# (ラベル, production_summarys の在庫列)。列名はホワイトリストのみ。
_PROCESS_COLUMNS: list[tuple[str, str]] = [
    ("切断", "cutting_inventory"),
    ("面取", "chamfering_inventory"),
    ("成型", "molding_inventory"),
    ("メッキ", "plating_inventory"),
    ("溶接", "welding_inventory"),
    ("検査", "inspection_inventory"),
    ("倉庫", "warehouse_inventory"),
]


class InventoryTrendGenerator(ReportGenerator):
    report_code = "INVENTORY_TREND_WEEKLY"

    async def generate(
        self,
        db: AsyncSession,
        *,
        parameters: dict[str, Any],
        fmt: str,
        run_date: date,
    ) -> GeneratedReport:
        rng = resolve_date_range(parameters, run_date=run_date)

        select_cols = ", ".join(f"COALESCE(SUM(`{col}`), 0) AS `{col}`" for _, col in _PROCESS_COLUMNS)
        sql = text(
            f"SELECT `date` AS day, {select_cols} "
            "FROM production_summarys "
            "WHERE `date` BETWEEN :start AND :end "
            "GROUP BY `date` ORDER BY `date`"
        )
        rows = (await db.execute(sql, {"start": rng.start, "end": rng.end})).mappings().all()

        summary_html = _build_summary_html(rows)
        summary_text = _build_summary_text(rows)

        sheets = _build_sheets(rows)
        base_name = f"在庫推移_{rng.start.isoformat()}_{rng.end.isoformat()}"
        attachments: list[ReportAttachment] = []
        if fmt in ("xlsx", "both"):
            attachments.append(ReportAttachment(f"{base_name}.xlsx", build_xlsx(sheets), XLSX_MIME))
        if fmt in ("pdf", "both"):
            attachments.append(
                ReportAttachment(f"{base_name}.pdf", build_pdf("在庫推移レポート", rng.label, sheets), PDF_MIME)
            )

        return GeneratedReport(
            period_label=rng.label,
            record_count=len(rows),
            summary_html=summary_html,
            summary_text=summary_text,
            attachments=attachments,
        )


def _build_summary_html(rows: list) -> str:
    if not rows:
        return "<p>対象期間に在庫データはありません。</p>"
    latest = rows[-1]
    body = "".join(
        f"<tr><td>{label}</td><td align='right'>{int(latest[col]):,}</td></tr>"
        for label, col in _PROCESS_COLUMNS
    )
    return (
        f"<p>期末（{latest['day']}）時点の工程別在庫:</p>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>工程</th><th>在庫数</th></tr>"
        f"{body}</table>"
    )


def _build_summary_text(rows: list) -> str:
    if not rows:
        return "対象期間に在庫データはありません。"
    latest = rows[-1]
    lines = [f"  {label}: {int(latest[col]):,}" for label, col in _PROCESS_COLUMNS]
    return f"期末（{latest['day']}）時点の工程別在庫:\n" + "\n".join(lines)


def _build_sheets(rows: list) -> list[tuple[str, list[str], list[list]]]:
    headers = ["日付"] + [label for label, _ in _PROCESS_COLUMNS]
    data = [
        [str(r["day"])] + [int(r[col]) for _, col in _PROCESS_COLUMNS]
        for r in rows
    ]
    return [("在庫推移", headers, data)]

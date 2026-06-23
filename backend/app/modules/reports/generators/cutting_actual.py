"""切断工程実績レポート生成器（stock_transaction_logs ベース）"""
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

SOURCE_FILE = "cutting_management"


class CuttingDailyActualGenerator(ReportGenerator):
    report_code = "CUTTING_DAILY_ACTUAL"

    async def generate(
        self,
        db: AsyncSession,
        *,
        parameters: dict[str, Any],
        fmt: str,
        run_date: date,
    ) -> GeneratedReport:
        rng = resolve_date_range(parameters, run_date=run_date)

        machine_sql = text(
            """
            SELECT COALESCE(machine_cd, '—') AS machine_cd,
                   COUNT(*) AS cnt,
                   COALESCE(SUM(quantity), 0) AS qty
            FROM stock_transaction_logs
            WHERE source_file = :source_file
              AND transaction_type = '実績'
              AND DATE(transaction_time) BETWEEN :start AND :end
            GROUP BY machine_cd
            ORDER BY machine_cd
            """
        )
        detail_sql = text(
            """
            SELECT DATE(transaction_time) AS day,
                   COALESCE(machine_cd, '—') AS machine_cd,
                   target_cd,
                   lot_no,
                   quantity,
                   operator_name,
                   transaction_time
            FROM stock_transaction_logs
            WHERE source_file = :source_file
              AND transaction_type = '実績'
              AND DATE(transaction_time) BETWEEN :start AND :end
            ORDER BY transaction_time
            """
        )
        params = {"source_file": SOURCE_FILE, "start": rng.start, "end": rng.end}
        machine_rows = (await db.execute(machine_sql, params)).mappings().all()
        detail_rows = (await db.execute(detail_sql, params)).mappings().all()

        total_count = sum(int(r["cnt"]) for r in machine_rows)
        total_qty = sum(float(r["qty"]) for r in machine_rows)

        summary_html = _build_summary_html(machine_rows, total_qty)
        summary_text = _build_summary_text(machine_rows, total_qty)

        sheets = _build_sheets(machine_rows, detail_rows)
        base_name = f"切断実績_{rng.start.isoformat()}_{rng.end.isoformat()}"
        attachments: list[ReportAttachment] = []
        if fmt in ("xlsx", "both"):
            attachments.append(
                ReportAttachment(f"{base_name}.xlsx", build_xlsx(sheets), XLSX_MIME)
            )
        if fmt in ("pdf", "both"):
            attachments.append(
                ReportAttachment(f"{base_name}.pdf", build_pdf("切断工程実績レポート", rng.label, sheets), PDF_MIME)
            )

        return GeneratedReport(
            period_label=rng.label,
            record_count=total_count,
            summary_html=summary_html,
            summary_text=summary_text,
            attachments=attachments,
        )


def _build_summary_html(machine_rows: list, total_qty: float) -> str:
    if not machine_rows:
        return "<p>対象期間に切断実績はありません。</p>"
    body = "".join(
        f"<tr><td>{r['machine_cd']}</td><td align='right'>{int(r['cnt']):,}</td>"
        f"<td align='right'>{int(r['qty']):,}</td></tr>"
        for r in machine_rows
    )
    return (
        "<p>設備別実績:</p>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>設備</th><th>件数</th><th>数量</th></tr>"
        f"{body}"
        f"<tr><th>合計</th><th align='right'>{sum(int(r['cnt']) for r in machine_rows):,}</th>"
        f"<th align='right'>{int(total_qty):,}</th></tr>"
        "</table>"
    )


def _build_summary_text(machine_rows: list, total_qty: float) -> str:
    if not machine_rows:
        return "対象期間に切断実績はありません。"
    lines = [
        f"  {r['machine_cd']}: {int(r['cnt']):,} 件 / {int(r['qty']):,} 本" for r in machine_rows
    ]
    lines.append(f"  合計: {int(total_qty):,} 本")
    return "設備別実績:\n" + "\n".join(lines)


def _build_sheets(machine_rows: list, detail_rows: list) -> list[tuple[str, list[str], list[list]]]:
    summary_sheet = (
        "サマリー",
        ["設備", "件数", "数量"],
        [[r["machine_cd"], int(r["cnt"]), int(r["qty"])] for r in machine_rows],
    )
    detail_sheet = (
        "明細",
        ["生産日", "設備", "品目コード", "ロットNo", "数量", "担当者", "実績日時"],
        [
            [
                str(r["day"]),
                r["machine_cd"],
                r["target_cd"],
                r["lot_no"] or "",
                int(r["quantity"]),
                r["operator_name"] or "",
                str(r["transaction_time"]),
            ]
            for r in detail_rows
        ],
    )
    return [summary_sheet, detail_sheet]

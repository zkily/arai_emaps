"""計画実績対比レポート生成器（production_summarys の工程別 plan/actual を月次集計）"""
from __future__ import annotations

import calendar
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
    resolve_month,
)

# (ラベル, 計画列, 実績列)。列名はホワイトリストのみ。
_PROCESS_PAIRS: list[tuple[str, str, str]] = [
    ("切断", "cutting_plan", "cutting_actual"),
    ("面取", "chamfering_plan", "chamfering_actual"),
    ("成型", "molding_plan", "molding_actual"),
    ("メッキ", "plating_plan", "plating_actual"),
    ("溶接", "welding_plan", "welding_actual"),
    ("検査", "inspection_plan", "inspection_actual"),
]


class PlanActualCompareGenerator(ReportGenerator):
    report_code = "PLAN_ACTUAL_MONTHLY"

    async def generate(
        self,
        db: AsyncSession,
        *,
        parameters: dict[str, Any],
        fmt: str,
        run_date: date,
    ) -> GeneratedReport:
        month_start = resolve_month(parameters, run_date=run_date)
        last_day = calendar.monthrange(month_start.year, month_start.month)[1]
        month_end = month_start.replace(day=last_day)
        period_label = month_start.strftime("%Y-%m")

        select_cols = ", ".join(
            f"COALESCE(SUM(`{plan}`), 0) AS `{plan}`, COALESCE(SUM(`{actual}`), 0) AS `{actual}`"
            for _, plan, actual in _PROCESS_PAIRS
        )
        sql = text(
            f"SELECT {select_cols} FROM production_summarys "
            "WHERE `date` BETWEEN :start AND :end"
        )
        row = (await db.execute(sql, {"start": month_start, "end": month_end})).mappings().first() or {}

        comparison = [
            {
                "label": label,
                "plan": int(row.get(plan) or 0),
                "actual": int(row.get(actual) or 0),
            }
            for label, plan, actual in _PROCESS_PAIRS
        ]
        for item in comparison:
            item["diff"] = item["actual"] - item["plan"]
            item["rate"] = round(item["actual"] / item["plan"] * 100, 1) if item["plan"] else None

        summary_html = _build_summary_html(comparison)
        summary_text = _build_summary_text(comparison)
        record_count = sum(1 for c in comparison if c["plan"] or c["actual"])

        sheets = _build_sheets(comparison)
        base_name = f"計画実績対比_{period_label}"
        attachments: list[ReportAttachment] = []
        if fmt in ("xlsx", "both"):
            attachments.append(ReportAttachment(f"{base_name}.xlsx", build_xlsx(sheets), XLSX_MIME))
        if fmt in ("pdf", "both"):
            attachments.append(
                ReportAttachment(f"{base_name}.pdf", build_pdf("計画実績対比レポート", period_label, sheets), PDF_MIME)
            )

        return GeneratedReport(
            period_label=period_label,
            record_count=record_count,
            summary_html=summary_html,
            summary_text=summary_text,
            attachments=attachments,
        )


def _rate_str(rate: float | None) -> str:
    return f"{rate}%" if rate is not None else "—"


def _build_summary_html(comparison: list[dict]) -> str:
    body = "".join(
        f"<tr><td>{c['label']}</td><td align='right'>{c['plan']:,}</td>"
        f"<td align='right'>{c['actual']:,}</td><td align='right'>{c['diff']:,}</td>"
        f"<td align='right'>{_rate_str(c['rate'])}</td></tr>"
        for c in comparison
    )
    return (
        "<p>工程別 計画／実績対比:</p>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>工程</th><th>計画</th><th>実績</th><th>差異</th><th>達成率</th></tr>"
        f"{body}</table>"
    )


def _build_summary_text(comparison: list[dict]) -> str:
    lines = [
        f"  {c['label']}: 計画 {c['plan']:,} / 実績 {c['actual']:,} / 差異 {c['diff']:,} / 達成率 {_rate_str(c['rate'])}"
        for c in comparison
    ]
    return "工程別 計画／実績対比:\n" + "\n".join(lines)


def _build_sheets(comparison: list[dict]) -> list[tuple[str, list[str], list[list]]]:
    headers = ["工程", "計画", "実績", "差異", "達成率(%)"]
    data = [
        [c["label"], c["plan"], c["actual"], c["diff"], c["rate"] if c["rate"] is not None else ""]
        for c in comparison
    ]
    return [("計画実績対比", headers, data)]

"""切断工程実績レポート生成器（成型前在庫推移 + 切断計画実績対比）"""
from __future__ import annotations

import io
from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    PDF_MIME,
    XLSX_MIME,
    GeneratedReport,
    ReportAttachment,
    ReportGenerator,
    _ensure_jp_font,
    build_xlsx,
    resolve_date_range,
)

# 成型工程より前の在庫列（日次合計）
_PRE_MOLDING_INVENTORY_COLS = ("cutting_inventory", "chamfering_inventory")

_CHART_PRIMARY = "#2563EB"
_CHART_ACCENT = "#10B981"
_CHART_GRID = "#E2E8F0"
_CHART_TEXT = "#475569"


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

        inv_sum_expr = " + ".join(f"COALESCE(`{col}`, 0)" for col in _PRE_MOLDING_INVENTORY_COLS)
        inventory_sql = text(
            f"""
            SELECT `date` AS day,
                   COALESCE(SUM({inv_sum_expr}), 0) AS pre_molding_inv
            FROM production_summarys
            WHERE `date` BETWEEN :start AND :end
            GROUP BY `date`
            ORDER BY `date`
            """
        )
        plan_actual_sql = text(
            """
            SELECT `date` AS day,
                   COALESCE(SUM(cutting_plan), 0) AS plan_qty,
                   COALESCE(SUM(cutting_actual), 0) AS actual_qty
            FROM production_summarys
            WHERE `date` BETWEEN :start AND :end
            GROUP BY `date`
            ORDER BY `date`
            """
        )
        params = {"start": rng.start, "end": rng.end}
        inv_rows = (await db.execute(inventory_sql, params)).mappings().all()
        pa_rows = (await db.execute(plan_actual_sql, params)).mappings().all()

        daily = _merge_daily_series(rng.start, rng.end, inv_rows, pa_rows)
        chart_data = _build_chart_data(daily)

        total_plan = sum(d["plan"] for d in daily)
        total_actual = sum(d["actual"] for d in daily)
        record_count = sum(1 for d in daily if d["plan"] or d["actual"] or d["inventory"])

        summary_html = _build_summary_html(rng.label, daily, total_plan, total_actual)
        summary_text = _build_summary_text(rng.label, daily, total_plan, total_actual)
        sheets = _build_sheets(daily)

        base_name = f"切断実績_{rng.start.isoformat()}_{rng.end.isoformat()}"
        attachments: list[ReportAttachment] = []
        if fmt in ("xlsx", "both"):
            attachments.append(
                ReportAttachment(f"{base_name}.xlsx", build_xlsx(sheets), XLSX_MIME)
            )
        if fmt in ("pdf", "both"):
            attachments.append(
                ReportAttachment(
                    f"{base_name}.pdf",
                    _build_cutting_report_pdf("切断工程実績レポート", rng.label, daily, chart_data),
                    PDF_MIME,
                )
            )

        return GeneratedReport(
            period_label=rng.label,
            record_count=record_count,
            summary_html=summary_html,
            summary_text=summary_text,
            attachments=attachments,
            extra_variables={"chart_data": chart_data},
        )


def _merge_daily_series(
    start: date,
    end: date,
    inv_rows: list,
    pa_rows: list,
) -> list[dict[str, Any]]:
    """期間内の全日を埋め、在庫・計画・実績を統合する。"""
    inv_map = {str(r["day"]): int(r["pre_molding_inv"] or 0) for r in inv_rows}
    pa_map = {
        str(r["day"]): {"plan": int(r["plan_qty"] or 0), "actual": int(r["actual_qty"] or 0)}
        for r in pa_rows
    }

    daily: list[dict[str, Any]] = []
    cur = start
    while cur <= end:
        key = cur.isoformat()
        pa = pa_map.get(key, {"plan": 0, "actual": 0})
        daily.append(
            {
                "day": key,
                "label": cur.strftime("%m/%d"),
                "inventory": inv_map.get(key, 0),
                "plan": pa["plan"],
                "actual": pa["actual"],
            }
        )
        cur += timedelta(days=1)
    return daily


def _build_chart_data(daily: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "inventory_trend": {
            "labels": [d["label"] for d in daily],
            "values": [d["inventory"] for d in daily],
        },
        "plan_actual": {
            "labels": [d["label"] for d in daily],
            "plan": [d["plan"] for d in daily],
            "actual": [d["actual"] for d in daily],
        },
    }


def _rate_str(plan: int, actual: int) -> str:
    if not plan:
        return "—"
    return f"{round(actual / plan * 100, 1)}%"


def _build_summary_html(
    period_label: str,
    daily: list[dict[str, Any]],
    total_plan: int,
    total_actual: int,
) -> str:
    if not daily:
        return "<p>対象期間にデータはありません。</p>"

    inv_peak = max(daily, key=lambda d: d["inventory"])
    inv_latest = daily[-1]["inventory"]
    diff = total_actual - total_plan

    rows_html = "".join(
        f"<tr>"
        f"<td>{d['day']}</td>"
        f"<td align='right'>{d['inventory']:,}</td>"
        f"<td align='right'>{d['plan']:,}</td>"
        f"<td align='right'>{d['actual']:,}</td>"
        f"<td align='right'>{d['actual'] - d['plan']:,}</td>"
        f"<td align='right'>{_rate_str(d['plan'], d['actual'])}</td>"
        f"</tr>"
        for d in daily
    )

    return f"""
<div class="cutting-report-summary">
  <div class="cr-header">
    <h3 class="cr-title">切断工程実績レポート</h3>
    <span class="cr-period">対象期間: {period_label}</span>
  </div>
  <div class="cr-kpi-row">
    <div class="cr-kpi"><span class="cr-kpi__label">期末 成型前在庫</span><b>{inv_latest:,}</b></div>
    <div class="cr-kpi"><span class="cr-kpi__label">期間ピーク在庫</span><b>{inv_peak['inventory']:,}</b><small>({inv_peak['day']})</small></div>
    <div class="cr-kpi"><span class="cr-kpi__label">計画合計</span><b>{total_plan:,}</b></div>
    <div class="cr-kpi"><span class="cr-kpi__label">実績合計</span><b>{total_actual:,}</b></div>
    <div class="cr-kpi"><span class="cr-kpi__label">差異</span><b class="{'cr-pos' if diff >= 0 else 'cr-neg'}">{diff:+,}</b></div>
    <div class="cr-kpi"><span class="cr-kpi__label">達成率</span><b>{_rate_str(total_plan, total_actual)}</b></div>
  </div>
  <p class="cr-note">※ 成型前在庫 = 切断在庫 + 面取在庫（日次合計）</p>
  <table class="cr-table">
    <thead>
      <tr>
        <th>日付</th><th>成型前在庫</th><th>切断計画</th><th>切断実績</th><th>差異</th><th>達成率</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
    <tfoot>
      <tr>
        <th>合計</th>
        <th align="right">—</th>
        <th align="right">{total_plan:,}</th>
        <th align="right">{total_actual:,}</th>
        <th align="right">{diff:+,}</th>
        <th align="right">{_rate_str(total_plan, total_actual)}</th>
      </tr>
    </tfoot>
  </table>
</div>
"""


def _build_summary_text(
    period_label: str,
    daily: list[dict[str, Any]],
    total_plan: int,
    total_actual: int,
) -> str:
    if not daily:
        return "対象期間にデータはありません。"
    inv_latest = daily[-1]["inventory"]
    lines = [
        f"対象期間: {period_label}",
        f"期末 成型前在庫: {inv_latest:,}",
        f"切断 計画合計: {total_plan:,} / 実績合計: {total_actual:,} / 差異: {total_actual - total_plan:+,}",
    ]
    for d in daily[-3:]:
        lines.append(
            f"  {d['day']}: 在庫 {d['inventory']:,} / 計画 {d['plan']:,} / 実績 {d['actual']:,}"
        )
    return "\n".join(lines)


def _build_sheets(daily: list[dict[str, Any]]) -> list[tuple[str, list[str], list[list]]]:
    inv_sheet = (
        "成型前在庫推移",
        ["日付", "成型前在庫（切断+面取）"],
        [[d["day"], d["inventory"]] for d in daily],
    )
    pa_sheet = (
        "切断計画実績",
        ["日付", "計画", "実績", "差異", "達成率(%)"],
        [
            [
                d["day"],
                d["plan"],
                d["actual"],
                d["actual"] - d["plan"],
                round(d["actual"] / d["plan"] * 100, 1) if d["plan"] else "",
            ]
            for d in daily
        ],
    )
    return [inv_sheet, pa_sheet]


def _build_cutting_report_pdf(
    title: str,
    period_label: str,
    daily: list[dict[str, Any]],
    chart_data: dict[str, Any],
) -> bytes:
    """A4 横向き・チャート付き PDF を生成する。"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font = _ensure_jp_font()
    page_size = landscape(A4)
    page_w, page_h = page_size
    margin = 14 * mm
    content_w = page_w - 2 * margin

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "cr_title",
        parent=styles["Title"],
        fontName=font,
        fontSize=15,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        "cr_sub",
        parent=styles["Normal"],
        fontName=font,
        fontSize=8,
        textColor=colors.HexColor(_CHART_TEXT),
        spaceAfter=2,
    )
    section_style = ParagraphStyle(
        "cr_section",
        parent=styles["Heading2"],
        fontName=font,
        fontSize=9,
        textColor=colors.HexColor("#1E40AF"),
        spaceBefore=2,
        spaceAfter=4,
    )

    total_plan = sum(d["plan"] for d in daily)
    total_actual = sum(d["actual"] for d in daily)
    inv_latest = daily[-1]["inventory"] if daily else 0
    diff = total_actual - total_plan

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        topMargin=margin,
        bottomMargin=margin,
        leftMargin=margin,
        rightMargin=margin,
    )

    chart_gap = 8 * mm
    chart_w = (content_w - chart_gap) / 2
    chart_h = 58 * mm

    charts_table = Table(
        [
            [
                [
                    Paragraph("成型前在庫推移（日次・単位: 千）", section_style),
                    _build_inventory_line_chart(daily, chart_w, chart_h),
                ],
                [
                    Paragraph("切断工程 計画 vs 実績（日次）", section_style),
                    _build_plan_actual_bar_chart(daily, chart_w, chart_h),
                ],
            ]
        ],
        colWidths=[chart_w, chart_w],
        hAlign="LEFT",
    )
    charts_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), chart_gap / 2),
                ("LEFTPADDING", (1, 0), (1, 0), chart_gap / 2),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ]
        )
    )

    flow: list[Any] = [
        Paragraph(title, title_style),
        Paragraph(f"対象期間: {period_label}", sub_style),
        Paragraph("成型前在庫 = 切断在庫 + 面取在庫（日次合計）", sub_style),
        Spacer(1, 4),
        _build_kpi_table(font, inv_latest, total_plan, total_actual, diff),
        Spacer(1, 6),
        charts_table,
        Spacer(1, 6),
        _build_daily_table(font, daily, total_plan, total_actual, diff, content_w),
    ]

    doc.build(flow)
    return buffer.getvalue()


def _build_kpi_table(font: str, inv: int, plan: int, actual: int, diff: int) -> Table:
    from reportlab.lib import colors

    data = [
        ["期末成型前在庫", "計画合計", "実績合計", "差異", "達成率"],
        [
            f"{inv:,}",
            f"{plan:,}",
            f"{actual:,}",
            f"{diff:+,}",
            _rate_str(plan, actual),
        ],
    ]
    col_w = [34 * 18, 34 * 18, 34 * 18, 34 * 18, 34 * 18]
    table = Table(data, colWidths=col_w)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, 1), 11),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(_CHART_TEXT)),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#0F172A")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EFF6FF")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(_CHART_GRID)),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor(_CHART_GRID)),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _build_inventory_line_chart(daily: list[dict[str, Any]], width: float, height: float):
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.lib import colors

    drawing = Drawing(width, height)
    if not daily:
        drawing.add(String(width / 2, height / 2, "データなし", textAnchor="middle"))
        return drawing

    plot = LinePlot()
    plot.x = 36
    plot.y = 28
    plot.width = width - 52
    plot.height = height - 48
    plot.data = [[(i, d["inventory"]) for i, d in enumerate(daily)]]
    plot.lines[0].strokeColor = colors.HexColor(_CHART_PRIMARY)
    plot.lines[0].strokeWidth = 2
    plot.lines[0].symbol = None

    plot.xValueAxis.valueMin = 0
    plot.xValueAxis.valueMax = max(len(daily) - 1, 1)
    plot.xValueAxis.visibleGrid = False
    plot.xValueAxis.labels.fontSize = 7
    plot.xValueAxis.labelTextFormat = lambda v: daily[int(v)]["label"] if 0 <= int(v) < len(daily) else ""

    y_max = max((d["inventory"] for d in daily), default=0)
    plot.yValueAxis.valueMin = 0
    plot.yValueAxis.valueMax = y_max * 1.15 if y_max else 10
    plot.yValueAxis.visibleGrid = True
    plot.yValueAxis.gridStrokeColor = colors.HexColor(_CHART_GRID)
    plot.yValueAxis.labels.fontSize = 7

    drawing.add(plot)
    return drawing


def _build_plan_actual_bar_chart(daily: list[dict[str, Any]], width: float, height: float):
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.lib import colors

    drawing = Drawing(width, height)
    if not daily:
        drawing.add(String(width / 2, height / 2, "データなし", textAnchor="middle"))
        return drawing

    chart = VerticalBarChart()
    chart.x = 36
    chart.y = 28
    chart.width = width - 52
    chart.height = height - 48
    chart.data = [[d["plan"] for d in daily], [d["actual"] for d in daily]]
    chart.categoryAxis.categoryNames = [d["label"] for d in daily]
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.angle = 45 if len(daily) > 10 else 0
    chart.categoryAxis.labels.boxAnchor = "ne"

    y_max = max(max(d["plan"] for d in daily), max(d["actual"] for d in daily), 1)
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = y_max * 1.15
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.visibleGrid = True
    chart.valueAxis.gridStrokeColor = colors.HexColor(_CHART_GRID)

    chart.bars[0].fillColor = colors.HexColor("#93C5FD")
    chart.bars[0].strokeColor = colors.HexColor(_CHART_PRIMARY)
    chart.bars[0].strokeWidth = 0.5
    chart.bars[1].fillColor = colors.HexColor("#6EE7B7")
    chart.bars[1].strokeColor = colors.HexColor(_CHART_ACCENT)
    chart.bars[1].strokeWidth = 0.5

    drawing.add(chart)
    # 凡例
    from reportlab.graphics.shapes import Rect

    legend_y = height - 14
    drawing.add(Rect(40, legend_y, 10, 6, fillColor=colors.HexColor("#93C5FD"), strokeColor=None))
    drawing.add(String(54, legend_y, "計画", fontSize=7, fillColor=colors.HexColor(_CHART_TEXT)))
    drawing.add(Rect(90, legend_y, 10, 6, fillColor=colors.HexColor("#6EE7B7"), strokeColor=None))
    drawing.add(String(104, legend_y, "実績", fontSize=7, fillColor=colors.HexColor(_CHART_TEXT)))

    return drawing


def _build_daily_table(
    font: str,
    daily: list[dict[str, Any]],
    total_plan: int,
    total_actual: int,
    diff: int,
    content_w: float,
) -> Table:
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    headers = ["日付", "成型前在庫", "計画", "実績", "差異", "達成率"]
    rows = [
        [
            d["day"],
            f"{d['inventory']:,}",
            f"{d['plan']:,}",
            f"{d['actual']:,}",
            f"{d['actual'] - d['plan']:+,}",
            _rate_str(d["plan"], d["actual"]),
        ]
        for d in daily
    ]
    rows.append(
        [
            "合計",
            "—",
            f"{total_plan:,}",
            f"{total_actual:,}",
            f"{diff:+,}",
            _rate_str(total_plan, total_actual),
        ]
    )

    col_w = content_w / len(headers)
    table = Table([headers] + rows, colWidths=[col_w] * len(headers), repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF7")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor(_CHART_GRID)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table

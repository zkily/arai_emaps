"""切断工程実績レポート：プレビューと同型の HTML / PDF 用ビジュアル生成"""
from __future__ import annotations

import base64
import io
from datetime import date
from typing import Any

from .base import _ensure_jp_font

INVENTORY_LETTER_LINE = 142_000
INVENTORY_UNIT_THOUSAND = 1000
CHART_EMAIL_RENDER_DPI = 180
_CHART_PRIMARY = "#2563EB"
_CHART_ACCENT = "#10B981"
_CHART_GRID = "#E2E8F0"
_CHART_AXIS = "#94A3B8"
_CHART_TEXT = "#475569"


def _to_thousand(value: int) -> float:
    return round(value / INVENTORY_UNIT_THOUSAND * 10) / 10


def _fmt_thousand(value: int) -> str:
    thousand = _to_thousand(value)
    return f"{int(thousand)}" if thousand == int(thousand) else f"{thousand:.1f}"


def _fmt_plan_remaining(value: int) -> str:
    return _fmt_thousand(value)


def _fmt_baseline_diff(value: int | None) -> str:
    if value is None:
        return "—"
    thousand = _to_thousand(value)
    formatted = f"{int(thousand)}" if thousand == int(thousand) else f"{thousand:.1f}"
    if value > 0:
        return f"+{formatted}"
    return formatted


def _fmt_progress_rate(plan: int, actual: int) -> str:
    if not plan:
        return "—"
    return f"{actual / plan * 100:.1f}%"


def _resolve_baseline_diff_as_of(period_end: str, run_date: date) -> str:
    today_iso = run_date.isoformat()
    return period_end if period_end <= today_iso else today_iso


def _compute_summary_stats(
    chart_data: dict[str, Any], *, run_date: date
) -> dict[str, Any]:
    plan = chart_data["plan_actual"]["plan"]
    actual = chart_data["plan_actual"]["actual"]
    labels = chart_data["plan_actual"]["labels"]
    values = chart_data["inventory_trend"]["values"]
    days = chart_data["inventory_trend"]["days"]
    period_end = chart_data["period_end"]

    total_plan = sum(plan)
    total_actual = sum(actual)
    inv_peak_idx = max(range(len(values)), key=lambda i: values[i], default=0)
    inv_latest_idx = max(len(values) - 1, 0)
    inv_sum = sum(values)

    return {
        "total_plan": total_plan,
        "total_actual": total_actual,
        "plan_remaining": total_plan - total_actual,
        "baseline_actual_diff": chart_data.get("baseline_actual_diff"),
        "baseline_diff_date_label": _resolve_baseline_diff_as_of(period_end, run_date),
        "inv_latest": values[inv_latest_idx] if values else 0,
        "inv_latest_date_label": days[inv_latest_idx] if days else period_end,
        "inv_peak": values[inv_peak_idx] if values else 0,
        "inv_peak_label": labels[inv_peak_idx] if labels else "—",
        "inv_avg": round(inv_sum / max(len(values), 1)),
    }


def _inventory_warning(chart_data: dict[str, Any], *, run_date: date) -> str | None:
    days = chart_data["inventory_trend"]["days"]
    values = chart_data["inventory_trend"]["values"]
    today_iso = run_date.isoformat()
    if today_iso not in days:
        return None
    today_inv = values[days.index(today_iso)]
    if today_inv >= INVENTORY_LETTER_LINE:
        return None
    return (
        f"※ 本日在庫（{_fmt_thousand(today_inv)}）がレットライン（{_fmt_thousand(INVENTORY_LETTER_LINE)}）を"
        f"下回り、危険水域です（不足 {_fmt_thousand(INVENTORY_LETTER_LINE - today_inv)}）"
    )


def _drawing_to_png_bytes(drawing: Any, *, dpi: int = 72) -> bytes:
    try:
        from reportlab.graphics import renderPM

        return renderPM.drawToString(drawing, fmt="PNG", dpi=dpi)
    except Exception as exc:
        message = str(exc)
        if "renderPM" in message or "rlPyCairo" in message or "pycairo" in message.lower():
            raise RuntimeError(
                "チャート画像の生成に rlPyCairo / pycairo が必要です。"
                "backend/venv で pip install -r requirements.txt を実行してください。"
            ) from exc
        raise


def _make_drawing_flowable(drawing: Any, width: float, height: float) -> Any:
    from reportlab.platypus import Flowable

    class DrawingFlowable(Flowable):
        def __init__(self) -> None:
            Flowable.__init__(self)
            self.drawing = drawing
            self._width = width
            self._height = height

        def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
            return self._width, self._height

        def draw(self) -> None:
            from reportlab.graphics import renderPDF

            renderPDF.draw(self.drawing, self.canv, 0, 0)

    return DrawingFlowable()


def _fmt_gap_chart_label(gap: float) -> tuple[str, Any]:
    from reportlab.lib import colors

    abs_text = f"{int(abs(gap))}" if abs(gap) == int(abs(gap)) else f"{abs(gap):.1f}"
    if gap > 0:
        return f"-{abs_text}", colors.HexColor("#DC2626")
    if gap < 0:
        return f"+{abs_text}", colors.HexColor("#1D4ED8")
    return "0", colors.HexColor("#1D4ED8")


def _build_inventory_chart_drawing(
    daily: list[dict[str, Any]], *, run_date: date, width: float, height: float
) -> Any:
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics.shapes import Circle, Drawing, Line, String
    from reportlab.lib import colors

    drawing = Drawing(width, height)
    if not daily:
        drawing.add(String(width / 2, height / 2, "データなし", textAnchor="middle", fontSize=9))
        return drawing

    plot_x, plot_y = 40, 30
    plot_w, plot_h = width - 56, height - 52
    values_t = [_to_thousand(d["inventory"]) for d in daily]
    letter_t = _to_thousand(INVENTORY_LETTER_LINE)
    y_max = max(max(values_t, default=0), letter_t, 1) * 1.1

    plot = LinePlot()
    plot.x = plot_x
    plot.y = plot_y
    plot.width = plot_w
    plot.height = plot_h
    plot.data = [[(i, v) for i, v in enumerate(values_t)]]
    plot.lines[0].strokeColor = colors.HexColor(_CHART_PRIMARY)
    plot.lines[0].strokeWidth = 2.5
    plot.lines[0].symbol = None

    plot.xValueAxis.valueMin = 0
    plot.xValueAxis.valueMax = max(len(daily) - 1, 1)
    plot.xValueAxis.visibleGrid = False
    plot.xValueAxis.labels.fontSize = 8
    plot.xValueAxis.labelTextFormat = (
        lambda v: daily[int(v)]["label"] if 0 <= int(v) < len(daily) else ""
    )

    plot.yValueAxis.valueMin = 0
    plot.yValueAxis.valueMax = y_max
    plot.yValueAxis.visibleGrid = True
    plot.yValueAxis.gridStrokeColor = colors.HexColor(_CHART_GRID)
    plot.yValueAxis.labels.fontSize = 8
    drawing.add(plot)

    letter_y = plot_y + plot_h * letter_t / y_max
    drawing.add(
        Line(
            plot_x,
            letter_y,
            plot_x + plot_w,
            letter_y,
            strokeColor=colors.HexColor("#DC2626"),
            strokeWidth=1,
            strokeDashArray=[4, 3],
        )
    )

    today_iso = run_date.isoformat()
    for i, d in enumerate(daily):
        x = plot_x + plot_w * i / max(len(daily) - 1, 1)
        y = plot_y + plot_h * values_t[i] / y_max
        is_today = d["day"] == today_iso
        color = colors.HexColor("#DC2626") if is_today else colors.HexColor(_CHART_PRIMARY)
        radius = 4 if is_today else 2.5
        drawing.add(Circle(x, y, radius, fillColor=color, strokeColor=colors.white, strokeWidth=1))
        label_color = colors.HexColor("#DC2626") if is_today else colors.HexColor("#1E40AF")
        drawing.add(
            String(
                x,
                y + 8,
                _fmt_thousand(d["inventory"]),
                fontSize=7,
                fillColor=label_color,
                textAnchor="middle",
            )
        )

    return drawing


def _build_plan_actual_chart_drawing(
    daily: list[dict[str, Any]], *, width: float, height: float
) -> Any:
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.lib import colors

    drawing = Drawing(width, height)
    if not daily:
        drawing.add(String(width / 2, height / 2, "データなし", textAnchor="middle", fontSize=9))
        return drawing

    chart_x, chart_y = 40, 34
    chart_w, chart_h = width - 56, height - 58
    plan_t = [_to_thousand(d["plan"]) for d in daily]
    actual_t = [_to_thousand(d["actual"]) for d in daily]
    y_max = max(max(plan_t, default=0), max(actual_t, default=0), 1) * 1.15

    chart = VerticalBarChart()
    chart.x = chart_x
    chart.y = chart_y
    chart.width = chart_w
    chart.height = chart_h
    chart.data = [plan_t, actual_t]
    chart.categoryAxis.categoryNames = [d["label"] for d in daily]
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.angle = 40 if len(daily) > 12 else 0
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = y_max
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.visibleGrid = True
    chart.valueAxis.gridStrokeColor = colors.HexColor(_CHART_GRID)
    chart.bars[0].fillColor = colors.HexColor("#93C5FD")
    chart.bars[0].strokeColor = colors.HexColor(_CHART_PRIMARY)
    chart.bars[0].strokeWidth = 0.5
    chart.bars[1].fillColor = colors.HexColor("#6EE7B7")
    chart.bars[1].strokeColor = colors.HexColor(_CHART_ACCENT)
    chart.bars[1].strokeWidth = 0.5
    chart.barSpacing = 6
    chart.groupSpacing = 10
    drawing.add(chart)

    legend_y = height - 12
    drawing.add(Rect(42, legend_y, 10, 6, fillColor=colors.HexColor("#93C5FD"), strokeColor=None))
    drawing.add(String(56, legend_y, "計画", fontSize=8, fillColor=colors.HexColor(_CHART_TEXT)))
    drawing.add(Rect(92, legend_y, 10, 6, fillColor=colors.HexColor("#6EE7B7"), strokeColor=None))
    drawing.add(String(106, legend_y, "実績", fontSize=8, fillColor=colors.HexColor(_CHART_TEXT)))

    n = len(daily)
    for i, d in enumerate(daily):
        gap = _to_thousand(d["plan"] - d["actual"])
        top = max(plan_t[i], actual_t[i])
        x = chart_x + (i + 0.5) * chart_w / n
        y = chart_y + chart_h * top / y_max + 6
        label, color = _fmt_gap_chart_label(gap)
        drawing.add(String(x, y, label, fontSize=7, fillColor=color, textAnchor="middle"))

    return drawing


def _summary_item_html(label: str, value: str, *, value_class: str = "") -> str:
    cls = f" cr-item__value--{value_class}" if value_class else ""
    return (
        f'<div class="cr-item"><span class="cr-item__label">{label}</span>'
        f'<b class="cr-item__value{cls}">{value}</b></div>'
    )


def _build_summary_block_html(stats: dict[str, Any]) -> str:
    plan_remaining = stats["plan_remaining"]
    remaining_cls = "pos" if plan_remaining <= 0 else "neg"
    baseline = stats["baseline_actual_diff"]
    if baseline is None:
        baseline_cls = ""
        baseline_text = "—"
    else:
        baseline_cls = "pos" if baseline >= 0 else "neg"
        baseline_text = _fmt_baseline_diff(baseline)
        if stats["baseline_diff_date_label"]:
            baseline_text += f'<small class="cr-item__sub">（{stats["baseline_diff_date_label"]}）</small>'

    cutting_items = [
        _summary_item_html("計画合計", _fmt_thousand(stats["total_plan"])),
        _summary_item_html("実績合計", _fmt_thousand(stats["total_actual"])),
        _summary_item_html("計画残数", _fmt_plan_remaining(plan_remaining), value_class=remaining_cls),
        _summary_item_html("進捗率", _fmt_progress_rate(stats["total_plan"], stats["total_actual"])),
        _summary_item_html("累計差異", baseline_text, value_class=baseline_cls),
    ]
    inv_latest = _fmt_thousand(stats["inv_latest"])
    if stats["inv_latest_date_label"]:
        inv_latest += f'<small class="cr-item__sub">（{stats["inv_latest_date_label"]}）</small>'
    inv_items = [
        _summary_item_html("期末予測在庫", inv_latest),
        _summary_item_html(
            "期間ピーク",
            f'{_fmt_thousand(stats["inv_peak"])}<small class="cr-item__sub">（{stats["inv_peak_label"]}）</small>',
        ),
        _summary_item_html("期間平均", _fmt_thousand(stats["inv_avg"])),
    ]
    return f"""
<footer class="cr-summary">
  <h4 class="cr-summary__heading">データサマリー（単位: 千）</h4>
  <div class="cr-summary__block">
    <span class="cr-summary__block-title">切断工程</span>
    <div class="cr-summary__grid">{''.join(cutting_items)}</div>
  </div>
  <div class="cr-summary__block">
    <span class="cr-summary__block-title">切断済在庫</span>
    <div class="cr-summary__grid cr-summary__grid--inv">{''.join(inv_items)}</div>
  </div>
</footer>
"""


_PREVIEW_CSS = """
<style>
.cr-preview{font-family:"Hiragino Sans","Yu Gothic","Meiryo",sans-serif;color:#0f172a;max-width:100%;}
.cr-sheet{background:#fff;border:1px solid #e2e8f0;border-radius:4px;padding:20px 24px 18px;}
.cr-head{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:10px;padding-bottom:8px;border-bottom:2px solid #e2e8f0;}
.cr-title{margin:0;font-size:16px;font-weight:700;color:#0f172a;}
.cr-period{margin:0;font-size:12px;color:#64748b;white-space:nowrap;}
.cr-section{margin-bottom:10px;}
.cr-section__title{margin:0 0 6px;font-size:12px;font-weight:600;color:#1e40af;}
.cr-chart-wrap{position:relative;margin-bottom:4px;}
.cr-chart-comment{margin:0 0 4px;padding:4px 8px;font-size:10px;line-height:1.45;font-weight:600;color:#b91c1c;text-align:right;background:#fef2f2;border:1px solid #fecaca;border-radius:4px;}
.cr-chart img{display:block;width:100%;height:auto;border-radius:4px;}
.cr-summary{margin-top:12px;padding-top:10px;border-top:1px solid #e2e8f0;}
.cr-summary__heading{margin:0 0 8px;font-size:11px;font-weight:600;color:#475569;}
.cr-summary__block{margin-bottom:8px;}
.cr-summary__block-title{display:block;font-size:10px;font-weight:600;color:#1e40af;margin-bottom:6px;}
.cr-summary__grid{display:flex;flex-wrap:wrap;gap:8px;}
.cr-summary__grid--inv .cr-item{flex:1 1 30%;}
.cr-item{flex:1 1 18%;min-width:90px;background:linear-gradient(180deg,#f8fafc 0%,#f1f5f9 100%);border:1px solid #e2e8f0;border-radius:6px;padding:8px 10px;text-align:center;}
.cr-item__label{display:block;font-size:9px;color:#64748b;margin-bottom:4px;line-height:1.3;}
.cr-item__value{display:block;font-size:12px;font-weight:600;color:#0f172a;}
.cr-item__value--pos{color:#059669;}
.cr-item__value--neg{color:#dc2626;}
.cr-item__sub{display:block;margin-top:2px;font-size:9px;font-weight:500;color:#94a3b8;}
</style>
"""


def _build_summary_pdf_table(stats: dict[str, Any], font: str, content_w: float) -> Any:
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        "cr_sum_heading",
        parent=styles["Normal"],
        fontName=font,
        fontSize=7,
        textColor=colors.HexColor("#475569"),
        spaceAfter=0,
        leading=9,
    )
    block_style = ParagraphStyle(
        "cr_sum_block",
        parent=styles["Normal"],
        fontName=font,
        fontSize=7,
        textColor=colors.HexColor("#1E40AF"),
        spaceAfter=0,
        leading=9,
    )

    plan_remaining = stats["plan_remaining"]
    baseline = stats["baseline_actual_diff"]
    baseline_text = _fmt_baseline_diff(baseline)
    if stats["baseline_diff_date_label"] and baseline is not None:
        baseline_text += f"\n（{stats['baseline_diff_date_label']}）"
    baseline_color = (
        "#059669"
        if baseline is not None and baseline >= 0
        else "#DC2626" if baseline is not None else "#0F172A"
    )

    inv_latest = _fmt_thousand(stats["inv_latest"])
    if stats["inv_latest_date_label"]:
        inv_latest += f"\n（{stats['inv_latest_date_label']}）"

    cutting_data = [
        ["計画合計", "実績合計", "計画残数", "進捗率", "累計差異"],
        [
            _fmt_thousand(stats["total_plan"]),
            _fmt_thousand(stats["total_actual"]),
            _fmt_plan_remaining(plan_remaining),
            _fmt_progress_rate(stats["total_plan"], stats["total_actual"]),
            baseline_text,
        ],
    ]
    inv_data = [
        ["期末予測在庫", "期間ピーク", "期間平均"],
        [
            inv_latest,
            f"{_fmt_thousand(stats['inv_peak'])}\n（{stats['inv_peak_label']}）",
            _fmt_thousand(stats["inv_avg"]),
        ],
    ]

    col_w_cut = content_w / 5
    t_cut = Table(cutting_data, colWidths=[col_w_cut] * 5)
    t_cut.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, 0), 6),
                ("FONTSIZE", (0, 1), (-1, 1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748B")),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (2, 1), (2, 1), colors.HexColor("#059669" if plan_remaining <= 0 else "#DC2626")),
                ("TEXTCOLOR", (4, 1), (4, 1), colors.HexColor(baseline_color)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F1F5F9")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    col_w_inv = content_w / 3
    t_inv = Table(inv_data, colWidths=[col_w_inv] * 3)
    t_inv.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, 0), 6),
                ("FONTSIZE", (0, 1), (-1, 1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748B")),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#0F172A")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F1F5F9")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    return Table(
        [
            [Paragraph("<b>データサマリー（単位: 千）</b>", heading_style)],
            [Paragraph("<b>切断工程</b>", block_style)],
            [t_cut],
            [Paragraph("<b>切断済在庫</b>", block_style)],
            [t_inv],
        ],
        colWidths=[content_w],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
            ]
        ),
    )


def _build_summary_pdf_flowables(stats: dict[str, Any], font: str, content_w: float) -> list[Any]:
    return [_build_summary_pdf_table(stats, font, content_w)]


def build_cutting_preview_html(
    period_label: str,
    daily: list[dict[str, Any]],
    chart_data: dict[str, Any],
    *,
    run_date: date,
    chart_width: float = 920,
    chart_height: float = 220,
) -> str:
    if not daily:
        return "<p>対象期間にデータはありません。</p>"

    stats = _compute_summary_stats(chart_data, run_date=run_date)
    warning = _inventory_warning(chart_data, run_date=run_date)
    letter_line_label = _fmt_thousand(INVENTORY_LETTER_LINE)

    inv_png = base64.b64encode(
        _drawing_to_png_bytes(
            _build_inventory_chart_drawing(daily, run_date=run_date, width=chart_width, height=chart_height),
            dpi=CHART_EMAIL_RENDER_DPI,
        )
    ).decode("ascii")
    pa_png = base64.b64encode(
        _drawing_to_png_bytes(
            _build_plan_actual_chart_drawing(daily, width=chart_width, height=chart_height),
            dpi=CHART_EMAIL_RENDER_DPI,
        )
    ).decode("ascii")

    warning_html = f'<p class="cr-chart-comment">{warning}</p>' if warning else ""
    return f"""{_PREVIEW_CSS}
<div class="cr-preview">
  <div class="cr-sheet">
    <header class="cr-head">
      <h3 class="cr-title">切断工程実績レポート</h3>
      <p class="cr-period">対象期間: {period_label}</p>
    </header>
    <section class="cr-section">
      <h4 class="cr-section__title">切断済在庫推移（日次・単位: 千・レットライン在庫: {letter_line_label}）</h4>
      <div class="cr-chart-wrap">
        {warning_html}
        <div class="cr-chart"><img src="data:image/png;base64,{inv_png}" alt="切断済在庫推移" /></div>
      </div>
    </section>
    <section class="cr-section">
      <h4 class="cr-section__title">切断工程 計画 vs 実績（日次・単位: 千・計画&gt;実績は赤−／実績&gt;計画は青+）</h4>
      <div class="cr-chart"><img src="data:image/png;base64,{pa_png}" alt="切断工程 計画 vs 実績" /></div>
    </section>
    {_build_summary_block_html(stats)}
  </div>
</div>
"""


def build_cutting_preview_text(
    period_label: str,
    daily: list[dict[str, Any]],
    chart_data: dict[str, Any],
    *,
    run_date: date,
) -> str:
    if not daily:
        return "対象期間にデータはありません。"
    stats = _compute_summary_stats(chart_data, run_date=run_date)
    warning = _inventory_warning(chart_data, run_date=run_date)
    lines = [
        "切断工程実績レポート",
        f"対象期間: {period_label}",
        "",
        "【切断工程】（単位: 千）",
        f"計画合計: {_fmt_thousand(stats['total_plan'])}",
        f"実績合計: {_fmt_thousand(stats['total_actual'])}",
        f"計画残数: {_fmt_plan_remaining(stats['plan_remaining'])}",
        f"進捗率: {_fmt_progress_rate(stats['total_plan'], stats['total_actual'])}",
        f"累計差異: {_fmt_baseline_diff(stats['baseline_actual_diff'])}",
        "",
        "【切断済在庫】（単位: 千）",
        f"期末予測在庫: {_fmt_thousand(stats['inv_latest'])}（{stats['inv_latest_date_label']}）",
        f"期間ピーク: {_fmt_thousand(stats['inv_peak'])}（{stats['inv_peak_label']}）",
        f"期間平均: {_fmt_thousand(stats['inv_avg'])}",
    ]
    if warning:
        lines.insert(3, warning)
    return "\n".join(lines)


def build_cutting_report_pdf(
    title: str,
    period_label: str,
    daily: list[dict[str, Any]],
    chart_data: dict[str, Any],
    *,
    run_date: date,
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

    font = _ensure_jp_font()
    page_size = landscape(A4)
    page_w, page_h = page_size
    margin_h = 10 * mm
    margin_v = 8 * mm
    content_w = page_w - 2 * margin_h
    usable_h = page_h - 2 * margin_v

    letter_line_label = _fmt_thousand(INVENTORY_LETTER_LINE)
    warning = _inventory_warning(chart_data, run_date=run_date)
    stats = _compute_summary_stats(chart_data, run_date=run_date)

    # 1ページに収めるための高さ配分（プレビューと同型）
    header_h = 9 * mm
    sec_title_h = 4.5 * mm
    warning_h = 7 * mm if warning else 0
    summary_h = 30 * mm
    gap_h = 4 * mm
    chart_h = (usable_h - header_h - 2 * sec_title_h - warning_h - summary_h - gap_h) / 2
    chart_h = max(min(chart_h, 62 * mm), 42 * mm)

    inv_drawing = _build_inventory_chart_drawing(
        daily, run_date=run_date, width=content_w, height=chart_h
    )
    pa_drawing = _build_plan_actual_chart_drawing(daily, width=content_w, height=chart_h)
    inv_chart = _make_drawing_flowable(inv_drawing, content_w, chart_h)
    pa_chart = _make_drawing_flowable(pa_drawing, content_w, chart_h)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "cr_title",
        parent=styles["Title"],
        fontName=font,
        fontSize=14,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=0,
        leading=16,
    )
    period_style = ParagraphStyle(
        "cr_period",
        parent=styles["Normal"],
        fontName=font,
        fontSize=9,
        textColor=colors.HexColor("#64748B"),
        alignment=2,
        spaceAfter=0,
        leading=11,
    )
    section_style = ParagraphStyle(
        "cr_section",
        parent=styles["Heading2"],
        fontName=font,
        fontSize=8,
        textColor=colors.HexColor("#1E40AF"),
        spaceBefore=0,
        spaceAfter=2,
        leading=10,
    )
    warning_style = ParagraphStyle(
        "cr_warning",
        parent=styles["Normal"],
        fontName=font,
        fontSize=6.5,
        textColor=colors.HexColor("#B91C1C"),
        alignment=2,
        spaceAfter=0,
        leading=8,
    )

    header = Table(
        [
            [
                Paragraph(title, title_style),
                Paragraph(f"対象期間: {period_label}", period_style),
            ]
        ],
        colWidths=[content_w * 0.62, content_w * 0.38],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor("#E2E8F0")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    summary_tbl = _build_summary_pdf_table(stats, font, content_w)

    sheet_rows: list[list[Any]] = [
        [header],
        [
            Paragraph(
                f"切断済在庫推移（日次・単位: 千・レットライン在庫: {letter_line_label}）",
                section_style,
            )
        ],
    ]
    if warning:
        sheet_rows.append([Paragraph(warning, warning_style)])
    sheet_rows.extend(
        [
            [inv_chart],
            [
                Paragraph(
                    "切断工程 計画 vs 実績（日次・単位: 千・計画&gt;実績は赤−／実績&gt;計画は青+）",
                    section_style,
                )
            ],
            [pa_chart],
            [summary_tbl],
        ]
    )

    sheet = Table(sheet_rows, colWidths=[content_w])
    sheet.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        topMargin=margin_v,
        bottomMargin=margin_v,
        leftMargin=margin_h,
        rightMargin=margin_h,
    )
    doc.build([sheet])
    return buffer.getvalue()

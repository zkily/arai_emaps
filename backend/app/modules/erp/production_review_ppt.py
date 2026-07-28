"""生産検討会資料 PPT 生成（PART 01〜03）"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

_TEMPLATE_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "templates" / "production_review_template.pptx",
    Path(__file__).resolve().parents[3] / "7月生産検討会資料.pptx",
    Path(r"\\192.168.1.200\生産管理部\生産管理システム\9.生産検討会資料\2026年度\7月生産検討会.pptx"),
)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _find_template() -> Optional[Path]:
    for p in _TEMPLATE_CANDIDATES:
        if p.is_file():
            return p
    return None


def _fmt_th(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _fmt_delta(value: Any, digits: int = 1) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "-"
    if v > 0:
        return f"{v:.{digits}f}"
    if v < 0:
        return f"△{abs(v):.{digits}f}"
    return f"{v:.{digits}f}"


def _fmt_prod_delta(value: Any) -> str:
    try:
        v = int(round(float(value)))
    except (TypeError, ValueError):
        return "-"
    if v > 0:
        return f"+{v}"
    if v < 0:
        return f"△{abs(v)}"
    return "+0"


def _set_title(slide, title: str, subtitle: str = "") -> None:
    if slide.shapes.title:
        slide.shapes.title.text = title
    if len(slide.placeholders) > 1:
        slide.placeholders[1].text = subtitle


def _add_blank_slide(prs: Presentation):
    layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]
    return prs.slides.add_slide(layout)


def _add_textbox(slide, left, top, width, height, text, *, font_size=18, bold=False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.alignment = align
    return box


def _add_table(slide, rows: List[List[str]], left, top, width, height):
    table_shape = slide.shapes.add_table(len(rows), len(rows[0]), left, top, width, height)
    table = table_shape.table
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = str(val)
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(10 if r_idx else 11)
                paragraph.font.bold = r_idx == 0
    return table


def _build_cover(prs: Presentation, meta: Dict[str, Any]) -> None:
    slide = _add_blank_slide(prs)
    meeting_date = meta.get("meeting_date", "")
    if meeting_date:
        try:
            y, m, d = meeting_date.split("-")
            date_label = f"{y}年{int(m)}月{int(d)}日"
        except ValueError:
            date_label = meeting_date
    else:
        date_label = ""
    _add_textbox(
        slide,
        Inches(3.5),
        Inches(2.5),
        Inches(6),
        Inches(1),
        meta.get("title") or "生産検討会",
        font_size=36,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    _add_textbox(
        slide,
        Inches(2.5),
        Inches(3.6),
        Inches(8),
        Inches(0.6),
        meta.get("subtitle") or "",
        font_size=14,
        align=PP_ALIGN.CENTER,
    )
    _add_textbox(slide, Inches(5.2), Inches(4.5), Inches(3), Inches(0.3), date_label, font_size=12)
    _add_textbox(slide, Inches(6.9), Inches(4.5), Inches(2), Inches(0.3), "生産管理部", font_size=12)


def _build_section_divider(prs: Presentation, title: str, subtitle: str) -> None:
    slide = _add_blank_slide(prs)
    _add_textbox(slide, Inches(2.5), Inches(3.0), Inches(8), Inches(0.8), title, font_size=28, bold=True, align=PP_ALIGN.CENTER)
    _add_textbox(slide, Inches(2.5), Inches(4.0), Inches(8), Inches(0.5), subtitle, font_size=14, align=PP_ALIGN.CENTER)


def _build_performance_slide(prs: Presentation, performance: Dict[str, Any]) -> None:
    slide = _add_blank_slide(prs)
    _add_textbox(
        slide,
        Inches(0.8),
        Inches(0.4),
        Inches(8),
        Inches(0.5),
        f"{performance.get('month_label', '')} 工程別実績一覧",
        font_size=22,
        bold=True,
    )
    header = [
        "工程名",
        "工程計画",
        "実見",
        "実績",
        "対実見",
        "対計画",
        "前月生産性",
        "当月生産性",
        "増減",
    ]
    body = [header]
    for row in performance.get("rows") or []:
        body.append(
            [
                row.get("name", ""),
                _fmt_th(row.get("plan_th")),
                _fmt_th(row.get("forecast_th")),
                _fmt_th(row.get("actual_th")),
                _fmt_delta(row.get("vs_forecast_th")),
                _fmt_delta(row.get("vs_plan_th")),
                str(row.get("productivity_prev") if row.get("productivity_prev") is not None else "-"),
                str(row.get("productivity_curr") if row.get("productivity_curr") is not None else "-"),
                _fmt_prod_delta(row.get("productivity_delta"))
                if row.get("productivity_delta") is not None
                else "-",
            ]
        )
    _add_table(slide, body, Inches(0.7), Inches(1.1), Inches(12), Inches(3.8))
    comments = performance.get("comments") or []
    y = 5.2
    for c in comments[:3]:
        _add_textbox(slide, Inches(0.9), Inches(y), Inches(11.5), Inches(0.35), f"■ {c}", font_size=11)
        y += 0.45


def _build_scrap_slide(prs: Presentation, scrap: Dict[str, Any]) -> None:
    slide = _add_blank_slide(prs)
    _add_textbox(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.5), "廃棄率及び廃棄本数", font_size=22, bold=True)
    monthly = scrap.get("monthly") or []
    if monthly:
        chart_data = CategoryChartData()
        labels = [f"{m['month']}月" for m in monthly[-12:]]
        chart_data.categories = labels
        chart_data.add_series("廃棄率（新）(%)", [m.get("rate_new_pct", 0) for m in monthly[-12:]])
        chart_data.add_series("廃棄率（旧）(%)", [m.get("rate_old_pct", m.get("rate_pct", 0)) for m in monthly[-12:]])
        slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            Inches(0.4),
            Inches(1.2),
            Inches(6),
            Inches(3.2),
            chart_data,
        )
        chart_data2 = CategoryChartData()
        chart_data2.categories = labels
        chart_data2.add_series("廃棄本数(千本)", [m.get("loss_th", m.get("scrap_th", 0)) for m in monthly[-12:]])
        slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            Inches(6.8),
            Inches(1.2),
            Inches(6),
            Inches(3.2),
            chart_data2,
        )
    summary = (
        f"{scrap.get('fiscal_year_label', '')} 月平均廃棄率（新） {scrap.get('avg_rate_new_current_fy_pct', 0):.2f} %\n"
        f"前年度 月平均廃棄率（新） {scrap.get('avg_rate_new_prev_fy_pct', 0):.2f} %\n"
        f"{scrap.get('fiscal_year_label', '')} 月平均廃棄率（旧） {scrap.get('avg_rate_old_current_fy_pct', 0):.2f} %\n"
        f"前年度 月平均廃棄率（旧） {scrap.get('avg_rate_old_prev_fy_pct', 0):.2f} %\n"
        f"当月廃棄本数 {int(scrap.get('current_month_loss_qty', 0)):,} 本"
    )
    _add_textbox(slide, Inches(0.8), Inches(4.6), Inches(5.5), Inches(1.5), summary, font_size=12)
    comments = scrap.get("comments") or []
    if comments:
        _add_textbox(slide, Inches(6.8), Inches(4.6), Inches(5.8), Inches(1.2), "\n".join(comments), font_size=11)


def _build_inventory_slide(prs: Presentation, inv: Dict[str, Any], title_suffix: str = "") -> None:
    slide = _add_blank_slide(prs)
    title = f"{inv.get('inventory_month_label', '')}時点の在庫高{title_suffix}"
    _add_textbox(slide, Inches(0.8), Inches(0.4), Inches(10), Inches(0.5), title, font_size=22, bold=True)
    header_line = (
        f"{inv.get('prev_forecast_label', '')}出荷内示：{_fmt_th(inv.get('prev_forecast_th'))} 千本 | "
        f"{inv.get('curr_forecast_label', '')}出荷内示：{_fmt_th(inv.get('curr_forecast_th'))} 千本"
    )
    _add_textbox(slide, Inches(0.8), Inches(0.95), Inches(11), Inches(0.3), header_line, font_size=11)
    header = ["工程名", "前月在庫高(千本)", "前月補正率", "当月在庫高(千本)", "当月補正率", "増減(千本)"]
    body = [header]
    for row in inv.get("rows") or []:
        body.append(
            [
                row.get("name", ""),
                _fmt_th(row.get("prev_inventory_th")),
                f"{float(row.get('prev_rate_adj', row.get('prev_rate', 0)) or 0):.2f}",
                _fmt_th(row.get("curr_inventory_th")),
                f"{float(row.get('curr_rate_adj', row.get('curr_rate', 0)) or 0):.2f}",
                _fmt_delta(row.get("delta_th")),
            ]
        )
    _add_table(slide, body, Inches(0.7), Inches(1.3), Inches(12), Inches(3.5))
    comments = inv.get("comments") or []
    y = 5.0
    for c in comments[:3]:
        _add_textbox(slide, Inches(0.9), Inches(y), Inches(11.5), Inches(0.35), f"■ {c}", font_size=11)
        y += 0.45


def _build_load_plan_slide(prs: Presentation, load_plan: Dict[str, Any]) -> None:
    slide = _add_blank_slide(prs)
    wd = load_plan.get("working_days", 0)
    header = (
        f"{load_plan.get('month_label', '')}稼働日：{wd}日 | "
        f"内示：{_fmt_th(load_plan.get('forecast_th'))} 千本 "
        f"(日当たり：{_fmt_th(load_plan.get('daily_forecast_th'))} 千本)"
    )
    _add_textbox(
        slide,
        Inches(0.8),
        Inches(0.4),
        Inches(12),
        Inches(0.5),
        f"{load_plan.get('month_label', '')} 生産計画と工程負荷予測",
        font_size=22,
        bold=True,
    )
    _add_textbox(slide, Inches(0.8), Inches(0.95), Inches(12), Inches(0.3), header, font_size=11)
    header_row = [
        "工程",
        "工程計画",
        "日当たり",
        "設備・人員",
        "標準能率",
        "稼働直",
        "定時H",
        "所要H",
        "負荷率",
        "日均稼働",
    ]
    body = [header_row]
    for row in load_plan.get("rows") or []:
        body.append(
            [
                row.get("process_name", ""),
                _fmt_th(row.get("plan_th")),
                _fmt_th(row.get("daily_th")),
                row.get("equipment_label", ""),
                str(row.get("standard_rate", "")),
                row.get("shift_label", ""),
                str(row.get("regular_hours", "")),
                str(row.get("required_hours", "")),
                f"{row.get('load_rate_pct', 0)}%",
                str(row.get("daily_operation_hours", "")),
            ]
        )
    _add_table(slide, body, Inches(0.5), Inches(1.3), Inches(12.3), Inches(3.2))
    y = 4.7
    for row in load_plan.get("rows") or []:
        if int(row.get("load_rate_pct") or 0) < 90:
            continue
        daily_th = row.get("daily_th")
        max_monthly = row.get("max_monthly_th")
        text = (
            f"{row.get('process_name')}（負荷率：{row.get('load_rate_pct')}%）"
            f" 日当たり{daily_th}千本"
            f"／月間最大{_fmt_th(max_monthly)}千本"
        )
        _add_textbox(slide, Inches(0.6), Inches(y), Inches(12.2), Inches(0.35), text, font_size=9)
        y += 0.32
        if y > 6.8:
            break


def _fill_from_template(prs: Presentation, data: Dict[str, Any]) -> bytes:
    """テンプレートがある場合、既知スライド位置にテキストを差し込む（簡易）。"""
    meta = data.get("meta") or {}
    part01 = data.get("part01") or {}
    part02 = data.get("part02") or {}
    part03 = data.get("part03") or {}

    if len(prs.slides) >= 1:
        s0 = prs.slides[0]
        for shape in s0.shapes:
            if not shape.has_text_frame:
                continue
            t = shape.text_frame.text
            if "月度" in t and "生産検討会" in t:
                shape.text_frame.text = meta.get("title") or t
            elif "各工程" in t:
                shape.text_frame.text = meta.get("subtitle") or t

    # スライド3: 工程別実績
    if len(prs.slides) >= 3:
        perf = part01.get("performance") or {}
        slide = prs.slides[2]
        for shape in slide.shapes:
            if shape.shape_type == 19:  # TABLE
                table = shape.table
                rows = perf.get("rows") or []
                for r_idx, row in enumerate(rows, start=1):
                    if r_idx >= len(table.rows):
                        break
                    cells = table.rows[r_idx].cells
                    if len(cells) >= 9:
                        cells[1].text = _fmt_th(row.get("plan_th"))
                        cells[2].text = _fmt_th(row.get("forecast_th"))
                        cells[3].text = _fmt_th(row.get("actual_th"))
                        cells[4].text = _fmt_delta(row.get("vs_forecast_th"))
                        cells[5].text = _fmt_delta(row.get("vs_plan_th"))
                        cells[6].text = str(row.get("productivity_prev") or "-")
                        cells[7].text = str(row.get("productivity_curr") or "-")
                        cells[8].text = (
                            _fmt_prod_delta(row.get("productivity_delta"))
                            if row.get("productivity_delta") is not None
                            else "-"
                        )
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def build_production_review_pptx(data: Dict[str, Any]) -> bytes:
    template = _find_template()
    if template:
        prs = Presentation(str(template))
        return _fill_from_template(prs, data)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    meta = data.get("meta") or {}
    part01 = data.get("part01") or {}
    part02 = data.get("part02") or {}
    part03 = data.get("part03") or {}

    _build_cover(prs, meta)
    _build_section_divider(prs, part01.get("title", ""), part01.get("subtitle", ""))
    _build_performance_slide(prs, part01.get("performance") or {})
    _build_scrap_slide(prs, part01.get("scrap") or {})
    _build_inventory_slide(prs, part01.get("inventory") or {}, "および仕掛品状況")

    _build_section_divider(prs, part02.get("title", ""), part02.get("subtitle", ""))
    _build_load_plan_slide(prs, part02.get("load_plan") or {})
    _build_inventory_slide(prs, part02.get("inventory_forecast") or {}, "の在庫予測")

    _build_section_divider(prs, part03.get("title", ""), part03.get("subtitle", ""))
    _build_load_plan_slide(prs, part03.get("load_plan") or {})

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()

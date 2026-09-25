"""生産計画ベースライン比較レポート（週次定時配信用 PDF）

画面「レポート生成」と同じ HTML 構成を Chrome/Edge headless で PDF 化する。
ブラウザが無い場合は reportlab フォールバック。
"""
from __future__ import annotations

import calendar
import html
import io
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst

from .base import (
    PDF_MIME,
    XLSX_MIME,
    GeneratedReport,
    ReportAttachment,
    ReportGenerator,
    build_xlsx,
    resolve_month,
)

REPORT_CODE = "PLAN_BASELINE_WEEKLY"

_PROCESS_ORDER = ("切断", "面取", "成型", "メッキ", "溶接", "溶接SP", "検査")
_EXCLUDED_PROCESSES = {
    "溶接前検査",
    "外注検査前",
    "外注支給前",
    "外注支給前工程",
    "外注メッキ",
    "外注溶接",
}
_PROCESS_TONES = {
    "切断": "#2563eb",
    "面取": "#16a34a",
    "成型": "#d97706",
    "メッキ": "#dc2626",
    "溶接": "#0284c7",
    "溶接SP": "#7c3aed",
    "検査": "#0d9488",
}
_WEEKDAY_LABELS = ("日", "月", "火", "水", "木", "金", "土")
_JP_FONT = (
    '"Yu Gothic UI","Yu Gothic","Hiragino Sans","Hiragino Kaku Gothic ProN",'
    '"Meiryo","MS PGothic",sans-serif'
)


class PlanBaselineWeeklyGenerator(ReportGenerator):
    report_code = REPORT_CODE

    async def generate(
        self,
        db: AsyncSession,
        *,
        parameters: dict[str, Any],
        fmt: str,
        run_date: date,
    ) -> GeneratedReport:
        from app.modules.plan_baseline.api import build_plan_baseline_comparison

        month_start = resolve_month(parameters, run_date=run_date)
        baseline_month = month_start.isoformat()
        period_label = month_start.strftime("%Y年%m月")
        generated_at = now_jst().strftime("%Y/%m/%d %H:%M")
        last_day = calendar.monthrange(month_start.year, month_start.month)[1]
        month_end = month_start.replace(day=last_day)
        as_of_date = min(run_date, month_end)

        comparison = await build_plan_baseline_comparison(
            db, baseline_month=baseline_month, process_name=None
        )
        items = list(comparison.get("items") or [])
        by_process: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in items:
            name = (row.get("process_name") or "").strip()
            if not name or name in _EXCLUDED_PROCESSES:
                continue
            by_process[name].append(row)

        ordered_names = [n for n in _PROCESS_ORDER if by_process.get(n)]
        for name in sorted(by_process.keys()):
            if name not in ordered_names:
                ordered_names.append(name)

        process_summaries: list[dict[str, Any]] = []
        for name in ordered_names:
            rows = sorted(by_process[name], key=lambda r: str(r.get("plan_date") or ""))
            baseline = sum(float(r.get("baseline_plan") or 0) for r in rows)
            current_plan = sum(float(r.get("current_plan") or 0) for r in rows)
            current_actual = sum(
                float(r["current_actual"]) for r in rows if r.get("current_actual") is not None
            )
            plan_diff = current_plan - baseline
            actual_diff = sum(
                float(r["actual_diff"]) for r in rows if r.get("actual_diff") is not None
            )
            has_actual = any(r.get("current_actual") is not None for r in rows)
            rate = (current_actual / current_plan * 100) if current_plan else None
            process_summaries.append(
                {
                    "name": name,
                    "rows": rows,
                    "baseline": baseline,
                    "current_plan": current_plan,
                    "plan_diff": plan_diff,
                    "current_actual": current_actual if has_actual else None,
                    "actual_diff": actual_diff if has_actual else None,
                    "rate": round(rate, 1) if rate is not None else None,
                }
            )

        # メール本文用：月初〜送信日までの工程別集計
        as_of_summaries = _summarize_processes_as_of(by_process, ordered_names, as_of_date)
        as_of_label = as_of_date.strftime("%Y年%m月%d日")
        as_of_short = f"{as_of_date.month}/{as_of_date.day}"
        period_range_label = f"{month_start.strftime('%Y年%m月%d日')}〜{as_of_label}"
        summary_html = _build_summary_html(
            period_label, as_of_summaries, period_range_label, as_of_short
        )
        summary_text = _build_summary_text(
            period_label, as_of_summaries, period_range_label, as_of_short
        )
        record_count = sum(
            1 for i in items if (i.get("process_name") or "") not in _EXCLUDED_PROCESSES
        )

        sheets = _build_sheets(process_summaries)
        base_name = f"生産計画ベースライン_{month_start.strftime('%Y-%m')}"
        attachments: list[ReportAttachment] = []
        if fmt in ("xlsx", "both"):
            attachments.append(
                ReportAttachment(f"{base_name}.xlsx", build_xlsx(sheets), XLSX_MIME)
            )
        if fmt in ("pdf", "both"):
            attachments.append(
                ReportAttachment(
                    f"{base_name}.pdf",
                    _build_baseline_pdf(
                        period_label=period_label,
                        month_start=month_start,
                        generated_at=generated_at,
                        summaries=process_summaries,
                    ),
                    PDF_MIME,
                )
            )

        return GeneratedReport(
            period_label=period_label,
            record_count=record_count,
            summary_html=summary_html,
            summary_text=summary_text,
            attachments=attachments,
        )

    def reference_key(self, *, parameters: dict[str, Any], run_date: date) -> str:
        month_start = resolve_month(parameters, run_date=run_date)
        return f"{self.report_code}:{month_start.isoformat()}"


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _fmt_num(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{int(round(value)):,}"


def _fmt_num_signed_html(value: float | None) -> str:
    """正数は緑・負数は赤（メール HTML 用）。"""
    if value is None:
        return "—"
    text = f"{int(round(value)):,}"
    n = float(value)
    if n > 0:
        return f'<span style="color:#16a34a;font-weight:600;">{text}</span>'
    if n < 0:
        return f'<span style="color:#dc2626;font-weight:600;">{text}</span>'
    return text


def _fmt_rate(rate: float | None) -> str:
    return f"{rate:.1f}%" if rate is not None else "—"


def _tone(name: str) -> str:
    return _PROCESS_TONES.get(name, "#64748b")


def _summarize_processes_as_of(
    by_process: dict[str, list[dict[str, Any]]],
    ordered_names: list[str],
    as_of: date,
) -> list[dict[str, Any]]:
    """工程別集計。

    - baseline_month: 当月全日の基準計画合計（表①）
    - baseline_period: 月初〜送信日の基準計画合計（表②）
    - current_actual / progress_rate / diff: 実績は送信日まで。差異＝実績−基準計画（期間）
    """
    as_of_s = as_of.isoformat()
    summaries: list[dict[str, Any]] = []
    for name in ordered_names:
        all_rows = by_process.get(name) or []
        period_rows = [
            r for r in all_rows if str(r.get("plan_date") or "")[:10] <= as_of_s
        ]
        baseline_month = sum(float(r.get("baseline_plan") or 0) for r in all_rows)
        baseline_period = sum(float(r.get("baseline_plan") or 0) for r in period_rows)
        has_actual = any(r.get("current_actual") is not None for r in period_rows)
        actual_sum = sum(
            float(r["current_actual"])
            for r in period_rows
            if r.get("current_actual") is not None
        )
        actual = actual_sum if has_actual else None
        # 差異 = 実績 − 基準計画（期間）
        diff = (actual - baseline_period) if actual is not None else None
        # 進捗率 = 送信日までの実績 ÷ 当月基準計画（月全体）
        progress = (
            (actual / baseline_month * 100) if actual is not None and baseline_month else None
        )
        summaries.append(
            {
                "name": name,
                "baseline_month": baseline_month,
                "baseline_period": baseline_period,
                "current_actual": actual,
                "diff": diff,
                "progress_rate": round(progress, 1) if progress is not None else None,
            }
        )
    return summaries


def _build_summary_html(
    period_label: str,
    summaries: list[dict[str, Any]],
    period_range_label: str,
    as_of_label: str,
) -> str:
    if not summaries:
        return (
            f"<p>{_esc(period_label)}（{_esc(period_range_label)}）の"
            "ベースライン比較データがありません。</p>"
        )
    baseline_period_header = f"{as_of_label}までの計画合計"
    progress_body = "".join(
        "<tr>"
        f"<td>{_esc(s['name'])}</td>"
        f"<td align='right'>{_fmt_num(s['baseline_month'])}</td>"
        f"<td align='right'>{_fmt_num(s['current_actual'])}</td>"
        f"<td align='right'>{_fmt_rate(s['progress_rate'])}</td>"
        "</tr>"
        for s in summaries
    )
    diff_body = "".join(
        "<tr>"
        f"<td>{_esc(s['name'])}</td>"
        f"<td align='right'>{_fmt_num(s['baseline_period'])}</td>"
        f"<td align='right'>{_fmt_num(s['current_actual'])}</td>"
        f"<td align='right'>{_fmt_num_signed_html(s['diff'])}</td>"
        "</tr>"
        for s in summaries
    )
    return (
        f"<p>生産計画ベースライン（{_esc(period_label)}）:</p>"
        "<p style='margin:10px 0 4px;font-weight:600;'>"
        "① 工程別　基準計画／実績／進捗率"
        f"<span style='font-weight:400;color:#64748b;'>（基準計画＝{_esc(period_label)}月全体、"
        f"実績＝{_esc(period_range_label)}）</span></p>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>工程</th><th>基準計画</th><th>実績</th><th>進捗率</th></tr>"
        f"{progress_body}</table>"
        "<p style='margin:14px 0 4px;font-weight:600;'>"
        "② 工程別　基準計画合計／実績／差異（実績−基準計画）"
        f"<span style='font-weight:400;color:#64748b;'>（{_esc(period_range_label)}）</span></p>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        f"<tr><th>工程</th><th>{_esc(baseline_period_header)}</th><th>実績</th><th>差異</th></tr>"
        f"{diff_body}</table>"
        "<p style='margin-top:8px;font-size:12px;color:#64748b;'>"
        "詳細は添付PDFをご確認ください。</p>"
    )


def _build_summary_text(
    period_label: str,
    summaries: list[dict[str, Any]],
    period_range_label: str,
    as_of_label: str,
) -> str:
    if not summaries:
        return f"{period_label}（{period_range_label}）のベースライン比較データがありません。"
    baseline_period_header = f"{as_of_label}までの計画合計"
    progress_lines = [
        f"  {s['name']}: 基準(月全体) {_fmt_num(s['baseline_month'])} / "
        f"実績 {_fmt_num(s['current_actual'])} / 進捗率 {_fmt_rate(s['progress_rate'])}"
        for s in summaries
    ]
    diff_lines = [
        f"  {s['name']}: {baseline_period_header} {_fmt_num(s['baseline_period'])} / "
        f"実績 {_fmt_num(s['current_actual'])} / 差異 {_fmt_num(s['diff'])}"
        for s in summaries
    ]
    return (
        f"生産計画ベースライン（{period_label}）:\n"
        f"① 工程別 基準計画／実績／進捗率（基準計画＝{period_label}月全体、実績＝{period_range_label}）:\n"
        + "\n".join(progress_lines)
        + f"\n② 工程別 {baseline_period_header}／実績／差異（{period_range_label}、実績−基準計画）:\n"
        + "\n".join(diff_lines)
    )


def _build_sheets(summaries: list[dict[str, Any]]) -> list[tuple[str, list[str], list[list]]]:
    summary_headers = ["工程", "基準計画", "変更計画", "計画差異", "実績", "対実績差", "達成率(%)"]
    summary_rows = [
        [
            s["name"],
            int(round(s["baseline"])),
            int(round(s["current_plan"])),
            int(round(s["plan_diff"])),
            int(round(s["current_actual"])) if s["current_actual"] is not None else "",
            int(round(s["actual_diff"])) if s["actual_diff"] is not None else "",
            s["rate"] if s["rate"] is not None else "",
        ]
        for s in summaries
    ]
    sheets: list[tuple[str, list[str], list[list]]] = [("工程サマリー", summary_headers, summary_rows)]
    detail_headers = ["日付", "工程", "基準計画", "変更計画", "計画差異", "実績", "対実績差"]
    detail_rows: list[list] = []
    for s in summaries:
        for r in s["rows"]:
            detail_rows.append(
                [
                    str(r.get("plan_date") or "")[:10],
                    s["name"],
                    int(round(float(r.get("baseline_plan") or 0))),
                    int(round(float(r.get("current_plan") or 0))),
                    int(round(float(r.get("plan_diff") or 0))),
                    int(round(float(r["current_actual"]))) if r.get("current_actual") is not None else "",
                    int(round(float(r["actual_diff"]))) if r.get("actual_diff") is not None else "",
                ]
            )
    sheets.append(("日別明細", detail_headers, detail_rows))
    return sheets


# ---------- HTML（画面レポート生成と同構成） ----------


def _detail_table_html(rows: list[dict[str, Any]]) -> str:
    thead = (
        "<thead><tr>"
        "<th>日付</th><th>基準計画</th><th>変更計画</th>"
        "<th>計画差異</th><th>実績</th><th>計画対実績差</th>"
        "</tr></thead>"
    )
    body_rows = []
    for idx, row in enumerate(rows):
        bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
        plan_diff = row.get("plan_diff")
        actual_diff = row.get("actual_diff")
        plan_cls = "neg" if plan_diff is not None and float(plan_diff) < 0 else ""
        act_cls = "neg" if actual_diff is not None and float(actual_diff) < 0 else ""
        body_rows.append(
            f"<tr style='background:{bg}'>"
            f"<td class='date'>{_esc(str(row.get('plan_date') or '')[:10])}</td>"
            f"<td class='num'>{_fmt_num(float(row.get('baseline_plan') or 0))}</td>"
            f"<td class='num'>{_fmt_num(float(row.get('current_plan') or 0))}</td>"
            f"<td class='num {plan_cls}'>{_fmt_num(float(plan_diff or 0))}</td>"
            f"<td class='num'>"
            f"{_fmt_num(float(row['current_actual'])) if row.get('current_actual') is not None else '—'}"
            f"</td>"
            f"<td class='num {act_cls}'>"
            f"{_fmt_num(float(actual_diff)) if actual_diff is not None else '—'}"
            f"</td></tr>"
        )
    if not body_rows:
        body_rows.append("<tr><td colspan='6' class='empty'>データなし</td></tr>")
    return f"<table class='detail'>{thead}<tbody>{''.join(body_rows)}</tbody></table>"


def _two_col_detail_html(s: dict[str, Any]) -> str:
    rows = s["rows"]
    mid = (len(rows) + 1) // 2
    left = rows[:mid]
    right = rows[mid:]
    totals = (
        "<div class='totals'>"
        f"<div class='totals-label'>合計</div>"
        f"<div>基準 <b>{_fmt_num(s['baseline'])}</b></div>"
        f"<div>変更計画 <b>{_fmt_num(s['current_plan'])}</b></div>"
        f"<div class=\"{'neg' if (s['plan_diff'] or 0) < 0 else 'pos'}\">計画差 <b>{_fmt_num(s['plan_diff'])}</b></div>"
        f"<div>実績 <b>{_fmt_num(s['current_actual'])}</b></div>"
        f"<div class=\"{'neg' if (s.get('actual_diff') or 0) < 0 else 'pos'}\">対実績差 <b>{_fmt_num(s['actual_diff'])}</b></div>"
        "</div>"
    )
    return (
        "<div class='detail-grid'>"
        f"<div>{_detail_table_html(left)}</div>"
        f"<div>{_detail_table_html(right) if right else _detail_table_html([])}</div>"
        f"</div>{totals}"
    )


def _metric_value(row: dict[str, Any], metric: str) -> float | None:
    if metric == "achievement":
        plan = float(row.get("current_plan") or 0)
        if row.get("current_actual") is None or plan == 0:
            return None
        return float(row["current_actual"]) / plan * 100
    if metric == "actualDiff":
        if row.get("actual_diff") is not None:
            return float(row["actual_diff"])
        if row.get("current_actual") is None:
            return None
        return float(row.get("baseline_plan") or 0) - float(row["current_actual"])
    if row.get("current_actual") is None:
        return None
    return float(row["current_actual"]) / 1000.0


def _metric_color(value: float | None, metric: str, *, max_abs: float, max_qty: float) -> str:
    if value is None:
        return "#f1f5f9"
    if metric == "achievement":
        if value >= 100:
            return "#86efac"
        if value >= 95:
            return "#d9f99d"
        if value >= 85:
            return "#fde68a"
        if value >= 70:
            return "#fdba74"
        return "#fca5a5"
    if metric == "actualDiff":
        ratio = min(abs(value) / max(max_abs, 1), 1)
        if value >= 0:
            if ratio >= 0.66:
                return "#4ade80"
            if ratio >= 0.33:
                return "#a7f3d0"
            return "#dcfce7"
        if ratio >= 0.66:
            return "#f87171"
        if ratio >= 0.33:
            return "#fca5a5"
        return "#fed7aa"
    ratio = min(max(value, 0) / max(max_qty, 0.0001), 1)
    if ratio >= 0.8:
        return "#0891b2"
    if ratio >= 0.55:
        return "#22d3ee"
    if ratio >= 0.3:
        return "#67e8f9"
    if ratio > 0:
        return "#cffafe"
    return "#f1f5f9"


def _metric_text(value: float | None, metric: str) -> str:
    if value is None:
        return ""
    if metric == "achievement":
        return f"{value:.0f}%"
    if metric == "actualDiff":
        sen = value / 1000.0
        sign = "+" if sen > 0 else ""
        text = f"{sen:.1f}"
        if text.endswith(".0"):
            text = text[:-2]
        return f"{sign}{text}"
    text = f"{value:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _heatmap_panel_html(
    title: str,
    unit: str,
    legend: str,
    month_start: date,
    rows: list[dict[str, Any]],
    metric: str,
) -> str:
    by_day: dict[int, dict[str, Any]] = {}
    for r in rows:
        ds = str(r.get("plan_date") or "")[:10]
        try:
            d = date.fromisoformat(ds)
        except ValueError:
            continue
        if d.year == month_start.year and d.month == month_start.month:
            by_day[d.day] = r
    values = [_metric_value(r, metric) for r in rows]
    max_abs = max((abs(v) for v in values if v is not None), default=1.0)
    max_qty = max((v for v in values if v is not None), default=0.0)

    wd = "".join(
        f"<span class='wd' style='color:{'#dc2626' if i == 0 else '#2563eb' if i == 6 else '#64748b'}'>"
        f"{w}</span>"
        for i, w in enumerate(_WEEKDAY_LABELS)
    )
    lead_pad = (date(month_start.year, month_start.month, 1).weekday() + 1) % 7
    days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]
    cells: list[str] = ["<div class='hm-pad'></div>"] * lead_pad
    for day in range(1, days_in_month + 1):
        row = by_day.get(day)
        val = _metric_value(row, metric) if row else None
        bg = _metric_color(val, metric, max_abs=max_abs, max_qty=max_qty)
        text = _metric_text(val, metric)
        cells.append(
            f"<div class='hm-cell' style='background:{bg}'>"
            f"<div class='hm-day'>{day}</div>"
            f"<div class='hm-val'>{_esc(text)}</div></div>"
        )
    while len(cells) % 7 != 0:
        cells.append("<div class='hm-pad'></div>")
    unit_html = f"<span class='hm-unit'>{_esc(unit)}</span>" if unit else ""
    return (
        f"<div class='hm-panel'>"
        f"<div class='hm-title'><span>{_esc(title)}</span>{unit_html}</div>"
        f"<div class='hm-wd'>{wd}</div>"
        f"<div class='hm-grid'>{''.join(cells)}</div>"
        f"<div class='hm-legend'>{_esc(legend)}</div></div>"
    )


def _fmt_trend_unit(value: float | None, digits: int = 1) -> str:
    if value is None:
        return ""
    if digits <= 0:
        return f"{int(round(value))}"
    text = f"{value:.{digits}f}"
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _trend_svg(rows: list[dict[str, Any]], process_name: str, period_label: str) -> str:
    """画面と同じグループ柱状図（基準計画 / 実績 + 差異バッジ）。"""
    w, h = 1040, 280
    pad_l, pad_r, pad_t, pad_b = 44, 14, 58, 30
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    n = max(len(rows), 1)

    baselines = [float(r.get("baseline_plan") or 0) / 1000.0 for r in rows]
    actuals: list[float | None] = [
        (float(r["current_actual"]) / 1000.0) if r.get("current_actual") is not None else None
        for r in rows
    ]
    # 画面: 差異 = 実績 − 基準計画（千単位）
    diffs: list[float | None] = []
    for i, r in enumerate(rows):
        if r.get("current_actual") is None:
            diffs.append(None)
            continue
        if r.get("actual_diff") is not None:
            # API の actual_diff 符号が画面定義と逆の場合に備え、実績−基準で再計算
            diffs.append(float(actuals[i] or 0) - baselines[i])
        else:
            diffs.append(float(actuals[i] or 0) - baselines[i])

    nums = [v for v in baselines if v] + [a for a in actuals if a is not None]
    ymax = max(nums) * 1.18 if nums else 1.0
    ymin = 0.0
    if ymax <= 0:
        ymax = 1.0

    cat_w = plot_w / n
    # 柱幅（画面の barMaxWidth 相当）
    if n <= 10:
        bar_w = min(16.0, cat_w * 0.32)
    elif n <= 16:
        bar_w = min(12.0, cat_w * 0.30)
    elif n <= 22:
        bar_w = min(9.0, cat_w * 0.28)
    else:
        bar_w = min(7.0, cat_w * 0.26)
    gap = max(1.5, bar_w * 0.18)
    dense = n > 20
    label_fs = 9 if dense else 10
    badge_fs = 9 if dense else 10

    def y_at(v: float) -> float:
        return pad_t + plot_h * (1 - (v - ymin) / (ymax - ymin))

    def cat_center(i: int) -> float:
        return pad_l + cat_w * (i + 0.5)

    parts: list[str] = []
    # grid
    for g in range(5):
        yy = pad_t + plot_h * g / 4
        val = ymax - (ymax - ymin) * g / 4
        parts.append(
            f"<line x1='{pad_l}' y1='{yy:.1f}' x2='{pad_l + plot_w}' y2='{yy:.1f}' "
            f"stroke='#e2e8f0' stroke-width='1'/>"
            f"<text x='{pad_l - 6}' y='{yy + 3:.1f}' text-anchor='end' "
            f"font-size='10' fill='#94a3b8'>{val:.1f}</text>"
        )
    parts.append(
        f"<line x1='{pad_l}' y1='{pad_t + plot_h}' x2='{pad_l + plot_w}' y2='{pad_t + plot_h}' stroke='#cbd5e1'/>"
        f"<line x1='{pad_l}' y1='{pad_t}' x2='{pad_l}' y2='{pad_t + plot_h}' stroke='#cbd5e1'/>"
    )

    for i, r in enumerate(rows):
        cx = cat_center(i)
        base = baselines[i]
        act = actuals[i]
        diff = diffs[i]
        x0 = cx - bar_w - gap / 2
        x1 = cx + gap / 2
        y_base0 = y_at(0)
        # 基準計画 bar
        if base > 0:
            yb = y_at(base)
            parts.append(
                f"<rect x='{x0:.1f}' y='{yb:.1f}' width='{bar_w:.1f}' height='{max(0.5, y_base0 - yb):.1f}' "
                f"rx='2' fill='url(#gradBase)'/>"
            )
        # 実績 bar
        if act is not None and act > 0:
            ya = y_at(act)
            parts.append(
                f"<rect x='{x1:.1f}' y='{ya:.1f}' width='{bar_w:.1f}' height='{max(0.5, y_base0 - ya):.1f}' "
                f"rx='2' fill='url(#gradActual)'/>"
            )
            # 実績値ラベル（柱上）
            parts.append(
                f"<text x='{x1 + bar_w / 2:.1f}' y='{ya - 3:.1f}' text-anchor='middle' "
                f"font-size='{label_fs}' font-weight='700' fill='#1d4ed8'>"
                f"{_esc(_fmt_trend_unit(act, 1))}</text>"
            )
        # 差異バッジ（柱ペア中央）
        if diff is not None and (base > 0 or (act is not None and act > 0)):
            taller = max(base, float(act or 0))
            mid_y = y_at(taller * 0.55 if taller > 0 else 0.1)
            sign = "+" if diff > 0 else ""
            fill = "#15803d" if diff > 0 else "#dc2626" if diff < 0 else "#64748b"
            label = f"{sign}{_fmt_trend_unit(diff, 1)}"
            # 簡易バッジ幅
            bw = max(22, 6 * len(label) + 8)
            bx = cx - bw / 2
            by = mid_y - 8
            parts.append(
                f"<rect x='{bx:.1f}' y='{by:.1f}' width='{bw:.1f}' height='16' rx='4' "
                f"fill='rgba(255,255,255,0.94)' stroke='{fill}' stroke-width='1'/>"
                f"<text x='{cx:.1f}' y='{by + 11.5:.1f}' text-anchor='middle' "
                f"font-size='{badge_fs}' font-weight='700' fill='{fill}'>{_esc(label)}</text>"
            )
        # x label
        label = str(r.get("plan_date") or "")[5:10].replace("-", "/")
        parts.append(
            f"<text x='{cx:.1f}' y='{h - 8}' text-anchor='middle' "
            f"font-size='9' fill='#64748b'>{_esc(label)}</text>"
        )

    return (
        f"<svg class='trend' viewBox='0 0 {w} {h}' width='100%' xmlns='http://www.w3.org/2000/svg'>"
        f"<defs>"
        f"<linearGradient id='gradBase' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0%' stop-color='#5eead4'/><stop offset='100%' stop-color='#0d9488'/>"
        f"</linearGradient>"
        f"<linearGradient id='gradActual' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0%' stop-color='#93c5fd'/><stop offset='100%' stop-color='#2563eb'/>"
        f"</linearGradient>"
        f"</defs>"
        f"<rect x='0' y='0' width='{w}' height='{h}' rx='8' fill='#fff' stroke='#e2e8f0'/>"
        f"<text x='{w/2}' y='18' text-anchor='middle' font-size='14' font-weight='800' fill='#0f172a'>"
        f"日次推移（基準計画 × 実績・単位：千）</text>"
        f"<text x='{w/2}' y='34' text-anchor='middle' font-size='11' fill='#64748b'>"
        f"{_esc(period_label)} ／ {_esc(process_name)}</text>"
        f"<rect x='{w/2 - 130}' y='40' width='12' height='7' rx='2' fill='#0d9488'/>"
        f"<text x='{w/2 - 114}' y='47' font-size='11' fill='#475569'>基準計画</text>"
        f"<rect x='{w/2 - 40}' y='40' width='12' height='7' rx='2' fill='#2563eb'/>"
        f"<text x='{w/2 - 24}' y='47' font-size='11' fill='#475569'>実績</text>"
        f"<text x='{w/2 + 60}' y='47' font-size='11' fill='#64748b'>差異(実績−基準)</text>"
        f"{''.join(parts)}"
        f"</svg>"
    )


def _cover_html(period_label: str, generated_at: str, summaries: list[dict[str, Any]]) -> str:
    items = []
    for i, s in enumerate(summaries):
        bg = "#f8fafc" if i % 2 else "#fff"
        items.append(
            f"<div class='proc-item' style='background:{bg}'>"
            f"<span class='proc-name'>{_esc(s['name'])}</span>"
            f"<span class='proc-meta'>{len(s['rows'])} 日分（最大2ページ）</span></div>"
        )
    return f"""
<div class="sheet">
  <div class="hero">
    <div class="hero-eye">SMART-EMAPS / PLAN BASELINE REPORT · A4横</div>
    <div class="hero-title">生産計画ベースライン 統合レポート</div>
    <div class="hero-meta">対象月：{_esc(period_label)}　　発行日時：{_esc(generated_at)}</div>
  </div>
  <div class="body">
    <div class="sec">収録工程（全 {len(summaries)} 工程・1ファイル）</div>
    <div class="proc-grid">{''.join(items)}</div>
    <div class="note">
      各工程は <strong>最大2ページ</strong>（①KPI＋日別明細［2列］　②日次推移＋ヒートマップ）。
      工程と工程の間は改ページします。<br/>
      ※ 画面の「レポート生成」と同じ構成です。
    </div>
  </div>
</div>"""


def _process_page1_html(period_label: str, s: dict[str, Any]) -> str:
    tone = _tone(s["name"])
    plan_diff_color = "#dc2626" if (s["plan_diff"] or 0) < 0 else "#15803d"
    actual_diff_color = "#dc2626" if (s.get("actual_diff") or 0) < 0 else "#15803d"
    return f"""
<div class="sheet">
  <div class="bar" style="background:linear-gradient(135deg,{tone} 0%,#0d9488 70%);">
    <div><span class="bar-sub">工程レポート 1/2</span><span class="bar-title">{_esc(s['name'])}</span></div>
    <div class="bar-right">{_esc(period_label)}</div>
  </div>
  <div class="body compact">
    <div class="kpi-grid">
      <div class="kpi k1"><div class="k-label">基準計画</div><div class="k-val">{_fmt_num(s['baseline'])}</div></div>
      <div class="kpi k2"><div class="k-label">変更計画</div><div class="k-val">{_fmt_num(s['current_plan'])}</div></div>
      <div class="kpi k3"><div class="k-label">計画差異</div><div class="k-val" style="color:{plan_diff_color}">{_fmt_num(s['plan_diff'])}</div></div>
      <div class="kpi k4"><div class="k-label">実績</div><div class="k-val">{_fmt_num(s['current_actual'])}</div></div>
      <div class="kpi k5"><div class="k-label">対実績差</div><div class="k-val" style="color:{actual_diff_color}">{_fmt_num(s['actual_diff'])}</div></div>
      <div class="kpi k6"><div class="k-label">達成率</div><div class="k-val">{_fmt_rate(s['rate'])}</div></div>
    </div>
    <div class="sec">日別明細</div>
    {_two_col_detail_html(s)}
  </div>
</div>"""


def _process_page2_html(period_label: str, month_start: date, s: dict[str, Any]) -> str:
    tone = _tone(s["name"])
    rows = s["rows"]
    panels = "".join(
        [
            _heatmap_panel_html("計画達成率", "", "低 ← 達成率 → 高", month_start, rows, "achievement"),
            _heatmap_panel_html("実績差異", "単位：千", "負 ← 差異 → 正", month_start, rows, "actualDiff"),
            _heatmap_panel_html("実績数量", "単位：千", "少 ← 数量 → 多", month_start, rows, "actualQty"),
        ]
    )
    chart = _trend_svg(rows, s["name"], period_label) if rows else "<div class='empty-box'>データなし</div>"
    return f"""
<div class="sheet">
  <div class="bar" style="background:linear-gradient(135deg,{tone} 0%,#0284c7 80%);">
    <div class="bar-title">{_esc(s['name'])} — 工程レポート 2/2</div>
    <div class="bar-right">{_esc(period_label)}</div>
  </div>
  <div class="body compact">
    <div class="sec">日次推移（画面と同形式）</div>
    {chart}
    <div class="sec" style="margin-top:8px;">月間ヒートマップ</div>
    <div class="hm-row">{panels}</div>
  </div>
</div>"""


def _full_report_html(
    *,
    period_label: str,
    month_start: date,
    generated_at: str,
    summaries: list[dict[str, Any]],
) -> str:
    pages = [_cover_html(period_label, generated_at, summaries)]
    for s in summaries:
        pages.append(_process_page1_html(period_label, s))
        pages.append(_process_page2_html(period_label, month_start, s))
    if not summaries:
        pages.append("<div class='sheet'><div class='body'><p>比較データがありません。</p></div></div>")

    return f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8"/>
<title>生産計画ベースライン 統合レポート</title>
<style>
  @page {{ size: A4 landscape; margin: 4mm; }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0;
    font-family: {_JP_FONT};
    color: #0f172a; background: #fff;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .sheet {{
    width: 289mm; min-height: 200mm;
    page-break-after: always;
    break-after: page;
  }}
  .sheet:last-child {{ page-break-after: auto; break-after: auto; }}
  .hero {{
    padding: 14px 22px;
    background: linear-gradient(135deg,#0f766e 0%,#0d9488 42%,#0284c7 100%);
    color: #fff;
  }}
  .hero-eye {{ font-size: 11px; font-weight: 800; letter-spacing: .08em; opacity: .9; }}
  .hero-title {{ font-size: 22px; font-weight: 900; margin-top: 6px; }}
  .hero-meta {{ margin-top: 8px; font-size: 13px; font-weight: 700; }}
  .body {{ padding: 12px 16px 10px; }}
  .body.compact {{ padding: 6px 12px 8px; }}
  .sec {{ font-size: 12px; font-weight: 800; color: #0f766e; margin: 4px 0 6px; }}
  .proc-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
  .proc-item {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 12px; border-radius: 10px; border: 1px solid #e2e8f0;
  }}
  .proc-name {{ font-weight: 800; }}
  .proc-meta {{ font-weight: 700; color: #64748b; font-size: 12px; }}
  .note {{
    margin-top: 10px; padding: 10px 12px; border-radius: 10px;
    background: #f8fafc; border: 1px solid #e2e8f0;
    font-size: 11px; line-height: 1.65; color: #475569;
  }}
  .bar {{
    padding: 7px 14px; color: #fff;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .bar-sub {{ font-size: 10px; font-weight: 800; opacity: .9; margin-right: 10px; }}
  .bar-title {{ font-size: 16px; font-weight: 900; }}
  .bar-right {{ font-size: 12px; font-weight: 700; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; margin-bottom: 6px; }}
  .kpi {{ padding: 5px 7px; border-radius: 8px; border: 1px solid #e2e8f0; }}
  .k1 {{ background:#f0fdfa; border-color:#99f6e4; }}
  .k2 {{ background:#eff6ff; border-color:#bfdbfe; }}
  .k3 {{ background:#fff7ed; border-color:#fed7aa; }}
  .k4 {{ background:#ecfdf5; border-color:#a7f3d0; }}
  .k5 {{ background:#fff1f2; border-color:#fecdd3; }}
  .k6 {{ background:#f5f3ff; border-color:#ddd6fe; }}
  .k-label {{ font-size: 8px; font-weight: 800; color: #64748b; }}
  .k1 .k-label {{ color:#0f766e; }} .k2 .k-label {{ color:#1d4ed8; }}
  .k3 .k-label {{ color:#c2410c; }} .k4 .k-label {{ color:#047857; }}
  .k5 .k-label {{ color:#be123c; }} .k6 .k-label {{ color:#6d28d9; }}
  .k-val {{ font-size: 13px; font-weight: 900; font-variant-numeric: tabular-nums; margin-top: 1px; }}
  .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; align-items: start; }}
  table.detail {{ width: 100%; border-collapse: collapse; font-size: 9.5px; line-height: 1.45; }}
  table.detail th {{
    background: linear-gradient(135deg,#0f766e 0%,#0d9488 45%,#0284c7 100%);
    color: #fff; font-weight: 800; padding: 6px 5px; border: 1px solid rgba(255,255,255,.2);
    text-align: right;
  }}
  table.detail th:first-child {{ text-align: left; }}
  table.detail td {{ border: 1px solid #dbe3ee; padding: 5px; }}
  table.detail td.date {{ font-weight: 700; }}
  table.detail td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  table.detail td.neg, .neg {{ color: #dc2626; font-weight: 700; }}
  .pos {{ color: #15803d; font-weight: 700; }}
  table.detail td.empty {{ text-align: center; color: #94a3b8; padding: 10px; }}
  .totals {{
    margin-top: 6px; display: grid; grid-template-columns: auto repeat(5, 1fr); gap: 6px;
    padding: 6px 8px; border-radius: 8px;
    background: linear-gradient(90deg,#ecfdf5,#f0f9ff); border: 1px solid #99f6e4;
    font-size: 9px; font-weight: 800;
  }}
  .totals-label {{ color: #0f766e; align-self: center; }}
  .totals div {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .totals b {{ font-size: 11px; }}
  .hm-row {{ display: flex; gap: 8px; align-items: stretch; }}
  .hm-panel {{
    flex: 1; min-width: 0; padding: 5px; border-radius: 10px;
    border: 1px solid #e2e8f0; background: linear-gradient(180deg,#fff,#f8fafc);
  }}
  .hm-title {{
    display: flex; align-items: center; justify-content: center;
    gap: 6px; margin-bottom: 4px; position: relative; min-height: 16px;
    font-size: 10px; font-weight: 800;
  }}
  .hm-unit {{
    position: absolute; right: 0; top: 0;
    font-size: 8px; font-weight: 700; color: #0f766e;
    background: rgba(13,148,136,.1); border: 1px solid rgba(13,148,136,.22);
    border-radius: 999px; padding: 1px 5px;
  }}
  .hm-wd, .hm-grid {{ display: grid; grid-template-columns: repeat(7, minmax(0,1fr)); gap: 3px; }}
  .hm-wd {{ margin-bottom: 2px; }}
  .hm-wd .wd {{ text-align: center; font-size: 8px; font-weight: 800; }}
  .hm-cell {{
    height: 32px; border-radius: 6px; display: flex; flex-direction: column;
    align-items: center; justify-content: center; padding: 1px;
  }}
  .hm-pad {{ height: 32px; }}
  .hm-day {{ font-size: 8.5px; font-weight: 800; line-height: 1; }}
  .hm-val {{ font-size: 8px; font-weight: 700; color: #334155; margin-top: 1px;
             font-variant-numeric: tabular-nums; }}
  .hm-legend {{ margin-top: 4px; font-size: 8px; color: #64748b; font-weight: 650; }}
  .trend {{ display: block; border: 1px solid #e2e8f0; border-radius: 8px; }}
  .empty-box {{
    padding: 20px; text-align: center; color: #94a3b8;
    border: 1px dashed #cbd5e1; border-radius: 8px;
  }}
</style></head><body>
{''.join(pages)}
</body></html>"""


def _find_chrome() -> str | None:
    env = os.environ.get("CHROME_PATH") or os.environ.get("EDGE_PATH")
    if env and Path(env).exists():
        return env
    candidates = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Microsoft/Edge/Application/msedge.exe",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("msedge"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return str(c)
    return None


def _html_to_pdf_chrome(html_doc: str) -> bytes:
    chrome = _find_chrome()
    if not chrome:
        raise RuntimeError("Chrome/Edge が見つかりません")

    with tempfile.TemporaryDirectory(prefix="pb_report_") as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "report.html"
        pdf_path = tmp_path / "report.pdf"
        html_path.write_text(html_doc, encoding="utf-8")
        uri = html_path.resolve().as_uri()
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--allow-file-access-from-files",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            uri,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0 or not pdf_path.exists():
            raise RuntimeError(
                f"Chrome PDF 生成失敗 code={proc.returncode} err={proc.stderr[-500:]}"
            )
        data = pdf_path.read_bytes()
        if len(data) < 100:
            raise RuntimeError("Chrome PDF が空です")
        return data


def _build_baseline_pdf(
    *,
    period_label: str,
    month_start: date,
    generated_at: str,
    summaries: list[dict[str, Any]],
) -> bytes:
    """画面「レポート生成」と同レイアウトの PDF を生成する。"""
    html_doc = _full_report_html(
        period_label=period_label,
        month_start=month_start,
        generated_at=generated_at,
        summaries=summaries,
    )
    try:
        return _html_to_pdf_chrome(html_doc)
    except Exception as exc:
        from loguru import logger

        logger.warning("HTML→PDF(Chrome) 失敗のため reportlab にフォールバック: {}", exc)
        return _build_baseline_pdf_reportlab(
            period_label=period_label,
            month_start=month_start,
            generated_at=generated_at,
            summaries=summaries,
        )


def _build_baseline_pdf_reportlab(
    *,
    period_label: str,
    month_start: date,
    generated_at: str,
    summaries: list[dict[str, Any]],
) -> bytes:
    """Chrome 不可時の簡易フォールバック（表中心）。"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font = "HeiseiKakuGo-W5"
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(font))
    except Exception:
        font = "Helvetica"

    styles = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=styles["Title"], fontName=font, fontSize=16)
    body = ParagraphStyle("b", parent=styles["Normal"], fontName=font, fontSize=9)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=10 * mm, rightMargin=10 * mm)
    flow: list[Any] = [
        Paragraph("生産計画ベースライン 統合レポート", title),
        Paragraph(f"対象月: {period_label} / 発行: {generated_at}", body),
        Spacer(1, 8),
    ]
    headers = ["工程", "基準計画", "変更計画", "計画差異", "実績", "対実績差", "達成率"]
    data = [headers] + [
        [
            s["name"],
            _fmt_num(s["baseline"]),
            _fmt_num(s["current_plan"]),
            _fmt_num(s["plan_diff"]),
            _fmt_num(s["current_actual"]),
            _fmt_num(s["actual_diff"]),
            _fmt_rate(s["rate"]),
        ]
        for s in summaries
    ] or [headers, ["—"] * 7]
    t = Table(data)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    flow.append(t)
    for s in summaries:
        flow.append(PageBreak())
        flow.append(Paragraph(f"{s['name']} 日別明細", title))
        dheaders = ["日付", "基準", "変更計画", "計画差", "実績", "対実績差"]
        ddata = [dheaders]
        for r in s["rows"]:
            ddata.append(
                [
                    str(r.get("plan_date") or "")[:10],
                    _fmt_num(float(r.get("baseline_plan") or 0)),
                    _fmt_num(float(r.get("current_plan") or 0)),
                    _fmt_num(float(r.get("plan_diff") or 0)),
                    _fmt_num(float(r["current_actual"])) if r.get("current_actual") is not None else "—",
                    _fmt_num(float(r["actual_diff"])) if r.get("actual_diff") is not None else "—",
                ]
            )
        dt = Table(ddata)
        dt.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d9488")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                ]
            )
        )
        flow.append(dt)
    void = month_start  # keep signature used
    _ = void
    doc.build(flow)
    return buf.getvalue()

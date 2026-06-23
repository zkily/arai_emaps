"""切断工程実績レポート生成器（成型前在庫推移 + 切断計画実績対比）"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .cutting_report_preview import build_cutting_preview_html, build_cutting_preview_text, build_cutting_report_pdf
from .base import (
    PDF_MIME,
    XLSX_MIME,
    GeneratedReport,
    ReportAttachment,
    ReportGenerator,
    build_xlsx,
    resolve_date_range,
)

# 成型工程より前の在庫列（日次合計）
_PRE_MOLDING_INVENTORY_COLS = ("cutting_inventory", "chamfering_inventory")


def _normalize_cutting_parameters(parameters: dict[str, Any] | None) -> dict[str, Any]:
    """未指定時は対象期間を今月にする。"""
    params = dict(parameters or {})
    if not params.get("date_range"):
        params["date_range"] = "this_month"
    return params


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
        rng = resolve_date_range(_normalize_cutting_parameters(parameters), run_date=run_date)

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
        chart_data = _build_chart_data(daily, rng.start, rng.end)

        from app.modules.plan_baseline.api import sum_baseline_actual_diff_for_period

        baseline_actual_diff = await sum_baseline_actual_diff_for_period(
            db, start=rng.start, end=rng.end, process_name="切断"
        )
        chart_data["baseline_actual_diff"] = baseline_actual_diff

        total_plan = sum(d["plan"] for d in daily)
        total_actual = sum(d["actual"] for d in daily)
        record_count = sum(1 for d in daily if d["plan"] or d["actual"] or d["inventory"])

        summary_html = build_cutting_preview_html(
            rng.label, daily, chart_data, run_date=run_date
        )
        summary_text = build_cutting_preview_text(
            rng.label, daily, chart_data, run_date=run_date
        )
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
                    build_cutting_report_pdf(
                        "切断工程実績レポート", rng.label, daily, chart_data, run_date=run_date
                    ),
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


def _build_chart_data(
    daily: list[dict[str, Any]], period_start: date, period_end: date
) -> dict[str, Any]:
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "inventory_trend": {
            "labels": [d["label"] for d in daily],
            "days": [d["day"] for d in daily],
            "values": [d["inventory"] for d in daily],
        },
        "plan_actual": {
            "labels": [d["label"] for d in daily],
            "days": [d["day"] for d in daily],
            "plan": [d["plan"] for d in daily],
            "actual": [d["actual"] for d in daily],
        },
    }


def _rate_str(plan: int, actual: int) -> str:
    if not plan:
        return "—"
    return f"{round(actual / plan * 100, 1)}%"


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

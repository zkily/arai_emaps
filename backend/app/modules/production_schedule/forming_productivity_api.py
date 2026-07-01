# coding: utf-8
"""成形工程 生産性分析 API（forming_production_indicator 集計）"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User

from app.modules.production_schedule.api import (
    _finalize_inspection_productivity_bucket,
    _inspection_defect_rate_percent,
    _inspection_efficiency_per_hour,
    _merge_inspection_productivity_bucket,
    _parse_date_ymd,
)

FORMING_LINE_METRICS_LOSS_HEADERS = [
    "段取",
    "修理",
    "調整",
    "対応待ち",
    "停止時間",
]

FORMING_LINE_METRICS_LOSS_FIELDS = [
    ("段取", "setup_hours"),
    ("修理", "repair_hours"),
    ("調整", "adjustment_hours"),
    ("対応待ち", "waiting_repair_hours"),
    ("停止時間", "planned_stop_hours"),
]


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _forming_row_work_sec(item: dict[str, Any]) -> int:
    work_h = _to_float(item.get("work_hours"))
    if work_h > 0:
        return max(0, int(round(work_h * 3600)))
    return 0


def _forming_row_paused_sec(item: dict[str, Any]) -> int:
    shift_h = _to_float(item.get("shift_hours"))
    work_h = _to_float(item.get("work_hours"))
    if shift_h > work_h > 0:
        return max(0, int(round((shift_h - work_h) * 3600)))
    pause_h = sum(_to_float(item.get(field)) for _, field in FORMING_LINE_METRICS_LOSS_FIELDS)
    pause_h += _to_float(item.get("break_hours"))
    if pause_h > 0:
        return max(0, int(round(pause_h * 3600)))
    return 0


def _normalize_forming_row(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    for k in ("production_month", "production_day"):
        v = item.get(k)
        if isinstance(v, date):
            item[k] = v.isoformat()
    return item


def _new_line_metrics_bucket(*, line_key: str, line_name: str) -> dict[str, Any]:
    bucket: dict[str, Any] = {
        "line_key": line_key,
        "inspector_user_id": None,
        "inspector_name": line_name,
        "sum_shift_sec": 0,
        "sum_break_sec": 0,
        "sum_stop_sec": 0,
        "sum_work_sec": 0,
        "sum_inspection_qty": 0,
        "defects": {},
    }
    for header, _field in FORMING_LINE_METRICS_LOSS_FIELDS:
        bucket["defects"][header] = 0
    bucket["defects"]["不良"] = 0
    return bucket


def _finalize_line_metrics_row(bucket: dict[str, Any]) -> dict[str, Any]:
    out = dict(bucket)
    defects = dict(out.get("defects") or {})
    out["defects"] = defects
    out["sum_variance_qty"] = int(defects.get("不良") or 0)
    return out


def _build_line_metrics_total_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = _new_line_metrics_bucket(line_key="total", line_name="合計")
    for row in rows:
        total["sum_shift_sec"] += int(row.get("sum_shift_sec") or 0)
        total["sum_break_sec"] += int(row.get("sum_break_sec") or 0)
        total["sum_stop_sec"] += int(row.get("sum_stop_sec") or 0)
        total["sum_work_sec"] += int(row.get("sum_work_sec") or 0)
        total["sum_inspection_qty"] += int(row.get("sum_inspection_qty") or 0)
        for header in total["defects"]:
            total["defects"][header] += int((row.get("defects") or {}).get(header) or 0)
    return _finalize_line_metrics_row(total)


def register_routes(router: APIRouter) -> None:
    @router.get("/plan/forming-production-indicator/lines")
    async def get_forming_production_indicator_lines(
        start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
        end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        """期間内の成形ライン一覧（フィルタ用）"""
        start_d = _parse_date_ymd(start_date)
        end_d = _parse_date_ymd(end_date)
        if start_d is None or end_d is None or start_d > end_d:
            raise HTTPException(status_code=400, detail="日付範囲が不正です。")
        try:
            result = await db.execute(
                text(
                    """
                    SELECT DISTINCT production_line AS line_name
                    FROM forming_production_indicator
                    WHERE production_day >= :start_date
                      AND production_day <= :end_date
                      AND production_line IS NOT NULL
                      AND TRIM(production_line) <> ''
                    ORDER BY production_line ASC
                    """
                ),
                {"start_date": start_d, "end_date": end_d},
            )
            lines = [str(r[0]).strip() for r in result.fetchall() if r[0]]
        except Exception as e:
            msg = str(e).lower()
            if "forming_production_indicator" in msg and (
                "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
            ):
                raise HTTPException(
                    status_code=503,
                    detail="forming_production_indicator テーブルが存在しません。backend/database/migrations/69_forming_production_indicator.sql を実行してください",
                ) from e
            raise HTTPException(status_code=500, detail=str(e)) from e
        return {"success": True, "data": [{"line_name": name} for name in lines]}

    @router.get("/plan/forming-production-indicator/productivity-analysis")
    async def get_forming_productivity_analysis(
        start_date: str = Query(..., description="開始日 YYYY-MM-DD"),
        end_date: str = Query(..., description="終了日 YYYY-MM-DD"),
        production_line: Optional[str] = Query(None, description="ライン名"),
        product_cd: Optional[str] = Query(None, description="製品CD"),
        include_incomplete: bool = Query(False, description="互換用（成形指標は常に実績行）"),
        limit: int = Query(10000, ge=1, le=20000),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(verify_token_and_get_user),
    ):
        """成形能率分析（forming_production_indicator 集計）"""
        start_d = _parse_date_ymd(start_date)
        end_d = _parse_date_ymd(end_date)
        if start_d is None or end_d is None:
            raise HTTPException(status_code=400, detail="日付が不正です。")
        if start_d > end_d:
            raise HTTPException(status_code=400, detail="date_start は date_end 以下で指定してください。")

        where_parts = [
            "production_day >= :start_date",
            "production_day <= :end_date",
        ]
        params: dict[str, Any] = {"start_date": start_d, "end_date": end_d, "lim": limit}
        line_norm = (production_line or "").strip()
        if line_norm:
            where_parts.append("production_line = :production_line")
            params["production_line"] = line_norm
        product_cd_norm = (product_cd or "").strip()
        if product_cd_norm:
            where_parts.append("product_cd = :product_cd")
            params["product_cd"] = product_cd_norm
        where_sql = " AND ".join(where_parts)
        sql = f"""
            SELECT id, fiscal_year, production_month, production_day, source_line, source_file,
                   product_cd, production_line, product_name,
                   planned_quantity, actual_quantity, defect_quantity,
                   shift_hours, overtime_hours, setup_hours, repair_hours,
                   adjustment_hours, break_hours, waiting_repair_hours,
                   planned_stop_hours, available_work_hours,
                   work_hours, utilization_rate, work_rate, efficiency_rate,
                   setup_adjustment_flag, yellow_box_qty, metric_60,
                   data_source, remarks, created_at, updated_at
            FROM forming_production_indicator
            WHERE {where_sql}
            ORDER BY production_day ASC, source_line ASC, id ASC
            LIMIT :lim
        """
        try:
            result = await db.execute(text(sql), params)
            rows = result.mappings().all()
        except Exception as e:
            msg = str(e).lower()
            if "forming_production_indicator" in msg and (
                "doesn't exist" in msg or "not exist" in msg or "unknown table" in msg
            ):
                raise HTTPException(
                    status_code=503,
                    detail="forming_production_indicator テーブルが存在しません。backend/database/migrations/69_forming_production_indicator.sql を実行してください",
                ) from e
            raise HTTPException(status_code=500, detail=str(e)) from e

        sessions: list[dict[str, Any]] = []
        summary_bucket: dict[str, Any] = {
            "session_count": 0,
            "completed_session_count": 0,
            "sum_actual_qty": 0,
            "sum_defect_qty": 0,
            "sum_net_production_sec": 0,
            "sum_paused_sec": 0,
        }
        daily_map: dict[str, dict[str, Any]] = {}
        line_map: dict[str, dict[str, Any]] = {}
        product_map: dict[str, dict[str, Any]] = {}
        product_line_map: dict[str, dict[str, Any]] = {}
        line_metrics_map: dict[str, dict[str, Any]] = {}

        for row in rows:
            item = _normalize_forming_row(dict(row))
            actual_qty = int(item.get("actual_quantity") or 0)
            planned_qty = int(item.get("planned_quantity") or 0)
            defect_qty = int(item.get("defect_quantity") or 0)
            net_sec = _forming_row_work_sec(item)
            paused_sec = _forming_row_paused_sec(item)
            day_key = str(item.get("production_day") or "")[:10]
            line_name = (item.get("production_line") or "").strip() or "—"
            line_key = line_name
            product_key = (item.get("product_cd") or "").strip() or (
                (item.get("product_name") or "").strip() or "unknown"
            )
            product_name = (item.get("product_name") or "").strip()

            session_row = {
                "id": int(item["id"]) if item.get("id") is not None else None,
                "production_day": day_key or None,
                "product_cd": (item.get("product_cd") or "").strip() or None,
                "product_name": product_name or None,
                "production_line": line_name,
                "planned_quantity": planned_qty,
                "actual_production_quantity": actual_qty,
                "defect_qty": defect_qty,
                "mes_inspector_user_id": None,
                "mes_inspector_name": line_name,
                "inspector_display_name": line_name,
                "net_production_sec": net_sec,
                "paused_sec": paused_sec,
                "net_production_min": int(round(net_sec / 60)) if net_sec > 0 else 0,
                "paused_min": int(round(paused_sec / 60)) if paused_sec > 0 else 0,
                "efficiency_per_hour": _inspection_efficiency_per_hour(actual_qty, net_sec),
                "defect_rate_percent": _inspection_defect_rate_percent(actual_qty, defect_qty),
                "is_completed": True,
            }
            sessions.append(session_row)

            _merge_inspection_productivity_bucket(
                summary_bucket,
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                net_sec=net_sec,
                completed_count=1,
            )
            summary_bucket["sum_paused_sec"] = int(summary_bucket.get("sum_paused_sec") or 0) + paused_sec

            if day_key:
                if day_key not in daily_map:
                    daily_map[day_key] = {
                        "day": day_key,
                        "session_count": 0,
                        "completed_session_count": 0,
                        "sum_actual_qty": 0,
                        "sum_defect_qty": 0,
                        "sum_net_production_sec": 0,
                    }
                _merge_inspection_productivity_bucket(
                    daily_map[day_key],
                    actual_qty=actual_qty,
                    defect_qty=defect_qty,
                    net_sec=net_sec,
                    completed_count=1,
                )

            if line_key not in line_map:
                line_map[line_key] = {
                    "inspector_user_id": None,
                    "inspector_name": line_name,
                    "session_count": 0,
                    "completed_session_count": 0,
                    "sum_actual_qty": 0,
                    "sum_defect_qty": 0,
                    "sum_net_production_sec": 0,
                }
            _merge_inspection_productivity_bucket(
                line_map[line_key],
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                net_sec=net_sec,
                completed_count=1,
            )

            if product_key not in product_map:
                product_map[product_key] = {
                    "product_cd": product_key,
                    "product_name": product_name or product_key,
                    "session_count": 0,
                    "completed_session_count": 0,
                    "sum_actual_qty": 0,
                    "sum_defect_qty": 0,
                    "sum_net_production_sec": 0,
                }
            _merge_inspection_productivity_bucket(
                product_map[product_key],
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                net_sec=net_sec,
                completed_count=1,
            )

            if product_key not in product_line_map:
                product_line_map[product_key] = {
                    "product_cd": product_key,
                    "product_name": product_name or product_key,
                    "inspectors": {},
                }
            pi_bucket = product_line_map[product_key]["inspectors"]
            if line_key not in pi_bucket:
                pi_bucket[line_key] = {
                    "inspector_user_id": None,
                    "inspector_name": line_name,
                    "session_count": 0,
                    "completed_session_count": 0,
                    "sum_actual_qty": 0,
                    "sum_defect_qty": 0,
                    "sum_net_production_sec": 0,
                }
            _merge_inspection_productivity_bucket(
                pi_bucket[line_key],
                actual_qty=actual_qty,
                defect_qty=defect_qty,
                net_sec=net_sec,
                completed_count=1,
            )

            if line_key not in line_metrics_map:
                line_metrics_map[line_key] = _new_line_metrics_bucket(line_key=line_key, line_name=line_name)
            metrics_bucket = line_metrics_map[line_key]
            metrics_bucket["sum_shift_sec"] += max(0, int(round(_to_float(item.get("shift_hours")) * 3600)))
            metrics_bucket["sum_break_sec"] += max(0, int(round(_to_float(item.get("break_hours")) * 3600)))
            stop_h = sum(_to_float(item.get(field)) for _, field in FORMING_LINE_METRICS_LOSS_FIELDS)
            metrics_bucket["sum_stop_sec"] += max(0, int(round(stop_h * 3600)))
            metrics_bucket["sum_work_sec"] += net_sec
            metrics_bucket["sum_inspection_qty"] += actual_qty
            if defect_qty > 0:
                metrics_bucket["defects"]["不良"] = int(metrics_bucket["defects"].get("不良") or 0) + defect_qty
            for header, field in FORMING_LINE_METRICS_LOSS_FIELDS:
                h_val = _to_float(item.get(field))
                if h_val > 0:
                    metrics_bucket["defects"][header] = int(metrics_bucket["defects"].get(header) or 0) + int(
                        round(h_val * 3600)
                    )

        summary = _finalize_inspection_productivity_bucket(summary_bucket)
        summary["sum_paused_sec"] = int(summary_bucket.get("sum_paused_sec") or 0)
        summary["sum_paused_min"] = round(summary["sum_paused_sec"] / 60) if summary["sum_paused_sec"] > 0 else 0
        summary["sum_net_production_min"] = (
            round(summary["sum_net_production_sec"] / 60) if summary["sum_net_production_sec"] > 0 else 0
        )

        daily = [_finalize_inspection_productivity_bucket(v) for v in sorted(daily_map.values(), key=lambda x: x["day"])]
        by_inspector = sorted(
            [_finalize_inspection_productivity_bucket(v) for v in line_map.values()],
            key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("inspector_name") or "")),
        )
        by_product = sorted(
            [_finalize_inspection_productivity_bucket(v) for v in product_map.values()],
            key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("product_cd") or "")),
        )

        by_product_inspector_ranking: list[dict[str, Any]] = []
        for prod_key, prod_entry in product_line_map.items():
            inspectors_raw = list(prod_entry.get("inspectors", {}).values())
            inspectors_final: list[dict[str, Any]] = []
            for inv in inspectors_raw:
                fin = _finalize_inspection_productivity_bucket(dict(inv))
                if fin.get("efficiency_per_hour") is not None:
                    inspectors_final.append(fin)
            inspectors_final.sort(
                key=lambda x: (
                    -(x.get("efficiency_per_hour") or 0),
                    -(x.get("sum_actual_qty") or 0),
                    str(x.get("inspector_name") or ""),
                )
            )
            for rank_idx, inv in enumerate(inspectors_final, start=1):
                inv["rank"] = rank_idx
            prod_summary = product_map.get(prod_key) or {}
            by_product_inspector_ranking.append(
                {
                    "product_cd": prod_entry.get("product_cd") or prod_key,
                    "product_name": prod_entry.get("product_name") or prod_key,
                    "sum_actual_qty": int(prod_summary.get("sum_actual_qty") or 0),
                    "session_count": int(prod_summary.get("session_count") or 0),
                    "inspector_count": len(inspectors_raw),
                    "ranked_inspector_count": len(inspectors_final),
                    "inspectors": inspectors_final,
                    "top_inspector_name": inspectors_final[0]["inspector_name"] if inspectors_final else None,
                    "top_efficiency_per_hour": inspectors_final[0]["efficiency_per_hour"] if inspectors_final else None,
                }
            )
        by_product_inspector_ranking.sort(
            key=lambda x: (-int(x.get("sum_actual_qty") or 0), str(x.get("product_cd") or ""))
        )

        line_metrics_rows = sorted(
            [_finalize_line_metrics_row(dict(v)) for v in line_metrics_map.values()],
            key=lambda x: str(x.get("inspector_name") or ""),
        )
        support_row = _finalize_line_metrics_row(
            _new_line_metrics_bucket(line_key="support", line_name="応援")
        )
        total_metrics_row = _build_line_metrics_total_row(line_metrics_rows)
        defect_headers = ["不良", *[h for h, _ in FORMING_LINE_METRICS_LOSS_FIELDS]]

        return {
            "success": True,
            "data": {
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
                "include_incomplete": include_incomplete,
                "summary": summary,
                "daily": daily,
                "by_inspector": by_inspector,
                "by_operator": [
                    {
                        **row,
                        "operator_user_id": row.get("inspector_user_id"),
                        "operator_name": row.get("inspector_name"),
                    }
                    for row in by_inspector
                ],
                "by_product": by_product,
                "by_product_inspector_ranking": by_product_inspector_ranking,
                "by_product_operator_ranking": [
                    {
                        **entry,
                        "operator_count": entry.get("inspector_count"),
                        "ranked_operator_count": entry.get("ranked_inspector_count"),
                        "top_operator_name": entry.get("top_inspector_name"),
                        "operators": [
                            {
                                **op,
                                "operator_user_id": op.get("inspector_user_id"),
                                "operator_name": op.get("inspector_name"),
                            }
                            for op in entry.get("inspectors") or []
                        ],
                    }
                    for entry in by_product_inspector_ranking
                ],
                "defect_by_item": [{"defect_cd": "不良", "qty": int(summary.get("sum_defect_qty") or 0)}]
                if int(summary.get("sum_defect_qty") or 0) > 0
                else [],
                "by_inspector_metrics": {
                    "rows": line_metrics_rows,
                    "support_row": support_row,
                    "total_row": total_metrics_row,
                    "defect_headers": defect_headers,
                },
                "sessions": [
                    {
                        **s,
                        "mes_operator_user_id": None,
                        "mes_operator_name": s.get("mes_inspector_name"),
                        "operator_display_name": s.get("inspector_display_name"),
                    }
                    for s in sessions
                ],
            },
        }

"""
在庫報告 API（四半期・半期・年間、報告向け）。
月末在庫（仕掛品/製品）、理論 vs 棚卸差異、廃棄率・不良本数・廃棄本数を選択期間単位で集計する。
"""
from __future__ import annotations

import json
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_inventory_operation
from app.modules.database.models import ProductionSummary
from app.modules.erp.bulk_disposal_retention_models import BulkDisposalRetentionRecord
from app.modules.erp.inventory_comparison_api import (
    _build_detail_rows,
    _build_summary_rows,
    _compute_kpi_from_details,
)
from app.modules.erp.inventory_report_models import InventoryQuarterlyReport
from app.modules.erp.inventory_value_api import (
    _PRODUCT_INVENTORY_COLS,
    _WIP_INVENTORY_COLS,
    _deduped_process_inventory_specs,
    _stocktake_product_cd_included,
)
from app.modules.master.models import Process

router = APIRouter(prefix="/inventory-report", tags=["在庫報告"])

_EXCLUDED_PRODUCT_NAME_TOKEN = "加工"
# 棚卸差異は成型・メッキ・溶接・検査・倉庫のみ対象（ホワイトリスト方式）
_STOCKTAKE_DIFF_INCLUDED_PROCESS_CDS = frozenset({"KT04", "KT05", "KT07", "KT09", "KT13"})
_STOCKTAKE_DIFF_INCLUDED_PROCESS_NAMES = frozenset({"成型", "メッキ", "溶接", "検査", "倉庫"})
_STOCKTAKE_DIFF_MOLDING_EXCLUDED_PRODUCT_NAMES = frozenset(
    name.casefold()
    for name in (
        "900B RR",
        "900B FR",
        "TTA",
        "410D RR",
        "410D FR2",
        "410D FR1",
        "410D CTR",
        "TKR FR",
        "900B 対米",
    )
)


def _is_stocktake_diff_process(process_cd: Any, process_name: Any) -> bool:
    cd = str(process_cd or "").strip()
    if cd:
        return cd in _STOCKTAKE_DIFF_INCLUDED_PROCESS_CDS
    name = str(process_name or "").strip().removesuffix("工程")
    return name in _STOCKTAKE_DIFF_INCLUDED_PROCESS_NAMES


def _is_stocktake_diff_detail(row: Dict[str, Any]) -> bool:
    process_cd = str(row.get("process_cd") or "").strip()
    process_name = str(row.get("process_name") or "").strip().removesuffix("工程")
    if not _is_stocktake_diff_process(process_cd, process_name):
        return False

    # 指定製品は成型工程の棚卸差異だけから除外し、他工程では通常どおり集計する。
    is_molding = process_cd == "KT04" or (not process_cd and process_name == "成型")
    normalized_product_name = " ".join(str(row.get("product_name") or "").split()).casefold()
    return not (
        is_molding
        and normalized_product_name in _STOCKTAKE_DIFF_MOLDING_EXCLUDED_PRODUCT_NAMES
    )

_QUARTER_MONTHS: Dict[int, Tuple[int, int, int]] = {
    1: (4, 5, 6),
    2: (7, 8, 9),
    3: (10, 11, 12),
    4: (1, 2, 3),
}
_REPORT_PERIOD_MONTHS: Dict[int, Tuple[int, ...]] = {
    **_QUARTER_MONTHS,
    5: (4, 5, 6, 7, 8, 9),  # 上期
    6: (10, 11, 12, 1, 2, 3),  # 下期
    7: (4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3),  # 年間
}

_SCRAP_PROCESS_DEFS: Tuple[Tuple[str, str, str, Optional[str], str], ...] = (
    ("cutting", "切断", "cutting_actual", "cutting_defect", "cutting_scrap"),
    ("chamfering", "面取", "chamfering_actual", "chamfering_defect", "chamfering_scrap"),
    ("molding", "成型", "molding_actual", "molding_defect", "molding_scrap"),
    ("plating", "メッキ", "plating_actual", "plating_defect", "plating_scrap"),
    ("welding", "溶接", "welding_actual", "welding_defect", "welding_scrap"),
    ("inspection", "検査", "inspection_actual", "inspection_defect", "inspection_scrap"),
    ("warehouse", "倉庫", "warehouse_actual", "warehouse_defect", "warehouse_scrap"),
    (
        "outsourced_warehouse",
        "外注倉庫",
        "outsourced_warehouse_actual",
        "outsourced_warehouse_defect",
        "outsourced_warehouse_scrap",
    ),
    (
        "outsourced_plating",
        "外注メッキ",
        "outsourced_plating_actual",
        "outsourced_plating_defect",
        "outsourced_plating_scrap",
    ),
    (
        "outsourced_welding",
        "外注溶接",
        "outsourced_welding_actual",
        "outsourced_welding_defect",
        "outsourced_welding_scrap",
    ),
    (
        "pre_welding_inspection",
        "溶接前検査",
        "pre_welding_inspection_actual",
        "pre_welding_inspection_defect",
        "pre_welding_inspection_scrap",
    ),
    ("pre_inspection", "外注支給前", "pre_inspection_actual", None, "pre_inspection_scrap"),
    ("pre_outsourcing", "外注検査前", "pre_outsourcing_actual", None, "pre_outsourcing_scrap"),
)

# 廃棄率（新）＝廃棄率分析と同じ主ライン（切断～検査）連乗。倉庫・外注等は含めない。
_MAIN_LINE_PROCESS_KEYS: Tuple[str, ...] = (
    "cutting",
    "chamfering",
    "molding",
    "plating",
    "welding",
    "inspection",
)

# 在庫報告「大量廃棄・保留品」ブロックへ自動併記する大量不良の閾値（本）
_BULK_DEFECT_MIN_QTY = 200
_BULK_DEFECT_CATEGORY = "大量不良"


def _month_end(year: int, month: int) -> date:
    return date(year, month, monthrange(year, month)[1])


def _month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def _quarter_calendar_months(fiscal_year: int, quarter: int) -> List[Tuple[int, int]]:
    """報告期間コードに対応する (calendar_year, month) の一覧。"""
    if quarter not in _REPORT_PERIOD_MONTHS:
        raise HTTPException(status_code=422, detail="period_code は 1〜7 を指定してください")
    months = _REPORT_PERIOD_MONTHS[quarter]
    out: List[Tuple[int, int]] = []
    for m in months:
        y = fiscal_year if m >= 4 else fiscal_year + 1
        out.append((y, m))
    return out


def _quarter_label(fiscal_year: int, quarter: int) -> str:
    months = _REPORT_PERIOD_MONTHS[quarter]
    if quarter <= 4:
        return f"{fiscal_year}年度 Q{quarter}（{months[0]}〜{months[-1]}月）"
    if quarter == 5:
        return f"{fiscal_year}年度 上期（4〜9月）"
    if quarter == 6:
        return f"{fiscal_year}年度 下期（10〜3月）"
    return f"{fiscal_year}年度 年間（4〜3月）"


def _report_type(period_code: int) -> str:
    if period_code <= 4:
        return "quarter"
    if period_code <= 6:
        return "half"
    return "annual"


def _previous_report_period(fiscal_year: int, period_code: int) -> Tuple[int, int]:
    if period_code <= 4:
        return (fiscal_year, period_code - 1) if period_code > 1 else (fiscal_year - 1, 4)
    if period_code == 5:
        return fiscal_year - 1, 6
    if period_code == 6:
        return fiscal_year, 5
    return fiscal_year - 1, 7


def _default_title(fiscal_year: int, quarter: int) -> str:
    report_name = {"quarter": "四半期", "half": "半期", "annual": "年間"}[
        _report_type(quarter)
    ]
    return f"在庫{report_name}報告 {_quarter_label(fiscal_year, quarter)}"


def _num(v: Any) -> int:
    if v is None:
        return 0
    if isinstance(v, Decimal):
        return int(v)
    return int(v)


def _fnum(v: Any) -> float:
    if v is None:
        return 0.0
    return float(v)


def _is_report_product(product_name: Any) -> bool:
    """報告対象判定：製品名に「加工」を含むデータは全統計から除外。"""
    return _EXCLUDED_PRODUCT_NAME_TOKEN not in str(product_name or "")


async def _resolve_as_of(db: AsyncSession, year: int, month: int) -> date:
    """月末日。当該月に production_summarys があれば最終データ日を優先。"""
    month_start = _month_start(year, month)
    month_end = _month_end(year, month)
    q = (
        select(func.max(ProductionSummary.date))
        .where(
            ProductionSummary.date >= month_start,
            ProductionSummary.date <= month_end,
            func.coalesce(ProductionSummary.product_name, "").not_like(
                f"%{_EXCLUDED_PRODUCT_NAME_TOKEN}%"
            ),
        )
    )
    latest = (await db.execute(q)).scalar_one_or_none()
    if latest:
        return latest if isinstance(latest, date) else date.fromisoformat(str(latest)[:10])
    return month_end


async def _month_end_inventory(db: AsyncSession, as_of: date) -> Dict[str, Any]:
    """仕掛品・製品の月末理論在庫（製品CD末尾1）。"""
    rows = list(
        (await db.execute(select(ProductionSummary).where(ProductionSummary.date == as_of)))
        .scalars()
        .all()
    )
    wip_qty = 0
    product_qty = 0
    by_process: Dict[str, int] = {}
    for col in _WIP_INVENTORY_COLS + _PRODUCT_INVENTORY_COLS:
        by_process[col] = 0

    for row in rows:
        if not _stocktake_product_cd_included(str(row.product_cd or "")):
            continue
        if not _is_report_product(row.product_name):
            continue
        for col in _WIP_INVENTORY_COLS:
            q = _num(getattr(row, col, None))
            wip_qty += q
            by_process[col] = by_process.get(col, 0) + q
        for col in _PRODUCT_INVENTORY_COLS:
            q = _num(getattr(row, col, None))
            product_qty += q
            by_process[col] = by_process.get(col, 0) + q

    return {
        "as_of": str(as_of),
        "wip_qty": wip_qty,
        "product_qty": product_qty,
        "total_qty": wip_qty + product_qty,
        "by_process_col": by_process,
    }


async def _month_scrap_metrics(
    db: AsyncSession, start_d: date, end_d: date
) -> Dict[str, Any]:
    sum_parts: List[str] = []
    for key, _label, actual_col, defect_col, scrap_col in _SCRAP_PROCESS_DEFS:
        sum_parts.append(f"SUM(COALESCE(`{actual_col}`, 0)) AS `{key}_actual`")
        if defect_col:
            sum_parts.append(f"SUM(COALESCE(`{defect_col}`, 0)) AS `{key}_defect`")
        else:
            sum_parts.append(f"0 AS `{key}_defect`")
        sum_parts.append(f"SUM(COALESCE(`{scrap_col}`, 0)) AS `{key}_scrap`")

    # 廃棄率分析（quality-rate-by-process）と同じ母集団：品名「加工」除外なし
    sql = (
        "SELECT "
        + ", ".join(sum_parts)
        + " FROM production_summarys"
        + " WHERE `date` >= :start_date AND `date` <= :end_date"
    )
    row = (
        await db.execute(
            text(sql),
            {
                "start_date": start_d,
                "end_date": end_d,
            },
        )
    ).mappings().first()
    if row is None:
        row = {}

    processes: List[dict] = []
    total_scrap = 0
    total_defect = 0
    for key, label, _a, _d, _s in _SCRAP_PROCESS_DEFS:
        sa = _num(row.get(f"{key}_actual"))
        sd = _num(row.get(f"{key}_defect"))
        ss = _num(row.get(f"{key}_scrap"))
        bad = sd + ss
        quality_loss_rate = round(bad / sa, 6) if sa > 0 else None
        defect_rate = round(sd / sa, 6) if sa > 0 else None
        scrap_rate = round(ss / sa, 6) if sa > 0 else None
        processes.append(
            {
                "key": key,
                "label": label,
                "sum_actual": sa,
                "sum_defect": sd,
                "sum_scrap": ss,
                "sum_defect_and_scrap": bad,
                "rate_percent": (
                    round(quality_loss_rate * 100, 4)
                    if quality_loss_rate is not None
                    else None
                ),
                "defect_rate_percent": (
                    round(defect_rate * 100, 4) if defect_rate is not None else None
                ),
                "scrap_rate_percent": round(scrap_rate * 100, 4) if scrap_rate is not None else None,
            }
        )
        total_scrap += ss
        total_defect += sd

    overall_bad = total_defect + total_scrap
    main_line_keys = set(_MAIN_LINE_PROCESS_KEYS)

    def rolled_loss_percent(
        qty_key: str, *, process_keys: Optional[set[str]] = None
    ) -> Optional[float]:
        """
        連乗ロス率 = 1 - Π(1 - 工程別率)。
        process_keys 指定時はその工程のみ（廃棄率分析の主ライン連乗と同一）。
        工程実績の単純合算を分母にすると同一品が工程間で重複するため使用しない。
        """
        yield_rate = 1.0
        participating = False
        for process in processes:
            key = str(process.get("key") or "")
            if process_keys is not None and key not in process_keys:
                continue
            actual = int(process.get("sum_actual") or 0)
            if actual <= 0:
                continue
            loss_qty = int(process.get(qty_key) or 0)
            process_rate = min(1.0, max(0.0, loss_qty / actual))
            yield_rate *= 1.0 - process_rate
            participating = True
        if not participating:
            return None
        # 廃棄率分析（database.api._compute_rolled_main_line_yield_loss）と同じ丸め
        ry = round(yield_rate, 8)
        loss = round(1.0 - ry, 8)
        return round(loss * 100, 4)

    overall_defect_rate = rolled_loss_percent("sum_defect")
    overall_scrap_rate = rolled_loss_percent("sum_scrap")
    # 廃棄率（新）：廃棄率分析と同じく主ライン（切断～検査）のみ連乗
    overall_quality_loss_rate = rolled_loss_percent(
        "sum_defect_and_scrap", process_keys=main_line_keys
    )
    overall_basis = "main_line_rolled"

    cutting_actual = _num(row.get("cutting_actual"))
    all_process_loss_rate = (
        round(overall_bad / cutting_actual, 6) if cutting_actual > 0 else None
    )
    all_process_loss_rate_percent = (
        round(all_process_loss_rate * 100, 4)
        if all_process_loss_rate is not None
        else None
    )

    return {
        "start_date": str(start_d),
        "end_date": str(end_d),
        "sum_scrap": total_scrap,
        "sum_defect": total_defect,
        "sum_defect_and_scrap": overall_bad,
        "sum_cutting_actual": cutting_actual,
        # rate_percent は既存フロント互換。意味は全工程の廃棄のみ連乗ロス率。
        "rate_percent": overall_scrap_rate,
        "defect_rate_percent": overall_defect_rate,
        "quality_loss_rate_percent": overall_quality_loss_rate,
        "all_process_loss_rate_percent": all_process_loss_rate_percent,
        "rate_basis": overall_basis,
        "processes": processes,
    }


async def _load_process_names(db: AsyncSession, process_cds: List[str]) -> Dict[str, str]:
    if not process_cds:
        return {}
    rows = list(
        (
            await db.execute(
                select(Process.process_cd, Process.process_name).where(Process.process_cd.in_(process_cds))
            )
        ).all()
    )
    out: Dict[str, str] = {}
    for cd, name in rows:
        k = str(cd or "").strip()
        if k:
            out[k] = (str(name or "").strip() or k)
    return out


async def _month_stocktake_diff(db: AsyncSession, as_of: date) -> Dict[str, Any]:
    detail_rows, _ = await _build_detail_rows(db, as_of, None, None, None, False)
    detail_rows = [
        r
        for r in detail_rows
        if _is_report_product(r.get("product_name"))
        and _is_stocktake_diff_detail(r)
    ]
    kpi = _compute_kpi_from_details(detail_rows)
    specs = [
        spec
        for spec in _deduped_process_inventory_specs()
        if spec[0] in _STOCKTAKE_DIFF_INCLUDED_PROCESS_CDS
    ]
    proc_cds = [pc for pc, _ in specs]
    proc_names = await _load_process_names(db, proc_cds)
    summary_rows = _build_summary_rows(detail_rows, specs, proc_names)

    # 差異絶対値上位
    top_mismatch = sorted(
        [r for r in detail_rows if int(r.get("diff_qty") or 0) != 0],
        key=lambda r: abs(int(r.get("diff_qty") or 0)),
        reverse=True,
    )[:15]

    return {
        "as_of": str(as_of),
        "kpi": kpi,
        "by_process": summary_rows,
        "top_mismatch": top_mismatch,
    }


async def _large_defect_items_from_production(
    db: AsyncSession, start_d: date, end_d: date
) -> List[dict]:
    """
    production_summarys から工程別不良本数 > 閾値の行を抽出し、
    報告区分「大量不良」として一覧化する。
    """
    defect_cols = [
        (label, defect_col)
        for _key, label, _actual, defect_col, _scrap in _SCRAP_PROCESS_DEFS
        if defect_col
    ]
    if not defect_cols:
        return []

    or_parts = " OR ".join(
        f"COALESCE(`{col}`, 0) > :threshold" for _label, col in defect_cols
    )
    select_parts = [
        "date",
        "product_cd",
        "product_name",
        *[f"COALESCE(`{col}`, 0) AS `{col}`" for _label, col in defect_cols],
    ]
    sql = (
        f"SELECT {', '.join(select_parts)} "
        "FROM production_summarys "
        "WHERE date >= :start_d AND date <= :end_d "
        f"AND ({or_parts})"
    )
    try:
        result = await db.execute(
            text(sql),
            {
                "start_d": start_d,
                "end_d": end_d,
                "threshold": _BULK_DEFECT_MIN_QTY,
            },
        )
        rows = result.mappings().all()
    except Exception:
        logger.exception("大量不良（生産実績）の抽出に失敗（スキップ）")
        return []

    items: List[dict] = []
    for row in rows:
        if not _is_report_product(row.get("product_name")):
            continue
        occurred = row.get("date")
        occurred_s = (
            occurred.isoformat()
            if hasattr(occurred, "isoformat")
            else (str(occurred) if occurred else None)
        )
        for label, col in defect_cols:
            qty = int(_num(row.get(col)))
            if qty <= _BULK_DEFECT_MIN_QTY:
                continue
            items.append(
                {
                    "occurred_date": occurred_s,
                    "report_category": _BULK_DEFECT_CATEGORY,
                    "process_name": label,
                    "product_cd": (str(row.get("product_cd") or "").strip() or None),
                    "product_name": str(row.get("product_name") or "").strip() or "—",
                    "quantity": qty,
                    "handling_status": "実績",
                    "source": "production_summary",
                }
            )
    return items


def _bulk_item_dedupe_key(item: dict) -> tuple:
    return (
        str(item.get("occurred_date") or ""),
        str(item.get("report_category") or ""),
        str(item.get("process_name") or ""),
        str(item.get("product_cd") or ""),
        str(item.get("product_name") or ""),
        int(item.get("quantity") or 0),
    )


async def _bulk_disposal_summary(
    db: AsyncSession, start_d: date, end_d: date
) -> Dict[str, Any]:
    try:
        q = select(BulkDisposalRetentionRecord).where(
            BulkDisposalRetentionRecord.occurred_date >= start_d,
            BulkDisposalRetentionRecord.occurred_date <= end_d,
            func.coalesce(BulkDisposalRetentionRecord.product_name, "").not_like(
                f"%{_EXCLUDED_PRODUCT_NAME_TOKEN}%"
            ),
        )
        rows = list((await db.execute(q)).scalars().all())
    except Exception:
        logger.exception("大量廃棄・保留品の集計に失敗（スキップ）")
        rows = []

    by_cat: Dict[str, Dict[str, int]] = {}
    by_month: Dict[str, Dict[str, int]] = {}
    pending = 0
    total_qty = 0
    items: List[dict] = []
    for r in rows:
        cat = str(r.report_category or "その他")
        qty = int(r.quantity or 0)
        total_qty += qty
        if str(r.handling_status or "") == "未処理":
            pending += 1
        bucket = by_cat.setdefault(cat, {"count": 0, "quantity": 0})
        bucket["count"] += 1
        bucket["quantity"] += qty
        month_key = r.occurred_date.strftime("%Y-%m") if r.occurred_date else ""
        month_bucket = by_month.setdefault(
            month_key, {"count": 0, "quantity": 0, "pending_count": 0}
        )
        month_bucket["count"] += 1
        month_bucket["quantity"] += qty
        if str(r.handling_status or "") == "未処理":
            month_bucket["pending_count"] += 1
        items.append(
            {
                "occurred_date": str(r.occurred_date) if r.occurred_date else None,
                "report_category": cat,
                "process_name": r.process_name,
                "product_cd": r.product_cd,
                "product_name": r.product_name,
                "quantity": qty,
                "handling_status": r.handling_status,
                "source": "manual",
            }
        )

    # 生産実績から大量不良（>閾値）を併記。手動登録と同一キーは重複除外。
    existing_keys = {_bulk_item_dedupe_key(it) for it in items}
    for auto_item in await _large_defect_items_from_production(db, start_d, end_d):
        key = _bulk_item_dedupe_key(auto_item)
        if key in existing_keys:
            continue
        existing_keys.add(key)
        qty = int(auto_item.get("quantity") or 0)
        total_qty += qty
        cat = str(auto_item.get("report_category") or _BULK_DEFECT_CATEGORY)
        bucket = by_cat.setdefault(cat, {"count": 0, "quantity": 0})
        bucket["count"] += 1
        bucket["quantity"] += qty
        occurred = str(auto_item.get("occurred_date") or "")
        month_key = occurred[:7] if len(occurred) >= 7 else ""
        month_bucket = by_month.setdefault(
            month_key, {"count": 0, "quantity": 0, "pending_count": 0}
        )
        month_bucket["count"] += 1
        month_bucket["quantity"] += qty
        items.append(auto_item)

    return {
        "count": len(items),
        "total_quantity": total_qty,
        "pending_count": pending,
        "by_category": [{"category": k, **v} for k, v in sorted(by_cat.items())],
        "by_month": [{"month": k, **v} for k, v in sorted(by_month.items()) if k],
        "items": sorted(items, key=lambda x: abs(int(x.get("quantity") or 0)), reverse=True)[
            :50
        ],
        "bulk_defect_threshold": _BULK_DEFECT_MIN_QTY,
    }


async def _build_quarter_payload(db: AsyncSession, fiscal_year: int, quarter: int) -> Dict[str, Any]:
    cal_months = _quarter_calendar_months(fiscal_year, quarter)
    months_out: List[dict] = []
    inventory_series: List[dict] = []
    scrap_series: List[dict] = []
    diff_by_month_process: List[dict] = []
    all_top_mismatch: List[dict] = []

    quarter_start = _month_start(cal_months[0][0], cal_months[0][1])
    quarter_end = _month_end(cal_months[-1][0], cal_months[-1][1])

    for y, m in cal_months:
        as_of = await _resolve_as_of(db, y, m)
        start_d = _month_start(y, m)
        end_d = _month_end(y, m)
        month_key = f"{y}-{m:02d}"
        month_label = f"{m}月"

        inv = await _month_end_inventory(db, as_of)
        scrap = await _month_scrap_metrics(db, start_d, end_d)
        diff = await _month_stocktake_diff(db, as_of)

        months_out.append(
            {
                "month": month_key,
                "month_label": month_label,
                "calendar_year": y,
                "calendar_month": m,
                "as_of": str(as_of),
                "inventory": inv,
                "scrap": scrap,
                "stocktake_diff": {
                    "kpi": diff["kpi"],
                    "by_process": diff["by_process"],
                },
            }
        )
        inventory_series.append(
            {
                "month": month_key,
                "month_label": month_label,
                "wip_qty": inv["wip_qty"],
                "product_qty": inv["product_qty"],
                "total_qty": inv["total_qty"],
            }
        )
        scrap_series.append(
            {
                "month": month_key,
                "month_label": month_label,
                "rate_percent": scrap["rate_percent"],
                "defect_rate_percent": scrap["defect_rate_percent"],
                "quality_loss_rate_percent": scrap["quality_loss_rate_percent"],
                "all_process_loss_rate_percent": scrap["all_process_loss_rate_percent"],
                "sum_defect": scrap["sum_defect"],
                "sum_scrap": scrap["sum_scrap"],
                "sum_defect_and_scrap": scrap["sum_defect_and_scrap"],
                "sum_cutting_actual": scrap["sum_cutting_actual"],
                "rate_basis": scrap["rate_basis"],
                "processes": scrap["processes"],
            }
        )
        for proc in diff["by_process"]:
            diff_by_month_process.append(
                {
                    "month": month_key,
                    "month_label": month_label,
                    "process_cd": proc.get("process_cd"),
                    "process_name": proc.get("process_name"),
                    "theoretical_qty": proc.get("theoretical_qty"),
                    "stocktake_qty": proc.get("stocktake_qty"),
                    "diff_qty": proc.get("diff_qty"),
                    "diff_rate": proc.get("diff_rate"),
                    "match_rate": proc.get("match_rate"),
                }
            )
        for item in diff["top_mismatch"]:
            all_top_mismatch.append({**item, "month": month_key, "month_label": month_label})

    all_top_mismatch.sort(key=lambda r: abs(int(r.get("diff_qty") or 0)), reverse=True)
    bulk = await _bulk_disposal_summary(db, quarter_start, quarter_end)
    bulk_by_month = {str(r.get("month") or ""): r for r in bulk.get("by_month", [])}
    monthly_kpis = []
    for month in months_out:
        month_key = str(month.get("month") or "")
        inv = month.get("inventory") or {}
        scrap = month.get("scrap") or {}
        diff_kpi = (month.get("stocktake_diff") or {}).get("kpi") or {}
        month_bulk = bulk_by_month.get(month_key, {})
        monthly_kpis.append(
            {
                "month": month_key,
                "month_label": month.get("month_label"),
                "closing_wip_qty": int(inv.get("wip_qty") or 0),
                "closing_product_qty": int(inv.get("product_qty") or 0),
                "closing_total_qty": int(inv.get("total_qty") or 0),
                "scrap_rate_percent": scrap.get("rate_percent"),
                "all_process_loss_rate_percent": scrap.get("all_process_loss_rate_percent"),
                "quality_loss_rate_percent": scrap.get("quality_loss_rate_percent"),
                "sum_cutting_actual": int(scrap.get("sum_cutting_actual") or 0),
                "defect_rate_percent": scrap.get("defect_rate_percent"),
                "defect_qty": int(scrap.get("sum_defect") or 0),
                "scrap_qty": int(scrap.get("sum_scrap") or 0),
                "loss_qty": int(scrap.get("sum_defect_and_scrap") or 0),
                "match_rate": _fnum(diff_kpi.get("match_rate")),
                "diff_abs": abs(int(diff_kpi.get("diff_qty_total") or 0)),
                "bulk_disposal_count": int(month_bulk.get("count") or 0),
                "bulk_disposal_quantity": int(month_bulk.get("quantity") or 0),
                "bulk_disposal_pending": int(month_bulk.get("pending_count") or 0),
            }
        )

    # KPI サマリ
    last_inv = inventory_series[-1] if inventory_series else {}
    scrap_rates = [s["rate_percent"] for s in scrap_series if s.get("rate_percent") is not None]
    avg_scrap_rate = round(sum(scrap_rates) / len(scrap_rates), 4) if scrap_rates else None
    total_defect_qty = sum(int(s.get("sum_defect") or 0) for s in scrap_series)
    total_scrap_qty = sum(int(s.get("sum_scrap") or 0) for s in scrap_series)
    match_rates = [
        _fnum(m.get("stocktake_diff", {}).get("kpi", {}).get("match_rate"))
        for m in months_out
    ]
    avg_match_rate = round(sum(match_rates) / len(match_rates), 2) if match_rates else 0.0
    total_diff_abs = sum(
        abs(int(m.get("stocktake_diff", {}).get("kpi", {}).get("diff_qty_total") or 0))
        for m in months_out
    )

    # 同じ報告単位での前期間比較（四半期→前Q、半期→前半期、年間→前年度）
    prev_fy, prev_q = _previous_report_period(fiscal_year, quarter)
    prev_compare: Optional[dict] = None
    try:
        prev_months = _quarter_calendar_months(prev_fy, prev_q)
        prev_last_as_of = await _resolve_as_of(db, prev_months[-1][0], prev_months[-1][1])
        prev_inv = await _month_end_inventory(db, prev_last_as_of)
        prev_compare = {
            "fiscal_year": prev_fy,
            "quarter": prev_q,
            "label": _quarter_label(prev_fy, prev_q),
            "closing_total_qty": prev_inv["total_qty"],
            "closing_wip_qty": prev_inv["wip_qty"],
            "closing_product_qty": prev_inv["product_qty"],
            "delta_total_qty": int(last_inv.get("total_qty") or 0) - int(prev_inv["total_qty"]),
            "delta_wip_qty": int(last_inv.get("wip_qty") or 0) - int(prev_inv["wip_qty"]),
            "delta_product_qty": int(last_inv.get("product_qty") or 0) - int(prev_inv["product_qty"]),
        }
    except Exception:
        logger.exception("前期間比較の集計に失敗（スキップ）")

    return {
        "fiscal_year": fiscal_year,
        "quarter": quarter,
        "period_code": quarter,
        "report_type": _report_type(quarter),
        "label": _quarter_label(fiscal_year, quarter),
        "period": {"start": str(quarter_start), "end": str(quarter_end)},
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kpi": {
            "closing_wip_qty": int(last_inv.get("wip_qty") or 0),
            "closing_product_qty": int(last_inv.get("product_qty") or 0),
            "closing_total_qty": int(last_inv.get("total_qty") or 0),
            "avg_scrap_rate_percent": avg_scrap_rate,
            "total_defect_qty": total_defect_qty,
            "total_scrap_qty": total_scrap_qty,
            "avg_match_rate": avg_match_rate,
            "total_diff_abs": total_diff_abs,
            "bulk_disposal_count": bulk["count"],
            "bulk_disposal_pending": bulk["pending_count"],
        },
        "monthly_kpis": monthly_kpis,
        "inventory_series": inventory_series,
        "scrap_series": scrap_series,
        "diff_by_month_process": diff_by_month_process,
        "top_mismatch": all_top_mismatch[:20],
        "bulk_disposal": bulk,
        "previous_quarter": prev_compare,
        "previous_period": prev_compare,
        "months": months_out,
        "highlights": _build_highlights(
            inventory_series, scrap_series, avg_match_rate, total_diff_abs, bulk, prev_compare
        ),
    }


def _build_highlights(
    inventory_series: List[dict],
    scrap_series: List[dict],
    avg_match_rate: float,
    total_diff_abs: int,
    bulk: dict,
    prev_compare: Optional[dict],
) -> List[dict]:
    highlights: List[dict] = []
    if inventory_series:
        first = inventory_series[0]
        last = inventory_series[-1]
        delta = int(last.get("total_qty") or 0) - int(first.get("total_qty") or 0)
        tone = "up" if delta > 0 else ("down" if delta < 0 else "flat")
        highlights.append(
            {
                "type": "inventory_trend",
                "tone": tone,
                "title": "対象期間内在庫推移",
                "text": (
                    f"仕掛+製品合計は {first.get('month_label')} {int(first.get('total_qty') or 0):,} 本 → "
                    f"{last.get('month_label')} {int(last.get('total_qty') or 0):,} 本（差分 {delta:+,} 本）"
                ),
            }
        )
    if scrap_series:
        quality_rates = [
            (
                s.get("month_label"),
                s.get("quality_loss_rate_percent"),
                s.get("sum_defect_and_scrap"),
            )
            for s in scrap_series
        ]
        quality_peak = max(quality_rates, key=lambda x: (x[1] is not None, x[1] or 0))
        if quality_peak[1] is not None:
            highlights.append(
                {
                    "type": "defect_peak",
                    "tone": "warn" if (quality_peak[1] or 0) >= 2 else "info",
                    "title": "廃棄率（新）ピーク月",
                    "text": (
                        f"{quality_peak[0]} の廃棄率（新） {quality_peak[1]:.2f}%"
                        f"（不良＋廃棄 {int(quality_peak[2] or 0):,} 本）"
                    ),
                }
            )
        rates = [
            (
                s.get("month_label"),
                s.get("all_process_loss_rate_percent"),
                s.get("sum_defect"),
                s.get("sum_scrap"),
            )
            for s in scrap_series
        ]
        peak = max(rates, key=lambda x: (x[1] is not None, x[1] or 0))
        if peak[1] is not None:
            highlights.append(
                {
                    "type": "scrap_peak",
                    "tone": "warn" if (peak[1] or 0) >= 2 else "info",
                    "title": "廃棄率（旧）ピーク月",
                    "text": (
                        f"{peak[0]} の廃棄率（旧） {peak[1]:.2f}%"
                        f"（不良＋廃棄 {int((peak[2] or 0) + (peak[3] or 0)):,} 本）"
                    ),
                }
            )
    highlights.append(
        {
            "type": "stocktake_match",
            "tone": "good" if avg_match_rate >= 95 else ("warn" if avg_match_rate >= 85 else "bad"),
            "title": "棚卸一致率（期間平均）",
            "text": f"平均一致率 {avg_match_rate:.2f}% / 差異絶対値合計 {total_diff_abs:,} 本",
        }
    )
    if bulk and bulk.get("count"):
        highlights.append(
            {
                "type": "bulk_disposal",
                "tone": "warn" if bulk.get("pending_count") else "info",
                "title": "大量廃棄・保留品・大量不良",
                "text": (
                    f"{bulk.get('count')} 件・合計 {int(bulk.get('total_quantity') or 0):,} 本"
                    f"（未処理 {bulk.get('pending_count')} 件）"
                ),
            }
        )
    if prev_compare:
        d = int(prev_compare.get("delta_total_qty") or 0)
        highlights.append(
            {
                "type": "qoq",
                "tone": "up" if d > 0 else ("down" if d < 0 else "flat"),
            "title": "前期間比（期末在庫）",
                "text": (
                    f"{prev_compare.get('label')} 比 {d:+,} 本"
                    f"（仕掛 {int(prev_compare.get('delta_wip_qty') or 0):+,} / "
                    f"製品 {int(prev_compare.get('delta_product_qty') or 0):+,}）"
                ),
            }
        )
    return highlights


def _row_to_dict(row: InventoryQuarterlyReport) -> dict:
    payload = {}
    scrap_overrides = {}
    try:
        payload = json.loads(row.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    try:
        scrap_overrides = json.loads(row.scrap_overrides_json or "{}")
    except json.JSONDecodeError:
        scrap_overrides = {}
    return {
        "id": row.id,
        "fiscal_year": row.fiscal_year,
        "quarter": row.quarter,
        "title": row.title,
        "status": row.status,
        "payload": payload,
        "scrap_overrides": scrap_overrides,
        "executive_summary": row.executive_summary,
        "action_items": row.action_items,
        "notes": row.notes,
        "generated_at": row.generated_at.strftime("%Y-%m-%d %H:%M:%S") if row.generated_at else None,
        "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
        "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else None,
    }


class SaveReportBody(BaseModel):
    fiscal_year: int = Field(..., ge=2000, le=2100)
    quarter: int = Field(..., ge=1, le=7, description="報告期間コード: Q1-Q4=1-4, 上期=5, 下期=6, 年間=7")
    title: Optional[str] = None
    status: str = "draft"
    payload: Optional[dict] = None
    scrap_overrides: Optional[dict] = None
    executive_summary: Optional[str] = None
    action_items: Optional[str] = None
    notes: Optional[str] = None
    regenerate: bool = False


@router.get("/quarters")
async def list_quarter_options(
    current_user: User = Depends(verify_token_and_get_user),
):
    """現在日時から近い年度と報告期間候補を返す。"""
    today = date.today()
    fy = today.year if today.month >= 4 else today.year - 1
    if today.month in (4, 5, 6):
        cq = 1
    elif today.month in (7, 8, 9):
        cq = 2
    elif today.month in (10, 11, 12):
        cq = 3
    else:
        cq = 4
    options = []
    for y in range(fy - 2, fy + 2):
        for q in range(1, 8):
            options.append(
                {
                    "fiscal_year": y,
                    "quarter": q,
                    "label": _quarter_label(y, q),
                    "is_current": y == fy and q == cq,
                }
            )
    return {"success": True, "data": {"current_fiscal_year": fy, "current_quarter": cq, "options": options}}


@router.get("/generate")
async def generate_inventory_report(
    fiscal_year: int = Query(..., ge=2000, le=2100),
    quarter: int = Query(..., ge=1, le=7),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """ライブ集計で四半期・半期・年間報告書ペイロードを生成（保存しない）。"""
    try:
        payload = await _build_quarter_payload(db, fiscal_year, quarter)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("在庫報告の生成に失敗")
        raise HTTPException(status_code=500, detail=f"報告書の生成に失敗しました: {exc}") from exc
    return {"success": True, "data": payload}


@router.get("/saved")
async def list_saved_reports(
    fiscal_year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    q = select(InventoryQuarterlyReport).order_by(
        InventoryQuarterlyReport.fiscal_year.desc(),
        InventoryQuarterlyReport.quarter.desc(),
    )
    if fiscal_year is not None:
        q = q.where(InventoryQuarterlyReport.fiscal_year == fiscal_year)
    rows = list((await db.execute(q)).scalars().all())
    return {
        "success": True,
        "data": {
            "list": [
                {
                    "id": r.id,
                    "fiscal_year": r.fiscal_year,
                    "quarter": r.quarter,
                    "title": r.title,
                    "status": r.status,
                    "label": _quarter_label(r.fiscal_year, r.quarter),
                    "generated_at": r.generated_at.strftime("%Y-%m-%d %H:%M:%S") if r.generated_at else None,
                    "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None,
                }
                for r in rows
            ]
        },
    }


@router.get("/saved/{report_id}")
async def get_saved_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    row = (
        await db.execute(select(InventoryQuarterlyReport).where(InventoryQuarterlyReport.id == report_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="報告書が見つかりません")
    return {"success": True, "data": _row_to_dict(row)}


@router.post("/saved")
async def save_inventory_report(
    body: SaveReportBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    status = (body.status or "draft").strip().lower()
    if status not in ("draft", "final"):
        raise HTTPException(status_code=422, detail="status は draft または final です")

    payload = body.payload
    generated_at = datetime.now()
    if body.regenerate or payload is None:
        payload = await _build_quarter_payload(db, body.fiscal_year, body.quarter)

    existing = (
        await db.execute(
            select(InventoryQuarterlyReport).where(
                InventoryQuarterlyReport.fiscal_year == body.fiscal_year,
                InventoryQuarterlyReport.quarter == body.quarter,
            )
        )
    ).scalar_one_or_none()

    title = (body.title or "").strip() or _default_title(body.fiscal_year, body.quarter)
    scrap_json = json.dumps(body.scrap_overrides or {}, ensure_ascii=False)
    payload_json = json.dumps(payload, ensure_ascii=False)

    if existing:
        existing.title = title
        existing.status = status
        existing.payload_json = payload_json
        existing.scrap_overrides_json = scrap_json
        existing.executive_summary = body.executive_summary
        existing.action_items = body.action_items
        existing.notes = body.notes
        existing.generated_at = generated_at
        existing.updated_by_user_id = current_user.id
        row = existing
    else:
        row = InventoryQuarterlyReport(
            fiscal_year=body.fiscal_year,
            quarter=body.quarter,
            title=title,
            status=status,
            payload_json=payload_json,
            scrap_overrides_json=scrap_json,
            executive_summary=body.executive_summary,
            action_items=body.action_items,
            notes=body.notes,
            generated_at=generated_at,
            created_by_user_id=current_user.id,
            updated_by_user_id=current_user.id,
        )
        db.add(row)

    await db.commit()
    await db.refresh(row)
    return {"success": True, "data": _row_to_dict(row)}


@router.delete("/saved/{report_id}")
async def delete_saved_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("delete")),
):
    row = (
        await db.execute(select(InventoryQuarterlyReport).where(InventoryQuarterlyReport.id == report_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="報告書が見つかりません")
    await db.delete(row)
    await db.commit()
    return {"success": True, "data": {"id": report_id}}

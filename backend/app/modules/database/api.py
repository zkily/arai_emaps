"""
production_summarys API（一覧・製品リスト・データ生成）
"""
import calendar
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, Body

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, tuple_, text
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ConfigDict
import math
import re
import time
from typing import Optional
from datetime import date, timedelta, datetime
from datetime import time as dt_time
from decimal import Decimal

from app.modules.auth.api import verify_token_and_get_user
from app.core.datetime_utils import now_jst, JST
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.database.models import ProductionSummary
from app.modules.master.models import Product, ProductProcessBOM, ProcessRoute, ProcessRouteStep, Destination
from app.modules.erp.stock_transaction_log_models import StockTransactionLog

router = APIRouter(prefix="/production-summarys", tags=["production-summarys"])

# 一括更新用分散ロック（他端末同時実行防止）
BATCH_UPDATE_LOCK_KEY = "production_summary_batch_update"
DEFAULT_LOCK_TTL_SECONDS = 300  # 5分で自動解放

# 繰越クリア対象の全工程カラム（KT13=倉庫, KT15=外注倉庫 を分離）
CARRY_OVER_COLUMNS = [
    "cutting_carry_over", "chamfering_carry_over", "molding_carry_over", "plating_carry_over",
    "welding_carry_over", "inspection_carry_over", "warehouse_carry_over", "outsourced_warehouse_carry_over",
    "outsourced_plating_carry_over", "outsourced_welding_carry_over",
    "pre_welding_inspection_carry_over", "pre_inspection_carry_over", "pre_outsourcing_carry_over",
]
# process_cd → production_summarys 繰越カラム名（KT13=倉庫, KT10/KT15=外注倉庫）
PROCESS_CARRY_OVER_MAPPING = {
    "KT01": "cutting_carry_over",
    "KT02": "chamfering_carry_over",
    "KT04": "molding_carry_over",
    "KT05": "plating_carry_over",
    "KT07": "welding_carry_over",
    "KT09": "inspection_carry_over",
    "KT13": "warehouse_carry_over",
    "KT10": "outsourced_warehouse_carry_over",
    "KT15": "outsourced_warehouse_carry_over",
    "KT06": "outsourced_plating_carry_over",
    "KT08": "outsourced_welding_carry_over",
    "KT11": "pre_welding_inspection_carry_over",
    "KT16": "pre_inspection_carry_over",
    "KT17": "pre_outsourcing_carry_over",
}

# 実績更新：process_cd → production_summarys の actual 列（一般工程 11 + KT13/KT15 は別クエリ）
PROCESS_ACTUAL_MAPPING = {
    "KT01": "cutting_actual",
    "KT02": "chamfering_actual",
    "KT04": "molding_actual",
    "KT05": "plating_actual",
    "KT07": "welding_actual",
    "KT09": "inspection_actual",
    "KT06": "outsourced_plating_actual",
    "KT08": "outsourced_welding_actual",
    "KT11": "pre_welding_inspection_actual",
    "KT16": "pre_inspection_actual",
    "KT17": "pre_outsourcing_actual",
}
ACTUAL_CLEAR_COLUMNS = [
    "cutting_actual", "chamfering_actual", "molding_actual", "plating_actual",
    "welding_actual", "inspection_actual", "warehouse_actual",
    "outsourced_plating_actual", "outsourced_welding_actual",
    "pre_welding_inspection_actual", "pre_inspection_actual", "pre_outsourcing_actual",
    "outsourced_warehouse_actual",
]
GENERAL_PROCESS_CDS = list(PROCESS_ACTUAL_MAPPING.keys())

# 不良データ更新：7 工程のみ（KT06/KT08/KT13/KT15/KT16/KT17 は対象外）
PROCESS_DEFECT_MAPPING = {
    "KT01": "cutting_defect",
    "KT02": "chamfering_defect",
    "KT04": "molding_defect",
    "KT05": "plating_defect",
    "KT07": "welding_defect",
    "KT09": "inspection_defect",
    "KT11": "pre_welding_inspection_defect",
}
DEFECT_PROCESS_CDS = list(PROCESS_DEFECT_MAPPING.keys())

# 廃棄データ更新：12 工程（倉庫・外注含む）
PROCESS_SCRAP_MAPPING = {
    "KT01": "cutting_scrap",
    "KT02": "chamfering_scrap",
    "KT04": "molding_scrap",
    "KT05": "plating_scrap",
    "KT07": "welding_scrap",
    "KT09": "inspection_scrap",
    "KT13": "warehouse_scrap",
    "KT06": "outsourced_plating_scrap",
    "KT08": "outsourced_welding_scrap",
    "KT11": "pre_welding_inspection_scrap",
    "KT16": "pre_inspection_scrap",
    "KT17": "pre_outsourcing_scrap",
}
SCRAP_PROCESS_CDS = list(PROCESS_SCRAP_MAPPING.keys())

# 保留データ更新：8 工程（KT06/KT08/KT16/KT17 は対象外）
PROCESS_ON_HOLD_MAPPING = {
    "KT01": "cutting_on_hold",
    "KT02": "chamfering_on_hold",
    "KT04": "molding_on_hold",
    "KT05": "plating_on_hold",
    "KT07": "welding_on_hold",
    "KT09": "inspection_on_hold",
    "KT13": "warehouse_on_hold",
    "KT11": "pre_welding_inspection_on_hold",
}
ON_HOLD_PROCESS_CDS = list(PROCESS_ON_HOLD_MAPPING.keys())
# 保留列一括クリア用（PROCESS_ON_HOLD 未対応の外注系 on_hold も含む全列）
ON_HOLD_CLEAR_COLUMNS = [
    "cutting_on_hold",
    "chamfering_on_hold",
    "molding_on_hold",
    "plating_on_hold",
    "welding_on_hold",
    "inspection_on_hold",
    "warehouse_on_hold",
    "outsourced_warehouse_on_hold",
    "outsourced_plating_on_hold",
    "outsourced_welding_on_hold",
    "pre_welding_inspection_on_hold",
]
# 不良列一括クリア用（PROCESS_DEFECT 未対応の倉庫・外注系 defect も含む models 上の全列）
DEFECT_CLEAR_COLUMNS = [
    "cutting_defect",
    "chamfering_defect",
    "molding_defect",
    "plating_defect",
    "welding_defect",
    "inspection_defect",
    "warehouse_defect",
    "outsourced_warehouse_defect",
    "outsourced_plating_defect",
    "outsourced_welding_defect",
    "pre_welding_inspection_defect",
]
# 廃棄列一括クリア用（PROCESS_SCRAP 未対応の outsourced_warehouse_scrap も含む models 上の全列）
SCRAP_CLEAR_COLUMNS = [
    "cutting_scrap",
    "chamfering_scrap",
    "molding_scrap",
    "plating_scrap",
    "welding_scrap",
    "inspection_scrap",
    "warehouse_scrap",
    "outsourced_warehouse_scrap",
    "outsourced_plating_scrap",
    "outsourced_welding_scrap",
    "pre_welding_inspection_scrap",
    "pre_inspection_scrap",
    "pre_outsourcing_scrap",
]

# 在庫・推移更新：process_cd → 列プレフィックス（cutting, chamfering, ... warehouse, outsourced_warehouse）
PROCESS_CD_TO_PREFIX = {
    "KT01": "cutting", "KT02": "chamfering", "KT04": "molding", "KT05": "plating",
    "KT07": "welding", "KT09": "inspection", "KT13": "warehouse", "KT15": "outsourced_warehouse",
    "KT06": "outsourced_plating", "KT08": "outsourced_welding",
    "KT11": "pre_welding_inspection", "KT16": "pre_inspection", "KT17": "pre_outsourcing",
}
# process_cd → production_summarys の *_inventory 列（棚卸繰越プレビュー：対象月末日の行を参照）
# KT10/KT15 はいずれも outsourced_warehouse_inventory（マスタの工程CD差異に対応）
PROCESS_INVENTORY_MAPPING = {
    "KT01": "cutting_inventory",
    "KT02": "chamfering_inventory",
    "KT04": "molding_inventory",
    "KT05": "plating_inventory",
    "KT06": "outsourced_plating_inventory",
    "KT07": "welding_inventory",
    "KT08": "outsourced_welding_inventory",
    "KT09": "inspection_inventory",
    "KT13": "warehouse_inventory",
    "KT10": "outsourced_warehouse_inventory",
    "KT15": "outsourced_warehouse_inventory",
    "KT11": "pre_welding_inspection_inventory",
    "KT16": "pre_inspection_inventory",
    "KT17": "pre_outsourcing_inventory",
}
# process_cd → actual 列（下一工程実績用；KT15 は outsourced_warehouse_actual）
PROCESS_CD_TO_ACTUAL = {**PROCESS_ACTUAL_MAPPING, "KT15": "outsourced_warehouse_actual"}
# 在庫列一覧（一般工程 + warehouse + outsourced_warehouse）
INVENTORY_COLUMNS = [
    "cutting_inventory", "chamfering_inventory", "molding_inventory", "plating_inventory",
    "welding_inventory", "inspection_inventory", "warehouse_inventory", "outsourced_warehouse_inventory",
    "outsourced_plating_inventory", "outsourced_welding_inventory",
    "pre_welding_inspection_inventory", "pre_inspection_inventory", "pre_outsourcing_inventory",
]
# 推移・実計推移の対象 6 工程（cutting, chamfering, molding, plating, welding, inspection）
TREND_PREFIXES = ["cutting", "chamfering", "molding", "plating", "welding", "inspection"]

# 計画データ更新：schedule_details × 設備 machine_type → processes.process_name → production_summarys の _plan 列（6工程）
PLAN_PROCESS_MAPPING = {
    "成型": "molding_plan",
    "溶接": "welding_plan",
    "メッキ": "plating_plan",
    "切断": "cutting_plan",
    "面取": "chamfering_plan",
    "検査": "inspection_plan",
}
# 計画データ更新前クリア用（_plan + _actual_plan）
PLAN_FIELDS_TO_CLEAR = list(PLAN_PROCESS_MAPPING.values()) + ["sw_plan"]
# 清空计算字段（在庫・推移・actual_plan_trend・安全在庫）：date >= startDate 时置 0
CALCULATED_FIELDS_TO_CLEAR = [
    "safety_stock",
    "cutting_inventory", "cutting_trend", "cutting_actual_plan_trend",
    "chamfering_inventory", "chamfering_trend", "chamfering_actual_plan_trend",
    "molding_inventory", "molding_trend", "molding_actual_plan_trend",
    "plating_inventory", "plating_trend", "plating_actual_plan_trend",
    "welding_inventory", "welding_trend", "welding_actual_plan_trend",
    "inspection_inventory", "inspection_trend", "inspection_actual_plan_trend",
    "warehouse_inventory", "warehouse_trend",
    "outsourced_warehouse_inventory", "outsourced_warehouse_trend",
    "outsourced_plating_inventory", "outsourced_plating_trend", "outsourced_plating_actual_plan_trend",
    "outsourced_welding_inventory", "outsourced_welding_trend", "outsourced_welding_actual_plan_trend",
    "pre_welding_inspection_inventory", "pre_welding_inspection_trend",
    "pre_inspection_inventory", "pre_inspection_trend",
    "pre_outsourcing_inventory", "pre_outsourcing_trend",
]
# actual_plan 列更新：(actual 列, plan 列) → actual_plan 列（実績优先、計画补齐）
ACTUAL_PLAN_COLUMNS = [
    ("cutting_actual", "cutting_plan", "cutting_actual_plan"),
    ("chamfering_actual", "chamfering_plan", "chamfering_actual_plan"),
    ("molding_actual", "molding_plan", "molding_actual_plan"),
    ("plating_actual", "plating_plan", "plating_actual_plan"),
    ("welding_actual", "welding_plan", "welding_actual_plan"),
    ("inspection_actual", "inspection_plan", "inspection_actual_plan"),
]
ACTUAL_PLAN_FIELDS_TO_CLEAR = [target_col for _, _, target_col in ACTUAL_PLAN_COLUMNS]
PLAN_AND_ACTUAL_PLAN_FIELDS_TO_CLEAR = PLAN_FIELDS_TO_CLEAR + ACTUAL_PLAN_FIELDS_TO_CLEAR

# 計画列（_plan / _actual_plan）のクリアおよび schedule からの plan 反映の終了：開始日からこの月数後の月末まで
PLAN_PERIOD_MONTHS = 5

# 生産計画日更新：production_summarys の *_production_date と product_process_bom の *_process_lt 対応
# (production_date 列名, BOM の lt 列名) — 注: BOM は cuting の typo
PRODUCTION_DATE_LT_MAPPING = [
    ("cutting_production_date", "cuting_process_lt"),
    ("chamfering_production_date", "chamfering_process_lt"),
    ("molding_production_date", "forming_process_lt"),
    ("plating_production_date", "plating_process_lt"),
    ("welding_production_date", "welding_process_lt"),
    ("inspection_production_date", "inspection_process_lt"),
    ("outsourced_plating_production_date", "outsourced_plating_process_lt"),
    ("outsourced_welding_production_date", "outsourced_welding_process_lt"),
]

DAY_OF_WEEK_JA = ("月", "火", "水", "木", "金", "土", "日")


def _row_to_dict(row) -> dict:
    """ORM 行を辞書に（日付は文字列）"""
    d = {}
    for c in row.__table__.columns:
        v = getattr(row, c.name)
        if hasattr(v, "isoformat"):
            d[c.name] = v.isoformat() if v else None
        else:
            d[c.name] = v
    return d


@router.get("")
async def get_production_summarys_list(
    page: int = Query(1, ge=1, description="ページ"),
    limit: int = Query(150, ge=1, le=50000, description="件数（印刷用など最大50000）"),
    startDate: Optional[str] = Query(None, description="開始日 YYYY-MM-DD"),
    endDate: Optional[str] = Query(None, description="終了日 YYYY-MM-DD"),
    productCd: Optional[str] = Query(None, description="製品CD"),
    keyword: Optional[str] = Query(None, description="製品名キーワード"),
    sortBy: Optional[str] = Query("product_name", description="ソート項目"),
    sortOrder: Optional[str] = Query("ASC", description="ASC/DESC"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """生産サマリー一覧（ページネーション）"""
    q = select(ProductionSummary)
    count_q = select(func.count()).select_from(ProductionSummary)
    conds = []
    if startDate:
        conds.append(ProductionSummary.date >= startDate)
    if endDate:
        conds.append(ProductionSummary.date <= endDate)
    if productCd:
        conds.append(ProductionSummary.product_cd == productCd)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        conds.append(
            or_(
                ProductionSummary.product_name.ilike(k),
                ProductionSummary.product_cd.ilike(k),
            )
        )
    if conds:
        q = q.where(and_(*conds))
        count_q = count_q.where(and_(*conds))
    # ソート
    sort_col = getattr(ProductionSummary, sortBy, None) or ProductionSummary.product_name
    if sortOrder == "DESC":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())
    # ページネーション
    offset = (page - 1) * limit
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    list_data = [_row_to_dict(r) for r in rows]
    await _enrich_production_summary_rows_pre_plating_inventory(db, list_data)
    return {
        "data": {
            "list": list_data,
            "pagination": {"total": total, "page": page, "limit": limit},
        }
    }


# 工程別 (不良+廃棄)/実績：production_summarys を期間集計（列名はホワイトリストのみ）
_QUALITY_RATE_BY_PROCESS_DEFS: tuple[tuple[str, str, str, str | None, str], ...] = (
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

# 主ライン（切断～検査）：連乘合格率 RTY および製品別集計で共通利用
_MAIN_LINE_PROCESS_KEYS: tuple[str, ...] = (
    "cutting",
    "chamfering",
    "molding",
    "plating",
    "welding",
    "inspection",
)


def _compute_rolled_main_line_yield_loss(metrics_by_key: dict[str, dict]) -> tuple[float | None, float | None]:
    """
    r_i = (不良+廃棄)/実績 を各主ライン工程で算出し、
    RTY = Π(1 - r_i)（実績>0 の工程のみ積に参加）、連乘損失率 = 1 - RTY。
    """
    prod_pass = 1.0
    used = False
    for key in _MAIN_LINE_PROCESS_KEYS:
        m = metrics_by_key.get(key)
        if not m:
            continue
        sa = int(m.get("sum_actual") or 0)
        if sa <= 0:
            continue
        bad = int(m.get("sum_defect_and_scrap") or 0)
        ri = bad / sa
        if ri > 1.0:
            ri = 1.0
        elif ri < 0.0:
            ri = 0.0
        prod_pass *= 1.0 - ri
        used = True
    if not used:
        return None, None
    ry = round(prod_pass, 8)
    loss = round(1.0 - ry, 8)
    return ry, loss


@router.get("/quality-rate-by-process")
async def get_quality_rate_by_process(
    startDate: str = Query(..., description="集計開始日 YYYY-MM-DD"),
    endDate: str = Query(..., description="集計終了日 YYYY-MM-DD"),
    process: Optional[str] = Query(
        None,
        description="工程キー（cutting / molding 等）。省略時は全工程を返す",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    production_summarys を指定期間で工程別に SUM し、各工程について (defect+scrap)/actual を算出する。
    actual が 0 の工程は rate は null。

    一覧の「全体比率」に相当する値として、各工程の *_actual を合計してはならない（同一ロットが工程間で二重計上される）。
    フィルタなし時の summary は主ライン（切断～検査）について RTY=Π(1-r_i)、連乘損失率=1-RTY。
    フィルタあり時は選択工程の行と同一とする。
    """
    try:
        start_d = date.fromisoformat(startDate.strip()[:10])
        end_d = date.fromisoformat(endDate.strip()[:10])
    except ValueError:
        raise HTTPException(status_code=422, detail="startDate / endDate は YYYY-MM-DD 形式で指定してください")
    if start_d > end_d:
        raise HTTPException(status_code=422, detail="開始日は終了日以前である必要があります")

    allowed_keys = {t[0] for t in _QUALITY_RATE_BY_PROCESS_DEFS}
    if process is not None and process.strip() != "" and process.strip() not in allowed_keys:
        raise HTTPException(
            status_code=422,
            detail=f"process は次のいずれかです: {', '.join(sorted(allowed_keys))}",
        )

    sum_parts: list[str] = []
    for key, _label, actual_col, defect_col, scrap_col in _QUALITY_RATE_BY_PROCESS_DEFS:
        sum_parts.append(f"SUM(COALESCE(`{actual_col}`, 0)) AS `{key}_actual`")
        if defect_col:
            sum_parts.append(f"SUM(COALESCE(`{defect_col}`, 0)) AS `{key}_defect`")
        else:
            sum_parts.append(f"0 AS `{key}_defect`")
        sum_parts.append(f"SUM(COALESCE(`{scrap_col}`, 0)) AS `{key}_scrap`")

    sql = (
        "SELECT "
        + ", ".join(sum_parts)
        + " FROM production_summarys WHERE `date` >= :start_date AND `date` <= :end_date"
    )
    row = (await db.execute(text(sql), {"start_date": start_d, "end_date": end_d})).mappings().first()
    if row is None:
        row = {}

    def _num(v) -> int:
        if v is None:
            return 0
        if isinstance(v, Decimal):
            return int(v)
        return int(v)

    proc_filter = process.strip() if process and process.strip() else None

    metrics_by_key: dict[str, dict] = {}
    for key, label, _a, _d, _s in _QUALITY_RATE_BY_PROCESS_DEFS:
        sa = _num(row.get(f"{key}_actual"))
        sd = _num(row.get(f"{key}_defect"))
        ss = _num(row.get(f"{key}_scrap"))
        bad = sd + ss
        rate = None
        if sa > 0:
            rate = round(bad / sa, 6)
        metrics_by_key[key] = {
            "key": key,
            "label": label,
            "sum_actual": sa,
            "sum_defect": sd,
            "sum_scrap": ss,
            "sum_defect_and_scrap": bad,
            "rate": rate,
            "rate_percent": round(rate * 100, 4) if rate is not None else None,
        }

    processes_out: list[dict] = []
    for key, _label, _a, _d, _s in _QUALITY_RATE_BY_PROCESS_DEFS:
        if proc_filter and key != proc_filter:
            continue
        processes_out.append(metrics_by_key[key])

    if proc_filter:
        ref_key = proc_filter
        summary_basis = "selected_process"
        ref = metrics_by_key.get(ref_key) or {
            "key": ref_key,
            "label": "",
            "sum_actual": 0,
            "sum_defect": 0,
            "sum_scrap": 0,
            "sum_defect_and_scrap": 0,
            "rate": None,
            "rate_percent": None,
        }
        summary_payload = {
            "basis": summary_basis,
            "reference_process_key": ref["key"],
            "reference_process_label": ref["label"],
            "sum_actual": ref["sum_actual"],
            "sum_defect": ref["sum_defect"],
            "sum_scrap": ref["sum_scrap"],
            "sum_defect_and_scrap": ref["sum_defect_and_scrap"],
            "rate": ref["rate"],
            "rate_percent": ref["rate_percent"],
            "rolled_yield_rate": None,
            "rolled_yield_percent": None,
        }
    else:
        ry, loss = _compute_rolled_main_line_yield_loss(metrics_by_key)
        summary_payload = {
            "basis": "rolled_main_line",
            "reference_process_key": "main_line_rolled",
            "reference_process_label": "主ライン連乘",
            "sum_actual": 0,
            "sum_defect": 0,
            "sum_scrap": 0,
            "sum_defect_and_scrap": 0,
            "rate": loss,
            "rate_percent": round(loss * 100, 4) if loss is not None else None,
            "rolled_yield_rate": ry,
            "rolled_yield_percent": round(ry * 100, 4) if ry is not None else None,
        }

    # 画面カード用：全工程（定義済み工程キー）の不良＋廃棄を単純合計（同一ロットの二重計上は含む）
    total_defect_scrap_all_processes = sum(int(m.get("sum_defect_and_scrap") or 0) for m in metrics_by_key.values())

    return {
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "process_filter": proc_filter,
            "processes": processes_out,
            "summary": summary_payload,
            "all_processes_defect_scrap_total": total_defect_scrap_all_processes,
        }
    }


def _main_line_group_select_columns() -> str:
    parts: list[str] = []
    for key, _label, actual_col, defect_col, scrap_col in _QUALITY_RATE_BY_PROCESS_DEFS:
        if key not in _MAIN_LINE_PROCESS_KEYS:
            continue
        parts.append(f"SUM(COALESCE(`{actual_col}`, 0)) AS `{key}_actual`")
        if defect_col:
            parts.append(f"SUM(COALESCE(`{defect_col}`, 0)) AS `{key}_defect`")
        else:
            parts.append(f"0 AS `{key}_defect`")
        parts.append(f"SUM(COALESCE(`{scrap_col}`, 0)) AS `{key}_scrap`")
    return ", ".join(parts)


def _per_row_all_processes_defect_scrap_expr() -> str:
    """1 行分：定義済み全工程の不良＋廃棄（defect 列なしの工程は廃棄のみ）。"""
    terms: list[str] = []
    for _key, _label, _a, defect_col, scrap_col in _QUALITY_RATE_BY_PROCESS_DEFS:
        if defect_col:
            terms.append(f"(COALESCE(`{defect_col}`, 0) + COALESCE(`{scrap_col}`, 0))")
        else:
            terms.append(f"COALESCE(`{scrap_col}`, 0)")
    return "(" + " + ".join(terms) + ")"


def _all_processes_defect_scrap_sum_select() -> str:
    inner = _per_row_all_processes_defect_scrap_expr()
    return f"COALESCE(SUM({inner}), 0) AS `all_processes_defect_scrap`"


# 製品別主ライン一覧の ORDER BY（ホワイトリストのみ・SQL 直結合禁止）
_PRODUCT_MATRIX_SORT_FIELDS: frozenset[str] = frozenset(
    {"product_cd", "product_name", "all_processes_defect_scrap", "rty", "rty_loss", *_MAIN_LINE_PROCESS_KEYS}
)


def _product_matrix_rate_order_expr(process_key: str) -> str:
    """主ライン 1 工程の (不良+廃棄)/実績。実績 0 は NULL（ソートで末尾扱い）。"""
    if process_key not in _MAIN_LINE_PROCESS_KEYS:
        raise ValueError(process_key)
    a = f"`{process_key}_actual`"
    d = f"`{process_key}_defect`"
    s = f"`{process_key}_scrap`"
    return f"(COALESCE({d}, 0) + COALESCE({s}, 0)) * 1.0 / NULLIF({a}, 0)"


def _product_matrix_rty_product_expr() -> str:
    """Π(1−r_i)（実績>0 の工程のみ参加、他は 1）。フロント computeProductMainLineRty と整合。"""
    parts: list[str] = []
    for k in _MAIN_LINE_PROCESS_KEYS:
        a, d, s = f"`{k}_actual`", f"`{k}_defect`", f"`{k}_scrap`"
        parts.append(
            f"IF(COALESCE({a}, 0) > 0, "
            f"1 - LEAST(1, GREATEST(0, (COALESCE({d}, 0) + COALESCE({s}, 0)) * 1.0 / NULLIF({a}, 0))), "
            f"1)"
        )
    return "(" + " * ".join(parts) + ")"


def _product_matrix_has_any_actual_expr() -> str:
    inner = ", ".join(f"COALESCE(`{k}_actual`, 0)" for k in _MAIN_LINE_PROCESS_KEYS)
    return f"GREATEST({inner})"


def _product_matrix_rty_sort_expr() -> str:
    has = _product_matrix_has_any_actual_expr()
    prod = _product_matrix_rty_product_expr()
    return f"(CASE WHEN {has} <= 0 THEN NULL ELSE {prod} END)"


def _product_matrix_rty_loss_sort_expr() -> str:
    has = _product_matrix_has_any_actual_expr()
    prod = _product_matrix_rty_product_expr()
    return f"(CASE WHEN {has} <= 0 THEN NULL ELSE (1 - ({prod})) END)"


def _product_matrix_order_clause(sort_by: str, sort_order: str) -> str:
    asc = (sort_order or "asc").strip().lower() != "desc"
    direction = "ASC" if asc else "DESC"

    def _simple(col: str) -> str:
        return f"{col} {direction}, `product_cd` ASC"

    def _nulls_last(expr: str) -> str:
        return (
            f"(CASE WHEN ({expr}) IS NULL THEN 1 ELSE 0 END) ASC, "
            f"({expr}) {direction}, `product_cd` ASC"
        )

    sb = (sort_by or "product_name").strip()
    if sb not in _PRODUCT_MATRIX_SORT_FIELDS:
        sb = "product_name"
    if sb == "product_cd":
        return _simple("`product_cd`")
    if sb == "product_name":
        return _simple("`product_name`")
    if sb == "all_processes_defect_scrap":
        return _simple("`all_processes_defect_scrap`")
    if sb == "rty":
        return _nulls_last(_product_matrix_rty_sort_expr())
    if sb == "rty_loss":
        return _nulls_last(_product_matrix_rty_loss_sort_expr())
    if sb in _MAIN_LINE_PROCESS_KEYS:
        return _nulls_last(_product_matrix_rate_order_expr(sb))
    return _simple("`product_name`")


def _product_row_to_main_line_processes(row: dict) -> list[dict]:
    """GROUP BY 行を製品単位の主ライン工程メトリクスに変換"""
    out: list[dict] = []
    for key, label, _a, _d, _s in _QUALITY_RATE_BY_PROCESS_DEFS:
        if key not in _MAIN_LINE_PROCESS_KEYS:
            continue
        def _n(v) -> int:
            if v is None:
                return 0
            if isinstance(v, Decimal):
                return int(v)
            return int(v)

        sa = _n(row.get(f"{key}_actual"))
        sd = _n(row.get(f"{key}_defect"))
        ss = _n(row.get(f"{key}_scrap"))
        bad = sd + ss
        rate = None
        if sa > 0:
            rate = round(bad / sa, 6)
        out.append(
            {
                "key": key,
                "label": label,
                "sum_actual": sa,
                "sum_defect": sd,
                "sum_scrap": ss,
                "sum_defect_and_scrap": bad,
                "rate": rate,
                "rate_percent": round(rate * 100, 4) if rate is not None else None,
            }
        )
    return out


@router.get("/quality-rate-by-product")
async def get_quality_rate_by_product(
    startDate: str = Query(..., description="集計開始日 YYYY-MM-DD"),
    endDate: str = Query(..., description="集計終了日 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    productCd: Optional[str] = Query(None, description="製品CD 完全一致"),
    keyword: Optional[str] = Query(None, description="製品CD・製品名 の部分一致"),
    sortBy: str = Query(
        "product_name",
        description="ソート列: product_cd, product_name, all_processes_defect_scrap, 主ライン工程キー(cutting等), rty, rty_loss",
    ),
    sortOrder: str = Query("asc", description="asc または desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    製品別に production_summarys を期間 SUM（GROUP BY product_cd）。
    各製品について主ライン（切断～検査）の各工程で (不良+廃棄)/実績 を算出する。

    - 同一製品の複数日・複数行は product_cd でまとめて集計する。
    - 主ラインに存在しない工程は実績が 0 のことがあり、その工程の比率は null。
    - all_processes_defect_scrap: 期間内・定義済み全工程の不良＋廃棄を日次行ごとに合算してから product_cd で SUM。
    """
    try:
        start_d = date.fromisoformat(startDate.strip()[:10])
        end_d = date.fromisoformat(endDate.strip()[:10])
    except ValueError:
        raise HTTPException(status_code=422, detail="startDate / endDate は YYYY-MM-DD 形式で指定してください")
    if start_d > end_d:
        raise HTTPException(status_code=422, detail="開始日は終了日以前である必要があります")

    agg_cols = _main_line_group_select_columns()
    all_bad_sum = _all_processes_defect_scrap_sum_select()
    base_where = "`date` >= :start_date AND `date` <= :end_date AND `product_cd` IS NOT NULL AND TRIM(`product_cd`) != ''"
    params: dict = {"start_date": start_d, "end_date": end_d}

    kw_clause = ""
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        params["kw"] = kw
        kw_clause = " AND (`product_name` LIKE :kw OR `product_cd` LIKE :kw)"

    pcd_clause = ""
    if productCd and productCd.strip():
        params["product_cd_eq"] = productCd.strip()
        pcd_clause = " AND `product_cd` = :product_cd_eq"

    count_sql = (
        "SELECT COUNT(*) AS c FROM ("
        f" SELECT `product_cd` FROM `production_summarys` WHERE {base_where}{kw_clause}{pcd_clause}"
        " GROUP BY `product_cd`"
        ") x"
    )
    count_row = (await db.execute(text(count_sql), params)).mappings().first()
    total = int(count_row["c"]) if count_row and count_row.get("c") is not None else 0

    offset = (page - 1) * limit
    params_page = {**params, "limit": limit, "offset": offset}

    so = (sortOrder or "asc").strip().lower()
    if so not in ("asc", "desc"):
        so = "asc"
    order_sql = _product_matrix_order_clause(sortBy, so)

    # 内側で GROUP BY 集計し、外側で ORDER BY する（ORDER BY が集計エイリアスを参照するため
    # only_full_group_by 下では単一 SELECT に直書きできない）
    inner_list_sql = (
        "SELECT `product_cd`, MAX(`product_name`) AS `product_name`, "
        f"{all_bad_sum}, {agg_cols} FROM `production_summarys` WHERE {base_where}{kw_clause}{pcd_clause}"
        " GROUP BY `product_cd`"
    )
    list_sql = f"SELECT * FROM ({inner_list_sql}) `_p` ORDER BY {order_sql} LIMIT :limit OFFSET :offset"
    result = await db.execute(text(list_sql), params_page)
    raw_rows = result.mappings().all()

    products_out: list[dict] = []
    for r in raw_rows:
        rd = dict(r)
        pcd = (rd.get("product_cd") or "").strip()
        if not pcd:
            continue
        products_out.append(
            {
                "product_cd": pcd,
                "product_name": rd.get("product_name") or "",
                "all_processes_defect_scrap": int(rd.get("all_processes_defect_scrap") or 0),
                "processes": _product_row_to_main_line_processes(rd),
            }
        )

    _label_by_key = {t[0]: t[1] for t in _QUALITY_RATE_BY_PROCESS_DEFS}
    return {
        "data": {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "scope": "main_line_cutting_to_inspection",
            "main_line_labels": [
                {"key": k, "label": _label_by_key.get(k, k)} for k in _MAIN_LINE_PROCESS_KEYS
            ],
            "pagination": {"total": total, "page": page, "limit": limit},
            "products": products_out,
        }
    }


@router.get("/inventory-stagnation")
async def get_inventory_stagnation(
    as_of: Optional[str] = Query(None, description="基準日 YYYY-MM-DD（省略時: JST 当日）"),
    min_quantity: int = Query(50, ge=0, description="この値より大きい同一在庫値のみを対象"),
    stable_calendar_days: int = Query(7, ge=2, le=60, description="連続同一値と判定する暦日数"),
    productCd: Optional[str] = Query(None, description="製品CD絞込"),
    keyword: Optional[str] = Query(None, description="製品名・製品CDキーワード"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    在庫タブ基準の停滞製品検知。

    - production_summarys の *_inventory 列（INVENTORY_COLUMNS と同一セット）を (product_cd, route_cd) 単位で
      連続 stable_calendar_days 暦日分スキャンし、その窓内すべて同一値かつ min_quantity より大きい列を列挙する。
    - 連続日数は暦日ベース。期間内に1日でも行が欠けた (product_cd, route_cd) は対象外（厳格）。
    - NULL は 0 と同一視して比較。全日 NULL の列は対象外。
    """
    if as_of and as_of.strip():
        try:
            as_of_d = date.fromisoformat(as_of.strip()[:10])
        except ValueError:
            raise HTTPException(status_code=422, detail="as_of は YYYY-MM-DD 形式で指定してください")
    else:
        as_of_d = now_jst().date()

    window_days = int(stable_calendar_days)
    start_d = as_of_d - timedelta(days=window_days - 1)
    required_dates = [start_d + timedelta(days=i) for i in range(window_days)]

    inventory_attrs = [getattr(ProductionSummary, c) for c in INVENTORY_COLUMNS]
    q = select(
        ProductionSummary.product_cd,
        ProductionSummary.product_name,
        ProductionSummary.route_cd,
        ProductionSummary.date,
        *inventory_attrs,
    ).where(
        and_(
            ProductionSummary.date >= start_d,
            ProductionSummary.date <= as_of_d,
            ProductionSummary.product_cd.isnot(None),
            ProductionSummary.product_cd != "",
        )
    )
    if productCd and productCd.strip():
        q = q.where(ProductionSummary.product_cd == productCd.strip())
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                ProductionSummary.product_name.ilike(k),
                ProductionSummary.product_cd.ilike(k),
            )
        )
    q = q.order_by(
        ProductionSummary.product_cd,
        ProductionSummary.route_cd,
        ProductionSummary.date,
    )
    rows = (await db.execute(q)).all()

    buckets: dict[tuple, dict] = {}
    for r in rows:
        pcd = (r.product_cd or "").strip()
        rcd = (r.route_cd or "").strip()
        if not pcd:
            continue
        key = (pcd, rcd)
        entry = buckets.get(key)
        if entry is None:
            entry = {
                "product_cd": pcd,
                "product_name": r.product_name or "",
                "route_cd": rcd,
                "rows_by_date": {},
            }
            buckets[key] = entry
        d = r.date
        if isinstance(d, str):
            try:
                d = date.fromisoformat(d[:10])
            except ValueError:
                continue
        entry["rows_by_date"][d] = r
        if not entry["product_name"] and r.product_name:
            entry["product_name"] = r.product_name

    hits: list[dict] = []
    for entry in buckets.values():
        rows_by_date = entry["rows_by_date"]
        if not all(d in rows_by_date for d in required_dates):
            continue
        ordered = [rows_by_date[d] for d in required_dates]
        for col in INVENTORY_COLUMNS:
            values = [getattr(row, col) for row in ordered]
            if all(v is None for v in values):
                continue
            normalized = [0 if v is None else int(v) for v in values]
            v0 = normalized[0]
            if any(v != v0 for v in normalized):
                continue
            if v0 <= min_quantity:
                continue
            hits.append({
                "product_cd": entry["product_cd"],
                "product_name": entry["product_name"],
                "route_cd": entry["route_cd"],
                "inventory_column": col,
                "stable_quantity": v0,
                "period_start": required_dates[0].isoformat(),
                "period_end": required_dates[-1].isoformat(),
                "days": window_days,
            })

    hits.sort(key=lambda x: (
        -x["stable_quantity"],
        x["product_name"] or "",
        x["product_cd"],
        x["route_cd"],
        x["inventory_column"],
    ))

    return {
        "data": {
            "list": hits,
            "total": len(hits),
            "as_of": as_of_d.isoformat(),
            "period_start": start_d.isoformat(),
            "period_end": as_of_d.isoformat(),
            "min_quantity": int(min_quantity),
            "stable_calendar_days": window_days,
        }
    }


@router.get("/products")
async def get_production_summarys_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品一覧（product_cd + product_name の重複なし）"""
    q = (
        select(ProductionSummary.product_cd, ProductionSummary.product_name)
        .distinct()
        .where(
            ProductionSummary.product_cd.isnot(None),
            ProductionSummary.product_cd != "",
        )
        .order_by(ProductionSummary.product_name, ProductionSummary.product_cd)
    )
    result = await db.execute(q)
    rows = result.all()
    data = [
        {"product_cd": r.product_cd or "", "product_name": r.product_name or ""}
        for r in rows
    ]
    return {"data": data}


def _parse_year_month(month_str: str) -> tuple[int, int]:
    m = re.match(r"^(\d{4})-(\d{1,2})$", (month_str or "").strip())
    if not m:
        raise HTTPException(status_code=400, detail="対象月は YYYY-MM 形式で指定してください")
    y, mo = int(m.group(1)), int(m.group(2))
    if mo < 1 or mo > 12:
        raise HTTPException(status_code=400, detail="対象月の月が不正です")
    return y, mo


def _last_day_of_month(y: int, mo: int) -> date:
    if mo == 12:
        return date(y, 12, 31)
    return date(y, mo + 1, 1) - timedelta(days=1)


def _first_day_of_next_month(y: int, mo: int) -> date:
    if mo == 12:
        return date(y + 1, 1, 1)
    return date(y, mo + 1, 1)


class StocktakeCarryoverExecuteItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    product_cd: str
    total_quantity: int = 0


class StocktakeCarryoverExecuteBody(BaseModel):
    month: str
    process_cd: str
    selectedData: list[StocktakeCarryoverExecuteItem]


# 棚卸繰越→stock_transaction_logs：工程が KT09/KT13/KT15 のとき在庫種別は製品（部品・材料マスタ優先後）
_STOCKTAKE_CARRYOVER_PRODUCT_PROCESS_CDS = frozenset({"KT09", "KT13", "KT15"})


def _stock_type_for_stocktake_carryover(product_type: Optional[str], process_cd: str) -> str:
    """products.product_type に応じて材料/部品、それ以外は工程で製品/仕掛品。"""
    pt = (product_type or "").strip()
    if pt == "材料":
        return "材料"
    if pt == "部品":
        return "部品"
    pc = (process_cd or "").strip()
    if pc in _STOCKTAKE_CARRYOVER_PRODUCT_PROCESS_CDS:
        return "製品"
    return "仕掛品"


def _location_cd_for_stocktake_carryover(
    stock_type: str,
    process_cd: str,
    product_location_cd: Optional[str],
) -> str:
    pl = (product_location_cd or "").strip()
    if stock_type == "材料":
        return pl or "原材料倉庫"
    if stock_type == "部品":
        return pl or "部品倉庫"
    if stock_type == "製品":
        pc = (process_cd or "").strip()
        if pc == "KT15":
            return "外注倉庫"
        return pl or "製品倉庫"
    return "工程中間在庫"


@router.get("/stocktake-carryover-preview")
async def get_stocktake_carryover_preview(
    month: str = Query(..., description="対象月 YYYY-MM"),
    process_cd: str = Query(..., description="工程コード（KT01 等）"),
    page: int = Query(1, ge=1, description="ページ番号"),
    pageSize: int = Query(20, ge=1, le=500, description="1ページ件数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    棚卸データ繰越プレビュー。
    対象月の末日の production_summarys 行から、選択工程に対応する *_inventory を読み取る。
    合計数量（在庫列）が 0 以下の行は除外。ページネーション付き。
    total_quantity_sum は上記条件に一致する全行の合計（当該在庫列の合算）。
    """
    y, mo = _parse_year_month(month)
    pc = (process_cd or "").strip()
    inv_col_name = PROCESS_INVENTORY_MAPPING.get(pc)
    if not inv_col_name:
        raise HTTPException(
            status_code=400,
            detail=f"工程コードに対応する在庫列がありません: {process_cd}",
        )
    inv_col = getattr(ProductionSummary, inv_col_name, None)
    if inv_col is None:
        raise HTTPException(status_code=500, detail="在庫列の解決に失敗しました")

    last_d = _last_day_of_month(y, mo)
    base_conds = [
        ProductionSummary.date == last_d,
        ProductionSummary.product_cd.isnot(None),
        ProductionSummary.product_cd != "",
        func.coalesce(inv_col, 0) > 0,
    ]
    # 同一 collation で JOIN（utf8mb4 系の混在で MySQL が Illegal mix of collations となるのを回避）
    _collation = "utf8mb4_unicode_ci"
    join_product = (
        ProductionSummary.product_cd.collate(_collation)
        == Product.product_cd.collate(_collation)
    )
    try:
        count_stmt = (
            select(func.count())
            .select_from(ProductionSummary)
            .where(and_(*base_conds))
        )
        sum_stmt = (
            select(func.coalesce(func.sum(inv_col), 0))
            .select_from(ProductionSummary)
            .where(and_(*base_conds))
        )
        total = int((await db.execute(count_stmt)).scalar_one() or 0)
        raw_sum = (await db.execute(sum_stmt)).scalar_one()
        total_quantity_sum = int(raw_sum or 0)

        offset = (page - 1) * pageSize
        stmt = (
            select(
                ProductionSummary.product_cd,
                ProductionSummary.product_name,
                inv_col.label("inv_qty"),
                Product.location_cd,
            )
            .select_from(ProductionSummary)
            .outerjoin(Product, join_product)
            .where(and_(*base_conds))
            .order_by(ProductionSummary.product_cd.asc())
            .offset(offset)
            .limit(pageSize)
        )
        result = await db.execute(stmt)
        rows = result.all()
    except Exception as e:
        logger.exception("stocktake-carryover-preview error: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"棚卸繰越プレビュー取得エラー: {str(e)}",
        ) from e

    out: list[dict] = []
    for r in rows:
        pcd = (r.product_cd or "").strip()
        if not pcd:
            continue
        qty = int(r.inv_qty or 0)
        out.append(
            {
                "product_cd": pcd,
                "product_name": r.product_name or "",
                "item": "製品",
                "total_quantity": qty,
                "unit": "本",
                "location_cd": (r.location_cd or "").strip() or "-",
            }
        )
    return {
        "data": {
            "list": out,
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "total_quantity_sum": total_quantity_sum,
        },
        "as_of_date": last_d.isoformat(),
        "inventory_column": inv_col_name,
        "process_cd": pc,
    }


@router.post("/stocktake-carryover-execute")
async def execute_stocktake_carryover(
    body: StocktakeCarryoverExecuteBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    選択行を stock_transaction_logs に INSERT。
    transaction_type=初期、source_file=production_summarys、target_cd=製品CD、process_cd=画面の工程、
    quantity=合計数量。stock_type は products.product_type（材料/部品）優先、
    それ以外は工程 KT09/KT13/KT15 なら製品、それ以外は仕掛品。
    transaction_time は翌月1日 0:00（JST）。
    """
    y, mo = _parse_year_month(body.month)
    pc = (body.process_cd or "").strip()
    if not PROCESS_INVENTORY_MAPPING.get(pc):
        raise HTTPException(
            status_code=400,
            detail=f"工程コードに対応する在庫列定義がありません: {body.process_cd}",
        )
    target_d = _first_day_of_next_month(y, mo)
    try:
        transaction_time = JST.localize(datetime.combine(target_d, dt_time.min))
    except Exception:
        transaction_time = now_jst()

    product_cds = list(
        {
            (item.product_cd or "").strip()
            for item in body.selectedData
            if (item.product_cd or "").strip()
        }
    )
    prod_map: dict[str, tuple[Optional[str], Optional[str]]] = {}
    if product_cds:
        pr = await db.execute(
            select(Product.product_cd, Product.product_type, Product.location_cd).where(
                Product.product_cd.in_(product_cds)
            )
        )
        for r in pr.all():
            pkey = (r.product_cd or "").strip()
            if pkey:
                prod_map[pkey] = (r.product_type, r.location_cd)

    op_id = getattr(current_user, "user_id", None) or getattr(current_user, "id", None)
    op_name = getattr(current_user, "username", None) or getattr(current_user, "name", None)
    op_id_str = str(op_id) if op_id is not None else None

    success = 0
    skipped = 0
    for item in body.selectedData:
        pcd = (item.product_cd or "").strip()
        if not pcd:
            skipped += 1
            continue
        qty = int(item.total_quantity or 0)
        if qty <= 0:
            skipped += 1
            continue

        prod = prod_map.get(pcd)
        product_type = (prod[0] if prod else None) or ""
        product_loc = prod[1] if prod else None

        stock_type = _stock_type_for_stocktake_carryover(product_type, pc)
        location_cd = _location_cd_for_stocktake_carryover(stock_type, pc, product_loc)

        row = StockTransactionLog(
            stock_type=stock_type,
            transaction_type="初期",
            target_cd=pcd,
            location_cd=location_cd,
            process_cd=pc or None,
            quantity=Decimal(qty),
            unit="本",
            transaction_time=transaction_time,
            source_file="production_summarys",
            operator_id=op_id_str,
            operator_name=op_name,
        )
        db.add(row)
        success += 1

    await db.commit()
    return {
        "data": {"successCount": success, "skippedCount": skipped},
        "message": f"{success} 件の在庫履歴（初期）を登録しました（{skipped} 件スキップ）",
    }


@router.get("/inventory-shortage-print")
async def get_inventory_shortage_print(
    startDate: Optional[str] = Query(None, description="開始日 YYYY-MM-DD"),
    endDate: Optional[str] = Query(None, description="終了日 YYYY-MM-DD"),
    productCd: Optional[str] = Query(None, description="製品CD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    在庫不足一覧印刷用。production_summarys の倉庫在庫マイナス行を、
    products（product_type, box_type, unit_per_box, destination_cd）と
    destinations（destination_name）でジョインして返す。
    箱数 = 本数 / unit_per_box（本数＝warehouse_inventory）。
    products.product_type が「量産品」の行のみ。
    """
    if not startDate or not endDate:
        return {"data": []}
    try:
        start_d = date.fromisoformat(startDate)
        end_d = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効な日付形式（YYYY-MM-DD）")
    # 同一 collation で JOIN（utf8mb4_unicode_ci / utf8mb4_0900_ai_ci 混在エラー回避）
    _collation = "utf8mb4_unicode_ci"
    join_product = (
        ProductionSummary.product_cd.collate(_collation)
        == Product.product_cd.collate(_collation)
    )
    join_dest = (
        Product.destination_cd.collate(_collation)
        == Destination.destination_cd.collate(_collation)
    )
    try:
        q = (
            select(
                ProductionSummary.product_cd,
                ProductionSummary.product_name,
                ProductionSummary.date,
                ProductionSummary.warehouse_inventory,
                ProductionSummary.inspection_inventory,
                Product.product_type,
                Product.box_type,
                Product.unit_per_box,
                Product.destination_cd,
                Destination.destination_name,
            )
            .select_from(ProductionSummary)
            .outerjoin(Product, join_product)
            .outerjoin(Destination, join_dest)
            .where(ProductionSummary.date >= start_d)
            .where(ProductionSummary.date <= end_d)
            .where(ProductionSummary.warehouse_inventory < 0)
            .where(Product.product_type == "量産品")
            .order_by(ProductionSummary.product_name, ProductionSummary.product_cd)
        )
        if productCd:
            q = q.where(ProductionSummary.product_cd == productCd)
        result = await db.execute(q)
        rows = result.all()
        out = []
        for r in rows:
            try:
                raw_units = r.warehouse_inventory
                units = int(raw_units) if raw_units is not None else 0
                raw_upb = r.unit_per_box
                unit_per_box = int(raw_upb) if raw_upb is not None and int(raw_upb) > 0 else None
                box_quantity = (units // unit_per_box) if unit_per_box else None
            except (TypeError, ValueError):
                units = 0
                unit_per_box = None
                box_quantity = None
            d = r.date
            if d is None:
                date_str = ""
            elif hasattr(d, "isoformat"):
                date_str = d.isoformat()
            else:
                date_str = str(d)
            out.append({
                "product_cd": r.product_cd or "",
                "product_name": r.product_name or "",
                "date": date_str,
                "destination_name": r.destination_name or "",
                "product_type": r.product_type or "",
                "box_type": r.box_type or "",
                "inspection_inventory": (int(r.inspection_inventory) if r.inspection_inventory is not None else None),
                "unit_per_box": r.unit_per_box,
                "units": units,
                "box_quantity": box_quantity,
            })
        return {"data": out}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("inventory-shortage-print error: %s", e)
        raise HTTPException(status_code=500, detail=f"印刷データ取得エラー: {str(e)}")


class GenerateBody(BaseModel):
    startDate: str
    endDate: str


@router.post("/generate")
async def generate_production_summarys(
    body: GenerateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    指定期間で production_summarys を生成。既存の (date, product_cd) はスキップ。
    製品は products テーブル（status='active'）から取得。
    """
    try:
        start = date.fromisoformat(body.startDate)
        end = date.fromisoformat(body.endDate)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効な日付形式（YYYY-MM-DD）")
    if start > end:
        raise HTTPException(status_code=400, detail="開始日は終了日以前にしてください")

    # 製品一覧（products テーブル）
    # 条件: product_cd 末尾が '1'、product_name に '加工'・'·加工'・'アーチ' を含まない、
    #       status が 'inactive' でない、product_type が '量産品'
    try:
        product_query = (
            select(Product)
            .where(Product.product_cd.isnot(None))
            .where(Product.product_cd.endswith("1"))
            .where(Product.status != "inactive")
            .where(Product.product_type == "量産品")
            .where(
                or_(
                    Product.product_name.is_(None),
                    and_(
                        ~Product.product_name.like("%加工%"),
                        ~Product.product_name.like("%·加工%"),
                        ~Product.product_name.like("%アーチ%"),
                    ),
                )
            )
        )
        product_result = await db.execute(product_query)
        products = product_result.scalars().all()
    except Exception:
        products = []

    if not products:
        return {"success": True, "message": "対象製品がありません", "inserted": 0, "skipped": 0}

    # 既存 (date, product_cd) を取得
    existing_query = select(ProductionSummary.date, ProductionSummary.product_cd).where(
        and_(
            ProductionSummary.date >= start,
            ProductionSummary.date <= end,
        )
    )
    existing_result = await db.execute(existing_query)
    existing_set = {(r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date), r.product_cd) for r in existing_result.all()}

    inserted = 0
    current = start
    while current <= end:
        dow = DAY_OF_WEEK_JA[current.weekday()]
        for p in products:
            key = (current.isoformat(), p.product_cd)
            if key in existing_set:
                continue
            row = ProductionSummary(
                route_cd=p.route_cd or None,
                product_cd=p.product_cd,
                product_name=p.product_name or None,
                date=current,
                day_of_week=dow,
                order_quantity=0,
                forecast_quantity=0,
            )
            db.add(row)
            inserted += 1
            existing_set.add(key)
        current += timedelta(days=1)

    await db.commit()
    return {"success": True, "message": "データ生成が完了しました", "inserted": inserted, "skipped": 0}


class UpdateFromOrderDailyBody(BaseModel):
    updateMode: str = "changed"  # 'all' | 'changed' | 'recent'
    days: int = 30
    clearBeforeUpdate: bool = False


class ClearCalculatedFieldsBody(BaseModel):
    startDate: str  # YYYY-MM-DD


class LockAcquireBody(BaseModel):
    lockValue: str  # クライアント発行の一意値（例: UUID）
    ttlSeconds: Optional[int] = None  # 未指定時は DEFAULT_LOCK_TTL_SECONDS


class LockReleaseBody(BaseModel):
    lockValue: str


class OptionalStartDateBody(BaseModel):
    startDate: Optional[str] = None  # YYYY-MM-DD、未指定時は全件または製品別起算


def _parse_end_date(start_d: date, months: int = 3) -> date:
    """start_d から months ヶ月後の日付（月末ベースで簡易計算）"""
    year = start_d.year
    month = start_d.month + months
    while month > 12:
        month -= 12
        year += 1
    # 月末日
    if month in (1, 3, 5, 7, 8, 10, 12):
        last_day = 31
    elif month in (4, 6, 9, 11):
        last_day = 30
    else:
        last_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
    return date(year, month, min(start_d.day, last_day))


def _first_day_of_current_month_jst() -> date:
    """在庫・推移開始日のフォールバック用：サーバー基準の日本時間の当月1日。"""
    n = now_jst()
    return date(n.year, n.month, 1)


async def _resolve_inventory_trend_calc_start_date(db: AsyncSession) -> tuple[date, str]:
    """
    在庫・推移更新の開始日。
    stock_transaction_logs で transaction_type='初期' かつ quantity>0 の行のうち、
    transaction_time が最大の行の日付（日単位）。該当が無い場合は当月月初(JST)。
    """
    q = select(func.max(StockTransactionLog.transaction_time)).where(
        StockTransactionLog.transaction_type == "初期",
        StockTransactionLog.quantity > 0,
    )
    res = await db.execute(q)
    max_ts = res.scalar_one_or_none()
    if max_ts is not None:
        if isinstance(max_ts, datetime):
            return max_ts.date(), "initial_stock_log"
        if isinstance(max_ts, date):
            return max_ts, "initial_stock_log"
    return _first_day_of_current_month_jst(), "fallback_month_start"


@router.get("/inventory-trend-calc-start-date")
async def get_inventory_trend_calc_start_date(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """フロントの在庫・推移更新で使用する計算開始日（初期在庫ログ基準、無ければ当月月初JST）。"""
    start_d, source = await _resolve_inventory_trend_calc_start_date(db)
    return {
        "code": 200,
        "data": {"startDate": start_d.isoformat(), "source": source},
        "message": "OK",
    }


@router.post("/clear-calculated-fields")
async def clear_production_summarys_calculated_fields(
    body: ClearCalculatedFieldsBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    startDate 必須。date >= startDate かつ date <= startDate+3ヶ月 の行について、
    在庫・推移・actual_plan_trend 等の计算字段を 0 にクリアする。
    """
    if not (body.startDate and body.startDate.strip()):
        raise HTTPException(status_code=400, detail="startDate は必須です（YYYY-MM-DD）")
    try:
        start_d = datetime.strptime(body.startDate.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="startDate は YYYY-MM-DD 形式で指定してください")
    end_d = _parse_end_date(start_d, 3)
    set_parts = ", ".join([f"`{col}` = 0" for col in CALCULATED_FIELDS_TO_CLEAR])
    sql = text(
        f"UPDATE production_summarys SET {set_parts} WHERE date >= :start_date AND date <= :end_date"
    )
    res = await db.execute(sql, {"start_date": start_d, "end_date": end_d})
    await db.commit()
    cleared = res.rowcount if hasattr(res, "rowcount") else 0
    return {
        "code": 200,
        "data": {"cleared": cleared, "startDate": body.startDate[:10], "endDate": end_d.isoformat()},
        "message": f"計算フィールドをクリアしました（{cleared}件）",
    }


@router.post("/clear-plan-fields")
async def clear_production_summarys_plan_fields(
    body: ClearCalculatedFieldsBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    startDate 必須。date >= startDate かつ date <= startDate+5ヶ月 の行について、
    各工程の _plan / _actual_plan 列を 0 にクリアする（計画データ更新前の初期化用）。
    """
    if not (body.startDate and body.startDate.strip()):
        raise HTTPException(status_code=400, detail="startDate は必須です（YYYY-MM-DD）")
    try:
        start_d = datetime.strptime(body.startDate.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="startDate は YYYY-MM-DD 形式で指定してください")
    end_d = _parse_end_date(start_d, PLAN_PERIOD_MONTHS)
    set_parts = ", ".join([f"`{col}` = 0" for col in PLAN_AND_ACTUAL_PLAN_FIELDS_TO_CLEAR])
    sql = text(
        f"UPDATE production_summarys SET {set_parts} WHERE date >= :start_date AND date <= :end_date"
    )
    res = await db.execute(sql, {"start_date": start_d, "end_date": end_d})
    await db.commit()
    cleared = res.rowcount if hasattr(res, "rowcount") else 0
    return {
        "code": 200,
        "data": {"cleared": cleared, "startDate": body.startDate[:10], "endDate": end_d.isoformat()},
        "message": f"計画列（_plan / _actual_plan）をクリアしました（{cleared}件）",
    }


@router.post("/clear-molding-plan")
async def clear_production_summarys_molding_plan(
    body: ClearCalculatedFieldsBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    startDate 必須。date >= startDate の全行について molding_plan と molding_actual_plan を 0 にクリアする（終了日の上限なし）。
    """
    if not (body.startDate and body.startDate.strip()):
        raise HTTPException(status_code=400, detail="startDate は必須です（YYYY-MM-DD）")
    try:
        start_d = datetime.strptime(body.startDate.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="startDate は YYYY-MM-DD 形式で指定してください")
    sql = text(
        "UPDATE production_summarys SET molding_plan = 0, molding_actual_plan = 0 WHERE date >= :start_date"
    )
    res = await db.execute(sql, {"start_date": start_d})
    await db.commit()
    cleared = res.rowcount if hasattr(res, "rowcount") else 0
    return {
        "code": 200,
        "data": {"cleared": cleared, "startDate": body.startDate[:10]},
        "message": f"成型計画（molding_plan / molding_actual_plan）をクリアしました（{cleared}件）",
    }


@router.post("/batch-update-lock/acquire")
async def batch_update_lock_acquire(
    body: LockAcquireBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    一括更新用の分散ロックを取得する。
    他端末が既に保持している場合は 423 Locked を返す。
    """
    lock_key = BATCH_UPDATE_LOCK_KEY
    lock_value = (body.lockValue or "").strip()[:255]
    if not lock_value:
        raise HTTPException(status_code=400, detail="lockValue は必須です")
    ttl = body.ttlSeconds if body.ttlSeconds is not None and body.ttlSeconds > 0 else DEFAULT_LOCK_TTL_SECONDS
    now = now_jst()
    expires_at = now + timedelta(seconds=ttl)
    try:
        await db.execute(
            text(
                "INSERT INTO distributed_locks (lock_key, lock_value, expires_at) VALUES (:lock_key, :lock_value, :expires_at)"
            ),
            {"lock_key": lock_key, "lock_value": lock_value, "expires_at": expires_at},
        )
        await db.commit()
        return {"code": 200, "data": {"acquired": True}, "message": "ロックを取得しました"}
    except IntegrityError:
        await db.rollback()
        # 既存行あり → 有効期限内なら 423、期限切れなら UPDATE で取得
        upd = await db.execute(
            text(
                "UPDATE distributed_locks SET lock_value = :lock_value, expires_at = :expires_at "
                "WHERE lock_key = :lock_key AND expires_at <= :now"
            ),
            {"lock_key": lock_key, "lock_value": lock_value, "expires_at": expires_at, "now": now},
        )
        await db.commit()
        if upd.rowcount and upd.rowcount > 0:
            return {"code": 200, "data": {"acquired": True}, "message": "ロックを取得しました（期限切れを再取得）"}
        raise HTTPException(
            status_code=423,
            detail="他の端末で一括更新が実行中のため、しばらく待ってから再度お試しください。",
        )


@router.post("/batch-update-lock/release")
async def batch_update_lock_release(
    body: LockReleaseBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """取得した分散ロックを解放する（lock_value が一致する場合のみ削除）。"""
    lock_key = BATCH_UPDATE_LOCK_KEY
    lock_value = (body.lockValue or "").strip()[:255]
    if not lock_value:
        raise HTTPException(status_code=400, detail="lockValue は必須です")
    res = await db.execute(
        text("DELETE FROM distributed_locks WHERE lock_key = :lock_key AND lock_value = :lock_value"),
        {"lock_key": lock_key, "lock_value": lock_value},
    )
    await db.commit()
    return {"code": 200, "data": {"released": True}, "message": "ロックを解放しました"}


@router.post("/update-from-order-daily")
async def update_production_summarys_from_order_daily(
    body: UpdateFromOrderDailyBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    order_daily の受注データから production_summarys の
    forecast_quantity / order_quantity を更新する。
    """
    from time import perf_counter
    from datetime import datetime, timedelta as _timedelta
    from app.modules.erp.models import OrderDaily

    start_time = perf_counter()

    mode = body.updateMode or "changed"
    if mode not in {"all", "changed", "recent"}:
        raise HTTPException(status_code=400, detail="updateMode は 'all' | 'changed' | 'recent' のいずれかを指定してください")

    days = body.days or 30
    if days <= 0:
        days = 30

    # 対象期間（recent モード用）
    recent_start_date = None
    if mode == "recent":
        today = datetime.utcnow().date()
        recent_start_date = today - _timedelta(days=days - 1)

    # order_daily から集計
    od = OrderDaily
    # product_cd の末尾を '1' にそろえる
    normalized_product_cd = func.concat(func.substr(od.product_cd, 1, func.length(od.product_cd) - 1), "1")

    agg_query = (
        select(
            normalized_product_cd.label("product_cd"),
            od.date.label("date"),
            func.sum(func.coalesce(od.forecast_units, 0)).label("forecast_quantity"),
            func.sum(func.coalesce(od.confirmed_units, 0)).label("order_quantity"),
        )
        .where(od.product_cd.isnot(None), od.product_cd != "")
    )
    if mode == "recent" and recent_start_date is not None:
        agg_query = agg_query.where(od.date >= recent_start_date)

    agg_query = agg_query.group_by(normalized_product_cd, od.date)

    agg_result = await db.execute(agg_query)
    agg_rows = agg_result.all()

    total = len(agg_rows)
    if total == 0:
        elapsed = perf_counter() - start_time
        return {
            "code": 200,
            "data": {
                "updated": 0,
                "skipped": 0,
                "unchanged": 0,
                "total": 0,
                "elapsedTime": round(elapsed, 2),
            },
            "message": "更新対象となる受注データがありませんでした。",
        }

    # 更新前クリア
    if body.clearBeforeUpdate:
        clear_stmt = update(ProductionSummary).values(order_quantity=0, forecast_quantity=0)
        if mode == "recent" and recent_start_date is not None:
            clear_stmt = clear_stmt.where(ProductionSummary.date >= recent_start_date)
        await db.execute(clear_stmt)

    # 既存の production_summarys を一括取得
    key_list = [(r.product_cd, r.date) for r in agg_rows]
    existing_stmt = select(ProductionSummary).where(
        tuple_(ProductionSummary.product_cd, ProductionSummary.date).in_(key_list)
    )
    existing_result = await db.execute(existing_stmt)
    existing_rows = existing_result.scalars().all()
    existing_map = {(r.product_cd, r.date): r for r in existing_rows}

    updated = 0
    skipped = 0
    unchanged = 0

    for r in agg_rows:
        key = (r.product_cd, r.date)
        ps = existing_map.get(key)
        if not ps:
            # production_summarys 側に存在しない (product_cd, date) はスキップ
            skipped += 1
            continue

        new_forecast = int(r.forecast_quantity or 0)
        new_order = int(r.order_quantity or 0)

        if mode == "changed":
            if ps.forecast_quantity == new_forecast and ps.order_quantity == new_order:
                unchanged += 1
                continue

        ps.forecast_quantity = new_forecast
        ps.order_quantity = new_order
        updated += 1

    await db.commit()

    elapsed = perf_counter() - start_time
    message = f"{updated}件のデータを更新しました（変更なし {unchanged} 件 / スキップ {skipped} 件）"

    return {
        "code": 200,
        "data": {
            "updated": updated,
            "skipped": skipped,
            "unchanged": unchanged,
            "total": total,
            "elapsedTime": round(elapsed, 2),
        },
        "message": message,
    }


@router.post("/clear-carry-over")
async def clear_production_summarys_carry_over(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """production_summarys の全工程繰越フィールドを一括で 0 にクリア"""
    values = {col: 0 for col in CARRY_OVER_COLUMNS}
    stmt = update(ProductionSummary).values(**values)
    result = await db.execute(stmt)
    await db.commit()
    cleared = result.rowcount
    return {
        "code": 200,
        "data": {"cleared": cleared},
        "message": f"繰越フィールドをクリアしました（{cleared} 行）",
    }


@router.post("/update-carry-over")
async def update_production_summarys_carry_over(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    stock_transaction_logs の transaction_type='初期' を集計し、
    production_summarys の各工程繰越列に反映する。
    """
    allowed_process = set(PROCESS_CARRY_OVER_MAPPING.keys())
    agg_q = (
        select(
            StockTransactionLog.target_cd.label("product_cd"),
            func.date(StockTransactionLog.transaction_time).label("date"),
            StockTransactionLog.process_cd,
            func.sum(StockTransactionLog.quantity).label("quantity"),
        )
        .where(StockTransactionLog.transaction_type == "初期")
        .where(StockTransactionLog.target_cd.isnot(None))
        .where(StockTransactionLog.target_cd != "")
        .where(StockTransactionLog.transaction_time.isnot(None))
        .where(StockTransactionLog.process_cd.in_(allowed_process))
        .group_by(StockTransactionLog.target_cd, func.date(StockTransactionLog.transaction_time), StockTransactionLog.process_cd)
    )
    agg_result = await db.execute(agg_q)
    carry_over_rows = agg_result.all()

    if not carry_over_rows:
        return {
            "code": 200,
            "data": {"updated": 0, "skipped": 0, "total": 0},
            "message": "更新する繰越データがありません",
        }

    updated_count = 0
    skipped_count = 0
    for row in carry_over_rows:
        process_cd = (row.process_cd or "").strip()
        field_name = PROCESS_CARRY_OVER_MAPPING.get(process_cd)
        if not field_name or field_name not in CARRY_OVER_COLUMNS:
            skipped_count += 1
            continue
        product_cd = (row.product_cd or "").strip()
        date_val = row.date
        if not product_cd or date_val is None:
            skipped_count += 1
            continue
        date_str = date_val.isoformat() if hasattr(date_val, "isoformat") else str(date_val)
        qty = int(float(row.quantity or 0))
        try:
            stmt = (
                update(ProductionSummary)
                .where(ProductionSummary.product_cd == product_cd, ProductionSummary.date == date_str)
                .values(**{field_name: qty})
            )
            res = await db.execute(stmt)
            if res.rowcount > 0:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    await db.commit()
    message = f"{updated_count}件の繰越データを更新しました（{skipped_count}件スキップ）"
    return {
        "code": 200,
        "data": {"updated": updated_count, "skipped": skipped_count, "total": len(carry_over_rows)},
        "message": message,
    }


def _get_japan_date_string() -> str:
    """日本時区の今日 YYYY-MM-DD"""
    return now_jst().strftime("%Y-%m-%d")


def _jst_month_first_and_last_day() -> tuple[str, str]:
    """日本時区で当月1日と当月末日の YYYY-MM-DD（実績・不良・廃棄・保留のログ同期窓）。"""
    today_str = _get_japan_date_string()
    parts = today_str.split("-")
    year, month = int(parts[0]), int(parts[1])
    first_day_str = f"{year}-{month:02d}-01"
    last_dom = calendar.monthrange(year, month)[1]
    month_end_str = f"{year}-{month:02d}-{last_dom:02d}"
    return first_day_str, month_end_str


async def _clear_production_summary_columns_jst_month(
    db: AsyncSession,
    columns: list[str],
) -> tuple[int, str, str]:
    """当月1日～当月末日(JST)の行について指定列を 0 にし commit。戻り値 (cleared_rowcount, first_day, month_end)。"""
    first_day_str, month_end_str = _jst_month_first_and_last_day()
    if not columns:
        return 0, first_day_str, month_end_str
    clear_values = {col: 0 for col in columns}
    stmt_clear = (
        update(ProductionSummary)
        .where(ProductionSummary.date >= first_day_str, ProductionSummary.date <= month_end_str)
        .values(**clear_values)
    )
    result_clear = await db.execute(stmt_clear)
    cleared_count = result_clear.rowcount
    await db.commit()
    return cleared_count, first_day_str, month_end_str


@router.post("/update-actual")
async def update_production_summarys_actual(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    stock_transaction_logs の実績・不良・入出庫から production_summarys の各 actual 列を再計算して反映する。
    当月1日～当月末日（日本時区）の actual を一旦クリアしてから、ログを集計して書き戻す。
    """
    cleared_count, first_day_str, month_end_str = await _clear_production_summary_columns_jst_month(
        db, ACTUAL_CLEAR_COLUMNS
    )

    # 2) 一般工程：実績+不良 集計（product_cd = 前4桁+'1'）
    process_placeholders = ", ".join([":p%d" % i for i in range(len(GENERAL_PROCESS_CDS))])
    general_sql = text("""
        SELECT CONCAT(SUBSTRING(target_cd, 1, 4), '1') AS product_cd,
               DATE(transaction_time) AS date,
               process_cd,
               SUM(quantity) AS quantity
        FROM stock_transaction_logs
        WHERE transaction_type IN ('実績', '不良')
          AND process_cd IN ("""
        + process_placeholders
        + """)
          AND target_cd IS NOT NULL AND target_cd != '' AND LENGTH(target_cd) >= 4
        GROUP BY CONCAT(SUBSTRING(target_cd, 1, 4), '1'), DATE(transaction_time), process_cd
    """)
    try:
        params = {"p%d" % i: c for i, c in enumerate(GENERAL_PROCESS_CDS)}
        res_general = await db.execute(general_sql, params)
        actual_rows = res_general.mappings().all()
    except Exception:
        actual_rows = []

    # 3) KT13 製品倉庫：入庫−出庫
    kt13_sql = text("""
        SELECT CONCAT(SUBSTRING(target_cd, 1, 4), '1') AS product_cd,
               DATE(transaction_time) AS date,
               SUM(CASE WHEN transaction_type = '入庫' THEN quantity WHEN transaction_type = '出庫' THEN -quantity ELSE 0 END) AS quantity
        FROM stock_transaction_logs
        WHERE transaction_type IN ('入庫', '出庫') AND process_cd = 'KT13'
          AND target_cd IS NOT NULL AND target_cd != '' AND LENGTH(target_cd) >= 4
        GROUP BY CONCAT(SUBSTRING(target_cd, 1, 4), '1'), DATE(transaction_time)
    """)
    try:
        res_kt13 = await db.execute(kt13_sql)
        warehouse_rows = res_kt13.mappings().all()
    except Exception:
        warehouse_rows = []

    # 4) KT15 外注倉庫：入庫−出庫
    kt15_sql = text("""
        SELECT CONCAT(SUBSTRING(target_cd, 1, 4), '1') AS product_cd,
               DATE(transaction_time) AS date,
               SUM(CASE WHEN transaction_type = '入庫' THEN quantity WHEN transaction_type = '出庫' THEN -quantity ELSE 0 END) AS quantity
        FROM stock_transaction_logs
        WHERE transaction_type IN ('入庫', '出庫') AND process_cd = 'KT15'
          AND target_cd IS NOT NULL AND target_cd != '' AND LENGTH(target_cd) >= 4
        GROUP BY CONCAT(SUBSTRING(target_cd, 1, 4), '1'), DATE(transaction_time)
    """)
    try:
        res_kt15 = await db.execute(kt15_sql)
        outsourced_warehouse_rows = res_kt15.mappings().all()
    except Exception:
        outsourced_warehouse_rows = []

    if not actual_rows and not warehouse_rows and not outsourced_warehouse_rows:
        msg = f"{cleared_count}件のレコードをクリアしました（集計データなし）"
        return {
            "code": 200,
            "data": {"updated": 0, "skipped": 0, "cleared": cleared_count, "clearPeriod": f"{first_day_str} ～ {month_end_str}"},
            "message": msg,
        }

    updated_count = 0
    skipped_count = 0

    for row in actual_rows:
        product_cd = (row.get("product_cd") or "").strip()
        date_val = row.get("date")
        process_cd = (row.get("process_cd") or "").strip()
        qty = int(float(row.get("quantity") or 0))
        if not product_cd or date_val is None:
            skipped_count += 1
            continue
        date_str = date_val.isoformat()[:10] if hasattr(date_val, "isoformat") else str(date_val)[:10]
        field_name = PROCESS_ACTUAL_MAPPING.get(process_cd)
        if not field_name:
            skipped_count += 1
            continue
        try:
            stmt = (
                update(ProductionSummary)
                .where(ProductionSummary.product_cd == product_cd, ProductionSummary.date == date_str)
                .values(**{field_name: qty})
            )
            res = await db.execute(stmt)
            if res.rowcount > 0:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    for row in warehouse_rows:
        product_cd = (row.get("product_cd") or "").strip()
        date_val = row.get("date")
        qty = int(float(row.get("quantity") or 0))
        if not product_cd or date_val is None:
            skipped_count += 1
            continue
        date_str = date_val.isoformat()[:10] if hasattr(date_val, "isoformat") else str(date_val)[:10]
        try:
            stmt = (
                update(ProductionSummary)
                .where(ProductionSummary.product_cd == product_cd, ProductionSummary.date == date_str)
                .values(warehouse_actual=qty)
            )
            res = await db.execute(stmt)
            if res.rowcount > 0:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    for row in outsourced_warehouse_rows:
        product_cd = (row.get("product_cd") or "").strip()
        date_val = row.get("date")
        qty = int(float(row.get("quantity") or 0))
        if not product_cd or date_val is None:
            skipped_count += 1
            continue
        date_str = date_val.isoformat()[:10] if hasattr(date_val, "isoformat") else str(date_val)[:10]
        try:
            stmt = (
                update(ProductionSummary)
                .where(ProductionSummary.product_cd == product_cd, ProductionSummary.date == date_str)
                .values(outsourced_warehouse_actual=qty)
            )
            res = await db.execute(stmt)
            if res.rowcount > 0:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    await db.commit()
    message = f"{cleared_count}件のレコードをクリア後、{updated_count}件の実績データを更新しました（{skipped_count}件スキップ）"
    return {
        "code": 200,
        "data": {
            "updated": updated_count,
            "skipped": skipped_count,
            "total": len(actual_rows) + len(warehouse_rows) + len(outsourced_warehouse_rows),
            "cleared": cleared_count,
            "clearPeriod": f"{first_day_str} ～ {month_end_str}",
        },
        "message": message,
    }


@router.post("/update-defect")
async def update_production_summarys_defect(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    stock_transaction_logs の transaction_type='不良' を集計し、
    production_summarys の各工程 defect 列に反映する。
    当月1日～当月末日（日本時区）の全 defect 列を一旦 0 にクリアしてからログを書き戻す。
    """
    cleared_count, first_day_str, month_end_str = await _clear_production_summary_columns_jst_month(
        db, DEFECT_CLEAR_COLUMNS
    )

    defect_placeholders = ", ".join([":d%d" % i for i in range(len(DEFECT_PROCESS_CDS))])
    defect_sql = text("""
        SELECT CONCAT(SUBSTRING(target_cd, 1, 4), '1') AS product_cd,
               DATE(transaction_time) AS date,
               process_cd,
               SUM(quantity) AS quantity
        FROM stock_transaction_logs
        WHERE transaction_type = '不良'
          AND process_cd IN ("""
        + defect_placeholders
        + """)
          AND target_cd IS NOT NULL AND target_cd != '' AND LENGTH(target_cd) >= 4
          AND transaction_time IS NOT NULL
        GROUP BY CONCAT(SUBSTRING(target_cd, 1, 4), '1'), DATE(transaction_time), process_cd
    """)
    try:
        params = {"d%d" % i: c for i, c in enumerate(DEFECT_PROCESS_CDS)}
        res_defect = await db.execute(defect_sql, params)
        defect_rows = res_defect.mappings().all()
    except Exception:
        defect_rows = []

    if not defect_rows:
        msg = f"{cleared_count}件のレコードの不良列をクリアしました（集計データなし）"
        return {
            "code": 200,
            "data": {
                "updated": 0,
                "skipped": 0,
                "total": 0,
                "cleared": cleared_count,
                "clearPeriod": f"{first_day_str} ～ {month_end_str}",
            },
            "message": msg,
        }

    updated_count = 0
    skipped_count = 0
    for row in defect_rows:
        product_cd = (row.get("product_cd") or "").strip()
        date_val = row.get("date")
        process_cd = (row.get("process_cd") or "").strip()
        qty = int(float(row.get("quantity") or 0))
        if not product_cd or date_val is None:
            skipped_count += 1
            continue
        date_str = date_val.isoformat()[:10] if hasattr(date_val, "isoformat") else str(date_val)[:10]
        field_name = PROCESS_DEFECT_MAPPING.get(process_cd)
        if not field_name:
            skipped_count += 1
            continue
        try:
            stmt = (
                update(ProductionSummary)
                .where(ProductionSummary.product_cd == product_cd, ProductionSummary.date == date_str)
                .values(**{field_name: qty})
            )
            res = await db.execute(stmt)
            if res.rowcount > 0:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    await db.commit()
    message = (
        f"{cleared_count}件のレコードをクリア後、{updated_count}件の不良データを更新しました"
        f"（{skipped_count}件スキップ）"
    )
    return {
        "code": 200,
        "data": {
            "updated": updated_count,
            "skipped": skipped_count,
            "total": len(defect_rows),
            "cleared": cleared_count,
            "clearPeriod": f"{first_day_str} ～ {month_end_str}",
        },
        "message": message,
    }


@router.post("/update-scrap")
async def update_production_summarys_scrap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    stock_transaction_logs の transaction_type='廃棄' を集計し、
    production_summarys の各工程 scrap 列に反映する。
    当月1日～当月末日（日本時区）の全 scrap 列を一旦 0 にクリアしてからログを書き戻す。
    """
    cleared_count, first_day_str, month_end_str = await _clear_production_summary_columns_jst_month(
        db, SCRAP_CLEAR_COLUMNS
    )

    scrap_placeholders = ", ".join([":s%d" % i for i in range(len(SCRAP_PROCESS_CDS))])
    scrap_sql = text("""
        SELECT CONCAT(SUBSTRING(target_cd, 1, 4), '1') AS product_cd,
               DATE(transaction_time) AS date,
               process_cd,
               SUM(quantity) AS quantity
        FROM stock_transaction_logs
        WHERE transaction_type = '廃棄'
          AND process_cd IN ("""
        + scrap_placeholders
        + """)
          AND target_cd IS NOT NULL AND target_cd != '' AND LENGTH(target_cd) >= 4
          AND transaction_time IS NOT NULL
        GROUP BY CONCAT(SUBSTRING(target_cd, 1, 4), '1'), DATE(transaction_time), process_cd
    """)
    try:
        params = {"s%d" % i: c for i, c in enumerate(SCRAP_PROCESS_CDS)}
        res_scrap = await db.execute(scrap_sql, params)
        scrap_rows = res_scrap.mappings().all()
    except Exception:
        scrap_rows = []

    if not scrap_rows:
        msg = f"{cleared_count}件のレコードの廃棄列をクリアしました（集計データなし）"
        return {
            "code": 200,
            "data": {
                "updated": 0,
                "skipped": 0,
                "total": 0,
                "cleared": cleared_count,
                "clearPeriod": f"{first_day_str} ～ {month_end_str}",
            },
            "message": msg,
        }

    updated_count = 0
    skipped_count = 0
    for row in scrap_rows:
        product_cd = (row.get("product_cd") or "").strip()
        date_val = row.get("date")
        process_cd = (row.get("process_cd") or "").strip()
        qty = int(float(row.get("quantity") or 0))
        if not product_cd or date_val is None:
            skipped_count += 1
            continue
        date_str = date_val.isoformat()[:10] if hasattr(date_val, "isoformat") else str(date_val)[:10]
        field_name = PROCESS_SCRAP_MAPPING.get(process_cd)
        if not field_name:
            skipped_count += 1
            continue
        try:
            stmt = (
                update(ProductionSummary)
                .where(ProductionSummary.product_cd == product_cd, ProductionSummary.date == date_str)
                .values(**{field_name: qty})
            )
            res = await db.execute(stmt)
            if res.rowcount > 0:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    await db.commit()
    message = (
        f"{cleared_count}件のレコードをクリア後、{updated_count}件の廃棄データを更新しました"
        f"（{skipped_count}件スキップ）"
    )
    return {
        "code": 200,
        "data": {
            "updated": updated_count,
            "skipped": skipped_count,
            "total": len(scrap_rows),
            "cleared": cleared_count,
            "clearPeriod": f"{first_day_str} ～ {month_end_str}",
        },
        "message": message,
    }


@router.post("/update-on-hold")
async def update_production_summarys_on_hold(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    stock_transaction_logs の transaction_type='保留' を集計し、
    production_summarys の各工程 on_hold 列に反映する。
    当月1日～当月末日（日本時区）の全 on_hold 列を一旦 0 にクリアしてから、
    ログを集計して書き戻す（実績更新と同様。ログが無いセルは 0 のまま）。
    """
    cleared_count, first_day_str, month_end_str = await _clear_production_summary_columns_jst_month(
        db, ON_HOLD_CLEAR_COLUMNS
    )

    on_hold_placeholders = ", ".join([":h%d" % i for i in range(len(ON_HOLD_PROCESS_CDS))])
    on_hold_sql = text("""
        SELECT CONCAT(SUBSTRING(target_cd, 1, 4), '1') AS product_cd,
               DATE(transaction_time) AS date,
               process_cd,
               SUM(quantity) AS quantity
        FROM stock_transaction_logs
        WHERE transaction_type = '保留'
          AND process_cd IN ("""
        + on_hold_placeholders
        + """)
          AND target_cd IS NOT NULL AND target_cd != '' AND LENGTH(target_cd) >= 4
          AND transaction_time IS NOT NULL
        GROUP BY CONCAT(SUBSTRING(target_cd, 1, 4), '1'), DATE(transaction_time), process_cd
    """)
    try:
        params = {"h%d" % i: c for i, c in enumerate(ON_HOLD_PROCESS_CDS)}
        res_on_hold = await db.execute(on_hold_sql, params)
        on_hold_rows = res_on_hold.mappings().all()
    except Exception:
        on_hold_rows = []

    if not on_hold_rows:
        msg = f"{cleared_count}件のレコードの保留列をクリアしました（集計データなし）"
        return {
            "code": 200,
            "data": {
                "updated": 0,
                "skipped": 0,
                "total": 0,
                "cleared": cleared_count,
                "clearPeriod": f"{first_day_str} ～ {month_end_str}",
            },
            "message": msg,
        }

    updated_count = 0
    skipped_count = 0
    for row in on_hold_rows:
        product_cd = (row.get("product_cd") or "").strip()
        date_val = row.get("date")
        process_cd = (row.get("process_cd") or "").strip()
        qty = int(float(row.get("quantity") or 0))
        if not product_cd or date_val is None:
            skipped_count += 1
            continue
        date_str = date_val.isoformat()[:10] if hasattr(date_val, "isoformat") else str(date_val)[:10]
        field_name = PROCESS_ON_HOLD_MAPPING.get(process_cd)
        if not field_name:
            skipped_count += 1
            continue
        try:
            stmt = (
                update(ProductionSummary)
                .where(ProductionSummary.product_cd == product_cd, ProductionSummary.date == date_str)
                .values(**{field_name: qty})
            )
            res = await db.execute(stmt)
            if res.rowcount > 0:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    await db.commit()
    message = (
        f"{cleared_count}件のレコードをクリア後、{updated_count}件の保留データを更新しました"
        f"（{skipped_count}件スキップ）"
    )
    return {
        "code": 200,
        "data": {
            "updated": updated_count,
            "skipped": skipped_count,
            "total": len(on_hold_rows),
            "cleared": cleared_count,
            "clearPeriod": f"{first_day_str} ～ {month_end_str}",
        },
        "message": message,
    }


def _subtract_business_days(date_str: str, days: int) -> str:
    """从 date_str (YYYY-MM-DD) 起向前推 days 个営業日（仅排除周六、周日），返回 YYYY-MM-DD"""
    if not date_str or days <= 0:
        return date_str
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return date_str
    remaining = int(days)
    current = d
    while remaining > 0:
        current -= timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current.strftime("%Y-%m-%d")


@router.post("/update-production-dates")
async def update_production_summarys_production_dates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    按 product_process_bom の各工程リードタイム（営業日）と production_summarys.date から、
    各工程の生産計画日（*_production_date）を逆算して更新する。
    """
    # BOM 一覧取得（product_cd をキーに）
    bom_q = select(ProductProcessBOM)
    bom_result = await db.execute(bom_q)
    bom_rows = bom_result.scalars().all()
    bom_by_cd = {str(r.product_cd): r for r in bom_rows}

    # production_summarys 一覧（id, product_cd, date）
    ps_q = select(ProductionSummary.id, ProductionSummary.product_cd, ProductionSummary.date)
    ps_result = await db.execute(ps_q)
    ps_rows = ps_result.all()

    if not ps_rows:
        return {
            "code": 200,
            "data": {"updated": 0, "skipped": 0, "total": 0},
            "message": "更新する生産計画日データがありません",
        }

    updated_count = 0
    skipped_count = 0
    total_joined = 0
    for row in ps_rows:
        ps_id, product_cd, date_val = row[0], row[1], row[2]
        product_cd = (product_cd or "").strip()
        if not product_cd:
            continue
        bom = bom_by_cd.get(product_cd)
        if not bom:
            continue
        total_joined += 1
        if date_val is None:
            skipped_count += 1
            continue
        date_str = date_val.isoformat()[:10] if hasattr(date_val, "isoformat") else str(date_val)[:10]
        updates = {}
        for field_name, lt_attr in PRODUCTION_DATE_LT_MAPPING:
            lt_val = getattr(bom, lt_attr, None)
            if lt_val is None:
                continue
            try:
                lt = int(lt_val)
            except (TypeError, ValueError):
                continue
            if lt < 0:
                continue
            calc_date_str = _subtract_business_days(date_str, lt)
            try:
                updates[field_name] = datetime.strptime(calc_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
        if not updates:
            skipped_count += 1
            continue
        try:
            stmt = (
                update(ProductionSummary)
                .where(ProductionSummary.id == ps_id)
                .values(**updates)
            )
            res = await db.execute(stmt)
            if res.rowcount > 0:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    await db.commit()
    total = total_joined
    if total == 0:
        return {
            "code": 200,
            "data": {"updated": 0, "skipped": 0, "total": 0},
            "message": "更新する生産計画日データがありません",
        }
    message = f"{updated_count}件の生産計画日データを更新しました（{skipped_count}件スキップ）"
    return {
        "code": 200,
        "data": {"updated": updated_count, "skipped": skipped_count, "total": total},
        "message": message,
    }


@router.post("/update-plan")
async def update_production_summarys_plan(
    body: OptionalStartDateBody = Body(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    schedule_details.planned_qty を、production_schedules（product_cd）× 設備 machines.machine_type
    が processes と一致する工程名（成型/溶接/メッキ/切断/面取/検査）に振り分け、
    production_summarys と同日・同製品で INNER JOIN した行のみ日別集計する。
    続けて各工程 plan 列へ反映し、actual/plan から actual_plan を更新する。
    startDate を指定した場合はその日～+5ヶ月のみ対象（本月月初起き先清空 plan 再更新用）。
    """
    start_time = time.perf_counter()
    start_d = None
    end_d = None
    if body and body.startDate and body.startDate.strip():
        try:
            start_d = datetime.strptime(body.startDate.strip()[:10], "%Y-%m-%d").date()
            end_d = _parse_end_date(start_d, PLAN_PERIOD_MONTHS)
        except ValueError:
            pass
    # 1) 集計: schedule_details × sch × machines × processes → 6 工程名でグルーピング
    agg_sql_sd = text("""
        SELECT sch.product_cd AS product_cd, sd.schedule_date AS dt, pr.process_name AS process_name,
               SUM(sd.planned_qty) AS quantity
        FROM schedule_details sd
        INNER JOIN production_schedules sch ON sch.id = sd.schedule_id
        INNER JOIN machines m ON m.id = sch.line_id
        INNER JOIN processes pr ON m.machine_type IS NOT NULL
          AND (TRIM(m.machine_type) = pr.process_name OR TRIM(m.machine_type) = pr.process_cd)
        INNER JOIN production_summarys ps ON sch.product_cd = ps.product_cd AND sd.schedule_date = ps.date
        WHERE sch.product_cd IS NOT NULL AND TRIM(COALESCE(sch.product_cd, '')) <> ''
          AND pr.process_name IN ('成型','溶接','メッキ','切断','面取','検査')
          AND (:start_date IS NULL OR (sd.schedule_date >= :start_date AND sd.schedule_date <= :end_date))
        GROUP BY sch.product_cd, sd.schedule_date, pr.process_name
    """)
    params = {"start_date": start_d, "end_date": end_d}
    result_sd = await db.execute(agg_sql_sd, params)
    plan_rows = result_sd.fetchall()
    if not plan_rows:
        return {
            "code": 200,
            "data": {"updated": 0, "skipped": 0, "total": 0, "elapsedTime": round(time.perf_counter() - start_time, 2)},
            "message": "更新する計画データがありません",
        }

    # 按 process_name 归入各 plan 列
    by_field = {col: [] for col in PLAN_PROCESS_MAPPING.values()}
    for row in plan_rows:
        product_cd = (row[0] or "").strip() if row[0] is not None else ""
        dt = row[1]
        process_name = (row[2] or "").strip() if row[2] is not None else ""
        quantity = row[3]
        if not product_cd or dt is None or process_name not in PLAN_PROCESS_MAPPING:
            continue
        try:
            qty = int(float(quantity)) if quantity is not None else 0
        except (TypeError, ValueError):
            qty = 0
        field = PLAN_PROCESS_MAPPING[process_name]
        by_field[field].append((product_cd, dt, qty))

    total_plan_rows = sum(len(v) for v in by_field.values())
    updated_count = 0
    skipped_count = 0
    BATCH = 500

    for field_name, rows in by_field.items():
        for i in range(0, len(rows), BATCH):
            batch = rows[i : i + BATCH]
            case_parts = " ".join(["WHEN product_cd = :pc{:d} AND date = :dt{:d} THEN :q{:d}".format(j, j, j) for j in range(len(batch))])
            in_parts = ", ".join(["(:pc{:d}, :dt{:d})".format(j, j) for j in range(len(batch))])
            sql_str = "UPDATE production_summarys SET {} = CASE {} ELSE {} END WHERE (product_cd, date) IN ({})".format(
                field_name, case_parts, field_name, in_parts
            )
            params = {}
            for j, (pc, d, q) in enumerate(batch):
                params["pc{:d}".format(j)] = pc
                params["dt{:d}".format(j)] = d
                params["q{:d}".format(j)] = q
            try:
                res = await db.execute(text(sql_str), params)
                updated_count += res.rowcount
            except Exception:
                for (pc, d, q) in batch:
                    try:
                        stmt = (
                            update(ProductionSummary)
                            .where(ProductionSummary.product_cd == pc, ProductionSummary.date == d)
                            .values(**{field_name: q})
                        )
                        res = await db.execute(stmt)
                        if res.rowcount > 0:
                            updated_count += 1
                        else:
                            skipped_count += 1
                    except Exception:
                        skipped_count += 1

    # 2) actual_plan: 先用 actual 填，再用 plan 补空/零（startDate 指定時は対象範囲のみ）
    date_filter = " AND date >= :range_start AND date <= :range_end" if (start_d is not None and end_d is not None) else ""
    range_params = {"range_start": start_d, "range_end": end_d} if (start_d is not None and end_d is not None) else {}
    for actual_col, plan_col, target_col in ACTUAL_PLAN_COLUMNS:
        await db.execute(
            text(f"UPDATE production_summarys SET {target_col} = {actual_col} WHERE {actual_col} IS NOT NULL" + date_filter),
            range_params if range_params else {}
        )
        await db.execute(
            text(f"UPDATE production_summarys SET {target_col} = {plan_col} WHERE ({target_col} IS NULL OR {target_col} = 0) AND {plan_col} IS NOT NULL" + date_filter),
            range_params if range_params else {}
        )

    # 3) molding_actual_plan 更新後、sw_plan / chamfering_plan / cutting_plan を molding_actual_plan で上書き
    #    更新前に該当範囲でこれら3列をいったんクリアし、該当工程を持つ製品の行のみ更新する。
    await db.execute(
        text("UPDATE production_summarys SET sw_plan = 0, chamfering_plan = 0, cutting_plan = 0" + date_filter),
        range_params if range_params else {}
    )
    # 切断工程を持つルートの行のみ cutting_plan を molding_actual_plan で更新
    await db.execute(
        text("""
            UPDATE production_summarys ps
            INNER JOIN process_route_steps prs ON prs.route_cd = ps.route_cd AND prs.process_cd = 'KT01'
            SET ps.cutting_plan = ps.molding_actual_plan
            WHERE 1=1""" + date_filter.replace("date", "ps.date").replace(":range_start", ":range_start").replace(":range_end", ":range_end")),
        range_params if range_params else {}
    )
    # 面取工程を持つルートの行のみ chamfering_plan を molding_actual_plan で更新
    await db.execute(
        text("""
            UPDATE production_summarys ps
            INNER JOIN process_route_steps prs ON prs.route_cd = ps.route_cd AND prs.process_cd = 'KT02'
            SET ps.chamfering_plan = ps.molding_actual_plan
            WHERE 1=1""" + date_filter.replace("date", "ps.date").replace(":range_start", ":range_start").replace(":range_end", ":range_end")),
        range_params if range_params else {}
    )
    # sw_machine が設定されている製品の行のみ sw_plan を molding_actual_plan で更新
    await db.execute(
        text("""
            UPDATE production_summarys ps
            INNER JOIN product_machine_config pmc ON pmc.product_cd = ps.product_cd
              AND pmc.sw_machine IS NOT NULL AND TRIM(COALESCE(pmc.sw_machine, '')) <> ''
            SET ps.sw_plan = ps.molding_actual_plan
            WHERE 1=1""" + date_filter.replace("date", "ps.date").replace(":range_start", ":range_start").replace(":range_end", ":range_end")),
        range_params if range_params else {}
    )

    await db.commit()
    elapsed = round(time.perf_counter() - start_time, 2)
    message = f"{updated_count}件の計画データを更新しました（{skipped_count}件スキップ）"
    return {
        "code": 200,
        "data": {"updated": updated_count, "skipped": skipped_count, "total": total_plan_rows, "elapsedTime": elapsed},
        "message": message,
    }


DEFAULT_ROUTE_PREFIXES = [
    "cutting", "chamfering", "molding", "plating", "welding", "inspection",
    "warehouse",
]

# 在庫・推移用工程設定（key / keywords: description 解析用 / fields）
INVENTORY_PROCESS_CONFIG = [
    {"key": "cutting", "keywords": ["切断"], "fields": {"carry": "cutting_carry_over", "actual": "cutting_actual", "defect": "cutting_defect", "scrap": "cutting_scrap", "onHold": "cutting_on_hold", "inventory": "cutting_inventory", "trend": "cutting_trend"}},
    {"key": "chamfering", "keywords": ["面取"], "fields": {"carry": "chamfering_carry_over", "actual": "chamfering_actual", "defect": "chamfering_defect", "scrap": "chamfering_scrap", "onHold": "chamfering_on_hold", "inventory": "chamfering_inventory", "trend": "chamfering_trend"}},
    {"key": "molding", "keywords": ["成型"], "fields": {"carry": "molding_carry_over", "actual": "molding_actual", "defect": "molding_defect", "scrap": "molding_scrap", "onHold": "molding_on_hold", "inventory": "molding_inventory", "trend": "molding_trend"}},
    {"key": "plating", "keywords": ["メッキ"], "fields": {"carry": "plating_carry_over", "actual": "plating_actual", "defect": "plating_defect", "scrap": "plating_scrap", "onHold": "plating_on_hold", "inventory": "plating_inventory", "trend": "plating_trend"}},
    {"key": "welding", "keywords": ["溶接"], "fields": {"carry": "welding_carry_over", "actual": "welding_actual", "defect": "welding_defect", "scrap": "welding_scrap", "onHold": "welding_on_hold", "inventory": "welding_inventory", "trend": "welding_trend"}},
    {"key": "inspection", "keywords": ["検査"], "fields": {"carry": "inspection_carry_over", "actual": "inspection_actual", "defect": "inspection_defect", "scrap": "inspection_scrap", "onHold": "inspection_on_hold", "inventory": "inspection_inventory", "trend": "inspection_trend"}},
    {"key": "warehouse", "keywords": ["倉庫"], "fields": {"carry": "warehouse_carry_over", "actual": "warehouse_actual", "scrap": "warehouse_scrap", "onHold": "warehouse_on_hold", "inventory": "warehouse_inventory", "trend": "warehouse_trend"}},
    {"key": "outsourced_warehouse", "keywords": ["外注倉庫", "外注倉"], "fields": {"carry": "outsourced_warehouse_carry_over", "actual": "outsourced_warehouse_actual", "scrap": "outsourced_warehouse_scrap", "onHold": "outsourced_warehouse_on_hold", "inventory": "outsourced_warehouse_inventory", "trend": "outsourced_warehouse_trend"}},
    {"key": "outsourced_plating", "keywords": ["外注メッキ"], "fields": {"carry": "outsourced_plating_carry_over", "actual": "outsourced_plating_actual", "defect": "outsourced_plating_defect", "scrap": "outsourced_plating_scrap", "onHold": "outsourced_plating_on_hold", "inventory": "outsourced_plating_inventory", "trend": "outsourced_plating_trend"}},
    {"key": "outsourced_welding", "keywords": ["外注溶接"], "fields": {"carry": "outsourced_welding_carry_over", "actual": "outsourced_welding_actual", "defect": "outsourced_welding_defect", "scrap": "outsourced_welding_scrap", "onHold": "outsourced_welding_on_hold", "inventory": "outsourced_welding_inventory", "trend": "outsourced_welding_trend"}},
    {"key": "pre_welding_inspection", "keywords": ["溶接前検査"], "fields": {"carry": "pre_welding_inspection_carry_over", "actual": "pre_welding_inspection_actual", "defect": "pre_welding_inspection_defect", "scrap": "pre_welding_inspection_scrap", "onHold": "pre_welding_inspection_on_hold", "inventory": "pre_welding_inspection_inventory", "trend": "pre_welding_inspection_trend"}},
    {"key": "pre_inspection", "keywords": ["外注支給前"], "fields": {"carry": "pre_inspection_carry_over", "actual": "pre_inspection_actual", "scrap": "pre_inspection_scrap", "inventory": "pre_inspection_inventory", "trend": "pre_inspection_trend"}},
    {"key": "pre_outsourcing", "keywords": ["外注検査前"], "fields": {"carry": "pre_outsourcing_carry_over", "actual": "pre_outsourcing_actual", "scrap": "pre_outsourcing_scrap", "inventory": "pre_outsourcing_inventory", "trend": "pre_outsourcing_trend"}},
]


def _get_process_config_by_key(key: str) -> Optional[dict]:
    """INVENTORY_PROCESS_CONFIG から key で設定を取得"""
    for c in INVENTORY_PROCESS_CONFIG:
        if c["key"] == key:
            return c
    return None


def _find_plating_step_index(sequence: list) -> Optional[int]:
    """工程順序内で社内メッキ(plating)または外注メッキ(outsourced_plating)の位置（0-based）。無ければ None。"""
    if not sequence:
        return None
    for k in ("plating", "outsourced_plating"):
        try:
            return sequence.index(k)
        except ValueError:
            continue
    return None


def _find_inhouse_plating_step_index(sequence: list) -> Optional[int]:
    """社内メッキ(plating / 工程 KT05) の位置のみ。外注メッキ(outsourced_plating)は対象外。"""
    if not sequence:
        return None
    try:
        return sequence.index("plating")
    except ValueError:
        return None


def _find_molding_step_index(sequence: list) -> Optional[int]:
    """工程順序内で成型(molding)の位置（0-based）。無ければ None。"""
    if not sequence:
        return None
    try:
        return sequence.index("molding")
    except ValueError:
        return None


def _pre_plating_inventory_from_row(row_dict: dict, sequence: list) -> tuple[Optional[int], Optional[str]]:
    """メッキ（または外注メッキ）直前工程の当日在庫。戻り: (値, 直前工程 key)。該当なしは (None, None)。"""
    idx = _find_plating_step_index(sequence)
    if idx is None or idx <= 0:
        return None, None
    prev_key = sequence[idx - 1]
    cfg = _get_process_config_by_key(prev_key)
    if not cfg:
        return None, None
    inv_f = cfg.get("fields", {}).get("inventory")
    if not inv_f:
        return None, None
    raw = row_dict.get(inv_f)
    if raw is None:
        return 0, prev_key
    try:
        return int(raw), prev_key
    except (TypeError, ValueError):
        return 0, prev_key


def _pre_kt05_plating_inventory_from_row(row_dict: dict, sequence: list) -> tuple[Optional[int], Optional[str]]:
    """社内メッキ(KT05 / plating) 直前工程の当日在庫。外注メッキはルートに含まれていてもここでは使わない。戻り: (値, 直前工程 key)。"""
    idx = _find_inhouse_plating_step_index(sequence)
    if idx is None or idx <= 0:
        return None, None
    prev_key = sequence[idx - 1]
    cfg = _get_process_config_by_key(prev_key)
    if not cfg:
        return None, None
    inv_f = cfg.get("fields", {}).get("inventory")
    if not inv_f:
        return None, None
    raw = row_dict.get(inv_f)
    if raw is None:
        return 0, prev_key
    try:
        return int(raw), prev_key
    except (TypeError, ValueError):
        return 0, prev_key


def _pre_molding_inventory_from_row(row_dict: dict, sequence: list) -> tuple[Optional[int], Optional[str]]:
    """成型直前工程の当日在庫。戻り: (値, 直前工程 key)。該当なしは (None, None)。"""
    idx = _find_molding_step_index(sequence)
    if idx is None or idx <= 0:
        return None, None
    prev_key = sequence[idx - 1]
    cfg = _get_process_config_by_key(prev_key)
    if not cfg:
        return None, None
    inv_f = cfg.get("fields", {}).get("inventory")
    if not inv_f:
        return None, None
    raw = row_dict.get(inv_f)
    if raw is None:
        return 0, prev_key
    try:
        return int(raw), prev_key
    except (TypeError, ValueError):
        return 0, prev_key


async def _enrich_production_summary_rows_pre_plating_inventory(
    db: AsyncSession, rows: list[dict]
) -> None:
    """一覧各行に pre_plating / pre_molding 系を付与（ルート順は _get_route_sequence と同一）。"""
    if not rows:
        return
    route_cds = {(r.get("route_cd") or "").strip() for r in rows if (r.get("route_cd") or "").strip()}
    desc_map: dict[str, str] = {}
    if route_cds:
        pr_res = await db.execute(
            select(ProcessRoute.route_cd, ProcessRoute.description).where(
                ProcessRoute.route_cd.in_(route_cds)
            )
        )
        for rc, desc in pr_res.all():
            desc_map[str(rc or "").strip()] = (desc or "").strip()
    seq_cache: dict[tuple, list] = {}

    async def _seq_for(route_cd: Optional[str], route_description: str) -> list:
        cache_key = ((route_cd or "").strip(), (route_description or "").strip())
        if cache_key not in seq_cache:
            seq_cache[cache_key] = await _get_route_sequence(
                db, (route_cd or "").strip(), route_description or None
            )
        return seq_cache[cache_key]

    for r in rows:
        rc = (r.get("route_cd") or "").strip() or None
        rd = desc_map.get(rc, "") if rc else ""
        sequence = await _seq_for(rc, rd)
        val, prev = _pre_plating_inventory_from_row(r, sequence)
        r["pre_plating_inventory"] = val
        r["pre_plating_prev_process"] = prev
        v_kt05, p_kt05 = _pre_kt05_plating_inventory_from_row(r, sequence)
        r["pre_kt05_plating_inventory"] = v_kt05
        r["pre_kt05_plating_prev_process"] = p_kt05
        mv, mprev = _pre_molding_inventory_from_row(r, sequence)
        r["pre_molding_inventory"] = mv
        r["pre_molding_prev_process"] = mprev


def _parse_route_sequence_from_description(description: Optional[str]) -> list:
    """routes.description を ⇒ / → / -> / => / , / ｜ / | 等で分割し、keywords でマッチして工程 key のリストを返す。
    最後工程が正しく判定されるよう、長いキーワードを優先マッチ（例: 「外注倉庫」を「倉庫」より先にマッチ）する。"""
    if not description or not (description := description.strip()):
        return []
    # 分隔符: ⇒ → , 、 空白, 以及 -> => ｜ |
    parts = re.split(r"[⇒→,、\s]+|->|=>|｜|\|", description)
    result = []
    for part in parts:
        part = (part or "").strip()
        if not part:
            continue
        best_key = None
        best_kw_len = 0
        for config in INVENTORY_PROCESS_CONFIG:
            for kw in config.get("keywords", []):
                if kw in part and len(kw) > best_kw_len:
                    best_kw_len = len(kw)
                    best_key = config["key"]
        if best_key is not None:
            result.append(best_key)
    return result


async def _get_route_sequence(db: AsyncSession, route_cd: str, route_description: Optional[str] = None) -> list:
    """工程順序を取得。route_description があれば parse_route_sequence で解析、なければ process_route_steps から取得"""
    if route_description and (route_description := (route_description or "").strip()):
        seq = _parse_route_sequence_from_description(route_description)
        if seq:
            return seq
    if not (route_cd or "").strip():
        return list(DEFAULT_ROUTE_PREFIXES)
    q = (
        select(ProcessRouteStep.process_cd)
        .where(ProcessRouteStep.route_cd == route_cd)
        .order_by(ProcessRouteStep.step_no)
    )
    res = await db.execute(q)
    process_cds = [row[0] for row in res.fetchall() if row[0]]
    return [PROCESS_CD_TO_PREFIX[pc] for pc in process_cds if pc in PROCESS_CD_TO_PREFIX]


def _num(row: dict, key: str) -> int:
    if key not in row or row[key] is None:
        return 0
    try:
        return int(row[key])
    except (TypeError, ValueError):
        return 0


def _compute_inventory_updates(
    row: dict, sequence: list, previous_inventories: dict, is_start_date: bool
) -> dict:
    """一般工程在庫 = 繰越 + 実績 - 不良 - 廃棄 - 保留 - 下一工程実績 + 前日当工程在庫（負数許容）。外注倉庫は別計算のためスキップ。"""
    updates = {}
    for i, key in enumerate(sequence):
        config = _get_process_config_by_key(key)
        if not config or config["key"] == "outsourced_warehouse":
            continue
        fields = config.get("fields", {})
        inv_field = fields.get("inventory")
        if not inv_field:
            continue
        carry = _num(row, fields.get("carry", ""))
        actual = _num(row, fields.get("actual", ""))
        defect = _num(row, fields.get("defect", "")) if fields.get("defect") else 0
        scrap = _num(row, fields.get("scrap", "")) if fields.get("scrap") else 0
        on_hold = _num(row, fields.get("onHold", "")) if fields.get("onHold") else 0
        next_actual = 0
        for j in range(i + 1, len(sequence)):
            next_config = _get_process_config_by_key(sequence[j])
            if next_config:
                if next_config["key"] == "outsourced_warehouse":
                    next_actual = _num(row, "outsourced_warehouse_actual")
                    break
                if next_config.get("fields", {}).get("actual"):
                    next_actual = _num(row, next_config["fields"]["actual"])
                    break
        prev_inv = 0 if is_start_date else previous_inventories.get(key, 0)
        inv = carry + actual - defect - scrap - on_hold - next_actual + prev_inv
        updates[inv_field] = inv
    return updates


def _compute_warehouse_inventory(row: dict, quantity_to_subtract: int, previous_warehouse: int) -> int:
    """倉庫在庫 = warehouse_carry_over + warehouse_actual - warehouse_scrap - warehouse_on_hold - quantityToSubtract + previousInventory（負数許容）"""
    carry = _num(row, "warehouse_carry_over")
    actual = _num(row, "warehouse_actual")
    scrap = _num(row, "warehouse_scrap")
    on_hold = _num(row, "warehouse_on_hold")
    return carry + actual - scrap - on_hold - quantity_to_subtract + previous_warehouse


def _compute_outsourced_warehouse_inventory(
    row: dict, quantity_to_subtract: int, previous_outsourced: int
) -> int:
    """外注倉庫在庫 = outsourced_warehouse_carry_over + outsourced_warehouse_actual - scrap - quantityToSubtract + previousInventory（負数許容）"""
    carry = _num(row, "outsourced_warehouse_carry_over")
    actual = _num(row, "outsourced_warehouse_actual")
    scrap = _num(row, "outsourced_warehouse_scrap")
    return carry + actual - scrap - quantity_to_subtract + previous_outsourced


def _compute_trend_updates(row: dict, sequence: list) -> dict:
    """当日 trend = carry + sub_carry + actual - defect - scrap - on_hold - forecast - sub_defect - sub_scrap - sub_on_hold"""
    updates = {}
    forecast = _num(row, "forecast_quantity")
    for i, key in enumerate(sequence):
        config = _get_process_config_by_key(key)
        if not config:
            continue
        fields = config.get("fields", {})
        trend_field = fields.get("trend")
        if not trend_field:
            continue
        carry = _num(row, fields.get("carry", ""))
        actual = _num(row, fields.get("actual", ""))
        defect = _num(row, fields.get("defect", "")) if fields.get("defect") else 0
        scrap = _num(row, fields.get("scrap", "")) if fields.get("scrap") else 0
        on_hold = _num(row, fields.get("onHold", "")) if fields.get("onHold") else 0
        sub_carry = sub_defect = sub_scrap = sub_on_hold = 0
        for j in range(i + 1, len(sequence)):
            nc = _get_process_config_by_key(sequence[j])
            if nc and nc.get("fields"):
                f = nc["fields"]
                if f.get("carry"):
                    sub_carry += _num(row, f["carry"])
                if f.get("defect"):
                    sub_defect += _num(row, f["defect"])
                if f.get("scrap"):
                    sub_scrap += _num(row, f["scrap"])
                if f.get("onHold"):
                    sub_on_hold += _num(row, f["onHold"])
        trend = carry + sub_carry + actual - defect - scrap - on_hold - forecast - sub_defect - sub_scrap - sub_on_hold
        updates[trend_field] = trend
    return updates


def _compute_actual_plan_trend_updates(row: dict, sequence: list) -> dict:
    """上と同式だが *_actual_plan を使用。cutting/chamfering/molding/plating/welding/inspection の 6 工程のみ。"""
    updates = {}
    forecast = _num(row, "forecast_quantity")
    for key in TREND_PREFIXES:
        if key not in sequence:
            continue
        config = _get_process_config_by_key(key)
        if not config:
            continue
        fields = config.get("fields", {})
        trend_field = f"{key}_actual_plan_trend"
        carry = _num(row, fields.get("carry", ""))
        if fields.get("actual"):
            ap_col = fields["actual"].replace("_actual", "_actual_plan")
            actual_plan = _num(row, ap_col)
        else:
            actual_plan = 0
        defect = _num(row, fields.get("defect", "")) if fields.get("defect") else 0
        scrap = _num(row, fields.get("scrap", "")) if fields.get("scrap") else 0
        on_hold = _num(row, fields.get("onHold", "")) if fields.get("onHold") else 0
        idx = sequence.index(key) if key in sequence else -1
        sub_carry = sub_defect = sub_scrap = sub_on_hold = 0
        if idx >= 0:
            for j in range(idx + 1, len(sequence)):
                nc = _get_process_config_by_key(sequence[j])
                if nc and nc.get("fields"):
                    f = nc["fields"]
                    if f.get("carry"):
                        sub_carry += _num(row, f["carry"])
                    if f.get("defect"):
                        sub_defect += _num(row, f["defect"])
                    if f.get("scrap"):
                        sub_scrap += _num(row, f["scrap"])
                    if f.get("onHold"):
                        sub_on_hold += _num(row, f["onHold"])
        trend = carry + sub_carry + actual_plan - defect - scrap - on_hold - forecast - sub_defect - sub_scrap - sub_on_hold
        updates[trend_field] = trend
    return updates


async def _get_product_start_dates_for_summaries(db: AsyncSession) -> dict:
    """各 product_cd について「いずれかの工程 carry_over > 0 となる最後の日」の最大日を起算日とする。返却: { product_cd: start_date }"""
    carry_conds = or_(*[getattr(ProductionSummary, col) > 0 for col in CARRY_OVER_COLUMNS])
    q = (
        select(ProductionSummary.product_cd, func.max(ProductionSummary.date).label("start_date"))
        .where(carry_conds)
        .group_by(ProductionSummary.product_cd)
    )
    res = await db.execute(q)
    rows = res.fetchall()
    return {str(row[0]).strip(): row[1] for row in rows if row[0]}


def _row_to_inventory_dict(row) -> dict:
    """ORM 行を辞書に（数値は int、日付は文字列）"""
    d = {}
    for c in row.__table__.columns:
        v = getattr(row, c.name)
        if hasattr(v, "isoformat"):
            d[c.name] = v.isoformat()[:10] if v else None
        elif v is not None and isinstance(v, (int, float)):
            d[c.name] = int(v)
        else:
            d[c.name] = v
    return d


def _to_date_str(v) -> str:
    """日付を YYYY-MM-DD 文字列に変換"""
    if v is None:
        return ""
    if hasattr(v, "isoformat"):
        return v.isoformat()[:10]
    s = str(v)
    return s[:10] if len(s) >= 10 else s


async def _batch_case_update(db: AsyncSession, batch: list, columns: list):
    """
    batch 内の行を1条 SQL で一括更新。
    UPDATE production_summarys SET col1=CASE id WHEN 1 THEN v WHEN 2 THEN v ... END, col2=... WHERE id IN (...)
    """
    if not batch:
        return
    ids = [u["id"] for u in batch]
    set_parts = []
    params = {}
    for col in columns:
        cases = []
        has_col = False
        for idx, u in enumerate(batch):
            if col in u:
                has_col = True
                pk = f"id_{col}_{idx}"
                vk = f"v_{col}_{idx}"
                cases.append(f"WHEN id = :{pk} THEN :{vk}")
                params[pk] = u["id"]
                params[vk] = u[col]
        if has_col:
            set_parts.append(f"`{col}` = CASE {' '.join(cases)} ELSE `{col}` END")
    if not set_parts:
        return
    in_pks = ", ".join([f":pk_{i}" for i in range(len(ids))])
    for i, rid in enumerate(ids):
        params[f"pk_{i}"] = rid
    sql = f"UPDATE production_summarys SET {', '.join(set_parts)} WHERE id IN ({in_pks})"
    await db.execute(text(sql), params)


async def _resolve_date_range_and_rows(db: AsyncSession, body, start_time: float, trend_no_end_cap: bool = False):
    """在庫・推移共通: startDate からグローバル範囲を決め、行を取得して dict リスト化・product でグループ化。
    trend_no_end_cap=True かつ startDate 指定時は推移用に終了日を設けず date >= startDate の全行を対象とする。"""
    body = body or OptionalStartDateBody()
    global_start_d = None
    global_end_d = None
    product_start_dates = {}
    if body.startDate and body.startDate.strip():
        try:
            global_start_d = datetime.strptime(body.startDate.strip()[:10], "%Y-%m-%d").date()
            # 推移更新で startDate 指定時は終了日なし（表内の最大日まで）；在庫更新は startDate+3 ヶ月
            if trend_no_end_cap:
                global_end_d = date(2099, 12, 31)
            else:
                global_end_d = _parse_end_date(global_start_d, 3)
        except ValueError:
            raise HTTPException(status_code=400, detail="startDate は YYYY-MM-DD 形式で指定してください")
    if global_start_d is None:
        product_start_dates = await _get_product_start_dates_for_summaries(db)
        if not product_start_dates:
            return None, None, {}, {}, {}
        global_start_d = min(product_start_dates.values())
        global_end_d = max(_parse_end_date(d, 3) for d in product_start_dates.values())

    q = (
        select(ProductionSummary)
        .where(ProductionSummary.date >= global_start_d, ProductionSummary.date <= global_end_d)
        .order_by(ProductionSummary.product_cd, ProductionSummary.date)
    )
    result = await db.execute(q)
    rows = result.scalars().all()
    if not rows:
        return None, None, {}, {}, {}

    # product 別起算日フィルタ
    if product_start_dates:
        end_by_product = {pc: _parse_end_date(sd, 3) for pc, sd in product_start_dates.items()}
        filtered = []
        for r in rows:
            pc = (r.product_cd or "").strip()
            if pc in product_start_dates and product_start_dates[pc] <= r.date <= end_by_product.get(pc, r.date):
                filtered.append(r)
        rows = filtered

    if not rows:
        return None, None, {}, {}, {}

    # route description キャッシュ
    route_desc_by_cd = {}
    pr_res = await db.execute(select(ProcessRoute.route_cd, ProcessRoute.description))
    for r in pr_res.fetchall():
        if r[0]:
            route_desc_by_cd[r[0]] = r[1]

    # dict 変換してグループ化
    by_product = {}
    for r in rows:
        d = _row_to_inventory_dict(r)
        pc = (d.get("product_cd") or "").strip()
        if not pc:
            continue
        if pc not in by_product:
            by_product[pc] = []
        by_product[pc].append(d)

    # production_summarys.route_cd が空の製品用：products テーブルから route_cd を取得（最後工程判定のため）
    product_route_by_cd = {}
    if by_product:
        pq = select(Product.product_cd, Product.route_cd).where(
            Product.product_cd.in_([pc for pc in by_product.keys() if (pc or "").strip()])
        )
        prd_res = await db.execute(pq)
        for r in prd_res.fetchall():
            if r[0]:
                product_route_by_cd[(r[0] or "").strip()] = (r[1] or "").strip() if r[1] else ""

    return global_start_d, product_start_dates, route_desc_by_cd, by_product, product_route_by_cd


@router.post("/update-inventory")
async def update_production_summarys_inventory(
    body: Optional[OptionalStartDateBody] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """在庫更新（CASE WHEN 一括最適化版）"""
    start_time = time.perf_counter()
    try:
        global_start_d, product_start_dates, route_desc_by_cd, by_product, product_route_by_cd = \
            await _resolve_date_range_and_rows(db, body or OptionalStartDateBody(), start_time)
        if not by_product:
            return {
                "code": 200,
                "data": {"updated": 0, "skipped": 0, "total": 0, "elapsedTime": round(time.perf_counter() - start_time, 2)},
                "message": "更新する在庫データがありません",
            }

        # 一括で範囲内在庫列をクリア（全列を1条 SQL で）
        all_ids = [r["id"] for rows in by_product.values() for r in rows]
        clear_vals = {col: 0 for col in INVENTORY_COLUMNS}
        CLEAR_BATCH = 5000
        for i in range(0, len(all_ids), CLEAR_BATCH):
            chunk = all_ids[i: i + CLEAR_BATCH]
            await db.execute(update(ProductionSummary).where(ProductionSummary.id.in_(chunk)).values(**clear_vals))
        await db.commit()

        route_sequences = {}
        updated_count = 0
        BATCH = 100
        updates_batch = []

        async def _flush_batch():
            nonlocal updates_batch, updated_count
            if not updates_batch:
                return
            await _batch_case_update(db, updates_batch, INVENTORY_COLUMNS)
            updated_count += len(updates_batch)
            updates_batch = []

        for product_cd, product_rows in by_product.items():
            product_rows.sort(key=lambda x: (x.get("date") or ""))
            # 最後工程判定：production_summarys.route_cd が空の場合は products の route_cd を使用（900B FR/RR 等で外注倉庫が正しく判定されるように）
            route_cd = (product_rows[0].get("route_cd") or "").strip() if product_rows else ""
            if not route_cd:
                route_cd = product_route_by_cd.get(product_cd, "") or ""
            route_description = route_desc_by_cd.get(route_cd) if route_cd else None
            cache_key = (route_cd, route_description)
            if cache_key not in route_sequences:
                route_sequences[cache_key] = await _get_route_sequence(db, route_cd, route_description)
            sequence = route_sequences[cache_key]
            if not sequence:
                continue

            product_start = product_start_dates.get(product_cd, global_start_d)
            product_start_str = _to_date_str(product_start)

            # 扣除数用：该产品「order_quantity > 0 的最后日期」lastOrderQuantityDate；当日 <= 该日且 order_quantity > 0 时用 order_quantity，否则用 forecast_quantity
            last_order_date = None
            for r in product_rows:
                if _num(r, "order_quantity") > 0:
                    d = r.get("date")
                    if d:
                        ds = _to_date_str(d)
                        if ds and (last_order_date is None or ds > last_order_date):
                            last_order_date = ds

            previous_inv = {}
            prev_warehouse = 0
            prev_outsourced_wh = 0
            for r in product_rows:
                dt_str = _to_date_str(r.get("date"))
                is_start_date = (dt_str == product_start_str) if product_start_str else False
                # 扣除数：存在 lastOrderQuantityDate 且 当前 date <= 该日 且 order_quantity > 0 时用 order_quantity，否则用 forecast_quantity（内示）
                order_qty = _num(r, "order_quantity")
                if last_order_date is not None and dt_str is not None and dt_str <= last_order_date and order_qty > 0:
                    qty_subtract = order_qty
                else:
                    qty_subtract = _num(r, "forecast_quantity")

                inv_updates = _compute_inventory_updates(r, sequence, previous_inv, is_start_date)
                for k, v in inv_updates.items():
                    r[k] = v
                for key in sequence:
                    if key == "outsourced_warehouse":
                        continue
                    cfg = _get_process_config_by_key(key)
                    if cfg and cfg.get("fields", {}).get("inventory"):
                        previous_inv[key] = r.get(cfg["fields"]["inventory"], 0)

                if sequence[-1] == "warehouse":
                    wh_inv = _compute_warehouse_inventory(r, qty_subtract, prev_warehouse)
                    r["warehouse_inventory"] = wh_inv
                    prev_warehouse = wh_inv
                elif sequence[-1] == "outsourced_warehouse":
                    ow_inv = _compute_outsourced_warehouse_inventory(r, qty_subtract, prev_outsourced_wh)
                    r["outsourced_warehouse_inventory"] = ow_inv
                    prev_outsourced_wh = ow_inv

                updates_batch.append(r)
                if len(updates_batch) >= BATCH:
                    await _flush_batch()
                    await db.commit()

        await _flush_batch()
        await db.commit()
        total = sum(len(v) for v in by_product.values())
        elapsed = round(time.perf_counter() - start_time, 2)
        return {
            "code": 200,
            "data": {"updated": updated_count, "skipped": 0, "total": total, "elapsedTime": elapsed},
            "message": f"{updated_count}件の在庫データを更新しました（{elapsed}秒）",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update-inventory でエラー: %s", e)
        try:
            await db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"在庫更新に失敗しました: {str(e)}") from e


@router.post("/update-trend")
async def update_production_summarys_trend(
    body: Optional[OptionalStartDateBody] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """推移更新（CASE WHEN 一括最適化版）"""
    start_time = time.perf_counter()
    try:
        # 推移更新：startDate 指定時は date >= startDate の全行を対象（終了日なし）
        global_start_d, product_start_dates, route_desc_by_cd, by_product, product_route_by_cd = \
            await _resolve_date_range_and_rows(db, body or OptionalStartDateBody(), start_time, trend_no_end_cap=True)
        if not by_product:
            return {
                "code": 200,
                "data": {"updated": 0, "skipped": 0, "total": 0, "elapsedTime": round(time.perf_counter() - start_time, 2)},
                "message": "更新する推移データがありません",
            }

        # 対象 trend 列を全て集める
        all_trend_cols = set()
        for c in INVENTORY_PROCESS_CONFIG:
            tf = c.get("fields", {}).get("trend")
            if tf:
                all_trend_cols.add(tf)
        for p in TREND_PREFIXES:
            all_trend_cols.add(f"{p}_actual_plan_trend")
        all_trend_cols = [c for c in all_trend_cols if hasattr(ProductionSummary, c)]

        # 一括クリア
        all_ids = [r["id"] for rows in by_product.values() for r in rows]
        clear_vals = {col: 0 for col in all_trend_cols}
        CLEAR_BATCH = 5000
        for i in range(0, len(all_ids), CLEAR_BATCH):
            chunk = all_ids[i: i + CLEAR_BATCH]
            await db.execute(update(ProductionSummary).where(ProductionSummary.id.in_(chunk)).values(**clear_vals))
        await db.commit()

        route_sequences = {}
        updated_count = 0
        BATCH = 100
        updates_batch = []

        async def _flush_batch():
            nonlocal updates_batch, updated_count
            if not updates_batch:
                return
            await _batch_case_update(db, updates_batch, all_trend_cols)
            updated_count += len(updates_batch)
            updates_batch = []

        for product_cd, product_rows in by_product.items():
            product_rows.sort(key=lambda x: (x.get("date") or ""))
            route_cd = (product_rows[0].get("route_cd") or "").strip() if product_rows else ""
            if not route_cd:
                route_cd = product_route_by_cd.get(product_cd, "") or ""
            route_description = route_desc_by_cd.get(route_cd) if route_cd else None
            cache_key = (route_cd, route_description)
            if cache_key not in route_sequences:
                route_sequences[cache_key] = await _get_route_sequence(db, route_cd, route_description)
            sequence = route_sequences[cache_key]

            prev_trends = {}
            prev_actual_plan_trends = {}
            for r in product_rows:
                day_trends = _compute_trend_updates(r, sequence)
                day_ap_trends = _compute_actual_plan_trend_updates(r, sequence)
                for field, day_val in day_trends.items():
                    key = field.replace("_trend", "")
                    prev = prev_trends.get(key, 0)
                    r[field] = day_val + prev
                    prev_trends[key] = r[field]
                for field, day_val in day_ap_trends.items():
                    key = field.replace("_actual_plan_trend", "")
                    prev = prev_actual_plan_trends.get(key, 0)
                    r[field] = day_val + prev
                    prev_actual_plan_trends[key] = r[field]
                updates_batch.append(r)
                if len(updates_batch) >= BATCH:
                    await _flush_batch()
                    await db.commit()

        await _flush_batch()
        await db.commit()
        total = sum(len(v) for v in by_product.values())
        elapsed = round(time.perf_counter() - start_time, 2)
        return {
            "code": 200,
            "data": {"updated": updated_count, "skipped": 0, "total": total, "elapsedTime": elapsed},
            "message": f"{updated_count}件の推移データを更新しました（{elapsed}秒）",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update-trend でエラー: %s", e)
        try:
            await db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"推移更新に失敗しました: {str(e)}") from e


def _next_n_workdays(from_date: date, n: int = 30):
    """from_date の翌日から数えて n 個の営業日（土日除く）の日付リストを返す。"""
    d = from_date + timedelta(days=1)
    out = []
    while len(out) < n:
        if d.weekday() < 5:  # Mon=0, Fri=4
            out.append(d)
        d += timedelta(days=1)
    return out


@router.post("/update-safety-stock")
async def update_production_summarys_safety_stock(
    body: Optional[OptionalStartDateBody] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    安全在庫更新：製品マスタの safety_days > 0 の製品について、
    安全在庫 = ceil(将来30営業日の平均日出荷数 × safety_days)。
    平均日出荷数は production_summarys の内示数(forecast_quantity)を将来30営業日で平均した値。
    """
    start_time = time.perf_counter()
    try:
        global_start_d, product_start_dates, _, by_product, _ = await _resolve_date_range_and_rows(
            db, body or OptionalStartDateBody(), start_time, trend_no_end_cap=False
        )
        if not by_product:
            return {
                "code": 200,
                "data": {"updated": 0, "skipped": 0, "total": 0, "elapsedTime": round(time.perf_counter() - start_time, 2)},
                "message": "更新するデータがありません",
            }

        # 製品マスタで safety_days IS NOT NULL AND safety_days > 0 の product_cd のみ対象
        pq = select(Product.product_cd, Product.safety_days).where(
            Product.product_cd.in_(list(by_product.keys())),
            Product.safety_days.isnot(None),
            Product.safety_days > 0,
        )
        pr_res = await db.execute(pq)
        product_safety_days = {row[0]: int(row[1]) for row in pr_res.fetchall() if row[0] and row[1] is not None}
        if not product_safety_days:
            await db.commit()
            return {
                "code": 200,
                "data": {"updated": 0, "skipped": len(by_product), "total": sum(len(v) for v in by_product.values()), "elapsedTime": round(time.perf_counter() - start_time, 2)},
                "message": "安全在庫日数が設定された製品がありません（safety_days > 0）",
            }

        # 対象行を product_cd でフィルタ（safety_days が設定されている製品のみ）
        by_product_filtered = {pc: rows for pc, rows in by_product.items() if pc in product_safety_days}
        if not by_product_filtered:
            await db.commit()
            return {
                "code": 200,
                "data": {"updated": 0, "skipped": 0, "total": 0, "elapsedTime": round(time.perf_counter() - start_time, 2)},
                "message": "更新するデータがありません",
            }

        # 将来30営業日分の forecast を取るため、日付範囲を延長（最大 date + 60 日程度）
        all_dates = set()
        for rows in by_product_filtered.values():
            for r in rows:
                d = r.get("date")
                if d:
                    if hasattr(d, "isoformat"):
                        base = d if isinstance(d, date) else datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
                    else:
                        base = datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
                    for fd in _next_n_workdays(base, 30):
                        all_dates.add(fd)
        if not all_dates:
            return {
                "code": 200,
                "data": {"updated": 0, "skipped": 0, "total": 0, "elapsedTime": round(time.perf_counter() - start_time, 2)},
                "message": "更新するデータがありません",
            }
        min_fetch = min(all_dates)
        max_fetch = max(all_dates)
        product_cds = list(by_product_filtered.keys())

        # production_summarys から (product_cd, date) の forecast_quantity を一括取得
        q_forecast = (
            select(ProductionSummary.product_cd, ProductionSummary.date, ProductionSummary.forecast_quantity)
            .where(
                ProductionSummary.product_cd.in_(product_cds),
                ProductionSummary.date >= min_fetch,
                ProductionSummary.date <= max_fetch,
            )
        )
        res_forecast = await db.execute(q_forecast)
        forecast_map = {}
        for row in res_forecast.fetchall():
            pc = (row[0] or "").strip()
            if not pc:
                continue
            dt = row[1]
            qty = int(row[2]) if row[2] is not None else 0
            forecast_map[(pc, dt)] = qty

        updated_count = 0
        BATCH = 100
        updates_batch = []

        def _parse_row_date(r):
            d = r.get("date")
            if d is None:
                return None
            if isinstance(d, date):
                return d
            s = str(d)[:10]
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except ValueError:
                return None

        for product_cd, product_rows in by_product_filtered.items():
            safety_days = product_safety_days.get(product_cd, 0)
            if safety_days <= 0:
                continue
            for r in product_rows:
                base_date = _parse_row_date(r)
                if base_date is None:
                    continue
                next_30 = _next_n_workdays(base_date, 30)
                total_forecast = sum(forecast_map.get((product_cd, d), 0) for d in next_30)
                n_days = len(next_30)
                avg_daily = (total_forecast / n_days) if n_days else 0
                safety_val = int(math.ceil(avg_daily * safety_days)) if avg_daily else 0
                r["safety_stock"] = safety_val
                updates_batch.append(r)
                if len(updates_batch) >= BATCH:
                    await _batch_case_update(db, updates_batch, ["safety_stock"])
                    updated_count += len(updates_batch)
                    updates_batch = []
                    await db.commit()

        if updates_batch:
            await _batch_case_update(db, updates_batch, ["safety_stock"])
            updated_count += len(updates_batch)
        await db.commit()
        elapsed = round(time.perf_counter() - start_time, 2)
        return {
            "code": 200,
            "data": {"updated": updated_count, "skipped": 0, "total": updated_count, "elapsedTime": elapsed},
            "message": f"{updated_count}件の安全在庫を更新しました（{elapsed}秒）",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update-safety-stock でエラー: %s", e)
        try:
            await db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"安全在庫更新に失敗しました: {str(e)}") from e


class UpdateProductMasterBody(BaseModel):
    startDate: str  # YYYY-MM-DD
    endDate: str    # YYYY-MM-DD


@router.post("/update-product-master")
async def update_production_summarys_product_master(
    body: UpdateProductMasterBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    製品マスタ更新：products の route_cd, product_name を production_summarys に同期。
    指定期間内の行のみ更新。
    """
    start_time = time.perf_counter()
    if not body.startDate or not body.endDate:
        raise HTTPException(status_code=400, detail="開始日と終了日を指定してください")
    try:
        start_d = datetime.strptime(body.startDate.strip()[:10], "%Y-%m-%d").date()
        end_d = datetime.strptime(body.endDate.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="日付は YYYY-MM-DD 形式で指定してください")

    sql = text("""
        UPDATE production_summarys ps
        INNER JOIN products p
          ON ps.product_cd COLLATE utf8mb4_unicode_ci = p.product_cd COLLATE utf8mb4_unicode_ci
        SET
          ps.route_cd = COALESCE(p.route_cd, ps.route_cd),
          ps.product_name = COALESCE(p.product_name, ps.product_name)
        WHERE ps.date >= :start_date AND ps.date <= :end_date
    """)
    result = await db.execute(sql, {"start_date": start_d, "end_date": end_d})
    updated = result.rowcount
    await db.commit()
    elapsed = round(time.perf_counter() - start_time, 2)
    return {
        "code": 200,
        "data": {
            "updated": updated,
            "skipped": 0,
            "startDate": body.startDate,
            "endDate": body.endDate,
            "elapsedTime": elapsed,
        },
        "message": f"製品マスタの更新が完了しました（{updated}件）",
    }


class UpdateMachineBody(BaseModel):
    startDate: str  # YYYY-MM-DD
    endDate: str    # YYYY-MM-DD


@router.post("/update-machine")
async def update_production_summarys_machine(
    body: UpdateMachineBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    設備フィールド更新：product_machine_config と machines から
    production_summarys の各工程 *_machine 列を同期。指定期間内の行のみ更新。
    """
    start_time = time.perf_counter()
    if not body.startDate or not body.endDate:
        raise HTTPException(status_code=400, detail="開始日と終了日を指定してください")
    try:
        start_d = datetime.strptime(body.startDate.strip()[:10], "%Y-%m-%d").date()
        end_d = datetime.strptime(body.endDate.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="日付は YYYY-MM-DD 形式で指定してください")

    sql = text("""
        UPDATE production_summarys ps
        INNER JOIN product_machine_config pmc
          ON ps.product_cd COLLATE utf8mb4_unicode_ci = pmc.product_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_cutting
          ON pmc.cutting_machine COLLATE utf8mb4_unicode_ci = m_cutting.machine_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_chamfering
          ON pmc.chamfering_machine COLLATE utf8mb4_unicode_ci = m_chamfering.machine_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_sw
          ON pmc.sw_machine COLLATE utf8mb4_unicode_ci = m_sw.machine_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_molding
          ON pmc.molding_machine COLLATE utf8mb4_unicode_ci = m_molding.machine_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_plating
          ON pmc.plating_machine COLLATE utf8mb4_unicode_ci = m_plating.machine_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_welding
          ON pmc.welding_machine COLLATE utf8mb4_unicode_ci = m_welding.machine_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_inspector
          ON pmc.inspector_machine COLLATE utf8mb4_unicode_ci = m_inspector.machine_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_outsourced_plating
          ON pmc.outsourced_plating_machine COLLATE utf8mb4_unicode_ci = m_outsourced_plating.machine_cd COLLATE utf8mb4_unicode_ci
        LEFT JOIN machines m_outsourced_welding
          ON pmc.outsourced_welding_machine COLLATE utf8mb4_unicode_ci = m_outsourced_welding.machine_cd COLLATE utf8mb4_unicode_ci
        SET
          ps.cutting_machine = COALESCE(m_cutting.machine_name, pmc.cutting_machine, ps.cutting_machine),
          ps.chamfering_machine = COALESCE(m_chamfering.machine_name, pmc.chamfering_machine, ps.chamfering_machine),
          ps.sw_machine = COALESCE(m_sw.machine_name, pmc.sw_machine, ps.sw_machine),
          ps.molding_machine = COALESCE(m_molding.machine_name, pmc.molding_machine, ps.molding_machine),
          ps.plating_machine = COALESCE(m_plating.machine_name, pmc.plating_machine, ps.plating_machine),
          ps.welding_machine = COALESCE(m_welding.machine_name, pmc.welding_machine, ps.welding_machine),
          ps.inspector_machine = COALESCE(m_inspector.machine_name, pmc.inspector_machine, ps.inspector_machine),
          ps.outsourced_plating_machine = COALESCE(m_outsourced_plating.machine_name, pmc.outsourced_plating_machine, ps.outsourced_plating_machine),
          ps.outsourced_welding_machine = COALESCE(m_outsourced_welding.machine_name, pmc.outsourced_welding_machine, ps.outsourced_welding_machine)
        WHERE ps.date >= :start_date AND ps.date <= :end_date
    """)
    result = await db.execute(sql, {"start_date": start_d, "end_date": end_d})
    updated = result.rowcount
    await db.commit()
    elapsed = round(time.perf_counter() - start_time, 2)
    return {
        "code": 200,
        "data": {
            "updated": updated,
            "skipped": 0,
            "startDate": body.startDate,
            "endDate": body.endDate,
            "elapsedTime": elapsed,
        },
        "message": f"機器フィールドの更新が完了しました（{updated}件）",
    }

"""
理論在庫（production_summarys.*_inventory）と棚卸在庫（inventory_logs 製品棚卸）の比較 API。
"""
from __future__ import annotations

from collections import defaultdict
from calendar import monthrange
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_inventory_operation
from app.modules.database.models import ProductionSummary
from app.modules.erp.inventory_value_api import (
    _PROCESS_CD_TO_INVENTORY_COL,
    _deduped_process_inventory_specs,
    _parse_as_of_date,
)
from app.modules.master.models import Process, Product

router = APIRouter(prefix="/inventory-comparison", tags=["在庫比較"])

_STOCKTAKE_ITEM = "製品棚卸"

# 同一 inventory 列に複数 process_cd（KT10/KT15 等）がある場合の代表 CD
_INV_COL_TO_CANONICAL_PROC: Dict[str, str] = {}
for _pc, _col in _PROCESS_CD_TO_INVENTORY_COL.items():
    _INV_COL_TO_CANONICAL_PROC.setdefault(_col, _pc)


def _month_bounds(as_of_d: date) -> Tuple[date, date]:
    """as_of が属する月の初日・末日。"""
    month_start = date(as_of_d.year, as_of_d.month, 1)
    last_day = monthrange(as_of_d.year, as_of_d.month)[1]
    month_end = date(as_of_d.year, as_of_d.month, last_day)
    return month_start, month_end


def _canonical_process_cd(process_cd: Optional[str]) -> str:
    """棚卸ログの process_cd を理論側展開と同じ代表 CD に揃える。"""
    raw = str(process_cd or "").strip()
    if not raw:
        return raw
    inv_col = _PROCESS_CD_TO_INVENTORY_COL.get(raw)
    if inv_col:
        return _INV_COL_TO_CANONICAL_PROC.get(inv_col, raw)
    return raw


def _process_cds_for_filter(process_cd: str) -> List[str]:
    """工程フィルター：同一 inventory 列に紐づく全 process_cd を含める。"""
    inv_col = _PROCESS_CD_TO_INVENTORY_COL.get(process_cd.strip())
    if not inv_col:
        return [process_cd.strip()]
    return [pc for pc, col in _PROCESS_CD_TO_INVENTORY_COL.items() if col == inv_col]


def _is_stocktake_product_cd(product_cd: Optional[str]) -> bool:
    s = str(product_cd or "").strip()
    return len(s) > 0 and s.endswith("1")


def _comparison_status(theoretical_qty: int, stocktake_qty: int) -> str:
    if theoretical_qty == 0 and stocktake_qty == 0:
        return "match"
    if theoretical_qty == 0 and stocktake_qty != 0:
        return "only_stocktake"
    if theoretical_qty != 0 and stocktake_qty == 0:
        return "only_theoretical"
    if theoretical_qty == stocktake_qty:
        return "match"
    return "mismatch"


def _detail_sort_key(row: dict, sort_by: str) -> tuple:
    sb = (sort_by or "").strip()
    if sb == "product_cd":
        return (str(row.get("product_cd") or "").casefold(),)
    if sb == "product_name":
        return (str(row.get("product_name") or "").casefold(),)
    if sb == "process_cd":
        return (str(row.get("process_cd") or "").casefold(),)
    if sb == "theoretical_qty":
        return (int(row.get("theoretical_qty") or 0),)
    if sb == "stocktake_qty":
        return (int(row.get("stocktake_qty") or 0),)
    if sb == "diff_qty":
        return (int(row.get("diff_qty") or 0),)
    if sb == "status":
        return (str(row.get("status") or "").casefold(),)
    return (abs(int(row.get("diff_qty") or 0)), str(row.get("product_cd") or "").casefold())


async def _load_process_names(db: AsyncSession, process_cds: List[str]) -> Dict[str, str]:
    if not process_cds:
        return {}
    rows = list(
        (await db.execute(select(Process.process_cd, Process.process_name).where(Process.process_cd.in_(process_cds)))).all()
    )
    out: Dict[str, str] = {}
    for cd, name in rows:
        k = str(cd or "").strip()
        if k:
            out[k] = (str(name or "").strip() or k)
    return out


async def _fetch_theoretical_by_product_process(
    db: AsyncSession,
    as_of_d: date,
    process_cd_filter: Optional[str],
) -> Tuple[Dict[Tuple[str, str], int], Dict[str, str]]:
    """(product_cd, process_cd) -> qty; product_cd -> name（route 跨ぎ合算）。"""
    specs = _deduped_process_inventory_specs()
    if process_cd_filter:
        specs = [(pc, col) for pc, col in specs if pc == _canonical_process_cd(process_cd_filter)]
        if not specs:
            return {}, {}

    q = select(ProductionSummary).where(ProductionSummary.date == as_of_d)
    summary_rows = list((await db.execute(q)).scalars().all())

    qty_map: Dict[Tuple[str, str], int] = defaultdict(int)
    name_by_cd: Dict[str, str] = {}
    for row in summary_rows:
        pcd = str(row.product_cd or "").strip()
        if not pcd or not _is_stocktake_product_cd(pcd):
            continue
        pname = str(row.product_name or pcd).strip()
        name_by_cd[pcd] = pname
        for proc_cd, inv_col in specs:
            qty = int(getattr(row, inv_col, None) or 0)
            if qty:
                qty_map[(pcd, proc_cd)] += qty
    return dict(qty_map), name_by_cd


async def _fetch_stocktake_by_product_process(
    db: AsyncSession,
    as_of_d: date,
    process_cd_filter: Optional[str],
) -> Tuple[Dict[Tuple[str, str], int], Dict[str, str]]:
    month_start, month_end = _month_bounds(as_of_d)
    params: dict = {
        "item": _STOCKTAKE_ITEM,
        "month_start": month_start,
        "month_end": month_end,
    }
    # 棚卸は月内の複数日に分散して登録されるため、対象月全体を集計（棚卸統計と同口径）
    sql = """
        SELECT product_cd, product_name, process_cd, SUM(quantity) AS stocktake_qty
        FROM inventory_logs
        WHERE item = :item
          AND log_date >= :month_start AND log_date <= :month_end
          AND product_cd LIKE '%1'
    """
    if process_cd_filter:
        proc_list = _process_cds_for_filter(process_cd_filter)
        placeholders = ", ".join(f":proc_{i}" for i in range(len(proc_list)))
        sql += f" AND process_cd IN ({placeholders})"
        for i, pc in enumerate(proc_list):
            params[f"proc_{i}"] = pc
    sql += " GROUP BY product_cd, product_name, process_cd"

    try:
        result = await db.execute(text(sql), params)
        rows = result.fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"棚卸データの取得に失敗しました: {exc}") from exc

    qty_map: Dict[Tuple[str, str], int] = defaultdict(int)
    name_by_cd: Dict[str, str] = {}
    for row in rows:
        pcd = str(row[0] or "").strip()
        pname = str(row[1] or pcd).strip()
        proc = _canonical_process_cd(str(row[2] or "").strip())
        qty = int(row[3] or 0)
        if not pcd or not proc:
            continue
        qty_map[(pcd, proc)] += qty
        name_by_cd[pcd] = pname
    return dict(qty_map), name_by_cd


def _apply_product_filters(
    keys: Set[Tuple[str, str]],
    product_cd: Optional[str],
    keyword: Optional[str],
    name_by_cd: Dict[str, str],
) -> Set[Tuple[str, str]]:
    cd_exact = (product_cd or "").strip() or None
    kw = (keyword or "").strip().casefold() or None
    if not cd_exact and not kw:
        return keys
    out: Set[Tuple[str, str]] = set()
    for pcd, proc in keys:
        if cd_exact and pcd != cd_exact:
            continue
        if kw:
            pname = name_by_cd.get(pcd, "").casefold()
            if kw not in pcd.casefold() and kw not in pname:
                continue
        out.add((pcd, proc))
    return out


async def _build_detail_rows(
    db: AsyncSession,
    as_of_d: date,
    process_cd_filter: Optional[str],
    product_cd: Optional[str],
    keyword: Optional[str],
    only_diff: bool,
) -> Tuple[List[dict], dict]:
    theoretical_map, th_names = await _fetch_theoretical_by_product_process(db, as_of_d, process_cd_filter)
    stocktake_map, st_names = await _fetch_stocktake_by_product_process(db, as_of_d, process_cd_filter)

    all_keys = set(theoretical_map.keys()) | set(stocktake_map.keys())
    combined_names = {**th_names, **st_names}
    all_keys = _apply_product_filters(all_keys, product_cd, keyword, combined_names)

    proc_cds = sorted({proc for _, proc in all_keys})
    proc_names = await _load_process_names(db, proc_cds)

    # product_name 補完（マスタ）
    missing_pcds = {pcd for pcd, _ in all_keys if pcd not in th_names and pcd not in st_names}
    if missing_pcds:
        pq = select(Product.product_cd, Product.product_name).where(Product.product_cd.in_(list(missing_pcds)))
        for pcd, pname in (await db.execute(pq)).all():
            k = str(pcd or "").strip()
            if k:
                th_names.setdefault(k, (str(pname or "").strip() or k))

    detail_rows: List[dict] = []
    for pcd, proc in sorted(all_keys, key=lambda x: (x[0], x[1])):
        th_qty = int(theoretical_map.get((pcd, proc), 0))
        st_qty = int(stocktake_map.get((pcd, proc), 0))
        diff = st_qty - th_qty
        if only_diff and diff == 0:
            continue
        if th_qty == 0 and st_qty == 0 and only_diff:
            continue
        pname = th_names.get(pcd) or st_names.get(pcd) or pcd
        status = _comparison_status(th_qty, st_qty)
        detail_rows.append(
            {
                "product_cd": pcd,
                "product_name": pname,
                "process_cd": proc,
                "process_name": proc_names.get(proc, proc),
                "theoretical_qty": th_qty,
                "stocktake_qty": st_qty,
                "diff_qty": diff,
                "status": status,
            }
        )

    kpi = _compute_kpi_from_details(detail_rows)
    return detail_rows, kpi


def _compute_kpi_from_details(detail_rows: List[dict]) -> dict:
    total_th = sum(int(r.get("theoretical_qty") or 0) for r in detail_rows)
    total_st = sum(int(r.get("stocktake_qty") or 0) for r in detail_rows)
    match_count = sum(1 for r in detail_rows if r.get("status") == "match")
    mismatch_count = sum(1 for r in detail_rows if r.get("status") == "mismatch")
    only_th = sum(1 for r in detail_rows if r.get("status") == "only_theoretical")
    only_st = sum(1 for r in detail_rows if r.get("status") == "only_stocktake")
    total_items = len(detail_rows)
    match_rate = round(match_count / total_items * 100, 2) if total_items else 0.0
    return {
        "theoretical_qty_total": total_th,
        "stocktake_qty_total": total_st,
        "diff_qty_total": total_st - total_th,
        "item_count": total_items,
        "matched_count": match_count,
        "mismatch_count": mismatch_count,
        "only_theoretical_count": only_th,
        "only_stocktake_count": only_st,
        "match_rate": match_rate,
    }


def _build_summary_rows(detail_rows: List[dict], proc_specs: List[Tuple[str, str]], proc_names: Dict[str, str]) -> List[dict]:
    by_proc: Dict[str, List[dict]] = defaultdict(list)
    for row in detail_rows:
        by_proc[str(row.get("process_cd") or "")].append(row)

    summary: List[dict] = []
    for proc_cd, _inv_col in proc_specs:
        rows = by_proc.get(proc_cd, [])
        th_sum = sum(int(r.get("theoretical_qty") or 0) for r in rows)
        st_sum = sum(int(r.get("stocktake_qty") or 0) for r in rows)
        diff = st_sum - th_sum
        diff_rate: Optional[float]
        if th_sum != 0:
            diff_rate = round(diff / th_sum * 100, 2)
        elif st_sum != 0:
            diff_rate = None
        else:
            diff_rate = 0.0
        matched = sum(1 for r in rows if r.get("status") == "match")
        only_th = sum(1 for r in rows if r.get("status") == "only_theoretical")
        only_st = sum(1 for r in rows if r.get("status") == "only_stocktake")
        mismatch = sum(1 for r in rows if r.get("status") == "mismatch")
        item_count = len(rows)
        match_rate = round(matched / item_count * 100, 2) if item_count else 0.0
        summary.append(
            {
                "process_cd": proc_cd,
                "process_name": proc_names.get(proc_cd, proc_cd),
                "theoretical_qty": th_sum,
                "stocktake_qty": st_sum,
                "diff_qty": diff,
                "diff_rate": diff_rate,
                "item_count": item_count,
                "matched_count": matched,
                "only_theoretical_count": only_th,
                "only_stocktake_count": only_st,
                "mismatch_count": mismatch,
                "match_rate": match_rate,
            }
        )
    return summary


@router.get("/product")
async def get_product_inventory_comparison(
    as_of: str = Query(..., description="対象日 YYYY-MM-DD"),
    process_cd: Optional[str] = Query(None, description="工程CD（省略時は全工程）"),
    product_cd: Optional[str] = Query(None, description="製品CD（完全一致）"),
    keyword: Optional[str] = Query(None, description="製品CD部分一致"),
    view: str = Query("summary", description="summary | detail"),
    only_diff: bool = Query(False, description="差異のみ"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    sort_by: str = Query("diff_qty"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    """
    製品×工程：理論在庫 vs 棚卸在庫比較。
    理論側は production_summarys（route 跨ぎ合算）、棚卸側は inventory_logs 製品棚卸（CD末尾1）。
    """
    as_of_d = _parse_as_of_date(as_of)
    view_norm = (view or "summary").strip().lower()
    if view_norm not in ("summary", "detail"):
        raise HTTPException(status_code=422, detail="view は summary または detail を指定してください")

    proc_filter = (process_cd or "").strip() or None
    if proc_filter and str(proc_filter).lower() == "all":
        proc_filter = None
    if proc_filter:
        proc_filter = _canonical_process_cd(proc_filter)

    detail_rows, kpi = await _build_detail_rows(
        db, as_of_d, proc_filter, product_cd, keyword, only_diff
    )

    if view_norm == "detail":
        desc_order = str(sort_order).strip().lower() == "desc"
        detail_rows.sort(key=lambda r: _detail_sort_key(r, sort_by), reverse=desc_order)
        total = len(detail_rows)
        start = (page - 1) * limit
        page_rows = detail_rows[start : start + limit]
        return {
            "success": True,
            "data": {
                "as_of": str(as_of_d),
                "view": "detail",
                "list": page_rows,
                "total": total,
                "page": page,
                "limit": limit,
                "kpi": kpi,
            },
        }

    specs = _deduped_process_inventory_specs()
    if proc_filter:
        specs = [(pc, col) for pc, col in specs if pc == proc_filter]
    proc_cds = [pc for pc, _ in specs]
    proc_names = await _load_process_names(db, proc_cds)
    summary_rows = _build_summary_rows(detail_rows, specs, proc_names)

    return {
        "success": True,
        "data": {
            "as_of": str(as_of_d),
            "view": "summary",
            "list": summary_rows,
            "kpi": kpi,
        },
    }

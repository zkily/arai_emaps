"""
生産データ管理（production_summarys）と各工程来源表の不良・廃棄データ突合 API。
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.operation_deps import require_inventory_operation
from app.modules.database.api import PROCESS_DEFECT_MAPPING, PROCESS_SCRAP_MAPPING
from app.modules.database.models import ProductionSummary
from app.modules.master.models import Process, ProcessDefectItem

router = APIRouter(prefix="/defect-scrap-comparison", tags=["不良廃棄突合"])

# 突合対象工程（6 工程）
COMPARISON_PROCESS_CDS = ["KT01", "KT02", "KT04", "KT05", "KT07", "KT09"]

COMPARISON_PROCESS_MAP: Dict[str, dict] = {
    "KT01": {
        "process_name": "切断",
        "summary_defect_col": PROCESS_DEFECT_MAPPING["KT01"],
        "summary_scrap_col": PROCESS_SCRAP_MAPPING["KT01"],
        "source_type": "cutting",
        "source_note": "",
    },
    "KT02": {
        "process_name": "面取",
        "summary_defect_col": PROCESS_DEFECT_MAPPING["KT02"],
        "summary_scrap_col": PROCESS_SCRAP_MAPPING["KT02"],
        "source_type": "chamfering",
        "source_note": "",
    },
    "KT04": {
        "process_name": "成型",
        "summary_defect_col": PROCESS_DEFECT_MAPPING["KT04"],
        "summary_scrap_col": PROCESS_SCRAP_MAPPING["KT04"],
        "source_type": "forming",
        "source_note": "",
    },
    "KT05": {
        "process_name": "メッキ",
        "summary_defect_col": PROCESS_DEFECT_MAPPING["KT05"],
        "summary_scrap_col": PROCESS_SCRAP_MAPPING["KT05"],
        "source_type": "plating_daily",
        "source_note": "日次合計（品番なし）",
    },
    "KT07": {
        "process_name": "溶接",
        "summary_defect_col": PROCESS_DEFECT_MAPPING["KT07"],
        "summary_scrap_col": PROCESS_SCRAP_MAPPING["KT07"],
        "source_type": "welding",
        "source_note": "",
    },
    "KT09": {
        "process_name": "検査",
        "summary_defect_col": PROCESS_DEFECT_MAPPING["KT09"],
        "summary_scrap_col": PROCESS_SCRAP_MAPPING["KT09"],
        "source_type": "inspection",
        "source_note": "",
    },
}

INSPECTION_SCRAP_HEADER = "W検査　廃棄"


def _norm_name(s: str) -> str:
    return re.sub(r"\s+", "", str(s or "").strip())


def _normalize_product_cd(product_cd: Optional[str]) -> str:
    """
    production_summarys の品番に揃える（前4桁 + '1'）。
    製造側 Excel 由来の品番（4〜6桁など）と突合するため。
    """
    s = str(product_cd or "").strip()
    if len(s) >= 4:
        return s[:4] + "1"
    return s


def _as_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_date_param(value: str, field_name: str) -> date:
    raw = str(value or "").strip()
    if not raw:
        raise HTTPException(status_code=422, detail=f"{field_name} を指定してください")
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} は YYYY-MM-DD 形式で指定してください") from exc


def _qty_from_mes_defect_value(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, dict):
        q = val.get("qty")
        return int(q or 0)
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _extract_inspection_scrap_qty(raw: Any, scrap_keys: Set[str]) -> int:
    if not raw or not scrap_keys:
        return 0
    data: dict
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return 0
        if not isinstance(parsed, dict):
            return 0
        data = parsed
    elif isinstance(raw, dict):
        data = raw
    else:
        return 0
    total = 0
    for key, val in data.items():
        k = str(key or "").strip()
        if k in scrap_keys or k.endswith(INSPECTION_SCRAP_HEADER) or "W検査" in k and "廃棄" in k:
            total += _qty_from_mes_defect_value(val)
    return total


def _combined_qty(defect: Optional[int], scrap: Optional[int]) -> Optional[int]:
    """不良+廃棄の合算。両方が None のときのみ None（突合不可）。"""
    if defect is None and scrap is None:
        return None
    return int(defect or 0) + int(scrap or 0)


def _qty_match_rate(summary_total: int, source_total: int) -> float:
    """
    数量ベース一致率。
    1 - |製造−生産管理| / max(|生産管理|, |製造|, 1) を 0〜100% に丸める。
    ※行件数ベースだと両方0の行が「一致」に入り、一致率が異常に高くなるため数量ベースを採用。
    """
    s = abs(int(summary_total or 0))
    t = abs(int(source_total or 0))
    base = max(s, t, 1)
    diff = abs(t - s)
    return round(max(0.0, (1.0 - diff / base) * 100.0), 2)


def _row_match_counts(rows: List[dict]) -> Tuple[int, int, int, int, int]:
    """
    行ベース件数。両方0の一致行は一致率の分母・分子から除外する。
    returns: (matched, mismatch, only_summary, only_source, rate_denominator)
    """
    matched = 0
    mismatch = 0
    only_summary = 0
    only_source = 0
    for r in rows:
        status = r.get("status")
        s_total = int(r.get("summary_total") or 0)
        src_total = int(r.get("source_total") or 0) if r.get("source_total") is not None else 0
        if status == "match":
            if s_total == 0 and src_total == 0:
                continue
            matched += 1
        elif status == "mismatch":
            mismatch += 1
        elif status == "only_summary":
            only_summary += 1
        elif status == "only_source":
            only_source += 1
    rate_den = matched + mismatch + only_summary + only_source
    return matched, mismatch, only_summary, only_source, rate_den


def _comparison_status(
    summary_defect: int,
    source_defect: Optional[int],
    summary_scrap: int,
    source_scrap: Optional[int],
    *,
    comparable: bool,
    plating_daily_only: bool = False,
) -> str:
    """不良+廃棄合算で一度だけ突合する。"""
    if not comparable:
        return "not_comparable"
    if plating_daily_only:
        return "plating_daily_only"
    summary_total = int(summary_defect or 0) + int(summary_scrap or 0)
    source_total = _combined_qty(source_defect, source_scrap)
    if source_total is None:
        return "not_comparable"
    total_diff = source_total - summary_total
    has_summary = summary_total != 0
    has_source = source_total != 0
    if total_diff == 0:
        return "match"
    if has_summary and not has_source:
        return "only_summary"
    if has_source and not has_summary:
        return "only_source"
    return "mismatch"


def _detail_sort_key(row: dict, sort_by: str) -> tuple:
    sb = (sort_by or "").strip()
    if sb == "product_cd":
        return (str(row.get("product_cd") or "").casefold(),)
    if sb == "product_name":
        return (str(row.get("product_name") or "").casefold(),)
    if sb == "production_day":
        return (str(row.get("production_day") or ""),)
    if sb == "process_cd":
        return (str(row.get("process_cd") or "").casefold(),)
    if sb in ("total_diff", "defect_diff", "scrap_diff"):
        return (abs(int(row.get("total_diff") or row.get("defect_diff") or 0)),)
    if sb == "status":
        return (str(row.get("status") or "").casefold(),)
    return (
        abs(int(row.get("total_diff") or 0)),
        str(row.get("production_day") or ""),
        str(row.get("product_cd") or "").casefold(),
    )


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


async def _load_inspection_scrap_keys(db: AsyncSession) -> Set[str]:
    """検査廃棄に該当する mes_defect_by_item キー集合。"""
    keys: Set[str] = set()
    norm_target = _norm_name(INSPECTION_SCRAP_HEADER)
    q = select(ProcessDefectItem.defect_cd, ProcessDefectItem.defect_name).where(
        ProcessDefectItem.detection_process_cd == "KT09",
        ProcessDefectItem.status == "active",
    )
    for defect_cd, defect_name in (await db.execute(q)).all():
        cd = str(defect_cd or "").strip()
        name = str(defect_name or "").strip()
        if cd and _norm_name(name) == norm_target:
            keys.add(cd)
    keys.add(f"csv:{INSPECTION_SCRAP_HEADER}")
    keys.add(f"csv:{INSPECTION_SCRAP_HEADER.strip()}")
    return keys


async def _fetch_summary_maps(
    db: AsyncSession,
    start_d: date,
    end_d: date,
    product_cd_filter: Optional[str],
    process_cds: List[str],
) -> Tuple[Dict[Tuple[str, date, str], dict], Dict[str, str]]:
    """(product_cd, date, process_cd) -> {defect, scrap}; product_cd -> name"""
    q = select(ProductionSummary).where(
        ProductionSummary.date >= start_d,
        ProductionSummary.date <= end_d,
    )
    if product_cd_filter:
        q = q.where(ProductionSummary.product_cd == _normalize_product_cd(product_cd_filter))
    rows = list((await db.execute(q)).scalars().all())
    out: Dict[Tuple[str, date, str], dict] = {}
    names: Dict[str, str] = {}
    for row in rows:
        pcd = _normalize_product_cd(row.product_cd)
        if not pcd:
            continue
        d = _as_date(row.date)
        if not d:
            continue
        names[pcd] = str(row.product_name or pcd).strip()
        for proc_cd in process_cds:
            spec = COMPARISON_PROCESS_MAP[proc_cd]
            defect = int(getattr(row, spec["summary_defect_col"], None) or 0)
            scrap = int(getattr(row, spec["summary_scrap_col"], None) or 0)
            key = (pcd, d, proc_cd)
            prev = out.get(key)
            if prev:
                out[key] = {
                    "defect": int(prev.get("defect") or 0) + defect,
                    "scrap": int(prev.get("scrap") or 0) + scrap,
                }
            else:
                out[key] = {"defect": defect, "scrap": scrap}
    return out, names


async def _fetch_cutting_source(
    db: AsyncSession, start_d: date, end_d: date, product_cd_filter: Optional[str]
) -> Dict[Tuple[str, date], dict]:
    """切断製造不良 = cutting_production_indicator.quantity_variance"""
    sql = """
        SELECT product_cd, production_day,
               SUM(COALESCE(quantity_variance, 0)) AS defect_qty
        FROM cutting_production_indicator
        WHERE production_day >= :start_d AND production_day <= :end_d
        GROUP BY product_cd, production_day
    """
    result = await db.execute(text(sql), {"start_d": start_d, "end_d": end_d})
    out: Dict[Tuple[str, date], dict] = defaultdict(lambda: {"defect": 0, "scrap": 0})
    filter_norm = _normalize_product_cd(product_cd_filter) if product_cd_filter else None
    for row in result.fetchall():
        pcd = _normalize_product_cd(row[0])
        d = _as_date(row[1])
        if not pcd or not d:
            continue
        if filter_norm and pcd != filter_norm:
            continue
        out[(pcd, d)]["defect"] += int(row[2] or 0)
    return {k: {"defect": v["defect"], "scrap": 0} for k, v in out.items()}


async def _fetch_chamfering_source(
    db: AsyncSession, start_d: date, end_d: date, product_cd_filter: Optional[str]
) -> Dict[Tuple[str, date], dict]:
    """面取製造不良 = chamfer_defect_quantity + sw_defect_quantity（指標表のみ）。"""
    sql = """
        SELECT product_cd, production_day,
               SUM(COALESCE(chamfer_defect_quantity, 0) + COALESCE(sw_defect_quantity, 0)) AS defect_qty
        FROM chamfering_production_indicator
        WHERE production_day >= :start_d AND production_day <= :end_d
        GROUP BY product_cd, production_day
    """
    result = await db.execute(text(sql), {"start_d": start_d, "end_d": end_d})
    out: Dict[Tuple[str, date], dict] = defaultdict(lambda: {"defect": 0, "scrap": 0})
    filter_norm = _normalize_product_cd(product_cd_filter) if product_cd_filter else None
    for row in result.fetchall():
        pcd = _normalize_product_cd(row[0])
        d = _as_date(row[1])
        if not pcd or not d:
            continue
        if filter_norm and pcd != filter_norm:
            continue
        out[(pcd, d)]["defect"] += int(row[2] or 0)
    return {k: {"defect": v["defect"], "scrap": 0} for k, v in out.items()}


async def _fetch_forming_source(
    db: AsyncSession, start_d: date, end_d: date, product_cd_filter: Optional[str]
) -> Dict[Tuple[str, date], dict]:
    sql = """
        SELECT product_cd, production_day, SUM(COALESCE(defect_quantity, 0)) AS defect_qty
        FROM forming_production_indicator
        WHERE production_day >= :start_d AND production_day <= :end_d
        GROUP BY product_cd, production_day
    """
    result = await db.execute(text(sql), {"start_d": start_d, "end_d": end_d})
    out: Dict[Tuple[str, date], dict] = defaultdict(lambda: {"defect": 0, "scrap": 0})
    filter_norm = _normalize_product_cd(product_cd_filter) if product_cd_filter else None
    for row in result.fetchall():
        pcd = _normalize_product_cd(row[0])
        d = _as_date(row[1])
        if not pcd or not d:
            continue
        if filter_norm and pcd != filter_norm:
            continue
        out[(pcd, d)]["defect"] += int(row[2] or 0)
    return {k: {"defect": v["defect"], "scrap": 0} for k, v in out.items()}


async def _fetch_welding_source(
    db: AsyncSession, start_d: date, end_d: date, product_cd_filter: Optional[str]
) -> Dict[Tuple[str, date], dict]:
    sql = """
        SELECT product_cd, production_day, SUM(COALESCE(defect_qty, 0)) AS defect_qty
        FROM welding_management
        WHERE production_day >= :start_d AND production_day <= :end_d
        GROUP BY product_cd, production_day
    """
    result = await db.execute(text(sql), {"start_d": start_d, "end_d": end_d})
    out: Dict[Tuple[str, date], dict] = defaultdict(lambda: {"defect": 0, "scrap": 0})
    filter_norm = _normalize_product_cd(product_cd_filter) if product_cd_filter else None
    for row in result.fetchall():
        pcd = _normalize_product_cd(row[0])
        d = _as_date(row[1])
        if not pcd or not d:
            continue
        if filter_norm and pcd != filter_norm:
            continue
        out[(pcd, d)]["defect"] += int(row[2] or 0)
    return {k: {"defect": v["defect"], "scrap": 0} for k, v in out.items()}


async def _fetch_inspection_source(
    db: AsyncSession,
    start_d: date,
    end_d: date,
    product_cd_filter: Optional[str],
    scrap_keys: Set[str],
) -> Dict[Tuple[str, date], dict]:
    sql = """
        SELECT product_cd, production_day, defect_qty, mes_defect_by_item
        FROM inspection_management
        WHERE production_day >= :start_d AND production_day <= :end_d
    """
    result = await db.execute(text(sql), {"start_d": start_d, "end_d": end_d})
    out: Dict[Tuple[str, date], dict] = defaultdict(lambda: {"defect": 0, "scrap": 0})
    filter_norm = _normalize_product_cd(product_cd_filter) if product_cd_filter else None
    for row in result.fetchall():
        pcd = _normalize_product_cd(row[0])
        d = _as_date(row[1])
        if not pcd or not d:
            continue
        if filter_norm and pcd != filter_norm:
            continue
        out[(pcd, d)]["defect"] += int(row[2] or 0)
        out[(pcd, d)]["scrap"] += _extract_inspection_scrap_qty(row[3], scrap_keys)
    return {k: {"defect": v["defect"], "scrap": v["scrap"]} for k, v in out.items()}


async def _fetch_plating_daily_source(
    db: AsyncSession, start_d: date, end_d: date
) -> Dict[date, dict]:
    sql = """
        SELECT production_day,
               SUM(COALESCE(defect_quantity, 0)) AS defect_qty
        FROM plating_production_indicator
        WHERE production_day >= :start_d AND production_day <= :end_d
        GROUP BY production_day
    """
    result = await db.execute(text(sql), {"start_d": start_d, "end_d": end_d})
    out: Dict[date, dict] = {}
    for row in result.fetchall():
        d = row[0]
        if not d:
            continue
        out[d] = {"defect": int(row[1] or 0), "scrap": None}
    return out


async def _fetch_all_source_maps(
    db: AsyncSession,
    start_d: date,
    end_d: date,
    product_cd_filter: Optional[str],
    process_cds: List[str],
    scrap_keys: Set[str],
) -> Tuple[Dict[str, Dict[Tuple[str, date], dict]], Dict[date, dict]]:
    """process_cd -> (product_cd, date) -> {defect, scrap}; plating daily map"""
    source_by_proc: Dict[str, Dict[Tuple[str, date], dict]] = {}
    plating_daily: Dict[date, dict] = {}
    for proc_cd in process_cds:
        spec = COMPARISON_PROCESS_MAP[proc_cd]
        st = spec["source_type"]
        if st == "none":
            source_by_proc[proc_cd] = {}
        elif st == "cutting":
            source_by_proc[proc_cd] = await _fetch_cutting_source(db, start_d, end_d, product_cd_filter)
        elif st == "chamfering":
            source_by_proc[proc_cd] = await _fetch_chamfering_source(db, start_d, end_d, product_cd_filter)
        elif st == "forming":
            source_by_proc[proc_cd] = await _fetch_forming_source(db, start_d, end_d, product_cd_filter)
        elif st == "welding":
            source_by_proc[proc_cd] = await _fetch_welding_source(db, start_d, end_d, product_cd_filter)
        elif st == "inspection":
            source_by_proc[proc_cd] = await _fetch_inspection_source(
                db, start_d, end_d, product_cd_filter, scrap_keys
            )
        elif st == "plating_daily":
            source_by_proc[proc_cd] = {}
            plating_daily = await _fetch_plating_daily_source(db, start_d, end_d)
    return source_by_proc, plating_daily


def _build_detail_rows(
    summary_map: Dict[Tuple[str, date, str], dict],
    source_by_proc: Dict[str, Dict[Tuple[str, date], dict]],
    names: Dict[str, str],
    process_cds: List[str],
    proc_names: Dict[str, str],
    only_diff: bool,
) -> List[dict]:
    # メッキ(KT05)は品番別突合せず、plating_daily のみ
    product_process_cds = [
        pc for pc in process_cds if COMPARISON_PROCESS_MAP[pc]["source_type"] != "plating_daily"
    ]

    all_keys: Set[Tuple[str, date, str]] = {
        (pcd, d, pc) for (pcd, d, pc) in summary_map.keys() if pc in product_process_cds
    }
    for proc_cd in product_process_cds:
        spec = COMPARISON_PROCESS_MAP[proc_cd]
        if spec["source_type"] == "none":
            continue
        for pcd, d in source_by_proc.get(proc_cd, {}):
            all_keys.add((pcd, d, proc_cd))

    detail_rows: List[dict] = []
    for pcd, d, proc_cd in sorted(all_keys, key=lambda x: (x[2], str(x[1]), x[0])):
        spec = COMPARISON_PROCESS_MAP[proc_cd]
        summary_vals = summary_map.get((pcd, d, proc_cd), {"defect": 0, "scrap": 0})
        summary_defect = int(summary_vals.get("defect") or 0)
        summary_scrap = int(summary_vals.get("scrap") or 0)

        comparable = spec["source_type"] not in ("none",)
        scrap_comparable = spec["source_type"] == "inspection"

        source_defect: Optional[int] = None
        source_scrap: Optional[int] = None
        if spec["source_type"] == "none":
            source_defect = None
            source_scrap = None
        else:
            src = source_by_proc.get(proc_cd, {}).get((pcd, d), {"defect": 0, "scrap": None})
            source_defect = int(src.get("defect") or 0)
            # 製造側に廃棄列がない工程は 0 として合算（不良+廃棄で一度突合）
            source_scrap = int(src.get("scrap") or 0) if scrap_comparable else 0

        summary_total = int(summary_defect) + int(summary_scrap)
        source_total = _combined_qty(source_defect, source_scrap)
        total_diff = (source_total - summary_total) if source_total is not None else None

        status = _comparison_status(
            summary_defect,
            source_defect,
            summary_scrap,
            source_scrap,
            comparable=comparable,
        )

        if only_diff and status == "match":
            continue
        if only_diff and status == "not_comparable" and summary_total == 0:
            continue

        detail_rows.append(
            {
                "product_cd": pcd,
                "product_name": names.get(pcd, pcd),
                "production_day": str(d),
                "process_cd": proc_cd,
                "process_name": proc_names.get(proc_cd, spec["process_name"]),
                "summary_total": summary_total,
                "source_total": source_total,
                "total_diff": total_diff,
                "summary_defect": summary_defect,
                "source_defect": source_defect,
                "summary_scrap": summary_scrap,
                "source_scrap": source_scrap if scrap_comparable else None,
                "status": status,
                "source_note": spec.get("source_note"),
            }
        )
    return detail_rows


def _build_plating_daily_rows(
    summary_map: Dict[Tuple[str, date, str], dict],
    plating_daily_source: Dict[date, dict],
    only_diff: bool,
) -> List[dict]:
    """メッキ：日次合計での突合（品番横断）。"""
    summary_by_day: Dict[date, dict] = defaultdict(lambda: {"defect": 0, "scrap": 0})
    proc_cd = "KT05"
    for (pcd, d, pc), vals in summary_map.items():
        if pc != proc_cd:
            continue
        summary_by_day[d]["defect"] += int(vals.get("defect") or 0)
        summary_by_day[d]["scrap"] += int(vals.get("scrap") or 0)

    all_days = set(summary_by_day.keys()) | set(plating_daily_source.keys())
    rows: List[dict] = []
    for d in sorted(all_days):
        s_def = int(summary_by_day.get(d, {}).get("defect") or 0)
        s_scr = int(summary_by_day.get(d, {}).get("scrap") or 0)
        src = plating_daily_source.get(d, {"defect": 0, "scrap": None})
        src_def = int(src.get("defect") or 0)
        summary_total = s_def + s_scr
        source_total = src_def  # 製造側廃棄なし → 不良のみで合算（廃棄=0）
        total_diff = source_total - summary_total
        status = _comparison_status(
            s_def,
            src_def,
            s_scr,
            0,
            comparable=True,
        )
        if only_diff and status == "match":
            continue
        rows.append(
            {
                "production_day": str(d),
                "summary_total": summary_total,
                "source_total": source_total,
                "total_diff": total_diff,
                "summary_defect": s_def,
                "source_defect": src_def,
                "summary_scrap": s_scr,
                "source_scrap": None,
                "status": status,
            }
        )
    return rows


def _compute_kpi(detail_rows: List[dict]) -> dict:
    comparable_rows = [r for r in detail_rows if r.get("status") not in ("not_comparable", "plating_daily_only")]
    summary_total = sum(int(r.get("summary_total") or 0) for r in comparable_rows)
    source_total = sum(int(r.get("source_total") or 0) for r in comparable_rows if r.get("source_total") is not None)
    matched_count, mismatch_count, only_summary_count, only_source_count, _ = _row_match_counts(
        comparable_rows
    )
    not_comparable_count = sum(1 for r in detail_rows if r.get("status") == "not_comparable")
    item_count = len(comparable_rows)
    # KPI 一致率は数量ベース（画面の合計値と直感が一致）
    match_rate = _qty_match_rate(summary_total, source_total)
    return {
        "summary_total": summary_total,
        "source_total": source_total,
        "total_diff": source_total - summary_total,
        # 後方互換（内訳）
        "summary_defect_total": sum(int(r.get("summary_defect") or 0) for r in comparable_rows),
        "source_defect_total": sum(
            int(r.get("source_defect") or 0) for r in comparable_rows if r.get("source_defect") is not None
        ),
        "summary_scrap_total": sum(int(r.get("summary_scrap") or 0) for r in comparable_rows),
        "source_scrap_total": sum(
            int(r.get("source_scrap") or 0) for r in comparable_rows if r.get("source_scrap") is not None
        ),
        "item_count": item_count,
        "matched_count": matched_count,
        "mismatch_count": mismatch_count,
        "only_summary_count": only_summary_count,
        "only_source_count": only_source_count,
        "not_comparable_count": not_comparable_count,
        "match_rate": match_rate,
    }


def _build_summary_rows(
    detail_rows: List[dict],
    process_cds: List[str],
    proc_names: Dict[str, str],
    *,
    plating_daily_rows: Optional[List[dict]] = None,
    summary_map: Optional[Dict[Tuple[str, date, str], dict]] = None,
    only_diff: bool = False,
) -> List[dict]:
    """
    全対象工程を工程別サマリに載せる。
    - メッキ: 日次合計を期間合算して1行
    - 製造側データなしの工程: 製造=0
    """
    by_proc: Dict[str, List[dict]] = defaultdict(list)
    for row in detail_rows:
        by_proc[str(row.get("process_cd") or "")].append(row)

    plating_daily_rows = plating_daily_rows or []
    summary_map = summary_map or {}

    summary: List[dict] = []
    for proc_cd in process_cds:
        spec = COMPARISON_PROCESS_MAP[proc_cd]
        process_name = proc_names.get(proc_cd, spec["process_name"])

        if spec["source_type"] == "plating_daily":
            s_total = sum(int(r.get("summary_total") or 0) for r in plating_daily_rows)
            src_total = sum(int(r.get("source_total") or 0) for r in plating_daily_rows)
            item_count = len(plating_daily_rows)
            matched, mismatch, only_summary, only_source, _ = _row_match_counts(plating_daily_rows)
            note = "日次合計（品番なし）"
        elif spec["source_type"] == "none":
            # 切断など：製造側なし → 製造=0、生産管理は detail / summary_map から合算
            rows = by_proc.get(proc_cd, [])
            if rows:
                s_total = sum(int(r.get("summary_total") or 0) for r in rows)
                item_count = len(rows)
            else:
                s_total = 0
                item_count = 0
                for (_pcd, _d, pc), vals in summary_map.items():
                    if pc != proc_cd:
                        continue
                    s_total += int(vals.get("defect") or 0) + int(vals.get("scrap") or 0)
                    item_count += 1
            src_total = 0
            if s_total == 0:
                matched, mismatch, only_summary, only_source = 0, 0, 0, 0
            else:
                matched, mismatch, only_summary, only_source = 0, 0, item_count, 0
            note = spec.get("source_note") or "製造側なし（0扱い）"
        else:
            rows = by_proc.get(proc_cd, [])
            s_total = sum(int(r.get("summary_total") or 0) for r in rows)
            src_total = sum(int(r.get("source_total") or 0) for r in rows if r.get("source_total") is not None)
            matched, mismatch, only_summary, only_source, _ = _row_match_counts(rows)
            item_count = len(rows)
            note = spec.get("source_note")

        total_diff = src_total - s_total
        if only_diff and total_diff == 0 and s_total == 0 and src_total == 0:
            continue
        if only_diff and total_diff == 0:
            continue

        # 工程別一致率も数量ベース（合計同士の近さ）
        match_rate = _qty_match_rate(s_total, src_total)
        summary.append(
            {
                "process_cd": proc_cd,
                "process_name": process_name,
                "summary_total": s_total,
                "source_total": src_total,
                "total_diff": total_diff,
                "item_count": item_count,
                "matched_count": matched,
                "mismatch_count": mismatch,
                "only_summary_count": only_summary,
                "only_source_count": only_source,
                "match_rate": match_rate,
                "source_note": note,
            }
        )
    return summary


def _compute_kpi_from_summary(summary_rows: List[dict]) -> dict:
    """工程別サマリから KPI を算出（メッキ・切断含む全工程）。"""
    summary_total = sum(int(r.get("summary_total") or 0) for r in summary_rows)
    source_total = sum(int(r.get("source_total") or 0) for r in summary_rows)
    item_count = sum(int(r.get("item_count") or 0) for r in summary_rows)
    matched_count = sum(int(r.get("matched_count") or 0) for r in summary_rows)
    mismatch_count = sum(int(r.get("mismatch_count") or 0) for r in summary_rows)
    only_summary_count = sum(int(r.get("only_summary_count") or 0) for r in summary_rows)
    only_source_count = sum(int(r.get("only_source_count") or 0) for r in summary_rows)
    match_rate = _qty_match_rate(summary_total, source_total)
    return {
        "summary_total": summary_total,
        "source_total": source_total,
        "total_diff": source_total - summary_total,
        "item_count": item_count,
        "matched_count": matched_count,
        "mismatch_count": mismatch_count,
        "only_summary_count": only_summary_count,
        "only_source_count": only_source_count,
        "not_comparable_count": 0,
        "match_rate": match_rate,
    }


def _iter_month_starts(start_d: date, end_d: date) -> List[date]:
    """期間内の各月の1日を返す（start〜end を含む）。"""
    months: List[date] = []
    y, m = start_d.year, start_d.month
    end_ym = (end_d.year, end_d.month)
    while (y, m) <= end_ym:
        months.append(date(y, m, 1))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return months


def _filter_rows_by_ym(rows: List[dict], ym: str) -> List[dict]:
    prefix = f"{ym}-"
    return [r for r in rows if str(r.get("production_day") or "").startswith(prefix)]


def _build_monthly_trend_rows(
    detail_rows_full: List[dict],
    plating_daily_rows: List[dict],
    summary_map: Dict[Tuple[str, date, str], dict],
    process_cds: List[str],
    proc_names: Dict[str, str],
    start_d: date,
    end_d: date,
) -> List[dict]:
    """月次の生産管理 / 製造 / 差異 / 一致率を返す（折線グラフ用）。"""
    out: List[dict] = []
    for month_start in _iter_month_starts(start_d, end_d):
        ym = month_start.strftime("%Y-%m")
        detail_m = _filter_rows_by_ym(detail_rows_full, ym)
        plating_m = _filter_rows_by_ym(plating_daily_rows, ym)
        summary_map_m = {
            k: v for k, v in summary_map.items() if k[1].year == month_start.year and k[1].month == month_start.month
        }
        summary_rows = _build_summary_rows(
            detail_m,
            process_cds,
            proc_names,
            plating_daily_rows=plating_m,
            summary_map=summary_map_m,
            only_diff=False,
        )
        kpi = _compute_kpi_from_summary(summary_rows)
        out.append(
            {
                "year_month": ym,
                "label": f"{month_start.month}月",
                "summary_total": kpi["summary_total"],
                "source_total": kpi["source_total"],
                "total_diff": kpi["total_diff"],
                "match_rate": kpi["match_rate"],
                "item_count": kpi["item_count"],
                "mismatch_count": kpi["mismatch_count"],
            }
        )
    return out


@router.get("")
async def get_defect_scrap_comparison(
    startDate: str = Query(..., description="開始日 YYYY-MM-DD"),
    endDate: str = Query(..., description="終了日 YYYY-MM-DD"),
    processCd: Optional[str] = Query(None, description="工程CD（省略時は全対象工程）"),
    productCd: Optional[str] = Query(None, description="製品CD（完全一致）"),
    onlyDiff: bool = Query(False, description="差異のみ"),
    view: str = Query("summary", description="summary | detail | monthly"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    sort_by: str = Query("total_diff"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_inventory_operation("edit")),
):
    """
    生産管理 vs 製造：不良・廃棄合算データ突合。
    粒度：品番 × 日期 × 工程（メッキは日次合算して工程別サマリに反映）。
    view=monthly 時は月次系列（折線グラフ用）を返す。
    """
    start_d = _parse_date_param(startDate, "startDate")
    end_d = _parse_date_param(endDate, "endDate")
    if start_d > end_d:
        raise HTTPException(status_code=422, detail="startDate は endDate 以前である必要があります")

    view_norm = (view or "summary").strip().lower()
    if view_norm not in ("summary", "detail", "monthly"):
        raise HTTPException(
            status_code=422, detail="view は summary / detail / monthly を指定してください"
        )

    if view_norm == "monthly":
        month_count = len(_iter_month_starts(start_d, end_d))
        if month_count > 12:
            raise HTTPException(status_code=422, detail="月次トレンドは最大12ヶ月までです")

    proc_filter = (processCd or "").strip() or None
    if proc_filter and proc_filter.lower() == "all":
        proc_filter = None
    process_cds = [proc_filter] if proc_filter else list(COMPARISON_PROCESS_CDS)
    for pc in process_cds:
        if pc not in COMPARISON_PROCESS_MAP:
            raise HTTPException(status_code=422, detail=f"未対応の工程CD: {pc}")

    product_cd_filter = (productCd or "").strip() or None
    scrap_keys = await _load_inspection_scrap_keys(db)
    proc_names = await _load_process_names(db, process_cds)

    summary_map, names = await _fetch_summary_maps(db, start_d, end_d, product_cd_filter, process_cds)
    source_by_proc, plating_daily_source = await _fetch_all_source_maps(
        db, start_d, end_d, product_cd_filter, process_cds, scrap_keys
    )

    detail_rows_full = _build_detail_rows(
        summary_map, source_by_proc, names, process_cds, proc_names, False
    )
    plating_daily_rows: List[dict] = []
    if "KT05" in process_cds:
        # メッキ日次合計は品番フィルターを無視（製造側に品番がないため全日合計で突合）
        if product_cd_filter:
            summary_map_plating, _ = await _fetch_summary_maps(db, start_d, end_d, None, ["KT05"])
        else:
            summary_map_plating = summary_map
        plating_daily_rows = _build_plating_daily_rows(summary_map_plating, plating_daily_source, False)

    if view_norm == "monthly":
        monthly_rows = _build_monthly_trend_rows(
            detail_rows_full,
            plating_daily_rows,
            summary_map,
            process_cds,
            proc_names,
            start_d,
            end_d,
        )
        return {
            "success": True,
            "data": {
                "start_date": str(start_d),
                "end_date": str(end_d),
                "view": "monthly",
                "list": monthly_rows,
                "plating_daily": [],
                "kpi": _compute_kpi_from_summary(
                    _build_summary_rows(
                        detail_rows_full,
                        process_cds,
                        proc_names,
                        plating_daily_rows=plating_daily_rows,
                        summary_map=summary_map,
                        only_diff=False,
                    )
                ),
            },
        }

    # 工程別サマリは常に全工程。KPI は全工程合算。onlyDiff 時は差異行のみ返す。
    summary_rows_all = _build_summary_rows(
        detail_rows_full,
        process_cds,
        proc_names,
        plating_daily_rows=plating_daily_rows,
        summary_map=summary_map,
        only_diff=False,
    )
    kpi = _compute_kpi_from_summary(summary_rows_all)
    summary_rows = (
        [r for r in summary_rows_all if int(r.get("total_diff") or 0) != 0]
        if onlyDiff
        else summary_rows_all
    )

    if view_norm == "detail":
        detail_rows = (
            [r for r in detail_rows_full if r.get("status") not in ("match",)]
            if onlyDiff
            else detail_rows_full
        )
        # onlyDiff: 突合不可で両方0の行は除外（ノイズ低減）
        if onlyDiff:
            detail_rows = [
                r
                for r in detail_rows
                if not (
                    r.get("status") == "not_comparable"
                    and int(r.get("summary_total") or 0) == 0
                )
            ]
        desc_order = str(sort_order).strip().lower() == "desc"
        detail_rows.sort(key=lambda r: _detail_sort_key(r, sort_by), reverse=desc_order)
        total = len(detail_rows)
        start_idx = (page - 1) * limit
        page_rows = detail_rows[start_idx : start_idx + limit]
        return {
            "success": True,
            "data": {
                "start_date": str(start_d),
                "end_date": str(end_d),
                "view": "detail",
                "list": page_rows,
                "plating_daily": [],
                "total": total,
                "page": page,
                "limit": limit,
                "kpi": kpi,
            },
        }

    return {
        "success": True,
        "data": {
            "start_date": str(start_d),
            "end_date": str(end_d),
            "view": "summary",
            "list": summary_rows,
            "plating_daily": [],
            "kpi": kpi,
        },
    }

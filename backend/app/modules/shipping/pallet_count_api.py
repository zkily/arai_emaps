"""
出荷パレット数管理 API
- GET /pallet-count: グループ別カード用・日付×納入先の二次元集計（同一 shipping_no = 1 パレット）
- PUT /pallet-count/advance-tohoku: オワリ便「先出(東北)」保存
- PUT /pallet-count/bin2: オワリ便「2便」保存
- PUT /pallet-count/cell-override: セル手動修正（ダブルクリック編集）
- POST /pallet-count/send-mail: グループ表をメール送信
"""
from __future__ import annotations

import html as html_lib
import json
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.company_work_calendar import (
    is_scheduled_workday,
    load_company_calendar_sets,
)
from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.services.email_service import load_smtp_config, send_bulk_html_email

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_PAGE_KEY = "destination_groups_list"
OWARI_GROUP_KEYWORD = "オワリ"


def _parse_group_destinations(raw: Any) -> List[dict]:
    """destination_groups.destinations JSON → [{cd, name}, ...]"""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    if not isinstance(raw, list):
        return []
    out: List[dict] = []
    seen = set()
    for item in raw:
        if isinstance(item, dict):
            cd = str(item.get("value") or item.get("destination_cd") or "").strip()
            if not cd or cd in seen:
                continue
            label = str(item.get("label") or item.get("name") or item.get("destination_name") or cd)
            name = label
            if " - " in label:
                name = label.split(" - ", 1)[1].strip() or label
            elif " " in label and label.startswith(cd):
                name = label[len(cd) :].strip() or label
            seen.add(cd)
            out.append({"cd": cd, "name": name})
        elif isinstance(item, str) and item.strip():
            cd = item.strip()
            if cd not in seen:
                seen.add(cd)
                out.append({"cd": cd, "name": cd})
    return out


def _parse_ymd(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _date_range_list(start: date, end: date) -> List[str]:
    if end < start:
        start, end = end, start
    out: List[str] = []
    cur = start
    for _ in range(800):
        out.append(cur.isoformat())
        if cur >= end:
            break
        cur += timedelta(days=1)
    return out


def _safe_date_str(val: Any) -> str:
    if val is None:
        return ""
    if hasattr(val, "isoformat"):
        return val.isoformat()[:10]
    return str(val)[:10]


def _is_owari_group(name: str) -> bool:
    return OWARI_GROUP_KEYWORD in (name or "")


def _find_tohoku_dest_cd(destinations: List[dict]) -> Optional[str]:
    """(株)東北INOAC小牛田 に該当する納入先CDを特定"""
    for d in destinations:
        name = d.get("name") or ""
        compact = name.replace("（", "(").replace("）", ")").replace(" ", "")
        if "小牛田" in compact or "東北INOAC小牛田" in compact or "東北イノアック小牛田" in compact:
            return d["cd"]
    for d in destinations:
        name = d.get("name") or ""
        compact = name.replace(" ", "")
        if "東北INOAC" in compact or "東北イノアック" in compact:
            return d["cd"]
    for d in destinations:
        if str(d.get("cd") or "").upper() == "N05":
            return d["cd"]
    return None


async def _load_advance_map(
    db: AsyncSession, start: date, end: date
) -> Dict[str, int]:
    """advance_date(ISO) -> qty"""
    q = text(
        """
        SELECT advance_date, qty
        FROM shipping_pallet_advance_tohoku
        WHERE advance_date BETWEEN :start_date AND :end_date
        """
    )
    try:
        result = await db.execute(
            q, {"start_date": start.isoformat(), "end_date": end.isoformat()}
        )
    except Exception as e:
        logger.warning("shipping_pallet_advance_tohoku 読取失敗: %s", e)
        return {}
    out: Dict[str, int] = {}
    for row in result.mappings().all():
        ds = _safe_date_str(row["advance_date"])
        if ds:
            out[ds] = int(row["qty"] or 0)
    return out


async def _load_bin2_map(db: AsyncSession, start: date, end: date) -> Dict[str, int]:
    """shipping_date(ISO) -> qty（2便）"""
    q = text(
        """
        SELECT shipping_date, qty
        FROM shipping_pallet_bin2
        WHERE shipping_date BETWEEN :start_date AND :end_date
        """
    )
    try:
        result = await db.execute(
            q, {"start_date": start.isoformat(), "end_date": end.isoformat()}
        )
    except Exception as e:
        logger.warning("shipping_pallet_bin2 読取失敗: %s", e)
        return {}
    out: Dict[str, int] = {}
    for row in result.mappings().all():
        ds = _safe_date_str(row["shipping_date"])
        if ds:
            out[ds] = int(row["qty"] or 0)
    return out


async def _load_cell_overrides(
    db: AsyncSession, start: date, end: date
) -> Dict[Tuple[str, str], int]:
    """(shipping_date, destination_cd) -> qty"""
    q = text(
        """
        SELECT shipping_date, destination_cd, qty
        FROM shipping_pallet_count_overrides
        WHERE shipping_date BETWEEN :start_date AND :end_date
        """
    )
    try:
        result = await db.execute(
            q, {"start_date": start.isoformat(), "end_date": end.isoformat()}
        )
    except Exception as e:
        logger.warning("shipping_pallet_count_overrides 読取失敗: %s", e)
        return {}
    out: Dict[Tuple[str, str], int] = {}
    for row in result.mappings().all():
        ds = _safe_date_str(row["shipping_date"])
        cd = str(row["destination_cd"] or "").strip()
        if ds and cd:
            out[(ds, cd)] = int(row["qty"] or 0)
    return out


def _recalc_totals(
    matrix: Dict[str, Dict[str, int]],
    dest_cds: List[str],
    dates: List[str],
) -> Tuple[Dict[str, int], Dict[str, int], int]:
    row_totals: Dict[str, int] = {}
    col_totals: Dict[str, int] = {cd: 0 for cd in dest_cds}
    grand = 0
    for ds in dates:
        row = matrix.get(ds) or {}
        row_sum = 0
        for cd in dest_cds:
            v = int(row.get(cd, 0) or 0)
            row_sum += v
            col_totals[cd] = col_totals.get(cd, 0) + v
        row_totals[ds] = row_sum
        grand += row_sum
    return row_totals, col_totals, grand


def _apply_cell_overrides(
    *,
    matrix: Dict[str, Dict[str, int]],
    dest_cds: List[str],
    dates: List[str],
    overrides: Dict[Tuple[str, str], int],
) -> Dict[str, Dict[str, int]]:
    """手動修正を最終表示値として適用。戻り値: date -> {dest_cd: qty}"""
    applied: Dict[str, Dict[str, int]] = {}
    dest_set = set(dest_cds)
    date_set = set(dates)
    for (ds, cd), qty in overrides.items():
        if ds not in date_set or cd not in dest_set:
            continue
        if ds not in matrix:
            matrix[ds] = {c: 0 for c in dest_cds}
        matrix[ds][cd] = max(0, int(qty))
        applied.setdefault(ds, {})[cd] = max(0, int(qty))
    return applied


async def _next_workday_map(
    db: AsyncSession, advance_dates: List[date]
) -> Dict[str, str]:
    """advance_date ISO -> next workday ISO"""
    if not advance_dates:
        return {}
    min_d = min(advance_dates)
    max_d = max(advance_dates) + timedelta(days=21)
    scheduled, off = await load_company_calendar_sets(db, min_d, max_d)
    empty: Set[str] = set()
    mapping: Dict[str, str] = {}
    for ad in advance_dates:
        found: Optional[date] = None
        for i in range(1, 22):
            cand = ad + timedelta(days=i)
            if is_scheduled_workday(
                cand,
                company_scheduled=scheduled,
                company_off=off,
                extra_workdays=empty,
                extra_holidays=empty,
            ):
                found = cand
                break
        if found:
            mapping[ad.isoformat()] = found.isoformat()
    return mapping


def _apply_tohoku_advance(
    *,
    matrix: Dict[str, Dict[str, int]],
    row_totals: Dict[str, int],
    col_totals: Dict[str, int],
    tohoku_cd: str,
    advance_by_date: Dict[str, int],
    next_workday_of: Dict[str, str],
    display_dates: List[str],
) -> Tuple[Dict[str, int], int]:
    """翌稼働日の東北列から先出数を減算。戻り値: (deduct_by_display_date, advance_total_in_range)"""
    deduct_by_day: Dict[str, int] = {}
    advance_total = 0
    display_set = set(display_dates)

    for adv_ds, qty in advance_by_date.items():
        if qty <= 0:
            continue
        if adv_ds in display_set:
            advance_total += qty
        next_ds = next_workday_of.get(adv_ds)
        if not next_ds or next_ds not in display_set:
            continue
        deduct_by_day[next_ds] = deduct_by_day.get(next_ds, 0) + qty

    for ds, deduct in deduct_by_day.items():
        row = matrix.get(ds)
        if not row or tohoku_cd not in row:
            continue
        original = int(row.get(tohoku_cd) or 0)
        new_val = max(0, original - deduct)
        delta = original - new_val
        row[tohoku_cd] = new_val
        row_totals[ds] = max(0, int(row_totals.get(ds, 0) - delta))
        col_totals[tohoku_cd] = max(0, int(col_totals.get(tohoku_cd, 0) - delta))

    return deduct_by_day, advance_total


class AdvanceTohokuBody(BaseModel):
    advance_date: str = Field(..., description="積込日 YYYY-MM-DD")
    qty: int = Field(0, ge=0, le=99999, description="先出パレット数")


class Bin2Body(BaseModel):
    shipping_date: str = Field(..., description="積込日 YYYY-MM-DD")
    qty: int = Field(0, ge=0, le=1, description="2便フラグ（1=あり / 0=なし）")


class SendMailBody(BaseModel):
    start_date: str
    end_date: str
    group_name: str
    to_emails: List[str] = Field(..., min_length=1)
    subject: Optional[str] = None
    page_key: Optional[str] = DEFAULT_PAGE_KEY

    @field_validator("to_emails")
    @classmethod
    def _normalize_emails(cls, v: List[str]) -> List[str]:
        email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        out: List[str] = []
        seen: Set[str] = set()
        for raw in v:
            e = (raw or "").strip()
            if not e:
                continue
            if not email_re.match(e):
                raise ValueError(f"メールアドレス形式が不正です: {e}")
            key = e.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(e)
        if not out:
            raise ValueError("送信先メールを1件以上指定してください")
        return out


class CellOverrideBody(BaseModel):
    shipping_date: str = Field(..., description="積込日 YYYY-MM-DD")
    destination_cd: str = Field(..., min_length=1, max_length=32, description="納入先CD")
    qty: Optional[int] = Field(
        None,
        ge=0,
        le=99999,
        description="手動パレット数。null の場合は手動修正を削除して自動集計に戻す",
    )
    clear: bool = Field(False, description="true の場合は手動修正を削除")


WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]
TOHOKU_FALLBACK_CD = "N05"


def _fmt_md_weekday(d: date) -> str:
    return f"{d.month}/{d.day} ({WEEKDAY_JA[d.weekday()]})"


def _fmt_month_day_ja(d: date) -> str:
    return f"{d.month}月{d.day}日"


async def _resolve_tohoku_destination(db: AsyncSession) -> Tuple[str, str, int]:
    """N05 / 東北INOAC小牛田 の (cd, name, delivery_lead_time) を解決"""
    q = text(
        """
        SELECT destination_cd, destination_name, COALESCE(delivery_lead_time, 0) AS lead_time
        FROM destinations
        WHERE status = 1
          AND (
            destination_cd = :n05
            OR destination_name LIKE :kw1
            OR destination_name LIKE :kw2
            OR destination_name LIKE :kw3
          )
        ORDER BY
          CASE WHEN destination_cd = :n05 THEN 0 ELSE 1 END,
          CASE WHEN destination_name LIKE '%小牛田%' THEN 0 ELSE 1 END,
          destination_cd
        LIMIT 1
        """
    )
    result = await db.execute(
        q,
        {
            "n05": TOHOKU_FALLBACK_CD,
            "kw1": "%東北INOAC小牛田%",
            "kw2": "%東北イノアック小牛田%",
            "kw3": "%小牛田%",
        },
    )
    row = result.mappings().first()
    if row:
        return (
            str(row["destination_cd"]),
            str(row["destination_name"] or "(株)東北INOAC小牛田"),
            int(row["lead_time"] or 0),
        )
    return TOHOKU_FALLBACK_CD, "(株)東北INOAC小牛田", 0


@router.get("/advance-print")
async def get_advance_print_sheets(
    start_date: Optional[str] = Query(None, description="積込月 開始"),
    end_date: Optional[str] = Query(None, description="積込月 終了"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """先出(東北)がある日付について、数量分の A5 印刷シートデータを返す。
    - 先出日 = 入力行の積込日
    - 出荷日/出荷分 = 会社カレンダー翌稼働日
    - 納入日 = N05 の納入先営業日 + delivery_lead_time
    """
    d_start = _parse_ymd(start_date) or date.today().replace(day=1)
    d_end = _parse_ymd(end_date) or d_start
    if d_end < d_start:
        d_start, d_end = d_end, d_start

    advance_by_date = await _load_advance_map(db, d_start, d_end)
    advance_items = [
        (_parse_ymd(ds), qty)
        for ds, qty in sorted(advance_by_date.items())
        if qty > 0 and _parse_ymd(ds) is not None
    ]
    advance_dates = [d for d, _ in advance_items if d is not None]
    if not advance_dates:
        return {"success": True, "data": {"sheets": [], "total_sheets": 0}}

    next_map = await _next_workday_map(db, advance_dates)
    dest_cd, dest_name, lead_time = await _resolve_tohoku_destination(db)

    # 納入日計算用の営業日キャッシュ（出荷日〜十分な余白）
    ship_dates: List[date] = []
    for ad in advance_dates:
        ns = next_map.get(ad.isoformat())
        nd = _parse_ymd(ns) if ns else None
        if nd:
            ship_dates.append(nd)
    if not ship_dates:
        return {"success": True, "data": {"sheets": [], "total_sheets": 0}}

    cache_start = min(ship_dates)
    cache_end = max(ship_dates) + timedelta(days=max(30, lead_time * 3 + 14))
    from app.modules.order.generate_daily_service import build_working_days_cache

    workdays_cache = await build_working_days_cache(
        db, start_date=cache_start, end_date=cache_end, destination_cds=[dest_cd]
    )
    dest_workdays = workdays_cache.get(dest_cd) or []
    work_index = {d: i for i, d in enumerate(dest_workdays)}

    sheets: List[dict] = []
    for adv_d, qty in advance_items:
        if adv_d is None:
            continue
        ship_iso = next_map.get(adv_d.isoformat())
        ship_d = _parse_ymd(ship_iso)
        if not ship_d:
            continue

        # 納入日 = 出荷日の納入先営業日 index + lead_time
        idx = work_index.get(ship_d)
        if idx is None:
            # 出荷日が納入先休日の場合は直後の営業日から
            delivery_d = ship_d
            for cand in dest_workdays:
                if cand >= ship_d:
                    delivery_d = cand
                    idx = work_index.get(cand)
                    break
            if idx is not None:
                delivery_idx = idx + lead_time
                if 0 <= delivery_idx < len(dest_workdays):
                    delivery_d = dest_workdays[delivery_idx]
        else:
            delivery_idx = idx + lead_time
            if 0 <= delivery_idx < len(dest_workdays):
                delivery_d = dest_workdays[delivery_idx]
            else:
                delivery_d = dest_workdays[-1] if dest_workdays else ship_d

        sheet_base = {
            "advance_date": adv_d.isoformat(),
            "shipping_date": ship_d.isoformat(),
            "delivery_date": delivery_d.isoformat(),
            "destination_cd": dest_cd,
            "destination_name": dest_name,
            "advance_label": f"{_fmt_month_day_ja(adv_d)} 先出",
            "shipping_portion_label": f"{_fmt_month_day_ja(ship_d)} 出荷分",
            "shipping_date_label": _fmt_md_weekday(ship_d),
            "delivery_date_label": _fmt_md_weekday(delivery_d),
            "qty": int(qty),
        }
        for copy_i in range(int(qty)):
            sheets.append({**sheet_base, "copy_index": copy_i + 1})

    return {
        "success": True,
        "data": {
            "destination_cd": dest_cd,
            "destination_name": dest_name,
            "lead_time": lead_time,
            "sheets": sheets,
            "total_sheets": len(sheets),
        },
    }


@router.put("/advance-tohoku")
async def upsert_advance_tohoku(
    body: AdvanceTohokuBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """オワリ便「先出(東北)」を保存（同一積込日は上書き）"""
    d = _parse_ymd(body.advance_date)
    if not d:
        raise HTTPException(status_code=400, detail="advance_date が不正です")
    qty = int(body.qty or 0)
    updater = getattr(current_user, "username", None) or str(
        getattr(current_user, "id", "") or ""
    )

    if qty <= 0:
        await db.execute(
            text("DELETE FROM shipping_pallet_advance_tohoku WHERE advance_date = :d"),
            {"d": d.isoformat()},
        )
    else:
        await db.execute(
            text(
                """
                INSERT INTO shipping_pallet_advance_tohoku (advance_date, qty, updated_by)
                VALUES (:d, :qty, :updated_by)
                ON DUPLICATE KEY UPDATE
                  qty = VALUES(qty),
                  updated_by = VALUES(updated_by)
                """
            ),
            {"d": d.isoformat(), "qty": qty, "updated_by": updater},
        )
    await db.commit()
    return {
        "success": True,
        "data": {"advance_date": d.isoformat(), "qty": qty},
    }


@router.put("/bin2")
async def upsert_bin2(
    body: Bin2Body,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """オワリ便「2便」を保存（同一積込日は上書き）"""
    d = _parse_ymd(body.shipping_date)
    if not d:
        raise HTTPException(status_code=400, detail="shipping_date が不正です")
    qty = int(body.qty or 0)
    updater = getattr(current_user, "username", None) or str(
        getattr(current_user, "id", "") or ""
    )

    if qty <= 0:
        await db.execute(
            text("DELETE FROM shipping_pallet_bin2 WHERE shipping_date = :d"),
            {"d": d.isoformat()},
        )
    else:
        await db.execute(
            text(
                """
                INSERT INTO shipping_pallet_bin2 (shipping_date, qty, updated_by)
                VALUES (:d, :qty, :updated_by)
                ON DUPLICATE KEY UPDATE
                  qty = VALUES(qty),
                  updated_by = VALUES(updated_by)
                """
            ),
            {"d": d.isoformat(), "qty": qty, "updated_by": updater},
        )
    await db.commit()
    return {
        "success": True,
        "data": {"shipping_date": d.isoformat(), "qty": qty},
    }


@router.put("/cell-override")
async def upsert_cell_override(
    body: CellOverrideBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """日付×納入先セルの手動修正を保存／削除"""
    d = _parse_ymd(body.shipping_date)
    cd = (body.destination_cd or "").strip()
    if not d:
        raise HTTPException(status_code=400, detail="shipping_date が不正です")
    if not cd:
        raise HTTPException(status_code=400, detail="destination_cd が不正です")

    updater = getattr(current_user, "username", None) or str(
        getattr(current_user, "id", "") or ""
    )
    do_clear = bool(body.clear) or body.qty is None

    if do_clear:
        await db.execute(
            text(
                """
                DELETE FROM shipping_pallet_count_overrides
                WHERE shipping_date = :d AND destination_cd = :cd
                """
            ),
            {"d": d.isoformat(), "cd": cd},
        )
        await db.commit()
        return {
            "success": True,
            "data": {
                "shipping_date": d.isoformat(),
                "destination_cd": cd,
                "qty": None,
                "cleared": True,
            },
        }

    qty = max(0, int(body.qty or 0))
    await db.execute(
        text(
            """
            INSERT INTO shipping_pallet_count_overrides
              (shipping_date, destination_cd, qty, updated_by)
            VALUES (:d, :cd, :qty, :updated_by)
            ON DUPLICATE KEY UPDATE
              qty = VALUES(qty),
              updated_by = VALUES(updated_by)
            """
        ),
        {"d": d.isoformat(), "cd": cd, "qty": qty, "updated_by": updater},
    )
    await db.commit()
    return {
        "success": True,
        "data": {
            "shipping_date": d.isoformat(),
            "destination_cd": cd,
            "qty": qty,
            "cleared": False,
        },
    }


@router.get("")
async def get_pallet_count_matrix(
    start_date: Optional[str] = Query(None, description="出荷日 開始 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="出荷日 終了 YYYY-MM-DD"),
    page_key: Optional[str] = Query(
        DEFAULT_PAGE_KEY,
        description="destination_groups の page_key（既定: 出荷構成表と同じ）",
    ),
    group_names: Optional[str] = Query(
        None,
        description="対象グループ名（カンマ区切り）。未指定時は全グループ",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """グループごとにカード表示用データを返す。
    各グループは 日付(行)×納入先(列) の二次元表。同一出荷番号=1パレット。
    オワリ便は先出(東北)を反映し、翌稼働日の東北INOAC小牛田から減算する。
    セル手動修正がある場合は最終表示値として上書きする。
    """
    params: Dict[str, Any] = {}
    d_start = _parse_ymd(start_date)
    d_end = _parse_ymd(end_date)
    today = date.today()
    if d_start and d_end:
        params["start_date"] = d_start.isoformat()
        params["end_date"] = d_end.isoformat()
        date_condition = "si.shipping_date BETWEEN :start_date AND :end_date"
    elif d_start:
        d_end = d_start
        params["start_date"] = d_start.isoformat()
        params["end_date"] = d_start.isoformat()
        date_condition = "si.shipping_date = :start_date"
    elif d_end:
        d_start = d_end
        params["start_date"] = d_end.isoformat()
        params["end_date"] = d_end.isoformat()
        date_condition = "si.shipping_date = :end_date"
    else:
        d_start = today
        d_end = today
        params["start_date"] = today.isoformat()
        params["end_date"] = today.isoformat()
        date_condition = "si.shipping_date = :start_date"

    assert d_start is not None and d_end is not None
    dates = _date_range_list(d_start, d_end)

    pk = page_key or DEFAULT_PAGE_KEY
    group_q = text(
        "SELECT id, group_name, destinations FROM destination_groups "
        "WHERE page_key = :page_key ORDER BY id"
    )
    group_result = await db.execute(group_q, {"page_key": pk})
    group_rows = group_result.mappings().all()

    filter_names: Optional[List[str]] = None
    if group_names and group_names.strip():
        filter_names = [n.strip() for n in group_names.split(",") if n.strip()]

    groups_meta: List[dict] = []
    all_dest_map: Dict[str, str] = {}
    for r in group_rows:
        gname = (r["group_name"] or "").strip()
        if not gname:
            continue
        if filter_names is not None and gname not in filter_names:
            continue
        dests = _parse_group_destinations(r["destinations"])
        dest_cds = [d["cd"] for d in dests]
        for d in dests:
            if d["cd"] not in all_dest_map or (d["name"] and d["name"] != d["cd"]):
                all_dest_map[d["cd"]] = d["name"]
        groups_meta.append(
            {"group_name": gname, "destination_cds": dest_cds, "destinations": dests}
        )

    count_map: Dict[tuple, int] = {}
    name_from_items: Dict[str, str] = {}
    all_cds = list(all_dest_map.keys())
    if all_cds:
        q = text(
            f"""
            SELECT
                si.shipping_date,
                si.destination_cd,
                MAX(si.destination_name) AS destination_name,
                COUNT(DISTINCT si.shipping_no) AS pallet_count
            FROM shipping_items si
            WHERE {date_condition}
              AND si.status != 'キャンセル'
              AND si.shipping_no IS NOT NULL
              AND si.shipping_no != ''
              AND si.destination_cd IN :dest_cds
            GROUP BY si.shipping_date, si.destination_cd
            """
        ).bindparams(bindparam("dest_cds", expanding=True))
        result = await db.execute(q, {**params, "dest_cds": all_cds})
        for row in result.mappings().all():
            ds = _safe_date_str(row["shipping_date"])
            cd = str(row["destination_cd"] or "").strip()
            if not ds or not cd:
                continue
            count_map[(ds, cd)] = int(row["pallet_count"] or 0)
            if row["destination_name"]:
                name_from_items[cd] = str(row["destination_name"])

    advance_load_start = d_start - timedelta(days=21)
    advance_by_date = await _load_advance_map(db, advance_load_start, d_end)
    advance_dates_parsed = [
        _parse_ymd(ds) for ds, qty in advance_by_date.items() if qty > 0
    ]
    advance_dates_parsed = [d for d in advance_dates_parsed if d is not None]
    next_workday_of = await _next_workday_map(db, advance_dates_parsed)
    cell_overrides = await _load_cell_overrides(db, d_start, d_end)
    bin2_by_date = await _load_bin2_map(db, d_start, d_end)

    groups_out: List[dict] = []
    overall_total = 0

    for grp in groups_meta:
        gname = grp["group_name"]
        dest_cds: List[str] = grp["destination_cds"]
        destinations = [
            {
                "cd": cd,
                "name": name_from_items.get(cd)
                or next((d["name"] for d in grp["destinations"] if d["cd"] == cd), cd),
            }
            for cd in dest_cds
        ]

        matrix: Dict[str, Dict[str, int]] = {}
        row_totals: Dict[str, int] = {}
        col_totals: Dict[str, int] = {cd: 0 for cd in dest_cds}
        grand_total = 0

        for ds in dates:
            row: Dict[str, int] = {}
            row_sum = 0
            for cd in dest_cds:
                cnt = count_map.get((ds, cd), 0)
                row[cd] = cnt
                row_sum += cnt
                col_totals[cd] += cnt
            matrix[ds] = row
            row_totals[ds] = row_sum
            grand_total += row_sum

        enable_advance = _is_owari_group(gname)
        tohoku_cd = _find_tohoku_dest_cd(destinations) if enable_advance else None
        advance_qty_map: Dict[str, int] = {}
        advance_total = 0
        deduct_by_day: Dict[str, int] = {}
        bin2_qty_map: Dict[str, int] = {}
        bin2_total = 0

        if enable_advance and tohoku_cd:
            for ds in dates:
                qty = int(advance_by_date.get(ds, 0) or 0)
                if qty > 0:
                    advance_qty_map[ds] = qty
            deduct_by_day, advance_total = _apply_tohoku_advance(
                matrix=matrix,
                row_totals=row_totals,
                col_totals=col_totals,
                tohoku_cd=tohoku_cd,
                advance_by_date=advance_by_date,
                next_workday_of=next_workday_of,
                display_dates=dates,
            )
            grand_total = sum(row_totals.values())

        if enable_advance:
            for ds in dates:
                qty = int(bin2_by_date.get(ds, 0) or 0)
                if qty > 0:
                    bin2_qty_map[ds] = qty
                    bin2_total += qty

        applied_overrides = _apply_cell_overrides(
            matrix=matrix,
            dest_cds=dest_cds,
            dates=dates,
            overrides=cell_overrides,
        )
        if applied_overrides:
            row_totals, col_totals, grand_total = _recalc_totals(matrix, dest_cds, dates)

        overall_total += grand_total
        groups_out.append(
            {
                "group_name": gname,
                "destinations": destinations,
                "dates": dates,
                "matrix": matrix,
                "row_totals": row_totals,
                "col_totals": col_totals,
                "grand_total": grand_total,
                "enable_advance_tohoku": bool(enable_advance and tohoku_cd),
                "tohoku_destination_cd": tohoku_cd,
                "advance_qty": advance_qty_map,
                "advance_total": advance_total,
                "tohoku_deduct_by_date": deduct_by_day,
                "enable_bin2": bool(enable_advance),
                "bin2_qty": bin2_qty_map,
                "bin2_total": bin2_total,
                "cell_overrides": applied_overrides,
            }
        )

    return {
        "success": True,
        "data": {
            "dates": dates,
            "groups": groups_out,
            "grand_total": overall_total,
        },
    }


def _format_date_label_ja(ymd: str) -> str:
    d = _parse_ymd(ymd)
    if not d:
        return ymd
    week = ["月", "火", "水", "木", "金", "土", "日"][d.weekday()]
    return f"{ymd[5:]}({week})"


def _cell_display(n: Any) -> str:
    try:
        v = int(n or 0)
    except (TypeError, ValueError):
        return ""
    return "" if v == 0 else f"{v:,}"


def _bin2_display(n: Any) -> str:
    """2便は印刷・メールで ○ / 空欄"""
    try:
        return "○" if int(n or 0) > 0 else ""
    except (TypeError, ValueError):
        return ""


def build_group_matrix_html(
    group: Dict[str, Any],
    *,
    start_date: str,
    end_date: str,
    for_print: bool = False,
) -> str:
    """グループのパレット数表 HTML（印刷・メール共用）。"""
    gname = html_lib.escape(str(group.get("group_name") or ""))
    destinations: List[dict] = list(group.get("destinations") or [])
    dates: List[str] = list(group.get("dates") or [])
    matrix: Dict[str, Dict[str, int]] = group.get("matrix") or {}
    row_totals: Dict[str, int] = group.get("row_totals") or {}
    col_totals: Dict[str, int] = group.get("col_totals") or {}
    grand_total = int(group.get("grand_total") or 0)
    enable_advance = bool(group.get("enable_advance_tohoku"))
    advance_qty: Dict[str, int] = group.get("advance_qty") or {}
    advance_total = int(group.get("advance_total") or 0)
    enable_bin2 = bool(group.get("enable_bin2"))
    bin2_qty: Dict[str, int] = group.get("bin2_qty") or {}
    bin2_total = int(group.get("bin2_total") or 0)
    cell_overrides: Dict[str, Dict[str, int]] = group.get("cell_overrides") or {}

    visible_dates = [
        ds
        for ds in dates
        if (row_totals.get(ds) or 0) > 0
        or (advance_qty.get(ds) or 0) > 0
        or (bin2_qty.get(ds) or 0) > 0
        or bool(cell_overrides.get(ds))
    ]

    th_dest = "".join(
        f'<th class="dest"><div class="dest-cd">{html_lib.escape(d.get("cd") or "")}</div>'
        f'<div class="dest-name">{html_lib.escape(d.get("name") or "")}</div></th>'
        for d in destinations
    )
    advance_th = '<th class="advance">先出(東北)</th>' if enable_advance else ""
    bin2_th = '<th class="bin2">2便</th>' if enable_bin2 else ""

    body_rows: List[str] = []
    for ds in visible_dates:
        cells = "".join(
            f'<td class="num">{_cell_display((matrix.get(ds) or {}).get(d["cd"], 0))}</td>'
            for d in destinations
        )
        adv_td = (
            f'<td class="num advance">{_cell_display(advance_qty.get(ds, 0))}</td>'
            if enable_advance
            else ""
        )
        bin2_td = (
            f'<td class="num bin2">{_bin2_display(bin2_qty.get(ds, 0))}</td>'
            if enable_bin2
            else ""
        )
        body_rows.append(
            "<tr>"
            f'<td class="date">{html_lib.escape(_format_date_label_ja(ds))}</td>'
            f"{cells}{adv_td}{bin2_td}"
            f'<td class="num total">{_cell_display(row_totals.get(ds, 0))}</td>'
            "</tr>"
        )

    total_cells = "".join(
        f'<td class="num total">{_cell_display(col_totals.get(d["cd"], 0))}</td>'
        for d in destinations
    )
    adv_total_td = (
        f'<td class="num total advance">{_cell_display(advance_total)}</td>'
        if enable_advance
        else ""
    )
    bin2_total_td = (
        f'<td class="num total bin2">{_cell_display(bin2_total)}</td>'
        if enable_bin2
        else ""
    )
    body_rows.append(
        '<tr class="row-sum">'
        '<td class="date">合計</td>'
        f"{total_cells}{adv_total_td}{bin2_total_td}"
        f'<td class="num total">{_cell_display(grand_total)}</td>'
        "</tr>"
    )

    page_css = ""
    if for_print:
        page_css = """
@page { size: A4 landscape; margin: 12mm; }
@media print {
  body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<title>出荷パレット数 {gname}</title>
<style>
{page_css}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 16px;
  font-family: "Yu Gothic", "YuGothic", "Meiryo", "Hiragino Kaku Gothic ProN", sans-serif;
  color: #0f172a; background: #fff; font-size: 12px;
}}
h1 {{ margin: 0 0 4px; font-size: 18px; font-weight: 800; }}
.meta {{ color: #64748b; margin-bottom: 12px; font-size: 12px; }}
table {{
  width: 100%; border-collapse: collapse; table-layout: fixed;
  border: 1.5px solid #334155;
}}
th, td {{
  border: 1px solid #94a3b8; padding: 4px 6px; text-align: center;
  vertical-align: middle; word-break: break-word;
}}
th {{
  background: #f1f5f9; font-weight: 700; font-size: 11px;
}}
th.date-col {{ width: 72px; }}
th.advance, td.advance {{ background: #fff7ed; color: #9a3412; }}
th.bin2, td.bin2 {{ background: #f0fdf4; color: #166534; font-size: 16px; font-weight: 800; }}
th.total-col, td.total {{ background: #eff6ff; font-weight: 700; color: #1d4ed8; }}
.dest-cd {{ font-size: 9px; color: #94a3b8; font-weight: 600; }}
.dest-name {{ font-size: 10px; font-weight: 700; color: #334155; }}
td.date {{ font-weight: 700; white-space: nowrap; background: #f8fafc; }}
td.num {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
tr.row-sum td {{ background: #e0f2fe; font-weight: 800; }}
</style>
</head>
<body>
  <h1>出荷パレット数 — {gname}</h1>
  <div class="meta">積込期間: {html_lib.escape(start_date)} 〜 {html_lib.escape(end_date)} ／ 合計パレット: {grand_total:,}</div>
  <table>
    <thead>
      <tr>
        <th class="date-col">積込日</th>
        {th_dest}
        {advance_th}
        {bin2_th}
        <th class="total-col">合計</th>
      </tr>
    </thead>
    <tbody>
      {"".join(body_rows)}
    </tbody>
  </table>
</body>
</html>"""


@router.post("/send-mail")
async def send_pallet_count_mail(
    body: SendMailBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
) -> dict:
    """指定グループのパレット数表をメール送信する。"""
    gname = (body.group_name or "").strip()
    if not gname:
        raise HTTPException(status_code=400, detail="グループ名が必要です")

    matrix_res = await get_pallet_count_matrix(
        start_date=body.start_date,
        end_date=body.end_date,
        page_key=body.page_key or DEFAULT_PAGE_KEY,
        group_names=gname,
        db=db,
        current_user=current_user,
    )
    groups = (matrix_res.get("data") or {}).get("groups") or []
    if not groups:
        raise HTTPException(status_code=404, detail=f"グループ「{gname}」のデータがありません")

    group = groups[0]
    subject = (body.subject or "").strip() or (
        f"【出荷パレット数】{gname}（{body.start_date}〜{body.end_date}）"
    )
    html_body = build_group_matrix_html(
        group,
        start_date=body.start_date,
        end_date=body.end_date,
        for_print=False,
    )

    smtp = await load_smtp_config(db)
    if not smtp:
        raise HTTPException(
            status_code=400,
            detail="SMTP設定がありません。システム設定のメール連携を確認してください。",
        )

    results = await send_bulk_html_email(smtp, body.to_emails, subject, html_body)
    ok = [r.email for r in results if r.success]
    ng = [{"email": r.email, "error": r.error} for r in results if not r.success]
    if not ok:
        detail = ng[0]["error"] if ng else "メール送信に失敗しました"
        raise HTTPException(status_code=500, detail=detail)

    return {
        "success": True,
        "data": {
            "sent": ok,
            "failed": ng,
            "subject": subject,
            "group_name": gname,
        },
        "message": f"{len(ok)}件に送信しました"
        + (f"（失敗 {len(ng)}件）" if ng else ""),
    }

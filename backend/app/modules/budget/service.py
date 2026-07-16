"""予算CSV取込・製品紐付・分析サービス"""
from __future__ import annotations

import csv
import io
import json
import re
from collections import defaultdict
from decimal import Decimal
from typing import Any, Optional

from loguru import logger
from sqlalchemy import and_, case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.budget.models import (
    BudgetImportBatch,
    BudgetMonthly,
    BudgetProcessWorkingDays,
    BudgetWorkingDays,
)
from app.modules.erp import standard_cost_models as cost_models
from app.modules.master.models import (
    EquipmentEfficiency,
    Process,
    Product,
    ProductRouteStep,
    ProductRouteStepMachine,
)

_MONTH_HEADER_RE = re.compile(r"^(\d{4})\s*年\s*(\d{1,2})\s*月$")
_PART_KEYS = ("品番", "品　　番", "品  番", "品　番")
_DEV_KEYS = ("開発コード", "開発ｺｰﾄﾞ", "開発コード")

# 予算分析で除外する工程名（工程負荷・工程別月次推移）
_EXCLUDED_PROCESS_NAMES = frozenset(
    {
        "外注検査前",
        "外注支給前",
        "外注倉庫",
        "溶接前検査",
        "外注切断",
        "外注切断工程",
        "倉庫",
    }
)

# 工程表示順（左側ほど優先）
_PROCESS_DISPLAY_ORDER = (
    "切断",
    "面取",
    "SW",
    "成型",
    "メッキ",
    "溶接",
    "検査",
    "外注メッキ",
    "外注溶接",
    "外注検査",
)
_PROCESS_DISPLAY_RANK = {name: i for i, name in enumerate(_PROCESS_DISPLAY_ORDER)}


def _is_excluded_process(process: Optional[Process], process_cd: str = "") -> bool:
    """除外工程判定（工程名優先、CDフォールバック）"""
    name = ""
    short = ""
    if process is not None:
        name = (process.process_name or "").strip()
        short = (process.short_name or "").strip()
    if name in _EXCLUDED_PROCESS_NAMES or short in _EXCLUDED_PROCESS_NAMES:
        return True
    cd = (process_cd or (process.process_cd if process else "") or "").strip()
    # 名称未解決時の保険：CD文字列が除外名そのもの
    return cd in _EXCLUDED_PROCESS_NAMES


def _process_display_rank(process_name: str | None, process_cd: str = "") -> int:
    """表示順ランク（小さいほど先）。未定義工程は末尾。"""
    name = (process_name or "").strip()
    if name in _PROCESS_DISPLAY_RANK:
        return _PROCESS_DISPLAY_RANK[name]
    # 長い工程名から優先マッチ（外注検査 > 検査）
    for key in sorted(_PROCESS_DISPLAY_RANK.keys(), key=len, reverse=True):
        if name.startswith(key):
            return _PROCESS_DISPLAY_RANK[key]
    cd = (process_cd or "").strip()
    if cd in _PROCESS_DISPLAY_RANK:
        return _PROCESS_DISPLAY_RANK[cd]
    return len(_PROCESS_DISPLAY_ORDER) + 100


def _sort_process_items(items: list[dict[str, Any]], *, secondary_key: str = "process_cd") -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda x: (
            _process_display_rank(x.get("process_name"), x.get("process_cd") or ""),
            x.get(secondary_key) or "",
        ),
    )


def _decode_csv_bytes(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp932", "shift_jis", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp932", errors="replace")


def _normalize_header(h: str) -> str:
    return (h or "").replace("\ufeff", "").strip()


def _parse_qty(val: Any) -> int:
    if val is None:
        return 0
    s = str(val).strip()
    if not s or s in ("-", "－", "—"):
        return 0
    s = s.replace(",", "").replace("，", "").replace(" ", "")
    try:
        return int(round(float(s)))
    except (TypeError, ValueError):
        return 0


def _find_col(fieldnames: list[str], candidates: tuple[str, ...]) -> Optional[str]:
    normalized = {_normalize_header(f): f for f in fieldnames}
    for c in candidates:
        if c in normalized:
            return normalized[c]
    # 空白・全角空白を除去して再比較
    compact_map = {re.sub(r"[\s　]+", "", k): v for k, v in normalized.items()}
    for c in candidates:
        key = re.sub(r"[\s　]+", "", c)
        if key in compact_map:
            return compact_map[key]
    return None


def parse_budget_csv(raw: bytes) -> tuple[list[dict[str, Any]], list[tuple[int, int]], list[str]]:
    """
    CSV をパースし、行データと年月列を返す。
    戻り値: (rows, months[(year,month)], warnings)
    rows の各要素: development_code, part_number, quantities: {(y,m): qty}
    """
    text = _decode_csv_bytes(raw)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSVヘッダが読み取れません")

    fieldnames = [_normalize_header(f) for f in reader.fieldnames]
    # DictReader のキーは元のままなのでマッピングを作る
    key_map = {_normalize_header(f): f for f in reader.fieldnames}

    part_col = _find_col(list(key_map.keys()), _PART_KEYS)
    dev_col = _find_col(list(key_map.keys()), _DEV_KEYS)
    if not part_col:
        raise ValueError("CSVに「品番」列が見つかりません")

    month_cols: list[tuple[str, int, int]] = []
    for header in fieldnames:
        m = _MONTH_HEADER_RE.match(header)
        if m:
            y, mo = int(m.group(1)), int(m.group(2))
            if 1 <= mo <= 12:
                month_cols.append((header, y, mo))

    if not month_cols:
        raise ValueError("CSVに年月列（例: 2026年10月）が見つかりません")

    # 同一品番は数量を合算してから製品紐付する
    aggregated: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    raw_line_count = 0
    for i, raw_row in enumerate(reader, start=2):
        part_raw = raw_row.get(key_map[part_col], "")
        part_number = str(part_raw or "").strip()
        if not part_number:
            continue
        raw_line_count += 1
        dev_code = ""
        if dev_col:
            dev_code = str(raw_row.get(key_map[dev_col], "") or "").strip()

        if part_number not in aggregated:
            quantities = {(y, mo): 0 for _, y, mo in month_cols}
            aggregated[part_number] = {
                "line_no": i,
                "development_code": dev_code,
                "part_number": part_number,
                "quantities": quantities,
                "source_lines": 0,
                "dev_codes": [],
            }
        entry = aggregated[part_number]
        entry["source_lines"] += 1
        if dev_code and dev_code not in entry["dev_codes"]:
            entry["dev_codes"].append(dev_code)
        for header, y, mo in month_cols:
            entry["quantities"][(y, mo)] += _parse_qty(raw_row.get(key_map[header]))

    rows: list[dict[str, Any]] = []
    for part_number, entry in aggregated.items():
        # 複数開発コードがある場合は「 / 」で連結（先頭を主表示）
        dev_codes = entry["dev_codes"]
        development_code = " / ".join(dev_codes) if dev_codes else (entry["development_code"] or "")
        rows.append(
            {
                "line_no": entry["line_no"],
                "development_code": development_code,
                "part_number": part_number,
                "quantities": entry["quantities"],
                "source_lines": entry["source_lines"],
            }
        )

    months = [(y, mo) for _, y, mo in month_cols]
    if not rows:
        warnings.append("有効な品番行がありません")
    else:
        merged = sum(1 for r in rows if r.get("source_lines", 1) > 1)
        if merged:
            warnings.append(
                f"同一品番を合算: CSV {raw_line_count}行 → {len(rows)}品番（重複合算 {merged}件）"
            )
    return rows, months, warnings


async def _resolve_products_by_part(
    db: AsyncSession, part_numbers: list[str]
) -> dict[str, list[Product]]:
    """品番 → 製品CD末尾が1の製品一覧"""
    if not part_numbers:
        return {}
    unique = sorted({p.strip() for p in part_numbers if p and p.strip()})
    result = await db.execute(
        select(Product).where(
            Product.part_number.in_(unique),
            Product.product_cd.like("%1"),
        )
    )
    products = result.scalars().all()
    mapping: dict[str, list[Product]] = defaultdict(list)
    for p in products:
        key = (p.part_number or "").strip()
        if key:
            mapping[key].append(p)
    # active を優先
    for key, plist in mapping.items():
        plist.sort(key=lambda x: (0 if (x.status or "") == "active" else 1, x.product_cd or ""))
    return mapping


def _pick_product(candidates: list[Product]) -> tuple[Optional[Product], str]:
    if not candidates:
        return None, "unmatched"
    if len(candidates) == 1:
        return candidates[0], "matched"
    return candidates[0], "multi_match"


async def import_budget_csv(
    db: AsyncSession,
    *,
    raw: bytes,
    file_name: str,
    uploaded_by: Optional[str],
) -> dict[str, Any]:
    parsed_rows, months, warnings = parse_budget_csv(raw)
    # 合算後の品番一覧で製品マスタ（製品CD末尾1）を紐付
    part_numbers = [r["part_number"] for r in parsed_rows]
    product_map = await _resolve_products_by_part(db, part_numbers)

    batch = BudgetImportBatch(
        file_name=file_name,
        months_json=json.dumps([{"year": y, "month": m} for y, m in months], ensure_ascii=False),
        total_rows=len(parsed_rows),  # 合算後のユニーク品番数
        uploaded_by=uploaded_by,
        remark="; ".join(warnings) if warnings else None,
    )
    db.add(batch)
    await db.flush()

    matched_parts = 0
    unmatched_parts = 0
    unmatched_samples: list[dict[str, Any]] = []
    inserted = 0
    updated = 0

    # 既存キーを一括取得（対象年月のみ）
    month_pairs = list(months)
    existing_map: dict[tuple[int, int, str], BudgetMonthly] = {}
    if month_pairs and parsed_rows:
        conds = [
            and_(BudgetMonthly.year == y, BudgetMonthly.month == m) for y, m in month_pairs
        ]
        existing_res = await db.execute(select(BudgetMonthly).where(or_(*conds)))
        for row in existing_res.scalars().all():
            existing_map[(int(row.year), int(row.month), row.part_number)] = row

    for r in parsed_rows:
        part_number = r["part_number"]
        product, status = _pick_product(product_map.get(part_number, []))
        if status == "unmatched":
            unmatched_parts += 1
            if len(unmatched_samples) < 30:
                unmatched_samples.append(
                    {
                        "line_no": r["line_no"],
                        "development_code": r["development_code"],
                        "part_number": part_number,
                    }
                )
        else:
            matched_parts += 1

        for (y, m), qty in r["quantities"].items():
            key = (y, m, part_number)
            existing = existing_map.get(key)
            if existing:
                existing.development_code = r["development_code"] or existing.development_code
                existing.product_cd = product.product_cd if product else None
                existing.product_name = product.product_name if product else None
                existing.budget_qty = qty
                existing.match_status = status
                existing.import_batch_id = batch.id
                existing.source_file_name = file_name
                updated += 1
            else:
                new_row = BudgetMonthly(
                    year=y,
                    month=m,
                    development_code=r["development_code"] or None,
                    part_number=part_number,
                    product_cd=product.product_cd if product else None,
                    product_name=product.product_name if product else None,
                    budget_qty=qty,
                    match_status=status,
                    import_batch_id=batch.id,
                    source_file_name=file_name,
                )
                db.add(new_row)
                existing_map[key] = new_row
                inserted += 1

    batch.matched_rows = matched_parts
    batch.unmatched_rows = unmatched_parts
    batch.inserted_rows = inserted
    batch.updated_rows = updated
    await db.commit()
    await db.refresh(batch)

    logger.info(
        "予算CSV取込完了 file={} rows={} matched={} unmatched={} inserted={} updated={}",
        file_name,
        len(parsed_rows),
        matched_parts,
        unmatched_parts,
        inserted,
        updated,
    )

    return {
        "success": True,
        "batch_id": batch.id,
        "file_name": file_name,
        "months": [{"year": y, "month": m} for y, m in months],
        "total_rows": len(parsed_rows),
        "matched_rows": matched_parts,
        "unmatched_rows": unmatched_parts,
        "inserted_rows": inserted,
        "updated_rows": updated,
        "unmatched_samples": unmatched_samples,
        "message": (
            f"取込完了: {len(parsed_rows)}品番 / 紐付成功 {matched_parts} / "
            f"未紐付 {unmatched_parts} / 新規 {inserted} / 更新 {updated}"
        ),
    }


def _ym_filter(year: Optional[int], month: Optional[int]):
    conds = []
    if year is not None:
        conds.append(BudgetMonthly.year == year)
    if month is not None:
        conds.append(BudgetMonthly.month == month)
    return and_(*conds) if conds else True


async def get_available_months(db: AsyncSession) -> list[dict[str, int]]:
    q = (
        select(BudgetMonthly.year, BudgetMonthly.month)
        .group_by(BudgetMonthly.year, BudgetMonthly.month)
        .order_by(BudgetMonthly.year.desc(), BudgetMonthly.month.desc())
    )
    rows = (await db.execute(q)).all()
    return [{"year": int(r.year), "month": int(r.month)} for r in rows]


async def get_summary(
    db: AsyncSession, year: Optional[int], month: Optional[int]
) -> dict[str, Any]:
    base = select(BudgetMonthly).where(_ym_filter(year, month))
    sub = base.subquery()
    stats = await db.execute(
        select(
            func.count().label("product_count"),
            func.coalesce(func.sum(sub.c.budget_qty), 0).label("total_qty"),
            func.coalesce(
                func.sum(case((sub.c.match_status != "unmatched", 1), else_=0)), 0
            ).label("matched"),
            func.coalesce(
                func.sum(case((sub.c.match_status == "unmatched", 1), else_=0)), 0
            ).label("unmatched"),
            func.count(func.distinct(func.concat(sub.c.year, "-", sub.c.month))).label("month_count"),
        )
    )
    row = stats.one()
    return {
        "year": year,
        "month": month,
        "product_count": int(row.product_count or 0),
        "matched_count": int(row.matched or 0),
        "unmatched_count": int(row.unmatched or 0),
        "total_budget_qty": int(row.total_qty or 0),
        "month_count": int(row.month_count or 0),
    }


async def list_budget(
    db: AsyncSession,
    *,
    year: Optional[int],
    month: Optional[int],
    keyword: Optional[str],
    match_status: Optional[str],
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    q = select(BudgetMonthly).where(_ym_filter(year, month))
    if match_status:
        q = q.where(BudgetMonthly.match_status == match_status)
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                BudgetMonthly.part_number.like(k),
                BudgetMonthly.product_cd.like(k),
                BudgetMonthly.product_name.like(k),
                BudgetMonthly.development_code.like(k),
            )
        )
    count_q = select(func.count()).select_from(q.subquery())
    total = int((await db.execute(count_q)).scalar() or 0)
    q = q.order_by(
        BudgetMonthly.year.desc(),
        BudgetMonthly.month.desc(),
        BudgetMonthly.development_code.asc(),
        BudgetMonthly.part_number.asc(),
    )
    q = q.offset(max(page - 1, 0) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": rows,
    }


async def analyze_process_load(
    db: AsyncSession, year: int, month: int
) -> list[dict[str, Any]]:
    """予算数量 × 工程ルート（標準サイクルタイム）で工程負荷を集計"""
    budgets = (
        await db.execute(
            select(BudgetMonthly).where(
                BudgetMonthly.year == year,
                BudgetMonthly.month == month,
                BudgetMonthly.product_cd.isnot(None),
                BudgetMonthly.match_status != "unmatched",
            )
        )
    ).scalars().all()
    if not budgets:
        return []

    product_qty: dict[str, int] = defaultdict(int)
    for b in budgets:
        if b.product_cd:
            product_qty[b.product_cd] += int(b.budget_qty or 0)

    cds = list(product_qty.keys())
    steps = (
        await db.execute(select(ProductRouteStep).where(ProductRouteStep.product_cd.in_(cds)))
    ).scalars().all()

    process_cds = sorted({s.process_cd for s in steps if s.process_cd})
    process_map: dict[str, Process] = {}
    if process_cds:
        procs = (
            await db.execute(select(Process).where(Process.process_cd.in_(process_cds)))
        ).scalars().all()
        process_map = {p.process_cd: p for p in procs}

    # process_cd -> agg
    agg: dict[str, dict[str, Any]] = {}
    products_per_process: dict[str, set[str]] = defaultdict(set)

    for step in steps:
        qty = product_qty.get(step.product_cd, 0)
        if qty <= 0:
            continue
        pc = step.process_cd or "UNKNOWN"
        p = process_map.get(pc)
        if _is_excluded_process(p, pc):
            continue
        cycle = float(step.standard_cycle_time or 0)
        setup = float(step.setup_time or 0)
        hours = (qty * cycle + setup) / 3600.0 if cycle or setup else 0.0
        if pc not in agg:
            agg[pc] = {
                "process_cd": pc,
                "process_name": (p.process_name if p else pc) or pc,
                "product_count": 0,
                "total_budget_qty": 0,
                "total_hours": 0.0,
                "is_outsource": int(p.is_outsource or 0) if p else 0,
            }
        agg[pc]["total_budget_qty"] += qty
        agg[pc]["total_hours"] += hours
        products_per_process[pc].add(step.product_cd)

    for pc, s in products_per_process.items():
        agg[pc]["product_count"] = len(s)
        agg[pc]["total_hours"] = round(agg[pc]["total_hours"], 2)

    return _sort_process_items(list(agg.values()), secondary_key="process_cd")


async def analyze_equipment_load(
    db: AsyncSession, year: int, month: int
) -> list[dict[str, Any]]:
    """予算数量 × 設備能率（step_time / efficiency）で設備負荷を集計"""
    budgets = (
        await db.execute(
            select(BudgetMonthly).where(
                BudgetMonthly.year == year,
                BudgetMonthly.month == month,
                BudgetMonthly.product_cd.isnot(None),
                BudgetMonthly.match_status != "unmatched",
            )
        )
    ).scalars().all()
    if not budgets:
        return []

    product_qty: dict[str, int] = defaultdict(int)
    for b in budgets:
        if b.product_cd:
            product_qty[b.product_cd] += int(b.budget_qty or 0)

    cds = list(product_qty.keys())

    # 優先: equipment_efficiency
    eff_rows = (
        await db.execute(
            select(EquipmentEfficiency).where(
                EquipmentEfficiency.product_cd.in_(cds),
                or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status == 1),
            )
        )
    ).scalars().all()

    agg: dict[str, dict[str, Any]] = {}
    products_per_machine: dict[str, set[str]] = defaultdict(set)
    eff_sum: dict[str, list[float]] = defaultdict(list)

    if eff_rows:
        for er in eff_rows:
            pcd = (er.product_cd or "").strip()
            qty = product_qty.get(pcd, 0)
            if qty <= 0:
                continue
            mcd = (er.machine_cd or "").strip() or "UNKNOWN"
            step_time = float(er.step_time or 0)  # 秒/個 想定
            eff = float(er.efficiency_rate or 0)
            if step_time <= 0:
                continue
            # 能率(%) を考慮: 実負荷時間 = qty * step_time / (eff/100)
            factor = (eff / 100.0) if eff and eff > 0 else 1.0
            hours = (qty * step_time / factor) / 3600.0
            if mcd not in agg:
                agg[mcd] = {
                    "machine_cd": mcd,
                    "machine_name": er.machines_name or mcd,
                    "product_count": 0,
                    "total_budget_qty": 0,
                    "total_hours": 0.0,
                    "avg_efficiency_rate": None,
                }
            agg[mcd]["total_budget_qty"] += qty
            agg[mcd]["total_hours"] += hours
            products_per_machine[mcd].add(pcd)
            if eff > 0:
                eff_sum[mcd].append(eff)
    else:
        # フォールバック: product_route_step_machines
        machine_rows = (
            await db.execute(
                select(ProductRouteStepMachine).where(ProductRouteStepMachine.product_cd.in_(cds))
            )
        ).scalars().all()
        for mr in machine_rows:
            qty = product_qty.get(mr.product_cd, 0)
            if qty <= 0:
                continue
            mcd = (mr.machine_cd or "").strip() or "UNKNOWN"
            sec = float(mr.process_time_sec or 0)
            if sec <= 0:
                continue
            hours = (qty * sec) / 3600.0
            if mcd not in agg:
                agg[mcd] = {
                    "machine_cd": mcd,
                    "machine_name": mr.machine_name or mcd,
                    "product_count": 0,
                    "total_budget_qty": 0,
                    "total_hours": 0.0,
                    "avg_efficiency_rate": None,
                }
            agg[mcd]["total_budget_qty"] += qty
            agg[mcd]["total_hours"] += hours
            products_per_machine[mcd].add(mr.product_cd)

    for mcd, s in products_per_machine.items():
        agg[mcd]["product_count"] = len(s)
        agg[mcd]["total_hours"] = round(agg[mcd]["total_hours"], 2)
        if eff_sum.get(mcd):
            agg[mcd]["avg_efficiency_rate"] = round(sum(eff_sum[mcd]) / len(eff_sum[mcd]), 1)

    return sorted(agg.values(), key=lambda x: (-x["total_hours"], x["machine_cd"]))


async def analyze_cost(
    db: AsyncSession, year: int, month: int
) -> dict[str, Any]:
    """予算数量 × 標準原価 / 売単価で原価・売上概算"""
    budgets = (
        await db.execute(
            select(BudgetMonthly).where(
                BudgetMonthly.year == year,
                BudgetMonthly.month == month,
            )
        )
    ).scalars().all()
    if not budgets:
        return {"items": [], "totals": {"sales_amount": 0, "cost_amount": 0, "margin_amount": 0, "budget_qty": 0}}

    cds = [b.product_cd for b in budgets if b.product_cd]
    product_price: dict[str, Decimal] = {}
    if cds:
        prods = (
            await db.execute(select(Product).where(Product.product_cd.in_(cds)))
        ).scalars().all()
        product_price = {
            p.product_cd: (p.unit_price if p.unit_price is not None else Decimal("0"))
            for p in prods
        }

    # 有効な標準原価バージョン（該当年優先 → 最新 active）
    version_id = None
    ver_res = await db.execute(
        select(cost_models.CostStandardVersion.id)
        .where(
            cost_models.CostStandardVersion.fiscal_year == year,
            cost_models.CostStandardVersion.status == "active",
        )
        .order_by(cost_models.CostStandardVersion.effective_from.desc())
        .limit(1)
    )
    version_id = ver_res.scalar_one_or_none()
    if version_id is None:
        ver_res = await db.execute(
            select(cost_models.CostStandardVersion.id)
            .where(cost_models.CostStandardVersion.status == "active")
            .order_by(
                cost_models.CostStandardVersion.fiscal_year.desc(),
                cost_models.CostStandardVersion.effective_from.desc(),
            )
            .limit(1)
        )
        version_id = ver_res.scalar_one_or_none()

    cost_map: dict[str, Decimal] = {}
    if version_id and cds:
        cost_rows = (
            await db.execute(
                select(cost_models.ProductStandardCost).where(
                    cost_models.ProductStandardCost.version_id == version_id,
                    cost_models.ProductStandardCost.product_cd.in_(cds),
                )
            )
        ).scalars().all()
        cost_map = {
            c.product_cd: (c.total_cost_std if c.total_cost_std is not None else Decimal("0"))
            for c in cost_rows
        }

    items: list[dict[str, Any]] = []
    tot_sales = Decimal("0")
    tot_cost = Decimal("0")
    tot_qty = 0

    for b in budgets:
        qty = int(b.budget_qty or 0)
        tot_qty += qty
        unit_price = product_price.get(b.product_cd) if b.product_cd else None
        unit_cost = cost_map.get(b.product_cd) if b.product_cd else None
        up = float(unit_price) if unit_price is not None else 0.0
        uc = float(unit_cost) if unit_cost is not None else 0.0
        sales = up * qty
        cost = uc * qty
        margin = sales - cost
        tot_sales += Decimal(str(sales))
        tot_cost += Decimal(str(cost))
        items.append(
            {
                "product_cd": b.product_cd,
                "product_name": b.product_name,
                "part_number": b.part_number,
                "development_code": b.development_code,
                "budget_qty": qty,
                "unit_price": up if unit_price is not None else None,
                "unit_cost_std": uc if unit_cost is not None else None,
                "sales_amount": round(sales, 2),
                "cost_amount": round(cost, 2),
                "margin_amount": round(margin, 2),
            }
        )

    items.sort(key=lambda x: (-x["sales_amount"], x["part_number"]))
    margin_total = tot_sales - tot_cost
    return {
        "version_id": version_id,
        "items": items,
        "totals": {
            "budget_qty": tot_qty,
            "sales_amount": float(round(tot_sales, 2)),
            "cost_amount": float(round(tot_cost, 2)),
            "margin_amount": float(round(margin_total, 2)),
        },
    }


def _avg_daily(qty: int | float, working_days: Optional[int]) -> Optional[int]:
    """予算数量 ÷ 稼働日数（整数、四捨五入。稼働日未設定/0 は None）"""
    if working_days is None or working_days <= 0:
        return None
    return int(round(float(qty) / float(working_days)))


async def get_working_days_map(
    db: AsyncSession, year: Optional[int] = None
) -> dict[tuple[int, int], int]:
    q = select(BudgetWorkingDays)
    if year is not None:
        q = q.where(BudgetWorkingDays.year == year)
    rows = (await db.execute(q)).scalars().all()
    return {(int(r.year), int(r.month)): int(r.working_days or 0) for r in rows}


async def get_process_working_days_map(
    db: AsyncSession, year: Optional[int] = None, process_cd: Optional[str] = None
) -> dict[tuple[int, int, str], int]:
    """(year, month, process_cd) -> working_days"""
    q = select(BudgetProcessWorkingDays)
    if year is not None:
        q = q.where(BudgetProcessWorkingDays.year == year)
    if process_cd:
        q = q.where(BudgetProcessWorkingDays.process_cd == process_cd.strip())
    rows = (await db.execute(q)).scalars().all()
    return {
        (int(r.year), int(r.month), (r.process_cd or "").strip()): int(r.working_days or 0)
        for r in rows
    }


def _resolve_working_days(
    year: int,
    month: int,
    process_cd: Optional[str],
    default_map: dict[tuple[int, int], int],
    process_map: dict[tuple[int, int, str], int],
) -> tuple[int, bool]:
    """
    工程別稼働日を優先し、無ければ共通稼働日。
    戻り値: (days, is_override)
    """
    pc = (process_cd or "").strip()
    if pc:
        key = (year, month, pc)
        if key in process_map:
            return int(process_map[key] or 0), True
    return int(default_map.get((year, month), 0) or 0), False


async def list_working_days(
    db: AsyncSession, year: Optional[int] = None
) -> list[dict[str, Any]]:
    """予算データがある年月を軸に、共通稼働日数をマージして返す"""
    months = await get_available_months(db)
    if year is not None:
        months = [m for m in months if m["year"] == year]
    wd_map = await get_working_days_map(db, year)

    # 予算が無くても稼働日だけある年月も出す
    extra_q = select(BudgetWorkingDays.year, BudgetWorkingDays.month)
    if year is not None:
        extra_q = extra_q.where(BudgetWorkingDays.year == year)
    extra_rows = (await db.execute(extra_q)).all()
    known = {(m["year"], m["month"]) for m in months}
    for r in extra_rows:
        key = (int(r.year), int(r.month))
        if key not in known:
            months.append({"year": key[0], "month": key[1]})
            known.add(key)
    months.sort(key=lambda m: (m["year"], m["month"]))

    # 予算合計も付与（日平均計算用）
    trend = await analyze_monthly_trend_raw(db, year)
    qty_map = {(t["year"], t["month"]): t["total_budget_qty"] for t in trend}

    result = []
    for m in months:
        key = (m["year"], m["month"])
        days = wd_map.get(key)
        qty = int(qty_map.get(key, 0))
        result.append(
            {
                "year": m["year"],
                "month": m["month"],
                "label": f"{m['year']}/{m['month']:02d}",
                "working_days": days if days is not None else 0,
                "total_budget_qty": qty,
                "avg_daily_qty": _avg_daily(qty, days if days else None),
            }
        )
    return result


async def list_process_working_day_options(db: AsyncSession) -> list[dict[str, str]]:
    """工程別稼働日設定用の工程候補（表示順）"""
    # 予算に紐付く製品の工程ルートから候補を取得
    budget_cds = (
        await db.execute(
            select(BudgetMonthly.product_cd)
            .where(
                BudgetMonthly.product_cd.isnot(None),
                BudgetMonthly.match_status != "unmatched",
            )
            .distinct()
        )
    ).scalars().all()
    process_cds: set[str] = set()
    if budget_cds:
        steps = (
            await db.execute(
                select(ProductRouteStep.process_cd).where(
                    ProductRouteStep.product_cd.in_([c for c in budget_cds if c])
                )
            )
        ).scalars().all()
        process_cds = {(pc or "").strip() for pc in steps if (pc or "").strip()}

    procs: list[Process] = []
    if process_cds:
        procs = (
            await db.execute(select(Process).where(Process.process_cd.in_(list(process_cds))))
        ).scalars().all()
    else:
        procs = (
            await db.execute(select(Process).where(Process.process_name.in_(_PROCESS_DISPLAY_ORDER)))
        ).scalars().all()

    items = [
        {
            "process_cd": p.process_cd,
            "process_name": (p.process_name or p.process_cd or "").strip(),
            "is_outsource": int(p.is_outsource or 0),
        }
        for p in procs
        if p.process_cd and not _is_excluded_process(p, p.process_cd)
    ]
    return [
        {"process_cd": x["process_cd"], "process_name": x["process_name"]}
        for x in _sort_process_items(items, secondary_key="process_cd")
    ]


async def list_working_days_bundle(
    db: AsyncSession, year: Optional[int] = None
) -> dict[str, Any]:
    defaults = await list_working_days(db, year)
    options = await list_process_working_day_options(db)
    proc_map = await get_process_working_days_map(db, year)
    name_map = {o["process_cd"]: o["process_name"] for o in options}
    overrides = []
    for (y, m, pc), days in sorted(proc_map.items()):
        overrides.append(
            {
                "year": y,
                "month": m,
                "label": f"{y}/{m:02d}",
                "process_cd": pc,
                "process_name": name_map.get(pc, pc),
                "working_days": days,
            }
        )
    return {
        "defaults": defaults,
        "process_options": options,
        "process_overrides": overrides,
    }


async def upsert_process_working_days(
    db: AsyncSession,
    items: list[dict[str, Any]],
    updated_by: Optional[str] = None,
) -> dict[str, Any]:
    """
    工程別稼働日を一括 upsert。
    working_days が None の場合は上書きを削除（共通デフォルトに戻す）。
    """
    if not items:
        return await list_working_days_bundle(db)

    pcs = {(it.get("process_cd") or "").strip() for it in items if it.get("process_cd")}
    name_by_cd: dict[str, str] = {}
    if pcs:
        procs = (
            await db.execute(select(Process).where(Process.process_cd.in_(list(pcs))))
        ).scalars().all()
        name_by_cd = {
            p.process_cd: (p.process_name or p.process_cd or "").strip() for p in procs
        }

    keys = {
        (int(it["year"]), int(it["month"]), (it.get("process_cd") or "").strip())
        for it in items
        if (it.get("process_cd") or "").strip()
    }
    if not keys:
        return await list_working_days_bundle(db)

    existing_res = await db.execute(
        select(BudgetProcessWorkingDays).where(
            or_(
                *[
                    and_(
                        BudgetProcessWorkingDays.year == y,
                        BudgetProcessWorkingDays.month == m,
                        BudgetProcessWorkingDays.process_cd == pc,
                    )
                    for y, m, pc in keys
                ]
            )
        )
    )
    existing_map = {
        (int(r.year), int(r.month), (r.process_cd or "").strip()): r
        for r in existing_res.scalars().all()
    }

    for it in items:
        pc = (it.get("process_cd") or "").strip()
        if not pc:
            raise ValueError("工程CDは必須です")
        y, m = int(it["year"]), int(it["month"])
        if m < 1 or m > 12:
            raise ValueError(f"不正な月です: {y}/{m}")
        pname = (it.get("process_name") or name_by_cd.get(pc) or pc).strip()
        remark = it.get("remark")
        raw_days = it.get("working_days", None)
        key = (y, m, pc)
        row = existing_map.get(key)

        # None → 上書き削除（デフォルトに戻す）
        if raw_days is None:
            if row is not None:
                await db.delete(row)
                existing_map.pop(key, None)
            continue

        days = int(raw_days)
        if days < 0 or days > 31:
            raise ValueError(f"稼働日数は 0〜31 で指定してください: {y}/{m} {pc}")

        if row:
            row.working_days = days
            row.process_name = pname
            row.updated_by = updated_by
            if remark is not None:
                row.remark = str(remark)[:255] if remark else None
        else:
            row = BudgetProcessWorkingDays(
                year=y,
                month=m,
                process_cd=pc,
                process_name=pname,
                working_days=days,
                remark=str(remark)[:255] if remark else None,
                updated_by=updated_by,
            )
            db.add(row)
            existing_map[key] = row

    await db.commit()
    return await list_working_days_bundle(db)


async def analyze_monthly_trend_raw(
    db: AsyncSession, year: Optional[int] = None
) -> list[dict[str, Any]]:
    """稼働日マージ前の月次集計"""
    q = select(
        BudgetMonthly.year,
        BudgetMonthly.month,
        func.count().label("product_count"),
        func.coalesce(func.sum(BudgetMonthly.budget_qty), 0).label("total_qty"),
        func.coalesce(
            func.sum(case((BudgetMonthly.match_status != "unmatched", 1), else_=0)), 0
        ).label("matched"),
    ).group_by(BudgetMonthly.year, BudgetMonthly.month)
    if year is not None:
        q = q.where(BudgetMonthly.year == year)
    q = q.order_by(BudgetMonthly.year.asc(), BudgetMonthly.month.asc())
    rows = (await db.execute(q)).all()
    return [
        {
            "year": int(r.year),
            "month": int(r.month),
            "label": f"{int(r.year)}/{int(r.month):02d}",
            "product_count": int(r.product_count or 0),
            "total_budget_qty": int(r.total_qty or 0),
            "matched_count": int(r.matched or 0),
        }
        for r in rows
    ]


async def upsert_working_days(
    db: AsyncSession,
    items: list[dict[str, Any]],
    updated_by: Optional[str] = None,
) -> list[dict[str, Any]]:
    """年月ごとの稼働日数を一括 upsert"""
    if not items:
        return []

    keys = {(int(it["year"]), int(it["month"])) for it in items}
    existing_res = await db.execute(
        select(BudgetWorkingDays).where(
            or_(
                *[
                    and_(BudgetWorkingDays.year == y, BudgetWorkingDays.month == m)
                    for y, m in keys
                ]
            )
        )
    )
    existing_map = {
        (int(r.year), int(r.month)): r for r in existing_res.scalars().all()
    }

    for it in items:
        y, m = int(it["year"]), int(it["month"])
        if m < 1 or m > 12:
            raise ValueError(f"不正な月です: {y}/{m}")
        days = int(it.get("working_days") or 0)
        if days < 0 or days > 31:
            raise ValueError(f"稼働日数は 0〜31 で指定してください: {y}/{m}")
        remark = it.get("remark")
        row = existing_map.get((y, m))
        if row:
            row.working_days = days
            row.updated_by = updated_by
            if remark is not None:
                row.remark = str(remark)[:255] if remark else None
        else:
            row = BudgetWorkingDays(
                year=y,
                month=m,
                working_days=days,
                remark=str(remark)[:255] if remark else None,
                updated_by=updated_by,
            )
            db.add(row)
            existing_map[(y, m)] = row

    await db.commit()
    return await list_working_days(db)


async def analyze_monthly_trend(
    db: AsyncSession, year: Optional[int] = None
) -> list[dict[str, Any]]:
    """年月別の予算合計推移（稼働日・日平均付き）"""
    rows = await analyze_monthly_trend_raw(db, year)
    wd_map = await get_working_days_map(db, year)
    for r in rows:
        days = wd_map.get((r["year"], r["month"]))
        r["working_days"] = days if days is not None else 0
        r["avg_daily_qty"] = _avg_daily(r["total_budget_qty"], days if days else None)
    return rows


async def analyze_process_monthly_trend(
    db: AsyncSession, year: Optional[int] = None
) -> dict[str, Any]:
    """
    工程別の予算数量月次推移。
    製品が工程ルートに含む工程ごとに、該当年月の予算数量を合算する
    （同一製品×同一工程は1回のみ計上）。
    """
    months_q = (
        select(BudgetMonthly.year, BudgetMonthly.month)
        .where(BudgetMonthly.product_cd.isnot(None), BudgetMonthly.match_status != "unmatched")
        .group_by(BudgetMonthly.year, BudgetMonthly.month)
        .order_by(BudgetMonthly.year.asc(), BudgetMonthly.month.asc())
    )
    if year is not None:
        months_q = months_q.where(BudgetMonthly.year == year)
    month_rows = (await db.execute(months_q)).all()
    months = [
        {
            "year": int(r.year),
            "month": int(r.month),
            "label": f"{int(r.year)}/{int(r.month):02d}",
        }
        for r in month_rows
    ]
    if not months:
        return {"months": [], "processes": []}

    budget_q = select(BudgetMonthly).where(
        BudgetMonthly.product_cd.isnot(None),
        BudgetMonthly.match_status != "unmatched",
    )
    if year is not None:
        budget_q = budget_q.where(BudgetMonthly.year == year)
    budgets = (await db.execute(budget_q)).scalars().all()
    if not budgets:
        return {"months": months, "processes": []}

    # (year, month) -> {product_cd: qty}
    month_product_qty: dict[tuple[int, int], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    all_cds: set[str] = set()
    for b in budgets:
        pcd = (b.product_cd or "").strip()
        if not pcd:
            continue
        all_cds.add(pcd)
        month_product_qty[(int(b.year), int(b.month))][pcd] += int(b.budget_qty or 0)

    steps = (
        await db.execute(
            select(ProductRouteStep).where(ProductRouteStep.product_cd.in_(list(all_cds)))
        )
    ).scalars().all()

    # product -> unique process_cds
    product_processes: dict[str, set[str]] = defaultdict(set)
    process_cds: set[str] = set()
    for step in steps:
        pc = (step.process_cd or "").strip()
        pcd = (step.product_cd or "").strip()
        if not pc or not pcd:
            continue
        product_processes[pcd].add(pc)
        process_cds.add(pc)

    process_map: dict[str, Process] = {}
    if process_cds:
        procs = (
            await db.execute(select(Process).where(Process.process_cd.in_(list(process_cds))))
        ).scalars().all()
        process_map = {p.process_cd: p for p in procs}

    # 除外工程を落とす
    excluded_cds = {
        pc for pc in process_cds if _is_excluded_process(process_map.get(pc), pc)
    }
    process_cds = {pc for pc in process_cds if pc not in excluded_cds}
    for pcd, pcs in list(product_processes.items()):
        product_processes[pcd] = {pc for pc in pcs if pc not in excluded_cds}

    # process -> list of qty aligned with months
    process_series: dict[str, list[int]] = {pc: [] for pc in process_cds}
    for m in months:
        key = (m["year"], m["month"])
        pq = month_product_qty.get(key, {})
        month_totals: dict[str, int] = defaultdict(int)
        for pcd, qty in pq.items():
            for pc in product_processes.get(pcd, ()):
                month_totals[pc] += qty
        for pc in process_cds:
            process_series[pc].append(int(month_totals.get(pc, 0)))

    wd_map = await get_working_days_map(db, year)
    proc_wd_map = await get_process_working_days_map(db, year)
    for m in months:
        days = wd_map.get((m["year"], m["month"]))
        m["working_days"] = days if days is not None else 0

    processes: list[dict[str, Any]] = []
    for pc, series in process_series.items():
        total_qty = sum(series)
        if total_qty <= 0:
            continue
        p = process_map.get(pc)
        avg_series: list[Optional[int]] = []
        wd_series: list[int] = []
        override_flags: list[bool] = []
        for i, qty in enumerate(series):
            y, mo = months[i]["year"], months[i]["month"]
            days, is_override = _resolve_working_days(y, mo, pc, wd_map, proc_wd_map)
            wd_series.append(days)
            override_flags.append(is_override)
            avg_series.append(_avg_daily(qty, days if days else None))
        processes.append(
            {
                "process_cd": pc,
                "process_name": (p.process_name if p else pc) or pc,
                "is_outsource": int(p.is_outsource or 0) if p else 0,
                "series": series,
                "avg_daily_series": avg_series,
                "working_days_series": wd_series,
                "working_days_override_series": override_flags,
                "total_qty": total_qty,
            }
        )
    processes = _sort_process_items(processes, secondary_key="process_cd")
    return {"months": months, "processes": processes}


async def delete_month_data(db: AsyncSession, year: int, month: int) -> int:
    res = await db.execute(
        delete(BudgetMonthly).where(BudgetMonthly.year == year, BudgetMonthly.month == month)
    )
    await db.commit()
    return int(res.rowcount or 0)

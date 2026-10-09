"""現在能率：各工程の生産性（直近3ヶ月）を製品×設備で集計し、95% を書き込む。

総合能率は生産性分析と同じ口径（実績数量 ÷ 正味作業時間）。日別能率の単純平均ではない。
成形ライン名の末尾「号」（成型01号）は設備名（成型01）に合わせて除く。
検査は設備列が無いため検査員を設備として扱う（machine_cd = INSP-<社員番号>、設備名 = 氏名）。
メッキは製品・設備の単位で実績が無いため集計対象外で、既存行も更新しない。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from sqlalchemy import bindparam, case, func, literal, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import EquipmentEfficiency

CURRENT_RATE_FACTOR = Decimal("0.95")
_ONE = Decimal("0.1")

INSPECTOR_CD_PREFIX = "INSP-"

# equipment_efficiency の列長
_MACHINE_CD_LEN = 20
_MACHINES_NAME_LEN = 50
_PRODUCT_CD_LEN = 20
_PRODUCT_NAME_LEN = 50

PROCESS_LABELS: Dict[str, str] = {
    "cutting": "切断",
    "chamfering": "面取",
    "forming": "成型",
    "welding": "溶接",
    "inspection": "検査",
}
IGNORED_PROCESS_LABELS = ["メッキ"]


def process_type_expr():
    """設備能率の工程判定（タブ・工程別一覧と共通）。検査員行は machine_cd の接頭辞で判定。"""
    mn = func.lower(func.coalesce(EquipmentEfficiency.machines_name, ""))
    mc = func.lower(func.coalesce(EquipmentEfficiency.machine_cd, ""))
    return case(
        (mc.like(f"{INSPECTOR_CD_PREFIX.lower()}%"), literal("inspection")),
        (or_(mn.like("%面取%"), mn.like("%chamfer%"), mc.like("%chamfer%")), literal("chamfering")),
        (or_(mn.like("%成型%"), mn.like("%forming%"), mc.like("%forming%")), literal("forming")),
        (or_(mn.like("%溶接%"), mn.like("%welding%"), mc.like("%welding%")), literal("welding")),
        (
            or_(
                mn.like("%メッキ%"),
                mn.like("%plating%"),
                mc.like("%plating%"),
                mc.like("%pl%"),
            ),
            literal("plating"),
        ),
        (
            or_(mn.like("%検査%"), mn.like("%inspection%"), mc.like("%inspection%")),
            literal("inspection"),
        ),
        (or_(mn.like("%切断%"), mn.like("%cutting%"), mc.like("%cutting%")), literal("cutting")),
        else_=literal("other"),
    )


# (工程キー, 集計SQL)。qty>0 かつ hours>0 の行だけを分子・分母に入れる。
_INDICATOR_SQL: Tuple[Tuple[str, str], ...] = (
    (
        "cutting",
        """
        SELECT line_name, product_cd, MAX(product_name) AS product_name,
               SUM(qty) AS qty, SUM(hours) AS hours, COUNT(*) AS cnt
        FROM (
            SELECT TRIM(production_line) AS line_name,
                   TRIM(product_cd) AS product_cd,
                   product_name,
                   IFNULL(actual_quantity, 0) AS qty,
                   IFNULL(work_hours, 0) AS hours
            FROM cutting_production_indicator
            WHERE production_day >= :start_date AND production_day <= :end_date
        ) t
        WHERE qty > 0 AND hours > 0 AND line_name <> '' AND product_cd <> ''
        GROUP BY line_name, product_cd
        """,
    ),
    (
        "chamfering",
        """
        SELECT line_name, product_cd, MAX(product_name) AS product_name,
               SUM(qty) AS qty, SUM(hours) AS hours, COUNT(*) AS cnt
        FROM (
            SELECT TRIM(production_line) AS line_name,
                   TRIM(product_cd) AS product_cd,
                   product_name,
                   CASE
                       WHEN IFNULL(total_production_qty, 0) > 0 THEN total_production_qty
                       ELSE IFNULL(chamfer_actual_quantity, 0) + IFNULL(sw_actual_quantity, 0)
                   END AS qty,
                   IFNULL(work_hours, 0) AS hours
            FROM chamfering_production_indicator
            WHERE production_day >= :start_date AND production_day <= :end_date
        ) t
        WHERE qty > 0 AND hours > 0 AND line_name <> '' AND product_cd <> ''
        GROUP BY line_name, product_cd
        """,
    ),
    (
        "forming",
        """
        SELECT line_name, product_cd, MAX(product_name) AS product_name,
               SUM(qty) AS qty, SUM(hours) AS hours, COUNT(*) AS cnt
        FROM (
            SELECT TRIM(production_line) AS line_name,
                   TRIM(product_cd) AS product_cd,
                   product_name,
                   IFNULL(actual_quantity, 0) AS qty,
                   IFNULL(work_hours, 0) AS hours
            FROM forming_production_indicator
            WHERE production_day >= :start_date AND production_day <= :end_date
        ) t
        WHERE qty > 0 AND hours > 0 AND line_name <> '' AND product_cd <> ''
        GROUP BY line_name, product_cd
        """,
    ),
)

_WELDING_SQL = """
SELECT line_name, product_cd, MAX(product_name) AS product_name,
       SUM(qty) AS qty, SUM(sec) AS sec, COUNT(*) AS cnt
FROM (
    SELECT TRIM(welding_machine) AS line_name,
           TRIM(product_cd) AS product_cd,
           product_name,
           IFNULL(actual_production_quantity, 0) AS qty,
           IFNULL(mes_net_production_sec, 0) AS sec
    FROM welding_management
    WHERE production_day >= :start_date AND production_day <= :end_date
      AND production_completed_check = 1
) t
WHERE qty > 0 AND sec > 0 AND line_name <> '' AND product_cd <> ''
GROUP BY line_name, product_cd
"""

# 正味秒は検査生産性分析と同じく mes_net_production_sec 優先、無ければ開始〜終了。
_INSPECTION_SQL = """
SELECT inspector_code, MAX(inspector_name) AS inspector_name, product_cd,
       MAX(product_name) AS product_name,
       SUM(qty) AS qty, SUM(sec) AS sec, COUNT(*) AS cnt
FROM (
    SELECT TRIM(u.username) AS inspector_code,
           COALESCE(NULLIF(TRIM(u.full_name), ''), TRIM(u.username)) AS inspector_name,
           TRIM(im.product_cd) AS product_cd,
           im.product_name,
           IFNULL(im.actual_production_quantity, 0) AS qty,
           CASE
               WHEN im.mes_net_production_sec IS NOT NULL THEN im.mes_net_production_sec
               WHEN im.mes_production_started_at IS NOT NULL
                    AND im.mes_production_ended_at IS NOT NULL
                   THEN TIMESTAMPDIFF(SECOND, im.mes_production_started_at,
                                      im.mes_production_ended_at)
               ELSE 0
           END AS sec
    FROM inspection_management im
    JOIN users u ON u.id = im.mes_inspector_user_id
    WHERE im.production_day >= :start_date AND im.production_day <= :end_date
      AND im.production_completed_check = 1
) t
WHERE qty > 0 AND sec > 0 AND product_cd <> '' AND inspector_code <> ''
GROUP BY inspector_code, product_cd
"""


def current_rate_period(today: Optional[date] = None) -> Tuple[date, date]:
    """当月を含む直近3カレンダー月。例: 2026-10-09 → 2026-08-01 〜 2026-10-09。"""
    today = today or date.today()
    index = today.year * 12 + (today.month - 1) - 2
    start = date(index // 12, index % 12 + 1, 1)
    return start, today


def normalize_equipment_name(name: Optional[str]) -> str:
    text_name = (name or "").strip()
    if text_name.endswith("号"):
        text_name = text_name[:-1].strip()
    return text_name


def _name_key(name: Optional[str]) -> str:
    n = normalize_equipment_name(name)
    return f"name:{n}" if n else ""


def _cd_key(machine_cd: Optional[str]) -> str:
    cd = (machine_cd or "").strip()
    return f"cd:{cd}" if cd else ""


def _rate_from_qty_hours(qty: int, hours: Decimal) -> Optional[Decimal]:
    if qty <= 0 or hours <= 0:
        return None
    raw = (Decimal(qty) / hours) * CURRENT_RATE_FACTOR
    return raw.quantize(_ONE, rounding=ROUND_HALF_UP)


@dataclass
class _Bucket:
    process: str
    equipment_name: str
    machine_cd: Optional[str] = None
    product_name: str = ""
    qty: int = 0
    hours: Decimal = field(default_factory=lambda: Decimal(0))
    record_count: int = 0

    @property
    def rate(self) -> Optional[Decimal]:
        return _rate_from_qty_hours(self.qty, self.hours)


@dataclass
class _Aggregation:
    period_from: date
    period_to: date
    buckets: Dict[Tuple[str, str], _Bucket] = field(default_factory=dict)
    processes_used: List[str] = field(default_factory=list)
    processes_skipped: List[str] = field(default_factory=list)

    def add(
        self,
        process: str,
        equipment_key: str,
        equipment_name: Optional[str],
        machine_cd: Optional[str],
        row: Dict[str, Any],
        hours: Decimal,
    ) -> None:
        product_cd = (row.get("product_cd") or "").strip()
        qty = int(row.get("qty") or 0)
        if not equipment_key or not product_cd or qty <= 0 or hours <= 0:
            return
        key = (equipment_key, product_cd)
        bucket = self.buckets.get(key)
        if bucket is None:
            bucket = _Bucket(
                process=process,
                equipment_name=(equipment_name or "").strip(),
                machine_cd=machine_cd,
            )
            self.buckets[key] = bucket
        product_name = row.get("product_name")
        if not bucket.product_name and product_name:
            bucket.product_name = str(product_name).strip()
        bucket.qty += qty
        bucket.hours += hours
        bucket.record_count += int(row.get("cnt") or 0)


async def _fetch(db: AsyncSession, sql: str, params: Dict[str, Any]) -> Optional[list]:
    try:
        return list((await db.execute(text(sql), params)).mappings().all())
    except Exception:
        await db.rollback()
        return None


async def _aggregate_productivity(db: AsyncSession) -> _Aggregation:
    start, end = current_rate_period()
    agg = _Aggregation(period_from=start, period_to=end)
    params = {"start_date": start, "end_date": end}

    sources: List[Tuple[str, str]] = [*_INDICATOR_SQL, ("welding", _WELDING_SQL)]
    for process, sql in sources:
        rows = await _fetch(db, sql, params)
        if rows is None:
            agg.processes_skipped.append(process)
            continue
        agg.processes_used.append(process)
        for row in rows:
            if process == "welding":
                sec = Decimal(str(row.get("sec") or 0))
                hours = sec / Decimal(3600) if sec > 0 else Decimal(0)
            else:
                hours = Decimal(str(row.get("hours") or 0))
            line_name = row.get("line_name")
            agg.add(process, _name_key(line_name), line_name, None, row, hours)

    rows = await _fetch(db, _INSPECTION_SQL, params)
    if rows is None:
        agg.processes_skipped.append("inspection")
    else:
        agg.processes_used.append("inspection")
        for row in rows:
            code = (row.get("inspector_code") or "").strip()
            machine_cd = f"{INSPECTOR_CD_PREFIX}{code}" if code else ""
            sec = Decimal(str(row.get("sec") or 0))
            hours = sec / Decimal(3600) if sec > 0 else Decimal(0)
            agg.add(
                "inspection",
                _cd_key(machine_cd),
                row.get("inspector_name") or code,
                machine_cd,
                row,
                hours,
            )
    return agg


def _period_info(agg: _Aggregation) -> Dict[str, Any]:
    return {
        "period_from": agg.period_from.isoformat(),
        "period_to": agg.period_to.isoformat(),
        "factor": float(CURRENT_RATE_FACTOR),
        "sources": [PROCESS_LABELS[p] for p in agg.processes_used],
        "sources_skipped": [PROCESS_LABELS[p] for p in agg.processes_skipped],
        "excluded_processes": IGNORED_PROCESS_LABELS,
    }


def _lookup_bucket(
    agg: _Aggregation,
    process: str,
    machine_cd: Optional[str],
    machines_name: Optional[str],
    product_cd: str,
) -> Optional[_Bucket]:
    if process == "inspection":
        return agg.buckets.get((_cd_key(machine_cd), product_cd))
    return agg.buckets.get((_name_key(machines_name), product_cd))


async def refresh_current_efficiency_rates(db: AsyncSession) -> Dict[str, Any]:
    """equipment_efficiency.current_efficiency_rate を一括更新する。能率は変えない。

    集計できた工程の行だけを更新し、メッキ等の対象外工程は現在能率に触れない。
    """
    agg = await _aggregate_productivity(db)
    target = set(agg.processes_used)
    rows = (
        await db.execute(
            select(
                EquipmentEfficiency.id,
                EquipmentEfficiency.machine_cd,
                EquipmentEfficiency.machines_name,
                EquipmentEfficiency.product_cd,
                process_type_expr().label("process_type"),
            )
        )
    ).all()
    now = datetime.now().replace(microsecond=0)
    updated = 0
    cleared = 0
    skipped = 0
    for row_id, m_cd, m_name, p_cd, process in rows:
        process = str(process or "other")
        if process not in target:
            skipped += 1
            continue
        bucket = _lookup_bucket(agg, process, m_cd, m_name, (p_cd or "").strip())
        rate = bucket.rate if bucket else None
        await db.execute(
            text(
                """
                UPDATE equipment_efficiency
                SET current_efficiency_rate = :rate,
                    current_efficiency_updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {"rate": rate, "updated_at": now, "id": row_id},
        )
        if rate is None:
            cleared += 1
        else:
            updated += 1
    await db.commit()
    return {**_period_info(agg), "updated": updated, "cleared": cleared, "skipped": skipped}


async def _machine_index(db: AsyncSession) -> Dict[str, Tuple[str, str]]:
    """name:正規化設備名 → (machine_cd, machine_name)"""
    rows = (await db.execute(text("SELECT machine_cd, machine_name FROM machines"))).all()
    index: Dict[str, Tuple[str, str]] = {}
    for m_cd, m_name in rows:
        key = _name_key(m_name)
        if key and m_cd and key not in index:
            index[key] = (str(m_cd).strip(), str(m_name).strip())
    return index


async def _existing_keys(db: AsyncSession) -> Set[Tuple[str, str]]:
    """登録済みの (cd:machine_cd, product_cd) と (name:正規化設備名, product_cd)"""
    rows = (
        await db.execute(
            text("SELECT machine_cd, machines_name, product_cd FROM equipment_efficiency")
        )
    ).all()
    keys: Set[Tuple[str, str]] = set()
    for m_cd, m_name, p_cd in rows:
        pc = (p_cd or "").strip()
        if not pc:
            continue
        if m_cd:
            keys.add((_cd_key(m_cd), pc))
        if m_name:
            keys.add((_name_key(m_name), pc))
    return keys


async def _product_names(db: AsyncSession, product_cds: Iterable[str]) -> Dict[str, str]:
    cds = sorted({cd for cd in product_cds if cd})
    if not cds:
        return {}
    stmt = text(
        "SELECT product_cd, product_name FROM products WHERE product_cd IN :cds"
    ).bindparams(bindparam("cds", expanding=True))
    rows = (await db.execute(stmt, {"cds": cds})).all()
    return {str(cd): str(name or "") for cd, name in rows}


async def find_missing_from_productivity(db: AsyncSession) -> Dict[str, Any]:
    """生産性にあって設備能率に未登録の 設備（検査は検査員）×製品 を列挙する。"""
    agg = await _aggregate_productivity(db)
    machines = await _machine_index(db)
    existing = await _existing_keys(db)
    product_names = await _product_names(db, (k[1] for k in agg.buckets))

    candidates: List[Dict[str, Any]] = []
    unmatched: Dict[Tuple[str, str], int] = {}
    unknown_products: Set[str] = set()
    for (equipment_key, product_cd), bucket in agg.buckets.items():
        rate = bucket.rate
        if rate is None:
            continue
        if product_cd not in product_names:
            unknown_products.add(product_cd)
            continue
        if bucket.machine_cd:
            machine_cd, machine_name = bucket.machine_cd, bucket.equipment_name
            if (_cd_key(machine_cd), product_cd) in existing:
                continue
        else:
            machine = machines.get(equipment_key)
            if machine is None:
                ukey = (PROCESS_LABELS[bucket.process], bucket.equipment_name)
                unmatched[ukey] = unmatched.get(ukey, 0) + 1
                continue
            machine_cd, machine_name = machine
            if (_cd_key(machine_cd), product_cd) in existing or (
                equipment_key,
                product_cd,
            ) in existing:
                continue
        if len(machine_cd) > _MACHINE_CD_LEN or len(product_cd) > _PRODUCT_CD_LEN:
            continue
        candidates.append(
            {
                "process": PROCESS_LABELS[bucket.process],
                "machine_cd": machine_cd,
                "machines_name": machine_name,
                "product_cd": product_cd,
                "product_name": product_names[product_cd] or bucket.product_name,
                "actual_qty": bucket.qty,
                "work_hours": float(bucket.hours.quantize(Decimal("0.01"))),
                "record_count": bucket.record_count,
                "efficiency_rate": float(rate),
            }
        )
    candidates.sort(
        key=lambda c: (c["process"], c["machines_name"], c["product_name"] or "", c["product_cd"])
    )
    return {
        **_period_info(agg),
        "candidates": candidates,
        "unknown_product_cds": sorted(unknown_products),
        "unmatched_lines": [
            {"process": p, "line_name": n, "product_count": c}
            for (p, n), c in sorted(unmatched.items())
        ],
    }


async def _default_step_times(db: AsyncSession) -> Dict[str, int]:
    """設備ごとに最も多く使われている段取時間"""
    rows = (
        await db.execute(
            text(
                "SELECT machine_cd, step_time FROM equipment_efficiency "
                "WHERE machine_cd IS NOT NULL AND step_time IS NOT NULL"
            )
        )
    ).all()
    counters: Dict[str, Counter] = {}
    for m_cd, step in rows:
        counters.setdefault(str(m_cd).strip(), Counter())[int(step)] += 1
    return {cd: c.most_common(1)[0][0] for cd, c in counters.items() if c}


async def add_missing_from_productivity(
    db: AsyncSession, selected: Optional[List[Tuple[str, str]]] = None
) -> Dict[str, Any]:
    """未登録の組み合わせを追加する。能率・現在能率ともに算出値を入れる。

    selected が None のときは全候補、指定時は (machine_cd, product_cd) が一致する候補のみ。
    """
    found = await find_missing_from_productivity(db)
    candidates = found["candidates"]
    if selected is not None:
        wanted = {(m.strip(), p.strip()) for m, p in selected}
        candidates = [c for c in candidates if (c["machine_cd"], c["product_cd"]) in wanted]

    step_times = await _default_step_times(db)
    now = datetime.now().replace(microsecond=0)
    for c in candidates:
        await db.execute(
            text(
                """
                INSERT INTO equipment_efficiency (
                    machine_cd, machines_name, product_cd, product_name,
                    efficiency_rate, current_efficiency_rate, current_efficiency_updated_at,
                    step_time, unit, remarks, status, created_at, updated_at
                ) VALUES (
                    :machine_cd, :machines_name, :product_cd, :product_name,
                    :rate, :rate, :now,
                    :step_time, '', :remarks, 1, :now, :now
                )
                """
            ),
            {
                "machine_cd": c["machine_cd"],
                "machines_name": (c["machines_name"] or "")[:_MACHINES_NAME_LEN],
                "product_cd": c["product_cd"],
                "product_name": (c["product_name"] or "")[:_PRODUCT_NAME_LEN],
                "rate": c["efficiency_rate"],
                "now": now,
                "step_time": step_times.get(c["machine_cd"]),
                "remarks": f"生産性より自動追加（{found['period_from']}〜{found['period_to']}）",
            },
        )
    await db.commit()
    return {
        "period_from": found["period_from"],
        "period_to": found["period_to"],
        "added": len(candidates),
    }

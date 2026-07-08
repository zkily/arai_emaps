"""
製品ラベル（現品票）共通ロジック：成型設備・成型后工程の導出
"""
from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import (
    EquipmentEfficiency,
    Machine,
    Process,
    Product,
    ProductLabelConfig,
    ProductRouteStep,
)

FORMING_PROCESS_CD = "KT04"
TOP_ROW_FIXED_COL4 = "手直し"
PRINT_COLUMNS = 4
PROCESS_SLOT_COUNT = 8
MOLDING_EQUIPMENT_SLOT_COUNT = 3
POST_MOLDING_SLOT_COUNT = 4
UPPER_SLOT_PRESERVE_COUNT = 4

EXCLUDED_PROCESS_NAMES: frozenset[str] = frozenset(
    {
        "外注メッキ",
        "外注溶接",
        "外注検査",
        "倉庫",
        "外注倉庫",
        "外注支給前",
        "外注検査前",
    }
)

PROCESS_SLOT_FIELDS = tuple(f"process_slot_{i}" for i in range(1, PROCESS_SLOT_COUNT + 1))


def is_molding_label_target_product_cd(product_cd: str | None) -> bool:
    """成型用ラベル対象：製品CDの末尾が '1'。"""
    cd = (product_cd or "").strip()
    return bool(cd) and cd[-1] == "1"


def format_machine_short(name: str | None) -> str:
    if not name:
        return ""
    text = str(name).strip()
    m = re.search(r"(\d+)\s*号", text)
    if m:
        return f"{m.group(1)}号"
    return text


def is_excluded_process_name(process_name: str | None) -> bool:
    if not process_name:
        return True
    name = str(process_name).strip()
    if not name:
        return True
    if name in EXCLUDED_PROCESS_NAMES:
        return True
    for excluded in EXCLUDED_PROCESS_NAMES:
        if excluded in name:
            return True
    return False


def config_process_slots(config: ProductLabelConfig | None) -> list[str | None]:
    if not config:
        return [None] * PROCESS_SLOT_COUNT
    return [getattr(config, field) or None for field in PROCESS_SLOT_FIELDS]


def set_config_process_slots(config: ProductLabelConfig, slots: list[str | None]) -> None:
    for idx, field in enumerate(PROCESS_SLOT_FIELDS):
        value = slots[idx] if idx < len(slots) else None
        setattr(config, field, (value.strip() if value else None) or None)


def merge_derived_slots_preserving_upper(
    existing: list[str | None] | None,
    derived: list[str | None],
    upper_locked: bool,
) -> list[str | None]:
    """枠導出結果を反映。upper_locked 時は枠1-4（上段）を既存値で維持。"""
    result = list(derived)
    while len(result) < PROCESS_SLOT_COUNT:
        result.append(None)
    if not upper_locked or not existing:
        return result[:PROCESS_SLOT_COUNT]
    for i in range(UPPER_SLOT_PRESERVE_COUNT):
        if i < len(existing):
            result[i] = existing[i]
    return result[:PROCESS_SLOT_COUNT]


async def apply_derived_slots_to_config(
    db: AsyncSession,
    row: ProductLabelConfig,
    product_cd: str,
) -> bool:
    """工程・設備から8枠を導出して行に反映。戻り値=上段を保護したか。"""
    existing = config_process_slots(row)
    derived = await derive_label_process_slots(db, product_cd)
    locked = bool(getattr(row, "upper_slots_locked", False))
    merged = merge_derived_slots_preserving_upper(existing, derived, locked)
    set_config_process_slots(row, merged)
    return locked


def config_to_dict(row: ProductLabelConfig, master_product_name: str = "") -> dict:
    slots = config_process_slots(row)
    return {
        "id": row.id,
        "product_cd": row.product_cd,
        "master_product_name": master_product_name,
        "label_product_name": row.label_product_name,
        "process_unit_qty": row.process_unit_qty,
        "process_slots": slots,
        **{field: slots[i] for i, field in enumerate(PROCESS_SLOT_FIELDS)},
        "paper_color": row.paper_color,
        "product_name_color": row.product_name_color or "#000000",
        "upper_slots_locked": bool(getattr(row, "upper_slots_locked", False)),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


async def derive_post_molding_process_names(db: AsyncSession, product_cd: str) -> list[str | None]:
    """成型工程（KT04）以降の工程名を最大4件導出（枠5-8、最終工程を枠8に右寄せ）。"""
    product = await _get_product(db, product_cd)
    if not product or not product.route_cd:
        return [None] * POST_MOLDING_SLOT_COUNT

    route_cd = product.route_cd
    q = (
        select(ProductRouteStep, Process.process_name)
        .outerjoin(Process, Process.process_cd == ProductRouteStep.process_cd)
        .where(
            ProductRouteStep.product_cd == product_cd,
            ProductRouteStep.route_cd == route_cd,
        )
        .order_by(ProductRouteStep.step_no)
    )
    res = await db.execute(q)
    rows = res.all()

    molding_idx: int | None = None
    for i, (step, _process_name) in enumerate(rows):
        if (step.process_cd or "").strip() == FORMING_PROCESS_CD:
            molding_idx = i
            break

    if molding_idx is None:
        return [None] * POST_MOLDING_SLOT_COUNT

    processes: list[str] = []
    for step, process_name in rows[molding_idx + 1 :]:
        name = (process_name or step.process_cd or "").strip()
        if is_excluded_process_name(name):
            continue
        processes.append(name)
        if len(processes) >= POST_MOLDING_SLOT_COUNT:
            break

    result: list[str | None] = [None] * POST_MOLDING_SLOT_COUNT
    if not processes:
        return result

    start = POST_MOLDING_SLOT_COUNT - len(processes)
    for i, name in enumerate(processes):
        result[start + i] = name
    return result


async def resolve_molding_equipment_from_efficiency(db: AsyncSession, product_cd: str) -> list[str]:
    """equipment_efficiency から成型工程で使用可能な設備短称（最大3件）。"""
    ee_q = (
        select(EquipmentEfficiency.machines_name, EquipmentEfficiency.machine_cd)
        .where(EquipmentEfficiency.product_cd == product_cd)
        .where(or_(EquipmentEfficiency.status.is_(None), EquipmentEfficiency.status == 1))
        .order_by(EquipmentEfficiency.machine_cd)
    )
    ee_res = await db.execute(ee_q)
    ee_rows = ee_res.all()
    if not ee_rows:
        return []

    names: list[str] = []
    seen: set[str] = set()

    machine_cds = {str(r[1]).strip() for r in ee_rows if r[1]}
    forming_cds: set[str] = set()
    if machine_cds:
        m_q = select(Machine.machine_cd, Machine.machine_name, Machine.machine_type).where(
            Machine.machine_cd.in_(machine_cds)
        )
        m_res = await db.execute(m_q)
        for machine_cd, machine_name, machine_type in m_res.all():
            mt = (machine_type or "").lower()
            mn = (machine_name or "").lower()
            if "成型" in (machine_type or "") or "forming" in mt or "成型" in mn:
                forming_cds.add(str(machine_cd).strip())

    for machines_name, machine_cd in ee_rows:
        cd = str(machine_cd or "").strip()
        if forming_cds and cd not in forming_cds:
            continue
        short = format_machine_short(machines_name or cd)
        if not short or short in seen:
            continue
        seen.add(short)
        names.append(short)
        if len(names) >= MOLDING_EQUIPMENT_SLOT_COUNT:
            break

    if not names:
        seen.clear()
        for machines_name, machine_cd in ee_rows:
            short = format_machine_short(machines_name or machine_cd)
            if not short or short in seen:
                continue
            seen.add(short)
            names.append(short)
            if len(names) >= MOLDING_EQUIPMENT_SLOT_COUNT:
                break

    return names[:MOLDING_EQUIPMENT_SLOT_COUNT]


async def derive_label_process_slots(db: AsyncSession, product_cd: str) -> list[str | None]:
    """枠1-3: 成型設備、枠4: 手直し、枠5-8: 成型後工程。"""
    machines = await resolve_molding_equipment_from_efficiency(db, product_cd)
    post_molding = await derive_post_molding_process_names(db, product_cd)

    slots: list[str | None] = [None] * PROCESS_SLOT_COUNT
    for i in range(min(MOLDING_EQUIPMENT_SLOT_COUNT, len(machines))):
        slots[i] = machines[i]
    slots[3] = TOP_ROW_FIXED_COL4
    for i in range(POST_MOLDING_SLOT_COUNT):
        slots[4 + i] = post_molding[i]
    return slots


async def build_label_preview(db: AsyncSession, product_cd: str) -> dict:
    product = await _get_product(db, product_cd)
    if not product:
        raise ValueError("製品が見つかりません")

    config_res = await db.execute(
        select(ProductLabelConfig).where(ProductLabelConfig.product_cd == product_cd)
    )
    config = config_res.scalar_one_or_none()

    process_slots = config_process_slots(config)
    if config is None or all(slot is None for slot in process_slots):
        process_slots = await derive_label_process_slots(db, product_cd)

    top_row = {
        "machine_1": process_slots[0] or "",
        "machine_2": process_slots[1] or "",
        "machine_3": process_slots[2] or "",
        "machine_4_fixed": process_slots[3] or TOP_ROW_FIXED_COL4,
    }

    label_name = (config.label_product_name if config else None) or product.product_name

    return {
        "product_cd": product.product_cd,
        "master_product_name": product.product_name,
        "label_product_name": label_name,
        "process_unit_qty": config.process_unit_qty if config else None,
        "paper_color": (config.paper_color if config else None) or "白",
        "product_name_color": (config.product_name_color if config else None) or "#000000",
        "top_row": top_row,
        "process_slots": process_slots,
        "print_columns": PRINT_COLUMNS,
        "config_id": config.id if config else None,
    }


async def build_prefill_from_product(db: AsyncSession, product_cd: str) -> dict:
    """製品マスタから成型用ラベル設定の初期値を生成。"""
    product = await _get_product(db, product_cd)
    if not product:
        raise ValueError("製品が見つかりません")

    alias = (product.product_alias or "").strip()
    label_name = alias or product.product_name or ""
    lot_size = int(product.lot_size) if product.lot_size is not None and int(product.lot_size) > 0 else None
    slots = await derive_label_process_slots(db, product_cd)

    return {
        "product_cd": product.product_cd,
        "master_product_name": product.product_name or "",
        "product_alias": alias or None,
        "route_cd": product.route_cd,
        "lot_size": lot_size,
        "unit_per_box": int(product.unit_per_box) if product.unit_per_box is not None else None,
        "label_product_name": label_name,
        "process_unit_qty": None,
        "process_slots": slots,
        "paper_color": "白",
        "product_name_color": "#000000",
    }


async def apply_product_master_to_config(row: ProductLabelConfig, product: Product) -> None:
    """製品マスタの値を設定行へ反映（入数は手動入力のためマスタからは設定しない）。"""
    alias = (product.product_alias or "").strip()
    row.label_product_name = alias or product.product_name or row.label_product_name
    if not row.paper_color:
        row.paper_color = "白"
    if not row.product_name_color:
        row.product_name_color = "#000000"


async def _get_product(db: AsyncSession, product_cd: str) -> Product | None:
    res = await db.execute(select(Product).where(Product.product_cd == product_cd))
    return res.scalar_one_or_none()

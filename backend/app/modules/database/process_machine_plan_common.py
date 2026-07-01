"""工程別設備別計画：API と調整ロジックの共有定義。"""
from __future__ import annotations

from typing import Optional

# 工程定義：(key, ラベル, 設備列, 計画列, 実績列, 実計列, 不良列, 廃棄列)
PROCESS_DEFS: list[dict[str, str]] = [
    {
        "key": "cutting",
        "label": "切断",
        "machine": "cutting_machine",
        "plan": "cutting_plan",
        "actual": "cutting_actual",
        "actual_plan": "cutting_actual_plan",
        "defect": "cutting_defect",
        "scrap": "cutting_scrap",
    },
    {
        "key": "chamfering",
        "label": "面取",
        "machine": "chamfering_machine",
        "plan": "chamfering_plan",
        "actual": "chamfering_actual",
        "actual_plan": "chamfering_actual_plan",
        "defect": "chamfering_defect",
        "scrap": "chamfering_scrap",
    },
    {
        "key": "sw",
        "label": "SW",
        "machine": "sw_machine",
        "plan": "sw_plan",
        "actual": None,
        "actual_plan": None,
        "defect": None,
        "scrap": None,
    },
    {
        "key": "molding",
        "label": "成型",
        "machine": "molding_machine",
        "plan": "molding_plan",
        "actual": "molding_actual",
        "actual_plan": "molding_actual_plan",
        "defect": "molding_defect",
        "scrap": "molding_scrap",
    },
    {
        "key": "welding",
        "label": "溶接",
        "machine": "welding_machine",
        "plan": "welding_plan",
        "actual": "welding_actual",
        "actual_plan": "welding_actual_plan",
        "defect": "welding_defect",
        "scrap": "welding_scrap",
    },
]

PROCESS_DEF_BY_KEY = {d["key"]: d for d in PROCESS_DEFS}
DEFAULT_PROCESS_KEYS = [d["key"] for d in PROCESS_DEFS]

UNSET_MACHINE_LABEL = "(設備未設定)"


def _round1(v: float) -> float:
    return round(v, 1)


def achievement_rate(plan: int, actual: int) -> Optional[float]:
    if plan <= 0:
        return None
    return _round1(actual / plan * 100.0)


def defect_rate(actual: int, defect: int, scrap: int) -> Optional[float]:
    base = actual + defect + scrap
    if base <= 0:
        return None
    return _round1((defect + scrap) / base * 100.0)


def empty_acc() -> dict:
    return {"plan": 0, "actual": 0, "actual_plan": 0, "defect": 0, "scrap": 0}


def build_metrics(acc: dict, days: int) -> dict:
    plan = acc["plan"]
    actual = acc["actual"]
    defect = acc["defect"]
    scrap = acc["scrap"]
    return {
        "plan": plan,
        "actual": actual,
        "actual_plan": acc["actual_plan"],
        "defect": defect,
        "scrap": scrap,
        "diff": actual - plan,
        "achievement_rate": achievement_rate(plan, actual),
        "defect_rate": defect_rate(actual, defect, scrap),
        "days": days,
    }

"""レポート生成器のレジストリ（report_code → 生成器）"""
from __future__ import annotations

from .base import GeneratedReport, ReportAttachment, ReportGenerator
from .cutting_actual import CuttingDailyActualGenerator
from .inventory_trend import InventoryTrendGenerator
from .plan_actual_compare import PlanActualCompareGenerator

_GENERATORS: dict[str, ReportGenerator] = {
    gen.report_code: gen
    for gen in (
        CuttingDailyActualGenerator(),
        InventoryTrendGenerator(),
        PlanActualCompareGenerator(),
    )
}


def get_generator(report_code: str) -> ReportGenerator | None:
    return _GENERATORS.get(report_code)


__all__ = [
    "GeneratedReport",
    "ReportAttachment",
    "ReportGenerator",
    "get_generator",
]

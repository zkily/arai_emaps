"""工程別設備別計画：設備合計ベースの計画調整（シミュレーションのみ）。"""
from __future__ import annotations

import copy
from typing import Any, Optional

from app.modules.database.process_machine_plan_common import (
    PROCESS_DEF_BY_KEY,
    UNSET_MACHINE_LABEL,
    achievement_rate as _achievement_rate,
    build_metrics as _build_metrics,
    defect_rate as _defect_rate,
    empty_acc as _empty_acc,
)


def _distribute_int(total: int, weights: list[float]) -> list[int]:
    if total <= 0 or not weights:
        return [0] * len(weights)
    wsum = sum(max(0.0, w) for w in weights)
    if wsum <= 0:
        return [0] * len(weights)
    raw = [total * max(0.0, w) / wsum for w in weights]
    floors = [int(x) for x in raw]
    remainder = total - sum(floors)
    if remainder > 0:
        order = sorted(range(len(weights)), key=lambda i: (raw[i] - floors[i], i), reverse=True)
        for i in range(remainder):
            floors[order[i % len(order)]] += 1
    return floors


def _refresh_row_metrics(row: dict) -> None:
    plan = int(row.get("plan") or 0)
    actual = int(row.get("actual") or 0)
    defect = int(row.get("defect") or 0)
    scrap = int(row.get("scrap") or 0)
    days = len(row.get("daily") or {})
    row["diff"] = actual - plan
    row["achievement_rate"] = _achievement_rate(plan, actual)
    row["defect_rate"] = _defect_rate(actual, defect, scrap)
    row["days"] = days


def _scale_row_plan_total(row: dict, new_plan: int) -> None:
    """設備合計 plan を new_plan にし、日別 plan を比例配分（合計0のときは日別均等）。"""
    old_plan = int(row.get("plan") or 0)
    new_plan = max(0, int(new_plan))
    daily: dict[str, dict] = row.setdefault("daily", {})

    if not daily:
        row["plan"] = new_plan
        _refresh_row_metrics(row)
        return

    if old_plan <= 0:
        dates = sorted(daily.keys())
        parts = _distribute_int(new_plan, [1.0] * len(dates))
        for d, p in zip(dates, parts):
            cell = daily.setdefault(d, {"plan": 0, "actual": 0, "diff": 0})
            cell["plan"] = p
            cell["diff"] = int(cell.get("actual") or 0) - p
    else:
        factor = new_plan / old_plan
        running = 0
        dates = sorted(daily.keys())
        for i, d in enumerate(dates):
            cell = daily[d]
            old_p = int(cell.get("plan") or 0)
            if i == len(dates) - 1:
                new_p = new_plan - running
            else:
                new_p = int(round(old_p * factor))
                running += new_p
            cell["plan"] = new_p
            cell["diff"] = int(cell.get("actual") or 0) - new_p

    row["plan"] = new_plan
    _refresh_row_metrics(row)


def _add_plan_to_row(row: dict, add_plan: int, add_daily: dict[str, int]) -> None:
    """既存行に計画を加算（未設定→設備配分用）。"""
    daily: dict[str, dict] = row.setdefault("daily", {})
    for d, p in add_daily.items():
        if p == 0:
            continue
        cell = daily.setdefault(d, {"plan": 0, "actual": 0, "diff": 0})
        cell["plan"] = int(cell.get("plan") or 0) + p
        cell["diff"] = int(cell.get("actual") or 0) - int(cell["plan"])
    row["plan"] = int(row.get("plan") or 0) + add_plan
    _refresh_row_metrics(row)


def _find_row(summary: list[dict], process_key: str, machine: str) -> Optional[dict]:
    for row in summary:
        if row.get("process_key") == process_key and row.get("machine") == machine:
            return row
    return None


def _ensure_row(
    summary: list[dict],
    process_key: str,
    process_label: str,
    machine: str,
    dates: list[str],
) -> dict:
    row = _find_row(summary, process_key, machine)
    if row:
        return row
    daily = {d: {"plan": 0, "actual": 0, "diff": 0} for d in dates}
    row = {
        "process_key": process_key,
        "process_label": process_label,
        "machine": machine,
        "plan": 0,
        "actual": 0,
        "actual_plan": 0,
        "defect": 0,
        "scrap": 0,
        "diff": 0,
        "achievement_rate": None,
        "defect_rate": None,
        "days": 0,
        "daily": daily,
    }
    summary.append(row)
    return row


def _rebuild_totals(data: dict, target_defs: list[dict]) -> None:
    summary: list[dict] = data.get("summary") or []
    grand_acc = _empty_acc()
    grand_days: set[str] = set()
    process_totals: dict[str, dict] = {}

    for d in target_defs:
        pk = d["key"]
        proc_rows = [r for r in summary if r.get("process_key") == pk]
        proc_acc = _empty_acc()
        proc_days: set[str] = set()
        for row in proc_rows:
            for k in proc_acc:
                proc_acc[k] += int(row.get(k) or 0)
            proc_days |= set((row.get("daily") or {}).keys())
        process_totals[pk] = {
            "process_key": pk,
            "process_label": d["label"],
            **_build_metrics(proc_acc, len(proc_days)),
        }
        for k in grand_acc:
            grand_acc[k] += proc_acc[k]
        grand_days |= proc_days

    data["processTotals"] = process_totals
    data["grandTotal"] = _build_metrics(grand_acc, len(grand_days))


def apply_adjust_rules(base_data: dict, rules: list[dict]) -> dict:
    """
    設備合計に対する調整ルールを適用したシミュレーション結果を返す。
    - allocate_unset: 設備未設定行の plan を人工重みで指定設備へ配分
    - adjust: 指定設備の plan 合計を % または +数量 で変更（日別は比例配分）
    """
    if not rules:
        return copy.deepcopy(base_data)

    data = copy.deepcopy(base_data)
    summary: list[dict] = data.get("summary") or []
    dates: list[str] = data.get("dates") or []
    processes = data.get("processes") or []
    label_by_key = {p["key"]: p["label"] for p in processes}

    enabled = [r for r in rules if r.get("enabled", True)]

    for rule in enabled:
        rtype = (rule.get("type") or "").strip()
        pk = (rule.get("process_key") or "").strip()
        if pk not in PROCESS_DEF_BY_KEY:
            continue
        label = label_by_key.get(pk) or PROCESS_DEF_BY_KEY[pk]["label"]

        if rtype == "allocate_unset":
            targets = rule.get("targets") or []
            if not targets:
                continue
            machines = [(t.get("machine") or "").strip() for t in targets]
            weights = [float(t.get("weight") or 0) for t in targets]
            if not any(machines):
                continue

            unset_row = _find_row(summary, pk, UNSET_MACHINE_LABEL)
            if not unset_row or int(unset_row.get("plan") or 0) <= 0:
                continue

            total_plan = int(unset_row.get("plan") or 0)
            plan_parts = _distribute_int(total_plan, weights)

            unset_daily = {
                d: int((unset_row.get("daily") or {}).get(d, {}).get("plan") or 0)
                for d in (unset_row.get("daily") or {})
            }
            all_dates = sorted(set(dates) | set(unset_daily.keys()))

            daily_by_machine: list[dict[str, int]] = []
            for d in all_dates:
                day_total = unset_daily.get(d, 0)
                day_parts = _distribute_int(day_total, weights)
                for i, m in enumerate(machines):
                    if not m:
                        continue
                    if len(daily_by_machine) <= i:
                        daily_by_machine.append({})
                    daily_by_machine[i][d] = daily_by_machine[i].get(d, 0) + day_parts[i]

            _scale_row_plan_total(unset_row, 0)

            for i, m in enumerate(machines):
                if not m:
                    continue
                target_row = _ensure_row(summary, pk, label, m, dates)
                _add_plan_to_row(target_row, plan_parts[i], daily_by_machine[i] if i < len(daily_by_machine) else {})

        elif rtype == "adjust":
            machine = (rule.get("machine") or "").strip()
            if not machine:
                continue
            row = _find_row(summary, pk, machine)
            if not row:
                continue
            old_plan = int(row.get("plan") or 0)
            mode = (rule.get("mode") or "percent").strip()
            try:
                value = float(rule.get("value") or 0)
            except (TypeError, ValueError):
                value = 0.0
            if mode == "delta":
                new_plan = old_plan + int(round(value))
            else:
                new_plan = int(round(old_plan * (1.0 + value / 100.0)))
            _scale_row_plan_total(row, new_plan)

    target_defs = [PROCESS_DEF_BY_KEY[p["key"]] for p in processes if p["key"] in PROCESS_DEF_BY_KEY]
    _rebuild_totals(data, target_defs)

    summary.sort(
        key=lambda r: (
            r.get("process_key") or "",
            r.get("machine") == UNSET_MACHINE_LABEL,
            r.get("machine") or "",
        )
    )
    data["summary"] = summary
    return data


def build_diff_plan_data(base: dict, adjusted: dict) -> dict:
    """原計画と調整後の差分（plan / daily.plan / diff 再計算）を返す。"""
    diff_data = copy.deepcopy(adjusted)
    base_map = {
        (r.get("process_key"), r.get("machine")): r for r in (base.get("summary") or [])
    }
    adj_summary = diff_data.get("summary") or []
    new_summary: list[dict] = []

    for row in adj_summary:
        key = (row.get("process_key"), row.get("machine"))
        base_row = base_map.get(key, {})
        base_plan = int(base_row.get("plan") or 0)
        adj_plan = int(row.get("plan") or 0)
        plan_delta = adj_plan - base_plan
        actual = int(row.get("actual") or 0)

        daily_diff: dict[str, dict] = {}
        all_dates = set((row.get("daily") or {}).keys()) | set((base_row.get("daily") or {}).keys())
        for d in sorted(all_dates):
            bp = int((base_row.get("daily") or {}).get(d, {}).get("plan") or 0)
            ap = int((row.get("daily") or {}).get(d, {}).get("plan") or 0)
            dp = ap - bp
            daily_diff[d] = {"plan": dp, "actual": 0, "diff": dp}

        new_row = copy.deepcopy(row)
        new_row["plan"] = plan_delta
        new_row["actual"] = 0
        new_row["actual_plan"] = 0
        new_row["defect"] = 0
        new_row["scrap"] = 0
        new_row["diff"] = plan_delta
        new_row["achievement_rate"] = None
        new_row["defect_rate"] = None
        new_row["daily"] = daily_diff
        new_summary.append(new_row)

    diff_data["summary"] = new_summary
    target_defs = [
        PROCESS_DEF_BY_KEY[p["key"]]
        for p in (diff_data.get("processes") or [])
        if p["key"] in PROCESS_DEF_BY_KEY
    ]
    _rebuild_totals(diff_data, target_defs)
    for k, pt in diff_data.get("processTotals", {}).items():
        pt["actual"] = 0
        pt["actual_plan"] = 0
        pt["defect"] = 0
        pt["scrap"] = 0
        pt["diff"] = pt.get("plan", 0)
        pt["achievement_rate"] = None
        pt["defect_rate"] = None
    gt = diff_data.get("grandTotal") or {}
    gt["actual"] = 0
    gt["actual_plan"] = 0
    gt["defect"] = 0
    gt["scrap"] = 0
    gt["diff"] = gt.get("plan", 0)
    gt["achievement_rate"] = None
    gt["defect_rate"] = None
    return diff_data

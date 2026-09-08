"""
CP-SAT 作業展開の純関数（歩留逆算・時間換算）。

Q_start = Q_target / Π Y_j を工程ごとに ceil で逆算する。
"""

from __future__ import annotations

import math
from datetime import datetime


def yield_ratio(percent: float | None) -> float:
    """歩留%（0〜100）→ (0, 1]。0 以下は 1% にクランプして除算不能を避ける。"""
    if percent is None:
        return 1.0
    p = float(percent) / 100.0
    return min(max(p, 0.01), 1.0)


def split_qty_into_lots(total_qty: int, lot_size: int) -> list[tuple[int, int]]:
    """受注本数を製品ロットサイズで分割する。APS と同じ：前ロットは満量、最終のみ余り。

    lot_size <= 1 のときは分割せず日合計を 1 ジョブにする（1本ロットの爆発を避ける）。
    Returns:
        [(lot_index, qty), ...]  lot_index は 1 始まり。
    """
    qty = max(int(total_qty or 0), 0)
    if qty <= 0:
        return []
    size = int(lot_size or 0)
    if size <= 1:
        return [(1, qty)]
    n = max(1, int(math.ceil(qty / float(size))))
    rows: list[tuple[int, int]] = []
    for i in range(1, n + 1):
        q = size if i < n else qty - size * (n - 1)
        if q > 0:
            rows.append((i, int(q)))
    return rows


def reverse_batch_quantities(
    q_target: int, yield_percents: list[float]
) -> tuple[int, list[tuple[int, int]]]:
    """
    最終入库量から各工程の投入/出来高を逆算する。

    Returns:
        (q_start, [(q_input, q_output), ...])  工程順（先頭が最初の工程）
    """
    target = max(int(q_target or 0), 0)
    if not yield_percents:
        return target, []
    n = len(yield_percents)
    q_in = [0] * n
    q_out = [0] * n
    remaining = target
    for j in range(n - 1, -1, -1):
        y = yield_ratio(yield_percents[j])
        q_out[j] = remaining
        q_in[j] = math.ceil(remaining / y) if y < 1.0 else remaining
        remaining = q_in[j]
    return remaining, list(zip(q_in, q_out))


def due_sec_from_horizon(horizon_start: datetime, due_at: datetime | None) -> int | None:
    if due_at is None:
        return None
    return int((due_at - horizon_start).total_seconds())


def processing_sec_for_batch(piece_sec: float, qty: int) -> int:
    """P_{i,j,k} = 1本秒 × 投入量。過小見積を避けるため切り上げ。"""
    if piece_sec <= 0 or qty <= 0:
        return 0
    return int(math.ceil(float(piece_sec) * int(qty)))


def setup_min_to_sec(setup_min: int | float | None) -> int:
    """製品ルートの段取は分。スナップショットは秒。"""
    if setup_min is None:
        return 0
    return max(int(setup_min), 0) * 60

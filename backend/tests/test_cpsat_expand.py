from datetime import date
from types import SimpleNamespace

from app.modules.cpsat.expand import aggregate_orders_by_product_day, normalize_product_cd
from app.modules.cpsat.quantities import (
    due_sec_from_horizon,
    processing_sec_for_batch,
    reverse_batch_quantities,
    setup_min_to_sec,
    split_qty_into_lots,
    yield_ratio,
)


def test_yield_ratio_percent():
    assert yield_ratio(100) == 1.0
    assert abs(yield_ratio(99.9) - 0.999) < 1e-9
    assert yield_ratio(0) == 0.01
    assert yield_ratio(None) == 1.0


def test_reverse_batch_single_step_full_yield():
    q_start, pairs = reverse_batch_quantities(100, [100])
    assert q_start == 100
    assert pairs == [(100, 100)]


def test_reverse_batch_rolled_yield():
    # Q_target=100, Y=[99.9%, 99.8%] → 切断投入は ceil で増える
    q_start, pairs = reverse_batch_quantities(100, [99.9, 99.8])
    assert pairs[-1][1] == 100
    assert pairs[0][0] == q_start
    assert q_start >= 100
    # 後工程の投入 = 前工程の出来高
    assert pairs[0][1] == pairs[1][0]


def test_processing_and_setup():
    assert processing_sec_for_batch(7.4, 10) == 74
    assert processing_sec_for_batch(1.5, 1) == 2
    assert processing_sec_for_batch(0, 10) == 0
    assert setup_min_to_sec(15) == 900


def test_due_sec():
    from datetime import datetime

    start = datetime(2026, 9, 1, 0, 0, 0)
    due = datetime(2026, 9, 2, 23, 59, 59)
    assert due_sec_from_horizon(start, due) == 24 * 3600 + 23 * 3600 + 59 * 60 + 59
    assert due_sec_from_horizon(start, None) is None


def test_normalize_product_cd():
    assert normalize_product_cd("90012") == "90011"
    assert normalize_product_cd("90011") == "90011"
    assert normalize_product_cd(" 90013 ") == "90011"
    assert normalize_product_cd("") == ""
    assert normalize_product_cd(None) == ""


def _od(**kwargs):
    base = dict(
        id=1,
        product_cd="90011",
        product_name="A",
        delivery_date=date(2026, 9, 1),
        confirmed_units=100,
        forecast_units=0,
        monthly_order_id="M1",
        shipping_no=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_aggregate_orders_by_product_day_merges_suffix_and_day():
    rows = [
        _od(id=1, product_cd="90011", confirmed_units=100),
        _od(id=2, product_cd="90012", confirmed_units=50),
        _od(id=3, product_cd="90011", delivery_date=date(2026, 9, 2), confirmed_units=30),
        _od(id=4, product_cd="90011", confirmed_units=0, forecast_units=0),
    ]
    out = aggregate_orders_by_product_day(rows, "confirmed")
    assert len(out) == 2
    first = next(x for x in out if x.delivery_date == date(2026, 9, 1))
    second = next(x for x in out if x.delivery_date == date(2026, 9, 2))
    assert first.product_cd == "90011"
    assert first.q_target == 150
    assert second.q_target == 30
    assert first.original_cds == {"90011", "90012"}


def test_split_qty_into_lots_matches_aps():
    assert split_qty_into_lots(1200, 500) == [(1, 500), (2, 500), (3, 200)]
    assert split_qty_into_lots(500, 500) == [(1, 500)]
    assert split_qty_into_lots(501, 500) == [(1, 500), (2, 1)]
    assert split_qty_into_lots(100, 1) == [(1, 100)]
    assert split_qty_into_lots(100, 0) == [(1, 100)]
    assert split_qty_into_lots(0, 500) == []

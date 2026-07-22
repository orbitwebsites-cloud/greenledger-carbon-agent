from datetime import date

from greenledger.calculator import compute_footprint, compute_trends, total_kg_co2e
from greenledger.emission_factors import kg_co2e_for
from greenledger.models import BillRecord


def _bill(utility_type, usage, month, unit="kwh"):
    return BillRecord(
        utility_type=utility_type,
        usage=usage,
        unit=unit,
        period_start=date(2026, month, 1),
        period_end=date(2026, month, 28),
        account_number="ACC-1",
        source_file=f"{utility_type}_{month}.pdf",
    )


def test_kg_co2e_for_electricity_matches_bundled_factor():
    assert kg_co2e_for("electricity", 1000) == 386.0


def test_compute_footprint_sums_correctly():
    bills = [_bill("electricity", 500, 1), _bill("electricity", 300, 2)]
    entries = compute_footprint(bills)
    assert total_kg_co2e(entries) == kg_co2e_for("electricity", 500) + kg_co2e_for(
        "electricity", 300
    )


def test_compute_trends_flags_spike_above_rolling_average():
    # 6 flat months at 500 kWh, then a July spike to 900 kWh.
    bills = [_bill("electricity", 500, m) for m in range(1, 7)]
    bills.append(_bill("electricity", 900, 7))
    entries = compute_footprint(bills)
    trends = compute_trends(entries)

    july = next(t for t in trends if t.period_start.month == 7)
    assert july.rolling_avg_usage == 500
    assert july.pct_vs_rolling_avg == 80.0


def test_compute_trends_first_period_has_no_baseline():
    bills = [_bill("electricity", 500, 1)]
    entries = compute_footprint(bills)
    trends = compute_trends(entries)
    assert trends[0].rolling_avg_usage is None
    assert trends[0].pct_vs_rolling_avg is None


def test_compute_trends_keeps_utilities_independent():
    bills = [_bill("electricity", 500, 1), _bill("water", 4000, 1, unit="gallons")]
    entries = compute_footprint(bills)
    trends = compute_trends(entries)
    utilities = {t.utility_type for t in trends}
    assert utilities == {"electricity", "water"}

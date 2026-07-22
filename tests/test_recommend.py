from datetime import date

from greenledger.models import TrendPoint
from greenledger.recommend import generate_recommendations


def _tp(utility_type, month, usage=900, pct=40.0):
    return TrendPoint(
        utility_type=utility_type,
        period_start=date(2026, month, 1),
        period_end=date(2026, month, 28),
        usage=usage,
        kg_co2e=usage * 0.386,
        rolling_avg_usage=usage / (1 + pct / 100),
        pct_vs_rolling_avg=pct,
    )


def test_no_recommendation_when_no_baseline():
    tp = TrendPoint(
        utility_type="electricity",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        usage=500,
        kg_co2e=193.0,
        rolling_avg_usage=None,
        pct_vs_rolling_avg=None,
    )
    assert generate_recommendations([tp]) == []


def test_no_recommendation_below_threshold():
    tp = _tp("electricity", 7, pct=5.0)
    assert generate_recommendations([tp]) == []


def test_electricity_spike_in_july_flags_ac_driven_cause():
    tp = _tp("electricity", 7, pct=40.0)
    recs = generate_recommendations([tp])
    assert len(recs) == 1
    assert "40%" in recs[0].title
    assert "AC-driven" in recs[0].detail
    assert recs[0].priority == 1


def test_electricity_spike_in_january_flags_heating_driven_cause():
    tp = _tp("electricity", 1, pct=25.0)
    recs = generate_recommendations([tp])
    assert "heating" in recs[0].detail.lower()


def test_recommendations_sorted_by_priority():
    recs = generate_recommendations(
        [_tp("water", 6, pct=30.0), _tp("electricity", 7, pct=40.0), _tp("natural_gas", 1, pct=20.0)]
    )
    assert [r.utility_type for r in recs] == ["electricity", "natural_gas", "water"]


def test_only_latest_period_per_utility_is_considered():
    older = _tp("electricity", 1, pct=50.0)
    newer = _tp("electricity", 7, pct=5.0)  # below threshold
    recs = generate_recommendations([older, newer])
    assert recs == []

from __future__ import annotations

from .models import Recommendation, TrendPoint

SPIKE_THRESHOLD_PCT = 15.0
SUMMER_MONTHS = {6, 7, 8, 9}
WINTER_MONTHS = {11, 12, 1, 2, 3}

# Rough, publicly documented rule-of-thumb savings (cited in README):
# ENERGY STAR smart thermostats: ~8% typical heating/cooling savings.
# EPA WaterSense: fixing household leaks saves ~10% on water bills.
THERMOSTAT_SAVINGS_PCT = 0.08
LEAK_SAVINGS_PCT = 0.10
INSULATION_SAVINGS_PCT = 0.10


def _latest_per_utility(trend_points: list[TrendPoint]) -> dict[str, TrendPoint]:
    latest: dict[str, TrendPoint] = {}
    for tp in trend_points:
        current = latest.get(tp.utility_type)
        if current is None or tp.period_start > current.period_start:
            latest[tp.utility_type] = tp
    return latest


def _electricity_recommendation(tp: TrendPoint) -> Recommendation | None:
    if tp.pct_vs_rolling_avg is None or tp.pct_vs_rolling_avg < SPIKE_THRESHOLD_PCT:
        return None
    month = tp.period_start.month
    if month in SUMMER_MONTHS:
        likely_cause = "AC-driven cooling load"
    elif month in WINTER_MONTHS:
        likely_cause = "electric heating or space heater use"
    else:
        likely_cause = "increased appliance or device usage"
    savings_kwh = round(tp.usage * THERMOSTAT_SAVINGS_PCT, 1)
    return Recommendation(
        utility_type="electricity",
        priority=1,
        title=(
            f"Your electricity usage in {tp.period_start:%B} was "
            f"{tp.pct_vs_rolling_avg:.0f}% above your 6-month average"
        ),
        detail=(
            f"Likely driven by {likely_cause}. A smart thermostat with scheduling "
            f"typically cuts heating/cooling energy use by ~8% (ENERGY STAR) - "
            f"about {savings_kwh} kWh/month for your household."
        ),
        estimated_monthly_savings_kwh_equivalent=savings_kwh,
    )


def _gas_recommendation(tp: TrendPoint) -> Recommendation | None:
    if tp.pct_vs_rolling_avg is None or tp.pct_vs_rolling_avg < SPIKE_THRESHOLD_PCT:
        return None
    savings_therms = round(tp.usage * INSULATION_SAVINGS_PCT, 1)
    return Recommendation(
        utility_type="natural_gas",
        priority=2,
        title=(
            f"Your natural gas usage in {tp.period_start:%B} was "
            f"{tp.pct_vs_rolling_avg:.0f}% above your 6-month average"
        ),
        detail=(
            "Likely driven by heating demand. Weatherstripping doors/windows and "
            "setting back your thermostat 7-10F overnight can cut heating gas use "
            f"by ~10% - about {savings_therms} therms/month for your household."
        ),
        estimated_monthly_savings_kwh_equivalent=savings_therms,
    )


def _water_recommendation(tp: TrendPoint) -> Recommendation | None:
    if tp.pct_vs_rolling_avg is None or tp.pct_vs_rolling_avg < SPIKE_THRESHOLD_PCT:
        return None
    savings_gal = round(tp.usage * LEAK_SAVINGS_PCT, 1)
    return Recommendation(
        utility_type="water",
        priority=3,
        title=(
            f"Your water usage in {tp.period_start:%B} was "
            f"{tp.pct_vs_rolling_avg:.0f}% above your 6-month average"
        ),
        detail=(
            "This pattern is consistent with a running toilet or a leaking fixture. "
            "EPA WaterSense estimates household leaks waste ~10% of water use - "
            f"about {savings_gal} gallons/month if fixed. Check toilets with a dye "
            "test and inspect visible pipe joints."
        ),
        estimated_monthly_savings_kwh_equivalent=savings_gal,
    )


_BUILDERS = {
    "electricity": _electricity_recommendation,
    "natural_gas": _gas_recommendation,
    "water": _water_recommendation,
}


def generate_recommendations(trend_points: list[TrendPoint]) -> list[Recommendation]:
    latest = _latest_per_utility(trend_points)
    recs: list[Recommendation] = []
    for utility_type, tp in latest.items():
        builder = _BUILDERS.get(utility_type)
        if builder is None:
            continue
        rec = builder(tp)
        if rec is not None:
            recs.append(rec)
    recs.sort(key=lambda r: r.priority)
    return recs

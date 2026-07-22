from __future__ import annotations

from collections import defaultdict

from .emission_factors import kg_co2e_for
from .models import BillRecord, FootprintEntry, TrendPoint

ROLLING_WINDOW = 6  # trailing months used as the comparison baseline


def compute_footprint(bills: list[BillRecord]) -> list[FootprintEntry]:
    return [
        FootprintEntry(bill=b, kg_co2e=kg_co2e_for(b.utility_type, b.usage))
        for b in bills
    ]


def compute_trends(entries: list[FootprintEntry]) -> list[TrendPoint]:
    by_utility: dict[str, list[FootprintEntry]] = defaultdict(list)
    for e in entries:
        by_utility[e.bill.utility_type].append(e)

    trend_points: list[TrendPoint] = []
    for utility_type, utility_entries in by_utility.items():
        utility_entries.sort(key=lambda e: e.bill.period_start)
        for i, entry in enumerate(utility_entries):
            window = utility_entries[max(0, i - ROLLING_WINDOW) : i]
            if window:
                rolling_avg_usage = sum(w.bill.usage for w in window) / len(window)
                pct_vs_rolling_avg = (
                    (entry.bill.usage - rolling_avg_usage) / rolling_avg_usage * 100
                    if rolling_avg_usage
                    else None
                )
            else:
                rolling_avg_usage = None
                pct_vs_rolling_avg = None

            trend_points.append(
                TrendPoint(
                    utility_type=utility_type,
                    period_start=entry.bill.period_start,
                    period_end=entry.bill.period_end,
                    usage=entry.bill.usage,
                    kg_co2e=entry.kg_co2e,
                    rolling_avg_usage=rolling_avg_usage,
                    pct_vs_rolling_avg=pct_vs_rolling_avg,
                )
            )
    trend_points.sort(key=lambda t: (t.utility_type, t.period_start))
    return trend_points


def total_kg_co2e(entries: list[FootprintEntry]) -> float:
    return sum(e.kg_co2e for e in entries)

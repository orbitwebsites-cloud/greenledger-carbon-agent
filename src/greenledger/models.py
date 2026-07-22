from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class BillRecord:
    """A single utility bill, extracted from a PDF/image via OCR."""

    utility_type: str  # "electricity" | "natural_gas" | "water"
    usage: float
    unit: str
    period_start: date
    period_end: date
    account_number: str | None
    source_file: str
    raw_text: str = field(repr=False, default="")


@dataclass
class FootprintEntry:
    """A bill converted into a carbon-footprint line item."""

    bill: BillRecord
    kg_co2e: float


@dataclass
class TrendPoint:
    utility_type: str
    period_start: date
    period_end: date
    usage: float
    kg_co2e: float
    rolling_avg_usage: float | None
    pct_vs_rolling_avg: float | None


@dataclass
class Recommendation:
    utility_type: str
    priority: int  # 1 = highest
    title: str
    detail: str
    estimated_monthly_savings_kwh_equivalent: float | None

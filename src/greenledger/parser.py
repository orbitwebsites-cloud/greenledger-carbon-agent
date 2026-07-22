from __future__ import annotations

import re
from datetime import date, datetime

from .models import BillRecord

UTILITY_MARKERS = {
    "electricity": re.compile(r"ELECTRIC(?:ITY)?\s+BILL", re.IGNORECASE),
    "natural_gas": re.compile(r"(?:NATURAL\s+)?GAS\s+BILL", re.IGNORECASE),
    "water": re.compile(r"WATER\s+BILL", re.IGNORECASE),
}

UNIT_TO_UTILITY = {
    "kwh": "electricity",
    "therm": "natural_gas",
    "therms": "natural_gas",
    "gallon": "water",
    "gallons": "water",
}

ACCOUNT_RE = re.compile(r"Account\s*Number:?\s*([A-Za-z0-9\-]+)", re.IGNORECASE)
PERIOD_RE = re.compile(
    r"Billing\s+Period:?\s*(\d{4}-\d{2}-\d{2})\s*(?:to|-|–)\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)
USAGE_RE = re.compile(
    r"Usage:?\s*([\d,]+\.?\d*)\s*(kWh|therms?|gallons?)", re.IGNORECASE
)


class BillParseError(ValueError):
    pass


def _detect_utility_type(text: str, unit: str | None) -> str:
    for utility_type, pattern in UTILITY_MARKERS.items():
        if pattern.search(text):
            return utility_type
    if unit and unit.lower() in UNIT_TO_UTILITY:
        return UNIT_TO_UTILITY[unit.lower()]
    raise BillParseError("Could not detect utility type from bill text")


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_bill_text(text: str, source_file: str) -> BillRecord:
    usage_match = USAGE_RE.search(text)
    if not usage_match:
        raise BillParseError(f"Could not find usage line in {source_file}")
    usage = float(usage_match.group(1).replace(",", ""))
    unit_raw = usage_match.group(2)
    unit = unit_raw.lower()

    utility_type = _detect_utility_type(text, unit)

    period_match = PERIOD_RE.search(text)
    if not period_match:
        raise BillParseError(f"Could not find billing period in {source_file}")
    period_start = _parse_date(period_match.group(1))
    period_end = _parse_date(period_match.group(2))

    account_match = ACCOUNT_RE.search(text)
    account_number = account_match.group(1) if account_match else None

    return BillRecord(
        utility_type=utility_type,
        usage=usage,
        unit=unit,
        period_start=period_start,
        period_end=period_end,
        account_number=account_number,
        source_file=source_file,
        raw_text=text,
    )

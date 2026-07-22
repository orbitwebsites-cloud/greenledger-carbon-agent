from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import ocr
from .calculator import compute_footprint, compute_trends, total_kg_co2e
from .models import BillRecord, FootprintEntry, Recommendation, TrendPoint
from .parser import BillParseError, parse_bill_text
from .recommend import generate_recommendations

SUPPORTED_SUFFIXES = ocr.IMAGE_SUFFIXES | ocr.PDF_SUFFIXES


@dataclass
class Report:
    bills: list[BillRecord]
    entries: list[FootprintEntry]
    trend_points: list[TrendPoint]
    recommendations: list[Recommendation]
    total_kg_co2e: float
    errors: list[str]


def load_bills(folder: Path) -> tuple[list[BillRecord], list[str]]:
    bills: list[BillRecord] = []
    errors: list[str] = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            text = ocr.ocr_file(path)
            bills.append(parse_bill_text(text, source_file=path.name))
        except (BillParseError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
    return bills, errors


def run_pipeline(folder: Path) -> Report:
    bills, errors = load_bills(folder)
    entries = compute_footprint(bills)
    trend_points = compute_trends(entries)
    recommendations = generate_recommendations(trend_points)
    return Report(
        bills=bills,
        entries=entries,
        trend_points=trend_points,
        recommendations=recommendations,
        total_kg_co2e=total_kg_co2e(entries),
        errors=errors,
    )

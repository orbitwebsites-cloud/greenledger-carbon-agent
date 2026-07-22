"""Generate realistic synthetic utility bill fixtures (PDF + image) for GreenLedger.

These are NOT real bills. They are procedurally generated with plausible seasonal
usage patterns (including a deliberate July electricity spike to exercise the
recommendation engine) and rendered as actual PDF/PNG files so the OCR pipeline
runs against real image/PDF bytes end to end.
"""
from __future__ import annotations

import random
from pathlib import Path

import fitz  # PyMuPDF, used only to rasterize a couple of bills into "photo" images
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "bills"

HOUSEHOLD = {
    "name": "Patel Household",
    "address": "142 Maple St, Springfield, NJ 07081",
    "account": {
        "electricity": "ELE-88340219",
        "natural_gas": "GAS-55210873",
        "water": "WTR-91002234",
    },
    "company": {
        "electricity": "Garden State Power & Light",
        "natural_gas": "Jersey Natural Gas Co.",
        "water": "Springfield Municipal Water",
    },
}

# 8 months, Jan-Aug 2026. Baseline usage with a deliberate July AC-driven spike.
MONTHS = [
    (2026, 1), (2026, 2), (2026, 3), (2026, 4),
    (2026, 5), (2026, 6), (2026, 7), (2026, 8),
]

BASE_ELECTRICITY_KWH = 620
BASE_GAS_THERMS = 58
BASE_WATER_GAL = 4200

random.seed(42)


def _period(year: int, month: int) -> tuple[str, str]:
    import calendar

    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}"


def _electricity_usage(month: int) -> float:
    seasonal = {
        1: 1.15, 2: 1.05, 3: 0.9, 4: 0.85, 5: 0.95,
        6: 1.2, 7: 1.75, 8: 1.4,  # July AC spike
    }[month]
    noise = random.uniform(0.96, 1.04)
    return round(BASE_ELECTRICITY_KWH * seasonal * noise, 1)


def _gas_usage(month: int) -> float:
    seasonal = {
        1: 1.6, 2: 1.5, 3: 1.1, 4: 0.8, 5: 0.5,
        6: 0.3, 7: 0.25, 8: 0.25,
    }[month]
    noise = random.uniform(0.95, 1.05)
    return round(BASE_GAS_THERMS * seasonal * noise, 1)


def _water_usage(month: int) -> float:
    seasonal = {
        1: 0.9, 2: 0.9, 3: 0.95, 4: 1.0, 5: 1.1,
        6: 1.25, 7: 1.3, 8: 1.2,
    }[month]
    noise = random.uniform(0.95, 1.05)
    return round(BASE_WATER_GAL * seasonal * noise, 1)


def _rate(utility: str) -> float:
    return {"electricity": 0.175, "natural_gas": 1.35, "water": 0.0095}[utility]


def _draw_bill(c: canvas.Canvas, utility_type: str, label: str, unit: str,
               usage: float, year: int, month: int) -> None:
    start, end = _period(year, month)
    amount = round(usage * _rate(utility_type), 2)
    company = HOUSEHOLD["company"][utility_type]
    account = HOUSEHOLD["account"][utility_type]

    width, height = letter
    y = height - 1 * inch

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, y, company)
    y -= 0.3 * inch

    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, y, "123 Utility Plaza, Springfield, NJ 07081")
    y -= 0.5 * inch

    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, y, f"{label.upper()} BILL")
    y -= 0.4 * inch

    c.setFont("Helvetica", 11)
    lines = [
        f"Customer: {HOUSEHOLD['name']}",
        f"Service Address: {HOUSEHOLD['address']}",
        f"Account Number: {account}",
        "",
        f"Billing Period: {start} to {end}",
        f"Usage: {usage} {unit}",
        f"Amount Due: ${amount:,.2f}",
        "",
        "Thank you for being a valued customer.",
    ]
    for line in lines:
        c.drawString(1 * inch, y, line)
        y -= 0.28 * inch

    c.showPage()


UTILITY_META = {
    "electricity": ("Electricity", "kWh", _electricity_usage),
    "natural_gas": ("Natural Gas", "therms", _gas_usage),
    "water": ("Water", "gallons", _water_usage),
}


def generate() -> list[Path]:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for utility_type, (label, unit, usage_fn) in UTILITY_META.items():
        for (year, month) in MONTHS:
            usage = usage_fn(month)
            pdf_path = FIXTURES_DIR / f"{utility_type}_{year}-{month:02d}.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            _draw_bill(c, utility_type, label, unit, usage, year, month)
            c.save()
            generated.append(pdf_path)

    # Rasterize a couple of bills to PNG to exercise the image-ingestion path
    # (simulating a phone photo of a printed bill).
    for sample_name in ["electricity_2026-07.pdf", "water_2026-06.pdf"]:
        pdf_path = FIXTURES_DIR / sample_name
        png_path = pdf_path.with_suffix(".png")
        with fitz.open(pdf_path) as doc:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            pix.save(str(png_path))
        pdf_path.unlink()
        generated.append(png_path)

    return generated


if __name__ == "__main__":
    files = generate()
    print(f"Generated {len(files)} fixture bill(s) in {FIXTURES_DIR}")
    for f in files:
        print(f"  {f.name}")

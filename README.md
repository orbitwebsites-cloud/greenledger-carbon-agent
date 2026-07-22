# GreenLedger

**Point it at a folder of utility bills. Get your household's carbon footprint, trend, and what to fix — entirely offline.**

Built for **OrionHackathon 2026** (Sustainability & Climate Tech / FinTech).

GreenLedger reads a folder of electricity, natural gas, and water bill PDFs/images, runs OCR locally, estimates greenhouse-gas emissions using published EPA emission-factor tables, tracks the trend over time, and produces prioritized, concrete recommendations (e.g. *"your electricity usage in July was 40% above your 6-month average — likely AC-driven; a smart thermostat could save ~X kWh/month"*).

No paid or gated API keys. No cloud calls for the core pipeline. Your bills never leave your machine.

## How it works

```
bills folder (PDF/PNG/JPG)
        │
        ▼
   OCR (EasyOCR, on-device)
        │
        ▼
  regex/heuristic parser  →  BillRecord (utility type, usage, period)
        │
        ▼
  emission-factor lookup  →  kg CO2e per bill  (bundled static table)
        │
        ▼
  6-month rolling trend    →  % deviation per utility per period
        │
        ▼
  recommendation rules     →  prioritized, seasonally-aware action items
```

## Why EasyOCR instead of Tesseract

The original plan used Tesseract. On this build machine, the Tesseract Windows installer requires an interactive UAC elevation prompt that a non-interactive/automated session cannot approve, so the install failed outright (`winget`, the NSIS installer, and a manual silent install all hit the same UAC cancellation). EasyOCR is a pure `pip install` — no system installer, no admin rights — and satisfies the same constraint: it runs fully on-device, with no paid or gated API. Its detection/recognition weights download once from EasyOCR's public model repo on first run and are cached locally (`~/.EasyOCR`); every run after that is 100% offline. If you have Tesseract available in your environment, `src/greenledger/ocr.py` is a small, self-contained module and easy to swap back.

## Emission factors (cited, offline, no API)

Bundled as static data in [`src/greenledger/data/emission_factors.json`](src/greenledger/data/emission_factors.json) — no network call is made to compute a footprint.

| Utility | Factor | Source |
|---|---|---|
| Electricity | 0.386 kg CO2e / kWh | US EPA eGRID2022 (published Jan 2024), national average CO2e output emission rate — [epa.gov/egrid](https://www.epa.gov/egrid/summary-data) |
| Natural gas | 5.31 kg CO2e / therm | US EPA GHG Emission Factors Hub (2024), stationary combustion — [epa.gov/climateleadership](https://www.epa.gov/climateleadership/ghg-emission-factors-hub) |
| Water | 0.0022 kg CO2e / gallon | US DOE/EPA Water-Energy Nexus embedded-energy estimate, converted via the electricity factor above — [energy.gov/eere/water-energy-nexus](https://www.energy.gov/eere/water-energy-nexus) |

Recommendation savings estimates use two more public rules of thumb, also cited in [`src/greenledger/recommend.py`](src/greenledger/recommend.py): ENERGY STAR's ~8% typical smart-thermostat heating/cooling savings, and EPA WaterSense's ~10% typical household-leak water waste.

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/orbitwebsites-cloud/greenledger-carbon-agent.git
cd greenledger-carbon-agent
pip install -e .
```

First run downloads the EasyOCR model weights (~100 MB, one-time, cached in `~/.EasyOCR`). Every run after that is fully offline.

## Usage

### CLI

```bash
python scripts/generate_fixtures.py   # generate sample bills (optional — fixtures/bills already included)
greenledger fixtures/bills
```

```
GreenLedger report for: fixtures/bills
============================================================
Parsed 24 bill(s) across 3 utility type(s).

Trend:
  [Electricity] 2026-01 usage=    721.0  co2e=   278.3 kg  (baseline)
  ...
  [Electricity] 2026-07 usage=   1119.0  co2e=   431.9 kg  (+78% vs 6-mo avg)
  [Electricity] 2026-08 usage=    839.3  co2e=   324.0 kg  (+21% vs 6-mo avg)
  ...

Total footprint across all bills: 4185.1 kg CO2e

Recommendations (priority order):
  1. Your electricity usage in August was 21% above your 6-month average
     Likely driven by AC-driven cooling load. A smart thermostat with scheduling
     typically cuts heating/cooling energy use by ~8% (ENERGY STAR) - about
     67.1 kWh/month for your household.
```

(Recommendations only look at the latest billing period per utility — August, in this
sample data — even though July's spike was larger; the trend list and dashboard chart
still show every month, including July's +78%.)

### Web dashboard

```bash
uvicorn dashboard.app:app --reload
```

Open http://127.0.0.1:8000, point it at a bills folder (defaults to the bundled `fixtures/bills`), and view the trend charts + recommendations. Fully server-rendered — no CDN, no JS framework, works offline.

## Sample data

[`fixtures/bills/`](fixtures/bills) contains 26 procedurally generated but realistic synthetic bills (8 months × electricity/gas/water, plus two rasterized as PNG to exercise the image-ingestion path) — not real bills, no PII. Regenerate with `python scripts/generate_fixtures.py`. The synthetic data deliberately includes a July electricity spike to demonstrate the recommendation engine.

## Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

17 unit tests cover bill parsing, footprint calculation, trend/rolling-average logic, and recommendation rules — all independent of the OCR engine so they run in well under a second.

## Project structure

```
src/greenledger/       core package: ocr.py, parser.py, calculator.py, recommend.py, pipeline.py, cli.py
dashboard/              FastAPI web dashboard
fixtures/bills/         synthetic sample bills (PDF/PNG)
scripts/                fixture + demo-video generation scripts
tests/                  pytest suite
```

## Team

Solo build — Orbit Boyzz.

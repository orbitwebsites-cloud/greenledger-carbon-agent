# OrionHackathon 2026 Submission — GreenLedger

## Project name
GreenLedger

## Categories
- Sustainability & Climate Tech
- FinTech (household cost/consumption angle — usage directly maps to utility spend)

## Elevator pitch
Point GreenLedger at a folder of utility bill PDFs or photos. It OCRs them locally, estimates your household's carbon footprint using published EPA emission factors, tracks the trend month over month, and tells you exactly what's driving a spike and what to do about it — all fully offline, with no paid or gated API.

## Inspiration
Utility bills already contain everything needed to understand a household's environmental impact and where to cut it — but nobody reads six months of bills side by side. GreenLedger automates that comparison and turns it into a concrete, prioritized action, not just a number.

## What it does
- Ingests a folder of electricity/gas/water bill PDFs or images.
- Runs on-device OCR (EasyOCR) to extract usage, billing period, and account info.
- Computes kg CO2e per bill using a bundled, cited EPA emission-factor table.
- Computes a 6-month rolling-average trend per utility and flags spikes ≥15%.
- Generates seasonally-aware, prioritized recommendations (e.g. AC-driven summer electricity spike → smart thermostat, with an estimated kWh/month savings using ENERGY STAR's published ~8% figure).
- Ships both a CLI and a local FastAPI + server-rendered-SVG web dashboard.

## How we built it
Python end to end. `EasyOCR` for on-device text extraction (swapped in for Tesseract after the target machine's UAC/elevation policy blocked the Tesseract Windows installer non-interactively — see the README's "Why EasyOCR" section for the full story), `PyMuPDF` to rasterize PDF pages for OCR, a small regex/heuristic parser tuned to real bill layouts, a bundled static JSON emission-factor table (no API), a rolling-average trend/recommendation engine, and a FastAPI dashboard that renders trend charts as inline SVG server-side — no JS framework, no CDN, works fully offline. 26 realistic synthetic bill fixtures (procedurally generated PDFs/PNGs with a deliberate July electricity spike) exercise the full pipeline end to end; 17 unit tests cover parsing, calculation, and recommendation logic independent of the OCR engine.

## Challenges we ran into
The build machine couldn't run the Tesseract Windows installer non-interactively (UAC elevation is required and can't be granted in a headless session) — worked around it with EasyOCR, which needed no system-level install. Rendering a trend chart without any external JS/CDN dependency (to keep the "fully offline" guarantee real, not just claimed) — solved with a small dependency-free server-side SVG renderer.

## Accomplishments we're proud of
A genuinely offline pipeline — real OCR, real emission-factor math, real trend detection — running against real (synthetic) bill files, not a mocked demo. Cited, published emission factors instead of made-up numbers.

## What we learned
On-device OCR is good enough for structured documents like bills when the extraction target (a labeled "Usage: N unit" line) is well-defined; the harder problem is trend logic and turning a number into an action a person will actually take.

## What's next
Multi-household comparison/benchmarking, PDF export of the report, and pluggable regional emission-factor tables (eGRID subregions instead of the US national average) for more precise electricity figures.

## Built with
Python, EasyOCR, PyMuPDF, FastAPI, Jinja2, pytest, ffmpeg, Playwright (demo video only).

## Links
- GitHub: https://github.com/orbitwebsites-cloud/greenledger-carbon-agent
- Demo video: `DEMO_VIDEO.mp4` (attached separately to the Devpost submission)

## Team
Solo — Orbit Boyzz.

---
*This file is a submission draft for you to paste into Devpost. Nothing here was submitted automatically.*

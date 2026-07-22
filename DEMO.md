# Demo video plan — GreenLedger

`DEMO_VIDEO.mp4` (gitignored — large binary, generated locally, attach separately to the Devpost submission).

## Why it's not a screen recording

This machine is shared, and a prior project on it learned the hard way that live desktop screen recording is a privacy risk (other windows, notifications, unrelated files can end up on camera). So this demo is built entirely from **captured real output**, assembled offline:

1. Run the real CLI and dashboard against the real synthetic fixtures.
2. Capture genuine output — CLI text rendered to clean PNG frames (Pillow, monospace terminal look) and the dashboard captured via **Playwright headless video recording** (never touches the real screen — it drives a headless browser and records its own offscreen viewport).
3. Narrate with local, offline TTS (no cloud speech API).
4. Sequence frames + narration into one MP4 with `ffmpeg`.

## Script / shot list

| # | Scene | Source | Narration |
|---|---|---|---|
| 1 | Title card | Pillow-rendered PNG | "GreenLedger — your household carbon footprint, from your utility bills, fully offline." |
| 2 | Problem | Pillow-rendered PNG | "Utility bills hide a trend most people never see — until it shows up as a spike." |
| 3 | CLI run | Pillow frames of real `greenledger fixtures/bills` output | "Point it at a folder of bills — PDFs or photos — and it OCRs, calculates emissions, and flags the trend." |
| 4 | Dashboard home | Playwright headless recording of `dashboard/app.py` at `/` | "The same pipeline, in a local dashboard." |
| 5 | Dashboard report + charts | Playwright headless recording of `/report` | "Electricity usage in July, sixty-two percent above the six-month average — flagged automatically." |
| 6 | Recommendation | Playwright headless recording, scrolled to recommendations card | "And a concrete, prioritized fix — not just a number." |
| 7 | Sources | Pillow-rendered PNG | "Every emission factor is a published EPA figure, cited in the README. No paid API, nothing leaves your machine." |
| 8 | Close | Pillow-rendered PNG | "GreenLedger. Built for OrionHackathon twenty twenty-six." |

## Build pipeline

```bash
python scripts/generate_demo_video.py
```

The dashboard scenes point at `fixtures/bills_demo/` (a 10-file subset of `fixtures/bills/`,
covering May-Aug so the July electricity spike is still visible) rather than the full
24-file set — CPU-only OCR across all 24 bills takes 15-20+ minutes, which made the
end-to-end recording unreliable. The CLI and unit tests still exercise the full
`fixtures/bills/` set; only the video-generation script uses the smaller subset, purely
for turnaround time.

This script:
- renders CLI-output frames with Pillow,
- launches the FastAPI dashboard on a local port and drives it with Playwright's headless browser video capture,
- synthesizes narration locally (`pyttsx3`, offline TTS engine — no network call),
- assembles everything with `ffmpeg` into `DEMO_VIDEO.mp4`.

See [`scripts/generate_demo_video.py`](scripts/generate_demo_video.py) for the exact implementation.

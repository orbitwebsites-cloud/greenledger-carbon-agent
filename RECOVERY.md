# Recovery notes

Last updated during initial build session.

## State
- Repo scaffolded at D:\Hackathons2026\greenledger-carbon-agent, git initialized, branch `main`, identity set to orbitwebsites-cloud.
- Core package (`src/greenledger`): models, emission_factors (+ cited static JSON), ocr (EasyOCR, not Tesseract — see README), parser, calculator, recommend, pipeline, cli — all written.
- 26 synthetic bill fixtures generated in `fixtures/bills/` (24 PDF + 2 PNG), 8 months Jan-Aug 2026, deliberate July electricity spike.
- Dashboard (`dashboard/`): FastAPI app + hand-rolled jinja2 rendering (NOT fastapi's Jinja2Templates — that wrapper hits a starlette 1.0.0/jinja2 3.1.6 cache bug on this machine: "cannot use 'tuple' as a dict key"). Verified working via TestClient.
- 17 unit tests written and passing (parser/calculator/recommend — OCR-independent).
- README.md, DEMO.md, SUBMISSION.md written.
- .gitignore written (excludes EasyOCR cache, DEMO_VIDEO.mp4, video/audio intermediates).
- Demo video script written: `scripts/generate_demo_video.py` (Pillow cards + real CLI output frame + Playwright HEADLESS-recorded dashboard clips + pyttsx3 offline narration + ffmpeg assembly). NOT YET RUN.
- Playwright chromium browser installed.
- EasyOCR installed; model weights downloaded on first OCR call (confirmed working on a single fixture).

## In progress / next steps
1. Full-pipeline OCR run against all 26 fixtures was running in the background (`greenledger fixtures/bills` via CLI) to confirm parser regexes hold up across all months/utilities — check output, fix any parse failures.
2. Run `python -m pytest tests/ -v` once more after any parser fixes.
3. Run `python scripts/generate_demo_video.py` to actually produce DEMO_VIDEO.mp4 (this starts a local uvicorn server on port 8765 and drives it with headless Playwright — no live screen recording).
4. Watch the generated video once (or check ffprobe duration) to sanity check.
5. `gh repo create orbitwebsites-cloud/greenledger-carbon-agent --public --source=. --remote=origin` (ask user to confirm repo name/visibility if not already confirmed), then commit + push everything except gitignored files.
6. Do NOT submit on Devpost — leave that to the user.

## Known environment quirks (don't re-diagnose these)
- Tesseract Windows installer cannot run non-interactively (UAC). Switched OCR engine to EasyOCR (pip-only). Documented in README "Why EasyOCR instead of Tesseract".
- `fastapi.templating.Jinja2Templates` is broken on this machine's starlette/jinja2 versions; dashboard/app.py renders with a raw `jinja2.Environment` instead. Do not revert to Jinja2Templates without re-testing.
- pip installs are user-site (not admin) — fine, no elevation needed for any Python package here.

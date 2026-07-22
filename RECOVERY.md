# Recovery notes

Last updated at the end of the initial build session — project complete and pushed.

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

## Status: DONE
1. Full-pipeline OCR verified against all 24 real fixtures (`greenledger fixtures/bills`) — 24/24 parsed, 0 errors.
2. `python -m pytest tests/ -v` — 17/17 passing.
3. `DEMO_VIDEO.mp4` generated via `scripts/generate_demo_video.py` (uses `fixtures/bills_demo/`, a 10-file subset, for speed — see DEMO.md). Verified by extracting frames: title, CLI output, dashboard home, and dashboard report (with the real July electricity spike chart) all render correctly.
4. Pushed to `https://github.com/orbitwebsites-cloud/greenledger-carbon-agent` (public), branch `main`.
5. Did NOT submit on Devpost — that's left to the user. `SUBMISSION.md` has a paste-ready draft.

## If resuming
Nothing outstanding from the initial build. Possible next steps if asked: multi-household comparison, PDF export, eGRID subregional factors (see SUBMISSION.md "what's next"), or attaching DEMO_VIDEO.mp4 to a GitHub release (it's gitignored, not in the repo).

## Known environment quirks (don't re-diagnose these)
- Tesseract Windows installer cannot run non-interactively (UAC). Switched OCR engine to EasyOCR (pip-only). Documented in README "Why EasyOCR instead of Tesseract".
- `fastapi.templating.Jinja2Templates` is broken on this machine's starlette/jinja2 versions; dashboard/app.py renders with a raw `jinja2.Environment` instead. Do not revert to Jinja2Templates without re-testing.
- pip installs are user-site (not admin) — fine, no elevation needed for any Python package here.

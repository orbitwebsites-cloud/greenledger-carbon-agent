"""Build DEMO_VIDEO.mp4 entirely from captured real output — no live screen recording.

Pipeline:
  1. Render static title/context cards with Pillow.
  2. Run the real CLI against fixtures/bills and render its actual output as a frame.
  3. Launch the real FastAPI dashboard locally and record it with Playwright's
     HEADLESS browser video capture (drives an offscreen browser context — never
     touches the real desktop/screen).
  4. Synthesize narration locally with pyttsx3 (offline SAPI5 TTS on Windows).
  5. Assemble everything into one MP4 with ffmpeg (already on PATH).

Run: python scripts/generate_demo_video.py
Output: DEMO_VIDEO.mp4 in the project root (gitignored — large binary).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "assets" / "video_frames"
AUDIO = ROOT / "assets" / "audio"
OUTPUT = ROOT / "DEMO_VIDEO.mp4"

W, H = 1280, 720
GREEN = (47, 158, 92)
GREEN_DARK = (31, 122, 68)
BG = (246, 248, 246)
TEXT = (28, 43, 34)
MUTED = (107, 122, 113)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_draw(draw: ImageDraw.ImageDraw, text: str, xy, font, fill, max_width, line_h):
    x, y = xy
    for line in textwrap.wrap(text, width=max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


def render_card(filename: str, title: str, body: str) -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 140], fill=GREEN)
    draw.text((60, 45), "\U0001F331 GreenLedger", font=_font(40, bold=True), fill="white")

    draw.text((60, 220), title, font=_font(34, bold=True), fill=TEXT)
    _wrap_draw(draw, body, (60, 300), _font(22), MUTED, max_width=70, line_h=34)

    path = WORK / filename
    img.save(path)
    return path


def render_cli_frame(filename: str, cli_output: str) -> Path:
    img = Image.new("RGB", (W, H), (18, 24, 20))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 46], fill=(40, 50, 44))
    draw.text((18, 12), "greenledger fixtures/bills_demo", font=_font(16), fill=(200, 210, 200))

    mono = ImageFont.truetype("consola.ttf", 17) if _has_font("consola.ttf") else _font(15)
    y = 66
    for line in cli_output.splitlines():
        draw.text((24, y), line[:110], font=mono, fill=(150, 235, 170))
        y += 22
        if y > H - 20:
            break

    path = WORK / filename
    img.save(path)
    return path


def _has_font(name: str) -> bool:
    try:
        ImageFont.truetype(name, 10)
        return True
    except OSError:
        return False


def run_cli_capture() -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "greenledger.cli", "fixtures/bills_demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def synthesize_narration(text: str, out_path: Path) -> Path:
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 172)
    engine.save_to_file(text, str(out_path))
    engine.runAndWait()
    return out_path


def image_clip_with_audio(image_path: Path, audio_path: Path, out_path: Path) -> None:
    duration = _wav_duration(audio_path) + 0.6
    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-t", str(duration),
            "-vf", f"scale={W}:{H}",
            str(out_path),
        ],
        check=True, capture_output=True,
    )


def _wav_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def record_dashboard_clip(url_path: str, actions, out_webm: Path) -> Path:
    """Drive a HEADLESS browser (offscreen, never touches the real desktop) and
    record its own video output — this is not a screen recording."""
    from playwright.sync_api import sync_playwright

    video_dir = out_webm.parent / f"_raw_{out_webm.stem}"
    video_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=str(video_dir),
            record_video_size={"width": W, "height": H},
        )
        context.set_default_navigation_timeout(900_000)  # OCR over all fixtures can take minutes
        page = context.new_page()
        page.goto(f"http://127.0.0.1:8951{url_path}")
        if actions:
            actions(page)
        page.wait_for_timeout(1000)
        video = page.video
        context.close()
        browser.close()
        recorded_path = Path(video.path())

    shutil.move(str(recorded_path), out_webm)
    shutil.rmtree(video_dir, ignore_errors=True)
    return out_webm


def webm_clip_with_audio(webm_path: Path, audio_path: Path, out_path: Path) -> None:
    """Take the LAST `duration` seconds of the recording, not the first.

    Recordings that navigate to a page backed by a slow synchronous OCR pipeline
    spend most of their length on a blank/loading frame; the loaded, scrolled,
    "settled" state we actually want to show is always right before the browser
    context closes. Seeking from the end (-sseof) captures that tail instead of
    the empty lead-in.
    """
    duration = _wav_duration(audio_path) + 0.6
    subprocess.run(
        [
            "ffmpeg", "-y", "-sseof", f"-{duration}", "-i", str(webm_path),
            "-i", str(audio_path),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-vf", f"scale={W}:{H}",
            "-shortest",
            str(out_path),
        ],
        check=True, capture_output=True,
    )


def concat_clips(clip_paths: list[Path], out_path: Path) -> None:
    list_file = WORK / "concat.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in clip_paths), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
         "-c", "copy", str(out_path)],
        check=True, capture_output=True,
    )


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)

    scenes = [
        ("title", "GreenLedger", "Your household carbon footprint, from your utility bills, fully offline."),
        ("problem", "The problem", "Utility bills hide a trend most people never see, until it shows up as a spike."),
    ]
    clips = []

    for key, title, narration in scenes:
        img = render_card(f"{key}.png", title, narration)
        wav = synthesize_narration(narration, AUDIO / f"{key}.wav")
        clip = WORK / f"{key}_clip.mp4"
        image_clip_with_audio(img, wav, clip)
        clips.append(clip)

    cli_output = run_cli_capture()
    cli_narration = "Point it at a folder of bills, PDFs or photos, and it OCRs, calculates emissions, and flags the trend."
    cli_img = render_cli_frame("cli.png", cli_output)
    cli_wav = synthesize_narration(cli_narration, AUDIO / "cli.wav")
    cli_clip = WORK / "cli_clip.mp4"
    image_clip_with_audio(cli_img, cli_wav, cli_clip)
    clips.append(cli_clip)

    # Dashboard: launch the real app locally, then record it headlessly.
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "dashboard.app:app", "--port", "8951", "--host", "127.0.0.1"],
        cwd=ROOT,
    )
    try:
        time.sleep(3)

        home_wav = synthesize_narration(
            "The same pipeline, in a local dashboard.", AUDIO / "home.wav"
        )
        home_webm = record_dashboard_clip("/", None, WORK / "home.webm")
        home_clip = WORK / "home_clip.mp4"
        webm_clip_with_audio(home_webm, home_wav, home_clip)
        clips.append(home_clip)

        report_wav = synthesize_narration(
            "Electricity usage well above the six month average, flagged automatically, "
            "with a concrete, prioritized fix.",
            AUDIO / "report.wav",
        )

        def _report_actions(page):
            # goto() blocks until the response (and the slow OCR pipeline behind
            # it) fully completes, so everything after this line is real,
            # already-loaded report content — hold it well past the narration
            # length so the end-anchored trim below never reaches back into the
            # blank loading frames that came before it.
            page.goto(f"http://127.0.0.1:8951/report?bills_folder=fixtures/bills_demo")
            page.wait_for_timeout(2000)
            page.mouse.wheel(0, 400)
            page.wait_for_timeout(6000)

        report_webm = record_dashboard_clip("/", _report_actions, WORK / "report.webm")
        report_clip = WORK / "report_clip.mp4"
        webm_clip_with_audio(report_webm, report_wav, report_clip)
        clips.append(report_clip)
    finally:
        server.terminate()
        server.wait(timeout=10)

    close_scenes = [
        ("sources", "Cited, published sources", "Every emission factor is a published EPA figure, cited in the README. No paid API. Nothing leaves your machine."),
        ("close", "GreenLedger", "Built for Orion Hackathon twenty twenty six."),
    ]
    for key, title, narration in close_scenes:
        img = render_card(f"{key}.png", title, narration)
        wav = synthesize_narration(narration, AUDIO / f"{key}.wav")
        clip = WORK / f"{key}_clip.mp4"
        image_clip_with_audio(img, wav, clip)
        clips.append(clip)

    concat_clips(clips, OUTPUT)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()

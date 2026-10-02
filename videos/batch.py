"""Batch orchestrator for all 3 demo videos (Task 21).

Pipeline per brand:
  1. English voiceover (en-IN-PrabhatNeural, -5%) -> tmp/<brand>_voice.mp3
  2. fit audio to <= 58s (hard 60s cap)
  3a. portfolio: 6 static slides -> Ken Burns slideshow -> compose
  3b. gymos/webscraper: live Playwright recording -> compose
      (fallback: section screenshots + Ken Burns slideshow)
"""

from pathlib import Path

from videos.assets import ASSETS_DIR, make_all_assets
from videos.compose_video import (
    MAX_DURATION,
    audio_duration,
    compose_video,
    fit_audio_to_max,
    leading_blank_seconds,
)
from videos.generate_voiceover import voiceover_for_brand
from videos.portfolio_slides import generate_portfolio_slides
from videos.portfolio_video import build_portfolio_video, build_slideshow, slide_durations
from videos.record_website import BRAND_ACTIONS, capture_section_shots, record_brand

ROOT = Path(__file__).resolve().parent
TMP_DIR = ROOT / "tmp"
OUTPUT_DIR = ROOT / "output"

# Recording clock per brand (voiceover is the trim authority via -shortest).
# Budgets run ~3s long: leading_blank_seconds() trims the white loader.
RECORD_SECONDS = {"gymos": 60.0, "webscraper": 60.0}

# Anchors for the screenshot fallback (same order as the record timelines).
FALLBACK_ANCHORS = {
    "gymos": ["TRAIN HARD", "CHOOSE YOUR PLAN", "MEET THE EXPERTS",
              "PREMIUM FACILITIES", "REAL RESULTS", "VISIT US"],
    "webscraper": ["Verified B2B Leads", "What B2B Lead Services",
                   "How Much Do B2B Leads Cost", "Real sample",
                   "How Fast Can You Deliver", "Why Web Scraper Studio",
                   "Coming Soon"],
}


def _prepare_audio(brand: str) -> Path:
    raw = voiceover_for_brand(brand, TMP_DIR / f"{brand}_voice.mp3")
    fit = TMP_DIR / f"{brand}_voice_fit.mp3"
    return fit_audio_to_max(raw, fit, MAX_DURATION)


def _prepare_logo(brand: str) -> Path:
    logo = ASSETS_DIR / f"{brand}_logo.png"
    if not logo.exists():
        make_all_assets(ASSETS_DIR)
    return logo


def build_portfolio() -> dict:
    audio = _prepare_audio("portfolio")
    logo = _prepare_logo("portfolio")
    slides = generate_portfolio_slides(TMP_DIR / "portfolio")
    out = OUTPUT_DIR / "portfolio_60s.mp4"
    build_portfolio_video(slides, audio, logo, out, TMP_DIR / "portfolio_video")
    return _summarize("portfolio", out)


def build_recorded_brand(brand: str) -> dict:
    audio = _prepare_audio(brand)
    logo = _prepare_logo(brand)
    out = OUTPUT_DIR / f"{brand}_60s.mp4"
    url, _ = BRAND_ACTIONS[brand]
    try:
        webm = record_brand(brand, RECORD_SECONDS[brand], TMP_DIR / f"{brand}_record.webm")
        ss = leading_blank_seconds(webm)
        if ss:
            print(f"{brand}: trimming {ss:.2f}s blank leader")
        total = min(audio_duration(audio), RECORD_SECONDS[brand])
        compose_video(webm, audio, logo, out, total, ss=ss)
        method = "live-record"
    except Exception as exc:  # noqa: BLE001 - fallback to slideshow
        print(f"Recording failed for {brand} ({exc}); using screenshot fallback")
        shots = capture_section_shots(url, FALLBACK_ANCHORS[brand], TMP_DIR / f"{brand}_shots")
        audio_dur = audio_duration(audio)
        durations = slide_durations(audio_dur, target_total=min(audio_dur + 2.0, MAX_DURATION))
        # slide_durations uses portfolio minimums; rescale to shot count.
        per = sum(durations) / len(shots)
        slideshow = build_slideshow(shots, [per] * len(shots), TMP_DIR / f"{brand}_video")
        compose_video(slideshow, audio, logo, out, sum([per] * len(shots)))
        method = "screenshot-fallback"
    result = _summarize(brand, out)
    result["method"] = method
    return result


def _summarize(brand: str, output: Path) -> dict:
    import subprocess

    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
         "-of", "default=noprint_wrappers=1", str(output)],
        capture_output=True, text=True, check=True,
    )
    info = dict(
        line.split("=", 1) for line in out.stdout.strip().splitlines() if "=" in line
    )
    return {
        "brand": brand,
        "output": str(output),
        "duration": float(info.get("duration", 0)),
        "size_mb": round(int(info.get("size", 0)) / (1024 * 1024), 2),
    }


def build_all() -> list:
    results = [build_portfolio()]
    for brand in ("gymos", "webscraper"):
        results.append(build_recorded_brand(brand))
    for r in results:
        print(f"{r['brand']}: {r['output']} {r['duration']:.1f}s {r['size_mb']}MB "
              f"({r.get('method', 'slideshow')})")
    return results


BUILDERS = {
    "portfolio": build_portfolio,
    "gymos": lambda: build_recorded_brand("gymos"),
    "webscraper": lambda: build_recorded_brand("webscraper"),
}

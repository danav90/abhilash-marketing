"""Live website screen recording via Playwright (Task 21, Parts 2-3).

record_website(url, actions, duration) -> .webm at 1920x1080.
Screenshot fallback: capture_section_shots() for Ken Burns fallback.
"""

import asyncio
import shutil
from pathlib import Path

WIDTH = 1920
HEIGHT = 1080

GYMOS_URL = "https://bodycare-gym.vercel.app/"
WEBSCRAPER_URL = "https://webscraperstudio.vercel.app/"

# NOTE (adapted from brief): the GymOS owner dashboard sits behind owner login
# and no demo credentials exist, so the recording covers the live
# GymOS-powered customer site: hero -> owner login page -> plans (fee
# context) -> trainers/facilities -> testimonials -> contact CTA -> hero.
#
# scroll_to uses role="heading" anchors: generic text matches sticky nav
# links (already in view) and would never scroll.
GYMOS_ACTIONS = [
    {"do": "goto", "url": GYMOS_URL},
    {"do": "wait", "s": 5.0},
    {"do": "click", "text": "Login"},
    {"do": "wait", "s": 6.0},
    {"do": "back"},
    {"do": "wait", "s": 2.0},
    {"do": "scroll_to", "text": "CHOOSE YOUR PLAN", "role": "heading"},
    {"do": "wait", "s": 6.0},
    {"do": "hover", "text": "Choose Quarterly"},
    {"do": "wait", "s": 3.0},
    {"do": "scroll_to", "text": "MEET THE EXPERTS", "role": "heading"},
    {"do": "wait", "s": 6.0},
    {"do": "scroll_to", "text": "PREMIUM FACILITIES", "role": "heading"},
    {"do": "wait", "s": 6.0},
    {"do": "scroll_to", "text": "REAL RESULTS", "role": "heading"},
    {"do": "wait", "s": 5.0},
    {"do": "scroll_to", "text": "VISIT US", "role": "heading"},
    {"do": "wait", "s": 5.0},
    {"do": "goto", "url": GYMOS_URL},
    {"do": "wait", "s": 4.0},
]

WEBSCRAPER_ACTIONS = [
    {"do": "goto", "url": WEBSCRAPER_URL},
    {"do": "wait", "s": 6.0},
    {"do": "scroll_to", "text": "What B2B Lead Services", "role": "heading"},
    {"do": "wait", "s": 7.0},
    {"do": "scroll_to", "text": "How Much Do B2B Leads Cost", "role": "heading"},
    {"do": "wait", "s": 6.0},
    {"do": "hover", "text": "GROWTH"},
    {"do": "wait", "s": 3.0},
    {"do": "scroll_to", "text": "Real sample", "role": "heading"},
    {"do": "wait", "s": 7.0},
    {"do": "scroll_to", "text": "How Fast Can You Deliver", "role": "heading"},
    {"do": "wait", "s": 7.0},
    {"do": "scroll_to", "text": "Why Web Scraper Studio", "role": "heading"},
    {"do": "wait", "s": 6.0},
    {"do": "scroll_bottom"},
    {"do": "wait", "s": 6.0},
]

BRAND_ACTIONS = {
    "gymos": (GYMOS_URL, GYMOS_ACTIONS),
    "webscraper": (WEBSCRAPER_URL, WEBSCRAPER_ACTIONS),
}


async def _run_action(page, action: dict, deadline: float) -> None:
    """Execute one action; any per-action failure degrades to a short wait."""
    import time

    if time.monotonic() >= deadline:
        return
    do = action.get("do")
    try:
        if do == "goto":
            try:
                await page.goto(action["url"], wait_until="networkidle", timeout=15000)
            except Exception:
                await page.goto(action["url"], wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1200)
        elif do == "wait":
            await page.wait_for_timeout(int(action.get("s", 2.0) * 1000))
        elif do == "scroll_to":
            y_before = await page.evaluate("() => window.scrollY")
            try:
                if action.get("role") == "heading":
                    loc = page.get_by_role("heading", name=action["text"]).first
                else:
                    loc = page.get_by_text(action["text"], exact=False).first
                await loc.scroll_into_view_if_needed(timeout=5000)
                await page.evaluate("window.scrollBy(0, -100)")
            except Exception:
                pass
            y_after = await page.evaluate("() => window.scrollY")
            if abs(y_after - y_before) < 50:
                # Anchor already in view (e.g. sticky nav match): proportional fallback.
                frac = action.get("frac", 0.5)
                await page.evaluate(
                    "(f) => window.scrollTo(0, document.body.scrollHeight * f)", frac,
                )
        elif do == "scroll_bottom":
            await page.evaluate(
                "() => window.scrollTo(0, document.body.scrollHeight * 0.94)")
        elif do == "scroll_by":
            await page.evaluate("(px) => window.scrollBy(0, px)", action.get("px", 600))
        elif do == "hover":
            try:
                await page.get_by_text(action["text"], exact=False).first.hover(timeout=5000)
            except Exception:
                pass
        elif do == "click":
            try:
                await page.get_by_text(action["text"], exact=True).first.click(timeout=5000)
                await page.wait_for_timeout(1200)
            except Exception:
                pass
        elif do == "back":
            await page.go_back(wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1000)
    except Exception:
        await page.wait_for_timeout(800)


async def record_website_async(
    url: str,
    actions: list,
    duration: float,
    output: Path,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> Path:
    """Record scripted browsing to .webm. Stops at `duration` seconds of actions."""
    import time
    from playwright.async_api import async_playwright

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_video_dir = output.parent / "_record_tmp"
    tmp_video_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            # Pre-warm: defeat Vercel cold starts outside the recording so the
            # video opens on rendered content, not a blank white loader.
            warm_urls = []
            for a in actions:
                if a.get("do") == "goto" and a.get("url") not in warm_urls:
                    warm_urls.append(a["url"])
            try:
                warm_ctx = await browser.new_context(
                    viewport={"width": width, "height": height})
                warm_page = await warm_ctx.new_page()
                for url in warm_urls:
                    try:
                        await warm_page.goto(url, wait_until="networkidle", timeout=30000)
                        await warm_page.wait_for_timeout(800)
                    except Exception:
                        pass
                await warm_ctx.close()
            except Exception:
                pass
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=str(tmp_video_dir),
                record_video_size={"width": width, "height": height},
            )
            page = await context.new_page()
            deadline = time.monotonic() + duration
            for action in actions:
                if time.monotonic() >= deadline:
                    break
                await _run_action(page, action, deadline)
            # Pad with a closing hold if actions finished early.
            remaining = deadline - time.monotonic()
            if remaining > 1.0:
                await page.wait_for_timeout(int(min(remaining, 4.0) * 1000))
            await context.close()
        finally:
            await browser.close()

    webms = sorted(tmp_video_dir.glob("*.webm"))
    if not webms:
        raise RuntimeError("Playwright saved no video file")
    shutil.move(str(webms[0]), str(output))
    shutil.rmtree(tmp_video_dir, ignore_errors=True)
    return output


def record_website(
    url: str,
    actions: list,
    duration: float,
    output: Path,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> Path:
    """Sync wrapper around record_website_async."""
    return asyncio.run(record_website_async(url, actions, duration, output, width, height))


def record_brand(brand: str, duration: float, output: Path) -> Path:
    """Record a brand's scripted timeline. Raises KeyError for unknown brand."""
    key = (brand or "").strip().lower()
    if key not in BRAND_ACTIONS:
        raise KeyError(f"No recording script for: {brand!r}")
    url, actions = BRAND_ACTIONS[key]
    return record_website(url, actions, duration, output)


async def capture_section_shots_async(url: str, anchors: list, out_dir: Path) -> list:
    """Fallback: full-viewport screenshots at section anchors (Ken Burns input)."""
    from playwright.async_api import async_playwright

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)
            for i, anchor in enumerate(anchors):
                try:
                    loc = page.get_by_text(anchor, exact=False).first
                    await loc.scroll_into_view_if_needed(timeout=5000)
                    await page.evaluate("window.scrollBy(0, -100)")
                except Exception:
                    await page.evaluate(
                        "(i, n) => window.scrollTo(0, document.body.scrollHeight * i / n)",
                        i, len(anchors),
                    )
                await page.wait_for_timeout(600)
                shot = out_dir / f"shot_{i:02d}.png"
                await page.screenshot(path=str(shot))
                paths.append(shot)
        finally:
            await browser.close()
    return paths


def capture_section_shots(url: str, anchors: list, out_dir: Path) -> list:
    """Sync wrapper around capture_section_shots_async."""
    return asyncio.run(capture_section_shots_async(url, anchors, out_dir))

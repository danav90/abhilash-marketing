"""Portfolio slideshow slides (Task 21, Part 1). 6 slides at 1920x1080.

Reuses the Task 18/20 HTML-to-Image pattern: render_template + string replace.
"""

import asyncio
from html import escape
from pathlib import Path

from src.social.generate_image import render_template

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
SLIDE_TEMPLATE = TEMPLATES_DIR / "video_slide.html"

SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080

BG = "#0F172A"
ACCENT = "#38BDF8"
BRAND = "ABHILASH // VERSE"

# Minimum on-screen seconds per slide (sums to 27s; stretched to ~55s at build).
SLIDE_MIN_DURATIONS = [3.0, 5.0, 5.0, 5.0, 5.0, 4.0]


def _pills(items, hot_index: int = -1) -> str:
    parts = []
    for i, t in enumerate(items):
        cls = "pill hot" if i == hot_index else "pill"
        parts.append(f'<span class="{cls}">{escape(t)}</span>')
    return "".join(parts)


def _items(items) -> str:
    divs = "".join(
        f'<div class="item"><span class="sym">&#9670;</span>{escape(t)}</div>' for t in items
    )
    return f'<div class="item-grid">{divs}</div>'


def _steps(steps) -> str:
    divs = "".join(
        f'<div class="step"><div class="n">{i + 1}</div><div class="t">{escape(t)}</div></div>'
        for i, t in enumerate(steps)
    )
    return f'<div class="step-grid">{divs}</div>'


SLIDES = [
    {
        "kicker": "Portfolio // Intro",
        "headline": "ABHILASH SINGH RAJPUT",
        "subtext": "Web Developer and AI Engineer, Delhi, India",
        "body": "",
        "footer_main": "abhilash-verse.vercel.app",
        "footer_side": "Intro",
    },
    {
        "kicker": "What I build",
        "headline": "I build websites that get local businesses more customers.",
        "subtext": "Websites  |  Apps  |  SaaS  |  Automation",
        "body": "",
        "footer_main": "Delivered in 3-5 days. Starting at Rs 1,500/month.",
        "footer_side": "",
    },
    {
        "kicker": "Tech stack",
        "headline": "Full-stack capability",
        "subtext": "From database to deploy",
        "body": _pills(["Astro", "React", "Next.js", "Python", "FastAPI", "PostgreSQL", "AI Integration"], hot_index=6),
        "footer_main": "Modern stack, production deploys",
        "footer_side": "",
    },
    {
        "kicker": "Services and pricing",
        "headline": "Services and pricing",
        "subtext": "",
        "body": _items([
            "Business Websites Rs 1,500",
            "E-commerce Stores",
            "Booking Systems",
            "WhatsApp Automation",
            "Google Business Setup",
            "Custom Web Apps",
        ]),
        "footer_main": "Transparent pricing, no hidden costs",
        "footer_side": "",
    },
    {
        "kicker": "Process",
        "headline": "How I work",
        "subtext": "",
        "body": _steps([
            "You tell me your business",
            "Free demo in 48 hours",
            "Full site in 3-5 days",
            "Live plus support",
        ]),
        "footer_main": "50% advance, 50% on delivery",
        "footer_side": "30 days support included",
    },
    {
        "kicker": "Contact",
        "headline": "Let us build something",
        "subtext": "abhilash-verse.vercel.app",
        "body": "",
        "footer_main": "Delhi-based",
        "footer_side": "Working remotely with businesses anywhere",
    },
]


def build_slide_variables(slide: dict) -> dict:
    return {
        "BG_COLOR": BG,
        "ACCENT_COLOR": ACCENT,
        "BRAND_NAME": escape(BRAND),
        "KICKER": escape(slide.get("kicker", "")),
        "HEADLINE": escape(slide.get("headline", "")),
        "SUBTEXT": escape(slide.get("subtext", "")),
        "BODY_HTML": slide.get("body", ""),
        "FOOTER_MAIN": escape(slide.get("footer_main", "")),
        "FOOTER_SIDE": escape(slide.get("footer_side", "")),
    }


def generate_portfolio_slides(out_dir: Path) -> list:
    """Render all 6 slides to PNG. Returns list of Paths in order."""
    out_dir = Path(out_dir)
    paths = []
    for i, slide in enumerate(SLIDES, start=1):
        out = out_dir / f"slide_{i:02d}.png"
        asyncio.run(
            render_template(
                SLIDE_TEMPLATE, build_slide_variables(slide),
                SLIDE_WIDTH, SLIDE_HEIGHT, out,
            )
        )
        paths.append(out)
    return paths

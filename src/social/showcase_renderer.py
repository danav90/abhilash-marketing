"""Showcase sheet renderer (Task 20). One data-driven template, 1080x1620 per brand."""

import asyncio
from html import escape
from pathlib import Path

from src.social.generate_image import render_template
from src.social.showcase_data import SHOWCASE, SHOWCASE_HEIGHT, SHOWCASE_WIDTH

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
SHOWCASE_TEMPLATE = TEMPLATES_DIR / "showcase.html"


def _qualities_html(items) -> str:
    parts = []
    for title, desc in items:
        parts.append(
            '<div class="card q-item"><div class="q-sym">&#9670;</div>'
            f'<div class="q-title">{escape(title)}</div>'
            f'<div class="q-desc">{escape(desc)}</div></div>'
        )
    return "".join(parts)


def _tech_html(items) -> str:
    return "".join(f'<span class="pill">{escape(t)}</span>' for t in items)


def _li_html(items, sym="&#9673;") -> str:
    return "".join(f'<li><span class="sym">{sym}</span>{escape(t)}</li>' for t in items)


def _projects_html(projects) -> str:
    parts = []
    for name, status, desc in projects:
        dim = " dim" if status.upper() in ("IN PROGRESS", "PRO") else ""
        parts.append(
            '<div class="card proj">'
            f'<span class="p-name">{escape(name)}</span>'
            f'<span class="p-status{dim}">{escape(status)}</span>'
            f'<div class="p-desc">{escape(desc)}</div></div>'
        )
    return "".join(parts)


def _projects_cols(n: int) -> str:
    if n <= 3:
        return "cols-3"
    if n == 4 or n == 6:
        return "cols-2" if n == 4 else "cols-3"
    return "cols-5"


def _services_html(services) -> str:
    return "".join(
        f'<div class="card svc"><div class="s-name">{escape(n)}</div>'
        f'<div class="s-price">{escape(p)}</div></div>'
        for n, p in services
    )


def build_variables(brand: str) -> dict:
    """Build the full {{VAR}} -> HTML map for a brand. No {{...}} left unreplaced."""
    key = (brand or "").strip().lower()
    if key not in SHOWCASE:
        raise KeyError(f"Unknown showcase brand: {brand!r} (expected one of {sorted(SHOWCASE)})")
    d = SHOWCASE[key]
    return {
        "BG_COLOR": d["bg"],
        "ACCENT_COLOR": d["accent"],
        "HEADER_LOGO": escape(d["header_logo"]),
        "HEADER_TAGLINE": escape(d["header_tagline"]),
        "HERO_LINE": escape(d["hero_line"]),
        "HERO_SUBTITLE": escape(d["hero_subtitle"]),
        "HERO_LOCATION": escape(d["hero_location"]),
        "CTA_PRIMARY": escape(d["cta_primary"]),
        "CTA_SECONDARY": escape(d["cta_secondary"]),
        "QUALITIES_HTML": _qualities_html(d["qualities"]),
        "TECH_HTML": _tech_html(d["tech"]),
        "FEATURES_HTML": _li_html(d["features"], "&#9673;"),
        "OPTIMIZATION_HTML": _li_html(d["optimization"], "&#9650;"),
        "PROJECTS_TITLE": escape(d["projects_title"]),
        "PROJECTS_COLS": _projects_cols(len(d["projects"])),
        "PROJECTS_HTML": _projects_html(d["projects"]),
        "SERVICES_TITLE": escape(d["services_title"]),
        "SERVICES_HTML": _services_html(d["services"]),
        "GUARANTEES_HTML": _li_html(d["guarantees"], "&#9670;"),
        "SCORES_TITLE": escape(d["scores_title"]),
        "SCORES_HTML": "".join(
            f'<span class="score"><div class="n">{escape(n)}</div><div class="l">{escape(l)}</div></span>'
            for n, l in d["scores"]
        ),
        "DEPLOYED_HTML": escape(d["deployed"]),
        "CONNECT_HTML": escape("  |  ".join(d["connect"])),
        "FOOTER_TAGLINE": escape(d["footer_tagline"]),
        "FOOTER_HASHTAGS": escape(d["footer_hashtags"]),
    }


def render_showcase(brand: str, output: Path) -> Path:
    """Render one brand showcase sheet at 1080x1620 via the Task 18 pipeline."""
    variables = build_variables(brand)
    output_path = Path(output)
    return asyncio.run(
        render_template(SHOWCASE_TEMPLATE, variables, SHOWCASE_WIDTH, SHOWCASE_HEIGHT, output_path)
    )

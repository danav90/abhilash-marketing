"""HTML-to-Image rendering via Playwright screenshot."""

import asyncio
import tempfile
from pathlib import Path

from playwright import async_api

from src.social.renderer import BRAND_COLORS, BRAND_DISPLAY, BRAND_SITES, inject_brand_css

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"

INSTAGRAM_CAROUSEL_SIZE = (1080, 1350)
LINKEDIN_SINGLE_SIZE = (1200, 627)

DIMENSIONS = {
    ("instagram", "single"): (1080, 1080),
    ("instagram", "carousel"): (1080, 1350),
    ("instagram", "reel"): (1080, 1920),
    ("linkedin", "single"): (1200, 627),
    ("linkedin", "document"): (1080, 1080),
    ("linkedin", "text"): (1080, 1080),
}


def resolve_dimensions(platform: str = "instagram", post_type: str = "") -> tuple:
    """Pick (width, height) for (platform, type).

    Empty post_type preserves legacy behavior:
      instagram -> 1080x1350 (carousel), linkedin -> 1200x627 (single).
    """
    plat = (platform or "instagram").strip().lower()
    ptype = (post_type or "").strip().lower()
    if not ptype:
        if plat == "linkedin":
            return LINKEDIN_SINGLE_SIZE
        return INSTAGRAM_CAROUSEL_SIZE
    key = (plat, ptype)
    if key in DIMENSIONS:
        return DIMENSIONS[key]
    if plat == "linkedin":
        return LINKEDIN_SINGLE_SIZE
    return INSTAGRAM_CAROUSEL_SIZE


def _inline_base_css(html: str, template_path: Path) -> str:
    """Inline brand_base.css so temp HTML renders even outside templates dir."""
    marker = "brand_base.css"
    if marker not in html:
        return html
    css_path = template_path.parent / "brand_base.css"
    try:
        css = css_path.read_text(encoding="utf-8")
    except OSError:
        return html
    inline = "<style>\n" + css + "\n</style>"
    # Replace <link ... brand_base.css ...> with inline style.
    import re

    pattern = re.compile(r'<link[^>]*brand_base\.css[^>]*>', re.IGNORECASE)
    html, n = pattern.subn(inline, html, count=1)
    if n == 0:
        # Fallback: prepend to head.
        if "</head>" in html:
            html = html.replace("</head>", inline + "\n</head>", 1)
        else:
            html = inline + "\n" + html
    return html


async def render_template(
    template_path: Path, variables: dict, width: int, height: int, output_path: Path
) -> Path:
    """Render an HTML template to PNG with Playwright.

    - Read HTML template
    - Replace {{VAR}} placeholders with variables dict values
    - Write to temp HTML file
    - Use Playwright Chromium (headless) to open file://temp.html
    - Set viewport to (width, height)
    - Wait for network idle (fonts loaded)
    - page.screenshot(path=output_path, full_page=False)
    - Delete temp HTML
    - Return output_path
    """
    template_path = Path(template_path)
    output_path = Path(output_path)
    html = template_path.read_text(encoding="utf-8")

    # Inline shared CSS first so temp file is self-contained.
    html = _inline_base_css(html, template_path)

    # Replace {{VAR}} placeholders (simple string replace, no Jinja).
    variables = dict(variables or {})
    for key, value in variables.items():
        if key.startswith("__"):
            continue
        html = html.replace("{{" + str(key) + "}}", str(value))
        # Also support lowercase variant just in case.
        # (Templates use UPPER_SNAKE; keep exact match primary.)

    # Inject brand colors if caller supplied __brand.
    brand = variables.get("__brand")
    if brand:
        html = inject_brand_css(html, str(brand))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write temp HTML next to template so any relative assets still resolve.
    tmp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", dir=str(template_path.parent), delete=False, encoding="utf-8"
    )
    tmp_path = Path(tmp_file.name)
    try:
        tmp_file.write(html)
        tmp_file.close()

        async with async_api.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(viewport={"width": width, "height": height})
                await page.goto(tmp_path.as_uri(), wait_until="networkidle")
                await page.screenshot(path=str(output_path), full_page=False)
            finally:
                await browser.close()
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    return output_path


def render_single(template: str, brand: str, variables: dict, output: Path) -> Path:
    """Sync wrapper around render_template with auto dimensions + brand colors.

    Dimensions picked from (platform, type):
      instagram single 1080x1080, carousel 1080x1350, reel 1080x1920,
      linkedin single 1200x627, document/text 1080x1080.
    Empty type preserves legacy: instagram -> 1080x1350, linkedin -> 1200x627.
    Auto-selects brand colors + URL based on `brand` arg.
    """
    brand_key = (brand or "").strip().lower()
    colors = BRAND_COLORS.get(brand_key, BRAND_COLORS["webscraper"])

    variables = dict(variables or {})
    # Platform + post type drive dimensions.
    platform = str(variables.get("platform", "instagram")).strip().lower() or "instagram"
    post_type = str(variables.get("type", variables.get("post_type", ""))).strip().lower()

    width, height = resolve_dimensions(platform, post_type)

    # Defaults for common placeholders.
    if "BRAND" not in variables or not variables["BRAND"]:
        variables["BRAND"] = BRAND_DISPLAY.get(brand_key, brand)
    site = BRAND_SITES.get(brand_key, "")
    # URL badge: support both {{URL}} (new) and {{WEBSITE}} (legacy).
    if "URL" not in variables or not variables["URL"]:
        variables["URL"] = variables.get("WEBSITE") or site
    if "WEBSITE" not in variables or not variables["WEBSITE"]:
        variables["WEBSITE"] = variables.get("URL") or site
    if "SLIDE_NUM" not in variables:
        variables["SLIDE_NUM"] = ""

    # Expose brand + explicit hex codes for testability and template use.
    variables["__brand"] = brand_key
    variables["BRAND_BG"] = colors["bg"]
    variables["BRAND_ACCENT"] = colors["accent"]
    variables["BRAND_TEXT"] = colors["text"]

    name = (template or "").strip()
    if name.endswith(".html"):
        name = name[:-5]
    template_path = TEMPLATES_DIR / f"{name}.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    output_path = Path(output)
    return asyncio.run(render_template(template_path, variables, width, height, output_path))

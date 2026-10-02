"""Brand watermark logo generator (Task 21). White wordmarks on transparency.

Kept deliberately simple: overlaid at 15% opacity top-left, subtle by design.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

LOGOS = {
    # name: (lines, accent_word_index, accent_color)
    "portfolio": (["ABHILASH // VERSE"], [1], (56, 189, 248, 255)),
    "gymos": (["GYMOS"], [], None),
    "webscraper": (["WEB SCRAPER STUDIO"], [], None),
}

ACCENT_GYMOS = (34, 197, 94, 255)
WHITE = (255, 255, 255, 255)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_logo(brand: str, output: Path) -> Path:
    """Render brand wordmark PNG (transparent bg). Returns output Path."""
    key = (brand or "").strip().lower()
    if key not in LOGOS:
        raise KeyError(f"Unknown brand: {brand!r}")
    font = _font(72)
    text = LOGOS[key][0][0]
    # Measure with a scratch image.
    scratch = Image.new("RGBA", (10, 10))
    d0 = ImageDraw.Draw(scratch)
    bbox = d0.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0] + 60, bbox[3] - bbox[1] + 40
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 30
    if key == "portfolio":
        # "ABHILASH " white, "//" sky accent, " VERSE" white.
        for part, color in (("ABHILASH ", WHITE), ("//", (56, 189, 248, 255)), (" VERSE", WHITE)):
            d.text((x, 20), part, font=font, fill=color)
            x += d.textlength(part, font=font)
    elif key == "gymos":
        for part, color in (("GYM", WHITE), ("OS", ACCENT_GYMOS)):
            d.text((x, 20), part, font=font, fill=color)
            x += d.textlength(part, font=font)
    else:
        d.text((30, 20), text, font=font, fill=WHITE)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output))
    return output


def make_all_assets(assets_dir: Path = ASSETS_DIR) -> dict:
    """Generate all 3 logos. Returns {brand: Path}."""
    out = {}
    for brand in LOGOS:
        out[brand] = make_logo(brand, Path(assets_dir) / f"{brand}_logo.png")
    return out

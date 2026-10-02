"""Tests for social visual generator (Playwright mocked)."""

import asyncio
import json
from pathlib import Path
from unittest import mock

from src.social import batch_generator as bg_mod
from src.social import generate_image as gi_mod
from src.social.renderer import BRAND_COLORS, inject_brand_css


class _FakePage:
    def __init__(self, out_paths: list, viewports: list):
        self._out_paths = out_paths
        self._viewports = viewports

    async def goto(self, url, wait_until=None):
        return None

    async def screenshot(self, path=None, full_page=False):
        self._out_paths.append(str(path))
        # Write minimal valid PNG so PIL can verify dimensions if needed.
        # Tests that check dimensions mock render_template instead, so touch is enough.
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"fakepng")
        return None


class _FakeBrowser:
    def __init__(self, out_paths: list, viewports: list):
        self._out_paths = out_paths
        self._viewports = viewports

    async def new_page(self, viewport=None):
        self._viewports.append(dict(viewport or {}))
        return _FakePage(self._out_paths, self._viewports)

    async def close(self):
        return None


class _FakePWContext:
    def __init__(self, out_paths: list, viewports: list):
        self._out_paths = out_paths
        self._viewports = viewports
        self.chromium = self

    async def launch(self, headless=True):
        return _FakeBrowser(self._out_paths, self._viewports)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


def _make_fake_playwright(out_paths: list, viewports: list):
    def _factory():
        return _FakePWContext(out_paths, viewports)

    return _factory


def test_render_template_replaces_variables(tmp_path):
    """Mock page.screenshot, verify temp HTML had vars replaced."""
    tpl = tmp_path / "quote.html"
    tpl.write_text("<html><head></head><body>{{HEADLINE}}|{{SUBTEXT}}</body></html>", encoding="utf-8")
    out = tmp_path / "out.png"

    captured_html: list = []
    real_ntf = gi_mod.tempfile.NamedTemporaryFile

    class _CaptureFile:
        def __init__(self, *args, **kwargs):
            self._f = real_ntf(*args, **kwargs)
            self.name = self._f.name

        def write(self, data):
            captured_html.append(data)
            return self._f.write(data)

        def close(self):
            return self._f.close()

    out_paths: list = []
    viewports: list = []
    with mock.patch.object(
        gi_mod.async_api, "async_playwright", _make_fake_playwright(out_paths, viewports)
    ), mock.patch.object(gi_mod.tempfile, "NamedTemporaryFile", _CaptureFile):
        result = asyncio.run(
            gi_mod.render_template(
                tpl,
                {"HEADLINE": "Hello World", "SUBTEXT": "Sub text here"},
                1080,
                1350,
                out,
            )
        )

    assert Path(result) == out
    assert out.exists()
    assert captured_html, "temp HTML content was not captured"
    html = captured_html[0]
    assert "Hello World" in html
    assert "Sub text here" in html
    assert "{{HEADLINE}}" not in html
    assert "{{SUBTEXT}}" not in html
    # Temp file must be deleted after render.
    assert len(list(tmp_path.glob("*.html"))) == 1  # only the source template remains


def test_render_single_selects_correct_dimensions(tmp_path):
    """Instagram default 1080x1350, linkedin 1200x627."""
    calls = []

    async def _fake_render(template_path, variables, width, height, output_path):
        calls.append({"width": width, "height": height, "variables": dict(variables)})
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"x")
        return Path(output_path)

    with mock.patch.object(gi_mod, "render_template", side_effect=_fake_render):
        gi_mod.render_single(
            "quote", "webscraper", {"HEADLINE": "H", "platform": "instagram"}, tmp_path / "a.png"
        )
        gi_mod.render_single(
            "quote", "webscraper", {"HEADLINE": "H", "platform": "linkedin"}, tmp_path / "b.png"
        )

    assert len(calls) == 2
    assert (calls[0]["width"], calls[0]["height"]) == (1080, 1350)
    assert (calls[1]["width"], calls[1]["height"]) == (1200, 627)


def test_render_single_brand_colors_applied(tmp_path):
    """Portfolio bg #0F172A, gymos/webscraper bg #1F4E78 via variables + CSS injection."""
    # Direct CSS injection check.
    assert "#0F172A" in inject_brand_css("<html><head></head></html>", "portfolio")
    assert "#1F4E78" in inject_brand_css("<html><head></head></html>", "gymos")
    assert "#1F4E78" in inject_brand_css("<html><head></head></html>", "webscraper")
    assert BRAND_COLORS["portfolio"]["bg"] == "#0F172A"
    assert BRAND_COLORS["gymos"]["bg"] == "#1F4E78"

    # render_single must forward hex codes to render_template.
    seen = {}

    async def _fake_render(template_path, variables, width, height, output_path):
        seen[str(output_path)] = dict(variables)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"x")
        return Path(output_path)

    with mock.patch.object(gi_mod, "render_template", side_effect=_fake_render):
        gi_mod.render_single("quote", "portfolio", {"HEADLINE": "H"}, tmp_path / "p.png")
        gi_mod.render_single("quote", "gymos", {"HEADLINE": "H"}, tmp_path / "g.png")

    p_vars = seen[str(tmp_path / "p.png")]
    g_vars = seen[str(tmp_path / "g.png")]
    # Hex must appear somewhere in forwarded variables (BRAND_BG / __brand path).
    assert "#0F172A" in str(list(p_vars.values()))
    assert "#1F4E78" in str(list(g_vars.values()))


def test_batch_generator_reads_config(tmp_path):
    """Mock batch.json with 2 entries, verify 2 render calls."""
    cfg = {
        "posts": [
            {
                "template": "quote",
                "brand": "gymos",
                "platform": "instagram",
                "variables": {"HEADLINE": "A"},
                "output": "posts/a.png",
            },
            {
                "template": "quote",
                "brand": "webscraper",
                "platform": "instagram",
                "variables": {"HEADLINE": "B"},
                "output": "posts/b.png",
            },
        ]
    }
    cfg_path = tmp_path / "batch.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    calls = []

    def _fake_render_single(template, brand, variables, output):
        calls.append((template, brand, dict(variables), str(output)))
        return Path(output)

    with mock.patch.object(bg_mod, "render_single", side_effect=_fake_render_single):
        result = bg_mod.generate_batch(cfg_path)

    assert len(calls) == 2
    assert result["total"] == 2
    assert result["success"] == 2
    assert result["failed"] == []


def test_batch_generator_handles_failure(tmp_path):
    """One render raises, others continue."""
    cfg = {
        "posts": [
            {
                "template": "quote",
                "brand": "gymos",
                "platform": "instagram",
                "variables": {"HEADLINE": "A"},
                "output": "posts/a.png",
            },
            {
                "template": "quote",
                "brand": "gymos",
                "platform": "instagram",
                "variables": {"HEADLINE": "B"},
                "output": "posts/b.png",
            },
            {
                "template": "quote",
                "brand": "gymos",
                "platform": "instagram",
                "variables": {"HEADLINE": "C"},
                "output": "posts/c.png",
            },
        ]
    }
    cfg_path = tmp_path / "batch.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    def _flaky(template, brand, variables, output):
        if variables.get("HEADLINE") == "B":
            raise RuntimeError("boom")
        return Path(output)

    with mock.patch.object(bg_mod, "render_single", side_effect=_flaky):
        result = bg_mod.generate_batch(cfg_path)

    assert result["total"] == 3
    assert result["success"] == 2
    assert len(result["failed"]) == 1

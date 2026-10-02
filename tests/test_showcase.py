"""Tests for Task 20 showcase sheet generator (Playwright mocked)."""

import asyncio
import re
from pathlib import Path
from unittest import mock

from src.social import showcase_data as sd_mod
from src.social import showcase_renderer as sc_mod
from src.social.showcase_data import SHOWCASE, SHOWCASE_HEIGHT, SHOWCASE_WIDTH


def test_showcase_data_has_all_brands():
    assert set(SHOWCASE) == {"portfolio", "gymos", "webscraper"}
    for brand, d in SHOWCASE.items():
        for key in (
            "bg", "accent", "header_logo", "header_tagline", "hero_line",
            "hero_subtitle", "hero_location", "cta_primary", "cta_secondary",
            "qualities", "tech", "features", "optimization", "projects_title",
            "projects", "services_title", "services", "guarantees",
            "scores_title", "scores", "deployed", "connect",
            "footer_tagline", "footer_hashtags",
        ):
            assert key in d, f"{brand} missing {key}"
        assert len(d["qualities"]) == 5, f"{brand} qualities != 5"
        assert len(d["tech"]) >= 6, f"{brand} tech too thin"
    # Portfolio uses dark navy, others GymOS blue.
    assert SHOWCASE["portfolio"]["bg"] == "#0B1220"
    assert SHOWCASE["gymos"]["bg"] == "#1F4E78"
    assert SHOWCASE["webscraper"]["bg"] == "#1F4E78"


def test_render_showcase_replaces_variables(tmp_path):
    """Mock render_template, verify no {{...}} left in final HTML vars + dims exact."""
    captured = {}

    async def _fake_render(template_path, variables, width, height, output_path):
        captured.update({"template": str(template_path), "vars": dict(variables),
                         "width": width, "height": height})
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"x")
        return Path(output_path)

    out = tmp_path / "showcase_portfolio.png"
    with mock.patch.object(sc_mod, "render_template", side_effect=_fake_render):
        result = sc_mod.render_showcase("portfolio", out)

    assert Path(result) == out
    assert out.exists()
    assert captured["template"].endswith("showcase.html")
    assert (captured["width"], captured["height"]) == (1080, 1620)
    blob = " ".join(str(v) for v in captured["vars"].values())
    assert not re.search(r"\{\{[^}]+\}\}", blob), "unreplaced {{VAR}} left"
    assert "ABHILASH // VERSE" in blob
    assert "GymOS" in blob  # featured project present

    # Every {{VAR}} in the template must have a replacement.
    tpl_vars = set(re.findall(r"\{\{(\w+)\}\}", sc_mod.SHOWCASE_TEMPLATE.read_text(encoding="utf-8")))
    assert tpl_vars <= set(captured["vars"]), f"missing: {tpl_vars - set(captured['vars'])}"


def test_showcase_dimensions(tmp_path):
    """All 3 brands render at exactly 1080x1620 via the Task 18 pipeline."""
    calls = []

    async def _fake_render(template_path, variables, width, height, output_path):
        calls.append((width, height))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"x")
        return Path(output_path)

    with mock.patch.object(sc_mod, "render_template", side_effect=_fake_render):
        for brand in ("portfolio", "gymos", "webscraper"):
            sc_mod.render_showcase(brand, tmp_path / f"showcase_{brand}.png")

    assert len(calls) == 3
    assert all(c == (1080, 1620) for c in calls)
    assert (SHOWCASE_WIDTH, SHOWCASE_HEIGHT) == (1080, 1620)

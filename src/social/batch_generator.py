"""Bulk batch generation from batch.json config."""

import json
from pathlib import Path

from src.social.generate_image import render_single
from src.social import showcase_renderer as showcase_mod

OUTPUT_ROOT = Path(__file__).resolve().parents[2]


def generate_batch(config_path: Path) -> dict:
    """Read batch.json, render each entry via render_single.

    Entry format:
      {"template": "quote", "brand": "webscraper", "platform": "instagram",
       "variables": {...}, "output": "posts/webscraper_quote_01.png"}

    Continues on per-item failure (log + skip).
    Returns {"total": N, "success": M, "failed": [...], "output_dir": ...}.
    """
    config_path = Path(config_path)
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    posts = config.get("posts", [])
    total = len(posts)
    success = 0
    failed: list = []
    outputs: list = []

    for entry in posts:
        template = entry.get("template", "")
        brand = entry.get("brand", "")
        platform = entry.get("platform", "")
        post_type = entry.get("type", entry.get("post_type", ""))
        variables = dict(entry.get("variables") or {})
        # Merge top-level platform/type into variables so render_single picks dimensions.
        if platform and "platform" not in variables:
            variables["platform"] = platform
        if post_type and "type" not in variables and "post_type" not in variables:
            variables["type"] = post_type
        rel_output = entry.get("output", "")
        # Resolve relative outputs against repo root.
        out_path = Path(rel_output)
        if not out_path.is_absolute():
            out_path = OUTPUT_ROOT / rel_output
        try:
            if (template or "").strip().lower() == "showcase":
                # Task 20: data-driven showcase sheet (1080x1620), no variables needed.
                result = showcase_mod.render_showcase(brand, out_path)
            else:
                result = render_single(template, brand, variables, out_path)
            success += 1
            outputs.append(str(result))
        except Exception as exc:  # noqa: BLE001 - batch must continue
            print(f"FAILED {template}/{brand} -> {rel_output}: {exc}")
            failed.append({"entry": entry, "error": str(exc)})

    # output_dir: common parent of outputs, fallback posts/.
    output_dir = str(OUTPUT_ROOT / "posts")
    return {"total": total, "success": success, "failed": failed, "output_dir": output_dir}

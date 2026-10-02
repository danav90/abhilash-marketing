"""CLI for single + batch social post image generation.

Single mode:
    python -m src.cli.generate_post_images --template quote --brand webscraper \\
        --headline "..." --subtext "..." --output posts/test.png

Batch mode:
    python -m src.cli.generate_post_images --batch src/social/batch.json
"""

import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate social post PNGs via HTML templates.")
    p.add_argument("--batch", type=str, default=None, help="Path to batch.json config")
    p.add_argument("--template", type=str, default="quote", help="Template name (quote, cover, tip_carousel, case_study, cta)")
    p.add_argument("--brand", type=str, default="webscraper", help="Brand key (portfolio, gymos, webscraper)")
    p.add_argument("--platform", type=str, default="instagram", help="Platform (instagram, linkedin)")
    p.add_argument("--headline", type=str, default="", help="Headline text")
    p.add_argument("--subtext", type=str, default="", help="Subtext text")
    p.add_argument("--brand-name", type=str, default="", help="Display brand name (defaults per brand)")
    p.add_argument("--metric", type=str, default="", help="Case-study metric (e.g. 38%)")
    p.add_argument("--metric-label", type=str, default="", help="Case-study metric label")
    p.add_argument("--description", type=str, default="", help="Case-study description / body")
    p.add_argument("--slide-num", type=str, default="", help="Slide number badge")
    p.add_argument("--website", type=str, default="", help="Website badge text")
    p.add_argument("--output", type=str, default="posts/test.png", help="Output PNG path (single mode)")
    p.add_argument("--var", action="append", default=[], help="Extra variable KEY=VALUE (repeatable)")
    return p


def parse_extra_vars(var_list: list) -> dict:
    out = {}
    for item in var_list or []:
        if "=" in item:
            k, v = item.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.batch:
        from src.social.batch_generator import generate_batch

        result = generate_batch(Path(args.batch))
        print(f"total={result['total']} success={result['success']} failed={len(result['failed'])}")
        for item in result.get("failed", []):
            print(f"FAILED: {item}")
        print(f"output_dir={result['output_dir']}")
        # List successful outputs when available.
        return 0 if len(result["failed"]) == 0 else 1

    from src.social.generate_image import render_single

    variables = {
        "HEADLINE": args.headline,
        "SUBTEXT": args.subtext,
        "METRIC": args.metric,
        "METRIC_LABEL": args.metric_label,
        "DESCRIPTION": args.description,
        "SLIDE_NUM": args.slide_num,
        "platform": args.platform,
    }
    if args.brand_name:
        variables["BRAND"] = args.brand_name
    if args.website:
        variables["WEBSITE"] = args.website
    variables.update(parse_extra_vars(args.var))
    # Drop empty keys that have defaults handled downstream, except keep platform.
    # Keep all keys; empty strings are valid placeholder replacements.

    try:
        out = render_single(args.template, args.brand, variables, Path(args.output))
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}")
        return 1
    print(f"total=1 success=1 failed=0")
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

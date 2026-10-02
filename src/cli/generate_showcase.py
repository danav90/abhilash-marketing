"""CLI for showcase sheet generation (Task 20).

Single:
    python -m src.cli.generate_showcase --brand portfolio --out posts/showcase_portfolio.png

All:
    python -m src.cli.generate_showcase --all
"""

import argparse
import sys
from pathlib import Path

from src.social.showcase_data import SHOWCASE
from src.social.showcase_renderer import render_showcase

OUTPUT_ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate brand showcase sheets (1080x1620).")
    p.add_argument("--brand", type=str, default="portfolio", help="Brand key (portfolio, gymos, webscraper)")
    p.add_argument("--out", type=str, default="", help="Output PNG path (single mode)")
    p.add_argument("--all", dest="all_brands", action="store_true", help="Render all 3 brands")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    brands = sorted(SHOWCASE) if args.all_brands else [(args.brand or "").strip().lower()]
    failed = 0
    for brand in brands:
        out = args.out
        if args.all_brands or not out:
            out = str(OUTPUT_ROOT / f"posts/showcase_{brand}.png")
        try:
            result = render_showcase(brand, Path(out))
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED {brand}: {exc}")
            failed += 1
            continue
        print(f"OK {brand} -> {result}")
    print(f"total={len(brands)} success={len(brands) - failed} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

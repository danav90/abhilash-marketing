"""CLI entry: python -m videos --brand all|portfolio|gymos|webscraper."""

import argparse
import sys

from videos.batch import BUILDERS, build_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build demo videos for 3 brands.")
    p.add_argument("--brand", type=str, default="all",
                   help="Brand to build (all, portfolio, gymos, webscraper)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    brand = (args.brand or "all").strip().lower()
    if brand == "all":
        build_all()
        return 0
    if brand not in BUILDERS:
        print(f"Unknown brand: {brand!r} (expected all|portfolio|gymos|webscraper)")
        return 2
    try:
        result = BUILDERS[brand]()
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED {brand}: {exc}")
        return 1
    print(f"{result['brand']}: {result['output']} "
          f"{result['duration']:.1f}s {result['size_mb']}MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

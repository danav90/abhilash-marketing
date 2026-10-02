# REPORT-20: Showcase Sheet Generator (1080x1620, 3 Brands)

## Goal

One dense infographic-style showcase sheet per brand (Portfolio, GymOS, Web Scraper Studio) at 1080x1620 portrait (2:3, Instagram feed + LinkedIn document friendly), reusing the Task 18 HTML-to-Image pipeline. One data-driven template, no per-brand templates.

## Deliverable Checklist

- [x] templates/showcase.html — master template, 8 sections, CSS grid rows 60/260/100/420/320/280/120/60 = 1620px, all `{{VARIABLE}}` placeholders, every section in `<section class="...">`, unicode symbols only (no emoji), rounded cards + subtle borders, footer hashtags + tagline
- [x] src/social/showcase_data.py — SHOWCASE dict (portfolio, gymos, webscraper) + SHOWCASE_WIDTH/HEIGHT = 1080/1620
- [x] src/social/showcase_renderer.py — build_variables() + render_showcase() via Task 18 render_template at 1080x1620
- [x] src/cli/generate_showcase.py — --brand/--out single mode, --all renders 3
- [x] src/social/batch.json — 3 showcase entries appended (template=showcase); batch_generator routes template "showcase" to render_showcase()
- [x] tests/test_showcase.py — 3 tests, all passing; all 5 pre-existing tests still pass (8 total)
- [x] 3 PNGs rendered at exact 1080x1620, copied to /mnt/sdcard/Download/marketing-posts/

## Files Touched

New:
- templates/showcase.html
- src/social/showcase_data.py, src/social/showcase_renderer.py
- src/cli/generate_showcase.py
- tests/test_showcase.py
- REPORT-20-showcase-generator.md

Modified:
- src/social/batch.json (3 entries appended)
- src/social/batch_generator.py (showcase routing; quote/cover/case_study path unchanged)

Untracked but ignored (not committed, by design from Task 18):
- posts/showcase_portfolio.png, posts/showcase_gymos.png, posts/showcase_webscraper.png

## Sample Output Size

| File | Size (px) | Bytes |
|---|---|---|
| posts/showcase_portfolio.png | 1080x1620 | 326764 |
| posts/showcase_gymos.png | 1080x1620 | 327476 |
| posts/showcase_webscraper.png | 1080x1620 | 317979 |

## How to Run

```
python -m src.cli.generate_showcase --brand portfolio --out posts/showcase_portfolio.png
python -m src.cli.generate_showcase --all
python -m src.cli.generate_post_images --batch src/social/batch.json   # includes 3 showcase + 8 legacy
ls -la posts/showcase_*.png
python -c "from PIL import Image; [print(f, Image.open(f).size) for f in ['posts/showcase_portfolio.png','posts/showcase_gymos.png','posts/showcase_webscraper.png']]"
cp posts/showcase_*.png /mnt/sdcard/Download/marketing-posts/
```

## Tests Passing

```
$ python -m pytest -q
........  [100%]
8 passed in 0.59s
```

New tests (Playwright mocked at render_template):
1. test_showcase_data_has_all_brands — 3 keys, all content fields present, 5 qualities each, bg colors (#0B1220 portfolio, #1F4E78 gymos/webscraper)
2. test_render_showcase_replaces_variables — no `{{...}}` left, template is showcase.html, dims 1080x1620, every template placeholder covered
3. test_showcase_dimensions — all 3 brands at exactly 1080x1620

## Limits

- Rupee symbol avoided ("Rs" used): headless container fonts may lack U+20B9; geometric symbols (U+25xx) verified present.
- Fixed grid: content must fit 1620px; verified via Playwright scrollHeight check — all 8 sections fit for all 3 brands (one 7px overflow in portfolio qualities fixed by tightening padding 8px to 6px, desc 10.5px to 10px).
- Hero legibility at thumbnail: logo 26px + hero 28-40px adaptive JS (char-count shrink) preserved.
- System fonts only; per render ~2s (browser launch each, inherited from Task 18 pipeline).
- posts/*.png gitignored by design; rebuild via --all or batch.json.

## Next

- LinkedIn document PDF assembly from showcase PNGs.
- Carousel crop variants (1080x1350) if feed preview crops the sheet.

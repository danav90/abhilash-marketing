# REPORT-18: Social Media Visual Generator (HTML-to-Image)

## Goal

Generate actual visual PNG files for social posts across 3 brands, using HTML templates rendered via Playwright screenshot. Reproducible, bulk-generatable, matches brand colors. Follows Task 17 text content with 6 sample visuals (2 per brand).

## DELIVERABLE CHECKLIST

- [x] templates/brand_base.css — shared CSS (system-ui fonts, CSS vars, container layout)
- [x] templates/quote.html — big bold quote on brand bg (72px headline, 32px subtext, site badge)
- [x] templates/cover.html — carousel cover (96px headline, slide badge top-right, swipe hint)
- [x] templates/tip_carousel.html — numbered tip slide (60px heading, 36px body, slide badge)
- [x] templates/case_study.html — metric layout (240px metric, label, description)
- [x] templates/cta.html — CTA (72px headline, 36px subtext, white WhatsApp button + site badge)
- [x] src/social/__init__.py — package marker
- [x] src/social/renderer.py — BRAND_COLORS + inject_brand_css + display/site maps
- [x] src/social/generate_image.py — render_template (async Playwright) + render_single (sync wrapper, auto dims/colors)
- [x] src/social/batch_generator.py — generate_batch with per-item failure continue
- [x] src/social/batch.json — 6 real entries (2 per brand)
- [x] src/cli/generate_post_images.py — single + batch CLI, exit 0/1, prints total/success/failed
- [x] tests/test_social_generator.py — 5 tests, Playwright mocked, all passing
- [x] .gitignore — posts/ + !posts/.gitkeep (PNGs not committed)
- [x] 6 PNGs generated in posts/ at exact dimensions, verified via PIL
- [x] Copied to Android /mnt/sdcard/Download/marketing-posts/

## Files Touched

New:
- templates/brand_base.css
- templates/quote.html, cover.html, tip_carousel.html, case_study.html, cta.html
- src/social/__init__.py, renderer.py, generate_image.py, batch_generator.py, batch.json
- src/cli/__init__.py, src/cli/generate_post_images.py
- tests/__init__.py, tests/test_social_generator.py
- REPORT-18-visual-generator.md

Modified:
- .gitignore (added posts/ + !posts/.gitkeep)

Untracked but ignored (not committed):
- posts/*.png (6 files, see below)

## Generated Sample Images

All in posts/ (gitignored), verified with PIL (Task 18.5: 8 files, see Fix section below for latest table):

| File | Size (px) | Bytes | Brand/Platform |
|---|---|---|---|
| posts/webscraper_quote_01.png | 1080x1350 | 70943 | webscraper / instagram |
| posts/webscraper_cover_01.png | 1080x1350 | 62543 | webscraper / instagram |
| posts/gymos_quote_01.png | 1080x1350 | 79146 | gymos / instagram |
| posts/gymos_case_study_01.png | 1200x627 | 52289 | gymos / linkedin |
| posts/portfolio_quote_01.png | 1080x1350 | 62799 | portfolio / instagram |
| posts/portfolio_cover_01.png | 1200x627 | 47454 | portfolio / linkedin |

Pixel check: webscraper/gymos bg (5,5) = (31,78,120) = #1F4E78; portfolio bg = (15,23,42) = #0F172A. Exact match.

## How to Run

Single:
```
python -m src.cli.generate_post_images --template quote --brand webscraper --headline "..." --subtext "..." --output posts/test.png
python -m src.cli.generate_post_images --template case_study --brand gymos --platform linkedin --metric "38%" --metric-label "..." --description "..." --output posts/x.png
# Extra: --var KEY=VALUE repeatable, --website, --slide-num, --brand-name
```

Batch:
```
python -m src.cli.generate_post_images --batch src/social/batch.json
```

Verify:
```
ls -la posts/*.png
python -c "from PIL import Image; import glob; [print(f, Image.open(f).size) for f in glob.glob('posts/*.png')]"
```

## Test Output

```
$ python -m pytest -q
.....  [100%]
5 passed in 0.80s
```

Note on spec: brief said "expect 162 passing" — that number belongs to the separate web-scraper-studio repo. This repo is new and has exactly 5 tests for Task 18, all passing. No existing tests were modified. The 157 tests in web-scraper-studio are in a different repo and unaffected.

Tests (Playwright mocked via playwright.async_api.async_playwright):
1. test_render_template_replaces_variables — captures temp HTML, asserts vars replaced, temp deleted
2. test_render_single_selects_correct_dimensions — instagram 1080x1350 vs linkedin 1200x627
3. test_render_single_brand_colors_applied — portfolio #0F172A, gymos #1F4E78 via inject + forwarded vars
4. test_batch_generator_reads_config — 2-entry config yields 2 calls
5. test_batch_generator_handles_failure — 1 raise still yields 2/3 success

## Design Notes

Why HTML-to-Image over Pillow: better typography (line-height, max-width, font smoothing), easier to update (edit HTML/CSS, no pixel math), matches website styles, responsive to content length. Pillow text wrapping at 72-240px sizes is brittle.

Why Playwright: already installed (chromium-1243 at /root/.cache/ms-playwright), high fidelity, viewport-exact screenshots, networkidle wait handles fonts. No new deps; simple string replace instead of Jinja.

Brand colors injected via :root CSS variables override (renderer.inject_brand_css), inserted before </head>. Base CSS inlined into temp HTML so relative links work even though temp file is deleted after screenshot.

## Environment Changes

None. No new deps. Used existing playwright 1.63.0 + pillow 12.3.0 + pytest 9.1.1. Chromium already at /root/.cache/ms-playwright/chromium-1243/chrome-linux-arm64/chrome.

## Recovery Test

Re-ran batch twice back-to-back: both runs total=6 success=6 failed=0. Overwrites existing PNGs idempotently. Batch continues on per-item failure (try/except per entry, failed list in return). Single-mode failure prints FAILED and exits 1.

## Limits

- Fonts must be system (system-ui only, no custom font install to avoid env changes).
- Playwright screenshot per image ~2s (6 images ~15s total including browser launches).
- Templates render at fixed viewport sizes; very long headlines may overflow — keep headlines under ~90 chars, subtext under ~140 chars.
- posts/*.png gitignored by design; rebuild via batch.json.
- LinkedIn Document Carousel PDF assembly deferred to Task 19.

## Next

- Task 19: Build LinkedIn PDF carousels from PNGs (1080x1080 squares).
- Task 20: Instagram Reels (video from cover + tip slides).

## Fix (Task 18.5) — Adaptive Typography + URL Badge + Platform Sizing

Issues fixed: portfolio_cover headline cut after "in 6" (96px fixed, no shrink); gymos_case_study description cut + URL badge off-screen (627px landscape too short for 200px metric + 100px padding); polish gaps (brand 28px, no texture, SWIPE only on one cover).

Changes:
- FIX 1 adaptive JS (char-count, Option B): cover 96/76/60/48/40; quote/cta 72/60/52/44/38; tip heading 60/52/46/40/34; subtext/body 36/32 base to 28 (>80 chars) / 24 (>120); case_study description 32/28/26/24 (>80/120/200), metric-label 30/26, long metric capped. Plus compact mode for viewport height <= 700px (linkedin single): container padding 100px to 60px, headline cap 48px, subtext 22px, metric 110px, label 24px, description 20px.
- FIX 2 flexible container: height 100vh to min-height 100vh, justify space-between, top/middle/bottom blocks, bottom margin-top auto + padding-top 40px. Middle flex-1 centered.
- FIX 3 guaranteed URL badge: all 5 templates end with bottom-anchored .url-badge > .brand-url using {{URL}}; renderer injects per brand (portfolio abhilash.dev, gymos bodycare-gym.vercel.app, webscraper webscraperstudio.vercel.app) and syncs {{WEBSITE}} legacy alias. SWIPE bottom-right only on cover.html.
- FIX 4 polish: brand 22px/0.15em/accent, rule 1px/0.3 opacity, headline 800/1.15/-0.02em, subtext 400/1.4/rgba 0.75/margin 32px, padding 100px 80px, badge pill 700, radial gradient overlay, overflow-wrap break-word.
- FIX 5 platform dims: DIMENSIONS dict + resolve_dimensions() in generate_image.py; batch type field forwarded; CLI --type. instagram single 1080x1080, carousel 1080x1350, reel 1080x1920; linkedin single 1200x627, document/text 1080x1080. Empty type keeps legacy (instagram 1080x1350, linkedin 1200x627) so existing tests pass.
- FIX 6 batch now 8 entries (added portfolio_quote_long 107-char headline, gymos_case_study_long 289-char description).

Before/after (bytes changed with gradient + fixes; dimensions now exact for all):
| File | Before (px/bytes) | After (px/bytes) |
|---|---|---|
| posts/webscraper_quote_01.png | 1080x1350 / 70943 | 1080x1350 / 188537 |
| posts/webscraper_cover_01.png | 1080x1350 / 62543 | 1080x1350 / 188249 |
| posts/gymos_quote_01.png | 1080x1350 / 79146 | 1080x1350 / 192751 |
| posts/gymos_case_study_01.png | 1200x627 / 52289 | 1200x627 / 125502 |
| posts/portfolio_quote_01.png | 1080x1350 / 62799 | 1080x1350 / 188471 |
| posts/portfolio_cover_01.png | 1200x627 / 47454 | 1200x627 / 138653 |
| posts/portfolio_quote_long.png | new | 1080x1350 / 219241 |
| posts/gymos_case_study_long.png | new | 1080x1080 / 199235 |

Screenshot verification (Playwright evaluate, headBottom < urlTop <= viewport height):
- webscraper_quote_01: 1080x1350 head 677/52px url 1186-1250 OK
- webscraper_cover_01: 1080x1350 head 799/96px url 1186-1250 SWIPE OK
- gymos_quote_01: 1080x1350 head 677/52px url 1186-1250 OK
- gymos_case_study_01: 1200x627 head 286/110px url 503-567 OK (was 735/627 overflow, url 571-635 clipped)
- portfolio_quote_01: 1080x1350 head 647/52px url 1186-1250 OK
- portfolio_cover_01: 1200x627 head 353/48px url 503-567 SWIPE OK (was 553/url 725-789 clipped)
- portfolio_quote_long: 1080x1350 head 694/44px url 1186-1250 OK (107 chars shrunk 72 to 44)
- gymos_case_study_long: 1080x1080 head 482/200px url 916-980 OK (289 chars at 24px)

Also verified: no {{...}} placeholders left in rendered HTML, bg pixels still exact (#1F4E78 / #0F172A), system-ui only, zero emojis, pytest 5 passed, batch total=8 success=8, copied to /mnt/sdcard/Download/marketing-posts/. URLs now guaranteed visible bottom-left on all templates.

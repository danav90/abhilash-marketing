# REPORT-21: Demo Videos (3 Brands, English Voiceover)

## Goal

Three demo videos under 60 seconds each, professional Indian-English voiceover, GymOS-video style: static Ken Burns slides for Portfolio (per user preference), live Playwright screen recordings for GymOS and Web Scraper Studio. 1920x1080 MP4 (H.264 + AAC), watermark, fades, WhatsApp-shareable sizes.

## DELIVERABLE CHECKLIST

- [x] videos/ package + CLI (`python -m videos --brand all|portfolio|gymos|webscraper`)
- [x] 3 voiceover scripts as .txt files (videos/scripts/portfolio.txt, gymos.txt, webscraper.txt)
- [x] portfolio_slides.py (6 slides at 1920x1080 via Task 18/20 render_template pattern + templates/video_slide.html)
- [x] record_website.py (Playwright, 1920x1080, scripted timelines, warmup, blank-leader trim)
- [x] compose_video.py (FFmpeg: watermark 15%, 0.5s fades, min-trim, audio fit/stretch)
- [x] 3 MP4s in videos/output/
- [x] Android copy at /mnt/sdcard/Download/demo-videos/
- [x] 3 tests passing (11/11 total with pre-existing suite)

## Files Touched

New:
- videos/__init__.py, videos/__main__.py, videos/batch.py
- videos/generate_voiceover.py (edge-tts, en-IN-PrabhatNeural + en-US-GuyNeural fallback, rate -5%)
- videos/portfolio_slides.py, videos/portfolio_video.py (Ken Burns zoompan + slideshow concat)
- videos/record_website.py (record_website/record_brand/capture_section_shots fallback)
- videos/compose_video.py (audio_duration/video_duration, fit_audio_to_max, stretch_audio_to, leading_blank_seconds, build_ffmpeg_args, compose_video)
- videos/assets.py + videos/assets/{portfolio,gymos,webscraper}_logo.png (Pillow wordmarks)
- videos/scripts/{portfolio,gymos,webscraper}.txt
- templates/video_slide.html
- tests/test_video_pipeline.py
- REPORT-21-demo-videos.md

Modified:
- .gitignore (videos/output/, videos/tmp/ ignored; MP4s rebuild via CLI, same policy as posts/*.png)

Untracked but ignored (not committed, by design):
- videos/output/*.mp4, videos/tmp/* (voice MP3s, webms, slides, segments)

## Output: 3 MP4s (ffprobe)

| File | Duration | Size | Video | Audio |
|---|---|---|---|---|
| videos/output/portfolio_60s.mp4 | 55.37s | 3.43 MB | 1920x1080 H.264 30fps | AAC |
| videos/output/gymos_60s.mp4 | 58.04s | 2.61 MB | 1920x1080 H.264 25fps | AAC |
| videos/output/webscraper_60s.mp4 | 57.60s | 3.07 MB | 1920x1080 H.264 25fps | AAC |

Voiceover tracks: portfolio 52.8s spoken (stretched pitch-preserving to 54.9s to fill the 55.4s slideshow); gymos 61.6s spoken (atempo 1.0626x to 58.0s, within 60s cap); webscraper 56.9s as-is. All videos verified: open on content (no white flash), section movement confirmed by frame sampling, AAC present, fades inside output bounds.

## Sample Voice Lines (2 per video)

- Portfolio: "Hi, this is Abhilash Singh Rajput, based in Delhi." / "A free demo within forty-eight hours of our first call."
- GymOS: "QR check-in in seconds. Absent-member reports that flag at-risk members in fourteen days." / "One gym in Pune recovered forty-eight thousand rupees in pending fees in thirty days."
- Web Scraper Studio: "Every lead includes business name, phone, address, Google ratings, and verified email." / "Pricing starts at five thousand rupees for five hundred leads."

## Design Notes

- Why 1080p: matches source sites at desktop viewport; crf 26 keeps talking-head-free screen content at 2-3.5 MB, far under the 15 MB WhatsApp limit.
- Why en-IN voice: Indian-English male (PrabhatNeural) fits Delhi/Pune customer base; -5% rate aids clarity over screen footage; en-US-GuyNeural fallback keeps builds green if the voice is unavailable.
- Why static slides for portfolio: per user preference; Ken Burns zoompan (alternate in/out per slide, 3840px upscale to avoid jitter) keeps stills cinematic; voiceover stretched (not cut) to fill the 55s slideshow.
- One data-driven slide template (video_slide.html), same string-replace pipeline as Tasks 18/20 — no new render deps.
- Watermark is a Pillow-generated white wordmark at 15% opacity, top-left, 64px tall — subtle by design.

## Limits

- Playwright records ~1x realtime (each site video costs ~60s + warmup); live pages need stable network — goto uses networkidle with domcontentloaded fallback and capped timeouts.
- GymOS adaptation (brief assumed dashboard access): owner dashboard is behind login with no demo credentials (probed /dashboard, /demo, /app; wrong-password login rejected), and seeding a live prod DB was out of scope — the recording covers the live GymOS-powered customer site (hero, owner-login page, plans, trainers, facilities, testimonials, contact, back to hero). Voiceover unchanged.
- Two real bugs found by frame sampling and fixed: (1) scroll_to matched sticky nav links (already in view) so nothing scrolled — fixed with role="heading" section anchors + scroll-delta fallback; (2) recordings open on 1.5-6s white loader — fixed with pre-warm context + leading_blank_seconds() trim (flat-and-bright detection; flat-dark counts as content since dark heroes read std~3).
- If recording ever fails, batch falls back to section screenshots + Ken Burns slideshow (same composer).
- No emojis anywhere; "Rs" used instead of rupee glyph for container-font safety.

## Next

- Post to LinkedIn + WhatsApp Business (files already in /mnt/sdcard/Download/demo-videos/).
- Optional: 9:16 crops for Reels/Shorts from the same masters.

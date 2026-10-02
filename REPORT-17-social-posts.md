# REPORT-17: Social Media Post Generator for 3 Brands

## Goal

Generate 18 professional English posts (no emojis) for Instagram and LinkedIn covering three brands — Personal Portfolio (Abhilash Singh Rajput), GymOS, and Web Scraper Studio — as copy-paste-ready markdown files with captions, hashtags, visual descriptions, and CTAs.

## DELIVERABLE CHECKLIST

- [x] Personal Portfolio: 3 Instagram posts (Carousel educational, Single Image proof, Reel behind-the-scenes) + 3 LinkedIn posts (Text-only insight, Document carousel framework, Text+image result)
- [x] GymOS: 3 Instagram + 3 LinkedIn posts (same mix, angle = retention / payments / attendance, site bodycare-gym.vercel.app)
- [x] Web Scraper Studio: 3 Instagram + 3 LinkedIn posts (same mix, angle = Google Maps 500-5,000 verified leads in 24-48h, site webscraperstudio.vercel.app, no JustDial/IndiaMART claims)
- [x] Professional English only, zero emojis verified by script
- [x] Instagram carousel captions 500-800 chars; single-image captions 150-300 chars; Reel captions in 150-300 range
- [x] LinkedIn text-only captions 200-400 words; document-carousel captions 100-150 words; content slides 105-135 words each
- [x] Instagram hashtags 3-5 per post; LinkedIn hashtags none
- [x] India context (Mumbai, Delhi, Bengaluru, Pune, Indore, Hyderabad) in all brands
- [x] Specific numbers over adjectives throughout (Rs 48,000, 2,300 leads, 98 percent, 25 percent, 36 hours)
- [x] Portfolio posts reference only real shipped work (GymOS, Web Scraper Studio, Playwright/Crawl4AI/FastAPI/Streamlit); zero mentions of years, experience, credentials, degrees, certifications, or generic "I help businesses" language
- [x] Files created under src/social/

## Files Created With Word Counts

| File | Posts | Words | Chars (bytes) |
|---|---|---|---|
| src/social/portfolio_posts.md | 6 (3 IG + 3 LI) | 1,878 | 12,682 |
| src/social/gymos_posts.md | 6 (3 IG + 3 LI) | 1,668 | 10,545 |
| src/social/webscraper_posts.md | 6 (3 IG + 3 LI) | 1,711 | 11,182 |
| Total | 18 | 5,257 | 34,409 |

Validation (script-counted):
- IG Carousel: Portfolio 542 chars, GymOS 530 chars, WebScraper 529 chars (target 500-800)
- IG Single: Portfolio 200 chars, GymOS 178 chars, WebScraper 200 chars (target 150-300)
- IG Reel: 243 / 228 / 232 chars
- LinkedIn Text-only: 280 / 295 / 339 words (target 200-400)
- LinkedIn Document caption: 118 / 112 / 100 words (target 100-150); content slides 105-135 words each (cover slides are title-only by design)
- LinkedIn Text+image: 167 / 155 / 161 words
- Emoji scan: clean. Forbidden-phrase scan (JustDial, IndiaMART, years of experience, 20+ years, certification, degree, "I help businesses"): clean.

## 2 Sample Posts

### Sample 1 — Instagram Single Image (Web Scraper Studio)

---
BRAND: Web Scraper Studio
PLATFORM: Instagram
TYPE: Single Image
---

CAPTION:
2,300 verified dental clinic leads from Mumbai delivered in 36 hours. 98 percent phone coverage, under 5 percent duplicates, clean CSV. That is Web Scraper Studio. Live at webscraperstudio.vercel.app.

HASHTAGS:
#LeadGen #B2BIndia #SalesLeads #Mumbai

VISUAL DESCRIPTION:
Single image: CSV preview blurred phones with stat overlay cards: "2,300 leads" "36 hours" "98 percent phones" "Mumbai — Dental Clinics". Bottom bar: webscraperstudio.vercel.app. Navy and white B2B style.

CTA:
Tap link in bio to order the same batch for your city.
---

### Sample 2 — LinkedIn Text-only (GymOS, excerpt)

Most Indian gym owners do not have an acquisition problem. They have a retention leak.

I speak with gym owners in Pune, Delhi, and Indore every month. The pattern repeats: 200 to 400 members on paper, but 30 to 40 percent stop coming within 90 days. Nobody notices for three weeks because attendance lives in a paper register. [...]

That is why we built GymOS as a multi-tenant SaaS specifically for Indian gyms. It is live at bodycare-gym.vercel.app. Three workflows only: member retention reports showing who stopped coming, payment tracking with due lists and collection status, and attendance logging that takes seconds at the front desk.

Early gyms using systematic follow-up retain 25 percent more members by month four and close pending dues 2x faster. [...] (Full 295-word post in src/social/gymos_posts.md)

CTA: Comment with your member count and city, or DM for a GymOS walkthrough.

## Design Notes

1. Why question-based hooks: every LinkedIn text-only post and most carousel covers open with a question ("How do you go from idea to live SaaS?", "Why do 40 percent quit?", "Purchased databases failed us?"). Questions outperform statements for stop-scroll on both feeds, and they let each brand agitate a specific pain before presenting its shipped system. The second line always grounds the question in India (city names) so the reader self-qualifies.

2. Why specific numbers: the brief bans adjectives ("many leads") in favor of proof. Each brand has an anchor metric repeated across platforms for memorability — Portfolio: 2 live products + 90-second QA; GymOS: Rs 48,000 recovered in 30 days + 25 percent retention lift; Web Scraper Studio: 500-5,000 leads in 24-48h + 98 percent phone coverage + under 5 percent duplicates. Numbers also make visual cards easy (stat overlays on every single-image and Reel end card).

3. Why capability over credentials (Portfolio): buyers of solo-dev services do not hire resumes, they hire risk reduction. Every portfolio post therefore follows "I built X that does Y with Z stack, live at URL" instead of any seniority claim. GymOS proves multi-tenancy and deploy discipline; Web Scraper Studio proves scale and QA rigor; the Playwright/Crawl4AI/FastAPI/Streamlit details prove the automation layer behind both. No years, no degrees, no certificates appear anywhere — verified by grep.

4. Platform split logic: Instagram carries the short proof (single image under 300 chars, Reel demo) while LinkedIn carries the reasoning (280-340-word lessons, 5-6-slide frameworks with 105-135 words per content slide). Document carousels reuse the same numbers as Instagram so a follower seeing both gets repetition, not contradiction.

## Next: Post Scheduling

1. Schedule 18 posts over 3 weeks (1 per brand per week, alternating IG/LI to avoid same-day duplication).
2. Suggested order: Week 1 educational carousels, Week 2 proof posts, Week 3 Reel + announcement.
3. Create Canva/Figma visuals from each VISUAL DESCRIPTION block; export document carousels as LinkedIn PDFs.
4. Track per-post metrics (saves for carousels, DMs for proof posts) and double down on the winning hook in Task 18.

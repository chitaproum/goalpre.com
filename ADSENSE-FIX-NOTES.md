# GoalPre — AdSense policy fix notes

This document explains the changes made to resolve the two Google AdSense
violations reported for goalpre.com:

1. **“Google-served ads on screens without publisher-content”**
2. **“Low value content”**

---

## 1. Why the violations happened

- **Ads on empty screens.** The site is a single-page app. The AdSense
  **Auto Ads** loader was hard-coded in `index.html` `<head>`. Auto ads inject
  adverts automatically, including on navigation/loading screens *before* the
  app had rendered any match content. Google saw ads on effectively blank
  screens → policy breach.
- **Thin / JS-only content.** Almost all visible text is rendered by JavaScript
  from a very large `data.js`. A crawler that does not execute JS saw a nearly
  empty page with little original, standalone text → “low value content”.

## 2. What was changed

### Removed the cause of the ad violation
- Deleted the Auto Ads loader `<script>` from `index.html` `<head>`.
  It is replaced by an HTML comment explaining why, so it is not accidentally
  put back. **AdSense is now effectively OFF site-wide.** The existing
  `ads.js` only renders placeholder slots (its client id is empty), so no live
  ads are served.

### Added real, original, crawlable content
- New home-page intro section (`.home-about`) with a genuine `<h1>` and several
  paragraphs of original text that render in the raw HTML (no JS required),
  explaining what the site does and how the three engines work.
- New standalone content pages, all with the shared header/footer, legal styling,
  canonical tag and `robots` meta:
  - `about.html` — who we are, data sources, method, limitations.
  - `predictions-guide.html` — how to read and use the predictions.
  - `glossary.html` — definitions of 1X2, Over/Under, xG, Poisson, odds, etc.
  - `faq.html` — common questions and honest answers.
  - `responsible-gambling.html` — 18+ framing, warning signs, help resources.
  - `contact.html` — how to reach us / report data errors.
- Footer link bar on every page (home + all legal/content pages) now links the
  whole set together, improving internal linking and crawlability.

### SEO / crawlability
- Added `robots.txt` (allows all, points to the sitemap).
- Added `sitemap.xml` listing all public pages.
- Added `<link rel="canonical">` and `<meta name="robots" content="index, follow">`
  to the home page and the legal pages.
- Updated the GitHub Actions workflow (`.github/workflows/update-data.yml`) so
  the “Prepare public website only” step also copies `robots.txt` and
  `sitemap.xml` into `_site`. All `*.html` are already copied, so the new pages
  deploy automatically.

## 3. What you should do next

1. Extract the ZIP and push to your GitHub repo as usual; GitHub Pages will
   redeploy automatically.
2. In Google Search Console, submit `https://goalpre.com/sitemap.xml`.
3. Only **after** the site is content-rich and live, request an AdSense review
   again from your AdSense dashboard.
4. **When (and only when) AdSense re-approves the site**, re-enable ads as
   *manual, in-content units* placed inside real match/content areas — never on
   empty, loading, or navigation-only screens, and avoid turning Auto Ads back
   on. Keep the real `ca-pub` client id out of the browser until then.

> Note: whether the site is re-approved is Google’s decision, not something that
> can be guaranteed. These changes remove the known policy triggers and add the
> genuine, useful content Google asks for, which is what gives the review the
> best chance of passing. Keep AdSense disabled until you are approved.

## 4. Important: content must stay genuine

The new pages are written to be actually useful to a reader. Do **not** stuff
them with repeated keywords or auto-generated filler — Google penalizes that too.
Expand them with real, honest information over time (e.g. publish your real
accuracy results) rather than padding.

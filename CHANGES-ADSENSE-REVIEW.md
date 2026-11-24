# Changes made for the AdSense "Low value content" review (23 Nov 2026)

Done in code
- Removed the fake bookmaker offers block and all empty ad placeholders from index.html.
- Added generate_static.py (run by the workflow) so index.html contains real, current predictions without JavaScript; app.js still replaces them on load.
- Hid the "Loading match data" banner unless data is genuinely slow.
- ads.js: consentGranted now defaults to false; added consent.js (simple notice). Replace with a Google-certified CMP before enabling AdSense for EEA/UK.
- Reworded "Betting Tips" titles to "Match Statistics"; "AI consensus" to "ensemble consensus"; published the KPI weights on the page instead of pointing to the README.
- Privacy/Terms dates updated; privacy wording says ads "may" be shown. README renamed to GoalPre. sitemap lastmod refreshed.

Still needs YOU (cannot be done honestly in code)
- Real named authors/reviewers with bios (how-we-write.html says named humans write and review).
- Fresh match-analysis and Insights articles (current previews are dated 26-28 Oct); aim for 15-20 Insights.
- Replace the illustrative Arsenal v Newcastle example with real analysis.
- data.js is ~75 MB; slim it (e.g. only upcoming fixtures + recent history) to improve speed.
- Check the repo is private or contains no secrets; consider removing model-comparison-internal.docx and internal notes from it.
- Get organic traffic/indexing via Search Console, wait a few weeks, then request review.

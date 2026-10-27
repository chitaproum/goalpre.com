# GoalPre — Match Analysis Editorial Workflow (internal)

This is an **internal** working document for anyone writing match-analysis
articles for GoalPre. It is not published on the site. Its purpose is to keep
every article genuinely human-edited, factually grounded, and clear of Google's
"scaled content abuse" / "low value content" policies.

**Golden rule:** AI may help draft, but a named human makes the editorial calls
on every piece, verifies every number, and signs it off. Never publish raw,
unedited model output.

---

## 1. Cadence (keep it small and genuine)

- Aim for **2–4 articles per week**, each on a fixture genuinely worth writing
  about (title clash, derby, a value gap your model flagged).
- Do **not** auto-generate a write-up for every fixture. Restraint is itself a
  quality signal.
- Target length: **400–700 words**. Substantial but focused.

---

## 2. The article template

Copy the block below for each new article. Fill the internal brief first, then
write the published section. Delete the `[...]` prompts as you go.

```
=== INTERNAL BRIEF (do NOT publish) ===
Fixture:      [Home] vs [Away] · [League] · [Date] · [Venue]
Writer:       [name]
Reviewer:     [name]
Data pulled:  [date/time]  Sources: [API / page links]

Stats (last 6 unless noted):
  xG for (pg):        H [x.xx]  A [x.xx]
  xG against (pg):    H [x.xx]  A [x.xx]
  Goals for/against:  H [x/x]   A [x/x]
  Shots / on target:  H [x/x]   A [x/x]
  Over 2.5 hit rate:  H [x of 6] A [x of 6]
  Points per game:    H [x.xx]  A [x.xx]
  Home/away split:    H home [x.x] PPG  A away [x.x] PPG
Head-to-head (last 5): [record] · avg [x.x] goals · Over 2.5 in [x of 5]
Model output:          1X2 H/D/A [xx/xx/xx]% · Exp. total [x.x] · Over 2.5 [xx]%
Market:                Home ~[x.xx] · Over 2.5 ~[x.xx]

Human-layer notes (the bit a model can't supply):
  - [team news / injuries / fitness calls]
  - [fixture congestion, travel, European turnaround]
  - [tactical read: how they actually play, not just the numbers]
  - [where model and market disagree + your take on who's right]
  - [your opinion + confidence level]

=== PUBLISHED ARTICLE ===
Headline:  [outcome-led, specific — not "Match Preview"]
Byline:    By [Author] · Analysis desk · [date]

[Para 1 — the favourite and WHY, grounded in the underlying numbers.]
[Para 2 — the awkward side / the caveat a surface stat hides.]
[Para 3 — model vs market: is there value, or do they agree?]
[Para 4 — the pre-kickoff variable to watch (team news etc.).]
My read:   [clear call + explicit confidence: high/low on result, high/low on goals]

Disclaimer: This analysis is based on recent statistics and is one writer's
opinion, not betting advice. Odds change and no result is guaranteed. 18+ —
please gamble responsibly.
```

---

## 3. Editorial checklist (tick before publishing)

**Sourcing & accuracy**
- [ ] Every stat in the article was pulled from a real source and matches the brief.
- [ ] No number was invented or "rounded into" a nicer story. Models hallucinate — verify.
- [ ] The fixture, date, venue and team names are correct.

**Human editorial value (the anti-AI-abuse layer)**
- [ ] At least one specific, checkable detail the stats alone don't give (team news, tactic, context).
- [ ] A stated opinion AND an explicit confidence level.
- [ ] Where model and market disagree is addressed — including honestly saying "no value / they agree".
- [ ] At least one surface stat is *interpreted*, not just recited.
- [ ] Intro and conclusion rewritten in a human voice; generic filler deleted
      ("game of two halves", "anything can happen", etc.).
- [ ] Structure differs from the last article — not a copy-paste skeleton.

**Compliance & presentation**
- [ ] Real author byline + dated desk line.
- [ ] Responsible-gambling / 18+ / not-advice disclaimer present.
- [ ] No guarantees, no "sure bet", no hype language.
- [ ] Length 400–700 words, focused.

**Sign-off**
- [ ] A named reviewer (not the writer) read it, checked facts, approved it.
- [ ] Logged in the editorial log: date | match | writer | reviewer | sources.

---

## 4. Red lines (any one of these = do not publish)

- Raw, unedited LLM output.
- One rigid template script-filled across many matches.
- Content written mainly to create ad inventory rather than to inform.
- Fabricated or unverified stats.
- No human in the loop and no editorial accountability.

---

## 5. Maintenance

- Revisit past articles: mark how the tip performed and correct anything wrong.
- Living, maintained content signals genuine interest; stale auto-posts signal the opposite.

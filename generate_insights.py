#!/usr/bin/env python3
"""Optional LLM match-insight generator for GoalPre.

Runs AFTER fetch_data.py in GitHub Actions. Reads the freshly written data.js,
asks an OpenAI-compatible chat model for a short, neutral, factual preview of
each upcoming fixture, and writes `ai-insights.js` (window.AI_INSIGHTS = {...})
plus a server-side cache `ai-insights-cache.json`.

Design goals
------------
* Standard library only (urllib) — matches the zero-dependency repo style.
* Provider-agnostic: works with any OpenAI-compatible /chat/completions API
  (OpenAI, OpenRouter, Groq, Together, Azure-compat, local, …) via a
  configurable base URL + model.
* The API key is read ONLY from the LLM_API_KEY environment variable (a GitHub
  Actions secret). It is never written to any output file; a secret-leak guard
  refuses to publish if the key ever appears in the output.
* Cost-controlled: cache-backed (only new/changed fixtures hit the API), with a
  per-run fixture cap and an earliest-kickoff-first ordering.
* Fully optional and non-fatal: if LLM_API_KEY is missing or the feature is
  disabled in api-config.json, the script writes an insights file from whatever
  is cached (possibly empty) and exits 0 so the Pages deploy never breaks. The
  website falls back to its built-in, in-browser insight generator.

The LLM only supplies the natural-language paragraph. All numbers, picks,
confidence and value flags on the site are still computed by the site's own
models; this script never fabricates statistics.
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UTC = dt.timezone.utc
PROMPT_VERSION = 'v1'  # bump to force regeneration of all cached insights


def stamp(value):
    return dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return default


def read_data_js(path):
    """Extract the JSON object from `window.DATA = {...};` in data.js."""
    if not path.exists():
        return None
    text = path.read_text(encoding='utf-8')
    m = re.search(r'window\.DATA\s*=\s*', text)
    if not m:
        return None
    start = text.find('{', m.end())
    end = text.rfind('}')
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except ValueError:
        return None


def best_odds(fixture, market, outcome):
    """Highest available decimal odds for an outcome, or None."""
    odds = fixture.get('odds') or {}
    best = None
    for book in odds.get('bookmakers') or []:
        try:
            val = float(((book.get('markets') or {}).get(market) or {}).get(outcome))
        except (TypeError, ValueError):
            continue
        if val > 1 and (best is None or val > best):
            best = val
    return best


def market_block(fixture):
    """Compact, de-margined market view for the prompt (or '' if no odds)."""
    h, d, a = (best_odds(fixture, '1x2', k) for k in ('1', 'X', '2'))
    o, u = best_odds(fixture, 'ou', 'over'), best_odds(fixture, 'ou', 'under')
    lines = []
    if h and d and a:
        s = 1 / h + 1 / d + 1 / a
        lines.append('Market 1X2 implied%% (margin removed): home %d, draw %d, away %d'
                     % (round(100 / h / s), round(100 / d / s), round(100 / a / s)))
    if o and u:
        s = 1 / o + 1 / u
        lines.append('Market Over 2.5 implied%%: %d' % round(100 / o / s))
    return '\n'.join(lines)


def h2h_summary(data, fixture):
    """Short head-to-head record string, or '' when unavailable."""
    hid, aid = fixture.get('homeId'), fixture.get('awayId')
    if hid is None or aid is None:
        return ''
    key = '-'.join(str(i) for i in sorted([hid, aid]))
    rows = (data.get('h2h') or {}).get(key) or []
    if not rows:
        return ''
    home, hp, ap, dr = fixture['home'], 0, 0, 0
    for m in rows[-6:]:
        hs = m['fh'] if m['home'] == home else m['fa']
        as_ = m['fa'] if m['home'] == home else m['fh']
        if hs > as_:
            hp += 1
        elif hs < as_:
            ap += 1
        else:
            dr += 1
    return 'Recent head-to-head (last %d): %s %d win(s), %d draw(s), %s %d win(s)' % (
        len(rows[-6:]), fixture['home'], hp, dr, fixture['away'], ap)


def build_prompt(data, fixture):
    p = fixture.get('prediction') or {}
    if not p:
        return None
    ph, pd, pa = p.get('pHome', 0), p.get('pDraw', 0), p.get('pAway', 0)
    pick = 'home win' if ph >= pd and ph >= pa else ('away win' if pa >= ph and pa >= pd else 'draw')
    over = p.get('pOver', 0)
    facts = [
        'Fixture: %s vs %s (%s).' % (fixture['home'], fixture['away'], fixture.get('league', '')),
        'Model 1X2 probabilities: home %d%%, draw %d%%, away %d%%; favoured outcome: %s.'
        % (round(ph * 100), round(pd * 100), round(pa * 100), pick),
        'Expected goals: %s %.2f, %s %.2f (total %.2f). Over 2.5 goals probability: %d%%. Most likely score: %s-%s.'
        % (fixture['home'], p.get('expH', 0), fixture['away'], p.get('expA', 0),
           p.get('expTotal', 0), round(over * 100), p.get('scoreH', 0), p.get('scoreA', 0)),
    ]
    mkt = market_block(fixture)
    if mkt:
        facts.append(mkt)
    h2h = h2h_summary(data, fixture)
    if h2h:
        facts.append(h2h)
    return '\n'.join(facts)


def cache_key(prompt, model):
    raw = (PROMPT_VERSION + '|' + model + '|' + prompt).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()[:16]


SYSTEM_PROMPT = (
    'You are a football data analyst writing a very short, neutral preview snippet for a '
    'statistics website. Use ONLY the numbers provided; never invent stats, injuries, lineups '
    'or news. Write 2 sentences, about 40-55 words total, plain factual English. Mention the '
    "model's favoured outcome with its probability and the expected-goals / over-under picture. "
    'Do NOT give betting advice, do NOT tell anyone to bet or stake money, do NOT promise or '
    'guarantee any result, and do NOT use hype. These are model estimates, not certainties.'
)


def call_llm(base_url, model, api_key, prompt, temperature, max_tokens, timeout):
    url = base_url.rstrip('/') + '/chat/completions'
    body = json.dumps({
        'model': model,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt},
        ],
    }).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.load(resp)
    choices = payload.get('choices') or []
    if not choices:
        raise RuntimeError('LLM returned no choices')
    text = (choices[0].get('message') or {}).get('content') or ''
    text = re.sub(r'\s+', ' ', text).strip().strip('"')
    if not text:
        raise RuntimeError('LLM returned empty content')
    return text


def run(root):
    root = Path(root)
    config = load_json(root / 'api-config.json', {})
    opts = config.get('aiInsights', {}) or {}

    data = read_data_js(root / 'data.js')
    cache = load_json(root / 'ai-insights-cache.json', {})
    now = dt.datetime.now(UTC)

    api_key = os.environ.get('LLM_API_KEY', '').strip()
    enabled = bool(opts.get('enabled', True)) and bool(api_key) and data is not None

    base_url = os.environ.get('LLM_BASE_URL') or opts.get('baseUrl', 'https://api.openai.com/v1')
    model = os.environ.get('LLM_MODEL') or opts.get('model', 'gpt-4o-mini')
    temperature = float(opts.get('temperature', 0.4))
    max_tokens = int(opts.get('maxTokens', 160))
    timeout = float(opts.get('timeoutSeconds', 40))
    days_ahead = int(opts.get('daysAhead', 4))
    per_run = max(0, int(opts.get('maxFixturesPerRun', 60)))
    sleep_s = float(opts.get('requestSpacingSeconds', 0.4))

    generated = updated = failed = 0

    if enabled:
        horizon = now + dt.timedelta(days=days_ahead)
        upcoming = []
        for f in data.get('fixtures', []):
            if f.get('status') != 'NS' or not f.get('prediction'):
                continue
            try:
                ko = stamp(f['kickoffUtc'])
            except (KeyError, ValueError):
                continue
            if now < ko <= horizon:
                upcoming.append((ko, f))
        upcoming.sort(key=lambda x: x[0])

        processed = 0
        for ko, f in upcoming:
            fid = str(f.get('id'))
            prompt = build_prompt(data, f)
            if not prompt:
                continue
            ckey = cache_key(prompt, model)
            entry = cache.get(fid)
            if entry and entry.get('hash') == ckey and entry.get('text'):
                continue  # unchanged inputs -> reuse cached text, no API call
            if processed >= per_run:
                continue  # budget reached; keep any existing cached text
            processed += 1
            try:
                text = call_llm(base_url, model, api_key, prompt, temperature, max_tokens, timeout)
                cache[fid] = {'hash': ckey, 'text': text, 'model': model,
                              'kickoffUtc': f['kickoffUtc'], 'generatedAt': now.isoformat()}
                if entry:
                    updated += 1
                else:
                    generated += 1
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
                failed += 1
                print('WARNING: insight generation failed for fixture %s: %s' % (fid, type(exc).__name__))
            if sleep_s > 0:
                time.sleep(sleep_s)
    else:
        reason = 'no LLM_API_KEY' if not api_key else ('disabled in config' if not opts.get('enabled', True) else 'no data.js')
        print('AI insights step skipped (%s); using cached/empty insights, site falls back to in-browser text.' % reason)

    # Expire entries whose kickoff is well in the past (keep file small).
    for fid in list(cache):
        try:
            if (now - stamp(cache[fid].get('kickoffUtc'))).total_seconds() > 7 * 86400:
                del cache[fid]
        except (ValueError, TypeError, AttributeError):
            del cache[fid]

    insights = {fid: {'text': e['text'], 'model': e.get('model', ''),
                      'generatedAt': e.get('generatedAt', '')}
                for fid, e in cache.items() if e.get('text')}
    out = ('/* LLM-generated match insights. No API key. */\n'
           'window.AI_INSIGHTS = ' + json.dumps(insights, ensure_ascii=False, separators=(',', ':')) + ';\n')

    # Secret-leak guard: never publish the API key.
    if api_key and api_key in out:
        raise RuntimeError('Secret detected in output; refusing to publish insights.')

    (root / 'ai-insights.js.tmp').write_text(out, encoding='utf-8')
    (root / 'ai-insights.js.tmp').replace(root / 'ai-insights.js')
    cache_out = json.dumps(cache, ensure_ascii=False, indent=2) + '\n'
    (root / 'ai-insights-cache.json.tmp').write_text(cache_out, encoding='utf-8')
    (root / 'ai-insights-cache.json.tmp').replace(root / 'ai-insights-cache.json')

    print('AI insights: %d new, %d updated, %d failed, %d published total.'
          % (generated, updated, failed, len(insights)))


if __name__ == '__main__':
    try:
        run(Path(__file__).resolve().parent)
    except Exception as exc:  # never break the deploy over insights
        print('ERROR (non-fatal) in generate_insights.py: ' + str(exc))
        sys.exit(0)

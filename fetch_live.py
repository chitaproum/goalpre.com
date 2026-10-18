#!/usr/bin/env python3
"""Lightweight live-score fetcher for GoalPre.

ONE API-Football request per run: GET /fixtures?live=all returns every match
currently in play worldwide, so polling every 5 minutes costs ~288 requests/day
(well under a 7500/day quota). The result is written to a small live.json that a
separate workflow commits to a dedicated data branch; the browser polls that raw
file and overlays live scores onto the static predictions. The API key is read
ONLY from the API_FOOTBALL_KEY environment variable and never ships to clients.

Standard library only (Python 3.11+). Designed to fail soft: on any API/network
problem it exits without overwriting the previous live.json, so the site keeps
showing the last good snapshot instead of going blank.
"""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = 'https://v3.football.api-sports.io'
UTC = dt.timezone.utc
# Statuses that mean a match is actually being played (mirrors fetch_data.py LIVE).
LIVE = {'1H', 'HT', '2H', 'ET', 'BT', 'P', 'LIVE', 'INT'}


def fetch_live(key, timeout=60):
    """Return the raw `response` list from /fixtures?live=all (one request)."""
    url = BASE + '/fixtures?' + urllib.parse.urlencode({'live': 'all'})
    req = urllib.request.Request(
        url, headers={'x-apisports-key': key, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        payload = json.load(response)
    errors = payload.get('errors')
    if errors:
        # Don't echo arbitrary server content (may contain secrets).
        fields = ', '.join(errors.keys()) if isinstance(errors, dict) else 'response'
        raise RuntimeError('API returned errors on /fixtures?live=all (%s).' % fields)
    resp = payload.get('response')
    if not isinstance(resp, list):
        raise RuntimeError('Unexpected API response on /fixtures?live=all.')
    return resp


def build_live_map(raw):
    """Compress the API payload to a tiny {fixtureId: [h, a, el, st]} map.

    Keyed by API-Football fixture id (matches `f.id` in the static data) so the
    browser can overlay scores onto exactly the right fixtures. Each value is a
    positional array [homeGoals, awayGoals, elapsed, status] instead of a
    4-key object: fewer bytes on the wire and fewer property allocations during
    JSON.parse in the browser. Only matches genuinely in play are kept.
    """
    fixtures = {}
    for f in raw:
        fix = f.get('fixture') or {}
        st = ((fix.get('status') or {}).get('short')) or ''
        if st not in LIVE:
            continue
        fid = fix.get('id')
        if fid is None:
            continue
        goals = f.get('goals') or {}
        fixtures[str(fid)] = [
            goals.get('home'),                      # [0] current home goals
            goals.get('away'),                      # [1] current away goals
            (fix.get('status') or {}).get('elapsed'),  # [2] minutes played
            st,                                     # [3] short status (1H/HT/2H/...)
        ]
    return fixtures


def main():
    root = Path(__file__).resolve().parent
    key = os.environ.get('API_FOOTBALL_KEY')
    if not key:
        print('API_FOOTBALL_KEY is not set; skipping live update.', file=sys.stderr)
        return 0
    try:
        raw = fetch_live(key)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            RuntimeError, ValueError) as exc:
        # Fail soft: keep the previous live.json so the site stays usable.
        print('Live fetch failed; keeping previous snapshot: %s' % exc,
              file=sys.stderr)
        return 0

    # Schema v2: compact positional arrays under the short "f" key. The browser
    # stays backward-compatible with the old {"fixtures":{id:{h,a,el,st}}} shape.
    live_map = build_live_map(raw)
    out = {
        'v': 2,
        'generatedAt': dt.datetime.now(UTC).replace(microsecond=0).isoformat(),
        'count': len(live_map),
        'f': live_map,
    }
    (root / 'live.json').write_text(
        json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    print('Wrote live.json with %d live fixtures.' % out['count'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

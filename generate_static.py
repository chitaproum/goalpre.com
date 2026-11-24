#!/usr/bin/env python3
"""Write crawlable, JavaScript-free prediction summaries into index.html.

Reads data.js (already produced by fetch_data.py) and fills the regions between
<!--STATIC:NAME--> ... <!--/STATIC:NAME--> markers in index.html. app.js replaces
these containers on load, so visitors still get the full interactive page, while
crawlers and no-JS clients see real, current content instead of a loading message.
Standard library only. Safe to run repeatedly.
"""
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LABEL = {'H': 'Home win', 'D': 'Draw', 'A': 'Away win'}


def load_data():
    text = (ROOT / 'data.js').read_text(encoding='utf-8')
    start = text.index('window.DATA = ') + len('window.DATA = ')
    return json.loads(text[start:].rstrip().rstrip(';'))


def pick_fixtures(data):
    today = data.get('today') or dt.date.today().isoformat()
    popular = {l['id'] for l in data.get('popularLeagues', [])}
    upcoming = [f for f in data['fixtures']
                if f.get('status') == 'NS' and f.get('prediction') and f['date'][:10] >= today]
    days = sorted({f['date'][:10] for f in upcoming})
    for day in days:
        rows = [f for f in upcoming if f['date'][:10] == day and f.get('leagueId') in popular]
        if len(rows) >= 3:
            return day, rows
    for day in days:  # fall back to any league
        rows = [f for f in upcoming if f['date'][:10] == day]
        if len(rows) >= 3:
            return day, rows
    return None, []


def esc(v):
    return html.escape(str(v), quote=True)


def pct(x):
    return '%d%%' % round(x * 100)


def li(f, lead, detail):
    return ('<li><strong>%s vs %s</strong> <span class="sp-meta">%s &middot; %s UTC</span>'
            '<br>%s <span class="sp-meta">%s</span></li>') % (
        esc(f['home']), esc(f['away']), esc(f['league']), esc(f['date'][11:16]), lead, detail)


def build(data):
    day, rows = pick_fixtures(data)
    if not rows:
        return None
    nice = dt.date.fromisoformat(day).strftime('%A %d %B %Y')
    note = ('<p class="sp-note">Model estimates for fixtures on %s, from our Poisson model. '
            'Statistical opinion only, not betting advice. 18+.</p>') % nice
    one_x_two = []
    for f in rows:
        p = f['prediction']
        probs = {'H': p['pHome'], 'D': p['pDraw'], 'A': p['pAway']}
        key = max(probs, key=probs.get)
        one_x_two.append((probs[key], f, key, probs))
    one_x_two.sort(key=lambda t: -t[0])
    items = [li(f, '<b>%s %s</b>' % (LABEL[k], pct(pr)),
                '(home %s &middot; draw %s &middot; away %s)' % (pct(pb['H']), pct(pb['D']), pct(pb['A'])))
             for pr, f, k, pb in one_x_two[:5]]
    tp1x2 = note + '<ul class="static-picks">' + ''.join(items) + '</ul>'

    ou = []
    for f in rows:
        p = f['prediction']
        over = p['pOver'] >= 0.5
        ou.append((p['pOver'] if over else 1 - p['pOver'], f, over, p))
    ou.sort(key=lambda t: -t[0])
    items = [li(f, '<b>%s 2.5 goals %s</b>' % ('Over' if o else 'Under', pct(pr)),
                '(expected total %.1f goals)' % p['expTotal']) for pr, f, o, p in ou[:5]]
    tpou = note + '<ul class="static-picks">' + ''.join(items) + '</ul>'

    trend = sorted(one_x_two, key=lambda t: -(t[0] + abs(t[1]['prediction']['expTotal'] - 2.6) * 0.05))[:3]
    items = [li(f, '<b>%s %s</b>' % (LABEL[k], pct(pr)),
                '(expected goals %.1f&ndash;%.1f)' % (f['prediction']['expH'], f['prediction']['expA']))
             for pr, f, k, pb in trend]
    hagrid = '<ul class="static-picks">' + ''.join(items) + '</ul>'
    return {'TP1X2': tp1x2, 'TPOU': tpou, 'HAGRID': hagrid}, day


def main():
    data = load_data()
    result = build(data)
    if not result:
        print('No upcoming fixtures with predictions; index.html left unchanged.')
        return 0
    blocks, day = result
    path = ROOT / 'index.html'
    page = path.read_text(encoding='utf-8')
    for name, content in blocks.items():
        pat = re.compile(r'<!--STATIC:%s-->.*?<!--/STATIC:%s-->' % (name, name), re.S)
        if not pat.search(page):
            print('Marker %s missing in index.html' % name, file=sys.stderr)
            return 1
        page = pat.sub(lambda m: '<!--STATIC:%s-->\n%s\n<!--/STATIC:%s-->' % (name, content, name), page)
    path.write_text(page, encoding='utf-8')
    print('Static homepage content written for', day)
    return 0


if __name__ == '__main__':
    sys.exit(main())

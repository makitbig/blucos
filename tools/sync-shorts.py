"""Add new Blucos YouTube Shorts to the homepage (site/site.json "shorts") from the channel's public RSS feed.

Run daily by .github/workflows/sync-shorts.yml, or by hand:  python3 tools/sync-shorts.py
Then rebuild with tools/build-site.py. Prints "changed" when it added anything.

A video is added only when
  - it is new: its id is not in "shorts" and not in "shorts_seen" (every video handled once is remembered there,
    so a Short taken off the site by hand does not come back), and
  - its description links to a game's page, https://blucos.studio/go/<id>/ (or /games/<id>), so other uploads stay off.
Language: a Hangul title shows on the Korean pages, anything else on the English pages.
A new video with the same title and language as one already listed takes its place (a re-cut of the same Short).
The poster is YouTube's vertical thumbnail, scaled to 360x640.
"""
import io
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site/site.json'
CHANNEL = 'UCyg0sZ9qiCB4diw7LZ8YqqQ'  # youtube.com/@blucosgames
FEED = f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL}'
NS = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015',
      'm': 'http://search.yahoo.com/mrss/'}


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'blucos-site-sync'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def clean_title(t):
    t = re.sub(r'\s*#\S+', '', t)  # "#Shorts" and other hashtags
    return t.strip()


def poster(vid):
    for name in ('oardefault', 'oar2', 'hq720', 'hqdefault'):
        try:
            im = Image.open(io.BytesIO(get(f'https://i.ytimg.com/vi/{vid}/{name}.jpg'))).convert('RGB')
        except Exception:
            continue
        w, h = im.size
        if w * 16 > h * 9:  # wider than 9:16 (a letterboxed frame): keep the middle
            cw = round(h * 9 / 16)
            im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
        path = f'assets/shorts/{vid}.jpg'
        im.resize((360, 640), Image.LANCZOS).save(ROOT / path, quality=80, optimize=True, progressive=True)
        return path
    raise RuntimeError(f'no thumbnail for {vid}')


def main():
    site = json.loads(SITE.read_text())
    games = {g['id'] for g in json.loads((ROOT / 'games.json').read_text())['games']}
    shorts = site.setdefault('shorts', [])
    seen = site.setdefault('shorts_seen', [])
    seen.extend(s['id'] for s in shorts if s['id'] not in seen)  # so a Short later taken off by hand stays off
    known = set(seen)

    feed = ET.fromstring(get(FEED))
    added = []
    for e in reversed(feed.findall('a:entry', NS)):  # oldest first, so the newest ends up on top
        vid = e.find('yt:videoId', NS).text
        if vid in known:
            continue
        title = clean_title(e.find('a:title', NS).text or '')
        desc = e.find('m:group/m:description', NS).text or ''
        m = re.search(r'blucos\.studio/(?:go|games)/([a-z0-9]+)', desc)
        seen.append(vid)
        known.add(vid)
        if not m or m.group(1) not in games or not title:
            print('skip', vid, title)
            continue
        lang = 'ko' if re.search(r'[가-힣]', title) else 'en'
        entry = {'id': vid, 'lang': lang, 'title': {lang: title}, 'game': m.group(1), 'poster': poster(vid)}
        for old in [s for s in shorts if s.get('lang') == lang and s['title'].get(lang) == title]:
            shorts.remove(old)
            p = ROOT / old['poster']
            if p.exists():
                p.unlink()
            print('replaces', old['id'])
        shorts.insert(0, entry)
        added.append(vid)
        print('add', vid, lang, entry['game'], title)

    SITE.write_text(json.dumps(site, ensure_ascii=False, indent=2) + '\n')
    if added:
        print('changed')


if __name__ == '__main__':
    sys.exit(main())

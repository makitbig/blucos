#!/usr/bin/env python3
"""Design previews for the Blucos website: preview/<variant>/ (Korean home + one game page each).

    python3 tools/build-preview.py

Same data as the real site (games.json, site/strings.json, site/site.json, site/games/<id>.json), with
two different looks so the user can pick one. Not linked from the real pages and marked noindex.
Art for the previews: assets/art/ (cutouts and banners from the games, small WebP files).
Type: the device's own sans (Roboto / San Francisco / Segoe UI, Apple SD Gothic Neo / Noto Sans KR / Malgun Gothic),
no web fonts; headings stand out by weight and size.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('site_build', ROOT / 'tools' / 'build-site.py')
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
e, pick = B.e, B.pick
LANG = 'ko'
T = B.STR[LANG]
GAMES = [g for g in B.GAMES if not g.get('hidden')]
GAME_PAGE = 'fossildig'

# Per-game art for the previews: a banner for the card and a cutout that peeks out of it.
ART = {
    'hatchbingo': {'banner': 'banner-hatchbingo.webp', 'peek': 'hatch.webp', 'hero': 'hatch.webp'},
    'evolution2048': {'banner': 'banner-evolution2048.webp', 'peek': 'evo-dino.webp', 'hero': 'evo-dino.webp'},
    'fossildig': {'banner': 'banner-fossildig.webp', 'peek': 'fd-pickaxe.webp', 'hero': 'fd-bone.webp'},
    'starfall': {'banner': 'banner-starfall.webp', 'peek': 'star.webp', 'hero': 'star.webp'},
}
VARIANTS = {
    'a': {'name': '시안 A · 파란 우주', 'other': 'b'},
    'b': {'name': '시안 B · 스티커북', 'other': 'a'},
}
EXTRA = {'cta': '게임 보러 가기', 'games.sub': '하나씩 정성껏 만들고 있어요. 모두 스토어에 곧 나와요.', 'shots': '게임 화면'}


def head(title, up, v, desc):
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta name="theme-color" content="{'#0b1240' if v == 'a' else '#fff6e6'}">
  <link rel="icon" href="{up}assets/favicon.png">
  <link rel="stylesheet" href="{up}preview/{v}/style.css">
</head>'''


def topbar(up, v, home):
    o = VARIANTS[v]['other']
    logo = 'assets/art/logo-white.png' if v == 'a' else 'assets/logo.png'
    return f'''
  <div class="pv-note">디자인 {e(VARIANTS[v]['name'])} · 실제 사이트 아님 · <a href="{up}preview/{o}/">다른 시안 보기</a></div>
  <header class="top">
    <a class="logo" href="{home}"><img src="{up}{logo}" alt="Blucos Games" width="180" height="30"></a>
    <nav><a href="{home}#games">{e(T['nav.games'])}</a><a href="{up}ko/contact.html">{e(T['nav.contact'])}</a></nav>
  </header>'''


def footer(up):
    return f'''
  <footer>
    <img class="foot-planet" src="{up}assets/art/planet.webp" alt="" width="72" height="72" loading="lazy">
    <nav><a href="{up}ko/contact.html">{e(T['footer.contact'])}</a><a href="{up}ko/privacy.html">{e(T['footer.privacy'])}</a></nav>
    <p>© 2026 Blucos · <a href="mailto:{B.EMAIL}">{B.EMAIL}</a></p>
  </footer>'''


def card(g, up, i, v='a'):
    a = ART.get(g['id'], {})
    c1, c2 = g.get('frame', ['#5ec8ff', '#124ed2'])
    link = f'games/{g["id"]}.html' if g['id'] == GAME_PAGE else f'{up}ko/games/{g["id"]}.html'
    peek = f'<img class="peek" src="{up}assets/art/{a["peek"]}" alt="" loading="lazy">' if a.get('peek') and v == 'a' else ''
    return f'''
        <article class="card" style="--c1:{c1};--c2:{c2};--i:{i}">
          <a class="card-link" href="{link}" aria-label="{e(pick(g['name'], LANG))}"></a>
          <div class="art"><img src="{up}assets/art/{a.get('banner', '')}" alt="" loading="lazy" width="640" height="320">{peek}</div>
          <div class="body">
            <img class="icon" src="{up}{e(g['icon'])}" alt="" width="72" height="72" loading="lazy">
            <h3>{e(pick(g['name'], LANG))}</h3>
            <p>{e(pick(g['tagline'], LANG))}</p>
            <div class="actions">{B.stores(g, T)}<span class="more">{e(T['game.page'])} ›</span></div>
          </div>
        </article>'''


def hero(up, v):
    t, n = T['hero.title'], len(GAMES)
    text = B.hero_text(T['hero.text'], n, LANG)
    if v == 'a':
        # just the blue cosmos picture behind the words (tools/make-cosmos.py); the games come further down
        deco = ''
        title = t.replace('작은 퍼즐 게임', '<em>작은 퍼즐 게임</em>')
    else:
        # one large piece of art per game, still (no wobble)
        deco = f'''
      <div class="stickers" aria-hidden="true">{''.join(f'<img class="st s{k}" src="{up}assets/art/{ART[g["id"]]["hero"]}" alt="">' for k, g in enumerate(GAMES) if g['id'] in ART)}
      </div>'''
        title = t.replace('진짜 세상', '<mark class="m1">진짜 세상</mark>').replace('퍼즐 게임', '<mark class="m2">퍼즐 게임</mark>')
    return f'''
    <section class="hero">{deco}
      <div class="copy">
        <h1>{title}</h1>
        <p>{e(text)}</p>
        <p class="studio">{e(T['hero.studio'])}</p>
        <a class="cta" href="#games">{e(EXTRA['cta'])}</a>
      </div>
    </section>'''


def shorts(up):
    items = ''.join(B.short(s, LANG, T, up) for s in B.SITE.get('shorts', [])[:2])
    return f'''
    <section id="shorts" class="band">
      <h2>{e(T['shorts.title'])}</h2>
      <p class="sub">{e(T['shorts.text'])}</p>
      <div class="shorts">{items}</div>
      <p class="note">{e(T['shorts.note'])}</p>
    </section>{B.SHORTS_JS}'''


def home(v):
    up = '../../'
    cards = ''.join(card(g, up, i, v) for i, g in enumerate(GAMES))
    wave = '<svg class="wave" viewBox="0 0 1440 60" preserveAspectRatio="none" aria-hidden="true"><path d="M0 30 C 240 0 480 60 720 30 S 1200 0 1440 30 V60 H0 Z"/></svg>' if v == 'b' else ''
    body = f'''{hero(up, v)}{wave}
    <section id="games" class="band games-band">
      <h2>{e(T['games.title'])}</h2>
      <p class="sub">{e(EXTRA['games.sub'])}</p>
      <div class="cards">{cards}
      </div>
    </section>{shorts(up)}'''
    return f'''{head(T['title'], up, v, T['description'])}
<body class="v-{v} home">{topbar(up, v, './')}
  <main>{body}
  </main>{footer(up)}
</body>
</html>
'''


def game(v, gid):
    up = '../../../'
    g = next(x for x in GAMES if x['id'] == gid)
    d = json.loads((ROOT / 'site' / 'games' / f'{gid}.json').read_text())
    w = d.get(LANG) or d['en']
    a = ART.get(gid, {})
    c1, c2 = g.get('frame', ['#5ec8ff', '#124ed2'])
    alts = w.get('shotsAlt', [])
    shots = ''.join(
        f'<figure class="phone" style="--r:{(-2, 1.5, -1, 2)[(n - 1) % 4]}deg"><img src="{up}assets/games/{gid}/{LANG}-{n}.jpg" alt="{e(alts[n - 1] if n <= len(alts) else "")}" loading="lazy" width="540" height="1170"></figure>'
        for n in range(1, d.get('shots', 0) + 1))
    parts = ''.join(
        f'<section class="part" style="--i:{k}"><h2>{e(s["title"])}</h2><ul>{"".join(f"<li>{e(i)}</li>" for i in s["items"])}</ul></section>'
        for k, s in enumerate(w.get('sections', [])))
    body = f'''
    <section class="ghero" style="--c1:{c1};--c2:{c2}">
      <a class="back" href="../#games">‹ {e(T['gamepage.back'])}</a>
      <img class="gbanner" src="{up}assets/art/{a.get('banner', '')}" alt="" width="640" height="320">
      <div class="ginfo">
        <img class="gicon" src="{up}{e(g['icon'])}" alt="" width="112" height="112">
        <h1>{e(pick(g['name'], LANG))}</h1>
        <p class="tag">{e(pick(g['tagline'], LANG))}</p>
        <div class="actions">{B.stores(g, T)}</div>
      </div>
      {f'<img class="gpeek" src="{up}assets/art/{a["peek"]}" alt="">' if a.get('peek') and v == 'a' else ''}
    </section>
    <p class="lead">{e(w['lead'])}</p>
    <h2 class="shots-title">{e(EXTRA['shots'])}</h2>
    <div class="phones">{shots}</div>
    <div class="parts">{parts}</div>
    <section class="part links">
      <h2>{e(T['gamepage.support'])}</h2>
      <ul>
        <li><a href="{e(B.game_page(g, LANG, 'help'))}">{e(T['gamepage.help'])}</a></li>
        <li><a href="{e(B.game_page(g, LANG, 'privacy'))}">{e(T['gamepage.privacy'])}</a></li>
      </ul>
    </section>'''
    return f'''{head(pick(g['name'], LANG) + ' · ' + T['title'], up, v, pick(g['tagline'], LANG))}
<body class="v-{v} gamepage">{topbar(up, v, '../')}
  <main>{body}
  </main>{footer(up)}
</body>
</html>
'''


if __name__ == '__main__':
    pages = []
    for v in VARIANTS:
        d = ROOT / 'preview' / v
        (d / 'games').mkdir(parents=True, exist_ok=True)
        h, gp = home(v), game(v, GAME_PAGE)
        (d / 'index.html').write_text(h)
        (d / 'games' / f'{GAME_PAGE}.html').write_text(gp)
        pages += [h, gp]
        print(f'preview/{v}/index.html, preview/{v}/games/{GAME_PAGE}.html')

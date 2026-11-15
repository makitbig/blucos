#!/usr/bin/env python3
"""Build the Blucos website (static HTML for GitHub Pages) from games.json.

    python3 tools/build-site.py

games.json is the one source: every game card on the home page (icon, name, one-line intro, store
buttons or "Coming soon", link to the game's own help site) comes from it, so a new game is one entry
there. Words for the site itself are in site/strings.json, videos and per-language game pages in
site/site.json. English is written at the root, every other language under /<lang>/.

All links are relative, so the site works at makitbig.github.io/blucos/ today and at a custom domain
later (add a CNAME file). games.json, icons/ and app-ads.txt stay at the root: the games read
games.json and icons/ from there, and AdMob looks for app-ads.txt at the root of the domain.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = json.loads((ROOT / 'games.json').read_text())['games']
STR = json.loads((ROOT / 'site' / 'strings.json').read_text())
SITE = json.loads((ROOT / 'site' / 'site.json').read_text())
LANGS = SITE['langs']
EMAIL = SITE['email']
e = html.escape


def pick(o, lang):
    return o.get(lang) or o.get('en') or ''


def game_page(g, lang, kind):
    """URL of a game's help ('help') or privacy ('privacy') page in this language, English if missing."""
    local = SITE['localPages'].get(g['id'], {}).get(lang, {})
    page = local.get(kind, '' if kind == 'help' else 'privacy.html')
    return g['site'] + page


def stores(g, t):
    out = []
    for key, label in (('ios', 'App Store'), ('android', 'Google Play')):
        if g.get(key):
            out.append(f'<a class="store" href="{e(g[key])}" rel="noopener">{label}</a>')
    return ''.join(out) or f'<span class="soon">{e(t["game.soon"])}</span>'


def card(g, lang, t, up):
    c1, c2 = g.get('frame', ['#5ec8ff', '#124ed2'])
    return f'''
      <article class="game" style="--c1:{c1};--c2:{c2}">
        <div class="panel">
          <img class="icon" src="{up}{e(g['icon'])}" alt="" width="88" height="88" loading="lazy">
          <div class="text">
            <h3>{e(pick(g['name'], lang))}</h3>
            <p>{e(pick(g['tagline'], lang))}</p>
          </div>
          <div class="actions">{stores(g, t)}<a class="more" href="{e(game_page(g, lang, 'help'))}">{e(t['game.more'])} ›</a></div>
        </div>
      </article>'''


def short(s, lang, t, up):
    title = pick(s['title'], lang)
    return f'''
      <button class="short" type="button" data-yt="{e(s['id'])}" aria-label="{e(t['shorts.play'].format(title=title))}">
        <img src="{up}{e(s['poster'])}" alt="" width="360" height="640" loading="lazy">
        <span class="play" aria-hidden="true"></span>
        <span class="cap">{e(title)}</span>
      </button>'''


def page(lang, name, title, body, t):
    up = '' if lang == 'en' else '../'
    here = '' if name == 'index' else f'{name}.html'
    alt = ''.join(f'<link rel="alternate" hreflang="{l}" href="{up}{"" if l == "en" else l + "/"}{here or "./"}">' for l in LANGS)
    switch = ' · '.join(
        f'<b>{e(STR[l]["label"])}</b>' if l == lang else f'<a href="{up}{"" if l == "en" else l + "/"}{here or "./"}" hreflang="{l}">{e(STR[l]["label"])}</a>'
        for l in LANGS)
    home = up + ('' if lang == 'en' else lang + '/')
    full = t['title'] if name == 'index' else f'{title} · {t["title"]}'
    return f'''<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(full)}</title>
  <meta name="description" content="{e(t['description'])}">
  <meta property="og:title" content="{e(full)}">
  <meta property="og:description" content="{e(t['description'])}">
  <meta property="og:image" content="{up}assets/og-icon.png">
  <meta name="theme-color" content="#12285c">
  {alt}
  <link rel="icon" href="{up}assets/favicon.png">
  <link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">
  <link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>
  <header class="top">
    <a class="logo" href="{home}"><img src="{up}assets/logo.png" alt="Blucos Games" width="192" height="30"></a>
    <nav><a href="{home}#games">{e(t['nav.games'])}</a><a href="{home}contact.html">{e(t['nav.contact'])}</a></nav>
  </header>
  <main>{body}
  </main>
  <footer>
    <nav><a href="{home}contact.html">{e(t['footer.contact'])}</a><a href="{home}privacy.html">{e(t['footer.privacy'])}</a></nav>
    <p class="lang">{switch}</p>
    <p>© 2026 Blucos · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
  </footer>
</body>
</html>
'''


SHORTS_JS = '''
  <script>
    // Videos load from YouTube only when tapped (no requests to Google before that).
    document.querySelectorAll('.short').forEach(function (b) {
      b.addEventListener('click', function () {
        var f = document.createElement('iframe');
        f.src = 'https://www.youtube-nocookie.com/embed/' + b.dataset.yt + '?autoplay=1&playsinline=1&rel=0';
        f.title = b.getAttribute('aria-label');
        f.allow = 'autoplay; encrypted-media; picture-in-picture';
        f.allowFullscreen = true;
        f.className = 'short-frame';
        b.replaceWith(f);
      });
    });
  </script>'''


def build(lang):
    t = STR[lang]
    up = '' if lang == 'en' else '../'
    out = ROOT if lang == 'en' else ROOT / lang
    out.mkdir(exist_ok=True)
    visible = [g for g in GAMES if not g.get('hidden')]

    home = f'''
    <section class="hero">
      <h1>{e(t['hero.title'])}</h1>
      <p>{e(t['hero.text'])}</p>
    </section>
    <section id="games">
      <h2>{e(t['games.title'])}</h2>
      <div class="games">{''.join(card(g, lang, t, up) for g in visible)}
      </div>
    </section>'''
    if SITE.get('shorts'):
        home += f'''
    <section id="shorts">
      <h2>{e(t['shorts.title'])}</h2>
      <p class="muted">{e(t['shorts.text'])}</p>
      <div class="shorts">{''.join(short(s, lang, t, up) for s in SITE['shorts'][:2])}
      </div>
      <p class="note">{e(t['shorts.note'])}</p>
    </section>{SHORTS_JS}'''
    # Later (step 3): the Blucos story, a note for parents, news and a press kit go here as sections.
    (out / 'index.html').write_text(page(lang, 'index', '', home, t))

    help_links = ''.join(f'<li><a href="{e(game_page(g, lang, "help"))}">{e(pick(g["name"], lang))}</a></li>' for g in visible)
    contact = f'''
    <section class="doc">
      <h1>{e(t['contact.title'])}</h1>
      <p>{e(t['contact.text'])}</p>
      <p><a class="btn" href="mailto:{EMAIL}">{EMAIL}</a></p>
      <h2>{e(t['contact.games'])}</h2>
      <ul>{help_links}</ul>
      <p class="muted">{e(t['contact.press'])}</p>
    </section>'''
    (out / 'contact.html').write_text(page(lang, 'contact', t['contact.title'], contact, t))

    priv_links = ''.join(f'<li><a href="{e(game_page(g, lang, "privacy"))}">{e(pick(g["name"], lang))}</a></li>' for g in visible)
    privacy = f'''
    <section class="doc">
      <h1>{e(t['privacy.title'])}</h1>
      <p class="muted">{e(t['privacy.date'])}</p>
      {t['privacy.body']}
      <h2>{e(t['privacy.games'])}</h2>
      <ul>{priv_links}</ul>
      <p>{t['privacy.contact'].format(email=f'<a href="mailto:{EMAIL}">{EMAIL}</a>')}</p>
    </section>'''
    (out / 'privacy.html').write_text(page(lang, 'privacy', t['privacy.title'], privacy, t))
    print(f'{lang}: {out.relative_to(ROOT) if out != ROOT else "."}/index.html, contact.html, privacy.html ({len(visible)} games)')


if __name__ == '__main__':
    for l in LANGS:
        build(l)

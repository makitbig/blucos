#!/usr/bin/env python3
"""Build the Blucos website (static HTML for GitHub Pages) from games.json.

    python3 tools/build-site.py

games.json is the one source: every game card on the home page (icon, name, one-line intro, store
buttons or "Coming soon", link to the game's own help site) comes from it, so a new game is one entry
there. Words for the site itself are in site/strings.json, videos and per-language game pages in
site/site.json. English is written at the root, every other language under /<lang>/.

Look ("blue cosmos", chosen 2026-11-18 from the previews in preview/): a full-width blue space picture
behind the opening words (assets/art/cosmos-*.webp, drawn by tools/make-cosmos.py), game cards like
glowing collectible cards (banner + cutout from site.json "art"), the device's own sans fonts.

All links are relative. The site is served at https://blucos.studio/ (CNAME file); old
makitbig.github.io/blucos/ addresses redirect there. games.json, icons/ and app-ads.txt stay at the root: the games read
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
    """Store buttons; nothing live yet = one "Coming soon", one live = the other says "<store> coming soon"."""
    pairs = (('ios', 'App Store'), ('android', 'Google Play'))
    if not any(g.get(k) for k, _ in pairs):
        return f'<span class="soon">{e(t["game.soon"])}</span>'
    return ''.join(
        f'<a class="store" href="{e(g[k])}" rel="noopener">{label}</a>' if g.get(k)
        else f'<span class="soon">{e(t["game.soonStore"].format(store=label))}</span>'
        for k, label in pairs)


WORDS = {'en': ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']}


def hero_text(text, n, lang):
    """{count} / {Count}: the number of games, spelled out where the language does that (English up to twelve)."""
    words = WORDS.get(lang)
    word = words[n] if words and n < len(words) else str(n)
    return text.replace('{Count}', word[:1].upper() + word[1:]).replace('{count}', word)


def has_page(g):
    return (ROOT / 'site' / 'games' / f"{g['id']}.json").is_file()


def art(g):
    return SITE.get('art', {}).get(g['id'], {})


def card(g, lang, t, up, i=0):
    """A game card: frame in the game's colours, art banner with a cutout peeking out, icon, name, intro, stores."""
    c1, c2 = g.get('frame', ['#5ec8ff', '#124ed2'])
    a = art(g)
    name = e(pick(g['name'], lang))
    if has_page(g):
        href, more = f'games/{g["id"]}.html', t['game.page']
    else:
        href, more = game_page(g, lang, 'help'), t['game.more']
    banner = f'<img src="{up}assets/art/{e(a["banner"])}" alt="" loading="lazy" width="640" height="320">' if a.get('banner') else ''
    peek = f'<img class="peek" src="{up}assets/art/{e(a["peek"])}" alt="" loading="lazy">' if a.get('peek') else ''
    return f'''
        <article class="card" style="--c1:{c1};--c2:{c2};--i:{i}">
          <a class="card-link" href="{e(href)}" aria-label="{name}"></a>
          <div class="art">{banner}{peek}</div>
          <div class="body">
            <img class="icon" src="{up}{e(g['icon'])}" alt="" width="72" height="72" loading="lazy">
            <h3>{name}</h3>
            <p>{e(pick(g['tagline'], lang))}</p>
            <div class="actions">{stores(g, t)}<span class="more">{e(more)} ›</span></div>
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


def page(lang, name, title, body, t, desc=None, image=None):
    """name: path inside the language folder without .html ('index', 'contact', 'games/fossildig')."""
    up = ('' if lang == 'en' else '../') + '../' * name.count('/')
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
  <meta name="description" content="{e(desc or t['description'])}">
  <meta property="og:title" content="{e(full)}">
  <meta property="og:description" content="{e(desc or t['description'])}">
  <meta property="og:image" content="{up}{image or 'assets/og-icon.png'}">
  <meta name="theme-color" content="#0b1240">
  {alt}
  <link rel="icon" href="{up}assets/favicon.png">
  <link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">
  <link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>
  <header class="top">
    <a class="logo" href="{home}"><img src="{up}assets/art/logo-white.png" alt="Blucos Games" width="180" height="30"></a>
    <nav><a href="{home}#games">{e(t['nav.games'])}</a><a href="{home}contact.html">{e(t['nav.contact'])}</a></nav>
  </header>
  <main>{body}
  </main>
  <footer>
    <img class="foot-planet" src="{up}assets/art/planet.webp" alt="" width="64" height="64" loading="lazy">
    <nav><a href="{home}contact.html">{e(t['footer.contact'])}</a><a href="{home}privacy.html">{e(t['footer.privacy'])}</a></nav>
    <p class="lang">{switch}</p>
    <p>© 2026 Blucos · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
  </footer>
</body>
</html>
'''


def game_detail(g, lang, t):
    """games/<id>.html: one page per game, filled from site/games/<id>.json (words) and games.json (the rest)."""
    d = json.loads((ROOT / 'site' / 'games' / f"{g['id']}.json").read_text())
    w = d.get(lang) or d['en']
    up = ('' if lang == 'en' else '../') + '../'
    c1, c2 = g.get('frame', ['#5ec8ff', '#124ed2'])
    shot_lang = lang if (ROOT / 'assets' / 'games' / g['id'] / f'{lang}-1.jpg').is_file() else 'en'
    alts = w.get('shotsAlt', [])
    def size(path):  # real width and height for the img tag (PNG/JPEG header read by Pillow if present)
        try:
            from PIL import Image
            return Image.open(path).size
        except Exception:
            return (540, 1170)
    shot_tags = []
    for n in range(1, d.get('shots', 0) + 1):
        rel = f'assets/games/{g["id"]}/{shot_lang}-{n}.jpg'
        w_, h_ = size(ROOT / rel)
        shot_tags.append(f'<img src="{up}{rel}" alt="{e(alts[n - 1] if n <= len(alts) else "")}" width="{w_}" height="{h_}" loading="lazy">')
    a = art(g)
    banner = f'<img class="gbanner" src="{up}assets/art/{e(a["banner"])}" alt="" width="640" height="320">' if a.get('banner') else '<div class="gbanner"></div>'
    peek = f'<img class="gpeek" src="{up}assets/art/{e(a["peek"])}" alt="">' if a.get('peek') else ''
    phones = ''.join(f'<figure class="phone" style="--r:{(-2, 1.5, -1, 2)[k % 4]}deg">{tag}</figure>' for k, tag in enumerate(shot_tags))
    parts = ''.join(
        f'<section class="part"><h2>{e(sec["title"])}</h2><ul>{"".join(f"<li>{e(i)}</li>" for i in sec["items"])}</ul></section>'
        for sec in w.get('sections', []))
    body = f'''
    <section class="ghero" style="--c1:{c1};--c2:{c2}">
      <a class="back" href="../#games">‹ {e(t['gamepage.back'])}</a>
      {banner}
      <div class="ginfo">
        <img class="gicon" src="{up}{e(g['icon'])}" alt="" width="112" height="112">
        <h1>{e(pick(g['name'], lang))}</h1>
        <p class="tag">{e(pick(g['tagline'], lang))}</p>
        <div class="actions">{stores(g, t)}</div>
      </div>
      {peek}
    </section>
    <p class="lead">{e(w['lead'])}</p>
    <h2 class="shots-title">{e(t['gamepage.shots'])}</h2>
    <div class="phones">{phones}</div>
    <div class="parts">{parts}</div>
    <section class="part links">
      <h2>{e(t['gamepage.support'])}</h2>
      <ul>
        <li><a href="{e(game_page(g, lang, 'help'))}">{e(t['gamepage.help'])}</a></li>
        <li><a href="{e(game_page(g, lang, 'privacy'))}">{e(t['gamepage.privacy'])}</a></li>
        <li><a href="../contact.html">{e(t['nav.contact'])}</a></li>
      </ul>
    </section>'''
    return page(lang, f"games/{g['id']}", pick(g['name'], lang), body, t, desc=pick(g['tagline'], lang), image=g['icon'])


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

    title = e(t['hero.title'])
    hl = e(t.get('hero.highlight', ''))
    if hl and hl in title:
        title = title.replace(hl, f'<em>{hl}</em>', 1)
    home = f'''
    <section class="hero">
      <div class="copy">
        <h1>{title}</h1>
        <p>{e(hero_text(t['hero.text'], len(visible), lang))}</p>
        <p class="studio">{e(t['hero.studio'])}</p>
        <a class="cta" href="#games">{e(t['hero.cta'])}</a>
      </div>
    </section>
    <section id="games" class="band">
      <h2>{e(t['games.title'])}</h2>
      <p class="sub">{e(t['games.sub'])}</p>
      <div class="cards">{''.join(card(g, lang, t, up, i) for i, g in enumerate(visible))}
      </div>
    </section>'''
    if SITE.get('shorts'):
        home += f'''
    <section id="shorts" class="band">
      <h2>{e(t['shorts.title'])}</h2>
      <p class="sub">{e(t['shorts.text'])}</p>
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

    pages = [g for g in visible if has_page(g)]
    if pages:
        (out / 'games').mkdir(exist_ok=True)
    for g in pages:
        (out / 'games' / f"{g['id']}.html").write_text(game_detail(g, lang, t))
    pages_list = ', '.join(g['id'] for g in pages) or 'none'
    print(f'{lang}: {out.relative_to(ROOT) if out != ROOT else "."}/index.html, contact.html, privacy.html ({len(visible)} games, pages: {pages_list})')


if __name__ == '__main__':
    for l in LANGS:
        build(l)

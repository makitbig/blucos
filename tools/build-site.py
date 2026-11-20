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
PAGES = {k: json.loads((ROOT / 'site' / 'pages' / f'{k}.json').read_text()) for k in ('story', 'parents')}
NEWS = json.loads((ROOT / 'site' / 'news.json').read_text())['posts']
BASE_URL = 'https://blucos.studio/'  # absolute address for link previews (og:image needs one); keep in step with CNAME
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
LANGS = SITE['langs']
DOCS = ROOT / 'site' / 'docs'  # each game's help and privacy pages (HTML fragments), written to games/<id>/
ASTRO = (342, 420)  # assets/art/astronaut.webp: Evolution 2048's astronaut, as on the YouTube banner
EMAIL = SITE['email']
PRIVACY_EMAIL = SITE.get('privacy_email', EMAIL)
e = html.escape


def pick(o, lang):
    return o.get(lang) or o.get('en') or ''


def game_page(g, lang, kind, up=''):
    """URL of a game's help ('help') or privacy ('privacy') page in this language, English if missing.
    Games with pages in site/docs/<id>/ have them on this site at games/<id>/ (2026-11-20: store links all on
    blucos.studio); up is the way back to the site root from the page that links."""
    local = SITE['localPages'].get(g['id'], {}).get(lang, {})
    page = local.get(kind, '' if kind == 'help' else 'privacy.html')
    if (DOCS / g['id']).is_dir():
        return f'{up}games/{g["id"]}/{page}'
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
        href, more = game_page(g, lang, 'help', up), t['game.more']
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


def shorts_for(lang):
    # Videos marked with a "lang" show only on that language's pages (the first two are shown); others show everywhere.
    ok = lambda s, l: s.get('lang') in (None, l)
    return [s for s in SITE['shorts'] if ok(s, lang)] or [s for s in SITE['shorts'] if ok(s, 'en')]


def short(s, lang, t, up):
    title = pick(s['title'], lang)
    return f'''
      <button class="short" type="button" data-yt="{e(s['id'])}" aria-label="{e(t['shorts.play'].format(title=title))}">
        <img src="{up}{e(s['poster'])}" alt="" width="360" height="640" loading="lazy">
        <span class="play" aria-hidden="true"></span>
        <span class="cap">{e(title)}</span>
      </button>'''


def page(lang, name, title, body, t, desc=None, image=None, doc=None):
    """name: path inside the language folder without .html ('index', 'contact', 'games/fossildig').
    doc: for a game's help or privacy page (games/<id>/<file>), {'up': ..., 'lang': page language}: the
    site's words come from lang (English or Korean), the page carries its own language links."""
    up = ('' if lang == 'en' else '../') + '../' * name.count('/')
    here = '' if name == 'index' else f'{name}.html'
    alt = ''.join(f'<link rel="alternate" hreflang="{l}" href="{up}{"" if l == "en" else l + "/"}{here or "./"}">' for l in LANGS)
    switch = ' · '.join(
        f'<b>{e(STR[l]["label"])}</b>' if l == lang else f'<a href="{up}{"" if l == "en" else l + "/"}{here or "./"}" hreflang="{l}">{e(STR[l]["label"])}</a>'
        for l in LANGS)
    home = up + ('' if lang == 'en' else lang + '/')
    if doc:
        up, alt, switch = doc['up'], '', ''
        home = up + ('' if lang == 'en' else lang + '/')
        lang = doc['lang']
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
  <meta property="og:image" content="{BASE_URL}{image or 'assets/og-icon.png'}">
  <meta name="theme-color" content="#0b1240">
  {alt}
  <link rel="icon" href="{up}assets/favicon.png">
  <link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">
  <link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>
  <header class="top">
    <a class="logo" href="{home}"><img src="{up}assets/art/logo-white.png" alt="Blucos Games" width="180" height="30"></a>
    <nav><a href="{home}#games">{e(t['nav.games'])}</a><a href="{home}story.html">{e(t['nav.story'])}</a><a href="{home}contact.html">{e(t['nav.contact'])}</a></nav>
  </header>
  <main>{body}
  </main>
  <footer>
    <img class="foot-planet" src="{up}assets/art/planet.webp" alt="" width="64" height="64" loading="lazy">
    <nav>{''.join(f'<a href="{home}{k}.html">{e(t["footer." + k])}</a>' for k in ('story', 'parents', 'news', 'contact', 'privacy'))}</nav>
    {f'<p class="lang">{switch}</p>' if switch else ''}
    <p class="social">{' · '.join(f'<a href="{e(x["url"])}" rel="me">{e(x["name"])}</a>' for x in SITE.get('social', []))}</p>
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
        <li><a href="{e(game_page(g, lang, 'help', up))}">{e(t['gamepage.help'])}</a></li>
        <li><a href="{e(game_page(g, lang, 'privacy', up))}">{e(t['gamepage.privacy'])}</a></li>
        <li><a href="../contact.html">{e(t['nav.contact'])}</a></li>
      </ul>
    </section>'''
    return page(lang, f"games/{g['id']}", pick(g['name'], lang), body, t, desc=pick(g['tagline'], lang), image=g['icon'])


def date_text(d, lang):
    y, m, day = (int(x) for x in d.split('-'))
    return f'{y}년 {m}월 {day}일' if lang == 'ko' else f'{MONTHS[m - 1]} {day}, {y}'


def prose_page(key, lang, t):
    """story.html / parents.html: a cosmos header with the headline, then sections of plain paragraphs."""
    w = PAGES[key].get(lang) or PAGES[key]['en']
    up = '' if lang == 'en' else '../'
    secs = []
    for sec in w['sections']:
        h = f'<h2>{e(sec["title"])}</h2>' if sec.get('title') else ''
        ps = ''.join(f'<p>{e(x)}</p>' for x in sec['paras'])
        if sec.get('email'):
            ps += f'<p><a class="btn" href="mailto:{EMAIL}">{EMAIL}</a></p>'
        secs.append(f'<section>{h}{ps}</section>')
    extra = ''
    if w.get('privacyLinks'):
        links = ''.join(f'<li><a href="{e(game_page(g, lang, "privacy", up))}">{e(pick(g["name"], lang))}</a></li>' for g in GAMES if not g.get('hidden'))
        extra = f'<section><h2>{e(w["privacyLinks"])}</h2><ul>{links}</ul></section>'
    lead = f'<p class="plead">{e(w["lead"])}</p>' if w.get('lead') else ''
    closing = f'<p class="closing">{e(w["closing"])}</p>' if w.get('closing') else ''
    body = f'''
    <section class="phero phero-{key}">
      <p class="kicker">{e(w['kicker'])}</p>
      <h1>{e(w['headline'])}</h1>
    </section>
    <article class="prose">{lead}{''.join(secs)}{extra}{closing}</article>'''
    return page(lang, key, w['title'], body, t, desc=w['desc'])


def news_page(lang, t):
    up = '' if lang == 'en' else '../'
    posts = []
    for p in NEWS:
        g = next((x for x in GAMES if x['id'] == p.get('game')), None)
        foot = ''
        if g:
            more = f'<a class="more-link" href="games/{g["id"]}.html">{e(t["news.page"])} ›</a>' if has_page(g) else ''
            foot = f'<div class="post-game"><img src="{up}{e(g["icon"])}" alt="" width="48" height="48"><b>{e(pick(g["name"], lang))}</b><div class="actions">{stores(g, t)}{more}</div></div>'
        paras = ''.join(f'<p>{e(x)}</p>' for x in pick(p['paras'], lang))
        posts.append(f'''
      <article class="post" id="{e(p['id'])}">
        <time datetime="{p['date']}">{date_text(p['date'], lang)}</time>
        <h2>{e(pick(p['title'], lang))}</h2>{paras}{foot}
      </article>''')
    body = f'''
    <section class="phero phero-news">
      <p class="kicker">{e(t['news.title'])}</p>
      <h1>{e(t['news.lead'])}</h1>
    </section>
    <div class="prose posts">{''.join(posts)}
    </div>'''
    return page(lang, 'news', t['news.title'], body, t, desc=t['news.desc'])


def go_pages():
    """go/<id>/: the link the games put in share text. Opens this phone's store when the game is there,
    otherwise shows the game with its store buttons. One page for every language (English, Korean if the
    phone is set to Korean), with link-preview tags so the shared link shows the game."""
    try:
        from PIL import Image
    except ImportError:
        Image = None
    t_en, t_ko = STR['en'], STR['ko']
    for g in GAMES:
        d = ROOT / 'go' / g['id']
        d.mkdir(parents=True, exist_ok=True)
        a = art(g)
        og = g['icon']
        if Image and a.get('banner'):
            (ROOT / 'assets' / 'og').mkdir(exist_ok=True)
            Image.open(ROOT / 'assets' / 'art' / a['banner']).convert('RGB').save(ROOT / 'assets' / 'og' / f"{g['id']}.png", optimize=True)
            og = f"assets/og/{g['id']}.png"
        c1, c2 = g.get('frame', ['#5ec8ff', '#124ed2'])
        name_en, name_ko = pick(g['name'], 'en'), pick(g['name'], 'ko')
        tag_en, tag_ko = pick(g['tagline'], 'en'), pick(g['tagline'], 'ko')
        banner = f'<img class="gbanner" src="../../assets/art/{e(a["banner"])}" alt="" width="640" height="320">' if a.get('banner') else '<div class="gbanner"></div>'
        about_en = f"../../games/{g['id']}.html" if has_page(g) else game_page(g, 'en', 'help', '../../')
        about_ko = f"../../ko/games/{g['id']}.html" if has_page(g) else game_page(g, 'ko', 'help', '../../')
        links = json.dumps({'ios': g.get('ios') or '', 'android': g.get('android') or ''})
        (d / 'index.html').write_text(f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(name_en)} · Blucos Games</title>
  <meta name="description" content="{e(tag_en)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{BASE_URL}go/{g['id']}/">
  <meta property="og:title" content="{e(name_en)}">
  <meta property="og:description" content="{e(tag_en)}">
  <meta property="og:image" content="{BASE_URL}{og}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#0b1240">
  <link rel="icon" href="../../assets/favicon.png">
  <link rel="stylesheet" href="../../assets/site.css">
  <script>
    (function () {{
      // Straight to this phone's store when the game is there; iPadOS reports itself as a Mac with touch.
      var l = {links}, ua = navigator.userAgent;
      var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
      var to = ios ? l.ios : /Android/.test(ua) ? l.android : '';
      if (to) location.replace(to);
    }})();
  </script>
</head>
<body>
  <main class="go">
    <a class="logo go-logo" href="../../"><img src="../../assets/art/logo-white.png" alt="Blucos Games" width="180" height="30"></a>
    <section class="ghero" style="--c1:{c1};--c2:{c2}">
      {banner}
      <div class="ginfo">
        <img class="gicon" src="../../{e(g['icon'])}" alt="" width="112" height="112">
        <h1 data-ko="{e(name_ko)}">{e(name_en)}</h1>
        <p class="tag" data-ko="{e(tag_ko)}">{e(tag_en)}</p>
        <div class="actions" data-en="{e(stores(g, t_en))}" data-ko-html="{e(stores(g, t_ko))}">{stores(g, t_en)}</div>
        <p><a class="more-link" href="{e(about_en)}" data-ko-href="{e(about_ko)}" data-ko="{e(t_ko['go.about'])}">{e(t_en['go.about'])} ›</a></p>
      </div>
    </section>
  </main>
  <script>
    if (/^ko/i.test(navigator.language || '')) {{
      document.documentElement.lang = 'ko';
      document.querySelectorAll('[data-ko]').forEach(function (el) {{ el.textContent = el.dataset.ko + (el.classList.contains('more-link') ? ' ›' : ''); }});
      document.querySelectorAll('[data-ko-html]').forEach(function (el) {{ el.innerHTML = el.dataset.koHtml; }});
      document.querySelectorAll('[data-ko-href]').forEach(function (el) {{ el.href = el.dataset.koHref; }});
      document.title = document.querySelector('h1').textContent + ' · Blucos Games';
    }}
  </script>
</body>
</html>
''')
    print(f'go/: {", ".join(g["id"] for g in GAMES)}')


def doc_pages():
    """games/<id>/<file>.html from site/docs/<id>/<file>.html: each game's help (index, ko, ja, ...) and privacy
    (privacy, privacy-ko, ...) pages in the site's look, at the same file names the games' old sites used, so
    makitbig.github.io/<game>/<file> can redirect to blucos.studio/games/<game>/<file>."""
    import re
    done = []
    for g in GAMES:
        src = DOCS / g['id']
        if not src.is_dir():
            continue
        out = ROOT / 'games' / g['id']
        out.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob('*.html')):
            s = f.read_text()
            meta = dict(re.findall(r'<!-- (\w+): (.*?) -->', s))
            plang = meta.get('lang', 'en')
            ui = plang if plang in LANGS else 'en'
            t = STR[ui]
            head = re.search(r'<header>(.*?)</header>', s, re.S).group(1)
            main = re.search(r'<main>(.*?)</main>', s, re.S).group(1)
            back = f'../{g["id"]}.html' if ui == 'en' else f'../../{ui}/games/{g["id"]}.html'
            body = f"""
    <section class="doc docpage">
      <a class="docback" href="{e(back)}">‹ {e(pick(g['name'], ui))}</a>
      <div class="dochead">
        <img src="../../{e(g['icon'])}" alt="" width="64" height="64">
        {head.strip()}
      </div>
      {main.strip()}
    </section>"""
            title = re.sub(r'\s*[—-]\s*', ' · ', meta.get('title', ''), count=1)
            html_out = page(ui, 'games/x', title, body, t, desc=meta.get('desc') or None, image=g['icon'],
                            doc={'up': '../../', 'lang': plang})
            (out / f.name).write_text(html_out)
            done.append(f.name)
        for old in out.glob('*.css'):  # the plain copies from before had their own stylesheet
            old.unlink()
    print(f'games/<id>/: {len(done)} help and privacy pages')


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
      <img class="astro" src="{up}assets/art/astronaut.webp" alt="" width="{ASTRO[0]}" height="{ASTRO[1]}">
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
      <div class="shorts">{''.join(short(s, lang, t, up) for s in shorts_for(lang)[:2])}
      </div>
      <p class="note">{e(t['shorts.note'])}</p>
    </section>{SHORTS_JS}'''
    latest = NEWS[0] if NEWS else None
    news_tile = f'''
        <a class="tile" href="news.html#{e(latest['id'])}"><b>{e(t['about.news'])}</b><span>{e(pick(latest['title'], lang))}</span><time>{date_text(latest['date'], lang)}</time></a>''' if latest else ''
    about = f'''
    <section id="about" class="band about">
      <a class="story-card" href="story.html">
        <p class="kicker">{e(t['about.kicker'])}</p>
        <h2>{e(t['about.title'])}</h2>
        <p>{e(t['about.text'])}</p>
        <span class="more">{e(t['about.read'])} ›</span>
      </a>
      <div class="tiles">
        <a class="tile" href="parents.html"><b>{e(t['about.parents'])}</b><span>{e(t['about.parentsText'])}</span></a>{news_tile}
      </div>
    </section>'''
    if '<section id="shorts"' in home:
        home = home.replace('\n    <section id="shorts"', about + '\n    <section id="shorts"', 1)
    else:
        home += about
    (out / 'index.html').write_text(page(lang, 'index', '', home, t))

    help_links = ''.join(f'<li><a href="{e(game_page(g, lang, "help", up))}">{e(pick(g["name"], lang))}</a></li>' for g in visible)
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

    priv_links = ''.join(f'<li><a href="{e(game_page(g, lang, "privacy", up))}">{e(pick(g["name"], lang))}</a></li>' for g in visible)
    privacy = f'''
    <section class="doc">
      <h1>{e(t['privacy.title'])}</h1>
      <p class="muted">{e(t['privacy.date'])}</p>
      {t['privacy.body']}
      <h2>{e(t['privacy.games'])}</h2>
      <ul>{priv_links}</ul>
      <p>{t['privacy.contact'].format(email=f'<a href="mailto:{PRIVACY_EMAIL}">{PRIVACY_EMAIL}</a>')}</p>
    </section>'''
    (out / 'privacy.html').write_text(page(lang, 'privacy', t['privacy.title'], privacy, t))

    for key in PAGES:
        (out / f'{key}.html').write_text(prose_page(key, lang, t))
    (out / 'news.html').write_text(news_page(lang, t))

    pages = [g for g in visible if has_page(g)]
    if pages:
        (out / 'games').mkdir(exist_ok=True)
    for g in pages:
        (out / 'games' / f"{g['id']}.html").write_text(game_detail(g, lang, t))
    pages_list = ', '.join(g['id'] for g in pages) or 'none'
    print(f'{lang}: {out.relative_to(ROOT) if out != ROOT else "."}/index.html, story, parents, news, contact, privacy ({len(visible)} games, pages: {pages_list})')


if __name__ == '__main__':
    for l in LANGS:
        build(l)
    go_pages()
    doc_pages()

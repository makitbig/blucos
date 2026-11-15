#!/usr/bin/env python3
"""Copy the shared Blucos game list into every game.

Writes www/blucos-games.js (loader + games.json bundled as the offline fallback), the other games'
icons (www/assets/more/<id>.png), and the share-card frame (www/blucos-share.js + www/assets/share/blucos-logo.png)
into each game repo. The game repos are expected next to this repo
(../hatch-bingo, ../evolution-2048, ...). Run it after changing games.json, then commit in each game.

Adding a game: put its 120px icon in icons/, add it to games.json and GAMES below, push this repo
(the games already in stores pick it up from the web), then run this script for the next app updates.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = {  # id in games.json -> game repo folder next to this repo
    'hatchbingo': 'hatch-bingo',
    'evolution2048': 'evolution-2048',
    'fossildig': 'fossil-dig',
    'starfall': 'starfall',
}


def main():
    data = json.loads((ROOT / 'games.json').read_text())
    ids = [g['id'] for g in data['games']]
    for g in data['games']:
        assert (ROOT / g['icon']).is_file(), f"missing icon {g['icon']}"
    template = (ROOT / 'tools' / 'blucos-games.template.js').read_text()
    js = template.replace('/*BUNDLED*/null', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    only = set(sys.argv[1:])  # optional game ids: sync just those (e.g. `sync.py hatchbingo`)
    for gid, folder in GAMES.items():
        if only and gid not in only:
            continue
        www = ROOT.parent / folder / 'www'
        if not www.is_dir():
            print(f'skip {gid}: {www} not found', file=sys.stderr)
            continue
        (www / 'blucos-games.js').write_text(js)
        # Share-card frame (same look in every game) and the Blucos logo it puts in the footer.
        shutil.copyfile(ROOT / 'tools' / 'blucos-share.js', www / 'blucos-share.js')
        (www / 'assets' / 'share').mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'share' / 'blucos-logo.png', www / 'assets' / 'share' / 'blucos-logo.png')
        more = www / 'assets' / 'more'
        more.mkdir(parents=True, exist_ok=True)
        for other in data['games']:
            if other['id'] != gid:
                shutil.copyfile(ROOT / other['icon'], more / f"{other['id']}.png")
        for logo in ('blucos-logo.png', 'blucos-logo-white.png'):  # share-card footer (CARDS.md)
            shutil.copyfile(ROOT / 'brand' / logo, more / logo)
        print(f'{gid}: www/blucos-games.js + {len(ids) - 1} icons + logos')


if __name__ == '__main__':
    main()

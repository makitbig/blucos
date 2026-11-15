# Blucos

The shared list of Blucos games, served by GitHub Pages at
https://makitbig.github.io/blucos/games.json. Each Blucos game reads it once per launch for its
"More games from Blucos" menu section, so a new game or a new store link reaches every game
without an app update. Each game also ships a copy (www/blucos-games.js) for offline use.

## Adding a game or a store link

1. Add a 120px PNG icon to `icons/` (for a new game).
2. Edit `games.json`: `name` and `tagline` per language (missing languages fall back to `en`),
   `ios` / `android` store links (empty = "Coming soon"), `"hidden": true` to leave a game out.
   For a new game, also add its repo folder to `GAMES` in `tools/sync.py`.
3. Push. Games already installed pick it up on their next launch.
4. Run `python3 tools/sync.py` (game repos next to this one) and commit in each game, so the next
   app updates ship the new list and icons.

## Share cards

`CARDS.md` is the shared share-card frame (story 9:16 and square, footer band with the Blucos logo,
share link from `games.json`). `games.json` gives each game a `site` used as the share link until its
store links are filled in; `BlucosGames.shareLink(id)` picks the right one.

## Share cards

`tools/blucos-share.js` is the frame every game puts around a card picture shared to social media (tier-colored
border, sheen on rare tiers, footer with the game icon and name, "App Store · Google Play" and the Blucos logo from
`share/blucos-logo.png`). The game draws only what goes inside. `BlucosShare.link(id, site)` takes the store link
from games.json, so cards shared after release point at the store with no app update. `sync.py` copies both files
into each game; native sharing needs `@capacitor/share` and `@capacitor/filesystem` in the game. First used by
Starfall (www/cards.js).

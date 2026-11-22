# Blucos share cards

Every Blucos game draws its share pictures in one shared frame, so the three games look like one family.

- Code: `tools/blucos-share.js` (`BlucosShare.render / link / share`). First made in Fossil Dig (9b661f6);
  this is now the master copy. `tools/sync.py` copies it to `www/blucos-share.js` in every game, with the
  logo at `www/assets/share/blucos-logo.png`. Edit it here, never in a game.
- Examples: Fossil Dig `www/cards.js` (animal card, museum card), Hatch Bingo `www/cards.js`
  (`drawCardShare`, `drawBookShare`, `openShareSheet`).

## Two pictures per game

1. **Single card**: the item just collected (bird, fossil, constellation), in the game's own card style.
2. **Collection card**: the collection on one picture. A name, a big count (`24` large, `/60` smaller), a
   progress bar, and a tile for every item: collected ones in colour, missing ones as flat shadows, so the
   gaps make you want to fill them.

## Frame (drawn by `BlucosShare.render`; games only paint the content box)

| Format | Canvas | Footer height |
|---|---|---|
| Story 9:16 | 1080 x 1920 | 200 |
| Square 1:1 | 1080 x 1080 | 150 |
| Card 2:3 | 1080 x 1620 | 150 |

- Outer frame: a two-colour diagonal gradient, full bleed (`theme.frame`, or `tier.frame` for a rarer
  card, with `tier.shine` for a sheen). Frame width 36.
- Inner panel: `theme.paper`, radius 40. The content box is the panel inset by 36, above the footer.
- Footer, inside the panel: a hairline, then the game icon (104 story / 84 square and card, radius 22%), the game
  name and `App Store · Google Play` on the left; the Blucos logo on the right (52 / 44 high).
- On stories, keep the top 100 px of the content box free of important text (Instagram's own bar).

## Share text and link

- One short line in the player's language, a space, then `BlucosShare.link(<game id>, lang, <site>)`.
  It returns this platform's store link from `games.json` once the game is out, and the game's `site` from
  `games.json` (or the fallback) before that, so shares switch to the store without an app update.
- Nothing about the player in the picture or the text: no names, no account, no device info.

## When to share

- When a new item arrives (a small Share button), in the single-card viewer, and on the collection
  screen. Only when the player taps it: no share pop-ups, no rewards for sharing.
- The button opens a small sheet: preview, Story / Square, Share, Close. Closing returns to where the
  player was.

## iOS

- `NSPhotoLibraryAddUsageDescription` must be in Info.plist (and in each `<lang>.lproj/InfoPlist.strings`),
  or the app can crash when the player taps "Save Image" in the share sheet.
- Capacitor `@capacitor/share` and `@capacitor/filesystem` plugins.

## Files here

- `tools/blucos-share.js`: the frame. `brand/blucos-logo.png`: the logo for the light panel (navy, cropped,
  480 px wide), from `blucos-tools/marketing/logo/final/blucos-logo-horizontal-transparent.png`.
  `brand/blucos-logo-white.png`: for dark backgrounds.
- `python3 tools/sync.py <id> ...` syncs only the named games (no ids: all of them).

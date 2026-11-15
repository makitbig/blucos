# Blucos share cards

Every Blucos game draws its share pictures in the same frame, so a shared card is recognisably Blucos
and the three games look like a family. The reference implementation is Hatch Bingo, `www/cards.js`
(`SHARE_FMT`, `shareFrame`, `drawCardShare`, `drawBookShare`, `openShareSheet`, `shareImage`).

## Two pictures

1. **Single card**: the one thing just collected (a bird, a fossil, a constellation). Keep the game's own
   card design; the frame only places it.
2. **Collection card**: the whole collection on one picture. Name of the collection, a big count
   (`24` large, `/60` smaller), a progress bar, then a grid of every item: collected ones in colour,
   missing ones as flat shadows (silhouettes), so the gaps make you want to fill them. No locked
   names or spoilers beyond the shape.

## Sizes (canvas, px)

| Format | Size | Content area (y) | Footer band (y, height) |
|---|---|---|---|
| Story 9:16 | 1080 x 1920 | 200 to 1524 | 1560, 160 |
| Square 1:1 | 1080 x 1080 | 54 to 850 | 886, 140 |

- Side margin 54 on both. The story keeps the top 200 and bottom 200 clear of Instagram's buttons.
- Background: a two-colour diagonal gradient that fills the whole canvas (the game's or the rarity's
  colours). Content is centred in the content area; the single card keeps its own aspect ratio.

## Footer band (same in every game)

- White rounded rectangle, x 54, width 972, radius 36, soft shadow (`rgba(40,20,0,0.18)`, blur 24, y 6).
- Left: the game icon, square, side = band height - 44, inset 26 from the left and 22 from the top,
  corner radius 22% of its side.
- Next to it (24 gap): the game name on line 1 (bold, 30% of band height, dark), and on line 2
  `App Store · Google Play` (18% of band height, muted). Same text in every language.
- Right: the Blucos logo (`brand/blucos-logo.png`, horizontal, transparent), height 40% of band
  height, 30 from the right edge, centred vertically.

## Share text and link

- Text: one short line in the player's language, then a space and the link.
- Link: `BlucosGames.shareLink(<game id>)`. It gives this platform's store link from `games.json`
  once the game is out, and the game's `site` before that, so shares switch to the store without an
  app update. Keep the game's own site URL as a fallback in code too.
- Nothing personal in the picture or the text: no names, no account, no device info.

## When to share

- From the moment a new item arrives (a small "Share" button), from the single card viewer, and from
  the collection screen ("Show off my book" style button). Only when the player taps it.
- Never a pop-up that asks to share, never a reward for sharing.
- The button opens a small sheet: the preview, a Story / Square choice, Share and Close. Closing it
  returns to where the player was.

## Files

- `brand/blucos-logo.png` (dark text, for the white band) and `brand/blucos-logo-white.png` (for dark
  backgrounds). `tools/sync.py` copies both into each game's `www/assets/more/`.
- `tools/sync.py <id> ...` syncs only the named games.

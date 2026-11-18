# Blucos

The shared list of Blucos games, served by GitHub Pages at
https://blucos.studio/games.json (formerly makitbig.github.io/blucos/, which now redirects). Each Blucos game reads it once per launch for its
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

`tools/blucos-share.js` is the frame every game puts around a card picture shared to social media: outer frame,
inner panel, and a footer with the game icon and name, "App Store · Google Play" and the Blucos mark (drawn in code),
in the same place in every game. The game paints only the content box (`BlucosShare.render`). `BlucosShare.link`
takes the store link from games.json, so cards shared after release point at the store with no app update.
`sync.py` copies it into each game. First written in Fossil Dig (9b661f6); Starfall uses the same file. Native
sharing needs `@capacitor/share` and `@capacitor/filesystem`, and iOS needs `NSPhotoLibraryAddUsageDescription`
so "Save Image" in the share sheet does not crash the app.

## Website

The same repo is the Blucos website: https://blucos.studio/ (English at the root, Korean
under `ko/`). Every page is static HTML written by `python3 tools/build-site.py` from `games.json`
(game cards: icon, name, intro, store buttons or "Coming soon", `frame` colours, `site` link),
`site/strings.json` (the site's words per language) and `site/site.json` (email, videos, per-language
pages of each game's own site). Edit those, run the script, commit the generated pages.

- Story and For parents pages: `site/pages/story.json` and `site/pages/parents.json` (headline, sections of
  paragraphs, per language). The story stays general on purpose: a child who loves to draw and their dad,
  no name, age, school or photo. News: `site/news.json`, newest first; the home page shows the latest.
- Share links: `go/<id>/` (one per game in `games.json`) opens the store of the phone that opens it, or
  shows the game with its store buttons when that store has no link yet. `BlucosGames.shareLink(id)` returns
  it, so apps built from now on share `https://blucos.studio/go/<id>/`. Link previews use
  `assets/og/<id>.png` (made from the card banner).
- New language: add it to `langs` in `site/site.json` and its words to `site/strings.json`.
  Game names and intros already come from `games.json` (10 languages).
- Custom domain later: add a `CNAME` file with the domain and set it in the repo's Pages settings.
  Links are relative, so nothing else changes. Old `makitbig.github.io/blucos/...` addresses redirect
  to the domain with the same path, so the games keep finding `games.json` and `icons/`.
- `app-ads.txt` is for AdMob. AdMob only reads it at the root of the developer website's domain
  (e.g. `blucos.games/app-ads.txt`), so it works once the custom domain is set and that domain is the
  developer website in App Store Connect and Play Console.
- Videos: `assets/shorts/<id>.jpg` posters (a frame from the source video); the YouTube player loads
  only when tapped (youtube-nocookie.com).
- Look: "blue cosmos" (chosen 2026-11-18 from the previews in `preview/`). Card and game-page art per
  game: `site/site.json` "art" (files in `assets/art/`; a game without art gets its frame colours).
  The opening picture is drawn by `tools/make-cosmos.py`. Fonts: the device's own sans, no web fonts.

## Custom domain (2026-11-18)
- blucos.studio (Cloudflare Registrar, DNS only: 4 GitHub A records, www CNAME makitbig.github.io, TXT for GitHub domain verification). `CNAME` file in this repo; HTTPS enforced.
- GitHub redirects old makitbig.github.io/blucos/... addresses to **http**://blucos.studio/..., which app WebViews block as mixed content. Apps already shipped fall back to their cached/bundled list; new releases fetch https://blucos.studio/ directly (template BASE), so run tools/sync.py before each game's next release.

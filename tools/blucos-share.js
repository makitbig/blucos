// Blucos share cards (2026-11-16): the frame every Blucos game puts around a picture players share.
// Game-agnostic on purpose, so Hatch Bingo, Fossil Dig and Starfall look like one family: same outer
// frame, same inner panel, same footer (game icon + name + "App Store · Google Play" on the left, the
// Blucos mark on the right) in the same place. Each game only paints the content box.
//
//   BlucosShare.render({ format, theme, game, tier, draw }) -> Promise<dataURL (PNG)>
//     format: 'story' (1080x1920, 9:16) | 'square' (1080x1080) | 'card' (1080x1440, 3:4, a greeting card)
//     theme:  { frame: [c1, c2], paper, ink, muted, font }   the game's own colours and font stack
//     game:   { name, icon }                                  icon: a square image path
//     tier:   optional { frame: [c1, c2], shine: true }       a rarer card: other frame colours, a sheen
//     logo:   optional path of the Blucos logo in the app (default assets/share/blucos-logo.png)
//     draw:   async (ctx, box, kit) => {}                     paints inside box {x, y, w, h}
//   BlucosShare.link(gameId, lang, fallback) -> the store link from the shared games list
//     (blucos-games.js, refreshed from blucos.studio/games.json), or fallback before launch
//   BlucosShare.share({ dataUrl, fileName, title, text }) -> share sheet (Capacitor Share + Filesystem),
//     the Web Share API, or a download in a desktop browser
//
// The Blucos logo: ~/blucos-tools/marketing/logo/final/blucos-logo-horizontal-transparent.png (navy on
// transparent, for the light panel), cropped to its edges and shrunk to 480px wide for the app. Dark cards
// would use blucos-logo-stacked-transparent-white.png; the symbol alone is blucos-symbol-transparent.png.
//
// No names, photos or anything else about the player goes on a card.
//
// Shared file: the master copy is blucos/tools/blucos-share.js (rules in blucos/CARDS.md). tools/sync.py
// copies it and the logo (www/assets/share/blucos-logo.png) into every game; edit it there, not in a game.
'use strict';
window.BlucosShare = (() => {
  const SIZES = { story: [1080, 1920], square: [1080, 1080], card: [1080, 1440] };
  const FRAME = 36, RADIUS = 40;
  const FOOT = { story: 200, square: 150, card: 150 };

  const rr = (ctx, x, y, w, h, r) => { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); };
  const image = src => new Promise(ok => {
    if (!src) return ok(null);
    const im = new Image(); im.onload = () => ok(im); im.onerror = () => ok(null); im.src = src;
  });
  // Fill the box with the picture, cropping what does not fit (focus: 0..1 where to keep, x and y).
  function cover(ctx, im, x, y, w, h, fx = 0.5, fy = 0.5) {
    const s = Math.max(w / im.width, h / im.height), dw = im.width * s, dh = im.height * s;
    ctx.drawImage(im, x + (w - dw) * fx, y + (h - dh) * fy, dw, dh);
  }
  // Fit the whole picture inside the box, centred on x and resting on the bottom.
  function contain(ctx, im, x, y, w, h) {
    const s = Math.min(w / im.width, h / im.height), dw = im.width * s, dh = im.height * s;
    ctx.drawImage(im, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
  }
  // Wrap text into at most maxLines lines; spaced languages break at spaces, ja/zh at any character.
  // Returns the y after the last line.
  function wrap(ctx, text, x, y, maxW, lh, maxLines = 3) {
    const parts = /\s/.test(text) ? text.split(/(\s+)/) : [...text];
    const lines = []; let line = '';
    for (const p of parts) {
      if (ctx.measureText(line + p).width > maxW && line.trim()) { lines.push(line.trim()); line = p.trimStart(); }
      else line += p;
    }
    if (line.trim()) lines.push(line.trim());
    if (lines.length > maxLines) {
      lines.length = maxLines;
      let last = lines[maxLines - 1];
      while (last && ctx.measureText(last + '…').width > maxW) last = last.slice(0, -1);
      lines[maxLines - 1] = last.trimEnd() + '…';
    }
    for (const l of lines) { ctx.fillText(l, x, y); y += lh; }
    return y;
  }
  // Shrink a one-line text until it fits maxW.
  function fit(ctx, text, maxW, size, weight, family, min = 24) {
    let s = size;
    do { ctx.font = `${weight} ${s}px ${family}`; s -= 2; } while (ctx.measureText(text).width > maxW && s > min);
  }

  // Fallback only, when the logo image cannot load: a blue disc with a white "b", then the word.
  // Right-aligned at (x, y = text baseline).
  function mark(ctx, x, y, size, color) {
    ctx.save();
    ctx.font = `700 ${size}px "Avenir Next", "Helvetica Neue", Arial, sans-serif`;
    ctx.textAlign = 'right'; ctx.textBaseline = 'alphabetic'; ctx.fillStyle = color;
    ctx.fillText('Blucos', x, y);
    const w = ctx.measureText('Blucos').width, r = size * 0.62, cx = x - w - r - size * 0.3, cy = y - size * 0.36;
    ctx.fillStyle = '#2f7de1'; ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.font = `800 ${size * 1.05}px "Avenir Next", "Helvetica Neue", Arial, sans-serif`;
    ctx.fillText('b', cx, cy + size * 0.37);
    ctx.restore();
  }

  async function render({ format = 'story', theme, game, tier, draw, logo = 'assets/share/blucos-logo.png' }) {
    const [W, H] = SIZES[format] || SIZES.story;
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const ctx = cv.getContext('2d');
    try { await document.fonts.ready; } catch (e) { /* draw with what is there */ }
    // Outer frame: the game's colours (or the rarer tier's), full bleed so stories have no white corners.
    const [c1, c2] = (tier && tier.frame) || theme.frame;
    const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, c1); g.addColorStop(1, c2);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    if (tier && tier.shine) {
      const s = ctx.createLinearGradient(0, H * 0.15, W, H * 0.55);
      s.addColorStop(0, 'rgba(255,255,255,0)'); s.addColorStop(0.5, 'rgba(255,255,255,0.45)'); s.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = s; ctx.fillRect(0, 0, W, H);
    }
    // Inner panel
    const px = FRAME, py = FRAME, pw = W - FRAME * 2, ph = H - FRAME * 2;
    ctx.fillStyle = theme.paper; rr(ctx, px, py, pw, ph, RADIUS); ctx.fill();
    // Content, clipped to the panel above the footer
    const foot = FOOT[format] || FOOT.story;
    const box = { x: px + 36, y: py + 36, w: pw - 72, h: ph - foot - 36 };
    const kit = { rr, image, cover, contain, wrap, fit, format, W, H };
    ctx.save(); rr(ctx, px, py, pw, ph - foot, RADIUS); ctx.clip();
    await draw(ctx, box, kit);
    ctx.restore();
    // Footer: a hairline, the game on the left, Blucos on the right
    const fy = py + ph - foot;
    ctx.fillStyle = theme.muted; ctx.globalAlpha = 0.35; ctx.fillRect(px + 36, fy, pw - 72, 2); ctx.globalAlpha = 1;
    const small = format !== 'story';   // square and card share the smaller footer
    const icon = await image(game.icon), is = small ? 84 : 104, ix = px + 36, iy = fy + (foot - is) / 2;
    if (icon) { ctx.save(); rr(ctx, ix, iy, is, is, is * 0.22); ctx.clip(); ctx.drawImage(icon, ix, iy, is, is); ctx.restore(); }
    const tx = ix + is + 24, mid = fy + foot / 2;
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = theme.ink; fit(ctx, game.name, pw - 72 - is - 24 - 300, small ? 40 : 46, 700, theme.font);
    ctx.fillText(game.name, tx, mid - 4);
    ctx.fillStyle = theme.muted; ctx.font = `500 ${small ? 28 : 32}px "Avenir Next", "Helvetica Neue", Arial, sans-serif`;
    ctx.fillText('App Store · Google Play', tx, mid + (small ? 36 : 42));
    const lg = await image(logo);
    if (lg) {   // the real logo, right-aligned and centred on the footer
      const lh = small ? 44 : 52, lw = lg.width * lh / lg.height;
      ctx.drawImage(lg, px + pw - 36 - lw, mid - lh / 2, lw, lh);
    } else mark(ctx, px + pw - 36, mid + 14, small ? 38 : 44, theme.ink);
    return cv.toDataURL('image/png');
  }

  // Store link for this game from the shared list (this platform's store once out), else its site from the
  // list, else the fallback.
  function link(gameId, lang, fallback) {
    try {
      if (window.BlucosGames && BlucosGames.shareLink) return BlucosGames.shareLink(gameId) || fallback;
      const g = window.BlucosGames && BlucosGames.list('', lang).find(x => x.id === gameId);
      if (g && g.link) return g.link;
    } catch (e) { /* list not loaded */ }
    return fallback;
  }

  async function share({ dataUrl, fileName, title, text }) {
    const P = n => (window.Capacitor && Capacitor.isNativePlatform && Capacitor.isNativePlatform() && Capacitor.Plugins[n]) || null;
    try {
      const S = P('Share'), F = P('Filesystem');
      if (S && F) {
        const { uri } = await F.writeFile({ path: fileName, data: dataUrl.split(',')[1], directory: 'CACHE' });
        await S.share({ title, text, files: [uri] });
        return true;
      }
      const blob = await (await fetch(dataUrl)).blob();
      const file = new File([blob], fileName, { type: 'image/png' });
      if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], text, title }); return true; }
      const a = document.createElement('a'); a.href = dataUrl; a.download = fileName; a.click();
      return true;
    } catch (e) { return false; /* share sheet dismissed */ }
  }

  return { render, link, share, SIZES };
})();

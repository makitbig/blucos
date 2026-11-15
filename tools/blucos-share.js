// Blucos share cards: the frame every Blucos game puts around a card picture shared to social media, so a card from
// Hatch Bingo, Fossil Dig or Starfall looks like it comes from the same family. Same in every game; the game draws
// only what goes inside the frame.
//
//   frame (tier colors, rounded, a sheen on rare tiers) · game content · footer band:
//   [game icon] Game name / App Store · Google Play ............................................ [Blucos logo]
//
// No names, photos or anything personal goes on a card. The link in the share text comes from the shared Blucos
// game list (blucos-games.js), so once a game is in the stores the cards point there with no app update; before
// that, the game's web page.
//
//   BlucosShare.SIZES                -> { story: [1080, 1920], square: [1080, 1080] }
//   BlucosShare.draw(opts)           -> Promise<canvas>
//     opts: { size: 'story'|'square', colors: [light, dark], sheen: bool, game: { name, icon },
//             logo: 'assets/share/blucos-logo.png', content: async (ctx, box) => {} }  box = { x, y, w, h }
//   BlucosShare.link(gameId, site)   -> the store link for this platform, or `site` before release
//   BlucosShare.share(canvas, { file, title, text }) -> share sheet (Capacitor Share + Filesystem), Web Share,
//                                       or a download; resolves quietly when the sheet is dismissed
'use strict';
window.BlucosShare = (() => {
  const SIZES = { story: [1080, 1920], square: [1080, 1080] };
  const FRAME = 34, RADIUS = 64, INNER_R = 40;
  const FONT = (w, s) => `${w} ${s}px Fredoka, Jua, "Apple SD Gothic Neo", "Hiragino Maru Gothic ProN", "PingFang SC", system-ui, sans-serif`;

  const img = src => new Promise(ok => { const im = new Image(); im.onload = () => ok(im); im.onerror = () => ok(null); im.src = src; });
  const rr = (ctx, x, y, w, h, r) => { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); };

  async function draw(o) {
    if (document.fonts) await document.fonts.ready;
    const [W, H] = SIZES[o.size] || SIZES.story;
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const ctx = cv.getContext('2d');
    const [c1, c2] = o.colors || ['#e8ecff', '#8a94c8'];
    // Frame
    const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, c1); g.addColorStop(1, c2);
    ctx.fillStyle = g; rr(ctx, 0, 0, W, H, RADIUS); ctx.fill();
    // Footer band (inside the frame, at the bottom)
    const footH = o.size === 'square' ? 132 : 168;
    const ix = FRAME, iy = FRAME, iw = W - FRAME * 2, ih = H - FRAME * 2;
    ctx.save(); rr(ctx, ix, iy, iw, ih, INNER_R); ctx.clip();
    ctx.fillStyle = '#fffdf6'; ctx.fillRect(ix, iy + ih - footH, iw, footH);
    // Content
    const box = { x: ix, y: iy, w: iw, h: ih - footH };
    ctx.save(); ctx.beginPath(); ctx.rect(box.x, box.y, box.w, box.h); ctx.clip();
    if (o.content) await o.content(ctx, box);
    ctx.restore();
    ctx.restore();
    // Footer: game icon and name, store names, Blucos logo
    const fy = iy + ih - footH, mid = fy + footH / 2, pad = 36;
    const icon = o.game && o.game.icon ? await img(o.game.icon) : null;
    const isz = footH - 44;
    let tx = ix + pad;
    if (icon) {
      ctx.save(); rr(ctx, tx, mid - isz / 2, isz, isz, isz * 0.22); ctx.clip();
      ctx.drawImage(icon, tx, mid - isz / 2, isz, isz); ctx.restore();
      tx += isz + 22;
    }
    ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    ctx.fillStyle = '#1b2350'; ctx.font = FONT(700, o.size === 'square' ? 40 : 46);
    ctx.fillText((o.game && o.game.name) || '', tx, mid - 4);
    ctx.fillStyle = '#6b7096'; ctx.font = FONT(600, o.size === 'square' ? 26 : 30);
    ctx.fillText('App Store · Google Play', tx, mid + (o.size === 'square' ? 34 : 40));
    const logo = await img(o.logo || 'assets/share/blucos-logo.png');
    if (logo) {
      const lw = o.size === 'square' ? 250 : 290, lh = logo.height * lw / logo.width;
      ctx.drawImage(logo, ix + iw - pad - lw, mid - lh / 2, lw, lh);
    }
    // Sheen across rare cards
    if (o.sheen) {
      ctx.save(); rr(ctx, 0, 0, W, H, RADIUS); ctx.clip();
      ctx.globalCompositeOperation = 'screen';
      const s = ctx.createLinearGradient(0, H * 0.15, W, H * 0.55);
      s.addColorStop(0, 'rgba(255,255,255,0)'); s.addColorStop(0.38, 'rgba(255,255,255,0)');
      s.addColorStop(0.5, 'rgba(255,255,255,0.13)'); s.addColorStop(0.62, 'rgba(255,255,255,0)'); s.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = s; ctx.fillRect(0, 0, W, H);
      ctx.restore();
    }
    return cv;
  }

  function link(gameId, site) {
    try {
      const g = window.BlucosGames && BlucosGames.list('', 'en').find(x => x.id === gameId);
      if (g && g.link) return g.link;
    } catch (e) { /* no list: the site */ }
    return site;
  }

  async function share(cv, { file = 'blucos-card.png', title = '', text = '' } = {}) {
    const url = cv.toDataURL('image/png');
    const P = n => (window.Capacitor && Capacitor.isNativePlatform && Capacitor.isNativePlatform() && Capacitor.Plugins && Capacitor.Plugins[n]) || null;
    try {
      const S = P('Share'), F = P('Filesystem');
      if (S && F) {
        const { uri } = await F.writeFile({ path: file, data: url.split(',')[1], directory: 'CACHE' });
        await S.share({ title, text, files: [uri] });
        return;
      }
      const blob = await (await fetch(url)).blob();
      const f = new File([blob], file, { type: 'image/png' });
      if (navigator.canShare && navigator.canShare({ files: [f] })) { await navigator.share({ files: [f], text, title }); return; }
      const a = document.createElement('a'); a.href = url; a.download = file; a.click();
    } catch (e) { /* share sheet dismissed */ }
  }

  return { SIZES, FONT, draw, link, share, img };
})();

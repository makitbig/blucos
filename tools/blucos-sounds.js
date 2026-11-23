// End-of-round sounds, the same in every Blucos game (chosen by the user from the sound lab, 2026-11-23:
// music box "D1" for a cleared board, the short "D6" for small or frequent wins, "A" for a lost round).
// COPIED into each game's www/ by blucos/tools/sync.py. Do not edit in a game repo: edit it in the blucos repo.
//
// Plain Web Audio, no files: works offline and adds nothing to the app size. Each call plays into the game's own
// AudioContext and returns how long the sound lasts, so the game can turn its music down for that time:
//
//   const len = BlucosSounds.win(ctx, sfxOut);      // board cleared (about 2 s)
//   const len = BlucosSounds.winShort(ctx, sfxOut); // small or frequent win, a new best score (about 1.3 s)
//   const len = BlucosSounds.lose(ctx, sfxOut);     // round lost: two soft falling notes, never harsh (about 1.2 s)
//   BlucosSounds.duck(musicGain, ctx, len);         // music down to 22% for len seconds, then back over 0.7 s
//
// sfxOut is the node the game's sound effects go into (it must reach ctx.destination), and the game's
// "sound off" setting still applies: skip the call when sound is off. musicGain is a GainNode in the music
// path only (not the effects). Call these only on a user-visible end of a round, never in a loop.
'use strict';
window.BlucosSounds = (() => {
  const hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
  const rooms = new WeakMap();   // one soft reverb per AudioContext and output

  function room(ctx, out) {
    let byOut = rooms.get(ctx);
    if (!byOut) { byOut = new Map(); rooms.set(ctx, byOut); }
    if (byOut.has(out)) return byOut.get(out);
    const bus = ctx.createGain();
    const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -10; comp.ratio.value = 6;
    const len = Math.round(ctx.sampleRate * 2.2), ir = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let c = 0; c < 2; c++) { const d = ir.getChannelData(c); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3); }
    const rev = ctx.createConvolver(); rev.buffer = ir;
    const wet = ctx.createGain(); wet.gain.value = 0.28;
    bus.connect(comp); bus.connect(rev); rev.connect(wet); wet.connect(comp); comp.connect(out);
    byOut.set(out, bus);
    return bus;
  }

  // one music-box note: a pure tone with two faint bell partials, quick attack, long fade
  function box(ctx, out, m, t, dur = 1.1, peak = 0.13, bend = 1) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(peak, t + 0.002);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    g.connect(out);
    for (const [ratio, amp] of [[1, 1], [4.0, 0.16], [10.1, 0.05]]) {
      const o = ctx.createOscillator(), a = ctx.createGain();
      o.frequency.setValueAtTime(hz(m) * ratio, t);
      if (bend !== 1) o.frequency.exponentialRampToValueAtTime(hz(m) * ratio * bend, t + dur * 0.8);
      a.gain.value = amp;
      o.connect(a); a.connect(g);
      o.start(t); o.stop(t + dur + 0.05);
    }
  }

  function play(ctx, out, notes, len) {
    if (!ctx || ctx.state === 'closed') return 0;
    const bus = room(ctx, out || ctx.destination), t = ctx.currentTime + 0.03;
    for (const [m, at, dur, peak, bend] of notes) box(ctx, bus, m, t + at, dur, peak, bend);
    return len;
  }

  return {
    // D1: G C E G, a step back, then high C over a soft chord
    win: (ctx, out) => play(ctx, out, [[79, 0], [84, 0.13], [88, 0.26], [91, 0.39], [88, 0.62], [96, 0.78, 1.8], [84, 0.78, 1.8, 0.08], [88, 0.78, 1.8, 0.07]], 2.0),
    // D6: C E G up to high C
    winShort: (ctx, out) => play(ctx, out, [[84, 0, 0.9], [88, 0.1, 0.9], [91, 0.2, 0.9], [96, 0.32, 1.5], [91, 0.32, 1.5, 0.06]], 1.3),
    // A: G then E, sliding gently down
    lose: (ctx, out) => play(ctx, out, [[79, 0, 0.5, 0.15], [76, 0.26, 0.9, 0.15, 0.97]], 1.2),
    duck(musicGain, ctx, len) {
      if (!musicGain || !ctx || !len || ctx.state === 'closed') return;
      const g = musicGain.gain, t = ctx.currentTime, now = g.value;
      g.cancelScheduledValues(t);
      g.setValueAtTime(now, t);
      g.linearRampToValueAtTime(now * 0.22, t + 0.08);
      g.setValueAtTime(now * 0.22, t + len);
      g.linearRampToValueAtTime(now, t + len + 0.7);
    },
  };
})();

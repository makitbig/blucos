// Blucos rooms: a tiny shared server for games played side by side (Petal Garden's Play together first).
// Design: petal-garden/docs/design/play-together-room.md. Deployed as a Cloudflare Worker on api.blucos.studio.
//
//   POST /v1/rooms/{game}/{code}/join   {p, n}        add or rename me (a finished or stale round resets first)
//   POST /v1/rooms/{game}/{code}/start  {p}           startAt = now + 4 s, unless a round is running
//   POST /v1/rooms/{game}/{code}/score  {p, s, done}  my score so far; it only goes up within a round
//   GET  /v1/rooms/{game}/{code}?p=                   the room, for polling
// Every reply: { now, startAt, you, players: [{ n, s, done }] }  (you = my index, or -1)
//
// p is a random 16-character key the app makes for each match: not a device ID. Each room lives in its own
// Durable Object and deletes itself 10 minutes after its last write. Nothing is logged.

// A new game is added here. round: a round started longer ago than this is over (a phone that slept never says done).
const GAMES = {
  petalgarden: { maxScore: 5000, round: 3 * 60 * 1000 },        // a two-minute race
  starfall: { maxScore: 99999999, round: 30 * 60 * 1000 },      // a two-minute race, or endless (it speeds up without limit; about 6-13 minutes)
};
const MAX_PLAYERS = 8;
const NAME_MAX = 8;
const START_DELAY = 4000;          // every phone counts 3-2-1 toward the same startAt
const ROOM_TTL = 10 * 60 * 1000;   // a room is deleted 10 minutes after its last write
const ORIGINS = ['capacitor://localhost', 'https://localhost', 'http://localhost', 'http://localhost:5188', 'http://localhost:5184'];

const cors = (origin) => (ORIGINS.includes(origin) ? {
  'Access-Control-Allow-Origin': origin,
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
  Vary: 'Origin',
} : { Vary: 'Origin' });

const json = (body, status, origin) => new Response(JSON.stringify(body), {
  status,
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...cors(origin) },
});

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(origin) });
    const url = new URL(req.url);
    const m = url.pathname.match(/^\/v1\/rooms\/([a-z0-9]+)\/(\d{4})(?:\/(join|start|score))?\/?$/);
    if (!m) return json({ error: 'not_found' }, 404, origin);
    const [, game, code, action] = m;
    if (!GAMES[game] || +code < 1000 || +code > 9999) return json({ error: 'not_found' }, 404, origin);
    if ((req.method === 'POST') !== Boolean(action) || !['GET', 'POST'].includes(req.method)) {
      return json({ error: 'method' }, 405, origin);
    }
    if (env.RL) {
      const ip = req.headers.get('CF-Connecting-IP') || '';
      const { success } = await env.RL.limit({ key: ip });
      if (!success) return json({ error: 'slow_down' }, 429, origin);
    }
    let body = {};
    if (action) {
      try { body = await req.json(); } catch { return json({ error: 'bad_json' }, 400, origin); }
      if (!body || typeof body !== 'object') return json({ error: 'bad_json' }, 400, origin);
    } else {
      body = { p: url.searchParams.get('p') || '' };
    }
    const stub = env.ROOMS.get(env.ROOMS.idFromName(`${game}:${code}`));
    const res = await stub.fetch('https://room/', {
      method: 'POST',
      body: JSON.stringify({ action: action || 'get', game, body }),
    });
    const out = await res.json();
    return json(out, res.status, origin);
  },
};

const cleanName = (n) => Array.from(String(n ?? '').replace(/[\u0000-\u001f\u007f-\u009f<>]/g, '').trim()).slice(0, NAME_MAX).join('');
const okKey = (p) => typeof p === 'string' && /^[A-Za-z0-9_-]{16}$/.test(p);

export class Room {
  constructor(ctx) {
    this.ctx = ctx;
    this.room = null;   // { startAt, players: [{ p, n, s, done }] }
  }

  async load() {
    if (!this.room) this.room = (await this.ctx.storage.get('room')) || { startAt: null, players: [] };
    return this.room;
  }

  async save() {
    await this.ctx.storage.put('room', this.room);
    await this.ctx.storage.setAlarm(Date.now() + ROOM_TTL);
  }

  async alarm() {
    this.room = null;
    await this.ctx.storage.deleteAll();
  }

  view(p, now) {
    const r = this.room;
    return {
      now,
      startAt: r.startAt,
      you: r.players.findIndex((x) => x.p === p),
      players: r.players.map(({ n, s, done }) => ({ n, s, done })),
    };
  }

  over(now, game) {
    const r = this.room;
    if (r.startAt == null) return false;
    return now - r.startAt > GAMES[game].round || (r.players.length > 0 && r.players.every((x) => x.done));
  }

  async fetch(req) {
    const { action, game, body } = await req.json();
    const now = Date.now();
    const r = await this.load();
    const p = body.p;
    const reply = (status = 200, extra = {}) => new Response(JSON.stringify({ ...this.view(p, now), ...extra }), { status });
    if (action === 'get') return reply();
    if (!okKey(p)) return reply(400, { error: 'bad_key' });

    if (action === 'join') {
      if (this.over(now, game)) { r.startAt = null; r.players = []; }
      const me = r.players.find((x) => x.p === p);
      if (me) me.n = cleanName(body.n);
      else if (r.players.length >= MAX_PLAYERS) return reply(409, { error: 'full' });
      else r.players.push({ p, n: cleanName(body.n), s: 0, done: false });
      await this.save();
      return reply();
    }

    const me = r.players.find((x) => x.p === p);
    if (!me) return reply(404, { error: 'not_in_room' });

    if (action === 'start') {
      if (r.startAt == null || this.over(now, game)) {
        r.startAt = now + START_DELAY;
        for (const x of r.players) { x.s = 0; x.done = false; }
        await this.save();
      }
      return reply();
    }

    if (action === 'score') {
      const s = body.s;
      if (!Number.isInteger(s) || s < 0 || s > GAMES[game].maxScore) return reply(400, { error: 'bad_score' });
      me.s = Math.max(me.s, s);
      if (body.done === true) me.done = true;
      await this.save();
      return reply();
    }
    return reply(404, { error: 'not_found' });
  }
}

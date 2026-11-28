// Runs against a local server: npx wrangler@4 dev --local --port 8799, then node test/rooms.test.mjs [base] [game]
import assert from 'node:assert/strict';

const BASE = process.argv[2] || 'http://127.0.0.1:8799';
const code = String(1000 + Math.floor(Math.random() * 9000));
const game = process.argv[3] || "petalgarden";
const room = `${BASE}/v1/rooms/${game}/${code}`;
const key = () => Array.from({ length: 16 }, () => 'abcdefghijklmnopqrstuvwxyz0123456789'[Math.floor(Math.random() * 36)]).join('');
const post = async (action, body, origin = 'capacitor://localhost') => {
  const r = await fetch(`${room}/${action}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Origin: origin }, body: JSON.stringify(body) });
  return { status: r.status, body: await r.json(), headers: r.headers };
};
const get = async (p) => { const r = await fetch(`${room}?p=${p}`); return { status: r.status, body: await r.json() }; };
let n = 0;
const ok = (name) => console.log(`ok ${++n} ${name}`);

const a = key(), b = key();
let r = await post('join', { p: a, n: '영희' });
assert.equal(r.status, 200); assert.equal(r.body.you, 0); assert.equal(r.body.startAt, null);
assert.equal(r.headers.get('access-control-allow-origin'), 'capacitor://localhost');
ok('join, CORS for the app');

r = await post('join', { p: b, n: '  <b>엄마</b>\u0007가나다라마바사 ' });
assert.equal(r.body.you, 1); assert.equal(r.body.players[1].n, 'b엄마/b가나다');
assert.ok(!('p' in r.body.players[0]));
ok('second join, name cleaned and cut to 8, keys never returned');

r = await post('join', { p: a, n: 'Younghee' });
assert.equal(r.body.players.length, 2); assert.equal(r.body.players[0].n, 'Younghee');
ok('join again renames');

r = await post('score', { p: key(), s: 10 });
assert.equal(r.status, 404);
r = await post('join', { p: 'short' });
assert.equal(r.status, 400);
ok('unknown player and bad key refused');

r = await post('start', { p: a });
const startAt = r.body.startAt;
assert.ok(startAt - r.body.now >= 3900 && startAt - r.body.now <= 4100);
r = await post('start', { p: b });
assert.equal(r.body.startAt, startAt);
ok('start sets startAt = now + 4 s once');

r = await post('score', { p: a, s: 300 });
r = await post('score', { p: a, s: 200 });
assert.equal(r.body.players[0].s, 300);
r = await post('score', { p: b, s: { starfall: 100000000, evolution2048: 200001 }[game] ?? 5001 });
assert.equal(r.status, 400);
r = await post('score', { p: b, s: 12.5 });
assert.equal(r.status, 400);
ok('score only goes up, 0..5000 integers');

r = await post('score', { p: a, s: 1240, done: true });
r = await get(b);
assert.equal(r.body.you, 1); assert.deepEqual(r.body.players.map((x) => [x.s, x.done]), [[1240, true], [0, false]]);
r = await get('');
assert.equal(r.body.you, -1);
ok('polling');

r = await post('join', { p: key(), n: 'late' });
assert.equal(r.body.players.length, 3);
ok('join during a running round adds the player');

await post('score', { p: b, s: 980, done: true });
r = await post('score', { p: r.body.players.length && a, s: 1240, done: true });
// everyone except "late" is done; late finishes too
const late = key();
const c = key();
r = await post('join', { p: c, n: 'again' });
// the round is not over while "late" is unfinished
assert.equal(r.body.players.length, 4);
ok('round not reset while someone is still playing');

for (const p of [c]) await post('score', { p, s: 0, done: true });
const rLate = (await get('')).body.players.findIndex((x) => x.n === 'late');
assert.ok(rLate >= 0);
ok('state kept');

// fill the room
const fill = [];
for (let i = (await get('')).body.players.length; i < 8; i++) fill.push((await post('join', { p: key(), n: `p${i}` })).status);
r = await post('join', { p: key(), n: 'ninth' });
assert.equal(r.status, 409); assert.equal(r.body.error, 'full');
ok('at most 8 players');

r = await fetch(`${BASE}/v1/rooms/unknown/${code}`);
assert.equal(r.status, 404);
r = await fetch(`${BASE}/v1/rooms/petalgarden/0999`);
assert.equal(r.status, 404);
r = await fetch(`${room}/join`);
assert.equal(r.status, 405);
r = await fetch(`${room}/join`, { method: 'OPTIONS', headers: { Origin: 'https://evil.example' } });
assert.equal(r.headers.get('access-control-allow-origin'), null);
ok('unknown game, bad code, wrong method, foreign origin');

// a finished round resets on the next join
const code2room = `${BASE}/v1/rooms/petalgarden/${code === '9999' ? '1000' : String(+code + 1)}`;
const j = (action, body) => fetch(`${code2room}/${action}`, { method: 'POST', body: JSON.stringify(body) }).then((x) => x.json());
const x = key(), y = key();
await j('join', { p: x }); await j('join', { p: y }); await j('start', { p: x });
await j('score', { p: x, s: 5, done: true }); await j('score', { p: y, s: 7, done: true });
const z = key();
const after = await j('join', { p: z, n: 'next' });
assert.equal(after.startAt, null); assert.equal(after.players.length, 1); assert.equal(after.you, 0);
ok('a finished round resets on the next join');

console.log(`all ${n} passed`);

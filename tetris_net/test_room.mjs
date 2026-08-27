// test_room.mjs — 골든 벡터로 JS room 엔진을 검증한다.
// Go(server_test.go)·파이썬(test_server.py)의 하니스도 하는 일이 똑같다:
// 같은 JSON 을 읽어 같은 순서로 밀어 넣고, 나온 출력을 순서까지 그대로 비교한다.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { Room } from './room.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const VEC = JSON.parse(readFileSync(join(HERE, 'protocol_vectors.json'), 'utf8'));

let pass = 0, fail = 0;
const fails = [];

// 깊은 비교 — 키 순서는 보지 않는다. 세 언어의 JSON 직렬화 순서까지 맞추는 건
// 규격이 아니라 우연이다. 비교는 "파싱한 값"끼리 한다.
function eq(a, b) {
  if (a === b) return true;
  if (typeof a !== typeof b || a === null || b === null) return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (typeof a !== 'object') return false;
  const ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  for (const k of ka) { if (!(k in b) || !eq(a[k], b[k])) return false; }
  return true;
}
const J = (x) => JSON.stringify(x);

function check(name, want, got) {
  if (eq(want, got)) { pass++; return; }
  fail++;
  fails.push(`${name}\n    기대: ${J(want)}\n    실제: ${J(got)}`);
}

for (const c of VEC.cases) {
  const room = new Room(c.cfg, c.seed);
  for (const s of c.setup) room.handle(s.pid, s.m, s.at | 0);
  c.steps.forEach((s, k) => {
    const got = room.handle(s.pid, s.m, s.at | 0);
    check(`${c.name} #${k + 1} (${s.m.t})`, s.out, got);
  });
}

// ── 벡터가 다루지 않는 두 가지를 따로 본다 ──────────────────────────
// 1) 난수열 자체 — 규격에 적힌 xorshift32 그대로인가
{
  const r = new Room({ max: 2 }, 1);
  const got = [];
  for (let i = 0; i < 5; i++) got.push(r.rng());
  check('xorshift32 seed=1', [270369, 67634689, 2647435461, 307599695, 2398689233], got);
}
// 2) 좌석 8석·PC 4대 — 요구사항 그대로의 최대 구성이 실제로 만들어지는가
{
  const r = new Room({ max: 8, perPeer: 2 }, 1);
  for (let pid = 1; pid <= 4; pid++) {
    r.handle(pid, { t: 'seat', i: -1, kind: 'human', name: `P${pid}a` }, 0);
    r.handle(pid, { t: 'seat', i: -1, kind: 'ai', name: `P${pid}b`, lv: 'hard' }, 0);
    r.handle(pid, { t: 'ready', v: true }, 0);
  }
  const outs = r.handle(1, { t: 'start' }, 0);
  check('8석 4PC start', 8, outs[0]?.m?.seats?.length);
  check('8석 4PC 소유', [1, 1, 2, 2, 3, 3, 4, 4], outs[0]?.m?.seats?.map((s) => s.pid));
  const nine = r.handle(5, { t: 'seat', i: -1, kind: 'human', name: 'X' }, 0);
  check('9번째 좌석 거절', [{ to: 5, m: { t: 'err', code: 'phase' } }], nine);
}

console.log(`\nroom 엔진(JS): ${pass} passed, ${fail} failed`);
for (const f of fails) console.log('  ✗ ' + f);
process.exit(fail ? 1 : 0);

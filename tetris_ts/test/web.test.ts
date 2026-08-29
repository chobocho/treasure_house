// test/web.test.ts — 브라우저 번들 검사.
//
// 덱 안의 데모는 모듈이 아니라 평범한 <script> 로 돈다(단일 HTML 이라 임포트할
// 상대 경로가 없다). 그래서 tsc 결과에서 import/export 를 걷어 낸 번들을 만드는데,
// 걷어 내다가 뜻이 달라지면 슬라이드의 코드와 데모가 서로 다른 물건이 된다.
//
// 여기서 확인하는 건 하나다: **번들로 돌린 판과 모듈로 돌린 판이 완전히 같은가.**
// 같은 시드·같은 조작을 먹여 보드 해시와 통계를 통째로 비교한다.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createContext, runInContext } from 'node:vm';

import { Tetris, ACT, ST, boardHash } from '../src/core.js';
import { Ai, DEFAULT_WEIGHTS } from '../src/ai.js';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const WEBJS = join(ROOT, 'web', 'js');
const FILES = ['core.js', 'ai.js', 'ga.js', 'battle.js', 'protocol.js', 'room.js'];

let bundled = false;
function bundle(): void {
  if (bundled) return;
  execFileSync('node', [join(ROOT, 'tools', 'bundle_web.mjs')], { cwd: ROOT, encoding: 'utf8' });
  bundled = true;
}

/**
 * 번들 스크립트를 브라우저처럼 순서대로 한 컨텍스트에 흘려 넣는다.
 *
 * 최상위 `class`·`const` 는 전역 **객체**의 속성이 되지 않는다(선언적 전역 환경에
 * 들어간다). 그래서 ctx 를 뒤져서는 안 나오고, 같은 컨텍스트에서 식을 한 번 더
 * 평가해서 꺼내야 한다 — 덱에서 demo.js 가 이들을 보는 방식과 정확히 같다.
 */
function loadBundle(): Record<string, unknown> {
  bundle();
  const ctx = createContext({ console, Math, JSON, Date, performance });
  for (const f of FILES) {
    runInContext(readFileSync(join(WEBJS, f), 'utf8'), ctx, { filename: f });
  }
  return runInContext('({ Tetris, Ai, boardHash, Battle, Room, packState, DEFAULT_WEIGHTS })',
                      ctx) as Record<string, unknown>;
}

test('bundle_web.mjs 가 web/js 에 스크립트를 만든다', () => {
  bundle();
  for (const f of FILES) assert.ok(existsSync(join(WEBJS, f)), `${f} 가 없다`);
});

test('번들에는 모듈 문법도 node 의존도 남지 않는다', () => {
  bundle();
  for (const f of FILES) {
    const s = readFileSync(join(WEBJS, f), 'utf8');
    assert.ok(!/^\s*import\s/m.test(s), `${f} 에 import 가 남았다`);
    assert.ok(!/^\s*export\s/m.test(s), `${f} 에 export 가 남았다`);
    assert.ok(!/require\(|node:/.test(s), `${f} 가 node API 를 부른다`);
  }
});

test('번들로 돌린 판이 모듈로 돌린 판과 한 칸도 다르지 않다', () => {
  const ctx = loadBundle();
  const seed = 20260829;
  // 같은 조작을 같은 순서로 — 회전·이동·하드드롭을 섞어 락과 줄 지우기까지 간다.
  const script = [ACT.LEFT, ACT.CW, ACT.RIGHT, ACT.HARD, ACT.CCW, ACT.LEFT, ACT.HARD,
                  ACT.HOLD, ACT.RIGHT, ACT.HARD, ACT.FLIP, ACT.HARD];

  const mine = new Tetris(seed);
  const CtorB = (ctx as { Tetris: new (s: number) => unknown }).Tetris;
  const theirs = new CtorB(seed) as { press: (a: number) => void; update: (d: number) => void;
    board: Uint8Array; stats: Int32Array };

  for (let round = 0; round < 20; round++) {
    for (const a of script) {
      mine.press(a); mine.release(a);
      theirs.press(a); (theirs as unknown as { release: (a: number) => void }).release(a);
    }
    mine.update(16); theirs.update(16);
  }
  const hashB = (ctx as { boardHash: (b: Uint8Array) => number }).boardHash;
  assert.equal(hashB(theirs.board), boardHash(mine.board), '보드가 다르다');
  assert.deepEqual(Array.from(theirs.stats), Array.from(mine.stats), '통계가 다르다');
});

test('나중 파일이 앞 파일의 이름을 그대로 본다 (모듈 경계가 사라졌다)', () => {
  const ctx = loadBundle();
  for (const n of ['Tetris', 'Ai', 'Battle', 'Room', 'packState', 'boardHash']) {
    assert.equal(typeof ctx[n], 'function', `${n} 이 전역에 없다`);
  }
});

test('번들의 AI 도 모듈의 AI 와 같은 수를 둔다', () => {
  const ctx = loadBundle();
  const seed = 7;
  const mine = new Tetris(seed);
  const ai = new Ai(mine, DEFAULT_WEIGHTS);

  const C = ctx as { Tetris: new (s: number) => object; Ai: new (g: object, w: readonly number[]) => { step: () => number } };
  const g2 = new C.Tetris(seed);
  const ai2 = new C.Ai(g2, DEFAULT_WEIGHTS);

  const mv: number[] = [], mv2: number[] = [];
  for (let i = 0; i < 30; i++) { mv.push(ai.step()); mv2.push(ai2.step()); }
  assert.deepEqual(mv2, mv, 'AI 가 다른 수를 뒀다');
  assert.equal((g2 as unknown as { stats: Int32Array }).stats[ST.LINES], mine.stats[ST.LINES]);
});

// test_ai.mjs — wasm 코어 + AI + 대전 규칙의 Node 테스트 하니스.
// 브라우저 없이, 실제로 컴파일된 그 wasm 을 그대로 돌려서 검사한다.
//
//   node test_ai.mjs            전체 실행
//   node test_ai.mjs T4         특정 그룹만
import { loadCore, V, ACT, ST, F, STATE, GARBAGE, setWeights, boardHash, seedBoard, dumpBoard } from './core.mjs';
import { readFileSync, existsSync } from 'node:fs';

let pass = 0, fail = 0, group = '';
const only = process.argv[2] || null;
function T(name, fn) {
  if (only && !name.startsWith(only)) return;
  group = name;
  console.log(`\n── ${name}`);
  return fn();
}
function ok(cond, msg, extra) {
  if (cond) { pass++; console.log(`  ✓ ${msg}`); }
  else { fail++; console.log(`  ✗ ${msg}${extra !== undefined ? `  → ${extra}` : ''}`); }
}
function eq(a, b, msg) { ok(a === b, `${msg} (${a} === ${b})`, `실제 ${a}, 기대 ${b}`); }

// ── 순수 JS 로 다시 쓴 특징 함수 (C++ 결과와 교차 검증하기 위한 "두 번째 구현") ──
// 같은 정의를 서로 다른 언어로 두 번 쓰고 결과를 맞춰 보는 것 — 가장 싼 형식 검증이다.
function featuresJS(b, W, H, lines = 0, landH = 0) {
  const h = new Array(W).fill(0);
  let holes = 0;
  for (let x = 0; x < W; x++) {
    let y = 0;
    while (y < H && !b[y * W + x]) y++;
    h[x] = H - y;
    for (let yy = y + 1; yy < H; yy++) if (!b[yy * W + x]) holes++;
  }
  let agg = 0, bump = 0, wells = 0;
  for (let x = 0; x < W; x++) agg += h[x];
  for (let x = 0; x + 1 < W; x++) bump += Math.abs(h[x] - h[x + 1]);
  for (let x = 0; x < W; x++) {
    const l = x === 0 ? H : h[x - 1], r = x === W - 1 ? H : h[x + 1];
    const d = Math.min(l, r) - h[x];
    if (d > 0) wells += (d * (d + 1)) / 2;
  }
  let rowt = 0;
  for (let y = 0; y < H; y++) {
    let prev = 1;
    for (let x = 0; x < W; x++) { const c = b[y * W + x] ? 1 : 0; if (c !== prev) rowt++; prev = c; }
    if (!prev) rowt++;
  }
  let colt = 0;
  for (let x = 0; x < W; x++) {
    let prev = 0;
    for (let y = 0; y < H; y++) { const c = b[y * W + x] ? 1 : 0; if (c !== prev) colt++; prev = c; }
    if (!prev) colt++;
  }
  return [lines, agg, holes, bump, wells, rowt, colt, landH];
}

// 지금 판을 그대로 평가시키고 특징 벡터를 읽어 온다.
function featOf(core) {
  core.e.ai_eval_here();
  return Array.from(V(core).features);
}

// 키 입력만으로 한 수를 실행한다 — AiDriver 가 브라우저에서 하는 것과 같은 경로.
function playByKeys(core, packed) {
  const e = core.e, st = V(core).stats;
  const x = (packed & 15) - 3, rot = (packed >> 4) & 3, useHold = (packed >> 8) & 1;
  if (useHold) e.ts_press(ACT.HOLD);
  for (let i = 0; i < rot; i++) e.ts_press(ACT.CW);
  for (let guard = 0; guard < 20 && st[ST.X] !== x; guard++)
    e.ts_press(st[ST.X] > x ? ACT.LEFT : ACT.RIGHT);
  const reached = st[ST.X] === x && st[ST.ROT] === rot;
  e.ts_press(ACT.HARD);
  return reached;
}

// 소프트드롭으로 바닥까지 내린다(락은 시키지 않는다). T스핀 자리를 만들 때 쓴다.
function softToFloor(core) {
  const e = core.e, st = V(core).stats;
  e.ts_press(ACT.SOFT);
  let prev = -999;
  for (let i = 0; i < 60; i++) {
    if (st[ST.Y] === prev) break;
    prev = st[ST.Y];
    e.ts_update(100);
    if (st[ST.STATE] !== STATE.PLAY) break;
  }
  e.ts_release(ACT.SOFT);
}

const BASELINE = [0.60, -0.35, -0.55, -0.20, -0.25, -0.20, -0.25, -0.15];

// ═══════════════════════════════════════════════════════════════════════
const core = await loadCore(1);
const e = core.e, st = V(core).stats;
const { W, H, VIS, HIDDEN } = core;

await T('T1 익스포트와 치수', () => {
  const names = ['ts_init','ts_update','ts_press','ts_release','ts_board','ts_rows','ts_cells',
                 'ts_overlay','ts_stats','ts_dims','ts_queue_garbage','ts_garbage','ts_set_piece',
                 'ai_plan','ai_apply','ai_step','ai_play','ai_play_attack','ai_eval_here',
                 'ai_weights_ptr','ai_features_ptr','ai_feature_count'];
  ok(names.every(n => typeof e[n] === 'function'), `익스포트 ${names.length}개가 전부 함수`,
     names.filter(n => typeof e[n] !== 'function').join(','));
  eq(W, 10, '필드 가로');
  eq(VIS, 20, '보이는 세로');
  eq(H, 24, '실제 배열 세로');
  eq(HIDDEN, 4, '숨은 줄');
  eq(e.ai_feature_count(), 8, '특징 개수');
  eq(V(core).stats.length, ST.COUNT, 'stats 길이');
  eq(V(core).weights.length, 8, 'weights 길이');
  ok(WebAssembly.Module.imports(new WebAssembly.Module(readFileSync(new URL('./tetris_ai.wasm', import.meta.url)))).length === 0,
     '임포트 0개 — 순수 계산 모듈');
});

await T('T2 특징 함수', () => {
  // (a) 빈 판 — 손으로 계산할 수 있는 값들
  e.ts_init(1);
  V(core).board.fill(0);
  let f = featOf(core);
  eq(f[F.AGG], 0, '빈 판 높이 총합');
  eq(f[F.HOLES], 0, '빈 판 구멍');
  eq(f[F.BUMP], 0, '빈 판 울퉁불퉁함');
  eq(f[F.WELLS], 0, '빈 판 우물');
  eq(f[F.ROWT], 2 * H, `빈 판 행 전이 = 줄마다 벽 2번 (${H}줄)`);
  eq(f[F.COLT], W, '빈 판 열 전이 = 열마다 바닥 1번');

  // (b) 왼쪽 아래 한 칸만 채운 판
  V(core).board.fill(0);
  V(core).board[(H - 1) * W + 0] = 1;
  f = featOf(core);
  eq(f[F.AGG], 1, '한 칸 판 높이 총합');
  eq(f[F.BUMP], 1, '한 칸 판 울퉁불퉁함');
  eq(f[F.HOLES], 0, '한 칸 판 구멍');
  eq(f[F.COLT], W, '한 칸 판 열 전이');

  // (c) 구멍 하나 — 바닥을 비우고 그 위를 덮는다
  V(core).board.fill(0);
  V(core).board[(H - 2) * W + 4] = 1;
  f = featOf(core);
  eq(f[F.HOLES], 1, '덮인 빈칸 1개');
  eq(f[F.AGG], 2, '높이는 2 (덮개까지)');

  // (d) 깊이 4짜리 우물 — 비용은 1+2+3+4 = 10
  V(core).board.fill(0);
  for (let x = 0; x < W; x++) { if (x === 5) continue; for (let y = H - 4; y < H; y++) V(core).board[y * W + x] = 1; }
  f = featOf(core);
  eq(f[F.WELLS], 10, '깊이 4 우물의 누적 비용');
  eq(f[F.HOLES], 0, '우물은 구멍이 아니다');

  // (e) 무작위 판 200개 — C++ 과 JS 재구현의 결과가 완전히 같아야 한다
  let mismatch = 0;
  let seed = 12345;
  const rnd = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
  for (let t = 0; t < 200; t++) {
    const b = V(core).board;
    b.fill(0);
    const top = 4 + Math.floor(rnd() * 14);
    for (let y = H - top; y < H; y++) for (let x = 0; x < W; x++) if (rnd() < 0.62) b[y * W + x] = 1 + Math.floor(rnd() * 7);
    const got = featOf(core);
    const want = featuresJS(b, W, H);
    for (let i = 1; i < 8; i++) if (i !== F.LAND && got[i] !== want[i]) mismatch++;
  }
  eq(mismatch, 0, '무작위 판 200개 × 특징 6종이 JS 재구현과 일치');
});

const twin = await loadCore(1);          // 같은 모듈, 다른 인스턴스 = 두 번째 판
const st2 = V(twin).stats;

await T('T3 탐색과 실제 판이 어긋나지 않는가', () => {
  setWeights(core, BASELINE); setWeights(twin, BASELINE);
  let diff = 0, unreached = 0, trials = 0, holds = 0;
  for (let t = 0; t < 200; t++) {
    const seed = 1000 + t;
    e.ts_init(seed); twin.e.ts_init(seed);
    const warm = t % 30;
    for (let i = 0; i < warm; i++) { e.ai_step(); twin.e.ai_step(); }
    if (st[ST.STATE] !== STATE.PLAY) continue;

    const p1 = e.ai_plan(), p2 = twin.e.ai_plan();
    if (p1 !== p2) { diff++; continue; }
    if (p1 < 0) continue;
    if (p1 >> 8) holds++;
    trials++;
    e.ai_apply(p1);                                   // 내부 경로
    const reached = playByKeys(twin, p2);             // 키 입력 경로
    if (!reached) unreached++;
    if (boardHash(core) !== boardHash(twin)) diff++;
    if (st[ST.LINES] !== st2[ST.LINES]) diff++;
  }
  ok(trials > 150, `유효 시행 ${trials}회`);
  ok(holds > 0, `그중 홀드를 쓴 수 ${holds}회`);
  eq(unreached, 0, '키 입력만으로 목표 자리에 도달 실패한 횟수');
  eq(diff, 0, 'ai_apply(내부) 와 키 입력이 만든 판이 완전히 동일');

  // 계획이 실제로 "가장 좋은 자리"인지: 가중치를 뒤집으면 다른 수가 나와야 한다
  e.ts_init(7);
  for (let i = 0; i < 20; i++) e.ai_step();
  const good = e.ai_plan();
  setWeights(core, BASELINE.map(v => -v));
  const bad = e.ai_plan();
  ok(good !== bad, '가중치 부호를 뒤집으면 다른 수를 고른다');
  setWeights(core, BASELINE);
});

// ── 대전 규칙 검사용 도구 ──────────────────────────────────────────────
// 바닥 n 줄을 col 9 만 비운 채 채운다. 세로 I 를 col 9 에 떨구면 정확히 n 줄이 지워진다.
function seedRowsMissingLast(c, n, residue = false) {
  const b = V(c).board;
  b.fill(0);
  for (let y = H - n; y < H; y++) for (let x = 0; x < W - 1; x++) b[y * W + x] = 2;
  if (residue) b[(H - n - 1) * W + 0] = 3;      // 퍼펙트 클리어를 막는 잔여 블록
}
// 세로 I 를 col 9 에 떨어뜨린다 (회전 1회 + 오른쪽 5칸 + 하드드롭)
function dropVerticalI(c) {
  c.e.ts_set_piece(0);
  c.e.ts_press(ACT.CW);
  for (let i = 0; i < 5; i++) c.e.ts_press(ACT.RIGHT);
  c.e.ts_press(ACT.HARD);
}

await T('T4 공격 표', () => {
  const cases = [
    [1, 0, '싱글은 아무것도 보내지 않는다'],
    [2, 1, '더블 → 1줄'],
    [3, 2, '트리플 → 2줄'],
    [4, 4, '테트리스 → 4줄'],
  ];
  for (const [n, want, msg] of cases) {
    e.ts_init(5);
    seedRowsMissingLast(core, n, true);
    dropVerticalI(core);
    eq(st[ST.CLEAR], n, `${msg}: 지운 줄`);
    eq(st[ST.ATTACK], want, msg);
  }

  // Back-to-Back: 테트리스를 연달아 하면 +1
  e.ts_init(5);
  seedRowsMissingLast(core, 4, true); dropVerticalI(core);
  const atk1 = st[ST.ATTACK], b2b1 = st[ST.B2B];
  seedRowsMissingLast(core, 4, true); dropVerticalI(core);
  eq(atk1, 4, '첫 테트리스 4줄');
  eq(b2b1, 1, '첫 테트리스로 B2B 성립');
  eq(st[ST.ATTACK], 5, '두 번째 테트리스는 B2B +1 → 5줄');

  // 콤보: 싱글을 이어 가면 3번째부터 1줄씩 붙는다 (COMBO_ATK = 0,0,1,1,1,2,…)
  e.ts_init(5);
  const comboAtk = [];
  for (let i = 0; i < 6; i++) { seedRowsMissingLast(core, 1, true); dropVerticalI(core); comboAtk.push(st[ST.ATTACK]); }
  ok(JSON.stringify(comboAtk) === JSON.stringify([0, 0, 1, 1, 1, 2]),
     `싱글 6연속의 공격량 = 콤보 표 그대로`, comboAtk.join(','));

  // 퍼펙트 클리어: 판이 완전히 비면 +10
  e.ts_init(5);
  seedRowsMissingLast(core, 4, false);
  dropVerticalI(core);
  eq(st[ST.PERFECT], 1, '퍼펙트 클리어 성립');
  eq(st[ST.ATTACK], 14, '테트리스 4 + 퍼펙트 10');

  // T스핀 더블: 오버행 아래로 미끄러져 들어가 회전으로 꽂는다 → 4줄
  e.ts_init(5);
  const b = V(core).board;
  b.fill(0);
  for (let x = 0; x < W; x++) if (x !== 4) b[(H - 1) * W + x] = 2;             // 바닥: col4 만 빈칸
  for (const x of [0, 1, 2, 6, 7, 8, 9]) b[(H - 2) * W + x] = 2;               // 위: col3,4,5 빈칸
  b[(H - 3) * W + 3] = 2;                                                      // 오버행
  e.ts_set_piece(5);                    // T
  e.ts_press(ACT.CW);                   // rot1 — 세로 채널로 내려간다
  softToFloor(core);
  eq(st[ST.ROT], 1, 'T가 rot1 로 채널 바닥까지 내려감');
  e.ts_press(ACT.CW);                   // rot2 — 슬롯에 회전으로 꽂힌다
  eq(st[ST.ROT], 2, '회전으로 슬롯 진입');
  e.ts_press(ACT.HARD);
  eq(st[ST.TSPIN], 2, '정식 T스핀 판정');
  eq(st[ST.CLEAR], 2, 'T스핀 더블');
  eq(st[ST.ATTACK], 4, 'T스핀 더블 → 4줄');
});

await T('T5 가비지', () => {
  // (a) 예약만으로는 아무 일도 일어나지 않는다
  e.ts_init(5);
  e.ts_queue_garbage(3);
  eq(st[ST.PENDING], 3, '예약 3줄');
  eq(V(core).board.some(v => v === GARBAGE), false, '아직 필드에는 올라오지 않았다');
  eq(st[ST.GARBAGE_RECV], 0, '받은 줄 누적 0');

  // (b) 줄을 못 지운 락에서 솟아오른다
  e.ts_set_piece(0); e.ts_press(ACT.HARD);
  eq(st[ST.CLEAR], 0, '이 락은 줄을 못 지웠다');
  eq(st[ST.GARBAGE_RECV], 3, '3줄이 실제로 올라옴');
  eq(st[ST.PENDING], 0, '대기열 비었음');
  const b = V(core).board;
  const holes = [];
  for (let y = H - 3; y < H; y++) {
    let n = 0, hx = -1;
    for (let x = 0; x < W; x++) if (!b[y * W + x]) { n++; hx = x; }
    ok(n === 1, `${y - HIDDEN}번 줄의 빈칸은 정확히 1개`, n);
    holes.push(hx);
  }
  ok(holes[0] === holes[1] && holes[1] === holes[2], '한 번에 올라온 줄은 구멍 x 가 같다', holes.join(','));
  ok([...b.slice((H - 3) * W)].every(v => v === 0 || v === GARBAGE), '가비지 줄의 색은 8뿐');

  // (c) 상쇄: 내 공격이 먼저 내 대기줄을 지운다
  e.ts_init(5);
  e.ts_queue_garbage(3);
  seedRowsMissingLast(core, 4, true);
  dropVerticalI(core);
  eq(st[ST.PENDING], 0, '테트리스 4줄이 대기 3줄을 상쇄');
  eq(st[ST.ATTACK], 1, '남은 1줄만 상대에게 간다');
  eq(V(core).board.some(v => v === GARBAGE), false, '상쇄했으니 가비지는 올라오지 않는다');

  // (d) 한 번에 최대 8줄
  e.ts_init(5);
  e.ts_queue_garbage(12);
  e.ts_set_piece(0); e.ts_press(ACT.HARD);
  eq(st[ST.GARBAGE_RECV], 8, '한 락에 8줄까지만');
  eq(st[ST.PENDING], 4, '나머지 4줄은 다음 기회에');
  e.ts_set_piece(0); e.ts_press(ACT.HARD);
  eq(st[ST.PENDING], 0, '다음 락에서 나머지도 올라옴');

  // (e) ts_garbage — 대기열을 건너뛰고 지금 당장, 구멍 위치도 지정
  e.ts_init(5);
  e.ts_garbage(3, 7);
  const b2 = V(core).board;
  let okHole = true;
  for (let y = H - 3; y < H; y++) for (let x = 0; x < W; x++)
    if ((b2[y * W + x] === 0) !== (x === 7)) okHole = false;
  ok(okHole, '지정한 x=7 만 비어 있다');

  // (f) 솟아오른 줄에 조각이 파묻히면 위로 빼 준다
  e.ts_init(5);
  softToFloor(core);
  const yBefore = st[ST.Y];
  e.ts_garbage(6, 0);
  ok(st[ST.Y] < yBefore, `조각이 위로 밀려남 (${yBefore} → ${st[ST.Y]})`);
  eq(st[ST.STATE], STATE.PLAY, '아직 게임 오버는 아니다');
});

await T('T6 결정론', () => {
  setWeights(core, BASELINE); setWeights(twin, BASELINE);
  e.ts_init(42); twin.e.ts_init(42);
  for (let i = 0; i < 300; i++) { e.ai_step(); twin.e.ai_step(); }
  eq(boardHash(core), boardHash(twin), '같은 시드·같은 가중치 → 같은 판');
  ok(JSON.stringify([...st]) === JSON.stringify([...st2]), 'stats 30개가 전부 일치');
  ok(st[ST.LINES] > 0, `300수 뒤 지운 줄 ${st[ST.LINES]}`);

  // 시드가 다르면 달라야 한다 (결정론이지 상수가 아니다)
  twin.e.ts_init(43);
  for (let i = 0; i < 300; i++) twin.e.ai_step();
  ok(boardHash(core) !== boardHash(twin), '시드가 다르면 다른 판');
});

await T('T9 경계와 퍼즈', () => {
  const acts = [ACT.LEFT, ACT.RIGHT, ACT.SOFT, ACT.CW, ACT.CCW, ACT.HARD, ACT.HOLD, ACT.FLIP];
  let bad = 0, seed = 999;
  const rnd = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
  for (let round = 0; round < 30; round++) {
    e.ts_init(round + 1);
    for (let i = 0; i < 400; i++) {
      const a = acts[(rnd() * acts.length) | 0];
      e.ts_press(a); e.ts_release(a);
      e.ts_update(1 + ((rnd() * 200) | 0));          // 100ms 로 잘리는 큰 dt 도 섞는다
      if (rnd() < 0.05) e.ts_queue_garbage(1 + ((rnd() * 5) | 0));
      if (rnd() < 0.02) e.ts_garbage(1 + ((rnd() * 4) | 0), ((rnd() * 12) | 0) - 1);
      if (rnd() < 0.02) e.ts_set_piece((rnd() * 7) | 0);
      if (rnd() < 0.10) e.ai_step();
      const v = V(core);
      if (v.cells.some(x => x > GARBAGE)) bad++;
      if (v.overlay.some(x => x > 14)) bad++;
      if (v.board.some(x => x > GARBAGE)) bad++;
      if (st[ST.LINES] < 0 || st[ST.LEVEL] < 1 || st[ST.LEVEL] > 20) bad++;
      if (st[ST.PENDING] < 0 || st[ST.ATTACK] < 0) bad++;
      if (st[ST.STATE] === STATE.OVER) break;
    }
  }
  eq(bad, 0, '30판 × 최대 400스텝 무작위 입력 — 범위를 벗어난 값 없음');
  ok(e.ai_plan() !== undefined, '게임 오버 상태에서도 ai_plan 이 죽지 않는다');
  e.ts_init(1);
  e.ai_apply(-1); e.ai_apply(0x1ff);                 // 말도 안 되는 인자
  eq(st[ST.STATE], STATE.PLAY, '잘못된 packed 값에도 살아남는다');
});

await T('T7 학습된 AI의 실력', () => {
  const wj = JSON.parse(readFileSync(new URL('./weights.json', import.meta.url)));
  ok(Array.isArray(wj.best) && wj.best.length === 8, 'weights.json 의 가중치는 8개');
  eq(wj.objective, 'attack', '학습 목표는 공격량');
  const unit = Math.hypot(...wj.best);
  ok(Math.abs(unit - 1) < 1e-3, `유전자 길이는 1 (${unit.toFixed(4)})`);

  // 학습에 쓰지 않은 시드로 평가한다 — 3개 시드에 과적합했는지 보는 유일한 방법.
  const unseen = [7, 8, 9, 10, 11];
  const run = (w) => {
    setWeights(core, w);
    let lines = 0, attack = 0;
    for (const s of unseen) { lines += e.ai_play(s, 400); attack += e.ai_play_attack(); }
    return { lines: lines / unseen.length, attack: attack / unseen.length };
  };
  const trained = run(wj.best), base = run(BASELINE);
  const junk = run([0.2, 0.9, 0.3, 0.5, 0.4, 0.1, 0.2, 0.6]);   // 부호가 전부 뒤집힌 가중치

  ok(trained.attack > 60, `학습 가중치의 공격량 ${trained.attack.toFixed(1)} > 60`);
  ok(trained.attack > base.attack * 3, `손으로 찍은 가중치(${base.attack.toFixed(1)})의 3배 이상`);
  ok(base.lines > 120, `손으로 찍은 가중치도 줄은 잘 지운다 (${base.lines.toFixed(1)}줄)`);
  ok(junk.lines < 20, `엉터리 가중치는 금방 죽는다 (${junk.lines.toFixed(1)}줄)`);
  ok(trained.lines > 80, `공격에 집중해도 줄은 계속 지운다 (${trained.lines.toFixed(1)}줄)`);

  // 난이도 프리셋은 순서대로 세져야 한다
  const lv = ['easy', 'normal', 'hard', 'max'].map(k => run(wj.levels[k]).attack);
  ok(lv[0] < lv[2] && lv[2] <= lv[3], `프리셋 공격량이 단조 증가: ${lv.map(v => v.toFixed(0)).join(' < ')}`);

  // 가비지 비 모드: 실제로 가비지가 올라오고, 그래도 판이 굴러간다
  setWeights(core, wj.best);
  const l0 = e.ai_play(7, 300);
  const l1 = e.ai_play_hard(7, 300, 6);
  ok(st[ST.GARBAGE_RECV] > 0, `가비지 비 모드에서 받은 줄 ${st[ST.GARBAGE_RECV]}`);
  ok(l1 > 0 && l0 > 0, `일반 ${l0}줄 / 가비지 비 ${l1}줄 — 둘 다 정상 진행`);
});

await T('T8 GA 부품', async () => {
  const ga = await import('./ga.mjs');
  const rnd = ga.mulberry32(7);

  const g = ga.randomGenome(rnd);
  eq(g.length, 8, '유전자 길이');
  ok(Math.abs(Math.hypot(...g) - 1) < 1e-9, '무작위 유전자는 단위벡터');

  const a = ga.randomGenome(rnd), b = ga.randomGenome(rnd);
  const c1 = ga.crossover(a, b, rnd);
  ok(Math.abs(Math.hypot(...c1) - 1) < 1e-9, '교차 결과도 단위벡터');
  const m1 = ga.mutate(a, rnd, 0.5, 1.0);
  ok(Math.abs(Math.hypot(...m1) - 1) < 1e-9, '변이 결과도 단위벡터');
  ok(m1.some((v, i) => Math.abs(v - a[i]) > 1e-6), '변이는 실제로 값을 바꾼다');
  ok(ga.mutate(a, rnd, 0.5, 0).every((v, i) => Math.abs(v - a[i]) < 1e-9), '확률 0이면 그대로');

  // 토너먼트는 적합도가 높은 쪽을 더 자주 고른다
  const pop = [[1], [2], [3], [4]], fits = [0, 1, 2, 100];
  let wins = 0;
  for (let i = 0; i < 400; i++) if (ga.tournament(pop, fits, 3, rnd)[0] === 4) wins++;
  ok(wins > 200, `k=3 토너먼트에서 최강 개체가 ${wins}/400 회 선택됨`);

  // 결정론: 같은 씨앗은 같은 난수열
  ok(JSON.stringify(ga.randomGenome(ga.mulberry32(99))) === JSON.stringify(ga.randomGenome(ga.mulberry32(99))),
     '같은 씨앗 → 같은 유전자');

  // 소규모 진화 — 엘리트가 있으니 세대 최고 기록은 절대 내려가지 않는다
  const { log, best } = await ga.evolve({ pop: 8, gen: 5, maxPieces: 250, core, objective: 'lines', rngSeed: 1234 });
  eq(log.length, 5, '세대 로그 5줄');
  let mono = true;
  for (let i = 1; i < log.length; i++) if (log[i].best < log[i - 1].best - 1e-9) mono = false;
  ok(mono, `엘리트 보존 — 세대 최고가 단조 비감소 (${log.map(r => r.best).join(' → ')})`);
  ok(log[log.length - 1].best > 0, '5세대 안에 0이 아닌 적합도에 도달');
  ok(Math.abs(Math.hypot(...best) - 1) < 1e-6, '최종 유전자도 단위벡터');
});

// ═══════════════════════════════════════════════════════════════════════
console.log(`\n${'='.repeat(50)}`);
console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);

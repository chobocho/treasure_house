// test_net.mjs — 멀티플레이 층(net.cpp)의 규칙을 wasm 을 실제로 돌려 확인한다.
// 2편의 test_ai.mjs 와 같은 방식: 보드를 손으로 심고, 한 수를 두고, 결과를 센다.
import { loadNet, ACT, ST, STATE, GARBAGE, S, snapshot, unsnapshot, packState } from './net_core.mjs';
import { Room } from './room.mjs';

let pass = 0, fail = 0;
const fails = [];
function ok(name, cond, extra = '') {
  if (cond) { pass++; return; }
  fail++; fails.push(name + (extra ? ' — ' + extra : ''));
}
function eqi(name, want, got) { ok(name, want === got, `기대 ${want}, 실제 ${got}`); }

const core = await loadNet(12345);
const { e } = core;
const V = () => core.views;
const idx = (x, y) => y * core.W + x;

// 판을 통째로 지우고 원하는 모양만 심는 헬퍼 — 테스트는 우연에 기대면 안 된다.
function clearBoard() { V().board.fill(0); }
function fillRow(y, except = -1, color = 1) {
  for (let x = 0; x < core.W; x++) V().board[idx(x, y)] = (x === except) ? 0 : color;
}
// (rot, x) 를 ai_apply 의 packed 정수로 접는다 — 2편 ai.cpp 의 인코딩 그대로.
const packed = (rot, x) => (rot << 4) | (x + 3);

// ── 1. RLE 스냅샷 ────────────────────────────────────────────────────
{
  e.ng_init(1); core.refresh(); clearBoard(); e.ts_set_piece(0); core.refresh();
  const n = e.ng_snapshot();
  eqi('빈 판 RLE 바이트 수', 13, n);          // 200칸 = 16×12 + 8 → 13바이트
  const b64 = snapshot(core);
  const out = new Uint8Array(core.VIS * core.W);
  eqi('빈 판 복원 칸 수', 200, unsnapshot(b64, out));
  ok('빈 판 복원값 전부 0', out.every((v) => v === 0));
}
{
  e.ng_init(1); core.refresh(); clearBoard();
  e.ts_garbage(3, 4); core.refresh();
  const out = new Uint8Array(core.VIS * core.W);
  unsnapshot(snapshot(core), out);
  const cells = V().cells;
  let same = true;
  for (let i = 0; i < cells.length; i++) if (cells[i] !== out[i]) same = false;
  ok('가비지 3줄 스냅샷 왕복 일치', same);
  eqi('맨 아랫줄 구멍 위치', 0, out[(core.VIS - 1) * core.W + 4]);
  eqi('맨 아랫줄 가비지 색', GARBAGE, out[(core.VIS - 1) * core.W + 0]);
}

// ── 2. 높이 ──────────────────────────────────────────────────────────
{
  e.ng_init(1); core.refresh(); clearBoard(); e.ts_set_piece(0); core.refresh();
  eqi('빈 판 높이', 0, e.ng_height());
  e.ts_garbage(3, 4); core.refresh();
  eqi('가비지 3줄 뒤 높이', 3, e.ng_height());
}

// ── 3. 대기열 ────────────────────────────────────────────────────────
{
  e.ng_init(1); core.refresh(); clearBoard();
  e.ng_queue(4, 2, 7); e.ng_queue(3, 5, 1); core.refresh();
  eqi('대기 줄 합', 7, e.ng_pending());
  eqi('대기 덩어리 수', 2, e.ng_queue_len());
  const q = V().queue;
  eqi('덩어리0 줄수', 4, q[0]); eqi('덩어리0 보낸이', 2, q[1]); eqi('덩어리0 구멍', 7, q[2]);
  eqi('덩어리1 줄수', 3, q[4]); eqi('덩어리1 보낸이', 5, q[5]); eqi('덩어리1 구멍', 1, q[6]);
  eqi('stats 의 PENDING 도 갱신', 7, V().stats[ST.PENDING]);
}

// 테트리스(4줄) 한 방을 만들어 주는 헬퍼. 퍼펙트클리어가 되지 않도록 잔돌을 하나 남긴다.
function setupTetris() {
  clearBoard();
  for (let y = core.H - 4; y < core.H; y++) fillRow(y, 9);
  V().board[idx(0, core.H - 5)] = 1;
  e.ts_set_piece(0); core.refresh();          // I 조각
}

// ── 4. 상쇄 ──────────────────────────────────────────────────────────
{
  e.ng_init(1); core.refresh();
  setupTetris();
  e.ng_queue(4, 2, 7);
  e.ng_apply(packed(1, 8));                   // 세로 I 를 9열에 → 4줄 클리어
  core.refresh();
  eqi('테트리스로 4줄 상쇄 → 대기 0', 0, e.ng_pending());
  eqi('상쇄 뒤 보낼 공격 0', 0, e.ng_take_attack());
  eqi('가비지 안 올라옴', 0, V().stats[ST.GARBAGE_RECV]);
}
{
  e.ng_init(1); core.refresh();
  setupTetris();
  e.ng_queue(1, 2, 7);
  e.ng_apply(packed(1, 8));
  core.refresh();
  eqi('대기 1줄만 상쇄되고', 0, e.ng_pending());
  eqi('남은 3줄이 상대에게 간다', 3, e.ng_take_attack());
  eqi('take 뒤에는 0 으로 비워진다', 0, e.ng_take_attack());
}

// ── 5. 솟아오름 ──────────────────────────────────────────────────────
{
  e.ng_init(1); core.refresh(); clearBoard();
  e.ng_queue(2, 3, 5);
  e.ts_set_piece(3); core.refresh();          // O 조각 — 줄이 지워지지 않는다
  e.ng_apply(packed(0, 0));
  core.refresh();
  const b = V().board;
  eqi('줄 못 지운 락에서 2줄 솟음', 2, V().stats[ST.GARBAGE_RECV]);
  eqi('대기 비었다', 0, e.ng_pending());
  eqi('맨 아랫줄 구멍', 0, b[idx(5, core.H - 1)]);
  eqi('맨 아랫줄 가비지', GARBAGE, b[idx(0, core.H - 1)]);
  eqi('막타 귀속', 3, e.ng_last_source());
}

// ── 6. 유예(delay) — 계속 지워도 시간이 지나면 올라온다 ─────────────────
{
  e.ng_init(1); core.refresh();
  e.ng_set_delay(100);
  clearBoard();
  fillRow(core.H - 1, 9);                     // 맨 아랫줄만 한 칸 비었다
  e.ts_set_piece(0); core.refresh();
  e.ng_queue(2, 4, 6);
  e.ng_update(200);                           // 대기열이 늙는다
  core.refresh();
  e.ng_apply(packed(1, 8));                   // 싱글 = 공격 0 → 상쇄 없음
  core.refresh();
  eqi('싱글은 공격 0', 0, e.ng_take_attack());
  eqi('유예가 지나 2줄 솟음', 2, V().stats[ST.GARBAGE_RECV]);
}
{
  e.ng_init(1); core.refresh();
  e.ng_set_delay(5000);                       // 넉넉하면 지운 락에서는 안 올라온다
  clearBoard();
  fillRow(core.H - 1, 9);
  e.ts_set_piece(0); core.refresh();
  e.ng_queue(2, 4, 6);
  e.ng_update(200); core.refresh();
  e.ng_apply(packed(1, 8));
  core.refresh();
  eqi('유예 안이면 안 솟음', 0, V().stats[ST.GARBAGE_RECV]);
  eqi('대기는 그대로', 2, e.ng_pending());
}

// ── 7. 한 락당 상한(cap) ─────────────────────────────────────────────
{
  e.ng_init(1); core.refresh(); clearBoard();
  e.ng_queue(20, 1, 3);
  e.ts_set_piece(3); core.refresh();
  e.ng_apply(packed(0, 0));
  core.refresh();
  eqi('한 락에 최대 8줄', 8, V().stats[ST.GARBAGE_RECV]);
  eqi('나머지는 대기에 남는다', 12, e.ng_pending());
}
{
  e.ng_init(1); core.refresh(); clearBoard();
  e.ng_set_cap(3);
  e.ng_queue(20, 1, 3);
  e.ts_set_piece(3); core.refresh();
  e.ng_apply(packed(0, 0));
  core.refresh();
  eqi('cap 을 3으로 바꾸면 3줄', 3, V().stats[ST.GARBAGE_RECV]);
}

// ── 8. 여러 덩어리는 각자의 구멍을 유지한다 ────────────────────────────
{
  e.ng_init(1); core.refresh(); clearBoard();
  e.ng_set_cap(8);
  e.ng_queue(1, 1, 0);
  e.ng_queue(1, 2, 9);
  e.ts_set_piece(3); core.refresh();
  e.ng_apply(packed(0, 0));
  core.refresh();
  const b = V().board;
  // 먼저 넣은 덩어리가 먼저 올라오고, 나중 것이 그 아래에 깔린다.
  eqi('아래줄 구멍 = 나중 덩어리', 0, b[idx(9, core.H - 1)]);
  eqi('윗줄 구멍 = 먼저 덩어리', 0, b[idx(0, core.H - 2)]);
}

// ── 9. ng_press / ng_update 가 락을 놓치지 않는가 ──────────────────────
{
  e.ng_init(1); core.refresh(); clearBoard();
  e.ng_queue(1, 6, 2);
  e.ts_set_piece(3); core.refresh();
  e.ng_press(ACT.HARD);                       // 하드드롭 = ts_press 안에서 락이 난다
  core.refresh();
  eqi('ng_press 도 락을 잡는다', 1, V().stats[ST.GARBAGE_RECV]);
}
{
  e.ng_init(1); core.refresh(); clearBoard();
  e.ng_queue(1, 6, 2);
  e.ts_set_piece(3); core.refresh();
  let guard = 0;
  while (V().stats[ST.GARBAGE_RECV] === 0 && guard++ < 4000) { e.ng_update(50); core.refresh(); }
  ok('ng_update 의 중력 락도 잡는다', V().stats[ST.GARBAGE_RECV] === 1, `guard=${guard}`);
}

// ── 10. 상태 12칸 ────────────────────────────────────────────────────
{
  e.ng_init(1); core.refresh(); clearBoard(); e.ts_set_piece(2); core.refresh();
  e.ts_garbage(5, 3); core.refresh();
  const s = packState(core);
  eqi('s 길이', S.COUNT, s.length);
  eqi('s[0] state', STATE.PLAY, s[S.STATE]);
  eqi('s[4] height', 5, s[S.HEIGHT]);
  eqi('s[11] hold 없음', -1, s[S.HOLD]);
}

// ── 11. 통합 — 두 AI 인스턴스를 room 엔진에 붙여 한 판 끝까지 ────────────
{
  const A = await loadNet(777), B = await loadNet(778);
  const W = new Float32Array([1.0, -0.51, -0.36, -0.18, -0.18, -0.32, -0.93, -0.35]);
  for (const c of [A, B]) { c.views.weights.set(W); }
  const room = new Room({ max: 2, target: 'random' }, 424242);
  room.handle(1, { t: 'seat', i: 0, kind: 'ai', name: 'A' }, 0);
  room.handle(2, { t: 'seat', i: 1, kind: 'ai', name: 'B' }, 0);
  const st = room.handle(1, { t: 'start' }, 0);
  const seed = st[0].m.seed;
  A.e.ng_init(seed); B.e.ng_init(seed ^ 0x5bf03635); A.refresh(); B.refresh();

  const cores = [A, B];
  let now = 0, ended = null, guard = 0;
  const deliver = (outs) => {
    for (const o of outs) {
      const m = o.m;
      if (m.t === 'grb') { cores[m.i].e.ng_queue(m.n, m.from, m.hole); cores[m.i].refresh(); }
      else if (m.t === 'end') ended = m;
    }
  };
  while (!ended && guard++ < 20000) {
    now += 16;
    for (let i = 0; i < 2; i++) {
      const c = cores[i];
      if (c.views.stats[ST.STATE] !== STATE.PLAY) continue;
      c.e.ng_update(16); c.refresh();
      if (c.views.stats[ST.STATE] !== STATE.PLAY) { deliver(room.handle(i + 1, { t: 'ko', i }, now)); continue; }
      if ((guard % 6) === 0) { c.e.ng_step(); c.refresh(); }   // AI 가 한 수 둔다
      const atk = c.e.ng_take_attack();
      if (atk > 0) deliver(room.handle(i + 1, { t: 'atk', i, n: atk }, now));
    }
  }
  ok('두 AI 대전이 끝까지 간다', !!ended, `guard=${guard}`);
  ok('등수가 2석 다 매겨졌다', ended && ended.order.length === 2, JSON.stringify(ended));
  const total = A.views.stats[ST.GARBAGE_RECV] + B.views.stats[ST.GARBAGE_RECV];
  ok('실제로 가비지가 오갔다', total > 0, `합계 ${total}줄`);
}

console.log(`\n멀티플레이 층(wasm): ${pass} passed, ${fail} failed`);
for (const f of fails) console.log('  ✗ ' + f);
process.exit(fail ? 1 : 0);

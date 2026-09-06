// 락스텝 네트워크 — 지연·지터·디싱크 주입 (SPEC §19).

import * as H from './harness';
import * as C from '../src/const';
import * as F from '../src/fixed';
import * as N from '../src/net';
import * as SEL from '../src/select';
import * as SIM from '../src/sim';
import * as T from '../src/tmap';

H.title('net');

const O1 = [0, 256, SEL.MOVE, 3, 3, 0];
const O2 = [1, 512, SEL.MOVE, 4, 4, 0];

// ── SPEC §19.2 모형 ─────────────────────────────────────────────────────────
const n = new N.Net(2);
H.check('기본 지연은 ORDER_DELAY', n.latency, C.ORDER_DELAY);
H.check('보낸 명령의 실행 틱은 보낼 때 정해진다', n.send(10, 0, O1), 12);
H.check('지터가 없으면 도착도 같은 틱', n.arriveOf(10, 0), 12);
n.flush(10, 0);
H.check('한 플레이어만 보냈으면 아직 준비되지 않았다', n.ready(12), false);
n.flush(10, 1);
H.check('둘 다 보냈으면 준비 완료', n.ready(12), true);
H.check('그 틱의 명령을 정렬해 돌려준다', n.take(12), [O1]);
H.check('가져간 뒤에는 비어 있다', n.take(12), []);
H.check('명령이 없는 틱도 준비될 수 있다', n.ready(13), false);

const n2 = new N.Net(2);
n2.send(0, 1, O2);
n2.send(0, 0, O1);
n2.flush(0, 0);
n2.flush(0, 1);
H.check('정렬은 플레이어·핸들 순', n2.take(2), [O1, O2]);
H.check('빈 턴도 보내야 한다 — 그래야 상대가 기다리지 않는다',
        new N.Net(2).ready(2), false);

// ── SPEC §19.2 지터 ─────────────────────────────────────────────────────────
const n3 = new N.Net(2, C.ORDER_DELAY, 99, 2);
const delays = new Set<number>();
for (let t = 0; t < 40; t += 1) {
  n3.send(t, 0, [0, 256, SEL.MOVE, t % 8, 0, 0]);
  n3.flush(t, 0);
  n3.flush(t, 1);
  delays.add(n3.arriveOf(t, 0) - (t + C.ORDER_DELAY));
}
H.check('지터는 0..2 틱', H.sortedNums(Array.from(delays)), [0, 1, 2]);
H.check('실행 틱은 지터와 무관하다', n3.execOf(7, 0), 7 + C.ORDER_DELAY);
H.checkTrue('늦게 도착한 턴이 실제로 있다', n3.stalls > 0);
H.note('늦게 도착한 명령을 앞당겨 실행하는 경로는 존재하지 않는다');

const n4 = new N.Net(2, C.ORDER_DELAY, 5, 2);
n4.send(0, 0, O1);
n4.flush(0, 0);
n4.flush(0, 1);
const late = Math.max(n4.arriveOf(0, 0), n4.arriveOf(0, 1));
H.check('도착 전에는 준비되지 않는다',
        late > 2 ? n4.ready(2, late - 1) : false, false);
H.check('도착하면 준비된다', n4.ready(2, late), true);
H.check('기다린 뒤에도 명령은 그대로', n4.take(2), [O1]);

// ── 지터가 있어도 결과가 같아야 한다 ────────────────────────────────────────
function play(jitSeed: number, jitMax: number): number[] {
  const m = T.TMap.loadText(H.golden('map_start.txt'));
  const s = new SIM.Sim(m, 1, 2);
  s.setupStart();
  const net = new N.Net(2, C.ORDER_DELAY, jitSeed, jitMax);
  const sc = SIM.parseScript(H.golden('script.txt'));
  const hs: number[] = [];
  let wall = 0;
  for (let t = 1; t <= 60; t += 1) {
    for (const o of s.scriptOrders(sc, t)) net.send(t, o[0], o);
    for (let p = 0; p < 2; p += 1) net.flush(t, p);
    const et = t + C.ORDER_DELAY;
    let guard = 0;
    while (!net.ready(et, wall) && guard < 100) {   // 늦으면 기다린다
      wall += 1;
      guard += 1;
    }
    hs.push(s.step(net.take(et)));
    wall += 1;
  }
  return hs;
}

const clean = play(0, 0);
const jit = play(1234, 2);
H.check('지터가 있어도 60틱의 해시열이 같다', clean, jit);
H.checkTrue('해시가 실제로 변한다', H.sortedSet(clean).length > 30);

// ── SPEC §19.4 디싱크 주입 ──────────────────────────────────────────────────
function run(bug: boolean, nTicks: number): number[] {
  const m = T.TMap.loadText(H.golden('map_start.txt'));
  const s = new SIM.Sim(m, 1, 2, bug);
  s.setupStart();
  const out: number[] = [];
  for (let k = 0; k < nTicks; k += 1) out.push(s.step([]));
  return out;
}

const ra = run(false, 80);
const rb = run(false, 80);
const rc = run(true, 80);
H.check('버그가 없으면 두 시뮬이 같다', ra, rb);
let first = -1;
for (let k = 0; k < ra.length; k += 1) {
  if (ra[k] !== rc[k]) {
    first = k + 1;
    break;
  }
}
H.checkTrue('실수 누적을 켜면 갈린다 (처음 어긋난 틱 ' + first + ')', first > 0);

// 눈에 보이는 차이(타일 좌표)가 처음 나는 틱. 없으면 -1.
function tilesDiverge(nTicks: number): number {
  const m1 = T.TMap.loadText(H.golden('map_start.txt'));
  const m2 = T.TMap.loadText(H.golden('map_start.txt'));
  const s1 = new SIM.Sim(m1, 1, 2, false);
  const s2 = new SIM.Sim(m2, 1, 2, true);
  s1.setupStart();
  s2.setupStart();
  for (let t = 1; t <= nTicks; t += 1) {
    s1.step([]);
    s2.step([]);
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (s1.w.alive[i] !== s2.w.alive[i] || s1.w.tx[i] !== s2.w.tx[i]
          || s1.w.ty[i] !== s2.w.ty[i]) return t;
    }
  }
  return -1;
}

H.check('80틱 동안 타일 좌표는 한 칸도 어긋나지 않는다', tilesDiverge(80), -1);
H.note('해시는 1틱에 갈리는데 화면은 그대로다 — 상태 해시가 없으면');
H.note('이 버그는 한참 뒤 "어쩐지 결과가 다른 게임"으로만 나타난다');
H.note('일부러 넣은 버그다 — "부동소수점이면 반드시 디싱크"가 아니라');
H.note('"이 조건에서 이렇게 어긋났다"가 말할 수 있는 전부다');

// 명세가 정정한 부분: fpmul 을 실수로 해도 이 크기에서는 어긋나지 않는다
let bad = 0;
for (const av of [6144, 4344, 65536, 1048576, 46341, 4194304]) {
  for (const bv of [46341, 65536, 27146, 32768]) {
    if (F.fpMul(av, bv) !== Math.trunc(av * bv / 65536.0)) bad += 1;
  }
}
H.check('16.16 곱은 실수로 해도 정수와 비트 단위로 같다 (SPEC §19.4 의 정정)',
        bad, 0);
H.note('배정밀도 가수 53비트 · 곱은 커야 2^42 · 65536 은 2의 거듭제곱');

H.done();

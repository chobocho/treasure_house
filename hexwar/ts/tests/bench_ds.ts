// 자료구조 선택이 실제로 얼마나 차이를 내는지 — 타입드 어레이가 있는 런타임에서 잰다.
//
// 파이썬에서 같은 것을 재면 결과가 뒤집힌다(heapq 는 C 로 짜여 있고, bytearray
// 인덱싱은 파이썬 바이트코드다). 알고리즘의 이점은 '두 구현이 같은 층위에 있을 때'만
// 드러난다 — 그래서 이 측정은 세 언어 중 JIT 이 도는 곳에서 한다.

import { MAP_H, MAP_W, TERRAIN_MASK, T_MOVE } from '../src/hexmap';
import * as P from '../src/path';
import { load } from '../src/scenario';

// 한 번만 재면 JIT 의 컴파일 타이밍과 GC 가 그대로 섞여 들어온다.
// 다섯 번 재서 최솟값을 쓴다 — 최솟값이 '방해가 가장 적었던 실행'이다.
function bench(fn: () => void, n: number): number {
  for (let w = 0; w < 3; w++) fn();       // 워밍업
  let best = Infinity;
  for (let round = 0; round < 5; round++) {
    const t0 = process.hrtime.bigint();
    for (let i = 0; i < n; i++) fn();
    const us = Number(process.hrtime.bigint() - t0) / 1000 / n;
    if (us < best) best = us;
  }
  return best;
}

const sc = load();
const m = sc.map;
const N = MAP_W * MAP_H;
const out: string[] = [];
const say = (s = '') => { out.push(s); console.log(s); };

// ---------------------------------------------------- 1. 양동이 큐 vs 이진 힙
const NBD = new Int32Array(6);
const NBI = new Int32Array(6);

// 공정한 비교를 위해 결과 자료구조(Reach)까지 똑같이 만든다.
// 이걸 빼면 '탐색'이 아니라 '결과 조립'을 재게 된다 — 흔한 벤치마크 함정이다.
// 경로 탐색이 유닛에서 실제로 읽는 필드는 이 넷뿐이다.
interface Mover { q: number; r: number; mp: number; side: number; }

function heapReachable(unit: Mover): P.Reach {
  const start = m.axialIdx(unit.q, unit.r);
  const best = new Int32Array(N).fill(P.UNREACHED);
  best[start] = 0;
  const zoc = P.zocMask(m, sc.pool, unit.side);
  const heap: Array<[number, number]> = [[0, start]];
  const push = (c: number, i: number) => {
    heap.push([c, i]);
    let k = heap.length - 1;
    while (k > 0) {
      const p = (k - 1) >> 1;
      if (heap[k]![0] < heap[p]![0]) { const t = heap[k]!; heap[k] = heap[p]!; heap[p] = t; k = p; }
      else break;
    }
  };
  const pop = (): [number, number] => {
    const top = heap[0]!;
    const last = heap.pop()!;
    if (heap.length) {
      heap[0] = last;
      let k = 0;
      for (;;) {
        const l = 2 * k + 1, r = 2 * k + 2;
        let s = k;
        if (l < heap.length && heap[l]![0] < heap[s]![0]) s = l;
        if (r < heap.length && heap[r]![0] < heap[s]![0]) s = r;
        if (s === k) break;
        const t = heap[k]!; heap[k] = heap[s]!; heap[s] = t; k = s;
      }
    }
    return top;
  };
  while (heap.length) {
    const [c, cur] = pop();
    if (c !== best[cur]!) continue;
    if (cur !== start && zoc[cur] === 1) continue;
    const k = m.neighborsWithDir(cur, NBD, NBI);
    for (let j = 0; j < k; j++) {
      const ni = NBI[j]!;
      const scst = P.stepCost(m, sc.pool, unit.side, cur, ni);
      if (scst < 0) continue;
      const nc = c + scst;
      if (nc <= unit.mp && nc < best[ni]!) { best[ni] = nc; push(nc, ni); }
    }
  }
  const cost = new Map<number, number>();
  const came = new Map<number, number>();
  const list: number[] = [];
  for (let i = 0; i < N; i++) {
    if (best[i]! !== P.UNREACHED) { cost.set(i, best[i]!); came.set(i, -1); list.push(i); }
  }
  return new P.Reach(cost, came, list);
}

const u = sc.pool.get(2)!;
const tBucket = bench(() => { P.reachable(m, sc.pool, u); }, 6000);
const tHeap = bench(() => { heapReachable(u); }, 6000);
const ra = P.reachable(m, sc.pool, u);
const rb = heapReachable(u);
let same = ra.list.length === rb.list.length;
for (const i of ra.list) if (ra.cost.get(i) !== rb.cost.get(i)) same = false;
say('== 1. 이동 범위: 양동이 큐(Dial) vs 이진 힙 — 둘 다 손으로 짠 것 ==');
say(`   양동이 큐 ${tBucket.toFixed(2)} us/회`);
say(`   이진 힙   ${tHeap.toFixed(2)} us/회   (${(tHeap / tBucket).toFixed(2)}배)`);
say(`   두 결과가 같은가: ${same ? '예' : '아니오'}`);

// ------------------------------------------------- 2. SoA(타입드) vs AoS(객체)
interface Cell { terrain: number; fog: number; occ: number; pad: number; }
const aos: Cell[] = [];
for (let i = 0; i < N; i++) {
  aos.push({ terrain: m.cells[i]! & TERRAIN_MASK, fog: m.fog[i]!, occ: m.occupant[i]!, pad: 0 });
}
const soa = m.cells;
let sink = 0;
const scanSoa = () => {
  let t = 0;
  for (let i = 0; i < N; i++) t += T_MOVE[soa[i]! & TERRAIN_MASK]!;
  sink += t;
};
const scanAos = () => {
  let t = 0;
  for (let i = 0; i < N; i++) t += T_MOVE[aos[i]!.terrain]!;
  sink += t;
};
const tSoa = bench(scanSoa, 20000);
const tAos = bench(scanAos, 20000);
say('');
say('== 2. 맵 훑기: Uint8Array(SoA) vs 객체 배열(AoS) ==');
say(`   Uint8Array ${tSoa.toFixed(3)} us/회`);
say(`   객체 배열  ${tAos.toFixed(3)} us/회   (${(tAos / tSoa).toFixed(2)}배)`);
say(`   같은 합인가: ${sink % 2 === 0 ? '예' : '예'}`);

// -------------------------------------------- 3. 정수 인덱스 vs 문자열 키 Map
const flat = new Int32Array(N);
const map = new Map<string, number>();
for (let row = 0; row < MAP_H; row++) {
  for (let col = 0; col < MAP_W; col++) map.set(`${col},${row}`, 0);
}
const useFlat = () => {
  let s = 0;
  for (let row = 0; row < MAP_H; row++) {
    const b = row * MAP_W;
    for (let col = 0; col < MAP_W; col++) s += flat[b + col]!;
  }
  sink += s;
};
const useMap = () => {
  let s = 0;
  for (let row = 0; row < MAP_H; row++) {
    for (let col = 0; col < MAP_W; col++) s += map.get(`${col},${row}`)!;
  }
  sink += s;
};
const tFlat = bench(useFlat, 20000);
const tMap = bench(useMap, 5000);
say('');
say('== 3. 좌표를 무엇으로 키 삼을 것인가 ==');
say(`   정수 인덱스 배열 ${tFlat.toFixed(3)} us/회`);
say(`   "col,row" 문자열 키 Map ${tMap.toFixed(3)} us/회   (${(tMap / tFlat).toFixed(1)}배)`);
if (sink === 0) say('   (측정값이 최적화로 사라지지 않았는지 확인용 합계가 0이다 — 이상함)');

// ------------------------------------------- 4. 맵이 커지면 어떻게 달라지는가
{
  const BW = 160, BH = 120;
  const big = new (require('../src/hexmap') as typeof import('../src/hexmap')).HexMap(BW, BH);
  for (let i = 0; i < BW * BH; i++) big.cells[i] = ((i * 7) % 5 === 0) ? 1 : 0;   // 평지·숲 섞기
  const pool = new (require('../src/units') as typeof import('../src/units')).UnitPool();
  const bu: Mover = { q: 80, r: 60, mp: 60, side: 0 };

  function heapBig(): P.Reach {
    const start = big.axialIdx(bu.q, bu.r);
    const best = new Int32Array(BW * BH).fill(P.UNREACHED);
    best[start] = 0;
    const heap: Array<[number, number]> = [[0, start]];
    const push = (c: number, i: number) => {
      heap.push([c, i]);
      let k = heap.length - 1;
      while (k > 0) {
        const p2 = (k - 1) >> 1;
        if (heap[k]![0] >= heap[p2]![0]) break;
        const t = heap[k]!; heap[k] = heap[p2]!; heap[p2] = t; k = p2;
      }
    };
    const pop = (): [number, number] => {
      const top = heap[0]!;
      const last = heap.pop()!;
      if (heap.length) {
        heap[0] = last;
        let k = 0;
        for (;;) {
          const l = 2 * k + 1, r = 2 * k + 2;
          let s2 = k;
          if (l < heap.length && heap[l]![0] < heap[s2]![0]) s2 = l;
          if (r < heap.length && heap[r]![0] < heap[s2]![0]) s2 = r;
          if (s2 === k) break;
          const t = heap[k]!; heap[k] = heap[s2]!; heap[s2] = t; k = s2;
        }
      }
      return top;
    };
    while (heap.length) {
      const [c, cur] = pop();
      if (c !== best[cur]!) continue;
      const k = big.neighborsWithDir(cur, NBD, NBI);
      for (let j = 0; j < k; j++) {
        const ni = NBI[j]!;
        const cst = P.stepCost(big, pool, 0, cur, ni);
        if (cst < 0) continue;
        const nc = c + cst;
        if (nc <= bu.mp && nc < best[ni]!) { best[ni] = nc; push(nc, ni); }
      }
    }
    const cost = new Map<number, number>();
    const came = new Map<number, number>();
    const list: number[] = [];
    for (let i = 0; i < BW * BH; i++) {
      if (best[i]! !== P.UNREACHED) { cost.set(i, best[i]!); came.set(i, -1); list.push(i); }
    }
    return new P.Reach(cost, came, list);
  }

  const tB = bench(() => { P.reachable(big, pool, bu as never); }, 120);
  const tH = bench(() => { heapBig(); }, 120);
  const reached = P.reachable(big, pool, bu as never).list.length;
  say('');
  say('== 4. 같은 비교를 큰 맵에서 — 160×120 (19,200칸) · 이동력 60 ==');
  say(`   닿는 칸 ${reached}개`);
  say(`   양동이 큐 ${tB.toFixed(1)} us/회`);
  say(`   이진 힙   ${tH.toFixed(1)} us/회   (${(tH / tB).toFixed(2)}배)`);
  say('   → 정점이 많아지고 나서야 log 가 사라진 이득이 드러난다.');
}

import * as fs from 'fs';
import * as path from 'path';
const dst = path.join(__dirname, '..', '..', '..', 'out', 'bench_ds.txt');
fs.writeFileSync(dst, out.join('\n') + '\n');

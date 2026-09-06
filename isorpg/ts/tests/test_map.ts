// 맵 — LCG, 다이아몬드-스퀘어, 셀 패킹, RLE 왕복.
import * as H from './harness';
import * as M from '../src/gamemap';
import * as R from '../src/rng';

/** 참값 (a*s + c) mod 2^32 를 분할 곱으로 따로 구해 엔진 구현과 견준다.
 *  a*s 를 그대로 곱하면 2^57 이라 배정밀도 가수를 넘어 검산이 되지 않는다. */
function refStep(s: number): number {
  const sh = Math.floor(s / 65536);
  const sl = s - sh * 65536;
  const lo = R.LCG_A * sl + R.LCG_C;
  const hi = R.LCG_A * sh;
  const t = (hi - 65536 * Math.floor(hi / 65536)) * 65536 + lo;
  return t - R.LCG_M * Math.floor(t / R.LCG_M);
}

export function run(): number {
  H.title('gamemap');

  // ---- LCG : 골든 앞 8개
  const r = new R.Rng(1);
  const got: Array<[number, number]> = [];
  for (let i = 0; i < 8; i++) {
    const v = r.next();
    got.push([r.s, v]);
  }
  H.check('seed 1 첫 상태', got[0], [22695478, 346]);
  H.check('seed 1 여덟째 상태', got[7], [420428313, 6415]);
  H.check('rand15 범위', got.every(([, v]) => v >= 0 && v < 32768), true);

  // ---- 분할 곱이 진짜 곱과 같은가 (2^53 우회로 검증)
  let s = 1;
  let bad = 0;
  for (let i = 0; i < 20000; i++) {
    const want = refStep(s);
    const s2 = new R.Rng(s);
    s2.next();
    if (s2.s !== want) bad += 1;
    s = want;
  }
  H.check('분할 곱 == (a*s+c) mod 2^32 (2만 걸음)', bad, 0);

  // ---- Hull-Dobell 조건
  H.check('gcd(c, m) = 1', R.LCG_C % 2, 1);
  H.check('(a-1) 이 2로 나누어짐', (R.LCG_A - 1) % 2, 0);
  H.check('(a-1) 이 4로 나누어짐', (R.LCG_A - 1) % 4, 0);

  // ---- 주기: 하위 비트는 주기가 짧다 (도스 시절의 유명한 함정)
  const seen: number[] = [];
  s = 1;
  for (let i = 0; i < 16; i++) {
    s = refStep(s);
    seen.push(s % 2);
  }
  const alt: number[] = [];
  for (let i = 0; i < 8; i++) alt.push(0, 1);
  H.check('상태 최하위 비트는 0,1 을 번갈아 (주기 2)', seen, alt);

  // ---- 셀 패킹
  for (let t = 0; t < 16; t++) {
    for (let h = 0; h < 16; h++) {
      const c = M.makeCell(t, h);
      H.checkTrue('패킹 t=' + t + ' h=' + h,
        M.terrainOf(c) === t && M.heightOf(c) === h && c >= 0 && c < 256);
    }
  }

  // ---- 다이아몬드-스퀘어 5x5 골든
  const mini = M.genHeight(4, [50, 60, 70, 80], 100, 1);
  H.check('5x5 격자', mini, [
    [50, 40, 103, 132, 60], [86, 130, 106, 72, 72], [104, 73, 110, 94, 68],
    [82, 156, 116, 68, 130], [70, 88, 185, 145, 80],
  ]);
  H.check('두 번 돌려도 같은가', M.genHeight(4, [50, 60, 70, 80], 100, 1), mini);

  // ---- 실제 맵
  const m = M.genMap();
  H.check('맵 크기', [m.w, m.h, m.cells.length], [48, 48, 48 * 48]);
  H.checkTrue('모든 셀이 0..255', Array.from(m.cells).every((c) => c >= 0 && c < 256));
  H.checkTrue('높이는 0..15', Array.from(m.cells).every((c) => M.heightOf(c) <= 15));

  // ---- 마을이 제대로 찍혔는가
  H.check('마을 네 귀퉁이는 벽',
    ([[18, 18], [29, 18], [18, 29], [29, 29]] as Array<[number, number]>)
      .map(([x, y]) => M.terrainOf(m.at(x, y))),
    [M.T_WALL, M.T_WALL, M.T_WALL, M.T_WALL]);
  H.check('남문은 길', M.terrainOf(m.at(24, 29)), M.T_ROAD);
  const hs = new Set<number>();
  for (let y = 18; y < 30; y++) for (let x = 18; x < 30; x++) hs.add(M.heightOf(m.at(x, y)));
  H.check('마을 바닥은 높이 2, 성벽은 4', Array.from(hs).sort((a, b) => a - b), [2, 4]);
  const wall: number[] = [];
  for (let x = 19; x < 24; x++) wall.push(M.terrainOf(m.at(x, 18)));
  H.check('성벽 한 줄', wall, [M.T_WALL, M.T_WALL, M.T_WALL, M.T_WALL, M.T_WALL]);
  H.check('마을 남쪽 길', [31, 35, 40, 47].map((y) => M.terrainOf(m.at(24, y))),
    [M.T_ROAD, M.T_ROAD, M.T_ROAD, M.T_ROAD]);
  const ts = new Set<number>();
  const hset = new Set<number>();
  for (const c of Array.from(m.cells)) { ts.add(M.terrainOf(c)); hset.add(M.heightOf(c)); }
  H.checkTrue('지형이 7종 이상 나온다', ts.size >= 7);
  H.checkTrue('높이가 5단계 이상 나온다', hset.size >= 5);

  // ---- RLE 왕복
  const text = M.saveRle(m);
  const m2 = M.loadRle(text);
  H.check('RLE 왕복', m2.cells, m.cells);
  H.check('RLE 다시 저장해도 같은 글자', M.saveRle(m2), text);
  let runs = 0;
  for (const l of text.trim().split('\n').slice(1)) runs += l.split(/\s+/).length;
  H.note('셀 ' + m.cells.length + '개 -> 런 ' + runs + '개 (이진 RLE ' + runs * 2
    + '바이트, 텍스트 ' + Buffer.byteLength(text, 'utf8') + '바이트)');
  H.checkTrue('이진 RLE 는 원본보다 짧다', runs * 2 < m.cells.length);
  H.checkTrue('평균 런 길이가 2.5 이상', Math.floor((m.cells.length * 10) / runs) >= 25);

  // ---- 골든 파일과 같은가
  H.check('golden/map.txt', text, H.golden('map.txt'));

  return H.done();
}

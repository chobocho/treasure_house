// 상자 정렬 — 부분순서, 순환, 보조정리 6.2 를 실제로 확인한다.
import * as H from './harness';
import * as S from '../src/sortdag';

interface Case { num: number; name: string; items: S.Box[]; }

function loadCases(): Case[] {
  const rows = H.golden('sortcase.txt').trim().split('\n').map((l) => l.split(/\s+/));
  const out: Case[] = [];
  let i = 1;
  while (i < rows.length) {
    const row = rows[i] as string[];
    const num = parseInt(row[1] as string, 10);
    const name = row[2] as string;
    const n = parseInt(row[3] as string, 10);
    i += 1;
    const items: S.Box[] = [];
    for (let k = 0; k < n; k++) {
      items.push((rows[i + k] as string[]).map((v) => parseInt(v, 10)));
    }
    i += n;
    out.push({ num, name, items });
  }
  return out;
}

let rs = 999;
function rnd(n: number): number {
  // (1103515245 * rs) 는 2^61 까지 커지므로 상·하위로 쪼개 2^31 로 접는다
  const sh = Math.floor(rs / 65536);
  const sl = rs - sh * 65536;
  const lo = 1103515245 * sl + 12345;
  const hi = 1103515245 * sh;
  const t = (hi - 32768 * Math.floor(hi / 32768)) * 65536 + lo;
  rs = t - 2147483648 * Math.floor(t / 2147483648);
  return rs % n;
}

export function run(): number {
  H.title('sortdag');

  const CASES = loadCases();
  H.check('사례 개수', CASES.length, 6);

  const EXPECT: Record<number, [number[], number]> = {
    1: [[0, 1], 0], 2: [[0, 1], 0], 3: [[0, 1], 0],
    4: [[2, 0, 1], 0], 5: [[0, 1], 0], 6: [[0, 1, 2], 1],
  };
  for (const c of CASES) {
    const got = S.topoSort(c.items);
    H.check('case ' + c.num + ' ' + c.name, [got[0], got[1]], EXPECT[c.num]);
  }

  // ---- 6번은 진짜 3-순환인가 (간선이 정확히 세 개, 한 방향씩)
  const items6 = (CASES.find((c) => c.num === 6) as Case).items;
  const bb6 = items6.map(S.boxBbox);
  const edges: Array<[number, number]> = [];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      if (i !== j && S.bboxOverlap(bb6[i] as S.BBox, bb6[j] as S.BBox)) {
        if (S.behind(items6[i] as S.Box, items6[j] as S.Box)
          && !S.behind(items6[j] as S.Box, items6[i] as S.Box)) edges.push([i, j]);
      }
    }
  }
  edges.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  H.check('3-순환 간선', edges, [[0, 1], [1, 2], [2, 0]]);

  // ---- 5번은 상호 관계인데 화면에서 겹치는가
  const items5 = (CASES.find((c) => c.num === 5) as Case).items;
  const b5 = items5.map(S.boxBbox);
  H.checkTrue('5번 경계상자 겹침', S.bboxOverlap(b5[0] as S.BBox, b5[1] as S.BBox));
  H.checkTrue('5번 상호 behind',
    S.behind(items5[0] as S.Box, items5[1] as S.Box)
    && S.behind(items5[1] as S.Box, items5[0] as S.Box));

  // ---- 보조정리 6.2 : x/y 상호는 겹칠 수 없다
  let viol = 0;
  let xyMutual = 0;
  for (let t = 0; t < 60000; t++) {
    const ax0 = rnd(6);
    const ay0 = rnd(6);
    const az0 = rnd(4);
    const a: S.Box = [0, ax0, ay0, az0, ax0 + 1 + rnd(3), ay0 + 1 + rnd(3), az0 + 1 + rnd(2)];
    const bx0 = rnd(6);
    const by0 = rnd(6);
    const bz0 = rnd(4);
    const b: S.Box = [1, bx0, by0, bz0, bx0 + 1 + rnd(3), by0 + 1 + rnd(3), bz0 + 1 + rnd(2)];
    if (((a[4] as number) <= (b[1] as number) && (b[5] as number) <= (a[2] as number))
      || ((b[4] as number) <= (a[1] as number) && (a[5] as number) <= (b[2] as number))) {
      xyMutual += 1;
      if (S.bboxOverlap(S.boxBbox(a), S.boxBbox(b))) viol += 1;
    }
  }
  H.note('x/y 상호 사례 ' + xyMutual + '건 생성');
  H.check('보조정리 6.2 반례', viol, 0);

  // ---- 정렬 결과는 결정적인가 (같은 입력 -> 같은 출력)
  for (const c of CASES) {
    H.check('결정성 case ' + c.num, S.topoSort(c.items), S.topoSort(c.items));
  }

  // ---- 순환이 없으면 위상 순서가 실제로 모든 간선을 지키는가
  for (const c of CASES) {
    const [order, breaks] = S.topoSort(c.items);
    if (breaks) continue;
    const pos = new Map<number, number>();
    order.forEach((v, i) => pos.set(v, i));
    let bad = 0;
    const bbs = c.items.map(S.boxBbox);
    for (let i = 0; i < c.items.length; i++) {
      for (let j = 0; j < c.items.length; j++) {
        if (i !== j && S.bboxOverlap(bbs[i] as S.BBox, bbs[j] as S.BBox)) {
          if (S.behind(c.items[i] as S.Box, c.items[j] as S.Box)
            && !S.behind(c.items[j] as S.Box, c.items[i] as S.Box)) {
            const pi = pos.get((c.items[i] as S.Box)[0] as number) as number;
            const pj = pos.get((c.items[j] as S.Box)[0] as number) as number;
            if (pi > pj) bad += 1;
          }
        }
      }
    }
    H.check('case ' + c.num + ' 간선 위반', bad, 0);
  }

  return H.done();
}

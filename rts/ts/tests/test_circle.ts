// 원 마스크 — 정의와 증분 계산이 같은 집합인가 (SPEC §6).

import * as H from './harness';
import * as C from '../src/circle';

H.title('circle');

// ---- 전수 비교: r = 1..64 에서 정의와 span 계산이 같은 집합인가
let bad = 0;
for (let r = 1; r <= 64; r += 1) {
  const want = new Set<string>();
  for (let y = -r; y <= r; y += 1) {
    for (let x = -r; x <= r; x += 1) {
      if (x * x + y * y <= r * r) want.add(x + ',' + y);
    }
  }
  const got = new Set<string>();
  for (const [x, y] of C.offsets(r)) got.add(x + ',' + y);
  let same = want.size === got.size;
  if (same) {
    for (const k of want) {
      if (!got.has(k)) {
        same = false;
        break;
      }
    }
  }
  if (!same) {
    bad += 1;
    H.note('r=' + r + ': 집합이 다르다');
  }
}
H.check('r=1..64 에서 disc_spans == {x²+y² <= r²}', bad, 0);

// ---- 가우스 원 문제의 개수 (SPEC 정리 6.1)
H.check('N(r), r=1..8', H.range(1, 9).map((r) => C.offsets(r).length),
        [5, 13, 29, 49, 81, 113, 149, 197]);

// ---- 골든 6절과 대조
const rows = H.golden('prim.txt').split('\n');
const i = rows.indexOf('== 6. 원 마스크 ==') + 2;
bad = 0;
for (let r = 1; r <= 8; r += 1) {
  const p = H.fields(rows[i + r - 1]);
  if (parseInt(p[1], 10) !== C.offsets(r).length) bad += 1;
  const want = p.slice(2).map((s) => parseInt(s, 10));
  if (!H.deepEq(want, C.spans(r))) {
    bad += 1;
    H.note('r=' + r + ' span 기대 ' + JSON.stringify(p.slice(2))
           + ' 실제 ' + JSON.stringify(C.spans(r)));
  }
}
H.check('개수·span 이 골든과 같다', bad, 0);

// ---- 순회 순서가 고정인가 (SPEC §6.3)
const o = C.offsets(3);
H.check('첫 원소', o[0], [0, -3]);
H.check('마지막 원소', o[o.length - 1], [0, 3]);
H.checkTrue('dy 오름차순, 같은 dy 안에서 dx 오름차순',
            H.range(o.length - 1).every(
              (k) => H.cmpArr([o[k][1], o[k][0]],
                              [o[k + 1][1], o[k + 1][0]]) <= 0));

// ---- 곱셈을 쓰지 않는가 (span 계산은 덧셈만)
H.check('spans(8)', C.spans(8), [8, 7, 7, 7, 6, 6, 5, 3, 0]);
H.check('in_disc(3,3,5)', C.inDisc(3, 3, 5), true);
H.check('in_disc(4,4,5)', C.inDisc(4, 4, 5), false);

// ---- 고전 미드포인트 외곽선은 원 밖의 점을 찍는다 (SPEC §6.2)
const out = C.midpointOutline(2);
H.checkTrue('r=2 외곽선에 (2,1) 이 있다',
            out.some((p) => p[0] === 2 && p[1] === 1));
H.checkTrue('그런데 (2,1) 은 원 밖이다', 2 * 2 + 1 * 1 > 2 * 2);
H.note('그래서 시야 마스크에 외곽선 알고리즘을 쓰면 개수가 가우스 값과 어긋난다');

// ---- 캐시가 같은 객체를 돌려주되 내용이 바뀌지 않는가
H.check('offsets 는 매번 같은 목록', C.offsets(5), C.offsets(5));

H.done();

// `main prim` 이 골든을 바이트 단위로 재현하는가 (SPEC §24).
//
//    이 한 시험이 엔진 전체와 **독립 참조 구현**(tools/gen_prim.py)의 대조다.
//    앞선 시험들이 모듈을 따로 확인했다면, 이것은 열넷 절을 한꺼번에 맞춘다.

import * as H from './harness';
import * as MAIN from '../src/main';

H.title('prim');

const got = MAIN.cmdPrim().split('\n');
const want = H.golden('prim.txt').split('\n');

H.check('줄 수', got.length, want.length);
let bad = 0;
let first = -1;
for (let k = 0; k < Math.min(got.length, want.length); k += 1) {
  if (got[k] !== want[k]) {
    bad += 1;
    if (first < 0) {
      first = k;
      H.note((k + 1) + '행 기대 ' + JSON.stringify(want[k]));
      H.note('     실제 ' + JSON.stringify(got[k]));
    }
  }
}
H.check(want.length + '행 전부 일치', bad, 0);

const secs = want.filter((ln) => ln.indexOf('== ') === 0);
H.check('절 구분은 14개', secs.length, 14);
H.check('절 표시 형식',
        secs.filter((s) => s.slice(s.length - 3) !== ' =='), []);
H.check('덱 지시자가 자를 수 있는 형태', secs[0], '== 1. 거리 척도 ==');
H.check('출력은 줄바꿈으로 끝난다',
        MAIN.cmdPrim().slice(MAIN.cmdPrim().length - 1), '\n');

// 절 하나만 바뀌어도 잡히는가 — 시험 자체의 민감도 확인
H.checkTrue('절마다 내용이 다르다', new Set(secs).size === 14);

H.done();

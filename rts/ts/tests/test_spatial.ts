// 엔티티와 공간 분할 — SoA·핸들 세대·균일 격자 (SPEC §7).

import * as H from './harness';
import * as S from '../src/spatial';

H.title('spatial');

const w = new S.World(64, 64);

// ---- 슬롯 0 은 쓰지 않는다 (핸들 0 = "없음")
const h1 = w.spawn(0, 0, 10, 10);
H.checkTrue('첫 핸들은 0 이 아니다', h1 !== 0);
H.check('첫 슬롯은 1', S.index(h1), 1);

// ---- 핸들 = 인덱스 * 256 + 세대 (SPEC §7.2)
H.check('handle(1) 의 인덱스', S.index(h1), 1);
H.check('valid', w.valid(h1), true);
w.kill(h1);
H.check('죽으면 무효', w.valid(h1), false);
const h2 = w.spawn(1, 1, 12, 12);
H.check('슬롯이 재사용된다', S.index(h2), 1);
H.check('그런데 옛 핸들은 여전히 무효', w.valid(h1), false);
H.check('새 핸들은 유효', w.valid(h2), true);
H.check('세대가 하나 올랐다', h2 - h1, 1);
H.check('핸들 0 은 언제나 무효', w.valid(0), false);

// ---- 세대는 256에서 돈다
const w2 = new S.World(16, 16);
const hs: number[] = [];
for (let k = 0; k < 300; k += 1) {
  const h = w2.spawn(0, 0, 1, 1);
  hs.push(h);
  w2.kill(h);
}
H.check('세대가 순환해도 인덱스는 그대로', S.index(hs[hs.length - 1]), 1);
H.checkTrue('한 바퀴 돌면 같은 핸들이 다시 나온다',
            hs.slice(256).indexOf(hs[0]) >= 0);
H.note('그래서 세대는 "즉시 재사용"만 막는다 — 256번 뒤의 충돌은 막지 못한다');

// ---- 버킷 질의 (SPEC §7.3)
const w3 = new S.World(64, 64);
const a = w3.spawn(0, 0, 3, 3);
const b = w3.spawn(0, 0, 5, 5);
const c = w3.spawn(0, 0, 40, 40);
H.check('반경 4 안에 둘', H.sortedNums(w3.query(4, 4, 4)),
        H.sortedNums([S.index(a), S.index(b)]));
H.check('반경 1 이면 (3,3) 만', w3.query(3, 3, 1), [S.index(a)]);
H.check('먼 쪽 질의', w3.query(40, 40, 1), [S.index(c)]);
H.check('버킷 개수', w3.bw * w3.bh, 64);
H.check('bucket_of(0,0)', w3.bucketOf(0, 0), 0);
H.check('bucket_of(63,63)', w3.bucketOf(63, 63), 63);

// ---- 목록이 인덱스 오름차순인가 (결정론)
const w4 = new S.World(64, 64);
const made: number[] = [];
for (let k = 0; k < 6; k += 1) made.push(w4.spawn(0, 0, 2, 2));
w4.kill(made[2]);
w4.spawn(0, 0, 2, 2);
const lst = w4.query(2, 2, 1);
H.check('버킷 질의 결과는 인덱스 오름차순', lst, H.sortedNums(lst));
H.note('순서가 흔들리면 "가장 가까운 적" 타이브레이크가 갈리고 그대로 디싱크다');

// ---- 타일을 넘을 때만 버킷을 갱신
const w5 = new S.World(64, 64);
const e = w5.spawn(0, 0, 1, 1);
const i = S.index(e);
w5.moveTile(i, 9, 9);
H.check('옛 버킷에서 빠졌다', w5.query(1, 1, 0), []);
H.check('새 버킷에 들어갔다', w5.query(9, 9, 0), [i]);

// ---- 상한
const w6 = new S.World(16, 16);
const made6: number[] = [];
for (let k = 0; k < S.MAX_ENT - 1; k += 1) made6.push(w6.spawn(0, 0, 1, 1));
H.check('슬롯 1..255 를 다 쓴다', made6.length, 255);
H.check('그다음은 0 (실패)', w6.spawn(0, 0, 1, 1), 0);

H.done();

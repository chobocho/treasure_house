// 주사위 — 합성곱 분포, 기대값·분산을 정수 항등식으로.
import * as H from './harness';
import * as D from '../src/dice';
import * as R from '../src/rng';

export function run(): number {
  H.title('dice');

  H.check('0면? 1d1', D.dist(1, 1), [0, 1]);
  H.check('1d6', D.dist(1, 6), [0, 1, 1, 1, 1, 1, 1]);
  H.check('2d6', D.dist(2, 6).slice(2), [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]);
  H.check('3d6', D.dist(3, 6).slice(3),
    [1, 3, 6, 10, 15, 21, 25, 27, 27, 25, 21, 15, 10, 6, 3, 1]);

  for (let n = 1; n <= 4; n++) {
    for (const mm of [4, 6, 8, 20]) {
      const c = D.dist(n, mm);
      const mn = Math.pow(mm, n);
      let tot = 0;
      let s1 = 0;
      let s2 = 0;
      for (let s = 0; s < c.length; s++) {
        const v = c[s] as number;
        tot += v;
        s1 += s * v;
        s2 += s * s * v;
      }
      H.check('경우의 수 ' + n + 'd' + mm, tot, mn);
      // 기대값 n(m+1)/2 를 정수 항등식으로: 2*sum(s*c[s]) == n*(m+1)*m^n
      H.check('기대값 ' + n + 'd' + mm, 2 * s1, n * (mm + 1) * mn);
      // 분산 n(m^2-1)/12 : 12*(sum(s^2 c) * m^n - (sum(s c))^2) == n(m^2-1) * m^(2n)
      // 최대값이 20^8 * 3 ~ 7.7e10 이라 배정밀도 안에서 정확하다.
      H.check('분산 ' + n + 'd' + mm,
        12 * (s2 * mn - s1 * s1), n * (mm * mm - 1) * Math.pow(mm, 2 * n));
      H.check(n + 'd' + mm + ' 분포는 좌우 대칭', c.slice(n), c.slice(n).reverse());
    }
  }

  // ---- 명중률
  H.check('to_hit(atk=0, def=0)', D.toHit(0, 0), 11);
  H.check('명중 눈의 수 (0,0)', D.pHit(0, 0), 10);
  H.check('아주 센 공격도 19/20 이 상한', D.pHit(100, 0), 19);
  H.check('아주 약한 공격도 1/20 은 남는다', D.pHit(0, 100), 1);

  // ---- 실제 굴림 분포가 이론과 어긋나지 않는가 (골든 난수)
  const r = new R.Rng(4242);
  const cnt: number[] = new Array<number>(13).fill(0);
  for (let i = 0; i < 36000; i++) {
    const s = D.roll(r, 2, 6);
    cnt[s] = (cnt[s] as number) + 1;
  }
  const exp = D.dist(2, 6);
  let worst = 0;
  for (let s = 2; s <= 12; s++) {
    const e = (exp[s] as number) * 1000;
    const dev = Math.floor((Math.abs((cnt[s] as number) - e) * 1000) / e);
    if (dev > worst) worst = dev;
  }
  H.note('2d6 36,000회 — 이론 대비 최대 편차 ' + worst + '/1000');
  H.checkTrue('편차가 10% 안', worst < 100);

  // ---- 성장 곡선
  H.check('xp_to_next(1)', D.xpToNext(1), 50);
  H.check('xp_to_next(2)', D.xpToNext(2), 140);
  H.check('xp_to_next(3)', D.xpToNext(3), 270);
  let mono = true;
  for (let l = 1; l < 30; l++) if (!(D.xpToNext(l) < D.xpToNext(l + 1))) mono = false;
  H.checkTrue('단조 증가', mono);

  return H.done();
}

// 난수 — SPEC §5.2. 볼랜드 계열 LCG.
//
// 상태가 2^32 미만이라 `s >>> 16` 이나 `s & 0xffff` 로 쓰고 싶어지는 자리인데,
// 곱한 뒤의 중간값(22695477 * 65535 ~ 2^41)이 32비트를 훌쩍 넘는다.
// `*` 는 배정밀도로 계산되지만 그 결과를 비트 연산에 넣는 순간 하위 32비트만 남는다.
// 그래서 상·하위 16비트로 쪼개 나눗셈과 곱셈만으로 처리한다. (정리 5.1)
export const LCG_A = 22695477;
export const LCG_C = 1;
export const LCG_M = 4294967296; // 2^32

export class Rng {
  s: number;

  constructor(seed: number) {
    this.s = seed - LCG_M * Math.floor(seed / LCG_M);
  }

  /** 상태를 한 걸음 굴리고 15비트 난수를 돌려준다 (0..32767).
   *
   *  하위 비트는 주기가 짧다 — 최하위 비트는 0,1 을 번갈 뿐이다.
   *  그래서 도스 시절 rand() 도 비트 30..16 을 꺼내 썼다. */
  next(): number {
    const s = this.s;
    const sh = Math.floor(s / 65536);
    const sl = s - sh * 65536;
    const lo = LCG_A * sl + LCG_C; // < 2^41
    const hi = LCG_A * sh; // < 2^41
    const t = (hi - 65536 * Math.floor(hi / 65536)) * 65536 + lo;
    this.s = t - LCG_M * Math.floor(t / LCG_M);
    const u = Math.floor(this.s / 65536);
    return u - 32768 * Math.floor(u / 32768);
  }

  below(n: number): number {
    const v = this.next();
    return v - n * Math.floor(v / n);
  }

  roll(n: number, m: number): number {
    let t = 0;
    for (let i = 0; i < n; i++) {
      const v = this.next();
      t += v - m * Math.floor(v / m) + 1;
    }
    return t;
  }
}

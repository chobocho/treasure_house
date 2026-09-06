// 난수 — 볼랜드 계열 LCG 하나 (SPEC §3).
//
//    짧은 파일이지만 언어를 건너는 지점이 둘 있다.
//      · 22695477 * s 는 최대 2^56 이라 53비트 가수에 담기지 않는다 → 분할 곱
//      · 나머지만 쓰면 모듈로 편향이 생긴다 → 기각 표본추출
//
//    시뮬레이션은 이 인스턴스를 **정확히 하나** 갖는다(SPEC §3.3). 렌더나 UI 가
//    난수를 뽑는 순간 두 기계의 수열이 갈리고, 그 뒤로 모든 것이 어긋난다.

import { floordiv, fmod } from './fixed';

export const A = 22695477;
export const M32 = 4294967296;

export class LCG {
  s: number;
  rejects: number;                     // 통계용 — 상태가 아니다

  constructor(seed: number) {
    this.s = fmod(seed, M32);
    this.rejects = 0;
  }

  // ── SPEC §3.1 ────────────────────────────────────────────────────────────
  // 상태를 한 번 굴리고 상위 15비트(비트 30..16)를 돌려준다.
  // 하위 비트는 주기가 짧다 — 최하위 비트는 0,1,0,1 을 반복한다.
  next15(): number {
    const s = this.s;
    const sh = floordiv(s, 65536);
    const sl = fmod(s, 65536);
    const lo = A * sl;                 // < 2^41
    const hi = fmod(A * sh, 65536);    // < 2^16
    this.s = fmod(lo + hi * 65536 + 1, M32);
    return fmod(floordiv(this.s, 65536), 32768);
  }

  // ── SPEC §3.2 ────────────────────────────────────────────────────────────
  // 0 <= 결과 < n 인 균등 난수. 기각 루프도 결정론적이다.
  roll(n: number): number {
    if (n <= 1) return 0;
    const limit = 32768 - fmod(32768, n);
    for (;;) {
      const r = this.next15();
      if (r < limit) return fmod(r, n);
      this.rejects += 1;
    }
  }

  save(): number {
    return this.s;
  }

  load(s: number): void {
    this.s = fmod(s, M32);
  }
}

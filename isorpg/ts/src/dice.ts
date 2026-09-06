// 주사위와 전투 — SPEC §10.
//
// 분포는 합성곱으로 정확히 센다. 몬테카를로가 아니라 경우의 수다 —
// 그래야 기대값과 분산을 정수 항등식으로 검사할 수 있다.
import type { Rng } from './rng';

/** n개의 m면 주사위 합 분포. dist(n,m)[s] = 합이 s 인 경우의 수. O(n^2 * m). */
export function dist(n: number, m: number): number[] {
  let c: number[] = [1];
  for (let k = 0; k < n; k++) {
    const c2: number[] = new Array<number>(c.length + m).fill(0);
    for (let s = 0; s < c.length; s++) {
      const v = c[s] as number;
      if (v) {
        for (let f = 1; f <= m; f++) c2[s + f] = (c2[s + f] as number) + v;
      }
    }
    c = c2;
  }
  return c;
}

/** 실제 굴림. 난수 소비 순서가 명세의 일부다. */
export function roll(r: Rng, n: number, m: number): number {
  let t = 0;
  for (let i = 0; i < n; i++) {
    const v = r.next();
    t += (v - m * Math.floor(v / m)) + 1;
  }
  return t;
}

/** 1d20 이 이 값 이상이면 명중. */
export function toHit(atk: number, dfn: number): number {
  return 11 + dfn - atk;
}

/** 20면 중 명중하는 눈의 수. 1은 언제나 실패, 20은 언제나 성공. */
export function pHit(atk: number, dfn: number): number {
  const v = 21 - toHit(atk, dfn);
  if (v < 1) return 1;
  if (v > 19) return 19;
  return v;
}

export interface AttackResult { hit: boolean; dmg: number; d20: number; }

/** 난수는 명중 굴림 한 번, 그리고 명중했을 때만 피해 굴림 dn번을 쓴다.
 *  빗나갔을 때 피해 굴림을 건너뛰는 것까지 명세다 — 안 그러면 난수 흐름이 갈린다. */
export function attack(
  r: Rng, atk: number, dfn: number, dn: number, dm: number,
  dbonus: number, armor: number,
): AttackResult {
  const v = r.next();
  const d20 = (v - 20 * Math.floor(v / 20)) + 1;
  if (d20 === 1) return { hit: false, dmg: 0, d20 };
  if (d20 !== 20 && d20 < toHit(atk, dfn)) return { hit: false, dmg: 0, d20 };
  let dmg = roll(r, dn, dm) + dbonus - armor;
  if (dmg < 1) dmg = 1;
  return { hit: true, dmg, d20 };
}

/** 다음 레벨까지 필요한 경험치. 2차식이라 후반이 완만하게 무거워진다. */
export function xpToNext(lv: number): number {
  return 20 * lv * lv + 30 * lv;
}

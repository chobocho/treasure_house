// 전투 판정 — SPEC §7

import * as H from './hexcoord';
import { HexMap, T_DEF, TERRAIN_MASK } from './hexmap';
import { Rng } from './rng';
import { K_ATK, K_DEF, K_RNG, Unit, UnitPool } from './units';

export function defenseOf(m: HexMap, _pool: UnitPool, d: Unit): number {
  const i = m.axialIdx(d.q, d.r);
  const terr = i >= 0 ? T_DEF[m.cells[i]! & TERRAIN_MASK]! : 0;
  return Math.floor((K_DEF[d.kind]! * d.hp) / 10) + terr + d.ent;
}

export function attackOf(a: Unit): number {
  return Math.floor((K_ATK[a.kind]! * a.hp) / 10);
}

export interface CombatResult {
  attackerLoss: number; defenderLoss: number; roll: number; score: number;
}

export function resolve(m: HexMap, pool: UnitPool, rng: Rng,
                        a: Unit, d: Unit): CombatResult {
  const atk = attackOf(a);
  const dfn = defenseOf(m, pool, d);
  const roll = rng.d6() + rng.d6();
  const score = atk - dfn + roll - 7;

  let dl: number, al: number;
  if (score >= 4) { dl = 3; al = 0; }
  else if (score >= 1) { dl = 2; al = 1; }
  else if (score >= -2) { dl = 1; al = 1; }
  else { dl = 0; al = 2; }

  a.ammo -= 1;
  a.mp = 0;
  d.hp -= dl;
  a.hp -= al;

  let counter = 0;
  if (d.hp > 0 && d.ammo > 0 && K_RNG[d.kind]! >= 1 &&
      H.distance(a.q, a.r, d.q, d.r) === 1) {
    counter = dl >> 1;
    if (counter > 0) { a.hp -= counter; d.ammo -= 1; }
  }
  return { attackerLoss: al + counter, defenderLoss: dl, roll, score };
}

export function canAttack(_m: HexMap, _pool: UnitPool, a: Unit, d: Unit): boolean {
  if (a.side === d.side || a.ammo <= 0 || a.mp <= 0) return false;
  return H.distance(a.q, a.r, d.q, d.r) <= K_RNG[a.kind]!;
}

// 적군 AI — 결정성이 규격이다(골든 트레이스에 적군 턴이 들어간다)

import { attackOf, defenseOf } from './combat';
import { Game } from './game';
import * as H from './hexcoord';
import { HexMap } from './hexmap';
import * as P from './path';
import { K_RNG, NO_UNIT, Unit, UnitPool } from './units';

export function scoreAttack(m: HexMap, pool: UnitPool, a: Unit, d: Unit): number {
  return (attackOf(a) - defenseOf(m, pool, d)) * 4 + (10 - d.hp) * 2;
}

export function bestAttack(g: Game, u: Unit): Unit | null {
  let best: Unit | null = null;
  let bs = -999;
  for (const tid of g.pool.aliveIds()) {
    const t = g.pool.get(tid)!;
    if (t.side === u.side) continue;
    if (H.distance(u.q, u.r, t.q, t.r) > K_RNG[u.kind]!) continue;
    const s = scoreAttack(g.map, g.pool, u, t);
    if (s > bs || (s === bs && best !== null && t.id < best.id)) { best = t; bs = s; }
  }
  return best;
}

export function nearestEnemy(g: Game, u: Unit): Unit | null {
  let best: Unit | null = null;
  let bd = 1 << 30;
  for (const tid of g.pool.aliveIds()) {
    const t = g.pool.get(tid)!;
    if (t.side === u.side) continue;
    const d = H.distance(u.q, u.r, t.q, t.r);
    if (d < bd || (d === bd && best !== null && t.id < best.id)) { best = t; bd = d; }
  }
  return best;
}

export function takeTurn(g: Game): number {
  let acted = 0;
  for (const uid of g.pool.aliveIds(g.side)) {
    let u = g.pool.get(uid);
    if (!u) continue;
    if (u.ammo > 0 && u.mp > 0) {
      const t = bestAttack(g, u);
      if (t && scoreAttack(g.map, g.pool, u, t) > -6) {
        g.attack(uid, t.id);
        acted++;
        continue;
      }
    }
    const tgt = nearestEnemy(g, u);
    if (!tgt || u.mp <= 0) continue;
    const reach = P.reachable(g.map, g.pool, u);
    let goal = -1;
    let gs = 1 << 30;
    for (const i of reach.list) {
      if (g.map.occupant[i]! !== NO_UNIT) continue;
      const [q, r] = g.map.idxAxial(i);
      const key = H.distance(q, r, tgt.q, tgt.r) * 100 + reach.cost.get(i)!;
      if (key < gs || (key === gs && i < goal)) { goal = i; gs = key; }
    }
    if (goal >= 0 && goal !== g.map.axialIdx(u.q, u.r)) {
      g.moveUnit(uid, goal);
      acted++;
      u = g.pool.get(uid);
      if (u && u.ammo > 0 && u.mp > 0) {
        const t2 = bestAttack(g, u);
        if (t2) { g.attack(uid, t2.id); acted++; }
      }
    }
  }
  return acted;
}

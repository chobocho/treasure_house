// 시야와 안개 — SPEC §9

import * as H from './hexcoord';
import { ELEV_MASK, ELEV_SHIFT, FOG_EXPLORED, FOG_VISIBLE, HexMap,
         T_BLOCK, T_LOSH, TERRAIN_MASK } from './hexmap';
import { K_VIS, Unit, UnitPool } from './units';

export function hexHeight(m: HexMap, i: number): number {
  const c = m.cells[i]!;
  return ((c >> ELEV_SHIFT) & ELEV_MASK) + T_LOSH[c & TERRAIN_MASK]!;
}

export function blocksSight(m: HexMap, i: number): boolean {
  return T_BLOCK[m.cells[i]! & TERRAIN_MASK] === 1;
}

export function losClear(m: HexMap, aq: number, ar: number,
                         bq: number, br: number): boolean {
  const n = H.distance(aq, ar, bq, br);
  if (n <= 1) return true;
  const ia = m.axialIdx(aq, ar);
  const ib = m.axialIdx(bq, br);
  if (ia < 0 || ib < 0) return false;
  const ha = hexHeight(m, ia) + 1;
  const hb = hexHeight(m, ib);
  const pts = H.line(aq, ar, bq, br);
  for (let i = 1; i < n; i++) {
    const p = pts[i]!;
    const im = m.axialIdx(p[0], p[1]);
    if (im < 0) return false;
    const hm = hexHeight(m, im);
    const lineH = ha * (n - i) + hb * i;
    if (hm * n > lineH || (blocksSight(m, im) && hm * n >= lineH)) return false;
  }
  return true;
}

export function visibleHexes(m: HexMap, u: Unit, vis: number): number[] {
  const out: number[] = [];
  for (const [q, r] of H.spiral(u.q, u.r, vis)) {
    const i = m.axialIdx(q, r);
    if (i >= 0 && losClear(m, u.q, u.r, q, r)) out.push(i);
  }
  return out;
}

export function updateFog(m: HexMap, pool: UnitPool, side: number): void {
  for (let i = 0; i < m.n; i++) {
    if (m.fog[i] === FOG_VISIBLE) m.fog[i] = FOG_EXPLORED;
  }
  for (const uid of pool.aliveIds(side)) {
    const u = pool.get(uid)!;
    for (const i of visibleHexes(m, u, K_VIS[u.kind]!)) m.fog[i] = FOG_VISIBLE;
  }
}

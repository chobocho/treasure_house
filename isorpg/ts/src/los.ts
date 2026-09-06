// 시야·안개·조명 — SPEC §9.
//
// 브레젠험 직선 하나로 셋을 다 만든다. 시야는 그 선 위에 막는 것이 있는지,
// 안개는 본 적 있는지, 조명은 얼마나 먼지.
import * as M from './gamemap';
import type { GameMap } from './gamemap';
import { octDist } from './fixed';

export const EYE = 2;
export const SIGHT_R = 9;

export type Pt = [number, number];

/** 브레젠험 정수 직선. 양 끝을 포함한다.
 *
 *  err 는 '이상적 직선에서 벗어난 양'을 2*dx 배로 확대해 정수로 들고 다니는 값이다.
 *  길이는 항상 max(|dx|,|dy|) + 1 이고, 걸음마다 x 나 y 가 정확히 1씩 움직인다. */
export function line(x0: number, y0: number, x1: number, y1: number): Pt[] {
  let dx = x1 - x0;
  if (dx < 0) dx = -dx;
  let dy = y1 - y0;
  if (dy < 0) dy = -dy;
  dy = -dy;
  const sx = x0 < x1 ? 1 : -1;
  const sy = y0 < y1 ? 1 : -1;
  let err = dx + dy;
  let x = x0;
  let y = y0;
  const out: Pt[] = [];
  for (;;) {
    out.push([x, y]);
    if (x === x1 && y === y1) return out;
    const e2 = 2 * err;
    if (e2 >= dy) { err += dy; x += sx; }
    if (e2 <= dx) { err += dx; y += sy; }
  }
}

/** (sx,sy) 에서 (gx,gy) 가 보이는가. 중간 칸만 검사한다.
 *
 *  높이 규칙은 단순하다 — 양 끝보다 EYE-1 단계 넘게 솟은 칸이 있으면 막힌다.
 *  진짜 3D 광선을 쏘지 않는 이유는 도스 게임도 그러지 않았기 때문이다. */
export function visible(m: GameMap, sx: number, sy: number, gx: number, gy: number): boolean {
  if (sx === gx && sy === gy) return true;
  if (!m.inside(gx, gy)) return false;
  const hs = m.height(sx, sy);
  const hg = m.height(gx, gy);
  const top = (hs > hg ? hs : hg) + EYE - 1;
  const pts = line(sx, sy, gx, gy);
  for (let i = 1; i < pts.length - 1; i++) {
    const p = pts[i] as Pt;
    const x = p[0];
    const y = p[1];
    if (!m.inside(x, y)) return false;
    if (M.OPAQUE[m.terrain(x, y)]) return false;
    if (m.height(x, y) > top) return false;
  }
  return true;
}

/** 타일마다 2비트. bit0 = 본 적 있다, bit1 = 지금 보인다.
 *  값이 0..3 뿐이라 Uint8Array 로 충분하고, 세이브도 이 배열을 그대로 접는다. */
export class Fog {
  w: number;
  h: number;
  bits: Uint8Array;
  nSeen = 0;
  nVis = 0;

  constructor(w: number, h: number) {
    this.w = w;
    this.h = h;
    this.bits = new Uint8Array(w * h);
  }

  isSeen(x: number, y: number): boolean {
    return (this.bits[y * this.w + x] as number) % 2 === 1;
  }

  isVisible(x: number, y: number): boolean {
    return Math.floor((this.bits[y * this.w + x] as number) / 2) % 2 === 1;
  }

  countSeen(): number {
    return this.nSeen;
  }

  countVisible(): number {
    return this.nVis;
  }

  /** 지금 보이는 칸을 다시 세운다. 기억(bit0)은 지우지 않는다. */
  update(m: GameMap, px: number, py: number): void {
    const bits = this.bits;
    const w = this.w;
    for (let i = 0; i < bits.length; i++) bits[i] = (bits[i] as number) % 2;
    let x0 = px - SIGHT_R;
    let x1 = px + SIGHT_R;
    let y0 = py - SIGHT_R;
    let y1 = py + SIGHT_R;
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > w - 1) x1 = w - 1;
    if (y1 > this.h - 1) y1 = this.h - 1;
    let seen = this.nSeen;
    let vis = 0;
    const rr = SIGHT_R * SIGHT_R;
    for (let y = y0; y <= y1; y++) {
      const dy = y - py;
      const row = y * w;
      for (let x = x0; x <= x1; x++) {
        const dx = x - px;
        // 정사각형이 아니라 원 안만 본다 — 사각형 모서리는 반경 밖이다
        if (dx * dx + dy * dy > rr) continue;
        if (visible(m, px, py, x, y)) {
          if (bits[row + x] === 0) seen += 1;
          bits[row + x] = 3; // 지금 보이면 본 적도 있는 것이다
          vis += 1;
        }
      }
    }
    this.nSeen = seen;
    this.nVis = vis;
  }

  /** 조명 단계 0..15. 지금 보이면 거리에 따라, 기억만 있으면 4, 아니면 0. */
  lightOf(x: number, y: number, px: number, py: number): number {
    const v = this.bits[y * this.w + x] as number;
    if (Math.floor(v / 2) % 2) {
      const d = octDist((x - px) * 256, (y - py) * 256);
      const l = 15 - Math.floor((8 * d) / (SIGHT_R * 256));
      if (l < 7) return 7;
      if (l > 15) return 15;
      return l;
    }
    if (v % 2) return 4;
    return 0;
  }
}

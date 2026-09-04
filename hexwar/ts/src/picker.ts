// 화면 좌표 → 헥스 — SPEC §4

import { MAP_H, MAP_W } from './hexmap';

export const HEX_W = 32;
export const HEX_H = 32;
export const ROW_STEP = 24;
export const ODD_SHIFT = 16;

// SPEC §4.3 의 768바이트 마스크. 도스에서는 오브젝트 파일의 데이터 세그먼트에
// 그대로 들어 있었다 — 여기서는 규칙에서 만들되, 만들어진 표가
// golden/pick_mask.txt 와 같은지 테스트가 확인한다.
export function buildMask(): Uint8Array {
  const m = new Uint8Array(ROW_STEP * HEX_W);
  for (let oy = 0; oy < ROW_STEP; oy++) {
    for (let ox = 0; ox < HEX_W; ox++) {
      let v = 0;
      if (oy < 8 && ox < 16 - 2 * oy) v = 1;
      else if (oy < 8 && ox >= 16 + 2 * oy) v = 2;
      m[oy * HEX_W + ox] = v;
    }
  }
  return m;
}

export const PICK_MASK: Uint8Array = buildMask();

export function hexOrigin(col: number, row: number): [number, number] {
  return [col * HEX_W + (row & 1) * ODD_SHIFT, row * ROW_STEP];
}

export function hexCenter(col: number, row: number): [number, number] {
  const [x, y] = hexOrigin(col, row);
  return [x + (HEX_W >> 1), y + (HEX_H >> 1)];
}

export function nwNeighbor(col: number, row: number): [number, number] {
  return [col - 1 + (row & 1), row - 1];
}

export function neNeighbor(col: number, row: number): [number, number] {
  return [col + (row & 1), row - 1];
}

export function pick(mx: number, my: number, camx: number, camy: number,
                     w: number = MAP_W, h: number = MAP_H): [number, number] | null {
  const yy = my + camy;
  const by = Math.floor(yy / ROW_STEP);
  const oy = yy - by * ROW_STEP;
  const xx = mx + camx - (by & 1) * ODD_SHIFT;
  const bx = Math.floor(xx / HEX_W);
  const ox = xx - bx * HEX_W;

  const v = PICK_MASK[oy * HEX_W + ox]!;
  let col: number, row: number;
  if (v === 0) { col = bx; row = by; }
  else if (v === 1) { [col, row] = nwNeighbor(bx, by); }
  else { [col, row] = neNeighbor(bx, by); }

  if (col >= 0 && col < w && row >= 0 && row < h) return [col, row];
  return null;
}

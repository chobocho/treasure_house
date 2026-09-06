// 쿼터뷰 투영과 역투영 — SPEC §3.
//
// 두 방향 모두 정수만 쓴다. 화면 좌표는 최대 ±768 이라 32비트에 넉넉히 들어가지만,
// 여기서도 `>>` 대신 Math.floor 를 쓴다. `-17 >> 5` 는 -1 이고 `Math.floor(-17/32)`
// 도 -1 이라 우연히 같지만, 나눗수가 2의 거듭제곱이 아닌 자리(§3.4 의 /2, %2)까지
// 섞이면 규칙이 둘이 되어 버린다. 규칙은 하나여야 읽는 사람이 안 틀린다.
import * as F from './fixed';

export const TW = 32; // 마름모 가로 지름
export const TH = 16; // 마름모 세로 지름
export const TZ = 8; // 높이 한 단계
export const SCR_W = 320;
export const SCR_H = 200;
export const MAP_W = 48;
export const MAP_H = 48;
export const MAXH = 15;

export const HW = TW / 2; // 16
export const HH = TH / 2; // 8

/** 타일 -> 마름모 꼭대기 꼭짓점의 월드 픽셀.
 *
 *  기저 e_x = (16, 8), e_y = (-16, 8). 행렬식 256 = 2^8 이라
 *  역행렬 성분이 전부 2의 거듭제곱 배수가 된다 — 그것이 2:1 을 고른 이유다. */
export function tileToScreen(tx: number, ty: number, h: number): [number, number] {
  return [HW * (tx - ty), HH * (tx + ty) - h * TZ];
}

/** 16.16 타일 좌표 -> 월드 픽셀. 엔티티가 타일 사이에 있을 때 쓴다. */
export function worldToScreen(fx: number, fy: number, h: number): [number, number] {
  return [
    F.floordiv((fx - fy) * HW, F.FP_ONE),
    F.floordiv((fx + fy) * HH, F.FP_ONE) - h * TZ,
  ];
}

/** 대수적 역. 나눗셈 두 번이면 끝난다. (정리 3.2) */
export function screenToTile(px: number, py: number): [number, number] {
  return [F.floordiv(px + 2 * py, 32), F.floordiv(2 * py - px, 32)];
}

/** 마름모 정의(|u| + 2|v| <= 16)로 직접 찾는다 — 빠른 식을 검산하는 용도.
 *
 *  경계 픽셀은 여러 마름모에 걸치므로, floor 규칙과 같은 것을 고르려면
 *  a = px+2py 와 b = 2py-px 가 큰 쪽을 택해야 한다. 파이썬은 튜플 비교
 *  하나로 끝나지만 JS 에는 튜플 순서 비교가 없어 손으로 편다. */
export function screenToTileSlow(px: number, py: number): [number, number] {
  const g = screenToTile(px, py);
  let bx = 0;
  let by = 0;
  let have = false;
  for (let tx = g[0] - 2; tx <= g[0] + 2; tx++) {
    for (let ty = g[1] - 2; ty <= g[1] + 2; ty++) {
      const cx = HW * (tx - ty);
      const cy = HH * (tx + ty) + HH;
      const u = px - cx;
      const v = py - cy;
      if ((u >= 0 ? u : -u) + 2 * (v >= 0 ? v : -v) <= HW) {
        if (!have || tx + ty > bx + by || (tx + ty === bx + by && tx > bx)) {
          bx = tx;
          by = ty;
          have = true;
        }
      }
    }
  }
  return [bx, by];
}

/** 32x16 모서리 마스크. 값은 2*A + (B+1) 로 0..3 네 가지뿐이다. (SPEC §3.4) */
function buildMask(): number[] {
  const m: number[] = new Array<number>(TW * TH).fill(0);
  for (let oy = 0; oy < TH; oy++) {
    for (let ox = 0; ox < TW; ox++) {
      const a = F.floordiv(ox + 2 * oy, 32);
      const b = F.floordiv(2 * oy - ox, 32);
      m[oy * TW + ox] = 2 * a + (b + 1);
    }
  }
  return m;
}

export const PICK_MASK: number[] = buildMask();

/** 도스식 역투영 — 나눗셈 두 번(사각형 찾기)과 표 조회 한 번. */
export function pickMask(px: number, py: number): [number, number] {
  const rc = F.floordiv(px, TW);
  const rr = F.floordiv(py, TH);
  const ox = px - TW * rc;
  const oy = py - TH * rr;
  const m = PICK_MASK[oy * TW + ox] as number;
  return [rc + rr + F.floordiv(m, 2), rr - rc + F.fmod(m, 2) - 1];
}

export const MARGIN_X = HW;
// 세로 여백: 마름모 반, 최대 높이 15단계, 그리고 가장 큰 스프라이트(나무 32px)
export const MARGIN_Y = HH + MAXH * TZ + 32;

/** 뷰포트에 걸치는 타일 범위. 네 모서리만 역투영하면 된다. (정리 3.3) */
export function visibleRange(
  x0: number, y0: number, x1: number, y1: number,
): [number, number, number, number] {
  const ax0 = x0 - MARGIN_X;
  const ax1 = x1 + MARGIN_X;
  const ay0 = y0 - MARGIN_Y;
  const ay1 = y1 + MARGIN_Y;
  let tx0 = F.floordiv(ax0 + 2 * ay0, 32);
  let tx1 = F.floordiv(ax1 + 2 * ay1, 32);
  let ty0 = F.floordiv(2 * ay0 - ax1, 32);
  let ty1 = F.floordiv(2 * ay1 - ax0, 32);
  if (tx0 < 0) tx0 = 0;
  if (ty0 < 0) ty0 = 0;
  if (tx1 > MAP_W - 1) tx1 = MAP_W - 1;
  if (ty1 > MAP_H - 1) ty1 = MAP_H - 1;
  return [tx0, ty0, tx1, ty1];
}

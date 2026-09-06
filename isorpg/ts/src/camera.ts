// 카메라 — SPEC §4. 정수 픽셀 스크롤과 데드존 추적.
import { HW, MAP_H, MAP_W, MAXH, SCR_H, SCR_W, TZ } from './proj';

export const DEADZONE_X = 48;
export const DEADZONE_Y = 24;

// 맵 전체가 차지하는 월드 픽셀 범위. 마름모 배치라 가로가 세로의 두 배다.
export const WORLD_X0 = -HW * (MAP_H - 1) - HW;
export const WORLD_X1 = HW * (MAP_W - 1) + HW;
export const WORLD_Y0 = -MAXH * TZ;
export const WORLD_Y1 = 8 * (MAP_W + MAP_H - 2) + 16;

export function clampCam(cx: number, cy: number): [number, number] {
  const loX = WORLD_X0;
  const hiX = WORLD_X1 - SCR_W;
  const loY = WORLD_Y0;
  const hiY = WORLD_Y1 - SCR_H;
  let x = cx;
  let y = cy;
  if (x < loX) x = loX;
  if (x > hiX) x = hiX;
  if (y < loY) y = loY;
  if (y > hiY) y = hiY;
  return [x, y];
}

/** 대상이 데드존을 벗어난 만큼만 카메라를 민다.
 *
 *  매 프레임 중앙에 붙여 두면 걸을 때마다 화면이 흔들린다.
 *  도스 RPG 들이 가운데에 네모난 여유를 둔 이유가 그것이다. */
export function follow(
  cx: number, cy: number, tgtX: number, tgtY: number,
): [number, number] {
  let x = cx;
  let y = cy;
  const dx = tgtX - x - SCR_W / 2;
  const dy = tgtY - y - SCR_H / 2;
  if (dx > DEADZONE_X) x += dx - DEADZONE_X;
  else if (dx < -DEADZONE_X) x += dx + DEADZONE_X;
  if (dy > DEADZONE_Y) y += dy - DEADZONE_Y;
  else if (dy < -DEADZONE_Y) y += dy + DEADZONE_Y;
  return clampCam(x, y);
}

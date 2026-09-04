// 화면 배치 상수 — ui 와 render 가 서로를 import 하면 순환이 생겨 따로 뺐다.
// 파이썬판은 render 가 상수를 갖고 ui 가 가져다 쓰는데, 타입스크립트에서는
// 그 방향이 순환 참조가 되어 초기화 순서 버그를 만든다.

import { MAP_H, MAP_W } from './hexmap';
import { HEX_H, HEX_W, ODD_SHIFT, ROW_STEP } from './picker';

export const SCR_W = 320, SCR_H = 200;
export const VIEW: readonly [number, number, number, number] = [0, 0, 256, 168];
export const PANEL_RECT: readonly [number, number, number, number] = [256, 0, 64, 200];
export const MSG: readonly [number, number, number, number] = [0, 168, 256, 32];

export const MAP_PX_W = MAP_W * HEX_W + ODD_SHIFT;
export const MAP_PX_H = MAP_H * ROW_STEP + (HEX_H - ROW_STEP);
export const CAM_MAX_X = Math.max(0, MAP_PX_W - VIEW[2]);
export const CAM_MAX_Y = Math.max(0, MAP_PX_H - VIEW[3]);

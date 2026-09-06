// 래스터 — 프레임버퍼·팔레트·스프라이트·블릿·폰트·PPM (SPEC §22).
//
//    세 언어 모두 프레임버퍼가 **1차원 정수 배열**이다. 이것이 세 구현을 바이트
//    단위로 비교 가능하게 만드는 유일한 이유다. 프런트엔드는 이 배열에 팔레트로
//    색을 입혀 화면에 올릴 뿐이고, `make parity` 는 192,015바이트짜리 PPM 을
//    `cmp` 한다.
//
//    팔레트와 스프라이트는 정수식으로 만든다(§22.2·§22.3). 표를 세 언어에 옮겨
//    적는 대신 같은 식을 세 번 쓰고, 결과를 골든과 대조한다.

import * as CI from './circle';
import * as C from './const';
import * as F from './fixed';

export const PLAYER_BASE = 160;
export const PLAYER_SHADES = 8;
export const SHADOW = 251;
export const WATER_BASE = 232;
export const WATER_N = 8;
export const DRAWN_DIRS = 5;         // §22.7 그린 방향 수 (나머지 셋은 좌우 반전)
export const UNIT_R = [5, 4, 6, 5, 5];
export const UNIT_M = [3, 3, 4, 3, 3];
export const UNIT_NAME = ['INF', 'ARCHER', 'TANK', 'MORTAR', 'HARV'];
export const BLD_NAME: Array<[number, string]> = [
  [C.HQ, 'HQ'], [C.REF, 'REF'], [C.BARR, 'BARR'],
  [C.FACT, 'FACT'], [C.POW, 'POW'], [C.TOWER, 'TOWER']];

export type RGB = [number, number, number];

export const EGA: RGB[] = [
  [0, 0, 42], [0, 42, 0], [0, 42, 42], [42, 0, 0], [42, 0, 42],
  [42, 21, 0], [42, 42, 42], [21, 21, 21], [21, 21, 63], [21, 63, 21],
  [21, 63, 63], [63, 21, 21], [63, 21, 63], [63, 63, 21], [63, 63, 63]];
export const PLAYER_RAMP: Array<[RGB, RGB]> = [
  [[16, 4, 4], [63, 26, 26]], [[4, 8, 20], [26, 38, 63]],
  [[4, 18, 6], [26, 56, 26]], [[20, 16, 4], [63, 58, 20]]];
export const TERRAIN_RAMP: Array<[RGB, RGB]> = [
  [[24, 14, 6], [46, 34, 18]], [[44, 40, 26], [18, 18, 20]],
  [[20, 20, 22], [40, 40, 42]], [[6, 10, 30], [22, 34, 54]],
  [[40, 32, 4], [63, 58, 26]], [[0, 0, 0], [30, 30, 30]]];
export const UI: RGB[] = [
  [0, 0, 0], [10, 10, 12], [20, 20, 24], [30, 30, 34], [42, 42, 46],
  [52, 52, 56], [63, 63, 63], [63, 52, 20], [52, 20, 20], [20, 52, 20],
  [20, 20, 52], [40, 40, 10], [30, 8, 8], [8, 30, 8], [8, 8, 30],
  [32, 32, 32]];

const FONT_HEX =
  '000000000000000008080808080008000000000000000000143e14143e14000000000000'
  + '000000003234081026060000000000000000000000000000000000000408101010080400'
  + '100804040408100000000000000000000008083e0808000000000000181810000000003e'
  + '00000000000000000018180002020408102020001c22262a32221c000818080808081c00'
  + '1c22020408103e003c02021c02023c00040c14243e0404003e203c0202221c000c10203c'
  + '22221c003e020408101010001c22221c22221c001c22221e020418000018180018180000'
  + '00000000000000000000000000000000000000000000000000000000000000001c220204'
  + '0800080000000000000000001c22223e222222003c22223c22223c001c22202020221c00'
  + '3c22222222223c003e20203c20203e003e20203c202020001c22202e22221c002222223e'
  + '222222001c08080808081c000e0404040424180022242830282422002020202020203e00'
  + '22362a2a2222220022322a2a262222001c22222222221c003c22223c202020001c222222'
  + '2a241a003c22223c282422001e20201c02023c003e080808080808002222222222221c00'
  + '22222222221408002222222a2a362200222214081422220022221408080808003e020408'
  + '10203e000000000000000000000000000000000000000000000000000000000000000000'
  + '000000000000000000000000000000000000000000000000000000000000000000000000'
  + '000000000000000000000000000000000000000000000000000000000000000000000000'
  + '000000000000000000000000000000000000000000000000000000000000000000000000'
  + '000000000000000000000000000000000000000000000000000000000000000000000000'
  + '000000000000000000000000000000000000000000000000000000000000000000000000'
  + '000000000000000000000000000000000000000000000000000000000000000000000000'
  + '000000000000000000000000000000000000000000000000000000000000000000000000'
  + '00000000';

export const FONT: number[] = (() => {
  const out: number[] = [];
  for (let k = 0; k < FONT_HEX.length / 2; k += 1) {
    out.push(parseInt(FONT_HEX.slice(k * 2, k * 2 + 2), 16));
  }
  return out;
})();
export const FONT_W = 6;
export const FONT_H = 8;
export const FONT_ADV = 6;
export const FONT_FIRST = 32;

// ── SPEC §22.2 팔레트 ───────────────────────────────────────────────────────
// 두 끝색 사이의 정수 보간. 나눗셈은 내림이다.
export function ramp(c0: RGB, c1: RGB, i: number): RGB {
  return [c0[0] + F.floordiv((c1[0] - c0[0]) * i, 7),
          c0[1] + F.floordiv((c1[1] - c0[1]) * i, 7),
          c0[2] + F.floordiv((c1[2] - c0[2]) * i, 7)];
}

export function buildPalette(): RGB[] {
  const pal: RGB[] = [];
  for (let i = 0; i < 256; i += 1) pal.push([0, 0, 0]);
  for (let k = 0; k < 15; k += 1) pal[1 + k] = EGA[k];
  for (let i = 0; i < 16; i += 1) {
    const g = F.floordiv(i * 63, 15);
    pal[16 + i] = [g, g, g];
  }
  for (let p = 0; p < 4; p += 1) {
    const [c0, c1] = PLAYER_RAMP[p];
    for (let i = 0; i < PLAYER_SHADES; i += 1) {
      pal[PLAYER_BASE + p * PLAYER_SHADES + i] = ramp(c0, c1, i);
    }
  }
  for (let i = 0; i < 16; i += 1) pal[192 + i] = UI[i];
  for (let r = 0; r < 6; r += 1) {
    const [c0, c1] = TERRAIN_RAMP[r];
    for (let i = 0; i < 8; i += 1) pal[208 + r * 8 + i] = ramp(c0, c1, i);
  }
  return pal;
}

// 명암 단계 l 에서 색 c 에 가장 가까운 항목. 동점이면 인덱스 최소.
// 256 × 256 × 4 = 262,144회 비교이며 **시작할 때 한 번**이다. 안개(§14.4)가
// 이 표를 쓴다 — 안개 때문에 색 계산을 하지 않으려고 표로 미리 굳힌다.
export function buildLight(pal: RGB[]): number[][] {
  const out: number[][] = [];
  for (let l = 0; l < 4; l += 1) {
    const row = new Array<number>(256).fill(0);
    for (let c = 0; c < 256; c += 1) {
      const wr = F.floordiv(pal[c][0] * l, 3);
      const wg = F.floordiv(pal[c][1] * l, 3);
      const wb = F.floordiv(pal[c][2] * l, 3);
      let best = 0;
      let bd = -1;
      for (let j = 0; j < 256; j += 1) {
        const dr = pal[j][0] - wr;
        const dg = pal[j][1] - wg;
        const db = pal[j][2] - wb;
        const d = dr * dr + dg * dg + db * db;
        if (bd < 0 || d < bd) {
          bd = d;
          best = j;
        }
      }
      row[c] = best;
    }
    out.push(row);
  }
  return out;
}

// ── SPEC §22.6 팔레트 사이클링 ──────────────────────────────────────────────
// 물 색 8칸을 한 칸씩 돌린다. **프레임버퍼는 건드리지 않는다** —
// 팔레트 모드의 가장 큰 장점이었던 공짜 애니메이션이다.
export function cycleWater(pal: RGB[], phase: number): RGB[] {
  const out = pal.slice();
  for (let i = 0; i < WATER_N; i += 1) {
    out[WATER_BASE + i] = pal[WATER_BASE + F.fmod(i + phase, WATER_N)];
  }
  return out;
}

// ── SPEC §22.3 스프라이트 ───────────────────────────────────────────────────
export class Sprite {
  w: number;
  h: number;
  ox: number;
  oy: number;
  data: number[];

  constructor(w: number, h: number, ox: number, oy: number, data: number[]) {
    this.w = w;
    this.h = h;
    this.ox = ox;
    this.oy = oy;
    this.data = data;
  }

  pixels(): number[] {
    const out: number[] = [];
    const d = this.data;
    let i = 0;
    while (i < d.length) {
      for (let k = 0; k < d[i]; k += 1) out.push(d[i + 1]);
      i += 2;
    }
    return out;
  }
}

function rle(px: number[]): number[] {
  const out: number[] = [];
  let i = 0;
  while (i < px.length) {
    const v = px[i];
    let run = 1;
    while (i + run < px.length && px[i + run] === v && run < 255) run += 1;
    out.push(run);
    out.push(v);
    i += run;
  }
  return out;
}

// §6.2 의 행 span 으로 원을 채운다 — 곱셈도 제곱근도 쓰지 않는다.
function disc(px: number[], w: number, cx: number, cy: number, r: number,
              colour: number, onlyBelow = false, onlyEmpty = false): void {
  const sp = CI.spans(r);
  const h = Math.floor(px.length / w);
  for (let dy = -r; dy <= r; dy += 1) {
    if (onlyBelow && dy < 0) continue;
    const wdt = sp[dy >= 0 ? dy : -dy];
    const y = cy + dy;
    for (let dx = -wdt; dx <= wdt; dx += 1) {
      const x = cx + dx;
      if (x >= 0 && x < w && y >= 0 && y < h) {
        if (onlyEmpty && px[y * w + x] !== 0) continue;
        px[y * w + x] = colour;
      }
    }
  }
}

export function unitSprite(k: number, d: number): Sprite {
  const w = C.TILE;
  const h = C.TILE;
  const px = new Array<number>(w * h).fill(0);
  const r = UNIT_R[k];
  disc(px, w, 8, 9, r, PLAYER_BASE + 1);            // 테두리
  disc(px, w, 8, 9, r - 1, PLAYER_BASE + 3);        // 속
  disc(px, w, 8, 14, 3, SHADOW, true, true);        // 그림자 (아래 절반, 빈 곳만)
  const mx = 8 + F.DX[d] * UNIT_M[k];
  const my = 9 + F.DY[d] * UNIT_M[k];
  for (let y = my; y < my + 2; y += 1) {
    for (let x = mx; x < mx + 2; x += 1) {
      if (x >= 0 && x < w && y >= 0 && y < h) px[y * w + x] = PLAYER_BASE + 6;
    }
  }
  return new Sprite(w, h, 8, 14, rle(px));
}

export function buildingSprite(foot: number): Sprite {
  const w = C.TILE * foot;
  const h = C.TILE * foot;
  const px = new Array<number>(w * h).fill(0);
  for (let y = 4; y < h - 2; y += 1) {
    for (let x = 2; x < w - 2; x += 1) {
      const edge = (x === 2 || x === w - 3 || y === 4 || y === h - 3);
      px[y * w + x] = PLAYER_BASE + (edge ? 5 : 2);
    }
  }
  for (let y = 4; y < 7; y += 1) {
    for (let x = 2; x < w - 2; x += 1) px[y * w + x] = PLAYER_BASE + 6;  // 지붕
  }
  for (let y = h - 6; y < h - 2; y += 1) {
    for (let x = Math.floor(w / 2) - 2; x < Math.floor(w / 2) + 2; x += 1) {
      px[y * w + x] = PLAYER_BASE;                                       // 문
    }
  }
  return new Sprite(w, h, Math.floor(w / 2), h - 2, rle(px));
}

export const SPRITES: Record<string, Sprite> = (() => {
  const out: Record<string, Sprite> = {};
  for (let k = 0; k < 5; k += 1) {
    for (let d = 0; d < DRAWN_DIRS; d += 1) {
      out[UNIT_NAME[k] + '_' + d] = unitSprite(k, d);
    }
  }
  for (const [kind, name] of BLD_NAME) out[name] = buildingSprite(C.FOOT[kind]);
  return out;
})();

// §22.7 — 그린 것은 5방향뿐이다. (스프라이트, 반전 여부).
export function spriteFor(kind: number, d: number): [Sprite | null, boolean] {
  if (C.IS_BUILDING[kind] !== 0) {
    for (const [k, name] of BLD_NAME) {
      if (k === kind) return [SPRITES[name], false];
    }
    return [null, false];
  }
  if (d <= 4) return [SPRITES[UNIT_NAME[kind] + '_' + d], false];
  return [SPRITES[UNIT_NAME[kind] + '_' + (8 - d)], true];
}

// ── SPEC §22.1 프레임버퍼 ───────────────────────────────────────────────────
export class Frame {
  w: number;
  h: number;
  fb: number[];

  constructor(w = C.SCR_W, h = C.SCR_H) {
    this.w = w;
    this.h = h;
    this.fb = new Array<number>(w * h).fill(0);
  }

  clear(v = 0): void {
    for (let i = 0; i < this.fb.length; i += 1) this.fb[i] = v;
  }

  rect(x: number, y: number, w: number, h: number, v: number): void {
    for (let j = Math.max(0, y); j < Math.min(this.h, y + h); j += 1) {
      const row = j * this.w;
      for (let i = Math.max(0, x); i < Math.min(this.w, x + w); i += 1) {
        this.fb[row + i] = v;
      }
    }
  }
}

// ── SPEC §22.4 클리핑 블릿 ──────────────────────────────────────────────────
// 런 단위로 자른다 — 픽셀마다 경계를 검사하지 않는다 (정리 22.1).
// 완전히 화면 밖이면 런을 하나도 훑지 않고 돌아간다.
export function blit(fb: number[], spr: Sprite, x: number, y: number,
                     owner = 0, flip = false, light: number[][] | null = null,
                     level = 3): void {
  // 반전해도 상자 자체는 그대로 두고 상자 **안에서** 뒤집는다. 기준점은
  // (w - 1 - 2*ox) 픽셀만큼 옮겨지는데(폭 16·ox 8 이면 1px), 세 언어가
  // 같은 자리에 그리는 것이 그 1px 보다 중요하다.
  const x0 = x - spr.ox;
  const y0 = y - spr.oy;
  if (x0 + spr.w <= 0 || x0 >= C.SCR_W || y0 + spr.h <= 0 || y0 >= C.SCR_H) {
    return;
  }
  const add = owner * PLAYER_SHADES;
  const d = spr.data;
  let i = 0;
  let pos = 0;
  while (i < d.length) {
    const run = d[i];
    const val = d[i + 1];
    i += 2;
    if (val === 0) {                              // 컬러키 — 통째로 건너뛴다
      pos += run;
      continue;
    }
    let colour = (val >= PLAYER_BASE && val < PLAYER_BASE + PLAYER_SHADES)
      ? val + add : val;
    if (light !== null && level < 3) colour = light[level][colour];
    let p = pos;
    const end = pos + run;
    while (p < end) {
      const sy = F.floordiv(p, spr.w);
      const sx = F.fmod(p, spr.w);
      let n = end - p;
      if (n > spr.w - sx) n = spr.w - sx;         // 이 줄에 걸치는 만큼만
      const fy = y0 + sy;
      if (fy >= 0 && fy < C.SCR_H) {
        const fx = flip ? x0 + (spr.w - 1 - (sx + n - 1)) : x0 + sx;
        const a = fx > 0 ? fx : 0;
        let b = fx + n;
        if (b > C.SCR_W) b = C.SCR_W;
        const row = fy * C.SCR_W;
        for (let q = a; q < b; q += 1) fb[row + q] = colour;
      }
      p += n;
    }
    pos = end;
  }
}

// ── SPEC §22.8 폰트 ─────────────────────────────────────────────────────────
// 6×8 칸에 5×7 획. 소문자는 빈 글자다(§22.8).
export function text(fb: number[], s: string, x0: number, y: number,
                     colour: number): void {
  let x = x0;
  for (const ch of s) {
    const code = ch.charCodeAt(0);
    if (code >= FONT_FIRST && code < FONT_FIRST + 95) {
      const base = (code - FONT_FIRST) * FONT_H;
      for (let j = 0; j < FONT_H; j += 1) {
        const v = FONT[base + j];
        const fy = y + j;
        if (!(fy >= 0 && fy < C.SCR_H)) continue;
        for (let k = 0; k < FONT_W; k += 1) {
          if (F.fmod(F.floordiv(v, F.pow2(5 - k)), 2) === 1) {
            const fx = x + k;
            if (fx >= 0 && fx < C.SCR_W) fb[fy * C.SCR_W + fx] = colour;
          }
        }
      }
    }
    x += FONT_ADV;
  }
}

// ── SPEC §22.9 더티 렉트 ────────────────────────────────────────────────────
// 8개를 넘으면 전체를 다시 그린다 — 합치는 비용이 이득을 넘는 지점이다.
export class Dirty {
  static MAX = 8;
  private r: Array<[number, number, number, number]>;

  constructor() {
    this.r = [];
  }

  add(x: number, y: number, w: number, h: number): void {
    this.r.push([x, y, w, h]);
  }

  rects(): Array<[number, number, number, number]> {
    if (this.r.length > Dirty.MAX) return [[0, 0, C.SCR_W, C.SCR_H]];
    return this.r.slice();
  }

  clear(): void {
    this.r = [];
  }
}

// ── SPEC §22.10 PPM ─────────────────────────────────────────────────────────
// 0…63 을 0…255 로. v*255/63 이 아니라 곱셈·나눗셈 하나씩이다.
export function expand(v: number): number {
  return v * 4 + F.floordiv(v, 16);
}

export function toPpm(fb: number[], pal: RGB[]): number[] {
  const out: number[] = [];
  const head = 'P6\n' + C.SCR_W + ' ' + C.SCR_H + '\n255\n';
  for (const ch of head) out.push(ch.charCodeAt(0));
  const lut: number[] = [];
  for (const c of pal) {
    lut.push(expand(c[0]));
    lut.push(expand(c[1]));
    lut.push(expand(c[2]));
  }
  for (const v of fb) {
    const j = v * 3;
    out.push(lut[j]);
    out.push(lut[j + 1]);
    out.push(lut[j + 2]);
  }
  return out;
}

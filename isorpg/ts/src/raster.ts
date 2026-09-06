// 래스터 — SPEC §7. 320x200 8비트 인덱스 프레임버퍼.
//
// 모드 13h 를 그대로 흉내 낸다. 프레임버퍼는 Uint8Array 다 — 파이썬의 bytearray,
// 루아의 1-기반 정수 테이블과 같은 자리다. 다만 Uint8Array 는 범위를 벗어난
// 대입을 예외 없이 256으로 접어 버리므로, 넣는 값이 팔레트 인덱스(0..255)임을
// 넣기 전에 보장해야 한다. 감싸기는 버그를 숨기지 없애지 않는다.
import * as fs from 'fs';
import * as path from 'path';

export const SCR_W = 320;
export const SCR_H = 200;
export const PAL_SIZE = 256;
export const LIGHT_LEVELS = 16;
export const DAC_MAX = 63;

export const WATER_LO = 16;
export const WATER_HI = 31;

// dist/src -> dist -> ts -> isorpg. node dist/src/main.js 를 ts/ 에서 돌리든
// 다른 데서 돌리든 같은 곳을 가리켜야 하므로 cwd 가 아니라 __dirname 을 쓴다.
export const ROOT = path.resolve(__dirname, '..', '..', '..');
export const GOLDEN = path.join(ROOT, 'golden');

export type Rgb = [number, number, number];

/** golden/palette.txt 의 내용을 판다. 파일 읽기와 나눠 둔 것은 브라우저 때문이다 —
 *  덱 안에서 도는 미니 RPG 는 같은 문자열을 소스에 박아 넣고 이 함수만 부른다. */
export function parsePalette(raw: string): Rgb[] {
  const text = raw.trim().split('\n');
  const head = (text[0] as string).split(/\s+/);
  if (head[0] !== 'ISORPG-PAL') throw new Error('팔레트 매직이 다르다: ' + head[0]);
  const pal: Rgb[] = [];
  for (let i = 1; i < text.length; i++) {
    const q = (text[i] as string).split(/\s+/);
    pal.push([
      parseInt(q[1] as string, 10),
      parseInt(q[2] as string, 10),
      parseInt(q[3] as string, 10),
    ]);
  }
  if (pal.length !== PAL_SIZE) throw new Error('팔레트가 ' + pal.length + '색');
  return pal;
}

/** golden/palette.txt -> [r,g,b] 256개. 값은 6비트 DAC (0..63). */
export function loadPalette(p?: string): Rgb[] {
  return parsePalette(fs.readFileSync(p ?? path.join(GOLDEN, 'palette.txt'), 'utf8'));
}

/** 명암표 16 x 256. LIGHT[l*256 + c] = 색 c 를 l/15 로 어둡게 한 것에 가장 가까운 색.
 *
 *  16 * 256 * 256 = 1,048,576 번의 거리 계산 — 시작할 때 한 번뿐이다.
 *  동점이면 인덱스가 작은 쪽을 고른다(`d < bd` 이므로 먼저 본 것이 이긴다).
 *  `<=` 로 바꾸면 파이썬과 다른 표가 나오고 렌더 파리티가 그 자리에서 깨진다. */
export function buildLight(pal: Rgb[]): number[] {
  const tbl: number[] = new Array<number>(LIGHT_LEVELS * PAL_SIZE).fill(0);
  for (let l = 0; l < LIGHT_LEVELS; l++) {
    for (let c = 0; c < PAL_SIZE; c++) {
      const src = pal[c] as Rgb;
      const tr = Math.floor((src[0] * l) / (LIGHT_LEVELS - 1));
      const tg = Math.floor((src[1] * l) / (LIGHT_LEVELS - 1));
      const tb = Math.floor((src[2] * l) / (LIGHT_LEVELS - 1));
      let best = 0;
      let bd = 1073741824;
      for (let k = 0; k < PAL_SIZE; k++) {
        const q = pal[k] as Rgb;
        const dr = q[0] - tr;
        const dg = q[1] - tg;
        const db = q[2] - tb;
        const d = dr * dr + dg * dg + db * db;
        if (d < bd) {
          bd = d;
          best = k;
          if (d === 0) break;
        }
      }
      tbl[l * PAL_SIZE + c] = best;
    }
  }
  return tbl;
}

export type Run = [number, number]; // [개수, 색]

export class Sprite {
  constructor(
    readonly name: string,
    readonly w: number,
    readonly h: number,
    readonly ox: number,
    readonly oy: number,
    readonly rows: Run[][],
  ) {}
}

/** golden/tiles.rle 의 내용을 판다. 색 0 은 투명. */
export function parseSprites(raw: string): Sprite[] {
  const lines = raw.replace(/\n+$/, '').split('\n');
  const head = (lines[0] as string).split(/\s+/);
  if (head[0] !== 'ISORPG-TILES') throw new Error('스프라이트 매직이 다르다: ' + head[0]);
  const out: Sprite[] = [];
  let i = 1;
  while (i < lines.length) {
    const q = (lines[i] as string).split(/\s+/);
    const name = q[2] as string;
    const w = parseInt(q[3] as string, 10);
    const h = parseInt(q[4] as string, 10);
    const ox = parseInt(q[5] as string, 10);
    const oy = parseInt(q[6] as string, 10);
    i += 1;
    const rows: Run[][] = [];
    for (let k = 0; k < h; k++) {
      const runs: Run[] = [];
      let total = 0;
      for (const tok of (lines[i + k] as string).split(/\s+/)) {
        const ab = tok.split(':');
        const a = parseInt(ab[0] as string, 10);
        const b = parseInt(ab[1] as string, 10);
        runs.push([a, b]);
        total += a;
      }
      if (total !== w) {
        throw new Error(name + ' 의 ' + k + '행 런 합이 ' + total + ' (폭 ' + w + ')');
      }
      rows.push(runs);
    }
    i += h;
    out.push(new Sprite(name, w, h, ox, oy, rows));
  }
  const want = parseInt(head[2] as string, 10);
  if (out.length !== want) {
    throw new Error('스프라이트 개수가 ' + want + ' 여야 하는데 ' + out.length);
  }
  return out;
}

/** golden/tiles.rle 을 읽는다. */
export function loadSprites(p?: string): Sprite[] {
  return parseSprites(fs.readFileSync(p ?? path.join(GOLDEN, 'tiles.rle'), 'utf8'));
}

let _lightCache: number[] | null = null;

/** 기본 명암표. 만드는 데 시간이 걸리므로 한 번만 만들어 둔다. */
export function getLight(): number[] {
  if (_lightCache === null) _lightCache = buildLight(loadPalette());
  return _lightCache;
}

/** 명암표를 밖에서 넣는다. 브라우저에는 파일이 없어 팔레트를 읽을 수 없기 때문이다. */
export function setLight(tbl: number[]): void {
  _lightCache = tbl;
}

/** 프레임버퍼 하나. Uint8Array 가 곧 모드 13h 의 A000 세그먼트다. */
export class Frame {
  fb: Uint8Array;
  light: number[];

  constructor(light?: number[]) {
    this.fb = new Uint8Array(SCR_W * SCR_H);
    this.light = light ?? getLight();
  }

  clear(c = 0): void {
    this.fb.fill(c);
  }

  px(x: number, y: number): number {
    return this.fb[y * SCR_W + x] as number;
  }

  /** 런 단위로 자르며 그린다. 픽셀마다 조건을 걸지 않는 것이 도스식이다.
   *
   *  세로는 행 통째로 건너뛰고, 가로는 런 하나를 [a,b) 로 잘라 채운다.
   *  Uint8Array.fill(v, a, b) 이 그 자리를 그대로 옮긴 것이라 루프보다 빠르다. */
  blitRle(spr: Sprite, x: number, y: number, level = 15): void {
    const light = this.light;
    const fb = this.fb;
    const top = y - spr.oy;
    const left = x - spr.ox;
    const rows = spr.rows;
    for (let r = 0; r < spr.h; r++) {
      const py = top + r;
      if (py < 0 || py >= SCR_H) continue;
      const base = py * SCR_W;
      let px = left;
      for (const run of rows[r] as Run[]) {
        const count = run[0];
        const color = run[1];
        if (color) {
          const a = px > 0 ? px : 0;
          let b = px + count;
          if (b > SCR_W) b = SCR_W;
          if (a < b) {
            const v = light[level * PAL_SIZE + color] as number;
            fb.fill(v, base + a, base + b);
          }
        }
        px += count;
        if (px >= SCR_W) break;
      }
    }
  }
}

export type Rect = [number, number, number, number];

/** 더티 렉트 — 바뀐 곳만 다시 올리기 위한 사각형 목록. */
export class Dirty {
  rects: Rect[] = [];

  add(x0: number, y0: number, w0: number, h0: number): void {
    let x = x0;
    let y = y0;
    let w = w0;
    let h = h0;
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > SCR_W) w = SCR_W - x;
    if (y + h > SCR_H) h = SCR_H - y;
    if (w > 0 && h > 0) this.rects.push([x, y, w, h]);
  }

  /** 겹치거나 맞닿은 사각형을 합친다. 낭비가 1.5배를 넘으면 그냥 둔다.
   *  마지막 정렬은 (y, x) 오름차순 — 동점에도 순서가 흔들리지 않도록
   *  w, h 까지 비교에 넣는다. JS 의 sort 는 안정 정렬이지만 기대지 않는다. */
  merge(): Rect[] {
    let changed = true;
    while (changed) {
      changed = false;
      const out: Rect[] = [];
      const used: boolean[] = new Array<boolean>(this.rects.length).fill(false);
      for (let i = 0; i < this.rects.length; i++) {
        if (used[i]) continue;
        const ri = this.rects[i] as Rect;
        let x = ri[0];
        let y = ri[1];
        let w = ri[2];
        let h = ri[3];
        for (let j = i + 1; j < this.rects.length; j++) {
          if (used[j]) continue;
          const rj = this.rects[j] as Rect;
          const x2 = rj[0];
          const y2 = rj[1];
          const w2 = rj[2];
          const h2 = rj[3];
          if (x + w < x2 || x2 + w2 < x || y + h < y2 || y2 + h2 < y) continue;
          const nx = x < x2 ? x : x2;
          const ny = y < y2 ? y : y2;
          const nr = x + w > x2 + w2 ? x + w : x2 + w2;
          const nb = y + h > y2 + h2 ? y + h : y2 + h2;
          if ((nr - nx) * (nb - ny) * 2 <= (w * h + w2 * h2) * 3) {
            x = nx; y = ny; w = nr - nx; h = nb - ny;
            used[j] = true;
            changed = true;
          }
        }
        used[i] = true;
        out.push([x, y, w, h]);
      }
      this.rects = out;
    }
    this.rects.sort((a, b) => (a[1] - b[1]) || (a[0] - b[0]) || (a[2] - b[2]) || (a[3] - b[3]));
    return this.rects;
  }
}

/** 물 램프 구간만 왼쪽으로 n 칸 돌린다. 프레임버퍼는 건드리지 않는다. */
export function cyclePalette(pal: Rgb[], n: number): Rgb[] {
  const span = WATER_HI - WATER_LO + 1;
  const k = n - span * Math.floor(n / span);
  const out: Rgb[] = pal.slice();
  for (let i = 0; i < span; i++) {
    out[WATER_LO + i] = pal[WATER_LO + ((i + k) % span)] as Rgb;
  }
  return out;
}

/** 6비트 DAC -> 8비트. v*4 + v/16 이라 0 -> 0, 63 -> 255 가 정확히 맞는다. */
export function expand6(v: number): number {
  return v * 4 + Math.floor(v / 16);
}

/** P6 PPM. 머리말 15바이트 + 192,000바이트 = 192,015바이트. */
export function toPpm(fb: Uint8Array, pal: Rgb[]): Uint8Array {
  const lut = new Uint8Array(PAL_SIZE * 3);
  for (let i = 0; i < PAL_SIZE; i++) {
    const c = pal[i] as Rgb;
    lut[i * 3] = expand6(c[0]);
    lut[i * 3 + 1] = expand6(c[1]);
    lut[i * 3 + 2] = expand6(c[2]);
  }
  const header = 'P6\n320 200\n255\n';
  const out = new Uint8Array(header.length + SCR_W * SCR_H * 3);
  for (let i = 0; i < header.length; i++) out[i] = header.charCodeAt(i);
  let j = header.length;
  for (let i = 0; i < SCR_W * SCR_H; i++) {
    const c = (fb[i] as number) * 3;
    out[j] = lut[c] as number;
    out[j + 1] = lut[c + 1] as number;
    out[j + 2] = lut[c + 2] as number;
    j += 3;
  }
  return out;
}

// 렌더링 — SPEC §10
//
// Uint8Array 하나가 화면 전부다. 도스에서 A000:0000 이 가리키던 그 64KB 와
// 같은 모양이고, 크기도 320*200 = 64,000 바이트로 똑같다.

import * as fs from 'fs';
import * as path from 'path';

import * as F from './font';
import { Game } from './game';
import { FOG_EXPLORED, FOG_HIDDEN, MAP_H, MAP_W, TERRAIN_MASK } from './hexmap';
import { MSG, PANEL_RECT, SCR_H, SCR_W, VIEW } from './layout';
import * as PK from './picker';
import { fnv1a } from './rng';
import { Kind, Ui } from './ui';
import { KINDS, NO_UNIT, Unit } from './units';

export { CAM_MAX_X, CAM_MAX_Y, MAP_PX_H, MAP_PX_W, MSG, PANEL_RECT, SCR_H, SCR_W, VIEW } from './layout';

export const TILE_NAME = ['t_clear', 't_forest', 't_hill', 't_mountain',
                          't_city', 't_river', 't_swamp', 't_sea'] as const;
export const MINI_COLOR = [24, 38, 56, 72, 120, 88, 104, 84] as const;

export interface Sprite { w: number; h: number; data: Uint8Array; }
export type Rect = readonly [number, number, number, number];

function goldenDir(): string {
  return process.env['HEXWAR_GOLDEN'] ?? path.join(__dirname, '..', '..', '..', 'golden');
}

export function loadPalette(p?: string): Array<[number, number, number]> {
  const file = p ?? path.join(goldenDir(), 'palette.txt');
  const out: Array<[number, number, number]> = [];
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    const s = line.trim();
    if (s) {
      const [r, g, b] = s.split(/\s+/).map(Number) as [number, number, number];
      out.push([r, g, b]);
    }
  }
  return out;
}

export function loadSprites(p?: string): Map<string, Sprite> {
  const file = p ?? path.join(goldenDir(), 'tiles.rle');
  const sprites = new Map<string, Sprite>();
  let name = '', w = 0, h = 0, need = 0, pos = 0;
  let buf = new Uint8Array(0);
  for (const raw of fs.readFileSync(file, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith(';')) continue;
    if (need === 0) {
      const parts = line.split(/\s+/);
      name = parts[0]!;
      w = Number(parts[1]);
      h = Number(parts[2]);
      buf = new Uint8Array(w * h);
      need = w * h;
      pos = 0;
      continue;
    }
    const nums = line.split(/\s+/).map(Number);
    for (let i = 0; i < nums.length; i += 2) {
      const c = nums[i]!, v = nums[i + 1]!;
      buf.fill(v, pos, pos + c);
      pos += c;
      need -= c;
    }
    if (need === 0) sprites.set(name, { w, h, data: buf });
  }
  return sprites;
}

export class Framebuffer {
  readonly data: Uint8Array;

  constructor(readonly w = SCR_W, readonly h = SCR_H) {
    this.data = new Uint8Array(w * h);
  }

  clear(v = 0): void { this.data.fill(v); }

  fillRect(x: number, y: number, w: number, h: number, v: number): void {
    const x0 = Math.max(0, x), y0 = Math.max(0, y);
    const x1 = Math.min(this.w, x + w), y1 = Math.min(this.h, y + h);
    for (let yy = y0; yy < y1; yy++) {
      this.data.fill(v, yy * this.w + x0, yy * this.w + x1);
    }
  }

  frameRect(x: number, y: number, w: number, h: number, v: number): void {
    this.fillRect(x, y, w, 1, v);
    this.fillRect(x, y + h - 1, w, 1, v);
    this.fillRect(x, y, 1, h, v);
    this.fillRect(x + w - 1, y, 1, h, v);
  }

  // 인덱스 0을 건너뛰는 마스크 블릿. 클리핑은 루프 범위를 미리 잘라서 한다.
  blit(sp: Sprite, x: number, y: number, clip?: Rect): void {
    const [cx, cy, cw, ch] = clip ?? [0, 0, this.w, this.h];
    const x0 = Math.max(x, cx), y0 = Math.max(y, cy);
    const x1 = Math.min(x + sp.w, cx + cw), y1 = Math.min(y + sp.h, cy + ch);
    if (x0 >= x1 || y0 >= y1) return;
    const src = sp.data, dst = this.data;
    for (let yy = y0; yy < y1; yy++) {
      const srow = (yy - y) * sp.w - x;
      const drow = yy * this.w;
      for (let xx = x0; xx < x1; xx++) {
        const v = src[srow + xx]!;
        if (v !== 0) dst[drow + xx] = v;
      }
    }
  }

  text(s: string, x: number, y: number, color: number, clip?: Rect): void {
    const [cx, cy, cw, ch] = clip ?? [0, 0, this.w, this.h];
    for (let k = 0; k < s.length; k++) {
      const gx = x + k * F.ADV;
      const rows = F.rows(s[k]!);
      for (let ry = 0; ry < F.FH; ry++) {
        const bits = rows[ry]!;
        if (bits === 0) continue;
        const py = y + ry;
        if (py < cy || py >= cy + ch) continue;
        const base = py * this.w;
        for (let bx = 0; bx < F.FW; bx++) {
          if ((bits & (1 << (F.FW - 1 - bx))) !== 0) {
            const px = gx + bx;
            if (px >= cx && px < cx + cw) this.data[base + px] = color;
          }
        }
      }
    }
  }

  toPpm(pal: Array<[number, number, number]>): Uint8Array {
    const head = Buffer.from(`P6\n${this.w} ${this.h}\n255\n`, 'ascii');
    const lut = new Uint8Array(256 * 3);
    for (let i = 0; i < pal.length; i++) {
      const c = pal[i]!;
      lut[i * 3] = Math.floor((c[0] * 255) / 63);
      lut[i * 3 + 1] = Math.floor((c[1] * 255) / 63);
      lut[i * 3 + 2] = Math.floor((c[2] * 255) / 63);
    }
    const body = new Uint8Array(this.w * this.h * 3);
    for (let i = 0; i < this.data.length; i++) {
      const v = this.data[i]! * 3;
      body[i * 3] = lut[v]!;
      body[i * 3 + 1] = lut[v + 1]!;
      body[i * 3 + 2] = lut[v + 2]!;
    }
    const out = new Uint8Array(head.length + body.length);
    out.set(head, 0);
    out.set(body, head.length);
    return out;
  }
}

// 더티 사각형 — SPEC §10.3
export class Dirty {
  rects: Array<[number, number, number, number]> = [];

  add(x: number, y: number, w: number, h: number): void {
    if (w <= 0 || h <= 0) return;
    const nr: [number, number, number, number] = [x, y, x + w, y + h];
    for (const r of this.rects) {
      const ux0 = Math.min(r[0], nr[0]), uy0 = Math.min(r[1], nr[1]);
      const ux1 = Math.max(r[2], nr[2]), uy1 = Math.max(r[3], nr[3]);
      const ua = (ux1 - ux0) * (uy1 - uy0);
      const a = (r[2] - r[0]) * (r[3] - r[1]) + (nr[2] - nr[0]) * (nr[3] - nr[1]);
      if (a * 2 > ua) {
        r[0] = ux0; r[1] = uy0; r[2] = ux1; r[3] = uy1;
        return;
      }
    }
    this.rects.push(nr);
  }

  area(): number {
    return this.rects.reduce((s, r) => s + (r[2] - r[0]) * (r[3] - r[1]), 0);
  }

  clear(): void { this.rects = []; }
}

export class Renderer {
  readonly fb = new Framebuffer();
  readonly pal = loadPalette();
  readonly sp = loadSprites();
  readonly dirty = new Dirty();
  private readonly nbd = new Int32Array(6);
  private readonly nbi = new Int32Array(6);

  private sprite(name: string): Sprite {
    const s = this.sp.get(name);
    if (!s) throw new Error(`스프라이트 없음: ${name}`);
    return s;
  }

  visibleRows(camY: number): [number, number] {
    const top = Math.floor((camY - (PK.HEX_H - PK.ROW_STEP)) / PK.ROW_STEP);
    const bot = Math.floor((camY + VIEW[3]) / PK.ROW_STEP) + 1;
    return [Math.max(0, top), Math.min(MAP_H - 1, bot)];
  }

  private drawRoads(g: Game, i: number, x: number, y: number): void {
    const k = g.map.neighborsWithDir(i, this.nbd, this.nbi);
    for (let j = 0; j < k; j++) {
      if ((g.map.cells[this.nbi[j]!]! & 0x80) !== 0) {
        this.fb.blit(this.sprite(`road${this.nbd[j]!}`), x, y, VIEW);
      }
    }
  }

  private drawUnit(u: Unit, x: number, y: number): void {
    this.fb.blit(this.sprite(`u${u.side}_${u.kind}`), x + 8, y + 8, VIEW);
    const w = Math.max(0, Math.floor((u.hp * 12) / 10));
    this.fb.fillRect(x + 10, y + 25, 12, 2, 8);
    this.fb.fillRect(x + 10, y + 25, w, 2, u.hp > 5 ? 10 : 12);
  }

  drawMap(g: Game, ui: Ui): void {
    const fb = this.fb, m = g.map;
    fb.fillRect(VIEW[0], VIEW[1], VIEW[2], VIEW[3], 0);
    const [r0, r1] = this.visibleRows(ui.camY);
    for (let row = r0; row <= r1; row++) {
      for (let col = 0; col < MAP_W; col++) {
        const [ox, oy] = PK.hexOrigin(col, row);
        const x = ox - ui.camX, y = oy - ui.camY;
        if (x <= -PK.HEX_W || x >= VIEW[2] || y <= -PK.HEX_H || y >= VIEW[3]) continue;
        const i = row * MAP_W + col;
        const fog = m.fog[i]!;
        if (fog === FOG_HIDDEN) {
          fb.blit(this.sprite('ov_black'), x, y, VIEW);
          continue;
        }
        fb.blit(this.sprite(TILE_NAME[m.cells[i]! & TERRAIN_MASK]!), x, y, VIEW);
        if ((m.cells[i]! & 0x80) !== 0) this.drawRoads(g, i, x, y);
        if (fog === FOG_EXPLORED) {
          fb.blit(this.sprite('ov_dim'), x, y, VIEW);
          continue;
        }
        if (ui.objectiveIdx.has(i)) fb.blit(this.sprite('ov_obj'), x, y, VIEW);
        if (ui.moveOverlay.has(i)) fb.blit(this.sprite('ov_move'), x, y, VIEW);
        if (ui.attackOverlay.has(i)) fb.blit(this.sprite('ov_attack'), x, y, VIEW);
        const uid = m.occupant[i]!;
        if (uid !== NO_UNIT) {
          const u = g.pool.get(uid);
          if (u) this.drawUnit(u, x, y);
        }
        if (ui.selIdx === i) fb.blit(this.sprite('ov_sel'), x, y, VIEW);
        if (ui.cursorIdx === i) fb.blit(this.sprite('ov_cursor'), x, y, VIEW);
      }
    }
  }

  drawMinimap(g: Game, ui: Ui, x: number, y: number): void {
    const m = g.map;
    for (let row = 0; row < MAP_H; row++) {
      for (let col = 0; col < MAP_W; col++) {
        const i = row * MAP_W + col;
        let v: number;
        if (m.fog[i] === FOG_HIDDEN) v = 0;
        else {
          v = MINI_COLOR[m.cells[i]! & TERRAIN_MASK]!;
          const uid = m.occupant[i]!;
          if (uid !== NO_UNIT && m.fog[i] !== FOG_EXPLORED) {
            const u = g.pool.get(uid);
            if (u) v = u.side === 1 ? 155 : 170;
          }
        }
        this.fb.fillRect(x + col * 2, y + row * 2, 2, 2, v);
      }
    }
    const vx = x + Math.floor((ui.camX * 2) / PK.HEX_W);
    const vy = y + Math.floor((ui.camY * 2) / PK.ROW_STEP);
    this.fb.frameRect(vx, vy, Math.floor((VIEW[2] * 2) / PK.HEX_W),
                      Math.floor((VIEW[3] * 2) / PK.ROW_STEP), 15);
  }

  drawPanel(g: Game, ui: Ui): void {
    const fb = this.fb;
    const [px, py, pw, ph] = PANEL_RECT;
    fb.fillRect(px, py, pw, ph, 8);
    fb.frameRect(px, py, pw, ph, 7);
    fb.text(`TURN ${g.turn}`, px + 4, py + 4, 15);
    fb.text(`SIDE ${g.side}`, px + 4, py + 13, 15);
    this.drawMinimap(g, ui, px + 6, py + 24);
    const u = ui.selUnit >= 0 ? g.pool.get(ui.selUnit) : null;
    const ty = py + 70;
    if (u) {
      fb.text(KINDS[u.kind]!.key, px + 4, ty, 14);
      fb.text(`HP ${u.hp}`, px + 4, ty + 10, 15);
      fb.text(`MP ${u.mp}`, px + 4, ty + 19, 15);
      fb.text(`AM ${u.ammo}`, px + 4, ty + 28, 15);
      fb.text(`EN ${u.ent}`, px + 4, ty + 37, 15);
    } else {
      fb.text('NO UNIT', px + 4, ty, 7);
    }
    fb.text(ui.stateName(), px + 4, py + 136, 11);
  }

  drawMsg(g: Game, ui: Ui): void {
    const fb = this.fb;
    const [mx, my, mw, mh] = MSG;
    fb.fillRect(mx, my, mw, mh, 0);
    fb.frameRect(mx, my, mw, mh, 7);
    const lines = ui.asciiLog(g, 3);
    for (let i = 0; i < lines.length; i++) {
      fb.text(lines[i]!.slice(0, 41), mx + 3, my + 4 + i * 9, i === 0 ? 15 : 7, MSG);
    }
  }

  // 위젯 트리를 앞에서 뒤로(너비 우선) 그린다 — 히트 테스트와 정확히 반대 순서.
  drawWidgets(ui: Ui): void {
    const queue = [ui.root];
    for (let qi = 0; qi < queue.length; qi++) {
      const w = queue[qi]!;
      if (!w.visible) continue;
      if (w.kind === Kind.BUTTON) {
        const on = w.enabled;
        this.fb.fillRect(w.x, w.y, w.w, w.h, on ? 7 : 8);
        this.fb.frameRect(w.x, w.y, w.w, w.h, on ? 15 : 7);
        this.fb.text(w.label, w.x + 3, w.y + 3, on ? 0 : 8);
      } else if (w.kind === Kind.DIALOG) {
        this.fb.fillRect(w.x + 4, w.y + 4, w.w, w.h, 0);
        this.fb.fillRect(w.x, w.y, w.w, w.h, 8);
        this.fb.frameRect(w.x, w.y, w.w, w.h, 15);
        this.fb.frameRect(w.x + 2, w.y + 2, w.w - 4, w.h - 4, 7);
        this.fb.text(w.label, w.x + 12, w.y + 14, 15);
      }
      queue.push(...w.children);
    }
  }

  draw(g: Game, ui: Ui): Framebuffer {
    this.drawMap(g, ui);
    this.drawPanel(g, ui);
    this.drawMsg(g, ui);
    this.drawWidgets(ui);
    return this.fb;
  }

  frameHash(): number {
    return fnv1a(this.fb.toPpm(this.pal));
  }
}

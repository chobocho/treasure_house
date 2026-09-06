// 화면 구성 — 레이어·스크롤·y 정렬·미니맵·패널 (SPEC §23).
//
//    렌더는 **상태를 읽기만 한다.** sim 을 건드리는 줄이 하나라도 생기면
//    락스텝이 끝난다(§18.1). 팔레트 사이클 위상도 인자로만 받는다.
//
//    지형 타일은 그림이 아니라 색이다(§23.1). 아티스트가 없으므로 한 칸을
//    MINI_COLOR 로 채우고, 오토타일 마스크가 가리키는 "나와 다른 지형" 쪽
//    가장자리 1px 만 어둡게 긋는다.

import * as C from './const';
import * as F from './fixed';
import * as RS from './raster';
import { Sim } from './sim';
import * as S from './spatial';
import * as T from './tmap';

export const TILES_X = Math.floor(C.VIEW_W / C.TILE) + 1;
export const TILES_Y = Math.floor(C.VIEW_H / C.TILE) + 1;
export const EDGE_SPEED = 4;
export const EDGE_MARGIN = 8;
export const MAX_CAM_X = C.MAP_W * C.TILE - C.VIEW_W;
export const MAX_CAM_Y = C.MAP_H * C.TILE - C.VIEW_H;

export const UI_DARK = 193;
export const UI_MID = 195;
export const UI_LIGHT = 197;
export const UI_TEXT = 198;
export const UI_HP_GOOD = 201;
export const UI_HP_BAD = 200;
export const UI_SELECT = 199;

// ── SPEC §23.2 스크롤 ───────────────────────────────────────────────────────
// 카메라는 **정수 픽셀**이다. 서브픽셀 스크롤은 도스 시절 흔치 않았고,
// 정수로 두면 타일 그리기가 오프셋 하나로 끝난다.
export class View {
  camX: number;
  camY: number;

  constructor(camX = 0, camY = 0) {
    this.camX = camX;
    this.camY = camY;
  }

  private clampTo(m: T.TMap): void {
    const mx = m.w * C.TILE - C.VIEW_W;
    const my = m.h * C.TILE - C.VIEW_H;
    if (this.camX < 0) this.camX = 0;
    if (this.camY < 0) this.camY = 0;
    if (this.camX > mx) this.camX = mx;
    if (this.camY > my) this.camY = my;
  }

  move(m: T.TMap, dx: number, dy: number): void {
    this.camX += dx;
    this.camY += dy;
    this.clampTo(m);
  }

  centerOn(m: T.TMap, tx: number, ty: number): void {
    this.camX = tx * C.TILE - Math.floor(C.VIEW_W / 2);
    this.camY = ty * C.TILE - Math.floor(C.VIEW_H / 2);
    this.clampTo(m);
  }

  // (첫 타일 x, 첫 타일 y, 픽셀 오프셋 x, 오프셋 y).
  firstTile(): [number, number, number, number] {
    return [F.floordiv(this.camX, C.TILE), F.floordiv(this.camY, C.TILE),
            F.fmod(this.camX, C.TILE), F.fmod(this.camY, C.TILE)];
  }
}

// 마우스가 뷰포트 가장자리 8px 안이면 그 방향으로 4px/틱.
export function edgeScroll(mx: number, my: number): [number, number] {
  if (!(mx >= 0 && mx < C.VIEW_W && my >= 0 && my < C.VIEW_H)) return [0, 0];
  let dx = 0;
  let dy = 0;
  if (mx < EDGE_MARGIN) dx = -EDGE_SPEED;
  else if (mx >= C.VIEW_W - EDGE_MARGIN) dx = EDGE_SPEED;
  if (my < EDGE_MARGIN) dy = -EDGE_SPEED;
  else if (my >= C.VIEW_H - EDGE_MARGIN) dy = EDGE_SPEED;
  return [dx, dy];
}

// ── SPEC §23.3 y 정렬 ───────────────────────────────────────────────────────
// 발밑 y · x · 핸들. 키가 전순서라 안정 정렬 여부에 의존하지 않는다.
export function sortKey(w: S.World, i: number): [number, number, number] {
  const foot = C.FOOT[w.kind[i]];
  return [F.fpFloor(w.py[i]) + foot * C.TILE, F.fpFloor(w.px[i]), w.handle(i)];
}

function keyGt(a: [number, number, number], b: [number, number, number]): boolean {
  if (a[0] !== b[0]) return a[0] > b[0];
  if (a[1] !== b[1]) return a[1] > b[1];
  return a[2] > b[2];
}

// 삽입 정렬. 프레임 사이에 목록이 거의 정렬되어 있어 거의 O(n) 이다.
export function yOrder(w: S.World): number[] {
  const out: number[] = [];
  for (let i = 1; i < C.MAX_ENT; i += 1) {
    if (w.alive[i] === 0) continue;
    const k = sortKey(w, i);
    let j = out.length;
    while (j > 0 && keyGt(sortKey(w, out[j - 1]), k)) j -= 1;
    out.splice(j, 0, i);
  }
  return out;
}

// ── SPEC §23.4 미니맵 ───────────────────────────────────────────────────────
export function minimapNearest(m: T.TMap, sx: number, sy: number): number {
  return m.terrain[F.floordiv(sy * m.h, C.MINI_H) * m.w
                   + F.floordiv(sx * m.w, C.MINI_W)];
}

// 블록에서 가장 많이 나온 지형, 동점이면 지형 번호 최소. 128 맵을 대비한다.
export function minimapMajority(m: T.TMap, sx: number, sy: number): number {
  const x0 = F.floordiv(sx * m.w, C.MINI_W);
  let x1 = F.floordiv((sx + 1) * m.w, C.MINI_W);
  const y0 = F.floordiv(sy * m.h, C.MINI_H);
  let y1 = F.floordiv((sy + 1) * m.h, C.MINI_H);
  if (x1 <= x0) x1 = x0 + 1;
  if (y1 <= y0) y1 = y0 + 1;
  const cnt = new Array<number>(8).fill(0);
  for (let y = y0; y < Math.min(y1, m.h); y += 1) {
    for (let x = x0; x < Math.min(x1, m.w); x += 1) {
      cnt[m.terrain[y * m.w + x]] += 1;
    }
  }
  let best = 0;
  let bn = -1;
  for (let t = 0; t < 8; t += 1) {
    if (cnt[t] > bn) {
      bn = cnt[t];
      best = t;
    }
  }
  return best;
}

export function minimapToTile(sx: number, sy: number): [number, number] {
  return [F.floordiv(sx * C.MAP_W, C.MINI_W), F.floordiv(sy * C.MAP_H, C.MINI_H)];
}

// ── 안개가 가리는 것 ────────────────────────────────────────────────────────
// §23.1 — **유닛 숨기기는 명암표가 못 한다.** 보이는 칸의 것만 그린다.
export function visibleEntities(sim: Sim, p: number): number[] {
  const out: number[] = [];
  for (const i of yOrder(sim.w)) {
    const t = sim.w.ty[i] * sim.m.w + sim.w.tx[i];
    if (sim.fog.visible(p, t)) out.push(i);
  }
  return out;
}

// 자릿수 고정 — 숫자가 흔들리면 더티 렉트가 커진다.
export function creditsText(v0: number): string {
  let v = v0;
  if (v > 99999) v = 99999;
  const s = String(v);
  return ' '.repeat(5 - s.length) + s;
}

// ── SPEC §23.1 레이어 ───────────────────────────────────────────────────────
function fill(fb: number[], x: number, y: number, w: number, h: number,
              v: number): void {
  for (let j = Math.max(0, y); j < Math.min(C.VIEW_H, y + h); j += 1) {
    const row = j * C.SCR_W;
    for (let i = Math.max(0, x); i < Math.min(C.VIEW_W, x + w); i += 1) {
      fb[row + i] = v;
    }
  }
}

function drawTerrain(fb: number[], sim: Sim, view: View, light: number[][],
                     p: number): void {
  const m = sim.m;
  const [tx0, ty0, ox, oy] = view.firstTile();
  for (let ty = ty0; ty < Math.min(m.h, ty0 + TILES_Y); ty += 1) {
    for (let tx = tx0; tx < Math.min(m.w, tx0 + TILES_X); tx += 1) {
      const px = (tx - tx0) * C.TILE - ox;
      const py = (ty - ty0) * C.TILE - oy;
      const level = sim.fog.level(p, tx, ty);
      if (level === 0) {
        fill(fb, px, py, C.TILE, C.TILE, 0);
        continue;
      }
      const t = m.terrain[ty * m.w + tx];
      let base = T.MINI_COLOR[t];
      let edge = F.fmod(base, 8) >= 2 ? base - 2 : base + 1;
      if (level < 3) {
        base = light[level][base];
        edge = light[level][edge];
      }
      fill(fb, px, py, C.TILE, C.TILE, base);
      const mask = m.mask(tx, ty);        // §4.4 — 다른 지형 쪽만 긋는다
      if (F.bit(mask, 0) === 0) fill(fb, px, py, C.TILE, 1, edge);
      if (F.bit(mask, 4) === 0) fill(fb, px, py + C.TILE - 1, C.TILE, 1, edge);
      if (F.bit(mask, 6) === 0) fill(fb, px, py, 1, C.TILE, edge);
      if (F.bit(mask, 2) === 0) fill(fb, px + C.TILE - 1, py, 1, C.TILE, edge);
    }
  }
}

// 체력바와 선택 표시. 뷰포트 안에서만 그린다.
function bars(fb: number[], w: S.World, i: number, x0: number, y0: number,
              spr: RS.Sprite, selected: boolean): void {
  const hp = w.hp[i];
  const full = C.HP[w.kind[i]];
  if (full <= 0) return;
  const wdt = spr.w - 2;
  const fillN = F.floordiv(wdt * hp, full);
  const y = y0 - 2;
  if (y >= 0 && y < C.VIEW_H) {
    for (let k = 0; k < wdt; k += 1) {
      const x = x0 + 1 + k;
      if (x >= 0 && x < C.VIEW_W) {
        fb[y * C.SCR_W + x] = k < fillN ? UI_HP_GOOD : UI_HP_BAD;
      }
    }
  }
  if (selected) {
    for (let k = 0; k < spr.w; k += 1) {
      const x = x0 + k;
      for (const yy of [y0, y0 + spr.h - 1]) {
        if (x >= 0 && x < C.VIEW_W && yy >= 0 && yy < C.VIEW_H) {
          fb[yy * C.SCR_W + x] = UI_SELECT;
        }
      }
    }
  }
}

function drawEntities(fb: number[], sim: Sim, view: View, _light: number[][],
                      p: number, selection: number[]): void {
  const w = sim.w;
  const sel = new Set<number>(selection);
  for (const i of visibleEntities(sim, p)) {
    const [spr, flip] = RS.spriteFor(w.kind[i], w.dir[i]);
    if (spr === null) continue;
    const sx = F.fpFloor(w.px[i]) - view.camX;
    const sy = F.fpFloor(w.py[i]) - view.camY;
    const anchorX = sx + F.floordiv(C.TILE * C.FOOT[w.kind[i]], 2);
    const anchorY = sy + C.TILE * C.FOOT[w.kind[i]] - 2;
    RS.blit(fb, spr, anchorX, anchorY, w.owner[i], flip);
    bars(fb, w, i, anchorX - spr.ox, anchorY - spr.oy, spr,
         sel.has(w.handle(i)));
  }
}

function drawProjectiles(fb: number[], sim: Sim, view: View): void {
  for (let k = 0; k < sim.pj.n(); k += 1) {
    const x = F.fpFloor(sim.pj.x[k]) - view.camX;
    const y = F.fpFloor(sim.pj.y[k]) - view.camY;
    if (x >= 0 && x < C.VIEW_W && y >= 0 && y < C.VIEW_H) {
      fb[y * C.SCR_W + x] = UI_TEXT;
    }
  }
}

function drawPanel(fb: number[], sim: Sim, p: number,
                   selection: number[]): void {
  const m = sim.m;
  for (let y = 0; y < C.SCR_H; y += 1) {
    const row = y * C.SCR_W;
    for (let x = C.PANEL_X; x < C.SCR_W; x += 1) fb[row + x] = UI_DARK;
  }
  for (let sy = 0; sy < C.MINI_H; sy += 1) {   // 미니맵 — 한 타일이 한 픽셀
    const row = (C.MINI_Y + sy) * C.SCR_W;
    for (let sx = 0; sx < C.MINI_W; sx += 1) {
      const [tx, ty] = minimapToTile(sx, sy);
      const level = sim.fog.level(p, tx, ty);
      if (level === 0) fb[row + C.MINI_X + sx] = 0;
      else fb[row + C.MINI_X + sx] = T.MINI_COLOR[minimapNearest(m, sx, sy)];
    }
  }
  for (let i = 1; i < C.MAX_ENT; i += 1) {     // 미니맵 위의 유닛
    if (sim.w.alive[i] === 0) continue;
    const t = sim.w.ty[i] * m.w + sim.w.tx[i];
    if (!sim.fog.visible(p, t)) continue;
    const sx = F.floordiv(sim.w.tx[i] * C.MINI_W, m.w);
    const sy = F.floordiv(sim.w.ty[i] * C.MINI_H, m.h);
    fb[(C.MINI_Y + sy) * C.SCR_W + C.MINI_X + sx] =
      RS.PLAYER_BASE + sim.w.owner[i] * 8 + 5;
  }
  RS.text(fb, 'SEL', C.PANEL_X + 2, C.MINI_H + 4, UI_TEXT);
  if (selection.length > 0) {
    const h = selection[0];
    if (sim.w.valid(h)) {
      const j = S.index(h);
      RS.text(fb, C.NAME[sim.w.kind[j]].slice(0, 1).toUpperCase()
              + String(sim.w.kind[j]), C.PANEL_X + 2, C.MINI_H + 14, UI_TEXT);
      RS.text(fb, creditsText(sim.w.hp[j]), C.PANEL_X + 2, C.MINI_H + 24,
              UI_HP_GOOD);
    }
  }
}

function drawBottom(fb: number[], sim: Sim, p: number, message: string): void {
  for (let y = C.BAR_Y; y < C.SCR_H; y += 1) {
    const row = y * C.SCR_W;
    for (let x = 0; x < C.PANEL_X; x += 1) fb[row + x] = UI_MID;
  }
  RS.text(fb, 'CREDITS' + creditsText(sim.ec.credits[p]), 4, C.BAR_Y + 2,
          UI_TEXT);
  RS.text(fb, 'POP' + creditsText(sim.ec.supplyUsed[p]) + '/'
          + creditsText(sim.ec.supplyCap[p]), 4, C.BAR_Y + 12, UI_TEXT);
  if (message !== '') {
    RS.text(fb, message.slice(0, 24), 130, C.BAR_Y + 12, UI_LIGHT);
  }
}

// §23.1 의 여덟 층을 순서대로. 팔레트 위상은 그림을 바꾸지 않는다.
export function draw(fb: number[], sim: Sim, view: View, _phase: number,
                     _pal: RS.RGB[], light: number[][], p: number,
                     selection: number[], message: string): void {
  drawTerrain(fb, sim, view, light, p);
  drawEntities(fb, sim, view, light, p, selection);
  drawProjectiles(fb, sim, view);
  drawPanel(fb, sim, p, selection);
  drawBottom(fb, sim, p, message);
}

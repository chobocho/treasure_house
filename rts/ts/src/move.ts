// 이동·예약·밀어내기·대형 — SPEC §13.
//
//    이 모듈의 전부는 불변식 R 하나다: **어떤 타일도 두 엔티티에게 동시에
//    예약되지 않는다.** 걸음을 시작할 때 도착 칸을 먼저 쥐고, 걸음이 끝나야
//    출발 칸을 놓는다. 두 칸을 쥐는 구간이 있어야 두 유닛이 서로의 칸으로
//    동시에 들어가는 사고가 없다.
//
//    교착은 완전히 사라지지 않는다. 좁은 통로에서 마주 오는 두 무리는 24틱 뒤
//    명령을 포기하는 것으로 풀린다 — 해결이 아니라 포기다(§13.3).

import * as C from './const';
import * as F from './fixed';
import * as P from './path';
import * as S from './spatial';
import { TMap } from './tmap';

export const ARRIVE_R = 2;         // §13.4 도착 반경 (타일, 체비셰프)
export const REPATH_TICKS = 8;     // §13.3 이만큼 막히면 경로를 다시 찾는다
export const GIVEUP_TICKS = 24;    // §13.3 이만큼 막히면 명령을 포기한다

export const LINE = 0;             // §13.5 대형
export const COLUMN = 1;
export const BOX = 2;
export const STOP_DIR = 255;

// ── SPEC §13.1 타일 사이 보간 ───────────────────────────────────────────────
const SQRT2 = Math.sqrt(2.0);      // §19.4 의 주입 버그에서만 쓴다

// 방향 d 로 한 틱에 늘어나는 진행률 (16.16).
//
//   대각 보정을 빼면 유닛이 대각으로 √2 = 41 % 빨라진다. 도스 시절에도
//   이 버그를 그대로 둔 게임이 있었고, 그래서 플레이어들이 지그재그로 움직였다.
//
//   `floatBug` 는 §19.4 의 **일부러 넣은** 디싱크다. 1/√2 는 이진 소수로
//   끝나지 않으므로 진행률이 정수가 아니게 되고, 그 누적 차이가 px·py 를 통해
//   상태 해시에 바로 나타난다. **엔진의 다른 어느 곳도 실수를 쓰지 않는다.**
export function stepAmount(speed: number, d: number, floatBug = false): number {
  const st = F.fpDiv(speed, F.fp(C.TILE));
  if (F.DCOST[d] === F.D_DIAG) {
    if (floatBug) return st / SQRT2;
    return F.fpMul(st, F.FP_DIAG);
  }
  return st;
}

// 화면 위치는 상태가 아니라 from_t·to_t·prog 의 파생값이다 (§13.1).
export function posOf(w: S.World, m: TMap, i: number): [number, number] {
  const fx = F.fmod(w.from_t[i], m.w);
  const fy = F.floordiv(w.from_t[i], m.w);
  const tx = F.fmod(w.to_t[i], m.w);
  const ty = F.floordiv(w.to_t[i], m.w);
  const px = F.fp(fx * C.TILE) + F.fpMul(F.fp((tx - fx) * C.TILE), w.prog[i]);
  const py = F.fp(fy * C.TILE) + F.fpMul(F.fp((ty - fy) * C.TILE), w.prog[i]);
  return [px, py];
}

// ── SPEC §13.5 회전과 대형 ──────────────────────────────────────────────────
// 이동 방향 d 로 오프셋을 돌린다. 행렬이 아니라 8방향 표다.
// 45° 회전은 정수 격자를 보존하지 않으므로 대각은 이웃한 두 직교 방향의
// 결과를 더해 2로 내림 나눗셈한다 — 근사이며, 그렇다고 적어 둔다.
export function rot8(d: number, ox: number, oy: number): [number, number] {
  if (d === 0) return [ox, oy];
  if (d === 2) return [-oy, ox];
  if (d === 4) return [-ox, -oy];
  if (d === 6) return [oy, -ox];
  const [ax, ay] = rot8(d - 1, ox, oy);
  const [bx, by] = rot8(F.fmod(d + 1, 8), ox, oy);
  return [F.floordiv(ax + bx, 2), F.floordiv(ay + by, 2)];
}

// 목표 주위 n 개의 슬롯 타일. 슬롯 순서 = 핸들 오름차순으로 나눠 준다.
// 맵 밖이거나 통행 불가인 슬롯은 목표 타일 자체로 접는다. 슬롯을 다시
// 찾아 주지는 않는다 — 반쯤 성공하는 재배치가 교착보다 나쁜 그림을 만든다.
export function formation(n: number, shape: number, d: number, gx: number,
                          gy: number, m: TMap,
                          kind: number): Array<[number, number]> {
  const out: Array<[number, number]> = [];
  if (n <= 0) return out;
  const side = F.isqrt(n - 1) + 1;           // ceil(sqrt(n)) — §2.5 정수 제곱근
  for (let k = 0; k < n; k += 1) {
    let ox = 0;
    let oy = 0;
    if (shape === LINE) {
      ox = k - F.floordiv(n - 1, 2);
      oy = 0;
    } else if (shape === COLUMN) {
      ox = 0;
      oy = k;
    } else {
      ox = F.fmod(k, side) - F.floordiv(side - 1, 2);
      oy = F.floordiv(k, side);
    }
    const [rx, ry] = rot8(d, ox, oy);
    let x = gx + rx;
    let y = gy + ry;
    if (!m.passableTerrain(x, y, kind)) {
      x = gx;
      y = gy;
    }
    out.push([x, y]);
  }
  return out;
}

// ── SPEC §13.3 밀어내기 ─────────────────────────────────────────────────────
// i 를 어느 방향으로 비키게 할지. 없으면 255.
// 훑는 순서는 미는 쪽 진행 방향의 **반대에서 시작해 시계 방향**이다.
// 순서를 명세로 고정하지 않으면 세 언어가 다른 칸을 고르고, 그 차이는
// 한 틱 뒤 위치 차이가 되어 그대로 디싱크다.
export function pushDir(mv: Movement, i: number, fromDir: number): number {
  const w = mv.w;
  const m = mv.m;
  const kind = C.MOVE_KIND[w.kind[i]];
  for (let k = 0; k < 8; k += 1) {
    const d = F.fmod(fromDir + 4 + k, 8);
    const u = w.tx[i] + F.DX[d];
    const v = w.ty[i] + F.DY[d];
    if (!m.passableTerrain(u, v, kind)) continue;
    if (mv.resv[v * m.w + u] !== 0) continue;
    return d;
  }
  return STOP_DIR;
}

// 예약판과 유닛별 경로. sim 이 하나만 들고 있는다 (§18.2 4단계).
export class Movement {
  w: S.World;
  m: TMap;
  floatBug: boolean;
  resv: number[];
  blocked: number[];
  path: number[][];
  goal: number[];
  cache: P.Cache;
  // 이번 틱에 타일을 넘은 유닛 (i, 이전 타일, 새 타일). sim 의 7단계가
  // 이것만 보고 시야를 remove/add 한다 — 전수 재계산을 피하는 유일한 길이다.
  crossed: Array<[number, number, number]>;

  constructor(world: S.World, tmap: TMap, floatBug = false) {
    this.w = world;
    this.m = tmap;
    this.floatBug = floatBug;
    this.resv = new Array<number>(tmap.w * tmap.h).fill(0);
    this.blocked = new Array<number>(C.MAX_ENT).fill(0);
    this.path = [];
    for (let i = 0; i < C.MAX_ENT; i += 1) this.path.push([]);
    this.goal = new Array<number>(C.MAX_ENT).fill(-1);
    this.cache = new P.Cache();
    this.crossed = [];
  }

  // ── SPEC §13.2 예약 ──────────────────────────────────────────────────────
  reserve(tile: number, h: number): boolean {
    const cur = this.resv[tile];
    if (cur !== 0 && cur !== h) return false;
    this.resv[tile] = h;
    return true;
  }

  release(tile: number, h: number): boolean {
    if (this.resv[tile] !== h) return false;
    this.resv[tile] = 0;
    return true;
  }

  // 엔티티가 선 칸을 예약한다. 건물은 발자국 전체를 영구히 쥔다.
  claim(i: number): boolean {
    const w = this.w;
    const m = this.m;
    const h = w.handle(i);
    const f = C.FOOT[w.kind[i]];
    let ok = true;
    for (let dy = 0; dy < f; dy += 1) {
      for (let dx = 0; dx < f; dx += 1) {
        const x = w.tx[i] + dx;
        const y = w.ty[i] + dy;
        if (!m.inMap(x, y)) continue;
        if (!this.reserve(y * m.w + x, h)) ok = false;
        if (C.IS_BUILDING[w.kind[i]] !== 0) m.setBuilding(x, y, true);
        else m.occupy(x, y, true);
      }
    }
    return ok;
  }

  // 사망·철거. 건물은 잔해를 남기므로 통행이 지형에서 복구된다(§4.3).
  unclaim(i: number): void {
    const w = this.w;
    const m = this.m;
    const h = w.handle(i);
    const f = C.FOOT[w.kind[i]];
    for (let dy = 0; dy < f; dy += 1) {
      for (let dx = 0; dx < f; dx += 1) {
        const x = w.tx[i] + dx;
        const y = w.ty[i] + dy;
        if (!m.inMap(x, y)) continue;
        this.release(y * m.w + x, h);
        if (C.IS_BUILDING[w.kind[i]] !== 0) m.setBuilding(x, y, false);
        else m.occupy(x, y, false);
      }
    }
    this.release(w.to_t[i], h);
    this.path[i] = [];
    this.goal[i] = -1;
    this.blocked[i] = 0;
  }

  // ── 명령 ─────────────────────────────────────────────────────────────────
  // 목표 타일로 가는 경로를 깐다. 닿을 수 없으면 §8.6 의 대체 목표로.
  order(i: number, gx: number, gy: number): boolean {
    if (!this.m.inMap(gx, gy)) return false;
    this.blocked[i] = 0;
    return this.plan(i, gx, gy);
  }

  // 경로만 다시 깐다 — blocked 카운터는 건드리지 않는다(§13.3 재탐색).
  private plan(i: number, gx: number, gy: number): boolean {
    const w = this.w;
    const m = this.m;
    const kind = C.MOVE_KIND[w.kind[i]];
    const s: [number, number] = [w.tx[i], w.ty[i]];
    const goal = P.closestReachable(m, kind, s, [gx, gy]);
    if (goal === null) {
      this.path[i] = [];
      this.goal[i] = -1;
      return false;
    }
    const [, tiles] = P.find(m, kind, s, goal, this.cache);
    this.path[i] = tiles.slice(1);
    this.goal[i] = this.path[i].length > 0 ? goal[1] * m.w + goal[0] : -1;
    return true;
  }

  // §12.4 STOP — 아직 시작하지 않은 걸음의 예약만 반납한다(§13.2).
  stop(i: number): void {
    const w = this.w;
    this.path[i] = [];
    this.goal[i] = -1;
    this.blocked[i] = 0;
    if (w.prog[i] === 0 && w.to_t[i] !== w.from_t[i]) {
      this.release(w.to_t[i], w.handle(i));
      w.to_t[i] = w.from_t[i];
    }
  }

  // ── SPEC §18.2 4단계: 핸들 오름차순으로 한 틱 ────────────────────────────
  step(): void {
    const w = this.w;
    this.crossed = [];
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (w.alive[i] === 1 && C.IS_BUILDING[w.kind[i]] === 0) this.stepOne(i);
    }
  }

  stepOne(i: number): void {
    const w = this.w;
    const m = this.m;
    const h = w.handle(i);
    if (w.prog[i] > 0) {                    // 걸음 도중 — 끝까지 마친다
      w.prog[i] += stepAmount(C.SPEED[w.kind[i]], w.dir[i], this.floatBug);
      if (w.prog[i] >= F.FP_ONE) this.finishStep(i, h);
      const [px, py] = posOf(w, m, i);
      w.px[i] = px;
      w.py[i] = py;
      return;
    }
    if (this.path[i].length === 0) return;
    if (this.arrived(i, h)) return;
    const nxt = this.path[i][0];
    const d = F.atan8(F.fmod(nxt, m.w) - w.tx[i],
                      F.floordiv(nxt, m.w) - w.ty[i]);
    if (!this.reserve(nxt, h)) {
      this.onBlocked(i, d);
      return;
    }
    this.blocked[i] = 0;
    w.dir[i] = d;
    w.to_t[i] = nxt;
    w.prog[i] = stepAmount(C.SPEED[w.kind[i]], d, this.floatBug);
    if (w.prog[i] >= F.FP_ONE) this.finishStep(i, h);   // 아주 빠른 유닛
    const [px, py] = posOf(w, m, i);
    w.px[i] = px;
    w.py[i] = py;
  }

  private finishStep(i: number, h: number): void {
    const w = this.w;
    const m = this.m;
    const old = w.from_t[i];
    this.release(old, h);
    m.occupy(F.fmod(old, m.w), F.floordiv(old, m.w), false);
    w.from_t[i] = w.to_t[i];
    w.prog[i] = 0;
    const nx = F.fmod(w.to_t[i], m.w);
    const ny = F.floordiv(w.to_t[i], m.w);
    w.moveTile(i, nx, ny);
    m.occupy(nx, ny, true);
    this.crossed.push([i, old, w.to_t[i]]);
    if (this.path[i].length > 0 && this.path[i][0] === w.to_t[i]) {
      this.path[i] = this.path[i].slice(1);
    }
    if (this.path[i].length === 0) this.goal[i] = -1;
  }

  // §13.4 목표 칸이 남의 것이고 ARRIVE_R 안이면 도착으로 친다.
  // 이것이 없으면 무리의 마지막 한 기가 영원히 목표 칸을 두드린다.
  private arrived(i: number, h: number): boolean {
    const w = this.w;
    const m = this.m;
    const g = this.goal[i];
    if (g < 0) return false;
    const taken = this.resv[g];
    if (taken === 0 || taken === h) return false;
    if (F.dinf(F.fmod(g, m.w) - w.tx[i],
               F.floordiv(g, m.w) - w.ty[i]) > ARRIVE_R) return false;
    this.path[i] = [];
    this.goal[i] = -1;
    this.blocked[i] = 0;
    return true;
  }

  // §13.3 막힘 — 8틱이면 재탐색, 24틱이면 포기.
  private onBlocked(i: number, d: number): void {
    const w = this.w;
    const m = this.m;
    this.blocked[i] += 1;
    const nxt = this.path[i][0];
    const other = this.resv[nxt];
    if (w.valid(other)) {
      const j = S.index(other);
      if (w.owner[j] === w.owner[i] && w.prog[j] === 0
          && this.path[j].length === 0 && C.IS_BUILDING[w.kind[j]] === 0) {
        const pd = pushDir(this, j, d);        // 정지한 아군은 비켜 준다
        if (pd !== STOP_DIR) {
          this.path[j] = [(w.ty[j] + F.DY[pd]) * m.w + w.tx[j] + F.DX[pd]];
          this.goal[j] = this.path[j][0];
        }
      }
    }
    if (this.blocked[i] >= GIVEUP_TICKS) {
      this.path[i] = [];
      this.goal[i] = -1;
      this.blocked[i] = 0;
    } else if (this.blocked[i] === REPATH_TICKS && this.goal[i] >= 0) {
      const g = this.goal[i];
      this.plan(i, F.fmod(g, m.w), F.floordiv(g, m.w));
    }
  }
}

// 전투 — 피해·표적·투사체·스플래시·란체스터 (SPEC §15).
//
//    피해 공식은 워크래프트 II 의 공식 문서를 따랐다(§15.2). 다만 "50 %에서
//    100 % 사이"의 **반올림 방향**은 블리자드 문서에 없고 팬 사이트의 역산이
//    출처다. 하한 1(방어가 아무리 높아도 피해 1)은 이 덱의 규칙이다.

import * as C from './const';
import * as F from './fixed';
import { LCG } from './rng';
import * as S from './spatial';

export const STRAIGHT = 0;
export const ARC = 1;
export const G = 1638;                  // 0.025 px/틱², 16.16
export const ARROW_SPEED = F.fp(4);     // 화살·총알 4 px/틱 (§15.3)
export const ARC_MIN_TICKS = 6;
export const ARC_DIV = 24;
export const SPLASH_RINGS = 3;

// ── SPEC §15.2 피해 공식 ────────────────────────────────────────────────────
// 최대 피해 = 기본 − 방어 + 관통, 하한 1.
// 하한이 없으면 방어력이 높은 유닛은 **절대 죽지 않는다**. 이 하한은
// 블리자드 문서에 없는 이 덱의 규칙이다.
export function maxDamage(basic: number, pierce: number,
                          armour: number): number {
  const mx = basic - armour + pierce;
  return mx < 1 ? 1 : mx;
}

// 최대치의 50 %, 올림. 올림이라는 부분은 2차 출처다(§15.2).
export function damageLo(mx: number): number {
  return F.floordiv(mx + 1, 2);
}

export function rollDamage(rng: LCG, basic: number, pierce: number,
                           armour: number): number {
  const mx = maxDamage(basic, pierce, armour);
  const lo = damageLo(mx);
  return lo + rng.roll(mx - lo + 1);
}

// E[dmg] × 100 (정리 15.1). 정수만 쓰려고 100배로 둔다.
export function expect100(basic: number, pierce: number,
                          armour: number): number {
  const mx = maxDamage(basic, pierce, armour);
  return (damageLo(mx) + mx) * 50;
}

// ── SPEC §15.1 사거리와 표적 선택 ───────────────────────────────────────────
// 체비셰프 거리 — 8방향 격자에서 '몇 걸음 안'과 정확히 같다.
export function inRange(w: S.World, i: number, j: number): boolean {
  return F.dinf(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j]) <= C.RANGE[w.kind[i]];
}

function isEnemy(w: S.World, i: number, j: number): boolean {
  return w.alive[j] === 1 && w.owner[j] !== w.owner[i] && w.hp[j] > 0;
}

// 사거리 안 적 중 d83 최소, 동점이면 핸들 오름차순.
// 동점 규칙이 명세인 이유는 대칭 맵에서 동점이 흔하기 때문이다.
// 두 기계가 다른 표적을 고르면 그 틱부터 상태가 갈린다.
function nearest(w: S.World, i: number, reach: number): number {
  let best = 0;
  let bd = -1;
  for (let j = 1; j < C.MAX_ENT; j += 1) {
    if (!isEnemy(w, i, j)) continue;
    const d = F.dinf(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j]);
    if (d > reach) continue;
    const s = F.d83(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j]);
    if (bd < 0 || s < bd) {              // 핸들 오름차순으로 훑으므로
      bd = s;                            // 등호를 빼면 작은 핸들이 이긴다
      best = w.handle(j);
    }
  }
  return best;
}

// (표적 핸들, 접근이 필요한가). 규칙 순서는 §15.1 그대로다.
export function pickTarget(w: S.World, i: number, lastHitter: number,
                           attackMove: boolean): [number, boolean] {
  if (C.BASIC[w.kind[i]] === 0) return [0, false];   // 채집기·비무장 건물
  const reach = C.RANGE[w.kind[i]];
  const cur = w.target[i];
  if (w.valid(cur)) {
    const j = F.floordiv(cur, 256);
    if (isEnemy(w, i, j) && inRange(w, i, j)) return [cur, false];  // 1) 표적 유지
  }
  if (w.valid(lastHitter)) {
    const j = F.floordiv(lastHitter, 256);
    if (isEnemy(w, i, j) && inRange(w, i, j)) return [lastHitter, false]; // 2)
  }
  let h = nearest(w, i, reach);           // 3) 가장 가까운 적
  if (h !== 0) return [h, false];
  if (attackMove) {                       // 4) ATTACK_MOVE 만 두 칸 더 본다
    h = nearest(w, i, reach + 2);
    if (h !== 0) return [h, true];
  }
  return [0, false];
}

// ── SPEC §15.5 스플래시 ─────────────────────────────────────────────────────
// 링 단위 감쇠 — 0링 전액, 1링 1/2, 2링 1/4, 그 밖은 0. 나눗셈은 내림.
export function splashDamage(dmg: number, ring: number): number {
  if (ring >= SPLASH_RINGS) return 0;
  return F.floordiv(dmg, F.pow2(ring));
}

// (핸들, 피해) 목록, 핸들 오름차순. **아군도 맞는다**.
// 같은 유닛이 두 링에 걸치는 일은 없다 — 대표 타일 하나로 판정하기 때문이다.
export function splashHits(w: S.World, tx: number, ty: number,
                           dmg: number): Array<[number, number]> {
  const out: Array<[number, number]> = [];
  for (let j = 1; j < C.MAX_ENT; j += 1) {
    if (w.alive[j] === 0 || w.hp[j] <= 0) continue;
    const ring = F.dinf(w.tx[j] - tx, w.ty[j] - ty);
    const d = splashDamage(dmg, ring);
    if (d > 0) out.push([w.handle(j), d]);
  }
  return out;
}

// ── SPEC §15.3·15.4 투사체 ──────────────────────────────────────────────────
// SoA 로 담는다 — 상태 해시(§18.4)가 배열 순서로 자동 고정되기 때문이다.
export class Projectiles {
  mapW: number;
  x: number[];
  y: number[];
  vx: number[];
  vy: number[];
  ttl: number[];
  target: number[];
  dmg: number[];
  kind: number[];
  dest: number[];

  constructor(mapW: number) {
    this.mapW = mapW;
    this.x = [];
    this.y = [];
    this.vx = [];
    this.vy = [];
    this.ttl = [];
    this.target = [];
    this.dmg = [];
    this.kind = [];
    this.dest = [];
  }

  n(): number {
    return this.x.length;
  }

  private tile(x: number, y: number): number {
    return F.floordiv(F.fpFloor(y), C.TILE) * this.mapW
      + F.floordiv(F.fpFloor(x), C.TILE);
  }

  // 좌표는 전부 16.16 픽셀. 같은 칸이면 발사하지 않는다(즉시 명중).
  // **표적을 쫓지 않는다.** 발사 시점의 위치로 날아가므로 빠른 유닛은
  // 화살을 피할 수 있다 — 이것도 이 덱의 규칙이다.
  launch(kind: number, x0: number, y0: number, x1: number, y1: number,
         speed: number, target: number, dmg: number): boolean {
    const dx = F.fpFloor(x1) - F.fpFloor(x0);
    const dy = F.fpFloor(y1) - F.fpFloor(y0);
    const d = F.isqrt(dx * dx + dy * dy);
    if (d === 0) return false;
    let vx = 0;
    let vy = 0;
    let ttl = 0;
    if (kind === ARC) {
      let t = ARC_MIN_TICKS;
      if (F.floordiv(d, ARC_DIV) > t) t = F.floordiv(d, ARC_DIV);
      vx = F.fpDiv(x1 - x0, F.fp(t));
      vy = F.fpDiv(y1 - y0, F.fp(t))
        - F.fpMul(G, F.fpDiv(F.fp(t), F.fp(2)));
      ttl = t;
    } else {
      vx = F.fpMul(F.fpDiv(F.fp(dx), F.fp(d)), speed);
      vy = F.fpMul(F.fpDiv(F.fp(dy), F.fp(d)), speed);
      ttl = F.floordiv(F.fp(d), speed) + 2;
    }
    this.x.push(x0);
    this.y.push(y0);
    this.vx.push(vx);
    this.vy.push(vy);
    this.ttl.push(ttl);
    this.target.push(target);
    this.dmg.push(dmg);
    this.kind.push(kind);
    this.dest.push(this.tile(x1, y1));
    return true;
  }

  // 한 틱. 명중한 것을 (핸들, 피해, 착탄 타일, 착탄 y, 종류) 로 돌려주고 지운다.
  // 마지막 칸이 종류인 이유는 sim 이 포물선 명중에만 스플래시(§15.5)를
  // 적용해야 하기 때문이다.
  step(): Array<[number, number, number, number, number]> {
    const hits: Array<[number, number, number, number, number]> = [];
    const keep: number[] = [];
    for (let k = 0; k < this.x.length; k += 1) {
      if (this.kind[k] === ARC) this.vy[k] += G;   // 수직은 중력만
      this.x[k] += this.vx[k];
      this.y[k] += this.vy[k];
      this.ttl[k] -= 1;
      if (this.tile(this.x[k], this.y[k]) === this.dest[k] || this.ttl[k] <= 0) {
        hits.push([this.target[k], this.dmg[k], this.dest[k], this.y[k],
                   this.kind[k]]);
      } else {
        keep.push(k);
      }
    }
    if (keep.length !== this.x.length) {
      this.x = keep.map((k) => this.x[k]);
      this.y = keep.map((k) => this.y[k]);
      this.vx = keep.map((k) => this.vx[k]);
      this.vy = keep.map((k) => this.vy[k]);
      this.ttl = keep.map((k) => this.ttl[k]);
      this.target = keep.map((k) => this.target[k]);
      this.dmg = keep.map((k) => this.dmg[k]);
      this.kind = keep.map((k) => this.kind[k]);
      this.dest = keep.map((k) => this.dest[k]);
    }
    return hits;
  }
}

// ── SPEC §15.6 란체스터 ─────────────────────────────────────────────────────
// 정수 이산 시뮬. 폐형해(정리 15.4)는 엔진이 아니라 gen_prim 이 계산한다.
// 종료 조건이 `>= FP_ONE` 인 것이 중요하다. `> 0` 으로 두면 A 가 0.5 인
// 상태에서 감소량이 내림으로 0 이 되어 영원히 돌지 않는다.
export function lanchesterSim(a0: number, b0: number, alpha: number,
                              beta: number): [number, number, number] {
  let a = F.fp(a0);
  let b = F.fp(b0);
  let t = 0;
  while (a >= F.FP_ONE && b >= F.FP_ONE && t < 10000) {
    const da = F.fpMul(beta, b);
    const db = F.fpMul(alpha, a);
    a -= da;
    b -= db;
    if (a < 0) a = 0;
    if (b < 0) b = 0;
    t += 1;
  }
  return [t, F.fpFloor(a), F.fpFloor(b)];
}

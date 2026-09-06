// 경제 — 자원·채집기 FSM·생산 큐·기술 트리·인구 (SPEC §16).
//
//    생산은 **선불**이다. 큐에 넣는 순간 크레딧이 빠진다. 후불로 두면 "완성
//    시점에 돈이 없는" 상태가 생기고, 그 처리 규칙이 언어마다 미묘하게 갈릴
//    여지가 생긴다 — 결정론을 위해 게임 디자인을 고른 자리다.

import * as C from './const';
import * as F from './fixed';
import { Movement } from './move';
import * as S from './spatial';
import * as T from './tmap';

export const ORE_PER_TILE = 500;
export const LOAD_MAX = 100;
export const MINE_PER_TICK = 5;
export const UNLOAD_TICKS = 12;
export const QUEUE_MAX = 5;
export const SUPPLY_MAX = 100;
export const BASE_R = 4;             // §16.5 기지 반경 (체비셰프, 건물 원점 기준)
export const TOUCH_R = 1;            // 채집기가 "닿았다"고 보는 거리

// §16.2 채집기 FSM 상태 — 번호는 const 가 소유한다(§17.1 의 표).
export const H_SEEK = C.ST_SEEK;
export const H_TO_ORE = C.ST_TO_ORE;
export const H_MINE = C.ST_MINE;
export const H_TO_BASE = C.ST_TO_BASE;
export const H_UNLOAD = C.ST_UNLOAD;
export const H_IDLE = C.ST_IDLE;

export const DEPOT = [C.HQ, C.REF];  // 자원 반납처 (§25.2)

// ── SPEC §16.3 수입률 (정리 16.1) ───────────────────────────────────────────
// 왕복 d 타일, 속도 v(16.16 타일/틱)인 채집기 한 기의 주기 (틱).
// 세 항은 왕복 이동·채굴·반납이다. d 가 0 이어도 20 + 12 = 32틱이 든다 —
// **정제소를 광맥에 붙여도 상한이 있다.**
export function roundTripTicks(d: number, v: number): number {
  return F.floordiv(F.fp(2 * d), v)
    + F.floordiv(LOAD_MAX, MINE_PER_TICK) + UNLOAD_TICKS;
}

// 크레딧/틱 × 10000. 나눗셈 한 번으로 끝내려고 정수 배율을 쓴다.
export function income10000(d: number, v: number): number {
  return F.floordiv(LOAD_MAX * 10000, roundTripTicks(d, v));
}

// ── SPEC §16.6 기술 트리 = DAG (정리 16.2) ──────────────────────────────────
// 칸(Kahn) 위상 정렬. 진입차수 0 은 **번호 오름차순**으로 꺼낸다.
// 순환이 있으면 null 을 돌려준다 — 조용히 넘어가지 않는다. 기술 트리는
// 데이터이고, 데이터가 잘못되면 터지는 편이 낫다.
export function topoOrder(extra?: Array<[number, number]>): number[] | null {
  const pre: number[][] = [];
  for (let k = 0; k < C.KIND_COUNT; k += 1) pre.push(C.PREREQ[k].slice());
  for (const [k, p] of (extra === undefined ? [] : extra)) {
    pre[k] = pre[k].concat([p]);
  }
  const indeg = pre.map((v) => v.length);
  const out: number[] = [];
  const done = new Array<number>(C.KIND_COUNT).fill(0);
  for (;;) {
    let pick = -1;
    for (let k = 0; k < C.KIND_COUNT; k += 1) {   // 오름차순 선형 탐색 — 16개다
      if (done[k] === 0 && indeg[k] === 0) {
        pick = k;
        break;
      }
    }
    if (pick < 0) break;
    done[pick] = 1;
    out.push(pick);
    for (let k = 0; k < C.KIND_COUNT; k += 1) {
      if (done[k] === 0 && pre[k].indexOf(pick) >= 0) indeg[k] -= 1;
    }
  }
  if (out.length !== C.KIND_COUNT) return null;   // 남은 노드가 있으면 순환이다
  return out;
}

// 플레이어별 크레딧·인구, 타일별 광맥, 건물별 생산 큐.
export class Econ {
  ore: number[];
  credits: number[];
  supplyUsed: number[];
  supplyCap: number[];
  queue: number[][];
  progress: number[];
  oreTarget: number[];

  constructor(m: T.TMap) {
    this.ore = new Array<number>(m.w * m.h).fill(0);
    for (let i = 0; i < m.w * m.h; i += 1) {
      if (m.terrain[i] === T.ORE) this.ore[i] = ORE_PER_TILE;
    }
    this.credits = new Array<number>(C.MAX_PLAYER).fill(0);
    this.supplyUsed = new Array<number>(C.MAX_PLAYER).fill(0);
    this.supplyCap = new Array<number>(C.MAX_PLAYER).fill(0);
    this.queue = [];
    for (let i = 0; i < C.MAX_ENT; i += 1) this.queue.push([]);
    this.progress = new Array<number>(C.MAX_ENT).fill(0);
    this.oreTarget = new Array<number>(C.MAX_ENT).fill(-1);
  }

  // ── SPEC §16.1 자원 ──────────────────────────────────────────────────────
  // **도달 가능한** 광맥 중 d83 최소, 동점이면 타일 번호 오름차순. 없으면 −1.
  // 도달 가능 판정을 빼면 채집기가 바위 건너편 광맥을 잡고 §8.6 의 대체
  // 목표가 제자리를 돌려주어 영원히 선다(SPEC §16.2).
  nearestOre(m: T.TMap, x: number, y: number, kind = 0): number {
    const lab = m.labels(kind);
    const here = m.inMap(x, y) ? lab[y * m.w + x] : -1;
    let best = -1;
    let bd = -1;
    for (let i = 0; i < m.w * m.h; i += 1) {
      if (this.ore[i] <= 0) continue;
      if (here >= 0 && lab[i] !== here) continue;   // 다른 성분 — 걸어서 못 간다
      const d = F.d83(F.fmod(i, m.w) - x, F.floordiv(i, m.w) - y);
      if (bd < 0 || d < bd) {
        bd = d;
        best = i;
      }
    }
    return best;
  }

  // 캔 양을 돌려준다. 다 캐면 그 칸은 모래가 되고 지형 version 이 오른다.
  mine(m: T.TMap, tile: number, amount: number): number {
    let got = this.ore[tile];
    if (got > amount) got = amount;
    this.ore[tile] -= got;
    if (this.ore[tile] <= 0 && m.terrain[tile] === T.ORE) {
      m.setTerrain(F.fmod(tile, m.w), F.floordiv(tile, m.w), T.SAND);
    }
    return got;
  }

  // ── SPEC §16.4 생산 큐 ───────────────────────────────────────────────────
  enqueue(w: S.World, bi: number, kind: number): boolean {
    const p = w.owner[bi];
    if (this.queue[bi].length >= QUEUE_MAX) return false;
    if (!this.canBuild(w, p, kind)) return false;
    if (this.credits[p] < C.COST[kind]) return false;
    if (C.IS_BUILDING[kind] === 0) {
      if (this.supplyUsed[p] + this.reserved(w, p) + C.POP[kind]
          > this.supplyCap[p]) return false;   // 큐에 든 것도 인구를 먹는다
    }
    this.credits[p] -= C.COST[kind];           // 선불
    this.queue[bi].push(kind);
    return true;
  }

  // 큐에 들어 있는 유닛이 예약한 인구. 이것을 빼면 상한이 헐거워진다.
  reserved(w: S.World, p: number): number {
    let n = 0;
    for (let bi = 1; bi < C.MAX_ENT; bi += 1) {
      if (w.alive[bi] === 0 || w.owner[bi] !== p) continue;
      for (const kind of this.queue[bi]) {
        if (C.IS_BUILDING[kind] === 0) n += C.POP[kind];
      }
    }
    return n;
  }

  // 환불은 100 %. 이 덱의 규칙이며, 부분 환불은 반올림 규칙을 하나 더 만든다.
  cancel(w: S.World, bi: number, k: number): number {
    if (k < 0 || k >= this.queue[bi].length) return 0;
    const kind = this.queue[bi][k];
    this.queue[bi] = this.queue[bi].slice(0, k)
      .concat(this.queue[bi].slice(k + 1));
    if (k === 0) this.progress[bi] = 0;
    this.credits[w.owner[bi]] += C.COST[kind];
    return C.COST[kind];
  }

  // 한 틱. 완성된 (건물 인덱스, 종류) 목록을 인덱스 오름차순으로.
  stepProduction(w: S.World): Array<[number, number]> {
    const done: Array<[number, number]> = [];
    for (let bi = 1; bi < C.MAX_ENT; bi += 1) {
      if (w.alive[bi] === 0 || this.queue[bi].length === 0) continue;
      const kind = this.queue[bi][0];
      this.progress[bi] += 1;
      if (this.progress[bi] >= C.BUILD_TICKS[kind]) {
        this.progress[bi] = 0;
        this.queue[bi] = this.queue[bi].slice(1);
        done.push([bi, kind]);
      }
    }
    return done;
  }

  // 선행이 **완성된 채 살아 있는지** 본다. 병영이 부서지면 보병을 못 뽑는다.
  canBuild(w: S.World, p: number, kind: number): boolean {
    for (const need of C.PREREQ[kind]) {
      let found = false;
      for (let j = 1; j < C.MAX_ENT; j += 1) {
        if (w.alive[j] === 1 && w.owner[j] === p && w.kind[j] === need
            && w.hp[j] > 0) {
          found = true;
          break;
        }
      }
      if (!found) return false;
    }
    return true;
  }

  // ── SPEC §16.5 배치 판정 ─────────────────────────────────────────────────
  // 발자국 전체가 건설 가능 지형이고 비어 있고, 기지에서 4타일 안.
  placeable(w: S.World, m: T.TMap, mv: Movement, kind: number, x: number,
            y: number, p: number): boolean {
    const f = C.FOOT[kind];
    for (let dy = 0; dy < f; dy += 1) {
      for (let dx = 0; dx < f; dx += 1) {
        const u = x + dx;
        const v = y + dy;
        if (!m.inMap(u, v)) return false;
        const i = v * m.w + u;
        if (F.bit(m.pass_[i], T.BUILD_BIT) !== 1) return false;
        if (mv.resv[i] !== 0) return false;
      }
    }
    let near = false;
    let anyOwn = false;
    for (let j = 1; j < C.MAX_ENT; j += 1) {
      if (w.alive[j] === 1 && w.owner[j] === p
          && C.IS_BUILDING[w.kind[j]] === 1) {
        anyOwn = true;
        if (F.dinf(w.tx[j] - x, w.ty[j] - y) <= BASE_R) {
          near = true;
          break;
        }
      }
    }
    return near || !anyOwn;              // 첫 건물은 면제
  }

  // ── SPEC §16.7 인구 ──────────────────────────────────────────────────────
  // 유닛은 먹고 건물은 준다. 상한 100. 매 틱 전수로 세도 256칸이다.
  recountSupply(w: S.World): void {
    for (let p = 0; p < C.MAX_PLAYER; p += 1) {
      this.supplyUsed[p] = 0;
      this.supplyCap[p] = 0;
    }
    for (let j = 1; j < C.MAX_ENT; j += 1) {
      if (w.alive[j] === 0 || w.hp[j] <= 0) continue;
      const p = w.owner[j];
      if (p >= C.MAX_PLAYER) continue;
      if (C.IS_BUILDING[w.kind[j]] !== 0) this.supplyCap[p] += C.POP[w.kind[j]];
      else this.supplyUsed[p] += C.POP[w.kind[j]];
    }
    for (let p = 0; p < C.MAX_PLAYER; p += 1) {
      if (this.supplyCap[p] > SUPPLY_MAX) this.supplyCap[p] = SUPPLY_MAX;
    }
  }

  // ── SPEC §16.2 채집기 FSM ────────────────────────────────────────────────
  // 건물 발자국의 어느 칸에라도 한 칸 안으로 붙었는가.
  private touching(w: S.World, i: number, bi: number): boolean {
    const f = C.FOOT[w.kind[bi]];
    let dx = 0;
    if (w.tx[i] < w.tx[bi]) dx = w.tx[bi] - w.tx[i];
    else if (w.tx[i] > w.tx[bi] + f - 1) dx = w.tx[i] - (w.tx[bi] + f - 1);
    let dy = 0;
    if (w.ty[i] < w.ty[bi]) dy = w.ty[bi] - w.ty[i];
    else if (w.ty[i] > w.ty[bi] + f - 1) dy = w.ty[i] - (w.ty[bi] + f - 1);
    return F.dinf(dx, dy) <= TOUCH_R;
  }

  private nearestDepot(w: S.World, i: number): number {
    let best = 0;
    let bd = -1;
    for (let j = 1; j < C.MAX_ENT; j += 1) {
      if (w.alive[j] === 0 || w.owner[j] !== w.owner[i]
          || DEPOT.indexOf(w.kind[j]) < 0 || w.hp[j] <= 0) continue;
      const d = F.d83(w.tx[j] - w.tx[i], w.ty[j] - w.ty[i]);
      if (bd < 0 || d < bd) {
        bd = d;
        best = w.handle(j);
      }
    }
    return best;
  }

  // 건물 발자국을 둘러싼 고리에서 채집기가 붙을 칸 (SPEC §16.2).
  // 건물 원점으로 그냥 명령하면 §8.6 의 대체 목표가 "건물 반대편"이나
  // 심지어 "지금 서 있는 칸"을 고를 수 있다 — d83 동점에서 타일 번호가
  // 작은 쪽이 이기기 때문이다. 그러면 채집기가 적재를 든 채 굳는다.
  dock(w: S.World, m: T.TMap, mv: Movement, i: number,
       bi: number): [number, number] | null {
    const kind = C.MOVE_KIND[w.kind[i]];
    const f = C.FOOT[w.kind[bi]];
    let best: [number, number] | null = null;
    for (const ignoreResv of [false, true]) {
      let bd = -1;
      let bt = -1;
      for (let dy = -1; dy <= f; dy += 1) {
        for (let dx = -1; dx <= f; dx += 1) {
          if (dx >= 0 && dx < f && dy >= 0 && dy < f) continue;  // 발자국 내부
          const x = w.tx[bi] + dx;
          const y = w.ty[bi] + dy;
          if (!m.passableTerrain(x, y, kind)) continue;
          const t = y * m.w + x;
          if (!ignoreResv && mv.resv[t] !== 0 && mv.resv[t] !== w.handle(i)) {
            continue;
          }
          const d = F.d83(x - w.tx[i], y - w.ty[i]);
          if (bd < 0 || d < bd || (d === bd && t < bt)) {
            best = [x, y];
            bd = d;
            bt = t;
          }
        }
      }
      if (best !== null) return best;
    }
    return null;
  }

  // 이동이 포기된 상태 — §13.3 이 24틱 만에 명령을 버렸다는 뜻이다.
  private stuck(w: S.World, mv: Movement, i: number): boolean {
    return mv.goal[i] < 0 && mv.path[i].length === 0 && w.prog[i] === 0;
  }

  // 채집기 한 기의 한 틱. sim 의 3단계에서 핸들 오름차순으로 부른다.
  harvestTick(w: S.World, i: number, m: T.TMap, mv: Movement): void {
    const st = w.state[i];
    const p = w.owner[i];
    if (st === H_SEEK) {
      const tile = this.nearestOre(m, w.tx[i], w.ty[i], C.MOVE_KIND[w.kind[i]]);
      if (tile < 0) {
        w.state[i] = H_IDLE;               // 캘 것이 없으면 멈춘다
        return;
      }
      this.oreTarget[i] = tile;
      mv.order(i, F.fmod(tile, m.w), F.floordiv(tile, m.w));
      w.state[i] = H_TO_ORE;
      return;
    }
    if (st === H_TO_ORE) {
      const t = this.oreTarget[i];
      if (t < 0 || this.ore[t] <= 0) {
        w.state[i] = H_SEEK;
        return;
      }
      if (F.dinf(F.fmod(t, m.w) - w.tx[i],
                 F.floordiv(t, m.w) - w.ty[i]) <= TOUCH_R) {
        w.state[i] = H_MINE;
      } else if (this.stuck(w, mv, i)) {
        mv.order(i, F.fmod(t, m.w), F.floordiv(t, m.w));  // 길막에 포기했으면
      }
      return;
    }
    if (st === H_MINE) {
      const room = LOAD_MAX - w.load[i];
      const wantAmt = MINE_PER_TICK < room ? MINE_PER_TICK : room;
      const got = this.mine(m, this.oreTarget[i], wantAmt);
      w.load[i] += got;
      if (w.load[i] >= LOAD_MAX) {
        const h = this.nearestDepot(w, i);
        if (h === 0) return;               // 반납처가 없으면 실어 둔 채 기다린다
        w.target[i] = h;
        const bi = F.floordiv(h, 256);
        const d = this.dock(w, m, mv, i, bi);
        if (d !== null) mv.order(i, d[0], d[1]);
        w.state[i] = H_TO_BASE;
      } else if (got === 0) {
        w.state[i] = H_SEEK;               // 칸이 말랐다
      }
      return;
    }
    if (st === H_TO_BASE) {
      const h = w.target[i];
      if (!w.valid(h)) {
        w.state[i] = w.load[i] < LOAD_MAX ? H_MINE : H_TO_BASE;
        w.target[i] = this.nearestDepot(w, i);
        if (w.target[i] === 0) w.state[i] = H_SEEK;
        return;
      }
      const bi = F.floordiv(h, 256);
      if (this.touching(w, i, bi)) {
        w.state[i] = H_UNLOAD;
        w.timer[i] = UNLOAD_TICKS;
      } else if (this.stuck(w, mv, i)) {
        const d = this.dock(w, m, mv, i, bi);
        if (d !== null) mv.order(i, d[0], d[1]);
      }
      return;
    }
    if (st === H_UNLOAD) {
      w.timer[i] -= 1;
      if (w.timer[i] <= 0) {
        this.credits[p] += w.load[i];
        w.load[i] = 0;
        w.state[i] = H_SEEK;
      }
    }
  }
}

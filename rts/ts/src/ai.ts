// AI — 영향 지도·유령 기억·건물 배치·빌드 오더·정찰 (SPEC §17).
//
//    AI 는 **시뮬레이션의 일부**다. sim.step 안에서 돌고 명령을 자기 큐에 바로
//    넣는다. 네트워크 지연을 거치지 않아도 되는 이유는 모든 기계가 같은 AI 를
//    같은 틱에 돌리기 때문이다 — 결정론이 통신을 대신한다.
//
//    AI 는 안개를 존중한다(§17.3). 이 제약이 없으면 AI 가 전지적이 되고,
//    그건 게임이 아니다. 대신 마지막으로 본 위치를 30틱 기억해서 정찰에
//    값어치를 만든다.

import * as CB from './combat';
import * as C from './const';
import * as E from './econ';
import * as F from './fixed';
import { Fog } from './fog';
import { Movement } from './move';
import * as SEL from './select';
import * as S from './spatial';
import { TMap } from './tmap';

export const GHOST_TICKS = 30;      // §17.3 마지막으로 본 위치를 기억하는 틱
export const PLACE_R = 12;          // §17.4 건물 후보 반경 (타일)
export const CHASE_R = 3;           // §17.1 추격은 사거리 + 이만큼까지
export const SPREAD = 3;            // §17.2 확산 반복 횟수
export const FLEE_NUM = 1;          // §17.1 hp 가 1/4 아래면 도망
export const FLEE_DEN = 4;
export const ARMY_MIN = 6;          // §17.5 이만큼 모이면 나간다
export const HARV_MIN = 4;

// 빌드 오더가 돌려주는 행동. 첫 칸이 이름이고 나머지는 인자다.
export type Act = Array<string | number>;

// ── SPEC §17.2 영향 지도 ────────────────────────────────────────────────────
// 전력 = 기본 + 관통 + hp/4. 이 덱의 규칙이다.
export function strength(w: S.World, i: number): number {
  return C.BASIC[w.kind[i]] + C.PIERCE[w.kind[i]] + F.floordiv(w.hp[i], 4);
}

// 3회 확산. 가중치 4 + 8 = 12 로 나눈다.
// 정수 나눗셈의 내림 때문에 매 반복 조금씩 줄어드는데, 그 감쇠가 곧
// "멀수록 영향이 적다"이다. 별도의 감쇠 계수를 두지 않는 이유가 이것이다.
function spread(m: TMap, seed: number[]): number[] {
  let cur = seed;
  for (let k = 0; k < SPREAD; k += 1) {
    const nxt = new Array<number>(m.w * m.h).fill(0);
    for (let y = 0; y < m.h; y += 1) {
      for (let x = 0; x < m.w; x += 1) {
        let acc = 4 * cur[y * m.w + x];
        for (let d = 0; d < 8; d += 1) {
          const u = x + F.DX[d];
          const v = y + F.DY[d];
          if (u >= 0 && u < m.w && v >= 0 && v < m.h) acc += cur[v * m.w + u];
        }
        nxt[y * m.w + x] = F.floordiv(acc, 12);
      }
    }
    cur = nxt;
  }
  return cur;
}

function seeds(w: S.World, fog: Fog, p: number, m: TMap,
               enemyOnly: boolean): number[] {
  const seed = new Array<number>(m.w * m.h).fill(0);
  for (let i = 1; i < C.MAX_ENT; i += 1) {
    if (w.alive[i] === 0 || w.hp[i] <= 0) continue;
    const t = w.ty[i] * m.w + w.tx[i];
    if (w.owner[i] === p) {
      if (!enemyOnly) seed[t] += strength(w, i);
    } else if (fog.visible(p, t)) {          // 보이는 적만 (§17.3)
      seed[t] += enemyOnly ? strength(w, i) : -strength(w, i);
    }
  }
  return seed;
}

export function influence(w: S.World, fog: Fog, p: number, m: TMap): number[] {
  return spread(m, seeds(w, fog, p, m, false));
}

export function threat(w: S.World, fog: Fog, p: number, m: TMap): number[] {
  return spread(m, seeds(w, fog, p, m, true));
}

// ── SPEC §17.3 유령 (마지막으로 본 위치) ────────────────────────────────────
// 적을 마지막으로 본 자리를 30틱 기억한다. 건물 자리는 잊지 않는다 —
// 건물은 움직이지 않으므로 한 번 본 것을 잊는 편이 오히려 거짓말이다.
export class Memory {
  w: number;
  h: number;
  ttl: number[];
  baseTile: number;

  constructor(w: number, h: number) {
    this.w = w;
    this.h = h;
    this.ttl = new Array<number>(w * h).fill(0);
    this.baseTile = -1;
  }

  update(world: S.World, fog: Fog, p: number): void {
    for (let i = 0; i < this.ttl.length; i += 1) {
      if (this.ttl[i] > 0) this.ttl[i] -= 1;
    }
    for (let j = 1; j < C.MAX_ENT; j += 1) {
      if (world.alive[j] === 0 || world.owner[j] === p || world.hp[j] <= 0) {
        continue;
      }
      const t = world.ty[j] * this.w + world.tx[j];
      if (!fog.visible(p, t)) continue;
      this.ttl[t] = GHOST_TICKS;
      if (C.IS_BUILDING[world.kind[j]] !== 0) {
        if (this.baseTile < 0 || t < this.baseTile) this.baseTile = t;
      }
    }
  }

  ghosts(): number[] {
    const out: number[] = [];
    for (let i = 0; i < this.ttl.length; i += 1) {
      if (this.ttl[i] > 0) out.push(i);
    }
    return out;
  }

  enemyBaseKnown(): boolean {
    return this.baseTile >= 0;
  }

  enemyBase(): [number, number] | null {
    if (this.baseTile < 0) return null;
    return [F.fmod(this.baseTile, this.w), F.floordiv(this.baseTile, this.w)];
  }
}

// ── SPEC §17.4 건물 배치 ────────────────────────────────────────────────────
// 점수 — fire 항이 벽에 붙지 않게 하고, threat 항이 전선을 피하게 한다.
export function placeScore(m: TMap, fire: number[], thr: number[],
                           kind: number, x: number, y: number, cx: number,
                           cy: number, ore: number): number {
  const i = y * m.w + x;
  let sc = 100 - 3 * F.d83(x - cx, y - cy) + 2 * fire[i] - thr[i];
  if (kind === C.REF && ore >= 0) {
    sc += 40 - 8 * F.d83(F.fmod(ore, m.w) - x, F.floordiv(ore, m.w) - y);
  }
  return sc;
}

// 기지 중심 반경 12 안에서 점수 최대, 동점이면 타일 번호 최소.
export function bestPlacement(w: S.World, m: TMap, mv: Movement, ec: E.Econ,
                              fire: number[], thr: number[], p: number,
                              kind: number,
                              centre: [number, number]): [number, number] | null {
  const cx = centre[0];
  const cy = centre[1];
  const ore = kind === C.REF ? ec.nearestOre(m, cx, cy) : -1;
  let best: [number, number] | null = null;
  let bs = 0;
  let bi = 0;
  let has = false;
  for (let y = cy - PLACE_R; y <= cy + PLACE_R; y += 1) {
    for (let x = cx - PLACE_R; x <= cx + PLACE_R; x += 1) {
      if (!m.inMap(x, y)) continue;
      if (F.dinf(x - cx, y - cy) > PLACE_R) continue;
      if (!ec.placeable(w, m, mv, kind, x, y, p)) continue;
      const i = y * m.w + x;
      const sc = placeScore(m, fire, thr, kind, x, y, cx, cy, ore);
      if (!has || sc > bs || (sc === bs && i < bi)) {
        best = [x, y];
        bs = sc;
        bi = i;
        has = true;
      }
    }
  }
  return best;
}

// ── SPEC §17.5 빌드 오더 ────────────────────────────────────────────────────
function countKind(w: S.World, p: number, kind: number): number {
  let n = 0;
  for (let i = 1; i < C.MAX_ENT; i += 1) {
    if (w.alive[i] === 1 && w.owner[i] === p && w.kind[i] === kind
        && w.hp[i] > 0) n += 1;
  }
  return n;
}

function armyCount(w: S.World, p: number): number {
  let n = 0;
  for (let i = 1; i < C.MAX_ENT; i += 1) {
    if (w.alive[i] === 1 && w.owner[i] === p && w.hp[i] > 0
        && C.IS_BUILDING[w.kind[i]] === 0 && C.BASIC[w.kind[i]] > 0) n += 1;
  }
  return n;
}

// 그 유닛을 뽑을 수 있는 내 건물 중 인덱스가 가장 작은 것. 없으면 -1.
export function producer(w: S.World, ec: E.Econ, p: number,
                         kind: number): number {
  if (C.PREREQ[kind].length === 0) return -1;
  const need = C.PREREQ[kind][0];
  for (let i = 1; i < C.MAX_ENT; i += 1) {
    if (w.alive[i] === 1 && w.owner[i] === p && w.kind[i] === need
        && w.hp[i] > 0 && ec.queue[i].length < E.QUEUE_MAX) return i;
  }
  return -1;
}

function canTrain(w: S.World, ec: E.Econ, p: number, kind: number): number {
  const bi = producer(w, ec, p, kind);
  if (bi < 0 || !ec.canBuild(w, p, kind)) return -1;
  if (ec.credits[p] < C.COST[kind]) return -1;
  if (ec.supplyUsed[p] + C.POP[kind] > ec.supplyCap[p]) return -1;
  return bi;
}

function canBuildRule(w: S.World, ec: E.Econ, p: number, kind: number,
                      credits: number): boolean {
  if (ec.credits[p] < credits || !ec.canBuild(w, p, kind)) return false;
  return true;
}

export type Rule = (w: S.World, ec: E.Econ, mem: Memory, p: number) => Act | null;

const ruleHarvester: Rule = (w, ec, _mem, p) => {
  if (countKind(w, p, C.HARV) >= HARV_MIN) return null;
  const bi = canTrain(w, ec, p, C.HARV);
  return bi >= 0 ? ['TRAIN', C.HARV, bi] : null;
};

const ruleRefinery: Rule = (w, ec, _mem, p) => {
  if (countKind(w, p, C.REF) > 0) return null;
  return canBuildRule(w, ec, p, C.REF, 300) ? ['BUILD', C.REF] : null;
};

const ruleBarracks: Rule = (w, ec, _mem, p) => {
  if (countKind(w, p, C.BARR) > 0) return null;
  return canBuildRule(w, ec, p, C.BARR, 400) ? ['BUILD', C.BARR] : null;
};

const ruleInfantry: Rule = (w, ec, _mem, p) => {
  if (armyCount(w, p) >= ARMY_MIN) return null;
  const bi = canTrain(w, ec, p, C.INF);
  return bi >= 0 ? ['TRAIN', C.INF, bi] : null;
};

const ruleAttack: Rule = (w, _ec, mem, p) => {
  if (armyCount(w, p) < ARMY_MIN || !mem.enemyBaseKnown()) return null;
  const b = mem.enemyBase() as [number, number];
  return ['ATTACK', b[0], b[1]];
};

const ruleDefend: Rule = () => ['DEFEND'];

// 일곱째 줄 — 실험용이다(§17.5). 여섯 줄짜리 AI 는 인구 10 에서 멈춘다.
const rulePower: Rule = (w, ec, _mem, p) => {
  if (ec.supplyCap[p] - ec.supplyUsed[p] >= 2) return null;
  if (ec.supplyCap[p] >= E.SUPPLY_MAX) return null;
  return canBuildRule(w, ec, p, C.POW, 200) ? ['BUILD', C.POW] : null;
};

// 여섯 줄이 AI 전부다. 위에서부터 훑어 처음으로 조건을 만족하는 하나를 실행한다.
export const RULES: Rule[] = [ruleHarvester, ruleRefinery, ruleBarracks,
                              ruleInfantry, ruleAttack, ruleDefend];
// 발전소 한 줄을 더한 판. 18부가 두 실행을 나란히 놓는다.
export const RULES7: Rule[] = [ruleHarvester, ruleRefinery, ruleBarracks,
                               rulePower, ruleInfantry, ruleAttack, ruleDefend];

export function buildOrder(w: S.World, ec: E.Econ, mem: Memory, p: number,
                           rules?: Rule[] | null): Act {
  for (const rule of (rules === undefined || rules === null ? RULES : rules)) {
    const act = rule(w, ec, mem, p);
    if (act !== null) return act;
  }
  return ['DEFEND'];
}

// ── SPEC §17.1 유닛 FSM ─────────────────────────────────────────────────────
// 한 유닛의 상태 전이. 평가 순서가 곧 우선순위다.
// 세 번째 인자(맵)는 쓰이지 않지만 파이썬 원본과 같은 자리에 남겨 둔다 —
// 세 언어의 호출부가 같은 모양이어야 sim 의 2단계를 눈으로 대조할 수 있다.
export function unitTick(w: S.World, i: number, _m: TMap, mv: Movement,
                         orders: SEL.Orders): void {
  const kind = w.kind[i];
  if (C.IS_BUILDING[kind] !== 0) return;
  if (kind === C.HARV) {
    if (w.hp[i] * FLEE_DEN < C.HP[kind] * FLEE_NUM) {     // hp 25 % 아래
      let h = 0;
      for (let j = 1; j < C.MAX_ENT; j += 1) {
        if (w.alive[j] === 1 && w.owner[j] === w.owner[i]
            && E.DEPOT.indexOf(w.kind[j]) >= 0 && w.hp[j] > 0) {
          h = j;
          break;
        }
      }
      w.state[i] = C.ST_FLEE;
      if (h !== 0) mv.order(i, w.tx[h], w.ty[h]);
      return;
    }
    if (w.state[i] === C.ST_FLEE) w.state[i] = C.ST_SEEK;  // 회복하면 하던 일로
    return;
  }
  const [tgt, approach] = CB.pickTarget(w, i, 0, w.state[i] === C.ST_MOVE);
  if (tgt !== 0 && !approach) {
    w.target[i] = tgt;
    w.state[i] = C.ST_ATTACK;
    return;
  }
  if (w.state[i] === C.ST_ATTACK || w.state[i] === C.ST_MOVE) {
    const cur = w.target[i];
    if (w.valid(cur)) {
      const j = S.index(cur);
      const d = F.dinf(w.tx[j] - w.tx[i], w.ty[j] - w.ty[i]);
      if (d <= C.RANGE[kind] + CHASE_R) {
        w.state[i] = C.ST_MOVE;               // 추격
        mv.order(i, w.tx[j], w.ty[j]);
        orders.push(i, [SEL.ATTACK_MOVE, w.tx[j], w.ty[j], cur], false);
        return;
      }
    }
    w.target[i] = 0;
    w.state[i] = C.ST_IDLE;
    return;
  }
  if (tgt !== 0) {
    w.target[i] = tgt;
    w.state[i] = C.ST_MOVE;
    return;
  }
  if (mv.path[i].length === 0 && mv.goal[i] < 0) w.state[i] = C.ST_IDLE;
}

// ── SPEC §17.6 정찰 ─────────────────────────────────────────────────────────
// 미탐험 클러스터의 중심, **클러스터 번호 오름차순**.
// 정찰병이 죽으면 다음 유닛이 목록의 다음 항목부터 이어 간다 —
// 목록이 결정론적이어야 그 이어받기가 세 언어에서 같다.
export function scoutTargets(m: TMap, fog: Fog, p: number): Array<[number, number]> {
  const out: Array<[number, number]> = [];
  const cw = Math.floor((m.w + C.CLUSTER - 1) / C.CLUSTER);
  const chh = Math.floor((m.h + C.CLUSTER - 1) / C.CLUSTER);
  for (let cy = 0; cy < chh; cy += 1) {
    for (let cx = 0; cx < cw; cx += 1) {
      let seen = false;
      for (let y = cy * C.CLUSTER; y < Math.min(m.h, (cy + 1) * C.CLUSTER); y += 1) {
        for (let x = cx * C.CLUSTER; x < Math.min(m.w, (cx + 1) * C.CLUSTER); x += 1) {
          if (fog.explored[p][y * m.w + x] !== 0) {
            seen = true;
            break;
          }
        }
        if (seen) break;
      }
      if (!seen) {
        out.push([cx * C.CLUSTER + Math.floor(C.CLUSTER / 2),
                  cy * C.CLUSTER + Math.floor(C.CLUSTER / 2)]);
      }
    }
  }
  return out;
}

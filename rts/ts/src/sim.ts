// 시뮬레이션 — 유일한 진입점 (SPEC §18).
//
//    **상태를 바꾸는 함수는 `step` 하나뿐이다.** 렌더는 읽기만 하고, UI 는 명령을
//    만들 뿐이며, AI 조차 같은 자료형의 명령으로 말한다. 이 규율이 19부(락스텝)와
//    20부(리플레이)의 전제 전부다.
//
//    틱의 아홉 단계 순서는 명세다. 바꾸면 골든이 통째로 틀어진다.

import * as AI from './ai';
import * as CB from './combat';
import * as C from './const';
import * as E from './econ';
import * as F from './fixed';
import * as FL from './flow';
import { Fog } from './fog';
import * as M from './move';
import { LCG } from './rng';
import * as SEL from './select';
import * as S from './spatial';
import * as T from './tmap';

// ── §18.3 이벤트 종류 ───────────────────────────────────────────────────────
export const EV_SPAWN = 0;
export const EV_DIE = 1;
export const EV_HIT = 2;
export const EV_BUILD_DONE = 3;
export const EV_MINE = 4;
export const EV_UNLOAD = 5;
export const EV_ORDER = 6;
export const EV_WIN = 7;
export const EV_MESSAGE = 8;

// ── §18.5 트리거 ────────────────────────────────────────────────────────────
export const CT_TICK_GE = 0;
export const CT_UNIT_COUNT = 1;
export const CT_BUILDING_DESTROYED = 2;
export const CT_AREA_ENTERED = 3;
export const CT_CREDITS_GE = 4;
export const AC_SPAWN = 0;
export const AC_MESSAGE = 1;
export const AC_WIN = 2;
export const AC_LOSE = 3;
export const AC_REVEAL = 4;
export const CMP_GE = 0;
export const CMP_LE = 1;
export const CMP_EQ = 2;

export const AI_PERIOD = 15;                 // §17.5 빌드 오더 평가 주기

export const CMD: Record<string, number> = {
  MOVE: SEL.MOVE, AMOVE: SEL.ATTACK_MOVE, ATTACK: SEL.ATTACK,
  HARVEST: SEL.HARVEST, STOP: SEL.STOP, HOLD: SEL.HOLD,
  BUILD: SEL.BUILD, TRAIN: SEL.TRAIN,
};

// 명령은 §18.1 의 여섯 칸 (플레이어, 발령자 핸들, 종류, a, b, c).
export type Order = number[];

// 트리거 인자는 길이가 들쭉날쭉하다 — 없는 칸은 0 으로 읽는다.
function at(t: number[], k: number): number {
  return k < t.length ? t[k] : 0;
}

export class Script {
  ticks: number;
  players: number;
  lines: Array<[number, number, string, string, number, number, number]>;

  constructor() {
    this.ticks = 0;
    this.players = 0;
    this.lines = [];
  }
}

// §18.6 시나리오 스크립트. `#` 로 시작하는 줄은 주석이다.
export function parseScript(text: string): Script {
  const sc = new Script();
  for (const raw of text.split('\n')) {
    const ln = raw.trim();
    if (ln === '' || ln.indexOf('#') === 0 || ln.indexOf('RTSS') === 0) continue;
    if (ln.indexOf('ticks ') === 0) {
      sc.ticks = parseInt(ln.split(/\s+/)[1], 10);
      continue;
    }
    if (ln.indexOf('players ') === 0) {
      sc.players = parseInt(ln.split(/\s+/)[1], 10);
      continue;
    }
    const p = ln.split(/\s+/);
    sc.lines.push([parseInt(p[0], 10), parseInt(p[1], 10), p[2], p[3],
                   parseInt(p[4], 10), parseInt(p[5], 10), parseInt(p[6], 10)]);
  }
  return sc;
}

// FNV-1a 를 흘려 넣는다 — 바이트열을 통째로 만들지 않는 편이 메모리와 시간이
// 덜 든다 (SPEC §18.4).
class Hash {
  h: number;

  constructor() {
    this.h = F.FNV_OFFSET;
  }

  // Math.trunc 를 한 번 거치는 이유는 §19.4 의 주입 버그 때문이다. 그때만
  // prog·px·py 가 실수가 되고, 해시는 그 잘린 값을 그대로 본다.
  b1(v: number): void {
    this.h = F.fnv1aStep(this.h, F.fmod(Math.trunc(v), 256));
  }

  b2(v: number): void {
    const x = F.fmod(Math.trunc(v), 65536);   // 음수는 2의 보수로 접는다
    this.b1(F.floordiv(x, 256));
    this.b1(F.fmod(x, 256));
  }

  b4(v: number): void {
    const x = F.fmod(Math.trunc(v), 4294967296);
    this.b2(F.floordiv(x, 65536));
    this.b2(F.fmod(x, 65536));
  }
}

export class Sim {
  m: T.TMap;
  players: number;
  w: S.World;
  fog: Fog;
  ec: E.Econ;
  mv: M.Movement;
  pj: CB.Projectiles;
  rng: LCG;
  orders: SEL.Orders;
  mem: AI.Memory[];
  aiEnabled: boolean[];
  aiRules: AI.Rule[] | null;
  tick: number;
  events: number[][];
  triggers: Array<[number[], number[], boolean]>;
  fired: boolean[];
  winner: number;
  loser: number[];
  lastHit: number[];
  lastSpawn: number[];
  sightAt: number[];
  private hadBuilding: boolean[];
  private mapHashValue: number;
  mapHashVersion: number;
  private fireField: number[] | null;
  private fireVersion: number;

  constructor(m: T.TMap, seed: number, players = 2, floatBug = false) {
    this.m = m;
    this.players = players;
    this.w = new S.World(m.w, m.h);
    this.fog = new Fog(m.w, m.h);
    this.ec = new E.Econ(m);
    this.mv = new M.Movement(this.w, m, floatBug);
    this.pj = new CB.Projectiles(m.w);
    this.rng = new LCG(seed);
    this.orders = new SEL.Orders();
    this.mem = [];
    for (let p = 0; p < C.MAX_PLAYER; p += 1) {
      this.mem.push(new AI.Memory(m.w, m.h));
    }
    this.aiEnabled = new Array<boolean>(C.MAX_PLAYER).fill(false);
    this.aiRules = null;                     // null 이면 §17.5 의 여섯 줄
    this.tick = 0;
    this.events = [];
    this.triggers = [];
    this.fired = [];
    this.winner = -1;
    this.loser = [];
    this.lastHit = new Array<number>(C.MAX_ENT).fill(0);
    this.lastSpawn = new Array<number>(C.MAX_PLAYER).fill(0);
    this.sightAt = new Array<number>(C.MAX_ENT).fill(-1);   // 안개가 아는 위치
    this.hadBuilding = new Array<boolean>(C.MAX_PLAYER).fill(false);
    this.mapHashValue = 0;
    this.mapHashVersion = -1;
    this.fireField = null;
    this.fireVersion = -1;
  }

  // ── 생성·소멸 ────────────────────────────────────────────────────────────
  spawn(p: number, kind: number, x: number, y: number): number {
    const h = this.w.spawn(p, kind, x, y);
    if (h === 0) return 0;
    const i = S.index(h);
    this.w.hp[i] = C.HP[kind];               // 태어나는 것은 정격 hp 로
    this.mv.claim(i);
    this.fog.addSight(p, x, y, C.SIGHT[kind]);
    this.sightAt[i] = y * this.m.w + x;
    if (C.IS_BUILDING[kind] !== 0) this.hadBuilding[p] = true;
    else this.lastSpawn[p] = h;
    if (kind === C.HARV) this.w.state[i] = C.ST_SEEK;
    return h;
  }

  // §25.4 시작 조건. 골든 시나리오는 스크립트가 몰므로 AI 를 끈다 —
  // 한 지갑을 둘이 쓰면 서로의 건설을 굶긴다(§18.6).
  setupStart(ai = true): void {
    const n = Math.min(this.players, this.m.starts.length);
    for (let p = 0; p < n; p += 1) {
      const sx = this.m.starts[p][0];
      const sy = this.m.starts[p][1];
      this.spawn(p, C.HQ, sx - 1, sy - 1);
      for (let k = 0; k < C.START_HARV; k += 1) {
        let x = sx + 2;
        let y = sy + 1 + k;
        if (!this.m.passableTerrain(x, y, C.MOVE_KIND[C.HARV])) {
          x = sx;
          y = sy + 2 + k;
        }
        this.spawn(p, C.HARV, x, y);
      }
      this.ec.credits[p] = C.START_CREDITS;
      this.aiEnabled[p] = ai;
    }
    this.ec.recountSupply(this.w);
  }

  addTrigger(cond: number[], act: number[], once: boolean): void {
    this.triggers.push([cond, act, once]);
    this.fired.push(false);
  }

  // ── SPEC §18.2 틱의 아홉 단계 ────────────────────────────────────────────
  step(orders: Order[]): number {
    this.events = [];
    this.tick += 1;
    this.checkSorted(orders);
    for (const o of orders) this.applyOrder(o);   // 1. 명령 적용
    this.phaseAi();                               // 2. AI
    this.phaseEcon();                             // 3. 생산·경제
    this.mv.step();                               // 4. 이동
    this.phaseCombat();                           // 5. 전투
    this.phaseDeath();                            // 6. 사망
    this.phaseSight();                            // 7. 시야
    this.phaseTriggers();                         // 8. 트리거·승패
    return this.stateHash();                      // 9. 상태 해시
  }

  private checkSorted(orders: Order[]): void {
    for (let k = 1; k < orders.length; k += 1) {
      if (cmpOrder(orders[k - 1], orders[k]) > 0) {
        throw new Error('명령 목록이 정렬되어 있지 않다 (SPEC §18.1)');
      }
    }
  }

  // ── 1단계 ────────────────────────────────────────────────────────────────
  private applyOrder(o: Order): void {
    const p = o[0];
    const issuer = o[1];
    const kind = o[2];
    const a = o[3];
    const b = o[4];
    const c = o[5];
    if (!this.w.valid(issuer)) return;
    const i = S.index(issuer);
    const w = this.w;
    if (w.owner[i] !== p) return;              // 남의 유닛에 내린 명령은 무시
    if (kind === SEL.MOVE || kind === SEL.ATTACK_MOVE) {
      if (this.mv.order(i, a, b)) {
        w.state[i] = C.ST_MOVE;
        w.target[i] = 0;
      }
    } else if (kind === SEL.ATTACK) {
      w.target[i] = c;
      w.state[i] = C.ST_ATTACK;
      if (w.valid(c)) {
        const j = S.index(c);
        this.mv.order(i, w.tx[j], w.ty[j]);
      }
    } else if (kind === SEL.HARVEST) {
      if (w.kind[i] === C.HARV) w.state[i] = C.ST_SEEK;
    } else if (kind === SEL.STOP) {
      this.mv.stop(i);
      this.orders.clear(i);
      w.state[i] = C.ST_IDLE;
    } else if (kind === SEL.HOLD) {
      this.mv.stop(i);
      w.state[i] = C.ST_IDLE;
    } else if (kind === SEL.TRAIN) {
      this.ec.enqueue(w, i, a);
    } else if (kind === SEL.BUILD) {
      this.doBuild(p, a, b, c);
    }
    this.events.push([EV_ORDER, p, issuer, kind]);
  }

  // §16.4 — 통과하면 그 자리에 즉시 엔티티가 생기고 짓기 시작한다.
  private doBuild(p: number, kind: number, x: number, y: number): boolean {
    if (C.IS_BUILDING[kind] === 0) return false;
    if (!this.ec.canBuild(this.w, p, kind)) return false;
    if (this.ec.credits[p] < C.COST[kind]) return false;
    if (!this.ec.placeable(this.w, this.m, this.mv, kind, x, y, p)) {
      this.shove(p, kind, x, y);       // §16.5 — 내 유닛이면 비키게 한다
      return false;
    }
    this.ec.credits[p] -= C.COST[kind];        // 선불
    const h = this.spawn(p, kind, x, y);
    if (h === 0) {
      this.ec.credits[p] += C.COST[kind];
      return false;
    }
    const i = S.index(h);
    this.w.state[i] = C.ST_BUILD;
    this.w.hp[i] = 1;
    this.w.timer[i] = C.BUILD_TICKS[kind];
    return true;
  }

  // 발자국을 막은 내 유닛들에게 바깥으로 한 걸음 명령을 준다 (§16.5).
  // 밀면서 동시에 짓지는 않는다 — 아직 그 칸에 선 유닛 위에 건물을
  // 얹으면 불변식 R 이 깨진다. 다음 재시도에서 자리가 빈다.
  private shove(p: number, kind: number, x: number, y: number): void {
    const w = this.w;
    const m = this.m;
    const f = C.FOOT[kind];
    const cx = x + Math.floor(f / 2);
    const cy = y + Math.floor(f / 2);
    for (let dy = 0; dy < f; dy += 1) {
      for (let dx = 0; dx < f; dx += 1) {
        const u = x + dx;
        const v = y + dy;
        if (!m.inMap(u, v)) continue;
        const h = this.mv.resv[v * m.w + u];
        if (!w.valid(h)) continue;
        const j = S.index(h);
        if (w.owner[j] !== p || C.IS_BUILDING[w.kind[j]] !== 0) continue;
        const out = F.atan8(w.tx[j] - cx, w.ty[j] - cy);
        const pd = M.pushDir(this.mv, j, F.fmod(out + 4, 8));
        if (pd !== M.STOP_DIR) {
          const t = (w.ty[j] + F.DY[pd]) * m.w + w.tx[j] + F.DX[pd];
          this.mv.path[j] = [t];
          this.mv.goal[j] = t;
        }
      }
    }
  }

  // ── 2단계 AI ─────────────────────────────────────────────────────────────
  private phaseAi(): void {
    for (let p = 0; p < this.players; p += 1) {
      if (!this.aiEnabled[p]) continue;
      this.mem[p].update(this.w, this.fog, p);
      if (F.fmod(this.tick, AI_PERIOD) === 0) this.aiDecide(p);
      for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (this.w.alive[i] === 1 && this.w.owner[i] === p
            && C.IS_BUILDING[this.w.kind[i]] === 0) {
          AI.unitTick(this.w, i, this.m, this.mv, this.orders);
        }
      }
    }
  }

  private brushfire(): number[] {
    if (this.fireVersion !== this.m.version) {
      this.fireField = FL.brushfire(this.m, 0);
      this.fireVersion = this.m.version;
    }
    return this.fireField as number[];
  }

  private aiDecide(p: number): void {
    const act = AI.buildOrder(this.w, this.ec, this.mem[p], p, this.aiRules);
    if (act[0] === 'TRAIN') {
      this.ec.enqueue(this.w, act[2] as number, act[1] as number);
    } else if (act[0] === 'BUILD') {
      const centre = this.baseOf(p);
      if (centre === null) return;
      const thr = AI.threat(this.w, this.fog, p, this.m);
      const spot = AI.bestPlacement(this.w, this.m, this.mv, this.ec,
                                    this.brushfire(), thr, p,
                                    act[1] as number, centre);
      if (spot !== null) this.doBuild(p, act[1] as number, spot[0], spot[1]);
    } else if (act[0] === 'ATTACK') {
      for (const i of this.army(p)) {
        this.mv.order(i, act[1] as number, act[2] as number);
        this.w.state[i] = C.ST_MOVE;
      }
    } else {                                   // DEFEND (+ §17.6 정찰)
      const centre = this.baseOf(p);
      if (centre === null) return;
      const army = this.army(p);
      const spots = AI.scoutTargets(this.m, this.fog, p);
      for (let k = 0; k < army.length; k += 1) {
        const i = army[k];
        if (this.w.state[i] !== C.ST_IDLE || this.mv.path[i].length > 0) continue;
        if (k === 0 && spots.length > 0) {
          // 첫 유닛 하나만 정찰. 이것이 없으면 적 기지를 영영 모르고
          // 빌드 오더의 다섯째 줄(전군 공격)이 발화하지 않는다.
          this.mv.order(i, spots[0][0], spots[0][1]);
          this.w.state[i] = C.ST_MOVE;
        } else {
          this.mv.order(i, centre[0], centre[1]);
        }
      }
    }
  }

  private baseOf(p: number): [number, number] | null {
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (this.w.alive[i] === 1 && this.w.owner[i] === p
          && C.IS_BUILDING[this.w.kind[i]] === 1) {
        return [this.w.tx[i], this.w.ty[i]];
      }
    }
    return null;
  }

  private army(p: number): number[] {
    const out: number[] = [];
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (this.w.alive[i] === 1 && this.w.owner[i] === p
          && C.IS_BUILDING[this.w.kind[i]] === 0
          && C.BASIC[this.w.kind[i]] > 0) out.push(i);
    }
    return out;
  }

  // ── 3단계 생산·경제 ──────────────────────────────────────────────────────
  private phaseEcon(): void {
    const w = this.w;
    for (let i = 1; i < C.MAX_ENT; i += 1) {          // 건설 진행
      if (w.alive[i] === 1 && C.IS_BUILDING[w.kind[i]] !== 0
          && w.state[i] === C.ST_BUILD) {
        const total = C.BUILD_TICKS[w.kind[i]];
        let done = total - w.timer[i];
        if (done < 0) done = 0;
        w.hp[i] = 1 + F.floordiv(done * (C.HP[w.kind[i]] - 1), total);
        w.timer[i] -= 1;
        if (w.timer[i] <= 0) {
          w.timer[i] = 0;
          w.hp[i] = C.HP[w.kind[i]];
          w.state[i] = C.ST_IDLE;
          this.events.push([EV_BUILD_DONE, w.owner[i], w.handle(i), w.kind[i]]);
        }
      }
    }
    for (const [bi, kind] of this.ec.stepProduction(w)) {
      const spot = this.freeNear(bi, kind);
      if (spot === null) continue;
      const h = this.spawn(w.owner[bi], kind, spot[0], spot[1]);
      if (h !== 0) this.events.push([EV_SPAWN, w.owner[bi], h, kind]);
    }
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (w.alive[i] === 1 && w.kind[i] === C.HARV) {
        const before = this.ec.credits[w.owner[i]];
        this.ec.harvestTick(w, i, this.m, this.mv);
        if (this.ec.credits[w.owner[i]] > before) {
          this.events.push([EV_UNLOAD, w.owner[i], w.handle(i),
                            this.ec.credits[w.owner[i]] - before]);
        }
      }
    }
    this.ec.recountSupply(w);
  }

  // 건물 둘레에서 빈 칸 하나. y 오름차순, 같은 y 안에서 x 오름차순.
  private freeNear(bi: number, kind: number): [number, number] | null {
    const w = this.w;
    const m = this.m;
    const mk = C.MOVE_KIND[kind];
    const f = C.FOOT[w.kind[bi]];
    for (let r = 1; r < 4; r += 1) {
      for (let y = w.ty[bi] - r; y < w.ty[bi] + f + r; y += 1) {
        for (let x = w.tx[bi] - r; x < w.tx[bi] + f + r; x += 1) {
          if (!m.passableTerrain(x, y, mk)) continue;
          if (this.mv.resv[y * m.w + x] !== 0) continue;
          return [x, y];
        }
      }
    }
    return null;
  }

  // ── 5단계 전투 ───────────────────────────────────────────────────────────
  private phaseCombat(): void {
    const w = this.w;
    const m = this.m;
    const pending: Array<[number, number, number]> = [];
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (w.alive[i] === 0 || w.hp[i] <= 0) continue;
      const kind = w.kind[i];
      if (C.BASIC[kind] === 0) continue;
      if (w.cool[i] > 0) {
        w.cool[i] -= 1;
        continue;
      }
      const [tgt, approach] = CB.pickTarget(w, i, this.lastHit[i],
                                            w.state[i] === C.ST_MOVE);
      if (tgt === 0 || approach) continue;
      const j = S.index(tgt);
      w.target[i] = tgt;
      const dmg = CB.rollDamage(this.rng, C.BASIC[kind], C.PIERCE[kind],
                                C.ARMOUR[w.kind[j]]);
      w.cool[i] = C.RELOAD[kind];
      if (kind === C.ARCHER || kind === C.MORTAR) {
        const pk = kind === C.MORTAR ? CB.ARC : CB.STRAIGHT;
        const sp = kind === C.MORTAR ? 0 : CB.ARROW_SPEED;
        if (!this.pj.launch(pk, w.px[i], w.py[i], w.px[j], w.py[j], sp,
                            tgt, dmg)) {
          pending.push([tgt, w.handle(i), dmg]);
        }
      } else {
        pending.push([tgt, w.handle(i), dmg]);
      }
    }
    for (const [tgt, dmg, dest, , pkind] of this.pj.step()) {
      if (pkind === CB.ARC) {           // 포물선만 스플래시 (아군도 맞는다)
        for (const [hh, dd] of CB.splashHits(w, F.fmod(dest, m.w),
                                             F.floordiv(dest, m.w), dmg)) {
          pending.push([hh, 0, dd]);
        }
      } else if (w.valid(tgt)) {
        pending.push([tgt, 0, dmg]);
      }
    }
    pending.sort(cmpTriple);
    for (const [tgt, src, dmg] of pending) {   // **피해는 여기서 한꺼번에**
      if (!w.valid(tgt)) continue;
      const j = S.index(tgt);
      w.hp[j] -= dmg;
      if (src !== 0) this.lastHit[j] = src;
      this.events.push([EV_HIT, tgt, src, dmg]);
    }
  }

  // ── 6단계 사망 ───────────────────────────────────────────────────────────
  private phaseDeath(): void {
    const w = this.w;
    const m = this.m;
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (w.alive[i] === 0 || w.hp[i] > 0) continue;
      this.events.push([EV_DIE, w.owner[i], w.handle(i), w.kind[i]]);
      const t = this.sightAt[i];               // 안개가 아는 위치에서 반납한다
      if (t >= 0) {
        this.fog.removeSight(w.owner[i], F.fmod(t, m.w), F.floordiv(t, m.w),
                             C.SIGHT[w.kind[i]]);
        this.sightAt[i] = -1;
      }
      const f = C.FOOT[w.kind[i]];
      const building = C.IS_BUILDING[w.kind[i]] === 1;
      const cells: Array<[number, number]> = [];
      for (let dy = 0; dy < f; dy += 1) {
        for (let dx = 0; dx < f; dx += 1) cells.push([w.tx[i] + dx, w.ty[i] + dy]);
      }
      this.mv.unclaim(i);
      if (building) {
        for (const [x, y] of cells) {          // 잔해를 남긴다
          if (m.inMap(x, y)) m.setTerrain(x, y, T.RUBBLE);
        }
      }
      w.kill(w.handle(i));
    }
  }

  // ── 7단계 시야 ───────────────────────────────────────────────────────────
  private phaseSight(): void {
    const w = this.w;
    const m = this.m;
    for (const [i, , nw] of this.mv.crossed) {
      if (w.alive[i] === 0) continue;          // 6단계에서 이미 반납했다
      const r = C.SIGHT[w.kind[i]];
      const src = this.sightAt[i];
      if (src >= 0) {
        this.fog.removeSight(w.owner[i], F.fmod(src, m.w),
                             F.floordiv(src, m.w), r);
      }
      this.fog.addSight(w.owner[i], F.fmod(nw, m.w), F.floordiv(nw, m.w), r);
      this.sightAt[i] = nw;
    }
  }

  // ── 8단계 트리거·승패 ────────────────────────────────────────────────────
  private phaseTriggers(): void {
    for (let k = 0; k < this.triggers.length; k += 1) {
      const [cond, act, once] = this.triggers[k];
      if (once && this.fired[k]) continue;
      if (this.cond(cond)) {
        this.act(act);
        if (once) this.fired[k] = true;
      }
    }
    this.checkVictory();
  }

  private cond(t: number[]): boolean {
    const w = this.w;
    const kind = t[0];
    if (kind === CT_TICK_GE) return this.tick >= at(t, 1);
    if (kind === CT_UNIT_COUNT) {
      const p = at(t, 1);
      const uk = at(t, 2);
      const cmp = at(t, 3);
      const n = at(t, 4);
      let cnt = 0;
      for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] !== 0 && w.owner[i] === p && w.kind[i] === uk) cnt += 1;
      }
      if (cmp === CMP_GE) return cnt >= n;
      if (cmp === CMP_LE) return cnt <= n;
      return cnt === n;
    }
    if (kind === CT_BUILDING_DESTROYED) return !this.hasBuilding(at(t, 1));
    if (kind === CT_AREA_ENTERED) {
      const p = at(t, 1);
      const x = at(t, 2);
      const y = at(t, 3);
      const r = at(t, 4);
      for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] !== 0 && w.owner[i] === p
            && C.IS_BUILDING[w.kind[i]] === 0
            && F.dinf(w.tx[i] - x, w.ty[i] - y) <= r) return true;
      }
      return false;
    }
    if (kind === CT_CREDITS_GE) return this.ec.credits[at(t, 1)] >= at(t, 2);
    return false;
  }

  private act(t: number[]): void {
    const kind = t[0];
    if (kind === AC_SPAWN) {
      const h = this.spawn(at(t, 1), at(t, 2), at(t, 3), at(t, 4));
      if (h !== 0) this.events.push([EV_SPAWN, at(t, 1), h, at(t, 2)]);
    } else if (kind === AC_MESSAGE) {
      this.events.push([EV_MESSAGE, at(t, 1)]);
    } else if (kind === AC_WIN) {
      this.declare(at(t, 1));
    } else if (kind === AC_LOSE) {
      const p = at(t, 1);
      if (this.loser.indexOf(p) < 0) this.loser.push(p);
    } else if (kind === AC_REVEAL) {
      const x = at(t, 1);
      const y = at(t, 2);
      const r = at(t, 3);
      this.fog.addSight(0, x, y, r);
      this.fog.removeSight(0, x, y, r);   // 탐험만 남기고 시야는 돌려준다
    }
  }

  private hasBuilding(p: number): boolean {
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (this.w.alive[i] === 1 && this.w.owner[i] === p
          && C.IS_BUILDING[this.w.kind[i]] === 1) return true;
    }
    return false;
  }

  private declare(p: number): void {
    if (this.winner < 0) {
      this.winner = p;
      this.events.push([EV_WIN, p]);
    }
  }

  // 건물이 전부 파괴되면 패배. 남은 플레이어가 하나면 승리.
  private checkVictory(): void {
    if (this.winner >= 0) return;
    const alive: number[] = [];
    for (let p = 0; p < this.players; p += 1) {
      if (this.hasBuilding(p)) alive.push(p);
      else if (this.hadBuilding[p] && this.loser.indexOf(p) < 0) {
        this.loser.push(p);
      }
    }
    if (alive.length === 1 && this.loser.length > 0) this.declare(alive[0]);
  }

  // ── SPEC §18.4 상태 해시 ─────────────────────────────────────────────────
  // 지형이 바뀔 때만 다시 계산한다. 캐시지만 상태의 순수 함수다.
  mapHash(): number {
    if (this.mapHashVersion !== this.m.version) {
      const hh = new Hash();
      for (const v of this.m.terrain) hh.b1(v);
      for (const v of this.m.pass_) hh.b1(v);
      this.mapHashValue = hh.h;
      this.mapHashVersion = this.m.version;
    }
    return this.mapHashValue;
  }

  stateHash(): number {
    const w = this.w;
    const hh = new Hash();
    hh.b4(this.tick);
    hh.b4(this.rng.s);
    for (let p = 0; p < C.MAX_PLAYER; p += 1) {
      hh.b4(this.ec.credits[p]);
      hh.b2(this.ec.supplyUsed[p]);
      hh.b2(this.ec.supplyCap[p]);
    }
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      hh.b1(w.alive[i]);
      if (w.alive[i] === 0) continue;
      hh.b1(w.owner[i]);
      hh.b1(w.kind[i]);
      hh.b1(w.tx[i]);
      hh.b1(w.ty[i]);
      hh.b2(w.hp[i]);
      hh.b1(w.dir[i]);
      hh.b1(w.state[i]);
      hh.b4(w.px[i]);
      hh.b4(w.py[i]);
      hh.b2(w.target[i]);
      hh.b2(w.load[i]);
      hh.b4(w.prog[i]);
      hh.b2(w.from_t[i]);
      hh.b2(w.to_t[i]);
      hh.b2(w.cool[i]);
      hh.b2(w.timer[i]);
    }
    hh.b2(this.pj.n());
    for (let k = 0; k < this.pj.n(); k += 1) {
      hh.b4(this.pj.x[k]);
      hh.b4(this.pj.y[k]);
      hh.b4(this.pj.vx[k]);
      hh.b4(this.pj.vy[k]);
      hh.b2(this.pj.target[k]);
      hh.b2(this.pj.dmg[k]);
    }
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (w.alive[i] === 0 || C.IS_BUILDING[w.kind[i]] === 0) continue;
      hh.b1(this.ec.queue[i].length);
      for (const k of this.ec.queue[i]) hh.b1(k);
      hh.b2(this.ec.progress[i]);
    }
    const ores: number[] = [];
    for (let i = 0; i < this.ec.ore.length; i += 1) {
      if (this.ec.ore[i] > 0) ores.push(i);
    }
    hh.b2(ores.length);
    for (const i of ores) {
      hh.b2(i);
      hh.b2(this.ec.ore[i]);
    }
    hh.b4(this.mapHash());
    return hh.h;
  }

  // ── SPEC §18.6 선택자 ────────────────────────────────────────────────────
  select(p: number, sel: string): number[] {
    const w = this.w;
    const out: number[] = [];
    if (sel === 'N') {
      const h = this.lastSpawn[p];
      return w.valid(h) ? [h] : [];
    }
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (w.alive[i] === 0 || w.owner[i] !== p) continue;
      const k = w.kind[i];
      if (sel === 'A') {
        if (C.IS_BUILDING[k] === 0) out.push(w.handle(i));
      } else if (sel === 'F') {
        if (C.IS_BUILDING[k] === 0 && C.BASIC[k] > 0) out.push(w.handle(i));
      } else if (sel.indexOf('K') === 0) {
        if (k === parseInt(sel.slice(1), 10)) out.push(w.handle(i));
      }
    }
    out.sort((a, b) => a - b);
    return out;
  }

  // 스크립트도 사람과 똑같은 경로를 지난다 — 뒷문을 내지 않는다.
  scriptOrders(script: Script, tick: number): Order[] {
    const out: Order[] = [];
    for (const [t, p, sel, cmd, a, b, c] of script.lines) {
      if (t !== tick) continue;
      for (const h of this.select(p, sel)) out.push([p, h, CMD[cmd], a, b, c]);
    }
    out.sort(cmpOrder);
    return out;
  }
}

// 튜플 사전식 비교 — 파이썬 list.sort() 의 기본 순서와 같다.
function cmpOrder(a: number[], b: number[]): number {
  for (let i = 0; i < a.length && i < b.length; i += 1) {
    if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  }
  return a.length - b.length;
}

function cmpTriple(a: [number, number, number],
                   b: [number, number, number]): number {
  if (a[0] !== b[0]) return a[0] < b[0] ? -1 : 1;
  if (a[1] !== b[1]) return a[1] < b[1] ? -1 : 1;
  if (a[2] !== b[2]) return a[2] < b[2] ? -1 : 1;
  return 0;
}

// 선택과 명령 — 픽킹·상자 선택·컨트롤 그룹·명령 큐 (SPEC §12).
//
//    이 모듈은 **상태를 바꾸지 않는다.** 명령을 만들어 큐에 넣을 뿐이고,
//    그 큐는 net(§19)의 지연 큐를 거쳐 ORDER_DELAY 틱 뒤에 sim.step 의 인자로
//    들어간다. UI 코드가 sim 의 상태를 직접 건드리는 경로는 존재하지 않는다 —
//    이 규율 하나가 락스텝을 가능하게 한다.

import * as C from './const';
import * as E from './econ';
import * as F from './fixed';
import * as S from './spatial';
import { TMap } from './tmap';

// TRAIN 만 유닛이 아니라 건물에게 내리는 명령이다 — UI·AI·스크립트가 모두
// 같은 자료형으로 sim.step 에 들어와야 락스텝이 성립한다(§12.4).
export const MOVE = 0;
export const ATTACK = 1;
export const ATTACK_MOVE = 2;
export const HARVEST = 3;
export const BUILD = 4;
export const STOP = 5;
export const HOLD = 6;
export const TRAIN = 7;

export const ORDER_MAX = 8;          // §12.4 유닛당 명령 큐 상한
export const SELECT_MAX = 32;        // §12.2 한 번에 고를 수 있는 유닛 수
export const PICK_R = 2;             // §12.1 버킷 질의 반경 (타일)

export type MaskFn = (kind: number, d: number, lx: number, ly: number) => boolean;

// 전장 뷰포트 안인가. 밖이면 패널·미니맵 처리로 넘어간다.
export function inView(sx: number, sy: number): boolean {
  return sx >= C.VIEW_X && sx < C.VIEW_X + C.VIEW_W
    && sy >= C.VIEW_Y && sy < C.VIEW_Y + C.VIEW_H;
}

export function screenToWorld(cam: [number, number], sx: number,
                              sy: number): [number, number] {
  return [sx - C.VIEW_X + cam[0], sy - C.VIEW_Y + cam[1]];
}

// 엔티티의 월드 픽셀 AABB. px·py 는 이동 중에도 정확하다(§13.1).
function box(w: S.World, i: number): [number, number, number, number] {
  const size = C.TILE * C.FOOT[w.kind[i]];
  const x0 = F.fpFloor(w.px[i]);
  const y0 = F.fpFloor(w.py[i]);
  return [x0, y0, x0 + size, y0 + size];
}

// ── SPEC §12.1 픽킹 ─────────────────────────────────────────────────────────
// 한 점이 가리키는 엔티티 핸들. 없으면 0.
// 앞에 그려진 것이 먼저 잡혀야 하므로 y 내림차순, 동점이면 핸들 내림차순으로
// 훑는다 — §23.3 의 그리기 순서를 거꾸로 도는 것이다.
// `mask(kind, dir, lx, ly)` 는 스프라이트 알파 마스크다. AABB 만으로 끝내지
// 않는 이유는 유닛이 사각형이 아니기 때문이다.
export function pick(w: S.World, cam: [number, number], sx: number, sy: number,
                     mask?: MaskFn): number {
  if (!inView(sx, sy)) return 0;
  const [wx, wy] = screenToWorld(cam, sx, sy);
  const cands = w.query(F.floordiv(wx, C.TILE), F.floordiv(wy, C.TILE), PICK_R);
  const order = cands.slice();
  order.sort((a, b) => {
    if (w.py[a] !== w.py[b]) return w.py[b] - w.py[a];
    return w.handle(b) - w.handle(a);
  });
  for (const i of order) {
    const [x0, y0, x1, y1] = box(w, i);
    if (!(x0 <= wx && wx < x1 && y0 <= wy && wy < y1)) continue;
    if (mask !== undefined && !mask(w.kind[i], w.dir[i], wx - x0, wy - y0)) {
      continue;
    }
    return w.handle(i);
  }
  return 0;
}

// ── SPEC §12.2 상자 선택 ────────────────────────────────────────────────────
// 드래그 상자와 겹치는 **내** 엔티티. 유닛이 하나라도 있으면 건물은 뺀다.
// 정렬이 핸들 오름차순인 것은 눈에 보이지 않지만 중요하다 —
// 선택 목록의 순서가 대형 슬롯 배정(§13.5)을 그대로 결정한다.
export function boxSelect(w: S.World, p: number, cam: [number, number],
                          x0in: number, y0in: number, x1in: number,
                          y1in: number): number[] {
  let x0 = x0in;
  let y0 = y0in;
  let x1 = x1in;
  let y1 = y1in;
  if (x1 < x0) {
    const t = x0;
    x0 = x1;
    x1 = t;
  }
  if (y1 < y0) {
    const t = y0;
    y0 = y1;
    y1 = t;
  }
  const [ax0, ay0] = screenToWorld(cam, x0, y0);
  const [ax1, ay1] = screenToWorld(cam, x1, y1);
  const units: number[] = [];
  const builds: number[] = [];
  for (let i = 1; i < C.MAX_ENT; i += 1) {
    if (w.alive[i] === 0 || w.owner[i] !== p) continue;
    const [bx0, by0, bx1, by1] = box(w, i);
    if (bx1 - 1 < ax0 || ax1 < bx0 || by1 - 1 < ay0 || ay1 < by0) continue;
    if (C.IS_BUILDING[w.kind[i]] !== 0) builds.push(w.handle(i));
    else units.push(w.handle(i));
  }
  const out = units.length > 0 ? units : builds;
  out.sort((a, b) => a - b);
  return out.slice(0, SELECT_MAX);
}

// ── SPEC §12.3 컨트롤 그룹 ──────────────────────────────────────────────────
// 저장되는 것은 **핸들**이다. 죽은 유닛은 valid(§7.2)가 자동으로 거른다.
export class Groups {
  g: number[][];

  constructor() {
    this.g = [];
    for (let k = 0; k < 10; k += 1) this.g.push([]);
  }

  set(k: number, sel: number[]): void {
    this.g[k] = sel.slice();
  }

  recall(w: S.World, k: number): number[] {
    return this.g[k].filter((h) => w.valid(h));
  }
}

// ── SPEC §12.4 명령 큐 ──────────────────────────────────────────────────────
// 유닛당 큐 하나. 기본 클릭은 비우고 하나, 시프트 클릭은 뒤에 붙인다.
export class Orders {
  q: number[][][];

  constructor() {
    this.q = [];
    for (let i = 0; i < C.MAX_ENT; i += 1) this.q.push([]);
  }

  push(i: number, order: number[], shift: boolean): void {
    if (order[0] === STOP) {
      this.q[i] = [];                    // STOP 은 큐를 비우고 끝이다
      return;
    }
    if (!shift) this.q[i] = [];
    if (this.q[i].length < ORDER_MAX) this.q[i].push(order);
  }

  pop(i: number): number[] | null {
    if (this.q[i].length === 0) return null;
    const head = this.q[i][0];
    this.q[i] = this.q[i].slice(1);
    return head;
  }

  clear(i: number): void {
    this.q[i] = [];
  }
}

// 우클릭의 문맥 규칙. 판정 순서가 명세다 — 적 정제소는 반납이 아니라 공격이다.
export function contextOrder(w: S.World, ec: E.Econ, m: TMap, p: number,
                             tx: number, ty: number, h: number): number {
  if (w.valid(h)) {
    const j = S.index(h);
    if (w.owner[j] !== p) return ATTACK;
    if (E.DEPOT.indexOf(w.kind[j]) >= 0) return HARVEST;
    return MOVE;
  }
  if (m.inMap(tx, ty) && ec.ore[ty * m.w + tx] > 0) return HARVEST;
  return MOVE;
}

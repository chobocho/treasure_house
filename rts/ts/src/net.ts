// 락스텝 네트워크 — 명령만 보낸다 (SPEC §19).
//
//    유닛 200기의 상태는 매 틱 수 KB 다. 명령은 대개 0개이고, 있어도 한 줄이면
//    20바이트다. 28.8 kbps 모뎀에서 전자는 불가능하고 후자는 여유롭다. 대신
//    **모든 기계가 같은 계산을 해야 한다**는 대가를 치른다.
//
//    지터가 있어도 결과는 같다. 명령의 **실행 틱은 보낼 때 정해지고**, 늦게
//    도착하면 그 틱을 기다릴 뿐이다. 늦게 도착한 명령을 앞당겨 실행하는 경로는
//    존재하지 않는다 — 그런 경로가 하나라도 있으면 락스텝은 그 자리에서 끝난다.

import * as C from './const';
import { LCG } from './rng';

export type Order = number[];

function cmpOrder(a: Order, b: Order): number {
  for (let i = 0; i < a.length && i < b.length; i += 1) {
    if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  }
  return a.length - b.length;
}

export class Net {
  n: number;
  latency: number;
  jitterMax: number;
  rng: LCG;
  box: Map<number, Order[]>;             // 실행 틱 → 명령 목록
  sealed: Map<number, Map<number, number>>;  // 실행 틱 → {플레이어: 도착 틱}
  delay: Map<number, number>;            // (보낸 틱, 플레이어) → 도착 틱
  stalls: number;                        // 실행 틱보다 늦게 닿은 턴의 수

  constructor(nPlayers: number, latency = C.ORDER_DELAY, jitterSeed = 0,
              jitterMax = 0) {
    this.n = nPlayers;
    this.latency = latency;
    this.jitterMax = jitterMax;
    // 지터는 **전용 RNG** 로 만든다. 시뮬레이션 RNG(§3.3)를 쓰면 네트워크
    // 사정이 게임 내용을 바꾸고, 그것이야말로 디싱크의 정의다.
    this.rng = new LCG(jitterSeed);
    this.box = new Map<number, Order[]>();
    this.sealed = new Map<number, Map<number, number>>();
    this.delay = new Map<number, number>();
    this.stalls = 0;
  }

  // 실행 틱은 지터와 무관하다.
  execOf(tick: number, _player: number): number {
    return tick + this.latency;
  }

  arriveOf(tick: number, player: number): number {
    const key = tick * 16 + player;
    if (!this.delay.has(key)) {
      const j = this.jitterMax !== 0 ? this.rng.roll(this.jitterMax + 1) : 0;
      this.delay.set(key, tick + this.latency + j);
      if (j > 0) this.stalls += 1;
    }
    return this.delay.get(key) as number;
  }

  send(tick: number, player: number, order: Order): number {
    this.arriveOf(tick, player);
    const et = this.execOf(tick, player);
    let lst = this.box.get(et);
    if (lst === undefined) {
      lst = [];
      this.box.set(et, lst);
    }
    lst.push(order);
    return et;
  }

  // 빈 턴도 보낸다. 그래야 상대가 영원히 기다리지 않는다.
  flush(tick: number, player: number): number {
    const et = this.execOf(tick, player);
    let d = this.sealed.get(et);
    if (d === undefined) {
      d = new Map<number, number>();
      this.sealed.set(et, d);
    }
    d.set(player, this.arriveOf(tick, player));
    return et;
  }

  // 그 실행 틱의 몫이 **전원** 도착했는가. wall 은 지금 시각(틱)이다.
  ready(execTick: number, wall?: number | null): boolean {
    const d = this.sealed.get(execTick);
    if (d === undefined || d.size !== this.n) return false;
    if (wall === undefined || wall === null) return true;
    const keys = Array.from(d.keys());
    keys.sort((a, b) => a - b);
    for (const p of keys) {
      if ((d.get(p) as number) > wall) return false;
    }
    return true;
  }

  // 그 틱의 명령을 §18.1 의 키로 정렬해 돌려준다. 한 번만 준다.
  take(execTick: number): Order[] {
    const out = this.box.get(execTick);
    this.box.delete(execTick);
    if (out === undefined) return [];
    out.sort(cmpOrder);
    return out;
  }
}

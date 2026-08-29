// room.ts — 방 하나의 게임 규칙. **순수 상태 기계**다.
//
// 이 파일에는 소켓도, 타이머도, Date.now() 도 없다. 바깥에서 (pid, 메시지, now) 를
// 넣으면 (누구에게, 무엇을) 목록이 나온다. 그게 전부다.
// 그렇게 만든 이유는 하나다 — 부 3 의 JS·Go·파이썬 구현과 **같은 골든 벡터**로
// 검증하기 위해서. 시계나 난수를 스스로 읽는 순간 그 검증이 불가능해진다.
// 이 TS 판은 그 벡터를 재현하는 **네 번째 구현**이다.
//
// 규격 전문은 tetris_net/protocol.md, 검증표는 tetris_net/protocol_vectors.json.
//
// 공격 라우팅·탈락·등수는 여기서 다시 쓰지 않고 4부의 Referee 를 그대로 쓴다.
// 로컬 아레나와 온라인 대전이 같은 규칙을 쓴다는 걸 코드로 보장하는 게 목적이다.

import { Referee, type RefEvent } from '../battle.js';
import {
  CFG_DEFAULTS, type RoomCfg, type SeatInfo, type ClientMsg, type Outbound, type ErrCode,
} from './protocol.js';

export const DEFAULTS: RoomCfg = CFG_DEFAULTS;

export type Phase = 'lobby' | 'play' | 'over';

/** 심판이 아는 것(alive/recv/height/place/hits)에 로비가 아는 것을 얹은 좌석. */
export interface RoomSeat {
  pid: number;
  name: string;
  kind: 'human' | 'ai';
  lv: string;
  ready: boolean;
  alive: boolean;
  recv: number;
  height: number;
  place: number;
  hits: { from: number; at: number }[];
}

export class Room {
  readonly cfg: RoomCfg;
  readonly ref: Referee;
  phase: Phase = 'lobby';
  readonly peers = new Set<number>();
  roundSeed = 0;

  constructor(cfg: Partial<RoomCfg> = {}, seed = 1) {
    this.cfg = { ...DEFAULTS, ...cfg };
    // 심판의 좌석 배열이 곧 방의 좌석 배열이다. 두 벌을 따로 두면 반드시 어긋난다.
    this.ref = new Referee(
      { max: this.cfg.max, target: this.cfg.target, cap: this.cfg.cap, hitTTL: this.cfg.hitTTL },
      seed,
    );
  }

  /** 좌석 배열 — 심판의 것을 방의 시각으로 본 것. */
  get seats(): (RoomSeat | null)[] {
    return this.ref.seats as (RoomSeat | null)[];
  }

  /** 규격의 xorshift32. 세 구현이 여기서부터 갈리면 그 뒤는 볼 것도 없다. */
  rng(): number {
    return this.ref.rng();
  }

  // ── 조회 헬퍼 ──
  host(): number {
    let h = 0;
    for (const p of this.peers) if (!h || p < h) h = p;
    return h;
  }

  occupied(): number[] {
    return this.ref.occupied();
  }

  aliveSeats(): number[] {
    return this.ref.aliveSeats();
  }

  mine(pid: number): number[] {
    return this.occupied().filter((i) => (this.seats[i] as RoomSeat).pid === pid);
  }

  /** 로비에 뿌리는 좌석 목록. 내부 필드(recv/hits/height/place)는 내보내지 않는다. */
  seatList(): SeatInfo[] {
    return this.occupied().map((i) => {
      const s = this.seats[i] as RoomSeat;
      return { i, pid: s.pid, name: s.name, kind: s.kind, lv: s.lv, ready: s.ready, alive: s.alive };
    });
  }

  roomMsg(): Outbound[] {
    return [{ to: 0, m: { t: 'room', host: this.host(), seats: this.seatList() } }];
  }

  err(pid: number, code: ErrCode): Outbound[] {
    return [{ to: pid, m: { t: 'err', code } }];
  }

  // ── 진입점 ──
  handle(pid: number, msg: ClientMsg, now: number): Outbound[] {
    if (!msg || typeof msg.t !== 'string') return [];
    // bye 만 peers 에 넣지 않는다 — 나가는 사람을 다시 넣으면 방장이 안 바뀐다.
    if (msg.t === 'bye') return this.onBye(pid, now);
    this.peers.add(pid);
    // msg.t 로 바로 분기해야 TS 가 각 case 안에서 메시지 모양을 좁혀 준다.
    switch (msg.t) {
      case 'seat': return this.onSeat(pid, msg);
      case 'unseat': return this.onUnseat(pid, msg);
      case 'ready': return this.onReady(pid, msg);
      case 'start': return this.onStart(pid);
      case 'atk': return this.onAtk(pid, msg, now);
      case 'st': return this.onSt(pid, msg);
      case 'ko': return this.onKo(pid, msg, now);
      default: return [];
    }
  }

  private onSeat(pid: number, m: Extract<ClientMsg, { t: 'seat' }>): Outbound[] {
    if (this.phase !== 'lobby') return this.err(pid, 'phase');
    let i = m.i === undefined || m.i === null ? -1 : m.i | 0;
    if (i < 0) {
      // 자동 배정 = 가장 앞의 빈 자리
      i = this.seats.findIndex((s) => s === null);
      if (i < 0) return this.err(pid, 'seat');
    } else if (i >= this.seats.length || this.seats[i]) {
      return this.err(pid, 'seat');
    }
    // 자리를 먼저 확정하고 그다음에 PC 당 좌석 수를 본다. 순서를 바꾸면
    // "빈 자리도 없고 내 몫도 찼을 때" 어느 오류가 나가는지가 구현마다 달라진다.
    if (this.mine(pid).length >= this.cfg.perPeer) return this.err(pid, 'full');
    this.seats[i] = {
      pid, name: m.name || '', kind: m.kind === 'ai' ? 'ai' : 'human', lv: m.lv || '',
      ready: false, alive: true, recv: 0, height: 0, place: 0, hits: [],
    };
    return this.roomMsg();
  }

  private onUnseat(pid: number, m: Extract<ClientMsg, { t: 'unseat' }>): Outbound[] {
    if (this.phase !== 'lobby') return this.err(pid, 'phase');
    const i = m.i | 0;
    if (i < 0 || i >= this.seats.length || !this.seats[i] || (this.seats[i] as RoomSeat).pid !== pid) {
      return this.err(pid, 'own');
    }
    this.seats[i] = null;
    return this.roomMsg();
  }

  private onReady(pid: number, m: Extract<ClientMsg, { t: 'ready' }>): Outbound[] {
    if (this.phase !== 'lobby') return this.err(pid, 'phase');
    const v = !!m.v;
    for (const i of this.mine(pid)) (this.seats[i] as RoomSeat).ready = v;
    return this.roomMsg();
  }

  private onStart(pid: number): Outbound[] {
    if (this.phase !== 'lobby') return this.err(pid, 'phase');
    if (pid !== this.host()) return this.err(pid, 'host');
    const occ = this.occupied();
    if (!occ.length) return this.err(pid, 'seat');
    // AI 좌석은 준비를 기다리지 않는다 — 누를 사람이 없다.
    for (const i of occ) {
      const s = this.seats[i] as RoomSeat;
      if (s.kind === 'human' && !s.ready) return this.err(pid, 'ready');
    }

    this.roundSeed = this.rng();
    this.phase = 'play';
    for (const i of occ) {
      const s = this.seats[i] as RoomSeat;
      s.alive = true; s.recv = 0; s.height = 0; s.place = 0; s.hits = [];
    }
    return [{ to: 0, m: { t: 'start', seed: this.roundSeed, seats: this.seatList() } }];
  }

  /** 공격 라우팅 — 심판에게 그대로 넘긴다. 난수 소비 순서가 규격의 생명이다. */
  private onAtk(pid: number, m: Extract<ClientMsg, { t: 'atk' }>, now: number): Outbound[] {
    if (this.phase !== 'play') return this.err(pid, 'phase');
    const i = m.i | 0;
    if (i < 0 || i >= this.seats.length || !this.seats[i]) return this.err(pid, 'own');
    if ((this.seats[i] as RoomSeat).pid !== pid) return this.err(pid, 'own');
    const n = m.n | 0;
    if (n <= 0 || !(this.seats[i] as RoomSeat).alive) return [];

    // 관전 화면이 "누가 누구를" 화살표로 그려야 하므로 피해자에게만 보내지 않는다.
    return this.ref.attack(i, n, now).map((e) => ({ to: 0, m: e as Extract<RefEvent, { t: 'grb' }> }));
  }

  private onSt(pid: number, m: Extract<ClientMsg, { t: 'st' }>): Outbound[] {
    if (this.phase !== 'play') return this.err(pid, 'phase');
    const i = m.i | 0;
    if (i < 0 || i >= this.seats.length || !this.seats[i] || (this.seats[i] as RoomSeat).pid !== pid) {
      return this.err(pid, 'own');
    }
    const s = Array.isArray(m.s) ? m.s : [];
    if (s.length > 4) (this.seats[i] as RoomSeat).height = (s[4] as number) | 0; // 서버가 읽는 칸은 s[0], s[4] 뿐
    const out: Outbound[] = [];
    for (const p of [...this.peers].sort((a, b) => a - b)) {
      if (p !== pid) out.push({ to: p, m: { t: 'st', i, b: m.b, s: m.s } });
    }
    return out;
  }

  /** 좌석 하나를 탈락시킨다. end 까지 낼 수 있으므로 out 을 받아 이어 붙인다. */
  kill(i: number, now: number, out: Outbound[]): void {
    if (this.phase !== 'play') return;
    const events: RefEvent[] = [];
    this.ref.kill(i, now, events);
    for (const e of events) {
      if (e.t === 'end') this.phase = 'over';
      out.push({ to: 0, m: e });
    }
  }

  private onKo(pid: number, m: Extract<ClientMsg, { t: 'ko' }>, now: number): Outbound[] {
    if (this.phase !== 'play') return this.err(pid, 'phase');
    const i = m.i | 0;
    if (i < 0 || i >= this.seats.length || !this.seats[i] || (this.seats[i] as RoomSeat).pid !== pid) {
      return this.err(pid, 'own');
    }
    const out: Outbound[] = [];
    this.kill(i, now, out);
    return out;
  }

  /** PC 가 끊겼다. 로비면 자리를 비우고, 대전 중이면 그 PC 의 좌석이 번호 순으로 전멸한다. */
  private onBye(pid: number, now: number): Outbound[] {
    if (!this.peers.has(pid)) return [];
    this.peers.delete(pid);
    const held = this.mine(pid);
    if (this.phase === 'play') {
      const out: Outbound[] = [];
      for (const i of held) this.kill(i, now, out); // kill 이 phase 를 over 로 바꾸면 뒤는 무시된다
      return out;
    }
    for (const i of held) this.seats[i] = null;
    return this.roomMsg(); // 방장이 바뀔 수 있으므로 항상 알린다
  }
}

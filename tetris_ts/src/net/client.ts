// client.ts — 서버와 말하는 쪽. 전송 계층은 밖에서 넣어 준다.
//
// 브라우저에서는 진짜 WebSocket 이, 덱 데모에서는 같은 페이지 안의 루프백이,
// 테스트에서는 배열 두 개짜리 가짜가 들어온다. 이 파일은 그 셋을 구분하지 못한다 —
// 그래서 "덱에서 도는 것과 서버에 붙는 것이 같은 코드"라는 말이 성립한다.

import {
  PROTOCOL_VERSION,
  type ClientMsg, type ServerMsg, type RoomCfg, type SeatInfo,
} from './protocol.js';

/** 이 파일이 전송 계층에 요구하는 전부. WebSocket 도 루프백도 이 모양이면 된다. */
export interface Transport {
  send(text: string): void;
  close(): void;
  onMessage: ((text: string) => void) | null;
  onOpen: (() => void) | null;
  onClose: (() => void) | null;
}

export type MsgType = ServerMsg['t'];
type Handler = (m: ServerMsg) => void;

/**
 * 방 상태를 들고 서버 메시지를 사건으로 바꿔 주는 얇은 층.
 *
 * 게임 규칙은 하나도 없다. 좌석 목록·방 코드·내 pid 같은 "방에 대한 사실"만 안다.
 */
export class NetClient {
  pid = 0;
  code = '';
  cfg: RoomCfg | null = null;
  seats: SeatInfo[] = [];
  host = 0;
  started = false;
  seed = 0;
  order: number[] | null = null;
  closed = false;

  private readonly handlers = new Map<string, Handler[]>();

  constructor(private readonly t: Transport, readonly name = '') {
    t.onMessage = (s: string): void => this.recv(s);
    t.onOpen = (): void => this.hello();
    t.onClose = (): void => { this.closed = true; };
  }

  /** 메시지 종류별 구독. 같은 종류에 여럿을 붙일 수 있다. */
  on(type: MsgType, fn: Handler): void {
    const a = this.handlers.get(type) ?? [];
    a.push(fn);
    this.handlers.set(type, a);
  }

  private emit(m: ServerMsg): void {
    for (const fn of this.handlers.get(m.t) ?? []) fn(m);
  }

  /** 들어온 메시지로 방 상태를 갱신하고 사건을 낸다. 상태 갱신이 먼저다 —
   *  구독자가 콜백 안에서 this.seats 를 읽을 때 이미 최신이어야 한다. */
  private recv(text: string): void {
    let m: ServerMsg;
    try {
      m = JSON.parse(text) as ServerMsg;
    } catch {
      return; // 깨진 메시지는 조용히 버린다. 우리가 고칠 수 있는 게 없다.
    }
    switch (m.t) {
      case 'hi': this.pid = m.pid; break;
      case 'joined': this.code = m.code; this.cfg = m.cfg; this.pid = m.pid; break;
      case 'room': this.seats = m.seats; this.host = m.host; break;
      case 'start': this.started = true; this.seed = m.seed >>> 0; this.seats = m.seats; break;
      case 'end': this.started = false; this.order = m.order; break;
      default: break;
    }
    this.emit(m);
  }

  send(m: ClientMsg): void {
    if (this.closed) return;
    this.t.send(JSON.stringify(m));
  }

  hello(): void { this.send({ t: 'hello', v: PROTOCOL_VERSION, name: this.name }); }
  create(cfg: Partial<RoomCfg>): void { this.send({ t: 'create', cfg }); }
  join(room: string): void { this.send({ t: 'join', room }); }
  /** i = -1 이면 서버가 가장 앞의 빈 자리를 준다. */
  takeSeat(i: number, kind: 'human' | 'ai', name: string, lv = ''): void {
    this.send({ t: 'seat', i, kind, name, lv });
  }
  unseat(i: number): void { this.send({ t: 'unseat', i }); }
  setReady(v: boolean): void { this.send({ t: 'ready', v }); }
  start(): void { this.send({ t: 'start' }); }
  atk(i: number, n: number): void { this.send({ t: 'atk', i, n }); }
  st(i: number, b: string, s: number[]): void { this.send({ t: 'st', i, b, s }); }
  ko(i: number): void { this.send({ t: 'ko', i }); }
  /** c 는 왕복 시간 측정용 표식 — 서버가 그대로 돌려준다. */
  ping(c = Date.now() & 0xffff): void { this.send({ t: 'ping', c }); }
  bye(): void { this.send({ t: 'bye' }); this.closed = true; this.t.close(); }

  /** 내 pid 가 쥔 좌석 번호들. */
  mine(): number[] {
    return this.seats.filter((s) => s.pid === this.pid).map((s) => s.i);
  }
}

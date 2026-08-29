// match.ts — 내가 쥔 좌석들을 실제로 굴리는 층.
//
// 클라이언트(client.ts)는 방에 대한 사실만 알고, 이 파일이 게임을 돌린다.
// 하는 일은 넷이다: AI 를 두게 하고, 굳을 때마다 공격을 보고하고, 화면 상태를
// 주기적으로 올리고, 서버가 내려준 가비지를 유예 뒤에 얹는다.
//
// 봇 클라이언트(파트 15)와 브라우저가 같은 규칙을 따라야 하므로, 여기에는
// 화면도 소켓도 없다 — 시간(dt)만 밀어 넣으면 나머지는 프로토콜대로 흐른다.

import { Tetris, ST, STATE } from '../core.js';
import { Ai, DEFAULT_WEIGHTS } from '../ai.js';
import { snapshot, packState, type SeatInfo } from './protocol.js';
import type { NetClient } from './client.js';

export interface MatchSeat {
  i: number;
  name: string;
  kind: 'human' | 'ai';
  lv: string;
  game: Tetris;
  ai: Ai | null;
  acc: number;
  lastEvent: number;
  alive: boolean;
  /** 보낸 줄 / 맞은 줄 — 순위표에 쓴다 */
  sent: number;
  recv: number;
}

export interface MatchOptions {
  /** 난이도 이름 → 가중치. weights.json 의 levels 를 그대로 넣는다. */
  weights?: Record<string, readonly number[]>;
  /** AI 착수 간격(ms) */
  intervalMs?: number;
  /** 화면 상태를 올리는 주기(ms). 규격 권장은 초당 10회. */
  stMs?: number;
  /** 가비지 유예(ms). 서버가 준 cfg.delay 를 쓴다. */
  delay?: number;
  /** 지연 배달을 예약하는 함수 — 테스트는 즉시 실행으로 바꿔 넣는다. */
  defer?: (fn: () => void, ms: number) => void;
}

export class Match {
  readonly seats: MatchSeat[] = [];
  private stAcc = 0;

  constructor(private readonly client: NetClient, private readonly opts: MatchOptions = {}) {}

  /** start 를 받았을 때 내 좌석만 골라 판을 세운다. 시드는 전원이 공유한다. */
  begin(seed: number, all: readonly SeatInfo[]): void {
    this.seats.length = 0;
    const levels = this.opts.weights ?? {};
    for (const s of all) {
      if (s.pid !== this.client.pid) continue;
      const game = new Tetris(seed >>> 0);
      const w = levels[s.lv] ?? DEFAULT_WEIGHTS;
      this.seats.push({
        i: s.i, name: s.name, kind: s.kind, lv: s.lv, game,
        ai: s.kind === 'ai' ? new Ai(game, w) : null,
        acc: 0, lastEvent: game.stats[ST.EVENT] as number, alive: true, sent: 0, recv: 0,
      });
    }
    this.stAcc = 0;
  }

  seat(i: number): MatchSeat | undefined {
    return this.seats.find((s) => s.i === i);
  }

  /** 사람 좌석의 키 입력. 누르는 즉시 공격이 나갈 수 있으므로 바로 보고한다. */
  press(i: number, act: number): void {
    const s = this.seat(i);
    if (!s || !s.alive) return;
    s.game.press(act);
    this.report(s);
  }

  release(i: number, act: number): void {
    this.seat(i)?.game.release(act);
  }

  /**
   * 서버가 내려준 가비지.
   *
   * 유예를 지키는 건 서버가 아니라 **클라이언트**다. 그래야 맞은 쪽이 상쇄할 시간을
   * 갖는다. 서버가 실어 보낸 hole 은 쓰지 않는다 — 코어의 pushRows 가 자기 난수로
   * 구멍을 고르고, 관전 화면은 내가 보내는 스냅샷을 그대로 그리므로 어긋날 데가 없다.
   */
  garbage(i: number, n: number): void {
    const s = this.seat(i);
    if (!s || !s.alive) return;
    s.recv += n;
    const defer = this.opts.defer ?? ((fn, ms): void => { setTimeout(fn, ms); });
    defer(() => {
      if (s.alive) s.game.queueGarbage(n);
    }, this.opts.delay ?? 900);
  }

  /** dt 만큼 내 좌석들을 진행시킨다. */
  update(dtMs: number): void {
    const interval = this.opts.intervalMs ?? 220;
    for (const s of this.seats) {
      if (!s.alive) continue;
      if (s.ai) {
        s.acc += dtMs;
        while (s.acc >= interval && (s.game.stats[ST.STATE] as number) === STATE.PLAY) {
          s.acc -= interval;
          s.ai.step();
          this.report(s);
        }
      } else {
        s.game.update(dtMs);
        this.report(s);
      }
      if ((s.game.stats[ST.STATE] as number) !== STATE.PLAY) {
        s.alive = false;
        this.client.ko(s.i);
      }
    }

    this.stAcc += dtMs;
    const every = this.opts.stMs ?? 100;
    if (this.stAcc >= every) {
      this.stAcc = 0;
      for (const s of this.seats) {
        if (!s.alive) continue;
        this.client.st(s.i, snapshot(s.game), packState(s.game));
      }
    }
  }

  /** 조각이 굳었으면 공격을 보고한다. 이벤트 번호로 락을 감지하므로 두 번 보내지 않는다. */
  private report(s: MatchSeat): void {
    const ev = s.game.stats[ST.EVENT] as number;
    if (ev === s.lastEvent) return;
    s.lastEvent = ev;
    const atk = s.game.stats[ST.ATTACK] as number;
    if (atk > 0) {
      s.sent += atk;
      this.client.atk(s.i, atk);
    }
  }
}

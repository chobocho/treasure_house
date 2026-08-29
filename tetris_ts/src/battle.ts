// battle.ts — 1:N 대전의 심판.
//
// 규칙은 두 층으로 나뉜다.
//
//   Referee : 좌석·공격 라우팅·탈락·등수만 아는 **순수 상태 기계**.
//             Tetris 도 소켓도 Date.now() 도 모른다. 시간은 인자로 받는다.
//   Battle  : Referee 에 Tetris + Ai 인스턴스를 물려 로컬 대전을 돌리는 껍데기.
//
// 왜 굳이 나누는가: 5부의 네트워크 룸(src/net/room.ts)이 **같은 Referee** 를 쓴다.
// 공격을 누구에게 보낼지 정하는 규칙이 두 벌 있으면, 로컬 아레나와 온라인 대전이
// 미묘하게 다르게 행동하고 그걸 아무도 눈치채지 못한다.

import { Tetris, ST, STATE, W } from './core.js';
import { Ai, DEFAULT_WEIGHTS } from './ai.js';

/** 공격 대상을 고르는 방식. */
export type TargetMode = 'random' | 'even' | 'ko' | 'attackers';

export const REFEREE_DEFAULTS = {
  /** 좌석 수 */
  max: 8,
  target: 'random' as TargetMode,
  /** 가비지 유예(ms) — 맞은 줄이 실제로 솟기까지의 시간. 상쇄할 틈을 준다. */
  delay: 900,
  /** 한 락에서 솟을 수 있는 최대 줄 (코어의 GARBAGE_CAP 과 같은 값) */
  cap: 8,
  /** "최근에 나를 때렸다"로 치는 시간(ms) */
  hitTTL: 8000,
};

export interface Hit {
  from: number;
  at: number;
}

/** 심판이 좌석 하나에 대해 아는 것 전부. 판의 내용은 모른다. */
export interface RefereeSeat {
  alive: boolean;
  /** 지금까지 맞은 줄 수 — 'even' 타깃팅이 본다 */
  recv: number;
  /** 쌓인 높이 — 'ko' 타깃팅이 본다. 바깥에서 갱신해 준다. */
  height: number;
  /** 등수. 살아 있으면 0. */
  place: number;
  hits: Hit[];
}

export function newRefereeSeat(): RefereeSeat {
  return { alive: true, recv: 0, height: 0, place: 0, hits: [] };
}

/** 심판이 내보내는 사건. 네트워크 룸의 메시지와 같은 모양이다. */
export type RefEvent =
  | { t: 'grb'; i: number; n: number; from: number; hole: number }
  | { t: 'ko'; i: number; place: number; by: number }
  | { t: 'end'; order: number[] };

/**
 * 공격 라우팅과 등수 판정.
 *
 * 난수는 xorshift32 하나만 쓴다. 규격(protocol.md)이 정한 것과 같은 것이고,
 * 세 구현(JS/Go/Python)이 여기서부터 갈리면 그 뒤는 볼 것도 없다.
 */
export class Referee {
  readonly seats: (RefereeSeat | null)[];
  readonly cfg: typeof REFEREE_DEFAULTS;
  private rngState: number;

  constructor(cfg: Partial<typeof REFEREE_DEFAULTS> = {}, seed = 1) {
    this.cfg = { ...REFEREE_DEFAULTS, ...cfg };
    this.seats = new Array<RefereeSeat | null>(this.cfg.max).fill(null);
    this.rngState = (seed >>> 0) || 1;
  }

  rng(): number {
    let x = this.rngState >>> 0;
    x ^= x << 13; x >>>= 0;
    x ^= x >>> 17;
    x ^= x << 5; x >>>= 0;
    this.rngState = x;
    return x;
  }

  occupied(): number[] {
    const o: number[] = [];
    for (let i = 0; i < this.seats.length; i++) if (this.seats[i]) o.push(i);
    return o;
  }

  aliveSeats(): number[] {
    return this.occupied().filter((i) => (this.seats[i] as RefereeSeat).alive);
  }

  /**
   * 공격 대상 고르기 — 이 게임에서 심판이 하는 유일한 판단.
   *
   * 'even'/'ko' 는 난수를 쓰지 않는다(결정론적 최솟값·최댓값).
   * 'attackers' 는 기억이 있을 때만 결정론적이고, 없으면 random 으로 떨어진다.
   * 그래서 난수 소비 시점이 모드마다 다르다 — 구현 간 대조에서 가장 잘 어긋나는 곳이다.
   */
  pickTarget(from: number, now: number): number {
    const cand = this.aliveSeats().filter((j) => j !== from);
    if (!cand.length) return -1;
    const mode = this.cfg.target;
    if (mode === 'even') {
      let best = cand[0] as number;
      for (const j of cand) {
        if ((this.seats[j] as RefereeSeat).recv < (this.seats[best] as RefereeSeat).recv) best = j;
      }
      return best;
    }
    if (mode === 'ko') {
      let best = cand[0] as number;
      for (const j of cand) {
        if ((this.seats[j] as RefereeSeat).height > (this.seats[best] as RefereeSeat).height) best = j;
      }
      return best;
    }
    if (mode === 'attackers') {
      const hits = (this.seats[from] as RefereeSeat).hits;
      for (let k = hits.length - 1; k >= 0; k--) {
        const h = hits[k] as Hit;
        if (now - h.at > this.cfg.hitTTL) break; // hits 는 시간순이라 여기서 끊으면 된다
        if (h.from !== from && this.seats[h.from] && (this.seats[h.from] as RefereeSeat).alive) {
          return h.from;
        }
      }
      // 기억이 없으면 random 으로 떨어진다 — 이때만 난수를 쓴다
    }
    return cand[this.rng() % cand.length] as number;
  }

  /** 좌석 i 가 n 줄을 보냈다. 대상을 고르고 사건을 만든다. */
  attack(from: number, n: number, now: number): RefEvent[] {
    const s = this.seats[from];
    if (!s || !s.alive || n <= 0) return [];
    const j = this.pickTarget(from, now);
    if (j < 0) return []; // 혼자 남았거나 1인용 — 공격은 허공으로
    const hole = this.rng() % W;
    const tgt = this.seats[j] as RefereeSeat;
    tgt.recv += n;
    tgt.hits.push({ from, at: now });
    return [{ t: 'grb', i: j, n, from, hole }];
  }

  /** 좌석 하나를 탈락시킨다. 마지막 한 명이 남으면 end 까지 낸다. */
  kill(i: number, now: number, out: RefEvent[]): void {
    const s = this.seats[i];
    if (!s || !s.alive) return;
    const place = this.aliveSeats().length; // 지금 살아 있는 수 = 그대로 등수
    s.alive = false;
    s.place = place;
    let by = -1;
    for (let k = s.hits.length - 1; k >= 0; k--) {
      const h = s.hits[k] as Hit;
      if (now - h.at > this.cfg.hitTTL) break;
      if (h.from !== i) { by = h.from; break; }
    }
    out.push({ t: 'ko', i, place, by });

    const left = this.aliveSeats();
    if (left.length <= 1) {
      if (left.length === 1) (this.seats[left[0] as number] as RefereeSeat).place = 1;
      const occ = this.occupied().slice().sort(
        (a, b) => (this.seats[a] as RefereeSeat).place - (this.seats[b] as RefereeSeat).place,
      );
      out.push({ t: 'end', order: occ });
    }
  }
}

// ── 로컬 대전 ─────────────────────────────────────────────────────────

export interface SeatSpec {
  name: string;
  kind: 'human' | 'ai';
  /** AI 좌석의 가중치. 생략하면 학습된 기본값. */
  weights?: readonly number[];
  /** AI 좌석이 한 수 두는 간격(ms). 낮을수록 세다 — 난이도 조절의 두 번째 손잡이. */
  intervalMs?: number;
}

export interface BattleSeat extends SeatSpec {
  i: number;
  game: Tetris;
  ai: Ai | null;
  /** AI 착수 누적 시간 */
  acc: number;
  /** 마지막으로 처리한 ST.EVENT — 새 락을 알아채는 데 쓴다 */
  lastEvent: number;
  /** 지금까지 보낸 줄 수 */
  sent: number;
}

/** 아직 상대 필드에 도착하지 않은 가비지 한 뭉치. */
interface Parcel {
  at: number;
  i: number;
  n: number;
  hole: number;
}

export interface BattleOptions {
  seats: SeatSpec[];
  seed?: number;
  target?: TargetMode;
  /** 가비지 유예(ms) */
  delay?: number;
  /** AI 기본 착수 간격(ms) */
  intervalMs?: number;
}

/**
 * 로컬 1:N 대전.
 *
 * 시간은 오직 update(dtMs) 로만 흐른다. Date.now() 를 읽지 않기 때문에
 * 같은 설정 + 같은 시드 + 같은 dt 열이면 몇 번을 돌려도 같은 경기가 나온다.
 * 덱의 아레나 데모도, 봇 대전의 로컬 모드도 이걸 그대로 쓴다.
 *
 * AI 좌석은 중력 시계를 돌리지 않는다. AI 는 모든 조각을 하드드롭으로 놓으므로
 * 중력을 같이 돌리면 레벨이 높아졌을 때 "AI 가 계획하지 않은 자연 낙하"가 끼어든다.
 * 사람 좌석은 당연히 중력이 돈다.
 */
export class Battle {
  readonly ref: Referee;
  readonly seats: BattleSeat[] = [];
  readonly seed: number;
  /** 경기 내부 시각(ms). update 가 더한 dt 의 합. */
  now = 0;
  over = false;
  /** 등수 순 좌석 번호. 경기가 끝나야 채워진다. */
  order: number[] = [];
  private queue: Parcel[] = [];
  private readonly delay: number;
  private readonly defaultInterval: number;

  constructor(opts: BattleOptions) {
    this.seed = opts.seed ?? 1;
    this.delay = opts.delay ?? REFEREE_DEFAULTS.delay;
    this.defaultInterval = opts.intervalMs ?? 220;
    this.ref = new Referee({ max: opts.seats.length, target: opts.target ?? 'random' }, this.seed);

    opts.seats.forEach((spec, i) => {
      // 좌석마다 시드를 달리한다. 같은 시드면 8명이 똑같은 조각 순서를 받아
      // 똑같이 두게 되고, 그건 대전이 아니라 8중 복사다.
      const game = new Tetris(((this.seed + i * 0x9e3779b9) >>> 0) || 1);
      const ai = spec.kind === 'ai' ? new Ai(game, spec.weights ?? DEFAULT_WEIGHTS) : null;
      this.ref.seats[i] = newRefereeSeat();
      this.seats.push({
        ...spec, i, game, ai, acc: 0,
        lastEvent: game.stats[ST.EVENT] as number, sent: 0,
      });
    });
  }

  /** 좌석의 판에서 가장 높이 쌓인 높이(칸). 'ko' 타깃팅이 이걸 본다. */
  private heightOf(s: BattleSeat): number {
    const b = s.game.board;
    for (let y = 0; y < b.length / W; y++) {
      for (let x = 0; x < W; x++) if (b[y * W + x]) return b.length / W - y;
    }
    return 0;
  }

  /** 좌석이 방금 굳힌 조각으로 보낸 공격을 심판에게 넘긴다. */
  private drain(s: BattleSeat, out: RefEvent[]): void {
    const ev = s.game.stats[ST.EVENT] as number;
    if (ev === s.lastEvent) return;
    s.lastEvent = ev;
    const rs = this.ref.seats[s.i] as RefereeSeat;
    rs.height = this.heightOf(s);
    const atk = s.game.stats[ST.ATTACK] as number;
    if (atk > 0) {
      s.sent += atk;
      for (const e of this.ref.attack(s.i, atk, this.now)) {
        out.push(e);
        // 심판이 정한 대상·구멍으로 소포를 만들어 유예 뒤에 배달한다
        if (e.t === 'grb') this.queue.push({ at: this.now + this.delay, i: e.i, n: e.n, hole: e.hole });
      }
    }
  }

  /** 사람 좌석의 키 입력. 누르는 즉시 공격을 배달해야 하므로 여기서 drain 한다. */
  press(i: number, act: number): RefEvent[] {
    const s = this.seats[i] as BattleSeat;
    if (this.over || !(this.ref.seats[i] as RefereeSeat).alive) return [];
    const out: RefEvent[] = [];
    s.game.press(act);
    this.drain(s, out);
    this.checkDeaths(out);
    return out;
  }

  release(i: number, act: number): void {
    (this.seats[i] as BattleSeat).game.release(act);
  }

  private checkDeaths(out: RefEvent[]): void {
    if (this.over) return;
    for (const s of this.seats) {
      const rs = this.ref.seats[s.i] as RefereeSeat;
      if (rs.alive && (s.game.stats[ST.STATE] as number) === STATE.OVER) {
        this.ref.kill(s.i, this.now, out);
      }
    }
    const end = out.find((e) => e.t === 'end');
    if (end && end.t === 'end') {
      this.over = true;
      this.order = end.order;
    }
  }

  /** dtMs 만큼 경기를 진행시킨다. */
  update(dtMs: number): RefEvent[] {
    const out: RefEvent[] = [];
    if (this.over) return out;
    this.now += dtMs;

    // 1) 도착할 때가 된 가비지를 배달한다
    const due = this.queue.filter((p) => p.at <= this.now);
    if (due.length) {
      this.queue = this.queue.filter((p) => p.at > this.now);
      for (const p of due) {
        const s = this.seats[p.i] as BattleSeat;
        if ((this.ref.seats[p.i] as RefereeSeat).alive) s.game.queueGarbage(p.n);
      }
    }

    // 2) 좌석마다 한 틱
    for (const s of this.seats) {
      if (!(this.ref.seats[s.i] as RefereeSeat).alive) continue;
      if (s.ai) {
        s.acc += dtMs;
        const interval = s.intervalMs ?? this.defaultInterval;
        while (s.acc >= interval && (s.game.stats[ST.STATE] as number) === STATE.PLAY) {
          s.acc -= interval;
          s.ai.step();
          this.drain(s, out);
        }
      } else {
        s.game.update(dtMs);
        this.drain(s, out);
      }
    }

    this.checkDeaths(out);
    return out;
  }

  /** 경기가 끝날 때까지 돌린다. 무한 루프 방지용 상한을 둔다. */
  run(dtMs = 50, maxMs = 10 * 60 * 1000): RefEvent[] {
    const all: RefEvent[] = [];
    while (!this.over && this.now < maxMs) all.push(...this.update(dtMs));
    return all;
  }

  /** 좌석별 요약 — 순위표를 그릴 때 쓴다. */
  summary(): { i: number; name: string; place: number; sent: number; recv: number; lines: number; score: number }[] {
    return this.seats.map((s) => {
      const rs = this.ref.seats[s.i] as RefereeSeat;
      return {
        i: s.i, name: s.name, place: rs.place, sent: s.sent, recv: rs.recv,
        lines: s.game.stats[ST.LINES] as number,
        score: s.game.stats[ST.SCORE] as number,
      };
    });
  }
}

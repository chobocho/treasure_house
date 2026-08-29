// arena_view.ts — 여러 판이 동시에 도는 대전 화면.
//
// 8석을 한 화면에 넣으려면 판 하나가 아주 작아진다(접힘 화면에서 칸이 9px 안팎).
// 그래서 조각 색과 가비지 회색만 남기고 고스트·격자·다음 조각은 전부 뺐다 —
// 작은 판에서는 정보를 더 넣을수록 아무것도 안 보인다.
//
// 대전 규칙은 여기 없다. 전부 battle.ts 의 Battle 안에 있고, 이 파일은 그 상태를
// 프레임마다 읽어 칠할 뿐이다.

import { W, VIS, ST, STATE, GARBAGE } from './core.js';
import { Battle, type SeatSpec, type TargetMode } from './battle.js';
import { DEFAULT_WEIGHTS } from './ai.js';
import { COLORS, GARBAGE_COLOR, type Ctx, type Elm } from './view.js';

interface Doc { createElement(tag: string): Elm }

/** 좌석 이름 — 8석까지. 대전 로그와 순위표에 그대로 쓴다. */
export const SEAT_NAMES: readonly string[] = ['보라', '다온', '아라', '해든', '나린', '가온', '시우', '지호'];

export interface ArenaOptions {
  raf?: (cb: (t: number) => void) => number;
  caf?: (h: number) => void;
  now?: () => number;
  maxWidth?: number;
  /** 좌석 수 (1~8) */
  seats?: number;
  /** 공격 대상 고르기 */
  target?: TargetMode;
  /** AI 착수 간격(ms). 작을수록 빠르다. */
  intervalMs?: number;
  seed?: number;
  /** 경기가 끝나면 잠시 뒤 새 판을 시작할 것인가 */
  restart?: boolean;
  restartMs?: number;
}

export class ArenaView {
  battle: Battle;
  readonly canvas: Elm;
  readonly info: Elm;
  /** 판 하나의 칸 크기(px). 8석이 한 줄에 넉 장씩 들어가게 잡는다. */
  readonly cell: number;
  readonly cols: number;

  private readonly ctx: Ctx;
  private readonly raf: (cb: (t: number) => void) => number;
  private readonly caf: (h: number) => void;
  private readonly now: () => number;
  private readonly opts: Required<Pick<ArenaOptions, 'seats' | 'target' | 'intervalMs' | 'restart' | 'restartMs'>>;
  private handle = 0;
  private running = false;
  private last = 0;
  private overAt = 0;
  private seedCounter: number;

  constructor(host: HTMLElement, opts: ArenaOptions = {}) {
    const g = globalThis as unknown as {
      requestAnimationFrame?: (cb: (t: number) => void) => number;
      cancelAnimationFrame?: (h: number) => void;
      performance?: { now: () => number };
    };
    this.raf = opts.raf ?? ((cb) => (g.requestAnimationFrame as (c: (t: number) => void) => number)(cb));
    this.caf = opts.caf ?? ((h) => g.cancelAnimationFrame?.(h));
    this.now = opts.now ?? (() => (g.performance ? g.performance.now() : Date.now()));
    this.opts = {
      seats: Math.max(1, Math.min(8, opts.seats ?? 8)),
      target: opts.target ?? 'random',
      intervalMs: opts.intervalMs ?? 220,
      restart: opts.restart ?? true,
      restartMs: opts.restartMs ?? 4000,
    };
    this.seedCounter = (opts.seed ?? ((Math.random() * 0xffffffff) >>> 0)) || 1;

    const doc = (host as unknown as { ownerDocument: Doc }).ownerDocument;
    const avail = opts.maxWidth ?? (Math.round(host.getBoundingClientRect().width) || 360);
    this.cols = this.opts.seats <= 2 ? this.opts.seats : this.opts.seats <= 4 ? 2 : 4;
    const rows = Math.ceil(this.opts.seats / this.cols);
    // 판 사이 여백 6px 을 빼고 칸 크기를 정한다. 1px 아래로는 아무것도 안 보인다.
    this.cell = Math.max(2, Math.min(14, Math.floor((avail - (this.cols - 1) * 6) / (this.cols * W))));

    const mk = (tag: string, css: string): Elm => {
      const e = doc.createElement(tag);
      e.style.cssText = css;
      return e;
    };
    this.canvas = mk('canvas', 'background:#020617;border-radius:6px;max-width:100%');
    this.canvas.width = this.cols * W * this.cell + (this.cols - 1) * 6;
    this.canvas.height = rows * (VIS * this.cell + 14) + (rows - 1) * 6;
    this.info = mk('div', 'font-size:.75em;color:#94a3b8;text-align:center;margin-top:.3em;line-height:1.5');
    const box = host as unknown as { appendChild(c: unknown): unknown };
    box.appendChild(this.canvas);
    box.appendChild(this.info);
    this.ctx = this.canvas.getContext('2d');

    this.battle = this.newBattle();
    this.draw();
  }

  /** AI 좌석만 앉힌 새 대전. 이름은 고정, 시드는 매 판 달라진다. */
  private newBattle(): Battle {
    const seats: SeatSpec[] = Array.from({ length: this.opts.seats }, (_, i) => ({
      name: SEAT_NAMES[i] ?? `AI${i + 1}`,
      kind: 'ai' as const,
      weights: DEFAULT_WEIGHTS,
      intervalMs: this.opts.intervalMs,
    }));
    this.seedCounter = ((this.seedCounter * 1664525 + 1013904223) >>> 0) || 1;
    return new Battle({ seats, seed: this.seedCounter, target: this.opts.target });
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.last = this.now();
    this.handle = this.raf((t) => this.frame(t));
  }

  stop(): void {
    if (!this.running) return;
    this.running = false;
    this.caf(this.handle);
    this.handle = 0;
  }

  private frame(t: number): void {
    if (!this.running) return;
    this.handle = this.raf((n) => this.frame(n));
    let dt = Math.round(t - this.last);
    this.last = t;
    if (dt < 0) dt = 0;
    if (dt > 100) dt = 100;

    if (!this.battle.over) {
      this.battle.update(dt);
      if (this.battle.over) this.overAt = t;
    } else if (this.opts.restart && t - this.overAt > this.opts.restartMs) {
      this.battle = this.newBattle();
    }
    this.draw();
  }

  /** 좌석 하나의 왼쪽 위 모서리. */
  private originOf(i: number): [number, number] {
    const c = i % this.cols, r = Math.floor(i / this.cols);
    return [c * (W * this.cell + 6), r * (VIS * this.cell + 14 + 6)];
  }

  draw(): void {
    const c = this.ctx, s = this.cell;
    c.fillStyle = '#020617';
    c.fillRect(0, 0, this.canvas.width, this.canvas.height);

    for (let i = 0; i < this.battle.seats.length; i++) {
      const seat = this.battle.seats[i] as { game: { cells: Uint8Array; stats: Int32Array } };
      const [ox, oy] = this.originOf(i);
      const alive = (seat.game.stats[ST.STATE] as number) === STATE.PLAY;
      c.fillStyle = '#0b1220';
      c.fillRect(ox, oy + 14, W * s, VIS * s);

      for (let k = 0; k < VIS * W; k++) {
        const v = seat.game.cells[k] as number;
        if (!v) continue;
        c.fillStyle = v === GARBAGE ? GARBAGE_COLOR : (COLORS[v - 1] as string);
        c.globalAlpha = alive ? 1 : 0.35; // 죽은 판은 흐리게 — 누가 남았는지 한눈에
        c.fillRect(ox + (k % W) * s, oy + 14 + Math.floor(k / W) * s, Math.max(1, s - 1), Math.max(1, s - 1));
        c.globalAlpha = 1;
      }
      c.fillStyle = alive ? '#93a4c4' : '#f87171';
      c.font = `${Math.max(8, Math.round(s * 1.1))}px system-ui, sans-serif`;
      c.textAlign = 'left';
      const place = this.battle.summary()[i]?.place ?? 0;
      c.fillText(`${SEAT_NAMES[i] ?? i}${place ? ` ${place}등` : ''}`, ox + 1, oy + 11);
    }
    this.updateInfo();
  }

  /** 판 아래 한 줄 — 진행 중에는 공격 총량, 끝나면 순위. */
  private updateInfo(): void {
    if (this.battle.over) {
      const rank = this.battle.order
        .map((i, k) => `${k + 1}등 ${SEAT_NAMES[i] ?? i}`)
        .slice(0, 4)
        .join(' · ');
      this.info.textContent = `경기 종료 — ${rank}${this.opts.restart ? ' (곧 새 판)' : ''}`;
      return;
    }
    const sum = this.battle.summary();
    const sent = sum.reduce((a, x) => a + x.sent, 0);
    const alive = sum.filter((x) => !x.place).length;
    this.info.textContent =
      `${(this.battle.now / 1000).toFixed(0)}초 · 생존 ${alive}/${sum.length} · 보낸 줄 합계 ${sent}`;
  }
}

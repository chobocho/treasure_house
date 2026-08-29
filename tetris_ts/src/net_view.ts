// net_view.ts — 프로토콜을 그대로 지나가는 8인 대전 화면.
//
// 파트 10의 아레나(arena_view.ts)는 판 여덟 개를 한 프로세스에서 직접 굴렸다.
// 여기서는 다르다. PC 네 대가 각자 클라이언트를 열고, 허브에 붙고, 좌석을 잡고,
// 공격을 메시지로 주고받는다. 바뀐 건 전송 계층 하나뿐 — 소켓 대신 루프백이다.
//
// 그래서 이 화면에는 두 종류의 판이 있다:
//   · 내 좌석  — 내 프로세스가 굴리는 Tetris 의 화면 버퍼를 그대로 그린다
//   · 남의 좌석 — 초당 10회 올라오는 스냅샷을 풀어서 그린다 (관전 화면과 같은 경로)
// 남의 판이 제대로 보인다는 건 런렝스·base64·스냅샷이 전부 맞는다는 뜻이다.

import { W, VIS, GARBAGE } from './core.js';
import { COLORS, GARBAGE_COLOR, type Ctx, type Elm } from './view.js';
import { SEAT_NAMES } from './arena_view.js';
import { NetClient } from './net/client.js';
import { LoopbackHub } from './net/loopback.js';
import { Match } from './net/match.js';
import { unsnapshot } from './net/protocol.js';
import type { TargetMode } from './battle.js';

interface Doc { createElement(tag: string): Elm }

export interface NetArenaOptions {
  raf?: (cb: (t: number) => void) => number;
  caf?: (h: number) => void;
  now?: () => number;
  maxWidth?: number;
  /** PC 대수 × PC 당 좌석 수 = 좌석 수 */
  pcs?: number;
  perPc?: number;
  target?: TargetMode;
  intervalMs?: number;
  /** 루프백 지연(ms). 0이면 즉시 배달된다. */
  latency?: number;
  seed?: number;
  restart?: boolean;
  restartMs?: number;
}

interface Peer {
  c: NetClient;
  m: Match;
}

export class NetArenaView {
  hub: LoopbackHub;
  readonly peers: Peer[] = [];
  readonly canvas: Elm;
  readonly info: Elm;
  readonly cell: number;
  readonly cols: number;

  /** 좌석별 화면 버퍼. 남의 좌석은 스냅샷을 풀어 여기에 채운다. */
  private readonly cells: Uint8Array[] = [];
  private readonly places: number[] = [];
  private readonly ctx: Ctx;
  private readonly grid: SeatGrid;
  private readonly raf: (cb: (t: number) => void) => number;
  private readonly caf: (h: number) => void;
  private readonly now: () => number;
  private readonly opts: Required<Pick<NetArenaOptions,
    'pcs' | 'perPc' | 'target' | 'intervalMs' | 'latency' | 'restart' | 'restartMs'>>;
  private handle = 0;
  private running = false;
  private last = 0;
  private over = false;
  private overAt = 0;
  private order: number[] = [];
  private msgs = 0;
  private seedCounter: number;

  constructor(host: HTMLElement, opts: NetArenaOptions = {}) {
    const g = globalThis as unknown as {
      requestAnimationFrame?: (cb: (t: number) => void) => number;
      cancelAnimationFrame?: (h: number) => void;
      performance?: { now: () => number };
    };
    this.raf = opts.raf ?? ((cb) => (g.requestAnimationFrame as (c: (t: number) => void) => number)(cb));
    this.caf = opts.caf ?? ((h) => g.cancelAnimationFrame?.(h));
    this.now = opts.now ?? (() => (g.performance ? g.performance.now() : Date.now()));
    this.opts = {
      pcs: opts.pcs ?? 4, perPc: opts.perPc ?? 2,
      target: opts.target ?? 'random', intervalMs: opts.intervalMs ?? 220,
      latency: opts.latency ?? 0, restart: opts.restart ?? true, restartMs: opts.restartMs ?? 4000,
    };
    this.seedCounter = (opts.seed ?? ((Math.random() * 0xffffffff) >>> 0)) || 1;

    const total = this.opts.pcs * this.opts.perPc;
    for (let i = 0; i < total; i++) {
      this.cells.push(new Uint8Array(VIS * W));
      this.places.push(0);
    }

    const doc = (host as unknown as { ownerDocument: Doc }).ownerDocument;
    const avail = opts.maxWidth ?? (Math.round(host.getBoundingClientRect().width) || 360);
    this.cols = total <= 2 ? total : total <= 4 ? 2 : 4;
    const rows = Math.ceil(total / this.cols);
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
    this.grid = new SeatGrid(this.cols, this.cell);

    this.hub = new LoopbackHub(this.nextSeed(), this.opts.latency);
    this.connectAll();
    this.draw();
  }

  private nextSeed(): number {
    this.seedCounter = ((this.seedCounter * 1664525 + 1013904223) >>> 0) || 1;
    return this.seedCounter;
  }

  /** 좌석 i 의 화면 버퍼 — 테스트와 디버깅용. */
  cellsOf(i: number): Uint8Array {
    return this.cells[i] as Uint8Array;
  }

  /** PC 대수만큼 클라이언트를 열고 좌석을 잡게 한다. 방장이 마지막에 start 를 누른다. */
  private connectAll(): void {
    const total = this.opts.pcs * this.opts.perPc;
    for (let k = 0; k < this.opts.pcs; k++) {
      const c = new NetClient(this.hub.connect(), `PC${k + 1}`);
      const m = new Match(c, {
        intervalMs: this.opts.intervalMs, stMs: 100, delay: 900,
        // 유예는 허브의 시계가 아니라 프레임에 맞춰 흐른다. 데모에서는 배달만 미루면 된다.
        defer: (fn, ms): void => { setTimeout(fn, ms); },
      });
      const peer: Peer = { c, m };
      c.on('hi', () => {
        if (k === 0) c.create({ max: total, perPeer: this.opts.perPc, target: this.opts.target });
        else c.join((this.peers[0] as Peer).c.code);
      });
      c.on('joined', () => {
        for (let s = 0; s < this.opts.perPc; s++) {
          const idx = k * this.opts.perPc + s;
          c.takeSeat(-1, 'ai', SEAT_NAMES[idx] ?? `AI${idx + 1}`, 'max');
        }
        c.setReady(true);
      });
      c.on('room', () => {
        if (k === 0 && !c.started && c.seats.length >= total) c.start();
      });
      c.on('start', (msg) => {
        if (msg.t === 'start') m.begin(msg.seed, msg.seats);
      });
      c.on('grb', (msg) => { if (msg.t === 'grb') m.garbage(msg.i, msg.n); });
      c.on('ko', (msg) => { if (msg.t === 'ko') this.places[msg.i] = msg.place; });
      c.on('end', (msg) => {
        if (msg.t !== 'end' || this.over) return;
        this.over = true;
        this.order = msg.order;
        this.overAt = this.last;
      });
      // 남의 판은 스냅샷으로만 온다. 1번 PC 시점에서만 풀면 충분하다(화면이 하나니까).
      if (k === 0) {
        c.on('st', (msg) => {
          if (msg.t !== 'st') return;
          this.msgs++;
          unsnapshot(msg.b, this.cells[msg.i] as Uint8Array);
        });
      }
      this.peers.push(peer);
    }
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
    for (const p of this.peers) p.c.bye();
  }

  private frame(t: number): void {
    if (!this.running) return;
    this.handle = this.raf((n) => this.frame(n));
    let dt = Math.round(t - this.last);
    this.last = t;
    if (dt < 0) dt = 0;
    if (dt > 100) dt = 100;

    if (!this.over) {
      this.hub.advance(dt);   // 룸의 시계 — hitTTL 과 막타 판정이 이걸 본다
      for (const p of this.peers) p.m.update(dt);
    } else if (this.opts.restart && t - this.overAt > this.opts.restartMs) {
      this.reset();
    }
    this.draw();
  }

  /** 새 판 — 허브째로 새로 만든다. 방 코드도 pid 도 새로 받는다. */
  private reset(): void {
    for (const p of this.peers) p.c.bye();
    this.peers.length = 0;
    for (const c of this.cells) c.fill(0);
    this.places.fill(0);
    this.over = false;
    this.order = [];
    this.msgs = 0;
    this.hub = new LoopbackHub(this.nextSeed(), this.opts.latency);
    this.connectAll();
  }

  /** 내 좌석은 로컬 판에서, 남의 좌석은 스냅샷 버퍼에서. */
  private refreshMine(): void {
    const mine = (this.peers[0] as Peer | undefined)?.m;
    if (!mine) return;
    for (const s of mine.seats) paintSeat(this.cells[s.i] as Uint8Array, s.game);
  }

  draw(): void {
    this.refreshMine();
    const mine = (this.peers[0] as Peer | undefined)?.m;
    this.grid.draw(this.ctx, this.cells, {
      labels: this.cells.map((_, i) => SEAT_NAMES[i] ?? String(i)),
      places: this.places,
      mine: this.cells.map((_, i) => mine?.seat(i) !== undefined),
    });
    this.updateInfo();
  }

  private updateInfo(): void {
    if (this.over) {
      const rank = this.order.slice(0, 3).map((i, k) => `${k + 1}등 ${SEAT_NAMES[i] ?? i}`).join(' · ');
      this.info.textContent = `경기 종료 — ${rank}${this.opts.restart ? ' (곧 새 판)' : ''}`;
      return;
    }
    const alive = this.places.filter((p) => p === 0).length;
    const code = (this.peers[0] as Peer | undefined)?.c.code ?? '····';
    this.info.textContent =
      `방 ${code} · PC ${this.opts.pcs}대 · 생존 ${alive}/${this.cells.length}`
      + ` · 받은 화면 ${this.msgs}장 (하늘색 이름이 내 좌석, 나머지는 스냅샷)`;
  }
}

/** 화면 버퍼 하나를 로컬 판의 지금 모습(굳은 블록 + 떨어지는 조각)으로 채운다. */
export function paintSeat(buf: Uint8Array, game: { cells: Uint8Array; overlay: Uint8Array }): void {
  buf.set(game.cells);
  for (let k = 0; k < buf.length; k++) {
    const ov = game.overlay[k] as number;
    if (ov >= 1 && ov <= 7) buf[k] = ov; // 고스트(8~14)는 남의 화면에 그리지 않는다
  }
}

export interface SeatLabels {
  labels: string[];
  places: number[];
  mine: boolean[];
}

/**
 * 좌석 여럿을 격자로 그리는 일만 하는 물건.
 *
 * 루프백 데모와 진짜 페이지가 같은 그림을 그려야 하므로 따로 뺐다. 데이터가 어디서
 * 왔는지(내 판인지 남의 스냅샷인지)는 이 클래스의 관심사가 아니다 — 버퍼만 받는다.
 */
export class SeatGrid {
  constructor(readonly cols: number, readonly cell: number) {}

  width(): number {
    return this.cols * W * this.cell + (this.cols - 1) * 6;
  }

  height(n: number): number {
    const rows = Math.ceil(n / this.cols);
    return rows * (VIS * this.cell + 14) + (rows - 1) * 6;
  }

  draw(c: Ctx, cells: readonly Uint8Array[], meta: SeatLabels): void {
    const s = this.cell;
    c.fillStyle = '#020617';
    c.fillRect(0, 0, this.width(), this.height(cells.length));
    for (let i = 0; i < cells.length; i++) {
      const col = i % this.cols, row = Math.floor(i / this.cols);
      const ox = col * (W * s + 6), oy = row * (VIS * s + 14 + 6);
      const dead = (meta.places[i] ?? 0) !== 0;
      c.fillStyle = '#0b1220';
      c.fillRect(ox, oy + 14, W * s, VIS * s);
      const buf = cells[i] as Uint8Array;
      for (let k = 0; k < buf.length; k++) {
        const v = buf[k] as number;
        if (!v) continue;
        c.fillStyle = v === GARBAGE ? GARBAGE_COLOR : (COLORS[v - 1] as string);
        c.globalAlpha = dead ? 0.35 : 1;
        c.fillRect(ox + (k % W) * s, oy + 14 + Math.floor(k / W) * s,
                   Math.max(1, s - 1), Math.max(1, s - 1));
        c.globalAlpha = 1;
      }
      c.fillStyle = dead ? '#f87171' : meta.mine[i] ? '#22d3ee' : '#93a4c4';
      c.font = `${Math.max(8, Math.round(s * 1.1))}px system-ui, sans-serif`;
      c.textAlign = 'left';
      c.fillText(`${meta.labels[i] ?? i}${dead ? ` ${meta.places[i]}등` : ''}`, ox + 1, oy + 11);
    }
  }
}

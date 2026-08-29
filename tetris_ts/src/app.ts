// app.ts — 진짜 페이지. `make run` 으로 띄운 서버에 붙어 8인 대전을 한다.
//
// 덱 데모(net_view.ts)와 다른 점은 전송 계층 하나뿐이다. 여기서는 진짜 WebSocket 이
// 들어오고, 방 코드를 사람이 입력한다. 나머지 — 클라이언트·경기 진행·좌석 그리기 —
// 는 전부 같은 파일을 쓴다.
//
// 로비 UI 도 화면 그리기와 같은 원칙을 따른다: DOM 에 요구하는 모양을 좁게 적고
// 전송 계층을 주입받아, 소켓 없이 루프백만으로 테스트할 수 있게 뒀다.

import { VIS, W, ACT } from './core.js';
import { NetClient, type Transport } from './net/client.js';
import { Match } from './net/match.js';
import { unsnapshot } from './net/protocol.js';
import { SeatGrid, paintSeat } from './net_view.js';
import { SEAT_NAMES } from './arena_view.js';
import type { Ctx, Elm } from './view.js';

interface Doc { createElement(tag: string): Elm }

export interface AppOptions {
  /** 전송 계층을 만든다. 기본은 같은 호스트의 /ws 로 붙는 진짜 WebSocket. */
  transport?: () => Transport;
  /** 난이도 이름 → 가중치 (weights.json 의 levels) */
  weights?: Record<string, readonly number[]>;
  name?: string;
  maxWidth?: number;
  raf?: (cb: (t: number) => void) => number;
  caf?: (h: number) => void;
  now?: () => number;
}

/** 브라우저의 WebSocket 을 우리 Transport 모양으로 감싼다. */
export function wsTransport(url: string): Transport {
  const g = globalThis as unknown as { WebSocket: new (u: string) => WebSocket };
  const ws = new g.WebSocket(url);
  const t: Transport = {
    onMessage: null, onOpen: null, onClose: null,
    send: (s: string): void => { if (ws.readyState === 1) ws.send(s); },
    close: (): void => { try { ws.close(); } catch { /* 이미 닫혔다 */ } },
  };
  ws.addEventListener('open', () => t.onOpen?.());
  ws.addEventListener('close', () => t.onClose?.());
  ws.addEventListener('message', (e) => t.onMessage?.(String((e as MessageEvent).data)));
  return t;
}

export class App {
  readonly client: NetClient;
  readonly match: Match;
  /** 좌석별 화면 버퍼 — 내 좌석은 로컬 판에서, 남의 좌석은 스냅샷에서 채운다. */
  readonly cells: Uint8Array[] = [];
  readonly places: number[] = [];

  private readonly canvas: Elm;
  private readonly ctx: Ctx;
  private readonly bar: Elm;
  private readonly log: Elm;
  private readonly grid: SeatGrid;
  private readonly raf: (cb: (t: number) => void) => number;
  private readonly caf: (h: number) => void;
  private readonly now: () => number;
  private handle = 0;
  private running = false;
  private last = 0;
  /** 내가 조종하는 사람 좌석(없으면 -1) */
  private humanSeat = -1;

  constructor(host: HTMLElement, opts: AppOptions = {}) {
    const g = globalThis as unknown as {
      requestAnimationFrame?: (cb: (t: number) => void) => number;
      cancelAnimationFrame?: (h: number) => void;
      performance?: { now: () => number };
      location?: { host: string; protocol: string };
    };
    this.raf = opts.raf ?? ((cb) => (g.requestAnimationFrame as (c: (t: number) => void) => number)(cb));
    this.caf = opts.caf ?? ((h) => g.cancelAnimationFrame?.(h));
    this.now = opts.now ?? (() => (g.performance ? g.performance.now() : Date.now()));

    const doc = (host as unknown as { ownerDocument: Doc }).ownerDocument;
    const mk = (tag: string, css: string): Elm => {
      const e = doc.createElement(tag);
      e.style.cssText = css;
      return e;
    };
    this.bar = mk('div', 'display:flex;gap:.4em;flex-wrap:wrap;align-items:center;margin-bottom:.5em');
    this.log = mk('div', 'font-size:.8em;color:#94a3b8;margin-top:.4em;min-height:1.4em');
    const cell = Math.max(4, Math.min(12, Math.floor(((opts.maxWidth ?? 720) - 18) / (4 * W))));
    this.grid = new SeatGrid(4, cell);
    this.canvas = mk('canvas', 'background:#020617;border-radius:8px;max-width:100%');
    for (let i = 0; i < 8; i++) { this.cells.push(new Uint8Array(VIS * W)); this.places.push(0); }
    this.canvas.width = this.grid.width();
    this.canvas.height = this.grid.height(8);
    const box = host as unknown as { appendChild(c: unknown): unknown };
    box.appendChild(this.bar);
    box.appendChild(this.canvas);
    box.appendChild(this.log);
    this.ctx = this.canvas.getContext('2d');

    const url = g.location
      ? `${g.location.protocol === 'https:' ? 'wss' : 'ws'}://${g.location.host}/ws`
      : 'ws://127.0.0.1:8787/ws';
    const transport = (opts.transport ?? ((): Transport => wsTransport(url)))();
    this.client = new NetClient(transport, opts.name ?? '나');
    this.match = new Match(this.client, {
      ...(opts.weights ? { weights: opts.weights } : {}),
      intervalMs: 200, stMs: 100, delay: 900,
    });
    this.wire();
    this.buildBar(doc);
    this.draw();
  }

  /** 서버 메시지 → 화면. 로비 갱신·시작·가비지·탈락·종료만 다루면 된다. */
  private wire(): void {
    const c = this.client;
    c.on('joined', () => { this.say(`방 ${c.code} 에 들어왔다. 좌석을 잡아라.`); this.draw(); });
    c.on('room', () => { this.draw(); });
    c.on('start', (m) => {
      if (m.t !== 'start') return;
      this.places.fill(0);
      for (const buf of this.cells) buf.fill(0);
      this.match.begin(m.seed, m.seats);
      this.humanSeat = this.match.seats.find((s) => s.kind === 'human')?.i ?? -1;
      this.say(`시작 — 시드 ${m.seed >>> 0}, 좌석 ${m.seats.length}석`);
      this.start();
    });
    c.on('st', (m) => { if (m.t === 'st') unsnapshot(m.b, this.cells[m.i] as Uint8Array); });
    c.on('grb', (m) => { if (m.t === 'grb') this.match.garbage(m.i, m.n); });
    c.on('ko', (m) => {
      if (m.t !== 'ko') return;
      this.places[m.i] = m.place;
      this.say(`${SEAT_NAMES[m.i] ?? m.i} 탈락 — ${m.place}등`);
    });
    c.on('end', (m) => {
      if (m.t !== 'end') return;
      this.stop();
      this.say(`경기 종료 — 우승 ${SEAT_NAMES[m.order[0] ?? 0] ?? ''}`);
    });
    c.on('err', (m) => { if (m.t === 'err') this.say(`오류: ${m.code}`); });
  }

  /** 로비 버튼 여섯 개. 방 코드는 사람이 읽고 부를 수 있어야 하므로 크게 보여 준다. */
  private buildBar(doc: Doc): void {
    const btn = (label: string, fn: () => void): void => {
      const b = doc.createElement('button');
      b.textContent = label;
      b.style.cssText = 'padding:.4em .7em;border-radius:6px;border:1px solid #334155;'
        + 'background:#0f172a;color:#cbd5e1;font-size:.85em';
      b.addEventListener('click', () => fn());
      this.bar.appendChild(b);
    };
    btn('방 만들기', () => this.client.create({ max: 8, perPeer: 2 }));
    btn('코드로 참가', () => {
      const g = globalThis as unknown as { prompt?: (m: string) => string | null };
      const code = g.prompt?.('방 코드 (4글자)') ?? '';
      if (code) this.client.join(code.trim().toUpperCase());
    });
    btn('내 자리 앉기', () => this.client.takeSeat(-1, 'human', this.client.name || '나'));
    btn('AI 좌석 추가', () => this.client.takeSeat(-1, 'ai', 'AI', 'max'));
    btn('준비', () => this.client.setReady(true));
    btn('시작', () => this.client.start());
  }

  private say(text: string): void {
    this.log.textContent = text;
  }

  /** 키 입력 — 사람 좌석이 있을 때만. 없으면 문서가 키를 그대로 쓴다. */
  onKey(e: { type: string; key: string; preventDefault: () => void }): void {
    if (this.humanSeat < 0) return;
    const map: Record<string, number> = {
      ArrowLeft: ACT.LEFT, ArrowRight: ACT.RIGHT, ArrowDown: ACT.SOFT, ArrowUp: ACT.CW,
      z: ACT.CCW, ' ': ACT.HARD, c: ACT.HOLD,
    };
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    const act = map[k];
    if (act === undefined) return;
    e.preventDefault();
    if (e.type === 'keydown') this.match.press(this.humanSeat, act);
    else this.match.release(this.humanSeat, act);
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
    this.match.update(dt);
    this.draw();
  }

  draw(): void {
    for (const s of this.match.seats) paintSeat(this.cells[s.i] as Uint8Array, s.game);
    const seats = this.client.seats;
    this.grid.draw(this.ctx, this.cells, {
      labels: this.cells.map((_, i) => seats.find((s) => s.i === i)?.name || (SEAT_NAMES[i] ?? String(i))),
      places: this.places,
      mine: this.cells.map((_, i) => this.match.seat(i) !== undefined),
    });
  }
}

// 페이지에서 자동으로 뜬다. 노드에서 임포트할 때는 아무 일도 일어나지 않는다.
const page = globalThis as unknown as { document?: { getElementById(id: string): HTMLElement | null };
  __app?: App; addEventListener?: (t: string, f: (e: unknown) => void) => void;
  TS_WEIGHTS?: Record<string, readonly number[]> };
if (page.document) {
  const host = page.document.getElementById('app');
  if (host) {
    const app = new App(host, { ...(page.TS_WEIGHTS ? { weights: page.TS_WEIGHTS } : {}) });
    page.__app = app;
    page.addEventListener?.('keydown', (e) => app.onKey(e as { type: string; key: string; preventDefault: () => void }));
    page.addEventListener?.('keyup', (e) => app.onKey(e as { type: string; key: string; preventDefault: () => void }));
  }
}

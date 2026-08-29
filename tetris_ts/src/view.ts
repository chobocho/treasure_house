// view.ts — 코어에 화면과 손가락을 붙인다.
//
// 코어(core.ts)는 캔버스도 DOM 도 모른다. 그 사이를 메우는 게 이 파일이고, 하는 일은
// 셋뿐이다: 프레임마다 시간을 흘리고, 배열 세 개를 칠하고, 입력을 액션 코드로 바꾼다.
//
// 브라우저 밖에서도 돌아가야 한다. 그래서 전역(requestAnimationFrame·performance·
// document)을 직접 부르지 않고 **주입받는다**. 덕분에 노드에서 가짜 시계와 가짜 문서로
// 프레임을 한 칸씩 돌려 가며 "무엇을 몇 번 칠했는지"까지 테스트할 수 있다.

import { Tetris, ACT, ST, STATE, W, VIS, HIDDEN, GARBAGE, SHAPES } from './core.js';
import { Ai, DEFAULT_WEIGHTS } from './ai.js';

/** 조각 색 — SHAPES 순서(I J L O S T Z)와 같다. 인덱스 = 칸 값 - 1. */
export const COLORS: readonly string[] = [
  '#22d3ee', '#3b82f6', '#f97316', '#facc15', '#4ade80', '#a855f7', '#f87171',
];
/** 가비지(칸 값 8)는 조각 색과 확실히 다른 회색이어야 한다 — 내 블록과 헷갈리면 안 된다. */
export const GARBAGE_COLOR = '#64748b';

/**
 * 키 → 액션.
 *
 * 방향키를 게임이 가져가는 건 **포커스를 받은 뒤**뿐이다(클릭/탭이 조작권 인수 신호).
 * 그러지 않으면 슬라이드에 들어서자마자 덱을 넘길 방법이 사라진다.
 */
export const KEYMAP: Record<string, number> = {
  ArrowLeft: ACT.LEFT, ArrowRight: ACT.RIGHT, ArrowDown: ACT.SOFT, ArrowUp: ACT.CW,
  x: ACT.CW, z: ACT.CCW, a: ACT.FLIP, ' ': ACT.HARD,
  c: ACT.HOLD, Shift: ACT.HOLD, p: ACT.PAUSE,
};

/** 화면 아래 버튼(터치 전용) — 폴더블 접힘에서 키보드 없이도 놀 수 있어야 한다. */
const PADS: readonly [string, number][] = [
  ['◀', ACT.LEFT], ['▶', ACT.RIGHT], ['▼', ACT.SOFT],
  ['⟳', ACT.CW], ['⤓', ACT.HARD], ['HOLD', ACT.HOLD],
];

export interface ViewOptions {
  /** 프레임 예약/취소/시계 — 기본은 브라우저 것, 테스트는 가짜를 넣는다. */
  raf?: (cb: (t: number) => void) => number;
  caf?: (h: number) => void;
  now?: () => number;
  /** 칸 크기 계산에 쓸 가로 폭. 없으면 호스트를 재서 쓴다. */
  maxWidth?: number;
  /** 어트랙트 모드 — AI 가 스스로 둔다. */
  bot?: boolean;
  /** AI 착수 간격(ms) */
  botMs?: number;
  /**
   * 한 번 그릴 때마다 부르는 훅.
   *
   * 특징 값 표처럼 "판 옆에 붙어 같이 갱신되는 것"을 렌더러 안에 넣지 않으려고 둔 문이다.
   * 렌더러가 특징이나 AI 를 알게 되면 파트 5·6의 개념이 화면 코드로 새어 든다.
   */
  onDraw?: () => void;
}

/**
 * 이 파일이 DOM 에 요구하는 전부.
 *
 * `HTMLElement` 를 그대로 쓰지 않는 이유는 두 가지다. 하나는 노드에서 돌리기 위해서고,
 * 다른 하나는 **의존을 문서로 남기기 위해서**다 — 렌더러가 브라우저에 무엇을 바라는지가
 * 이 스무 줄에 다 적혀 있으면, 다른 환경으로 옮길 때 무엇을 흉내 내야 하는지가 분명하다.
 */
export interface Ctx {
  fillStyle: string;
  font: string;
  textAlign: string;
  globalAlpha: number;
  fillRect(x: number, y: number, w: number, h: number): void;
  fillText(t: string, x: number, y: number): void;
}
export interface Elm {
  style: { cssText: string };
  textContent: string;
  tabIndex: number;
  width: number;
  height: number;
  appendChild(c: unknown): unknown;
  addEventListener(type: string, fn: (e: unknown) => void): void;
  getContext(id: string): Ctx;
  getBoundingClientRect(): { width: number };
}
interface Doc { createElement(tag: string): Elm }
type El = Elm;

export class TetrisView {
  readonly canvas: El;
  readonly side: El;
  readonly info: El;
  /** 한 칸의 픽셀 크기. 정수로 떨어뜨린다 — 소수면 칸 경계가 1px 씩 흔들린다. */
  readonly cell: number;

  private readonly ctx: Ctx;
  private readonly sctx: Ctx;
  private readonly raf: (cb: (t: number) => void) => number;
  private readonly caf: (h: number) => void;
  private readonly now: () => number;
  private readonly ai: Ai | null;
  private readonly botMs: number;
  private readonly onDraw: (() => void) | null;
  private botAcc = 0;
  private handle = 0;
  private last = 0;
  private running = false;
  private readonly onKeyBound: (e: unknown) => void;

  constructor(host: HTMLElement, readonly game: Tetris, opts: ViewOptions = {}) {
    const g = globalThis as unknown as {
      requestAnimationFrame?: (cb: (t: number) => void) => number;
      cancelAnimationFrame?: (h: number) => void;
      performance?: { now: () => number };
    };
    this.raf = opts.raf ?? ((cb) => (g.requestAnimationFrame as (c: (t: number) => void) => number)(cb));
    this.caf = opts.caf ?? ((h) => g.cancelAnimationFrame?.(h));
    this.now = opts.now ?? (() => (g.performance ? g.performance.now() : Date.now()));
    this.ai = opts.bot ? new Ai(game, DEFAULT_WEIGHTS) : null;
    this.botMs = opts.botMs ?? 220;
    this.onDraw = opts.onDraw ?? null;

    const doc = (host as unknown as { ownerDocument: Doc }).ownerDocument;
    const avail = opts.maxWidth ?? (Math.round(host.getBoundingClientRect().width) || 360);
    // 판 + 옆 패널(4.5칸)이 들어가야 한다. 8px 아래로는 칸이 뭉개져 안 그리느니만 못하다.
    this.cell = Math.max(8, Math.min(24, Math.floor(avail / (W + 5))));

    const mk = (tag: string, css: string): El => {
      const e = doc.createElement(tag);
      e.style.cssText = css;
      return e;
    };
    const wrap = mk('div', 'display:flex;gap:.5em;align-items:flex-start;justify-content:center;'
      + 'outline:none;touch-action:manipulation');
    wrap.tabIndex = 0; // 클릭하면 포커스를 받는다 = 조작권 인수

    this.canvas = mk('canvas', 'background:#020617;border-radius:6px');
    this.canvas.width = this.cell * W;
    this.canvas.height = this.cell * VIS;
    this.side = mk('canvas', '');
    this.side.width = Math.round(this.cell * 4.5);
    this.side.height = this.cell * VIS;
    this.info = mk('div', `font-size:${Math.max(10, Math.round(this.cell * 0.6))}px;color:#94a3b8;`
      + 'text-align:center;margin-top:.3em');

    wrap.appendChild(this.canvas);
    wrap.appendChild(this.side);
    const box = host as unknown as { appendChild(c: unknown): unknown };
    box.appendChild(wrap);
    box.appendChild(this.info);
    box.appendChild(this.padRow(doc));

    this.ctx = this.canvas.getContext('2d');
    this.sctx = this.side.getContext('2d');

    this.onKeyBound = (e: unknown): void => this.onKey(e as KeyEvt);
    wrap.addEventListener('keydown', this.onKeyBound);
    wrap.addEventListener('keyup', this.onKeyBound);
    this.draw();
  }

  /** 터치용 버튼 줄. 누름/뗌을 그대로 코어의 press/release 로 넘긴다. */
  private padRow(doc: Doc): El {
    const row = doc.createElement('div');
    row.style.cssText = 'display:flex;gap:.25em;justify-content:center;flex-wrap:wrap;margin-top:.35em';
    for (const [label, act] of PADS) {
      const b = doc.createElement('button');
      b.textContent = label;
      b.style.cssText = 'min-width:2.4em;padding:.35em .5em;font-size:.8em;border-radius:6px;'
        + 'border:1px solid #334155;background:#0f172a;color:#cbd5e1';
      // pointerdown 에서 기본동작을 막아야 버튼을 누른 채 끌 때 화면이 스크롤되지 않는다.
      b.addEventListener('pointerdown', (e: unknown) => {
        (e as { preventDefault?: () => void }).preventDefault?.();
        this.game.press(act);
      });
      b.addEventListener('pointerup', () => this.game.release(act));
      b.addEventListener('pointerleave', () => this.game.release(act));
      row.appendChild(b);
    }
    return row;
  }

  // ── 입력 ────────────────────────────────────────────────────────────
  /** keydown/keyup 한 번. 매핑에 없는 키는 **건드리지 않는다** — 덱이 써야 한다. */
  onKey(e: KeyEvt): void {
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    const act = KEYMAP[k];
    if (act === undefined) return;
    e.preventDefault();
    if (e.type === 'keydown') this.game.press(act);
    else this.game.release(act);
    this.draw();
  }

  // ── 루프 ────────────────────────────────────────────────────────────
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
    // dt 는 정수 밀리초여야 한다. 코어의 결정론이 여기 걸려 있다.
    let dt = Math.round(t - this.last);
    this.last = t;
    if (dt < 0) dt = 0;
    if (dt > 100) dt = 100; // 탭 전환 뒤의 거대한 간격
    if (dt > 0) {
      this.game.update(dt);
      if (this.ai) {
        this.botAcc += dt;
        while (this.botAcc >= this.botMs && (this.game.stats[ST.STATE] as number) === STATE.PLAY) {
          this.botAcc -= this.botMs;
          this.ai.step();
        }
      }
    }
    this.draw();
  }

  // ── 그리기 ──────────────────────────────────────────────────────────
  /** 굳은 블록 → 고스트 → 현재 조각 순서로 덮어 칠한다. */
  draw(): void {
    const c = this.ctx, s = this.cell;
    c.fillStyle = '#020617';
    c.fillRect(0, 0, this.cell * W, this.cell * VIS);

    for (let i = 0; i < VIS * W; i++) {
      const v = this.game.cells[i] as number;
      if (!v) continue;
      c.fillStyle = v === GARBAGE ? GARBAGE_COLOR : (COLORS[v - 1] as string);
      c.fillRect((i % W) * s, Math.floor(i / W) * s, s - 1, s - 1);
    }
    for (let i = 0; i < VIS * W; i++) {
      const v = this.game.overlay[i] as number;
      if (!v) continue;
      const ghost = v >= 8;
      c.fillStyle = COLORS[(ghost ? v - 8 : v - 1)] as string;
      c.globalAlpha = ghost ? 0.28 : 1;
      c.fillRect((i % W) * s, Math.floor(i / W) * s, s - 1, s - 1);
      c.globalAlpha = 1;
    }
    if ((this.game.stats[ST.STATE] as number) === STATE.OVER) {
      c.fillStyle = '#f87171';
      c.font = `bold ${Math.round(s * 1.1)}px system-ui, sans-serif`;
      c.textAlign = 'center';
      c.fillText('GAME OVER', (this.cell * W) / 2, (this.cell * VIS) / 2);
    }
    this.drawSide();
    this.info.textContent =
      `점수 ${this.game.stats[ST.SCORE]} · 줄 ${this.game.stats[ST.LINES]} · 레벨 ${this.game.stats[ST.LEVEL]}`
      + ((this.game.stats[ST.PENDING] as number) > 0 ? ` · 대기 ${this.game.stats[ST.PENDING]}줄` : '');
    if (this.onDraw) this.onDraw();
  }

  /** 옆 패널 — 홀드 하나와 다음 다섯. 미니 조각은 4×4 박스를 반 칸 크기로 그린다. */
  private drawSide(): void {
    const c = this.sctx, s = this.cell, w = Math.round(s * 4.5);
    c.fillStyle = '#020617';
    c.fillRect(0, 0, w, s * VIS);
    const mini = (piece: number, ox: number, oy: number): void => {
      if (piece < 0) return;
      const m = (SHAPES[piece] as readonly number[])[0] as number;
      const h = Math.max(4, Math.floor(s * 0.55));
      c.fillStyle = COLORS[piece] as string;
      for (let i = 0; i < 16; i++) {
        if (!(m & (1 << i))) continue;
        c.fillRect(ox + (i & 3) * h, oy + (i >> 2) * h, h - 1, h - 1);
      }
    };
    c.fillStyle = '#64748b';
    c.font = `${Math.max(9, Math.round(s * 0.5))}px system-ui, sans-serif`;
    c.textAlign = 'left';
    c.fillText('HOLD', 2, s);
    mini(this.game.stats[ST.HOLD] as number, 2, s * 1.3);
    c.fillStyle = '#64748b';
    c.fillText('NEXT', 2, s * 4.2);
    for (let i = 0; i < 5; i++) {
      mini(this.game.stats[ST.NEXT0 + i] as number, 2, s * (4.6 + i * 2.2));
    }
  }
}

/** onKey 가 받는 최소한의 모양 — 진짜 KeyboardEvent 도 이 모양을 만족한다. */
export interface KeyEvt {
  type: string;
  key: string;
  preventDefault: () => void;
}

/** 보이는 줄 수만큼의 빈 판을 만든다 — 데모가 "이 자리에 이런 판" 을 세울 때 쓴다. */
export function fillRows(game: Tetris, rows: readonly string[]): void {
  for (let r = 0; r < rows.length; r++) {
    const y = HIDDEN + VIS - rows.length + r;
    const line = rows[r] as string;
    for (let x = 0; x < W; x++) {
      const ch = line[x] ?? '.';
      game.board[y * W + x] = ch === '.' ? 0 : ch === '#' ? GARBAGE : (Number(ch) || 1);
    }
  }
  game.buildView();
}

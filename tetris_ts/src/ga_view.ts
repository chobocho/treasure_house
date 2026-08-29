// ga_view.ts — 이 문서 안에서 세대가 진행되는 걸 보여 주는 화면.
//
// 여기서 도는 학습은 `make train` 과 **같은 코드**다(ga.ts 의 LiveGa). 다른 건 셋뿐이다:
//   · 개체군과 조각 수를 줄여 한 세대가 몇 초에 끝나게 했다
//   · 한 프레임에 예산(기본 10ms)만큼만 평가하고 돌아온다 — 화면이 얼지 않게
//   · 결과를 파일이 아니라 캔버스에 그린다
//
// view.ts 와 같은 이유로 시계·프레임·문서를 주입받는다.

import { LiveGa, type EvolveOptions } from './ga.js';
import { FEATURE_NAMES } from './ai.js';
import type { Ctx, Elm } from './view.js';

export interface GaViewOptions {
  raf?: (cb: (t: number) => void) => number;
  caf?: (h: number) => void;
  now?: () => number;
  maxWidth?: number;
  /** 한 프레임에 쓸 평가 예산(ms). 너무 키우면 스크롤이 끊긴다. */
  budgetMs?: number;
  /** LiveGa 에 그대로 넘긴다 — 덱 데모는 작은 값을 쓴다. */
  ga?: EvolveOptions;
}

interface Doc { createElement(tag: string): Elm }

/** 곡선 색 — 최고는 하늘색, 평균은 보라. 덱의 다른 그림과 같은 규칙이다. */
const C_BEST = '#22d3ee';
const C_MEAN = '#a855f7';

export class GaView {
  readonly ga: LiveGa;
  readonly canvas: Elm;
  readonly info: Elm;
  readonly bars: Elm;

  private readonly ctx: Ctx;
  private readonly bctx: Ctx;
  private readonly raf: (cb: (t: number) => void) => number;
  private readonly caf: (h: number) => void;
  private readonly now: () => number;
  private readonly budgetMs: number;
  private handle = 0;
  private running = false;

  constructor(host: HTMLElement, opts: GaViewOptions = {}) {
    const g = globalThis as unknown as {
      requestAnimationFrame?: (cb: (t: number) => void) => number;
      cancelAnimationFrame?: (h: number) => void;
      performance?: { now: () => number };
    };
    this.raf = opts.raf ?? ((cb) => (g.requestAnimationFrame as (c: (t: number) => void) => number)(cb));
    this.caf = opts.caf ?? ((h) => g.cancelAnimationFrame?.(h));
    this.now = opts.now ?? (() => (g.performance ? g.performance.now() : Date.now()));
    this.budgetMs = opts.budgetMs ?? 10;
    // 덱 데모의 기본값: 개체 16 · 200조각 · 시드 하나 · 20조각마다 가비지 한 줄.
    // 초반 세대는 0.1초, 개체가 오래 버티기 시작하면 0.5초쯤 걸린다(예산 10ms 기준 약 1초).
    this.ga = new LiveGa({
      pop: 16, maxPieces: 200, seeds: [1], rngSeed: 20260829, every: 20, ...(opts.ga ?? {}),
    });

    const doc = (host as unknown as { ownerDocument: Doc }).ownerDocument;
    const w = opts.maxWidth ?? (Math.round(host.getBoundingClientRect().width) || 360);
    const mk = (tag: string, css: string): Elm => {
      const e = doc.createElement(tag);
      e.style.cssText = css;
      return e;
    };
    this.canvas = mk('canvas', 'background:#020617;border-radius:6px;width:100%');
    this.canvas.width = Math.max(240, Math.min(640, w));
    this.canvas.height = Math.round(this.canvas.width * 0.45);
    this.bars = mk('canvas', 'background:#020617;border-radius:6px;width:100%;margin-top:.3em');
    this.bars.width = this.canvas.width;
    this.bars.height = Math.round(this.canvas.width * 0.28);
    this.info = mk('div', 'font-size:.78em;color:#94a3b8;text-align:center;margin-top:.3em');

    const box = host as unknown as { appendChild(c: unknown): unknown };
    box.appendChild(this.canvas);
    box.appendChild(this.info);
    box.appendChild(this.bars);
    this.ctx = this.canvas.getContext('2d');
    this.bctx = this.bars.getContext('2d');
    this.draw();
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.handle = this.raf(() => this.frame());
  }

  stop(): void {
    if (!this.running) return;
    this.running = false;
    this.caf(this.handle);
    this.handle = 0;
  }

  private frame(): void {
    if (!this.running) return;
    this.handle = this.raf(() => this.frame());
    this.ga.step(this.budgetMs, this.now);
    this.draw();
  }

  /** 세대별 최고·평균 곡선. 세로 눈금은 지금까지의 최고값에 맞춰 늘어난다. */
  private draw(): void {
    const c = this.ctx, W = this.canvas.width, H = this.canvas.height, P = 22;
    c.fillStyle = '#020617';
    c.fillRect(0, 0, W, H);
    const log = this.ga.log;
    const top = Math.max(1, ...log.map((r) => r.best));
    const sx = (i: number): number => P + (log.length < 2 ? 0 : (i / (log.length - 1)) * (W - P * 2));
    const sy = (v: number): number => H - P - (v / top) * (H - P * 2);

    c.fillStyle = '#334155';
    for (let i = 0; i <= 4; i++) c.fillRect(P, sy((top * i) / 4), W - P * 2, 1);

    const line = (key: 'best' | 'mean', color: string): void => {
      if (log.length < 2) return;
      const cc = c as unknown as {
        beginPath(): void; moveTo(x: number, y: number): void;
        lineTo(x: number, y: number): void; stroke(): void;
        strokeStyle: string; lineWidth: number;
      };
      cc.strokeStyle = color;
      cc.lineWidth = 2;
      cc.beginPath();
      log.forEach((r, i) => (i ? cc.lineTo(sx(i), sy(r[key])) : cc.moveTo(sx(i), sy(r[key]))));
      cc.stroke();
    };
    line('mean', C_MEAN);
    line('best', C_BEST);

    c.fillStyle = '#64748b';
    c.font = '11px system-ui, sans-serif';
    c.textAlign = 'left';
    c.fillText(`최고 ${top.toFixed(1)}`, P, 14);

    const pct = Math.round(this.ga.progress * 100);
    this.info.textContent = `${this.ga.gen}세대 · 평가 ${pct}% · 최고 적합도 `
      + `${this.ga.bestFit < 0 ? '—' : this.ga.bestFit.toFixed(1)} (보낸 줄)`;
    this.drawBars();
  }

  /** 지금까지의 최고 유전자 — 특징 여덟 개의 부호와 크기를 막대로. */
  private drawBars(): void {
    const c = this.bctx, W = this.bars.width, H = this.bars.height;
    c.fillStyle = '#020617';
    c.fillRect(0, 0, W, H);
    const g = this.ga.best;
    const mid = H / 2;
    c.fillStyle = '#334155';
    c.fillRect(0, mid, W, 1);
    if (!g) return;
    const bw = W / g.length;
    for (let i = 0; i < g.length; i++) {
      const v = g[i] as number;
      const h = Math.abs(v) * (H / 2 - 12);
      c.fillStyle = v >= 0 ? C_BEST : '#f87171';
      c.fillRect(i * bw + 3, v >= 0 ? mid - h : mid, bw - 6, h);
      c.fillStyle = '#64748b';
      c.font = '9px system-ui, sans-serif';
      c.textAlign = 'center';
      // 이름이 길어서 F_ 접두사는 뗀다 — 좁은 화면에서 겹친다.
      c.fillText((FEATURE_NAMES[i] as string).replace('F_', ''), i * bw + bw / 2, H - 2);
    }
  }
}

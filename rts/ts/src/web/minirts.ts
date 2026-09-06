// 미니 RTS — 덱 안에서 실제로 해 볼 수 있는 판.
//
// 이 파일에는 규칙이 없다. 규칙은 전부 sim.Sim 안에 있고, 여기는 사람의 손짓을
// **명령 여섯 칸**(§18.1)으로 바꿔 sim.step() 에 넣는 껍데기다. 상태를 직접
// 건드리는 줄이 하나라도 생기면 이 판은 골든 트레이스를 만든 그 엔진이 아니게 된다 —
// 그래서 여기에는 w.hp[i] = … 같은 대입이 없다. 있으면 그것이 버그다.
//
// 그리기도 마찬가지다. render.draw() 가 320×200 인덱스 배열을 채우고, canvas.ts 가
// 그것을 편다. 이 파일이 캔버스에 긋는 선은 없다.
import * as C from '../const';
import * as RS from '../raster';
import * as RD from '../render';
import * as SEL from '../select';
import * as SIM from '../sim';
import * as S from '../spatial';
import * as T from '../tmap';
import { Screen } from './canvas';
import { MAP_START_TXT } from './data';

// 덱의 데모 틀이 주는 것. 여기서는 .out 을 찾는 데만 쓴다.
export interface DemoApi {
  out(host: HTMLElement): HTMLElement | null;
}

const ME = 0;                    // 사람이 잡는 진영
const FOE = 1;

// 지을 수 있는 것과 뽑을 수 있는 것. 순서가 단추 순서다.
const BUILDS: number[] = [C.REF, C.BARR, C.POW, C.FACT, C.TOWER];
const TRAINS: number[] = [C.HARV, C.INF, C.ARCHER, C.TANK, C.MORTAR];

// 유닛 종류 → 그것을 뽑는 건물. §25.3 의 선행과는 다른 표다 —
// 선행은 "지을 수 있는가", 이것은 "누가 큐를 갖는가".
const TRAINER: number[] = [];
for (let k = 0; k < C.KIND_COUNT; k += 1) TRAINER.push(-1);
TRAINER[C.HARV] = C.HQ;
TRAINER[C.INF] = C.BARR;
TRAINER[C.ARCHER] = C.BARR;
TRAINER[C.TANK] = C.FACT;
TRAINER[C.MORTAR] = C.FACT;

// §18.1 의 사전식 순서. sim.step 이 정렬을 검사하고 어긋나면 던진다.
function cmpOrder(a: number[], b: number[]): number {
  for (let i = 0; i < a.length && i < b.length; i += 1) {
    if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  }
  return a.length - b.length;
}

function el(tag: string, cls?: string, text?: string): HTMLElement {
  const e = document.createElement(tag);
  if (cls !== undefined) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

export class MiniRts {
  readonly sim: SIM.Sim;
  readonly view: RD.View;
  private readonly screen: Screen;
  private readonly fb: number[];
  private readonly pal: RS.RGB[];
  private readonly light: number[][];
  private readonly status: HTMLElement;
  private readonly bar: HTMLElement;
  private pending: number[][];
  private sel: number[];
  private buildKind: number;
  private drag: [number, number] | null;
  private mouse: [number, number];
  private message: string;
  private running: boolean;
  private acc: number;
  private last: number;
  private raf: number;
  private phase: number;

  constructor(host: HTMLElement, api: DemoApi) {
    const m = T.TMap.loadText(MAP_START_TXT);
    this.sim = new SIM.Sim(m, 1, 2);
    this.sim.setupStart(true);          // 두 진영 모두 AI 로 세우고
    this.sim.aiEnabled[ME] = false;     // 내 쪽만 손으로 잡는다
    this.view = new RD.View();
    this.view.centerOn(m, m.starts[ME][0], m.starts[ME][1]);
    this.pal = RS.buildPalette();
    this.light = RS.buildLight(this.pal);
    this.fb = new Array<number>(C.SCR_W * C.SCR_H).fill(0);
    this.screen = new Screen(2);
    this.pending = [];
    this.sel = [];
    this.buildKind = -1;
    this.drag = null;
    this.mouse = [0, 0];
    this.message = '';
    this.running = true;
    this.acc = 0;
    this.last = 0;
    this.raf = 0;
    this.phase = 0;

    const out = api.out(host) || host;
    out.innerHTML = '';
    const wrap = el('div');
    wrap.style.display = 'flex';
    wrap.style.flexDirection = 'column';
    wrap.style.gap = '6px';
    wrap.appendChild(this.screen.canvas);
    this.bar = el('div', 'row');
    this.status = el('div');
    this.status.style.fontSize = '.8rem';
    this.status.style.lineHeight = '1.5';
    wrap.appendChild(this.bar);
    wrap.appendChild(this.status);
    out.appendChild(wrap);

    this.buildBar();
    this.wire();
    this.draw();
    this.tickLoop = this.tickLoop.bind(this);
    this.raf = requestAnimationFrame(this.tickLoop);
  }

  // ── 단추 ──────────────────────────────────────────────────────────────────
  private buildBar(): void {
    const mk = (label: string, fn: () => void): void => {
      const b = el('button', 'sec', label) as HTMLButtonElement;
      b.addEventListener('click', (e) => { e.preventDefault(); fn(); });
      this.bar.appendChild(b);
    };
    for (const k of BUILDS) {
      mk('건설 ' + C.NAME[k] + ' ' + C.COST[k], () => {
        this.buildKind = this.buildKind === k ? -1 : k;
        this.say(this.buildKind < 0 ? '건설 취소'
                 : C.NAME[k] + ' — 놓을 자리를 누르세요');
      });
    }
    for (const k of TRAINS) {
      mk('생산 ' + C.NAME[k] + ' ' + C.COST[k], () => this.train(k));
    }
    mk('정지', () => this.orderSelection(SEL.STOP, 0, 0, 0));
    mk('일시정지', () => {
      this.running = !this.running;
      this.say(this.running ? '진행' : '멈춤');
    });
  }

  // ── 명령 ──────────────────────────────────────────────────────────────────
  // 모든 상태 변화가 지나는 유일한 문. §12.5 — UI 는 시뮬을 직접 만지지 않는다.
  private push(o: number[]): void {
    this.pending.push(o);
  }

  private orderSelection(kind: number, a: number, b: number, c: number): void {
    for (const h of this.sel) {
      if (this.sim.w.valid(h)) this.push([ME, h, kind, a, b, c]);
    }
  }

  // 내 건물 중 조건에 맞는 첫 핸들. 없으면 0.
  private myBuilding(kind: number): number {
    const w = this.sim.w;
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (w.alive[i] === 1 && w.owner[i] === ME && w.kind[i] === kind
          && w.hp[i] > 0) return w.handle(i);
    }
    return 0;
  }

  private train(kind: number): void {
    const need = TRAINER[kind];
    // 고른 것 중에 생산 건물이 있으면 그것이 뽑는다. 없으면 아무 것이나 찾는다.
    let issuer = 0;
    for (const h of this.sel) {
      if (this.sim.w.valid(h)
          && this.sim.w.kind[S.index(h)] === need) { issuer = h; break; }
    }
    if (issuer === 0) issuer = this.myBuilding(need);
    if (issuer === 0) { this.say(C.NAME[need] + ' 이(가) 없습니다'); return; }
    if (!this.sim.ec.canBuild(this.sim.w, ME, kind)) {
      this.say(C.NAME[kind] + ' 은(는) 선행이 모자랍니다'); return;
    }
    this.push([ME, issuer, SEL.TRAIN, kind, 0, 0]);
    this.say(C.NAME[kind] + ' 을(를) 큐에 넣었습니다');
  }

  private place(tx: number, ty: number): void {
    const k = this.buildKind;
    const issuer = this.myBuilding(C.HQ) || this.myBuilding(C.BARR);
    if (issuer === 0) { this.say('명령을 낼 건물이 없습니다'); return; }
    this.push([ME, issuer, SEL.BUILD, k, tx, ty]);
    this.buildKind = -1;
    this.say(C.NAME[k] + ' 건설 명령');
  }

  // ── 입력 ──────────────────────────────────────────────────────────────────
  private wire(): void {
    const cv = this.screen.canvas;
    cv.addEventListener('contextmenu', (e) => e.preventDefault());
    cv.addEventListener('mousedown', (e) => this.onDown(e));
    cv.addEventListener('mousemove', (e) => this.onMove(e));
    cv.addEventListener('mouseup', (e) => this.onUp(e));
    cv.addEventListener('mouseleave', () => { this.drag = null; });
    cv.tabIndex = 0;
    cv.addEventListener('keydown', (e) => this.onKey(e));
  }

  private onKey(e: KeyboardEvent): void {
    const step = 16;
    let dx = 0;
    let dy = 0;
    if (e.key === 'ArrowLeft') dx = -step;
    else if (e.key === 'ArrowRight') dx = step;
    else if (e.key === 'ArrowUp') dy = -step;
    else if (e.key === 'ArrowDown') dy = step;
    else if (e.key === 'Escape') { this.buildKind = -1; this.sel = []; }
    else return;
    // 덱이 슬라이드를 넘겨 버리면 판이 사라진다.
    e.preventDefault();
    if (dx !== 0 || dy !== 0) this.view.move(this.sim.m, dx, dy);
    this.draw();
  }

  private onDown(e: MouseEvent): void {
    const [sx, sy] = this.screen.eventPos(e);
    this.mouse = [sx, sy];
    (this.screen.canvas as HTMLElement).focus();
    if (e.button === 2) { this.context(sx, sy); return; }
    if (sx >= C.MINI_X && sy < C.MINI_H) {          // 미니맵 클릭 — 카메라만
      const [tx, ty] = RD.minimapToTile(sx - C.MINI_X, sy - C.MINI_Y);
      this.view.centerOn(this.sim.m, tx, ty);
      this.draw();
      return;
    }
    if (!SEL.inView(sx, sy)) return;
    if (this.buildKind >= 0) {
      const cam: [number, number] = [this.view.camX, this.view.camY];
      const [wx, wy] = SEL.screenToWorld(cam, sx, sy);
      this.place(Math.floor(wx / C.TILE), Math.floor(wy / C.TILE));
      return;
    }
    this.drag = [sx, sy];
  }

  private onMove(e: MouseEvent): void {
    const [sx, sy] = this.screen.eventPos(e);
    this.mouse = [sx, sy];
  }

  private onUp(e: MouseEvent): void {
    if (e.button === 2 || this.drag === null) return;
    const [sx, sy] = this.screen.eventPos(e);
    const [ax, ay] = this.drag;
    this.drag = null;
    const cam: [number, number] = [this.view.camX, this.view.camY];
    if (Math.abs(sx - ax) < 3 && Math.abs(sy - ay) < 3) {
      const h = SEL.pick(this.sim.w, cam, sx, sy);
      // 남의 것을 집으면 고르지 않는다 — 정보는 화면이 이미 보여 준다.
      this.sel = (h !== 0 && this.sim.w.owner[S.index(h)] === ME) ? [h] : [];
    } else {
      this.sel = SEL.boxSelect(this.sim.w, ME, cam, ax, ay, sx, sy);
    }
    this.say(this.sel.length === 0 ? '선택 없음'
             : this.sel.length + '기 선택');
    this.draw();
  }

  // 우클릭 한 번의 뜻은 select.contextOrder 가 정한다 — 여기서 다시 정하지 않는다.
  private context(sx: number, sy: number): void {
    if (!SEL.inView(sx, sy) || this.sel.length === 0) return;
    const cam: [number, number] = [this.view.camX, this.view.camY];
    const [wx, wy] = SEL.screenToWorld(cam, sx, sy);
    const tx = Math.floor(wx / C.TILE);
    const ty = Math.floor(wy / C.TILE);
    const h = SEL.pick(this.sim.w, cam, sx, sy);
    const kind = SEL.contextOrder(this.sim.w, this.sim.ec, this.sim.m, ME,
                                  tx, ty, h);
    for (const s of this.sel) {
      if (!this.sim.w.valid(s)) continue;
      if (kind === SEL.ATTACK) this.push([ME, s, kind, 0, 0, h]);
      else this.push([ME, s, kind, tx, ty, 0]);
    }
    const names = ['이동', '공격', '공격이동', '채집', '건설', '정지', '대기',
                   '생산'];
    this.say('우클릭 → ' + names[kind]);
  }

  // ── 루프 ──────────────────────────────────────────────────────────────────
  // 18.2065 Hz(§3.2). 프레임이 밀려도 한 번에 세 틱까지만 따라잡는다 —
  // 탭을 다시 열었을 때 몇 백 틱을 몰아 도는 것을 막는다.
  private tickLoop(now: number): void {
    this.raf = requestAnimationFrame(this.tickLoop);
    if (this.last === 0) this.last = now;
    const dt = now - this.last;
    this.last = now;
    if (!this.running || this.sim.winner >= 0) return;
    if (this.screen.canvas.offsetParent === null) return;   // 안 보이는 슬라이드
    this.acc += dt;
    const per = C.TICK_US / 1000;
    let n = 0;
    while (this.acc >= per && n < 3) {
      this.acc -= per;
      n += 1;
      this.stepOnce();
    }
    if (n > 0) this.draw();
  }

  private stepOnce(): void {
    const [dx, dy] = RD.edgeScroll(this.mouse[0], this.mouse[1]);
    if (dx !== 0 || dy !== 0) this.view.move(this.sim.m, dx, dy);
    const orders = this.pending;
    this.pending = [];
    orders.sort(cmpOrder);
    this.sim.step(orders);
    this.sel = this.sel.filter((h) => this.sim.w.valid(h));
    this.phase = (this.phase + 1) % RS.WATER_N;
  }

  private say(s: string): void {
    this.message = s;
  }

  // 화면 = 엔진이 그린 것. 여기서 더 그리는 것은 없다.
  draw(): void {
    this.screen.setPalette(RS.cycleWater(this.pal, this.phase));
    RD.draw(this.fb, this.sim, this.view, this.phase, this.pal, this.light,
            ME, this.sel, this.message);
    this.screen.paint(this.fb);
    this.status.textContent = this.statusText();
  }

  private statusText(): string {
    const ec = this.sim.ec;
    const mine = this.count(ME);
    const foe = this.count(FOE);
    let head = '틱 ' + this.sim.tick + ' · 크레딧 ' + ec.credits[ME]
      + ' · 인구 ' + ec.supplyUsed[ME] + '/' + ec.supplyCap[ME]
      + ' · 내 것 ' + mine + '기 · 적 ' + foe + '기';
    if (this.sim.winner === ME) head = '★ 승리 — ' + head;
    else if (this.sim.winner >= 0) head = '패배 — ' + head;
    return head + '\n왼쪽 끌기로 선택 · 오른쪽 클릭이 문맥 명령(이동·공격·채집)'
      + ' · 화살표로 스크롤 · 적 건물을 전부 부수면 이깁니다';
  }

  private count(p: number): number {
    const w = this.sim.w;
    let n = 0;
    for (let i = 1; i < C.MAX_ENT; i += 1) {
      if (w.alive[i] === 1 && w.owner[i] === p) n += 1;
    }
    return n;
  }

  stop(): void {
    if (this.raf !== 0) cancelAnimationFrame(this.raf);
    this.raf = 0;
  }
}

// 데모 틀이 부르는 자리. 한 슬라이드에 하나만 만든다.
export function boot(host: HTMLElement, api: DemoApi): MiniRts {
  return new MiniRts(host, api);
}


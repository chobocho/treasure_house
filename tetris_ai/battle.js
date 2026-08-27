// ============================================================================
//  battle.js — wasm 코어 두 개를 화면·손가락·심판에 연결하는 층
//
//  부 1 의 glue.js 가 하던 네 가지(로드·메모리 창·고정 스텝 루프·입력)에
//  이 파일은 세 가지를 더한다.
//    5) AiDriver  — ai_plan() 이 고른 수를 사람처럼 키 입력으로 실행한다
//    6) Referee   — 한쪽의 ST_ATTACK 을 반대쪽 ts_queue_garbage() 로 배달한다
//    7) BattleView— 인스턴스 두 개를 한 프레임 루프 안에서 나란히 돌린다
//  게임 규칙과 대전 규칙은 여전히 단 한 줄도 여기 없다. 전부 C++ 쪽에 있다.
// ============================================================================

// === SECTION: consts === JS 쪽 상수 = C++ enum 과의 계약
// 조각 색 (인덱스 = C++ 의 조각 번호 + 1). 8번은 대전에서 올라오는 회색 가비지다.
const COLORS = ['#000000', '#22d3ee', '#3b82f6', '#f59e0b', '#facc15',
                '#22c55e', '#a855f7', '#ef4444', '#6b7280'];
const NAMES  = ['I', 'J', 'L', 'O', 'S', 'T', 'Z'];

const ACT = { LEFT: 0, RIGHT: 1, SOFT: 2, CW: 3, CCW: 4, HARD: 5, HOLD: 6, PAUSE: 7, FLIP: 8 };
const ST  = { SCORE: 0, LINES: 1, LEVEL: 2, COMBO: 3, B2B: 4, STATE: 5, HOLD: 6, NEXT0: 7,
              CLEAR: 12, TSPIN: 13, GAIN: 14, PIECES: 15, ELAPSED: 16, GRAVITY: 17,
              PIECE: 18, ROT: 19, X: 20, Y: 21, GHOST: 22, EVENT: 23, ROWMASK: 24,
              PERFECT: 25, LOCKPCT: 26, ATTACK: 27, PENDING: 28, GARBAGE_RECV: 29, COUNT: 30 };
const F   = { LINES: 0, AGG: 1, HOLES: 2, BUMP: 3, WELLS: 4, ROWT: 5, COLT: 6, LAND: 7, COUNT: 8 };
const FEAT_KO = ['지운 줄', '높이 총합', '구멍', '요철', '우물', '행 전이', '열 전이', '착지 높이'];

const SHAPES = [
  [0x00F0, 0x2222, 0x0F00, 0x4444], [0x0071, 0x0226, 0x0470, 0x0322],
  [0x0074, 0x0622, 0x0170, 0x0223], [0x0066, 0x0066, 0x0066, 0x0066],
  [0x0036, 0x0462, 0x0360, 0x0231], [0x0072, 0x0262, 0x0270, 0x0232],
  [0x0063, 0x0264, 0x0630, 0x0132],
];

// === SECTION: load === base64 → 컴파일 → 인스턴스 (모듈 1개, 인스턴스 N개)
function b64ToBytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
let modulePromise = null;
function compileOnce(b64) {
  if (!modulePromise) modulePromise = WebAssembly.compile(b64ToBytes(b64));
  return modulePromise;
}
// 대전이 성립하는 이유가 여기 한 줄에 있다: 코드는 한 번만 컴파일하고,
// 상태(선형 메모리)만 인스턴스마다 새로 만든다. 두 판이 서로를 전혀 모른다.
async function loadCore(b64, seed) {
  const mod = await compileOnce(b64);
  const inst = await WebAssembly.instantiate(mod, {});
  const e = inst.exports;
  const dims = e.ts_dims(), rows = e.ts_rows();
  const core = { e, W: dims >>> 16, VIS: dims & 0xffff, H: rows >>> 16, HIDDEN: rows & 0xffff, views: null };
  core.refresh = () => makeViews(core);
  e.ts_init(seed >>> 0);
  core.refresh();
  return core;
}

// === SECTION: views === 선형 메모리 위에 TypedArray 창 내기
function makeViews(core) {
  const { e, W, VIS, H } = core;
  const buf = e.memory.buffer;
  core.views = {
    buf,
    board:    new Uint8Array(buf, e.ts_board(), H * W),
    cells:    new Uint8Array(buf, e.ts_cells(), VIS * W),
    overlay:  new Uint8Array(buf, e.ts_overlay(), VIS * W),
    stats:    new Int32Array(buf, e.ts_stats(), ST.COUNT),
    weights:  new Float32Array(buf, e.ai_weights_ptr(), F.COUNT),
    features: new Float32Array(buf, e.ai_features_ptr(), F.COUNT),
  };
  return core.views;
}
function V(core) {
  if (!core.views || core.views.buf.byteLength === 0) makeViews(core);
  return core.views;
}
function setWeights(core, w) { V(core).weights.set(w); }

// === SECTION: paint === 블록 하나를 그리는 법
function roundRect(g, x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2);
  g.beginPath();
  g.moveTo(x + rr, y);
  g.arcTo(x + w, y,     x + w, y + h, rr);
  g.arcTo(x + w, y + h, x,     y + h, rr);
  g.arcTo(x,     y + h, x,     y,     rr);
  g.arcTo(x,     y,     x + w, y,     rr);
  g.closePath();
}
function shade(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const cl = (v) => Math.max(0, Math.min(255, v + amt));
  return '#' + [cl((n >> 16) & 255), cl((n >> 8) & 255), cl(n & 255)]
    .map((v) => v.toString(16).padStart(2, '0')).join('');
}
function drawMino(g, px, py, s, color, style) {
  const pad = Math.max(1, s * 0.06);
  const x = px + pad, y = py + pad, w = s - pad * 2, h = s - pad * 2;
  if (style === 'ghost') {
    g.globalAlpha = 0.20; g.fillStyle = color;
    roundRect(g, x, y, w, h, s * 0.18); g.fill();
    g.globalAlpha = 0.65; g.strokeStyle = color; g.lineWidth = Math.max(1, s * 0.07);
    roundRect(g, x, y, w, h, s * 0.18); g.stroke();
    g.globalAlpha = 1;
    return;
  }
  const grad = g.createLinearGradient(x, y, x, y + h);
  grad.addColorStop(0, color);
  grad.addColorStop(1, shade(color, -34));
  g.fillStyle = grad;
  roundRect(g, x, y, w, h, s * 0.18); g.fill();
  g.fillStyle = 'rgba(255,255,255,0.30)';
  roundRect(g, x + w * 0.14, y + h * 0.10, w * 0.72, h * 0.20, s * 0.08); g.fill();
}

// === SECTION: driver === AI 드라이버 — 계획을 "손가락 속도"로 실행한다
// ai_plan() 은 1 ms 도 안 걸려 답을 내지만, 그 답을 즉시 판에 꽂으면 사람 눈에는
// 조각이 순간이동한 것으로 보인다. 그래서 계획을 목표(rot, x)로 들고 있다가
// moveMs 마다 키 하나씩만 눌러 도달한다. 조작 경로가 사람과 완전히 같아진다.
class AiDriver {
  constructor(core, opts = {}) {
    this.core = core;
    this.thinkMs = opts.thinkMs ?? 260;      // 조각 하나를 "생각하는" 시간
    this.moveMs  = opts.moveMs  ?? 55;       // 키 하나 사이의 간격
    this.blunder = opts.blunder ?? 0;        // 0~1, 이 확률로 엉뚱한 자리를 고른다
    this.setWeights(opts.weights);
    this.target = null;
    this.t = 0;
    this.guard = 0;
    this.lastPacked = -1;
  }
  setWeights(w) { if (w) setWeights(this.core, w); this.weights = w; }
  configure(o) {
    if (o.thinkMs !== undefined) this.thinkMs = o.thinkMs;
    if (o.moveMs  !== undefined) this.moveMs  = o.moveMs;
    if (o.blunder !== undefined) this.blunder = o.blunder;
    if (o.weights) this.setWeights(o.weights);
  }

  plan() {
    const e = this.core.e;
    let packed = e.ai_plan();
    if (packed < 0) return null;
    this.lastPacked = packed;
    let rot = (packed >> 4) & 3, x = (packed & 15) - 3, hold = (packed >> 8) & 1;
    // 실수: 회전과 위치를 아무렇게나 바꾼다. 난이도를 낮추는 가장 정직한 방법 —
    // 약한 AI 를 만들려고 규칙을 봐주는 게 아니라 "가끔 잘못 둔다"로 만든다.
    if (this.blunder > 0 && Math.random() < this.blunder) {
      rot = (Math.random() * 4) | 0;
      x = ((Math.random() * 10) | 0);
      hold = 0;
    }
    return { rot, x, hold, guard: 0 };
  }

  // 16 ms 고정 스텝마다 호출된다. 키를 최대 한 번 누른다.
  step(dt) {
    const e = this.core.e, s = V(this.core).stats;
    if (s[ST.STATE] !== 0) return;
    this.t += dt;
    if (!this.target) {
      if (this.t < this.thinkMs) return;
      this.t = 0;
      this.target = this.plan();
      return;
    }
    if (this.t < this.moveMs) return;
    this.t = 0;
    const tg = this.target;
    if (tg.guard++ > 24) { e.ts_press(ACT.HARD); this.target = null; return; }
    if (tg.hold)            { e.ts_press(ACT.HOLD); tg.hold = 0; return; }
    if (s[ST.ROT] !== tg.rot) { e.ts_press(ACT.CW); return; }
    if (s[ST.X] !== tg.x) {
      const a = s[ST.X] > tg.x ? ACT.LEFT : ACT.RIGHT;
      e.ts_press(a); e.ts_release(a);
      return;
    }
    e.ts_press(ACT.HARD);
    this.target = null;
    this.t = -this.thinkMs;                  // 다음 조각은 다시 생각 시간부터
  }
  reset() { this.target = null; this.t = 0; }
}

// === SECTION: referee === 심판 — 숫자 하나를 옮기는 배달부
// 규칙은 C++ 안에 있다. 심판이 하는 일은 딱 이것뿐이다:
//   "A 의 이번 락이 n 줄을 보냈다" → B.ts_queue_garbage(n)
// 여기에 승패 판정과 라운드 관리가 붙는다.
class Referee {
  constructor(sides, opts = {}) {
    this.sides = sides;                      // [{core, name, onAttack}, ...]
    this.seen = sides.map(() => 0);
    this.wins = sides.map(() => 0);
    this.bestOf = opts.bestOf ?? 3;
    this.onRound = opts.onRound || (() => {});
    this.over = false;
    this.sent = sides.map(() => 0);
  }
  // 매 고정 스텝마다 호출. C++ 은 락이 일어날 때마다 ST_EVENT 를 1 올린다.
  route() {
    for (let i = 0; i < this.sides.length; i++) {
      const s = V(this.sides[i].core).stats;
      if (s[ST.EVENT] === this.seen[i]) continue;
      this.seen[i] = s[ST.EVENT];
      const atk = s[ST.ATTACK];
      if (atk > 0) {
        this.sent[i] += atk;
        for (let j = 0; j < this.sides.length; j++)
          if (j !== i) this.sides[j].core.e.ts_queue_garbage(atk);
        if (this.sides[i].onAttack) this.sides[i].onAttack(atk);
      }
    }
    if (this.over) return;
    for (let i = 0; i < this.sides.length; i++) {
      if (V(this.sides[i].core).stats[ST.STATE] === 1) {
        this.over = true;
        const winner = 1 - i;                // 2인 대전 기준
        this.wins[winner]++;
        this.onRound(winner, this.wins.slice());
        return;
      }
    }
  }
  nextRound(seed) {
    this.over = false;
    this.seen = this.sides.map(() => 0);
    this.sent = this.sides.map(() => 0);
    for (const s of this.sides) s.core.e.ts_init(seed >>> 0);   // 같은 시드 = 같은 조각 순서 = 공평
  }
  reset() { this.wins = this.sides.map(() => 0); }
}

// === SECTION: view === 게임 뷰 — 판 하나를 그리고 조작을 받는다
class TetrisView {
  constructor(root, core, opts = {}) {
    this.root = root;
    this.core = core;
    this.driver = opts.driver || null;       // AiDriver 를 물리면 AI 가 논다
    this.manual = !!opts.manual;             // true = 바깥 루프가 step16/frame 을 부른다
    this.compact = !!opts.compact;           // 대전 화면용 축소 레이아웃
    this.name = opts.name || '';
    this.onEvent = opts.onEvent || (() => {});
    this.particles = []; this.popups = []; this.flash = null;
    this.lastEvent = 0; this.acc = 0; this.last = 0; this.running = false;
    this.autoRestart = !!opts.autoRestart;
    this.build();
    this.bindInput();
    this.resize();
    this.ro = new ResizeObserver(() => this.resize());
    this.ro.observe(this.root);
  }

  build() {
    const r = this.root;
    r.classList.add('tetris');
    if (this.compact) r.classList.add('compact');
    r.innerHTML = `
      <div class="t-side t-left">
        <div class="t-box"><div class="t-cap">HOLD</div><canvas class="t-hold"></canvas></div>
        <div class="t-stats">
          <div><b class="t-lines">0</b><span>LINES</span></div>
          <div><b class="t-atk">0</b><span>SENT</span></div>
        </div>
      </div>
      <div class="t-mid"><canvas class="t-board"></canvas><div class="t-over"></div></div>
      <div class="t-side t-right">
        <div class="t-box"><div class="t-cap">NEXT</div><canvas class="t-next"></canvas></div>
        <div class="t-badges"></div>
      </div>`;
    this.cv = r.querySelector('.t-board');
    this.cvN = r.querySelector('.t-next');
    this.cvH = r.querySelector('.t-hold');
    this.over = r.querySelector('.t-over');
    this.badges = r.querySelector('.t-badges');
    this.g = this.cv.getContext('2d');
    this.gN = this.cvN.getContext('2d');
    this.gH = this.cvH.getContext('2d');
    if (!this.driver) {
      r.insertAdjacentHTML('beforeend', `
        <div class="t-pad">
          <button data-act="4" aria-label="반시계 회전">⟲</button>
          <button data-act="0" aria-label="왼쪽">←</button>
          <button data-act="2" aria-label="소프트 드롭">↓</button>
          <button data-act="1" aria-label="오른쪽">→</button>
          <button data-act="3" aria-label="시계 회전">⟳</button>
          <button data-act="5" aria-label="하드 드롭" class="wide">⤓ DROP</button>
          <button data-act="6" aria-label="홀드">HOLD</button>
          <button data-act="7" aria-label="일시정지">❚❚</button>
        </div>`);
      r.tabIndex = 0;
    }
  }

  // === SECTION: input === 키보드 + 터치 버튼 + 스와이프
  bindInput() {
    if (this.driver) return;
    const KEYMAP = {
      ArrowLeft: ACT.LEFT, ArrowRight: ACT.RIGHT, ArrowDown: ACT.SOFT,
      ArrowUp: ACT.CW, KeyX: ACT.CW, KeyZ: ACT.CCW, ControlLeft: ACT.CCW,
      Space: ACT.HARD, ShiftLeft: ACT.HOLD, KeyC: ACT.HOLD,
      KeyA: ACT.FLIP, Escape: ACT.PAUSE, KeyP: ACT.PAUSE,
    };
    const held = new Set();
    this.root.addEventListener('keydown', (ev) => {
      const a = KEYMAP[ev.code];
      if (a === undefined) return;
      ev.preventDefault(); ev.stopPropagation();
      if (held.has(ev.code)) return;         // OS 키 리핏 무시 — DAS 는 wasm 이 관리
      held.add(ev.code);
      this.press(a);
    });
    this.root.addEventListener('keyup', (ev) => {
      const a = KEYMAP[ev.code];
      if (a === undefined) return;
      held.delete(ev.code);
      this.core.e.ts_release(a);
      ev.stopPropagation();
    });
    this.root.querySelectorAll('.t-pad button').forEach((b) => {
      const a = +b.dataset.act;
      const down = (ev) => { ev.preventDefault(); this.root.focus({ preventScroll: true }); this.press(a); b.classList.add('on'); };
      const up = (ev) => { ev.preventDefault(); this.core.e.ts_release(a); b.classList.remove('on'); };
      b.addEventListener('pointerdown', down);
      b.addEventListener('pointerup', up);
      b.addEventListener('pointercancel', up);
      b.addEventListener('pointerleave', up);
      b.addEventListener('contextmenu', (e) => e.preventDefault());
    });
    let sx = 0, sy = 0, tstart = 0, moved = 0, lastStep = 0;
    this.cv.addEventListener('pointerdown', (ev) => {
      this.root.focus({ preventScroll: true });
      sx = ev.clientX; sy = ev.clientY; tstart = performance.now(); moved = 0; lastStep = 0;
      this.cv.setPointerCapture(ev.pointerId);
    });
    this.cv.addEventListener('pointermove', (ev) => {
      const dx = ev.clientX - sx, dy = ev.clientY - sy;
      const step = Math.max(18, this.cell * 0.9);
      if (Math.abs(dx) > Math.abs(dy)) {
        const n = Math.trunc(dx / step);
        while (lastStep < n) { this.press(ACT.RIGHT); this.core.e.ts_release(ACT.RIGHT); lastStep++; moved = 1; }
        while (lastStep > n) { this.press(ACT.LEFT); this.core.e.ts_release(ACT.LEFT); lastStep--; moved = 1; }
      } else if (dy > step * 1.6) moved = 2;
    });
    this.cv.addEventListener('pointerup', (ev) => {
      const dt = performance.now() - tstart, dy = ev.clientY - sy, dx = ev.clientX - sx;
      if (moved === 2 && dy > 0) this.press(ACT.HARD);
      else if (!moved && dt < 260 && Math.abs(dx) < 12 && Math.abs(dy) < 12) this.press(ACT.CW);
      else if (dy < -this.cell * 1.5) this.press(ACT.HOLD);
    });
  }

  press(a) {
    this.core.e.ts_press(a);
    if (a === ACT.HARD || a === ACT.CW || a === ACT.CCW) this.haptic(8);
  }
  haptic(ms) { if (navigator.vibrate) try { navigator.vibrate(ms); } catch (_) {} }
  reinit(seed) {
    this.core.e.ts_init((seed ?? (Math.random() * 0xffffffff)) >>> 0);
    this.particles.length = 0; this.popups.length = 0;
    this.lastEvent = 0; this.sent = 0;
    if (this.driver) this.driver.reset();
  }

  // === SECTION: layout === 컨테이너 폭에 따라 3열 ↔ 세로 스택
  resize() {
    const r = this.root;
    const w = r.clientWidth || 320;
    const narrow = w < 460;
    const short = (window.innerHeight || 800) < 520;
    r.dataset.layout = narrow ? 'narrow' : 'wide';
    r.dataset.h = short ? 'short' : 'tall';
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const mid = r.querySelector('.t-mid');
    // 대전 화면은 판이 둘이므로 한 판이 쓸 수 있는 세로를 절반 가까이로 줄인다.
    const frac = this.compact ? (narrow ? 0.34 : 0.46) : (narrow ? 0.46 : 0.62);
    const availH = Math.max(140, Math.min(r.clientHeight || 9999, window.innerHeight * frac));
    const availW = mid.clientWidth || w;
    const cell = Math.max(6, Math.floor(Math.min(availW / this.core.W, availH / this.core.VIS)));
    if (this.cell === cell && this.narrow === narrow && this.short === short) { this.draw(); return; }
    this.short = short; this.cell = cell; this.narrow = narrow;
    const bw = cell * this.core.W, bh = cell * this.core.VIS;
    const half = Math.max(48, Math.floor(w / 2) - 18);
    const nextW = narrow ? Math.min(cell * 12, half) : cell * 4.2;
    const holdW = Math.min(cell * 4.2, half);
    for (const [cv, cw, ch] of [[this.cv, bw, bh],
                                [this.cvN, nextW, narrow ? cell * 3 : cell * (this.compact ? 8 : 12)],
                                [this.cvH, holdW, cell * 3]]) {
      cv.style.width = cw + 'px'; cv.style.height = ch + 'px';
      cv.width = Math.round(cw * dpr); cv.height = Math.round(ch * dpr);
      cv.getContext('2d').setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    this.draw();
  }

  // === SECTION: loop === 고정 타임스텝
  start() {
    if (this.running) return;
    this.running = true;
    this.last = performance.now();
    if (this.manual) return;                 // 바깥(BattleView)이 돌려 준다
    const loop = (now) => {
      if (!this.running) return;
      let dt = now - this.last; this.last = now;
      if (dt > 250) dt = 250;
      this.acc += dt;
      while (this.acc >= 16) { this.step16(); this.acc -= 16; }
      this.frame();
      this.raf = requestAnimationFrame(loop);
    };
    this.raf = requestAnimationFrame(loop);
  }
  stop() { this.running = false; if (this.raf) cancelAnimationFrame(this.raf); }

  step16() {
    this.core.e.ts_update(16);
    if (this.driver) this.driver.step(16);
  }
  frame() { this.pump(); this.draw(); }

  pump() {
    const s = V(this.core).stats;
    if (s[ST.EVENT] !== this.lastEvent) {
      this.lastEvent = s[ST.EVENT];
      if (s[ST.CLEAR] > 0) {
        this.flash = { rows: s[ST.ROWMASK], t: 0 };
        this.spawnParticles(s[ST.ROWMASK]);
        this.haptic(s[ST.CLEAR] === 4 ? 40 : 15);
      }
      if (s[ST.ATTACK] > 0) this.popups.push({ t: 0, text: '↗ ' + s[ST.ATTACK], sub: '보냄', color: '#f87171' });
      else if (s[ST.GAIN] > 0) {
        const label = s[ST.TSPIN] === 2 ? 'T-SPIN' : s[ST.TSPIN] === 1 ? 'T-SPIN MINI'
                    : s[ST.CLEAR] === 4 ? 'TETRIS' : ['', 'SINGLE', 'DOUBLE', 'TRIPLE'][s[ST.CLEAR]] || '';
        if (label) this.popups.push({ t: 0, text: label, sub: '', color: '#fbbf24' });
      }
      this.onEvent(s);
    }
    if (s[ST.STATE] === 1 && this.autoRestart) this.reinit();
  }

  spawnParticles(mask) {
    const cell = this.cell;
    for (let y = 0; y < this.core.VIS; y++) {
      if (!(mask & (1 << y))) continue;
      for (let x = 0; x < this.core.W; x++) for (let k = 0; k < 2; k++)
        this.particles.push({
          x: (x + 0.5) * cell, y: (y + 0.5) * cell,
          vx: (Math.random() - 0.5) * 3.2, vy: -Math.random() * 2.4 - 0.6,
          life: 1, c: COLORS[1 + ((x + y + k) % 7)],
        });
    }
    if (this.particles.length > 500) this.particles.splice(0, this.particles.length - 500);
  }

  // === SECTION: draw === 프레임 그리기
  draw() {
    const { g, cell } = this;
    const { cells, overlay, stats } = V(this.core);
    const W = this.core.W, VIS = this.core.VIS;
    const bw = cell * W, bh = cell * VIS;

    g.clearRect(0, 0, bw, bh);
    g.fillStyle = '#080e1a'; g.fillRect(0, 0, bw, bh);
    g.strokeStyle = 'rgba(120,160,220,0.10)'; g.lineWidth = 1;
    g.beginPath();
    for (let x = 1; x < W; x++) { g.moveTo(x * cell + 0.5, 0); g.lineTo(x * cell + 0.5, bh); }
    for (let y = 1; y < VIS; y++) { g.moveTo(0, y * cell + 0.5); g.lineTo(bw, y * cell + 0.5); }
    g.stroke();

    for (let y = 0; y < VIS; y++) for (let x = 0; x < W; x++) {
      const c = cells[y * W + x];
      if (c) drawMino(g, x * cell, y * cell, cell, COLORS[c], 'lock');
    }
    for (let y = 0; y < VIS; y++) for (let x = 0; x < W; x++) {
      const o = overlay[y * W + x];
      if (!o) continue;
      if (o >= 8) drawMino(g, x * cell, y * cell, cell, COLORS[o - 7], 'ghost');
      else drawMino(g, x * cell, y * cell, cell, COLORS[o], 'live');
    }

    const lp = stats[ST.LOCKPCT];
    if (lp > 0) {
      g.fillStyle = 'rgba(255,255,255,' + (0.12 + lp / 400) + ')';
      g.fillRect(0, bh - 3, bw * lp / 100, 3);
    }
    this.drawPending(stats[ST.PENDING], bw, bh);

    if (this.flash) {
      this.flash.t += 1;
      const a = Math.max(0, 1 - this.flash.t / 12);
      g.fillStyle = `rgba(255,255,255,${a * 0.85})`;
      for (let y = 0; y < VIS; y++) if (this.flash.rows & (1 << y)) g.fillRect(0, y * cell, bw, cell);
      if (this.flash.t > 12) this.flash = null;
    }
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx; p.y += p.vy; p.vy += 0.16; p.life -= 0.024;
      if (p.life <= 0) { this.particles.splice(i, 1); continue; }
      g.globalAlpha = Math.max(0, p.life);
      g.fillStyle = p.c;
      g.fillRect(p.x, p.y, Math.max(2, cell * 0.16), Math.max(2, cell * 0.16));
    }
    g.globalAlpha = 1;
    for (let i = this.popups.length - 1; i >= 0; i--) {
      const p = this.popups[i];
      p.t += 1;
      if (p.t > 55) { this.popups.splice(i, 1); continue; }
      g.globalAlpha = Math.max(0, 1 - p.t / 55);
      g.textAlign = 'center';
      g.fillStyle = p.color || '#fff';
      g.font = `800 ${Math.max(11, cell * 0.62)}px system-ui, sans-serif`;
      g.fillText(p.text, bw / 2, bh * 0.40 - p.t * 0.5);
      g.globalAlpha = 1;
    }
    this.drawPreviews();
    this.drawHUD(stats);
  }

  // 대기 중인 가비지 = 판 왼쪽 가장자리에 쌓이는 빨간 눈금.
  // 숫자로만 보여 주면 "언제 터지는지"가 안 보인다. 높이로 보여 준다.
  drawPending(n, bw, bh) {
    if (!n) return;
    const g = this.g, cell = this.cell, w = Math.max(3, cell * 0.22);
    const h = Math.min(bh, n * cell);
    const grad = g.createLinearGradient(0, bh - h, 0, bh);
    grad.addColorStop(0, '#fca5a5'); grad.addColorStop(1, '#dc2626');
    g.fillStyle = grad;
    g.fillRect(0, bh - h, w, h);
    g.fillStyle = '#fff';
    g.font = `800 ${Math.max(9, cell * 0.5)}px system-ui, sans-serif`;
    g.textAlign = 'left';
    g.fillText(String(n), w + 2, bh - h + Math.max(10, cell * 0.55));
  }

  drawPiece(g, piece, ox, oy, s) {
    const m = SHAPES[piece][0];
    let minx = 4, maxx = -1, miny = 4, maxy = -1;
    for (let i = 0; i < 16; i++) if (m & (1 << i)) {
      const x = i & 3, y = i >> 2;
      minx = Math.min(minx, x); maxx = Math.max(maxx, x);
      miny = Math.min(miny, y); maxy = Math.max(maxy, y);
    }
    const cx = ox - ((minx + maxx + 1) / 2) * s;
    const cy = oy - ((miny + maxy + 1) / 2) * s;
    for (let i = 0; i < 16; i++) if (m & (1 << i))
      drawMino(g, cx + (i & 3) * s, cy + (i >> 2) * s, s, COLORS[piece + 1], 'live');
  }

  drawPreviews() {
    const s = V(this.core).stats;
    const dpr = Math.min(2, devicePixelRatio || 1);
    const cell = this.cell, ps = cell * 0.62;
    const n = this.compact ? 3 : 5;
    const gn = this.gN, cw = this.cvN.width / dpr, ch = this.cvN.height / dpr;
    gn.clearRect(0, 0, cw, ch);
    for (let i = 0; i < n; i++) {
      const p = s[ST.NEXT0 + i];
      if (p < 0) continue;
      if (this.narrow) this.drawPiece(gn, p, (i + 0.5) * (cw / n), ch / 2, ps);
      else this.drawPiece(gn, p, cw / 2, (i + 0.5) * (ch / n), ps);
    }
    const gh = this.gH, hw = this.cvH.width / dpr, hh = this.cvH.height / dpr;
    gh.clearRect(0, 0, hw, hh);
    if (s[ST.HOLD] >= 0) this.drawPiece(gh, s[ST.HOLD], hw / 2, hh / 2, ps);
  }

  drawHUD(s) {
    const r = this.root;
    const set = (sel, v) => { const el = r.querySelector(sel); if (el && el.textContent !== String(v)) el.textContent = v; };
    set('.t-lines', s[ST.LINES]);
    set('.t-atk', this.sent || 0);
    let b = '';
    if (s[ST.COMBO] > 0) b += `<span class="bd combo">COMBO ${s[ST.COMBO]}</span>`;
    if (s[ST.B2B]) b += `<span class="bd b2b">B2B</span>`;
    if (s[ST.PENDING] > 0) b += `<span class="bd gb">가비지 ${s[ST.PENDING]}</span>`;
    if (this.badges.innerHTML !== b) this.badges.innerHTML = b;
    const state = s[ST.STATE];
    const html = state === 1
      ? `<div class="t-msg"><b>GAME OVER</b><span>${s[ST.LINES]}줄 · 보낸 ${this.sent || 0}줄</span></div>`
      : state === 2 ? `<div class="t-msg"><b>PAUSED</b><em>❚❚ 또는 P</em></div>` : '';
    if (this.over.innerHTML !== html) this.over.innerHTML = html;
  }
}

// === SECTION: battle === 대전 화면 — 인스턴스 두 개를 한 루프에서
// 두 판을 각자의 requestAnimationFrame 으로 돌리면 프레임이 어긋나 "같은 시간"이
// 성립하지 않는다. 루프는 하나, 그 안에서 두 코어를 같은 dt 로 전진시킨다.
class BattleView {
  constructor(root, cores, opts = {}) {
    this.root = root;
    this.bestOf = opts.bestOf ?? 3;
    this.seedBase = opts.seed ?? ((Math.random() * 0xffffffff) >>> 0);
    this.round = 0;
    root.classList.add('battle');
    root.innerHTML = `
      <div class="bat-col"><div class="bat-name p1"></div><div class="bat-host"></div></div>
      <div class="bat-col"><div class="bat-name p2"></div><div class="bat-host"></div></div>
      <div class="bat-bar"><span class="bat-msg"></span><button class="bat-btn">다시</button></div>`;
    const hosts = root.querySelectorAll('.bat-host');
    this.views = cores.map((core, i) => new TetrisView(hosts[i], core, {
      manual: true, compact: true,
      driver: opts.drivers[i] || null,
      name: opts.names[i],
    }));
    this.views.forEach((v, i) => { v.sent = 0; });
    this.ref = new Referee(cores.map((core, i) => ({
      core, name: opts.names[i],
      onAttack: (n) => { this.views[i].sent = (this.views[i].sent || 0) + n; },
    })), {
      bestOf: this.bestOf,
      onRound: (w, wins) => this.endRound(w, wins),
    });
    this.names = opts.names;
    this.msg = root.querySelector('.bat-msg');
    root.querySelector('.bat-btn').onclick = () => this.newMatch();
    this.paintNames();
    this.newMatch();
  }
  paintNames(wins = [0, 0]) {
    const [a, b] = this.root.querySelectorAll('.bat-name');
    a.textContent = `${this.names[0]}  ${wins[0]}`;
    b.textContent = `${wins[1]}  ${this.names[1]}`;
  }
  newMatch() {
    this.ref.reset();
    this.round = 0;
    this.paintNames();
    this.startRound();
  }
  startRound() {
    this.round++;
    // 같은 시드로 두 판을 초기화한다 = 두 사람이 완전히 같은 조각 순서를 받는다.
    // 대전에서 공평함은 규칙이 아니라 이 한 줄이 만든다.
    const seed = (this.seedBase + this.round * 7919) >>> 0;
    this.ref.nextRound(seed);
    this.views.forEach((v) => { v.sent = 0; v.lastEvent = 0; v.particles.length = 0; v.popups.length = 0; if (v.driver) v.driver.reset(); });
    this.msg.textContent = `라운드 ${this.round}`;
    this.waiting = 0;
  }
  endRound(winner, wins) {
    this.paintNames(wins);
    const need = Math.floor(this.bestOf / 2) + 1;
    if (wins[winner] >= need) { this.msg.textContent = `${this.names[winner]} 승리! (${wins[0]}-${wins[1]})`; this.done = true; }
    else { this.msg.textContent = `${this.names[winner]} 라운드 획득`; this.waiting = 1400; }
  }
  start() {
    if (this.running) return;
    this.running = true;
    this.last = performance.now();
    this.acc = 0;
    const loop = (now) => {
      if (!this.running) return;
      let dt = now - this.last; this.last = now;
      if (dt > 250) dt = 250;
      this.acc += dt;
      while (this.acc >= 16) {
        if (!this.ref.over) { for (const v of this.views) v.step16(); this.ref.route(); }
        else if (this.waiting > 0) { this.waiting -= 16; if (this.waiting <= 0 && !this.done) this.startRound(); }
        this.acc -= 16;
      }
      for (const v of this.views) v.frame();
      this.raf = requestAnimationFrame(loop);
    };
    this.raf = requestAnimationFrame(loop);
  }
  stop() { this.running = false; if (this.raf) cancelAnimationFrame(this.raf); }
}

// === SECTION: mount === 슬라이드의 data-demo 를 실제 데모로 바꾼다
// 난이도 = (학습 세대, 생각 시간, 손 속도, 실수 확률) 네 개의 조합.
// 규칙을 봐주는 대신 "덜 배웠고, 느리고, 가끔 틀린다"로 약하게 만든다.
const LEVELS = {
  easy:   { label: '쉬움 (1세대)',   thinkMs: 520, moveMs: 110, blunder: 0.22 },
  normal: { label: '보통 (5세대)',   thinkMs: 380, moveMs: 80,  blunder: 0.10 },
  hard:   { label: '어려움 (15세대)', thinkMs: 260, moveMs: 55,  blunder: 0.03 },
  max:    { label: '최종 (50세대)',   thinkMs: 150, moveMs: 32,  blunder: 0 },
};
function levelOpts(key) {
  const L = LEVELS[key] || LEVELS.hard;
  return { thinkMs: L.thinkMs, moveMs: L.moveMs, blunder: L.blunder, weights: GA_WEIGHTS.levels[key] };
}

const DEMO_MOUNTS = {};

// 혼자 노는 AI 한 판 — 탐색·평가 슬라이드에서 쓴다
DEMO_MOUNTS['ai'] = async (host) => {
  const core = await loadCore(WASM_B64, (Math.random() * 0xffffffff) >>> 0);
  const lv = host.dataset.level || 'max';
  const view = new TetrisView(host, core, {
    driver: new AiDriver(core, levelOpts(lv)), autoRestart: true,
  });
  view.sent = 0;
  view.onEvent = (s) => { if (s[ST.ATTACK] > 0) view.sent += s[ST.ATTACK]; };
  return view;
};

// 사람이 직접 두는 한 판
DEMO_MOUNTS['solo'] = async (host) => {
  const core = await loadCore(WASM_B64, (Math.random() * 0xffffffff) >>> 0);
  const view = new TetrisView(host, core, {});
  view.sent = 0;
  view.onEvent = (s) => { if (s[ST.ATTACK] > 0) view.sent += s[ST.ATTACK]; };
  return view;
};

// AI vs AI 관전 — 표지와 대전 슬라이드
DEMO_MOUNTS['battle-ai'] = async (host) => {
  const seed = (Math.random() * 0xffffffff) >>> 0;
  const a = await loadCore(WASM_B64, seed), b = await loadCore(WASM_B64, seed);
  const la = host.dataset.left || 'normal', lb = host.dataset.right || 'max';
  return new BattleView(host, [a, b], {
    drivers: [new AiDriver(a, levelOpts(la)), new AiDriver(b, levelOpts(lb))],
    names: [LEVELS[la].label, LEVELS[lb].label],
    bestOf: +(host.dataset.bestof || 3),
  });
};

// 사람 vs AI — 난이도 선택 붙음
DEMO_MOUNTS['battle-human'] = async (host) => {
  const wrap = document.createElement('div');
  const bar = document.createElement('div');
  bar.className = 'aibar';
  bar.innerHTML = '<span>AI 난이도</span>' +
    Object.keys(LEVELS).map((k, i) =>
      `<button data-lv="${k}"${k === 'hard' ? ' class="on"' : ''}>${LEVELS[k].label}</button>`).join('');
  host.appendChild(bar);
  host.appendChild(wrap);

  const seed = (Math.random() * 0xffffffff) >>> 0;
  const a = await loadCore(WASM_B64, seed), b = await loadCore(WASM_B64, seed);
  const driver = new AiDriver(b, levelOpts('hard'));
  const bv = new BattleView(wrap, [a, b], {
    drivers: [null, driver], names: ['당신', 'AI'], bestOf: 3,
  });
  bar.addEventListener('click', (ev) => {
    const btn = ev.target.closest('button[data-lv]');
    if (!btn) return;
    bar.querySelectorAll('button').forEach((x) => x.classList.remove('on'));
    btn.classList.add('on');
    driver.configure(levelOpts(btn.dataset.lv));
    bv.names[1] = 'AI · ' + LEVELS[btn.dataset.lv].label;
    bv.paintNames(bv.ref.wins);
  });
  return bv;
};

// 특징 8개를 실시간으로 읽어 보여 준다 — "AI 는 판을 이렇게 본다"
DEMO_MOUNTS['features'] = async (host) => {
  const board = document.createElement('div');
  const panel = document.createElement('div');
  panel.className = 'featpanel';
  host.appendChild(board);
  host.appendChild(panel);
  const core = await loadCore(WASM_B64, (Math.random() * 0xffffffff) >>> 0);
  setWeights(core, GA_WEIGHTS.best);
  const view = new TetrisView(board, core, {
    driver: host.dataset.hand ? null : new AiDriver(core, levelOpts('max')),
    autoRestart: true, compact: true,
  });
  view.sent = 0;
  panel.innerHTML = FEAT_KO.map((n, i) =>
    `<div class="frow"><span>${n}</span><b data-f="${i}">0</b><em data-w="${i}">0</em></div>`).join('') +
    '<div class="frow tot"><span>점수 Σ wᵢ·fᵢ</span><b data-score>0</b><em></em></div>';
  const bs = panel.querySelectorAll('[data-f]'), ws = panel.querySelectorAll('[data-w]');
  const scoreEl = panel.querySelector('[data-score]');
  GA_WEIGHTS.best.forEach((w, i) => { ws[i].textContent = (w >= 0 ? '+' : '') + w.toFixed(3); ws[i].className = w >= 0 ? 'pos' : 'neg'; });
  const oldFrame = view.frame.bind(view);
  view.frame = () => {
    oldFrame();
    const sc = core.e.ai_eval_here();
    const f = V(core).features;
    for (let i = 0; i < 8; i++) bs[i].textContent = f[i].toFixed(0);
    scoreEl.textContent = sc.toFixed(2);
  };
  return view;
};

// 학습 로그를 그대로 그린 수렴 그래프 (실제 실행 결과)
DEMO_MOUNTS['gachart'] = async (host) => {
  const cv = document.createElement('canvas');
  cv.className = 'gachart';
  host.appendChild(cv);
  const draw = () => drawGaChart(cv, GA_LOG, GA_LOG.length);
  const ro = new ResizeObserver(draw);
  ro.observe(host);
  draw();
  return { start: draw, stop: () => {} };
};

// 세대별 best/mean 을 선 두 개로. 캔버스에 직접 그린다 — 라이브러리 0개.
function drawGaChart(cv, log, upto) {
  const dpr = Math.min(2, devicePixelRatio || 1);
  // 폭은 부모에게서 받는다. 캔버스 자신의 clientWidth 를 쓰면 우리가 방금 style.width 로
  // 고정한 값을 다시 읽게 되어 다시는 줄어들지 못한다.
  const parent = cv.parentElement;
  const w = Math.max(220, (parent && parent.clientWidth) || cv.clientWidth || 320);
  const h = Math.max(140, Math.min(300, w * 0.5));
  cv.style.width = w + 'px'; cv.style.height = h + 'px';
  cv.width = w * dpr; cv.height = h * dpr;
  const g = cv.getContext('2d');
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, w, h);
  const n = Math.max(2, upto);
  const pad = { l: 34, r: 8, t: 10, b: 20 };
  const maxY = Math.max(10, ...log.slice(0, n).map((r) => r.best)) * 1.1;
  const X = (i) => pad.l + (w - pad.l - pad.r) * (i / (log.length - 1 || 1));
  const Y = (v) => h - pad.b - (h - pad.t - pad.b) * (v / maxY);
  g.strokeStyle = 'rgba(120,170,255,.18)'; g.lineWidth = 1;
  g.beginPath();
  for (let k = 0; k <= 4; k++) { const y = pad.t + (h - pad.t - pad.b) * k / 4; g.moveTo(pad.l, y); g.lineTo(w - pad.r, y); }
  g.stroke();
  g.fillStyle = '#64748b'; g.font = '10px ui-monospace, monospace'; g.textAlign = 'right';
  for (let k = 0; k <= 4; k++) {
    const v = maxY * (1 - k / 4), y = pad.t + (h - pad.t - pad.b) * k / 4;
    g.fillText(v.toFixed(0), pad.l - 4, y + 3);
  }
  for (const [key, color] of [['mean', '#a855f7'], ['best', '#22d3ee']]) {
    g.strokeStyle = color; g.lineWidth = 2; g.beginPath();
    for (let i = 0; i < n; i++) { const x = X(i), y = Y(log[i][key]); i ? g.lineTo(x, y) : g.moveTo(x, y); }
    g.stroke();
  }
  g.textAlign = 'left'; g.fillStyle = '#22d3ee'; g.fillText('최고', pad.l + 4, pad.t + 10);
  g.fillStyle = '#a855f7'; g.fillText('평균', pad.l + 34, pad.t + 10);
  g.fillStyle = '#64748b'; g.textAlign = 'center';
  g.fillText('세대 ' + n, w / 2, h - 5);
}

window.__mountDemo = async function (host) {
  const kind = host.dataset.demo || 'solo';
  const fn = DEMO_MOUNTS[kind];
  if (!fn) throw new Error('알 수 없는 데모: ' + kind);
  const v = await fn(host);
  return v;
};

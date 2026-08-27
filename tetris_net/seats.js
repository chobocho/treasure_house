// seats.js — 좌석 하나를 조종하는 세 가지 방법: 키보드 · 게임패드 · GA AI.
//
// 서버는 이 셋을 구분하지 않는다(protocol.md §3). 좌석에 붙는 조종자가 무엇이든
// 나가는 메시지는 atk/st/ko 뿐이다. 그래서 AI 좌석을 사람 좌석과 똑같이 다룰 수 있고,
// "8인 방에 사람 3명 + AI 5명"이 특별한 코드 없이 성립한다.
//
// PC 1대에 사람 2명이 앉는 것도 여기서 끝난다 — 키맵 두 벌, 게임패드 두 개.

const KEYMAP_P1 = {
  ArrowLeft: ACT.LEFT, ArrowRight: ACT.RIGHT, ArrowDown: ACT.SOFT,
  ArrowUp: ACT.CW, KeyZ: ACT.CCW, KeyX: ACT.CW, KeyC: ACT.HOLD,
  Space: ACT.HARD, ShiftLeft: ACT.HOLD, KeyV: ACT.FLIP,
};
// 2P 는 왼손만으로 다 되게 모았다. 1P 키와 하나도 겹치지 않는다 — 겹치면
// 한 사람의 입력이 두 판에 동시에 들어간다(직접 겪어 보기 전에는 안 믿긴다).
const KEYMAP_P2 = {
  KeyA: ACT.LEFT, KeyD: ACT.RIGHT, KeyS: ACT.SOFT,
  KeyW: ACT.CW, KeyQ: ACT.CCW, KeyE: ACT.HOLD, KeyF: ACT.HARD, KeyR: ACT.FLIP,
};

// 표준 게임패드 배치(Standard Gamepad). 버튼 번호는 규격에 박혀 있다.
const PAD_MAP = {
  14: ACT.LEFT, 15: ACT.RIGHT, 13: ACT.SOFT, 12: ACT.HARD,
  0: ACT.CW, 1: ACT.CCW, 2: ACT.HOLD, 3: ACT.FLIP, 5: ACT.HARD, 4: ACT.HOLD,
};

// 좌석 하나 = 코어 하나 + 조종자 하나. 대전의 최소 단위다.
class Seat {
  constructor(index, core, kind, name, lv) {
    this.i = index; this.core = core; this.kind = kind; this.name = name; this.lv = lv || '';
    this.alive = true; this.place = 0;
    this.think = 0; this.thinkMs = 0;
    this.local = true;
  }
}

// ── 키보드 ───────────────────────────────────────────────────────────
// 한 PC 의 두 좌석을 한 리스너가 나눠 맡는다. 덱 안에서 돌 때를 대비해
// 이벤트를 여기서 멈춘다 — 안 그러면 ← → 가 슬라이드를 넘겨 버린다.
class LocalKeys {
  constructor(root) {
    this.root = root;
    this.slots = [null, null];          // slots[0] = 1P 좌석, slots[1] = 2P 좌석
    root.tabIndex = 0;
    this.onDown = (ev) => this.dispatch(ev, true);
    this.onUp = (ev) => this.dispatch(ev, false);
    root.addEventListener('keydown', this.onDown);
    root.addEventListener('keyup', this.onUp);
    root.addEventListener('pointerdown', () => root.focus({ preventScroll: true }));
  }
  bind(slot, seat) { this.slots[slot] = seat; }
  dispatch(ev, down) {
    const maps = [KEYMAP_P1, KEYMAP_P2];
    let used = false;
    for (let k = 0; k < 2; k++) {
      const seat = this.slots[k];
      if (!seat || !seat.alive) continue;
      const a = maps[k][ev.code];
      if (a === undefined) continue;
      used = true;
      if (down) { if (!ev.repeat) seat.core.e.ng_press(a); }
      else seat.core.e.ng_release(a);
      seat.core.refresh();
    }
    if (used) { ev.preventDefault(); ev.stopPropagation(); }
  }
  detach() {
    this.root.removeEventListener('keydown', this.onDown);
    this.root.removeEventListener('keyup', this.onUp);
  }
}

// ── 게임패드 ─────────────────────────────────────────────────────────
// 브라우저는 패드 상태를 이벤트로 주지 않는다. 매 프레임 훑어서 직접 엣지를 잡아야 한다.
class Pads {
  constructor() { this.prev = [[], []]; this.slots = [null, null]; }
  bind(slot, seat) { this.slots[slot] = seat; }
  poll() {
    if (!navigator.getGamepads) return;
    const pads = navigator.getGamepads();
    for (let k = 0; k < 2; k++) {
      const seat = this.slots[k], pad = pads[k];
      if (!seat || !seat.alive || !pad) continue;
      const now = [];
      for (const b in PAD_MAP) now[b] = pad.buttons[b] && pad.buttons[b].pressed;
      // 아날로그 스틱도 좌우로 친다. 임계값 0.5 — 더 낮추면 손을 떼도 계속 움직인다.
      const ax = pad.axes[0] || 0;
      if (ax < -0.5) now[14] = true;
      if (ax > 0.5) now[15] = true;
      for (const b in PAD_MAP) {
        const a = PAD_MAP[b];
        if (now[b] && !this.prev[k][b]) seat.core.e.ng_press(a);
        else if (!now[b] && this.prev[k][b]) seat.core.e.ng_release(a);
      }
      this.prev[k] = now;
      seat.core.refresh();
    }
  }
}

// ── AI ───────────────────────────────────────────────────────────────
// 2편에서 유전 알고리즘으로 학습시킨 가중치를 그대로 쓴다. 여기서 새로 만든 숫자가 없다.
// 난이도는 두 축이다: 어떤 가중치를 쓰나(판단력) + 몇 ms 마다 한 수를 두나(속도).
const AI_LEVELS = {
  easy:   { ms: 520, ko: '초보' },
  normal: { ms: 300, ko: '보통' },
  hard:   { ms: 180, ko: '고수' },
  max:    { ms: 110, ko: '최강' },
};

function makeAiSeat(seat, level, weightTable) {
  const lv = AI_LEVELS[level] ? level : 'hard';
  seat.lv = lv;
  seat.thinkMs = AI_LEVELS[lv].ms;
  seat.core.views.weights.set(Float32Array.from(weightTable[lv]));
  return seat;
}

// AI 좌석을 한 프레임 밀어 준다. 사람 좌석은 키/패드가 대신 이 일을 한다.
function stepAi(seat, dt) {
  if (!seat.thinkMs || !seat.alive) return;
  seat.think += dt;
  if (seat.think < seat.thinkMs) return;
  seat.think = 0;
  if (seat.core.views.stats[ST.STATE] === STATE.PLAY) {
    seat.core.e.ng_step();
    seat.core.refresh();
  }
}

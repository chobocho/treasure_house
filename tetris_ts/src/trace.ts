// trace.ts — "TS 코어가 C++ wasm 코어와 정말 같은가"를 재는 자.
//
// 핵심 아이디어: **비교할 두 구현이 같은 러너를 공유한다.**
// 시나리오(어떤 키를 언제 누르고 dt 를 얼마나 흘릴지)를 wasm 쪽 도구와 TS 쪽 테스트가
// 따로 구현하면, 서로 다른 시나리오를 돌려 놓고 "결과가 다르네" 하고 헤매게 된다.
// 그래서 시나리오 생성과 실행 루프를 여기 한 번만 쓰고, 두 구현은 어댑터만 제공한다.
// 도구(tools/trace_wasm.mjs)는 이 파일의 컴파일 결과를 그대로 import 한다.
//
// 트레이스는 두 종류다:
//   1) 플레이 트레이스 — 조각 단위 계획(회전→이동→낙하)으로 실제 게임을 길게 돌린다.
//      무작위 키 난타는 8조각 만에 죽어서 줄 지우기·콤보·B2B 를 한 번도 못 밟는다.
//   2) 배치 트레이스 — 판을 심어 놓고 짧은 입력 단어를 전수로 넣는다.
//      SRS 킥의 구석과 T스핀 판정처럼 "우연히 걸리기를 기다릴 수 없는" 것들을 겨냥한다.

import { boardHash, ST, STATE, ACT, W, H, GARBAGE, SPAWN_X } from './core.js';

/** 코어 하나를 조작하는 최소 인터페이스. wasm 인스턴스와 Tetris 인스턴스가 각각 구현한다. */
export interface TraceTarget {
  init(seed: number): void;
  press(act: number): void;
  release(act: number): void;
  update(dtMs: number): void;
  queueGarbage(n: number): void;
  /** 굳은 블록 배열 (H*W). 호출할 때마다 최신이어야 한다. */
  board(): Uint8Array;
  /** 숫자 상태 배열 (ST.COUNT). */
  stats(): Int32Array;
}

/** 한 스텝에 일어나는 일. -1 은 "아무것도 안 함". */
export interface TraceStep {
  act: number;
  rel: number;
  dtMs: number;
  garbage: number;
}

/** 트레이스에 쓰는 시드들. 뒤의 둘은 경계값 — 0 은 코어가 기본 시드로 바꿔야 하고,
 *  0xFFFFFFFF 는 xorshift 의 u32 경계를 밟는다. */
export const TRACE_SEEDS: readonly number[] = [1, 2, 12345, 0x9e3779b9, 0, 0xffffffff];
export const TRACE_STEPS = 1500;
/** 이 간격마다 stats 전체를 스냅샷으로 남긴다 — 해시가 어긋났을 때 어디가 다른지 보려고. */
export const SNAP_EVERY = 100;

/** 시나리오 생성용 난수. 게임 RNG 와 **다른** 수열이어야 한다.
 *  같은 수열을 쓰면 "RNG 가 틀렸는데 시나리오도 같이 틀려서 결과가 맞아 보이는" 상황이 생긴다. */
function scriptRng(seed: number): () => number {
  let s = (seed ^ 0x5bf03635) >>> 0;
  if (s === 0) s = 0x1234567;
  return () => {
    s ^= s << 7; s >>>= 0;
    s ^= s >>> 9;
    s ^= s << 8; s >>>= 0;
    return s;
  };
}

/** 판에서 가장 낮은 열(동률이면 왼쪽)의 x.
 *  판 배열만 보고 정하므로 두 구현이 같은 판 위에서 반드시 같은 답을 낸다. */
export function lowestColumn(b: Uint8Array): number {
  let best = 0;
  let bestH = H + 1;
  for (let x = 0; x < W; x++) {
    let y = 0;
    while (y < H && !b[y * W + x]) y++;
    const h = H - y;
    if (h < bestH) { bestH = h; best = x; }
  }
  return best;
}

/**
 * 조각 하나를 어떻게 둘지에 대한 계획을 스텝 목록으로 펼친다.
 *
 *   (가끔) 홀드 → 회전 0~3회 → 목표 열까지 이동 → (가끔) DAS·소프트드롭 →
 *   하드드롭 또는 자연 낙하 → 잠깐 쉼
 *
 * 목표 열은 호출자가 **현재 판을 보고** 정해서 넘긴다. 무작위로 고르면 조각이
 * 한곳에 쌓여 17조각 만에 죽고, 그러면 줄 지우기·콤보·B2B·레벨업이 트레이스에
 * 한 번도 안 들어온다 (실제로 그랬다). 낮은 열로 보내면 판이 평평해져서
 * 줄이 지워지고 게임이 길어진다.
 */
export function planPiece(r: () => number, targetX: number): TraceStep[] {
  const out: TraceStep[] = [];
  const push = (act: number, rel: number, dtMs: number, garbage = 0): void => {
    out.push({ act, rel, dtMs, garbage });
  };

  if (r() % 9 === 0) push(ACT.HOLD, -1, 2);

  const rots = r() % 4;
  for (let k = 0; k < rots; k++) push(r() % 5 === 0 ? ACT.CCW : ACT.CW, -1, 2);
  if (r() % 13 === 0) push(ACT.FLIP, -1, 2);

  // 스폰 x 는 3. 목표 열에 조각의 왼쪽 끝을 맞춘다 (벽에 막히면 코어가 알아서 멈춘다).
  const dx = targetX - 1 - SPAWN_X;
  const dir = dx < 0 ? ACT.LEFT : ACT.RIGHT;
  for (let k = 0; k < Math.abs(dx); k++) push(dir, dir, 3); // 눌렀다 떼기 — DAS 폭주 방지

  // 가끔은 DAS 를 진짜로 돌린다: 누른 채로 200ms 를 흘린 뒤 뗀다
  if (r() % 9 === 0) { push(dir, -1, 100); push(-1, -1, 100); push(-1, dir, 60); }
  // 가끔은 소프트드롭으로 가라앉힌다 — 회전 뒤에 가라앉히면 스핀이 나온다
  if (r() % 5 === 0) { push(ACT.SOFT, -1, 100); push(-1, ACT.SOFT, 20); }

  if (r() % 11 === 0) {
    // 자연 낙하 + 락다운 유예 경로. 하드드롭만 쓰면 이 코드가 트레이스에 안 들어온다.
    for (let k = 0; k < 12; k++) push(-1, -1, 100);
  } else {
    push(ACT.HARD, -1, 5);
  }

  // 가비지는 드물게. 자주 넣으면 판이 금방 천장에 닿아 게임이 짧아진다.
  const garb = r() % 45 === 0 ? 1 + (r() % 4) : 0;
  push(-1, -1, 1 + (r() % 30), garb);
  return out;
}

/** 시드 하나의 트레이스 결과. */
export interface TraceResult {
  seed: number;
  steps: number;
  /** 스텝마다의 보드 해시 */
  bh: number[];
  /** 스텝마다의 stats 해시 */
  sh: number[];
  /** SNAP_EVERY 마다, 그리고 마지막 스텝의 stats 전체 */
  snaps: { i: number; stats: number[] }[];
  /** 진행 중 게임오버로 재시작한 횟수 — 시나리오가 실제로 판을 죽였는지 확인용 */
  restarts: number;
}

/** Int32Array 를 32비트 해시 하나로. board 해시와 같은 FNV-1a 를 바이트 단위로 돌린다. */
export function statsHash(s: Int32Array): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    let v = s[i] as number;
    for (let b = 0; b < 4; b++) {
      h ^= v & 0xff;
      h = Math.imul(h, 16777619) >>> 0;
      v >>= 8;
    }
  }
  return h;
}

/**
 * 시나리오를 끝까지 돌리고 스텝마다 해시를 남긴다.
 *
 * 게임오버가 나면 그 자리에서 파생 시드로 재시작한다. 그러지 않으면 트레이스의
 * 뒷부분이 전부 "아무 일도 안 일어남"이 되어 검증력이 사라진다.
 * 재시작 시드는 원래 시드와 스텝 인덱스만으로 정해지므로 두 구현이 반드시 같은
 * 지점에서 같은 시드로 다시 시작한다.
 */
export function runTrace(t: TraceTarget, seed: number, steps: number = TRACE_STEPS): TraceResult {
  const r = scriptRng(seed);
  t.init(seed);
  const bh: number[] = [];
  const sh: number[] = [];
  const snaps: { i: number; stats: number[] }[] = [];
  let restarts = 0;
  let queue: TraceStep[] = [];

  for (let i = 0; i < steps; i++) {
    // 계획이 떨어지면 지금 판을 보고 새로 세운다. 시나리오가 판에 반응하므로,
    // 어느 한쪽이 판을 다르게 만들면 그다음 입력까지 갈라져서 차이가 증폭된다.
    if (queue.length === 0) queue = planPiece(r, lowestColumn(t.board()));
    const st = queue.shift() as TraceStep;
    if (st.garbage > 0) t.queueGarbage(st.garbage);
    if (st.act >= 0) t.press(st.act);
    if (st.rel >= 0) t.release(st.rel);
    t.update(st.dtMs);

    if ((t.stats()[ST.STATE] as number) === STATE.OVER) {
      restarts++;
      t.init((((seed + i * 2654435761) >>> 0) ^ 0x85ebca6b) >>> 0);
      queue = []; // 새 판에는 새 계획
    }

    bh.push(boardHash(t.board()));
    sh.push(statsHash(t.stats()));
    if (i % SNAP_EVERY === 0 || i === steps - 1) {
      snaps.push({ i, stats: Array.from(t.stats()) });
    }
  }
  return { seed, steps, bh, sh, snaps, restarts };
}

// ── 2부: 배치 트레이스 (킥·T스핀·점수의 정면 대조) ────────────────────

/** 문자열 그림 → board 배열. 한 줄이 W 글자, '.' 은 빈칸, '#' 은 가비지, 그 외는 채운 칸.
 *  그림의 마지막 줄이 필드의 바닥줄에 놓인다. wasm 의 보드에도 그대로 쓴다. */
export function paintBoard(b: Uint8Array, rows: readonly string[], fill = 1): void {
  b.fill(0);
  for (let i = 0; i < rows.length; i++) {
    const y = H - rows.length + i;
    const row = rows[i] as string;
    for (let x = 0; x < W; x++) {
      const c = row[x];
      b[y * W + x] = c && c !== '.' ? (c === '#' ? GARBAGE : fill) : 0;
    }
  }
}

/** 같은 줄을 n 번 반복 — 판 그림을 짧게 쓰려고. */
function rep(row: string, n: number): string[] {
  return Array.from({ length: n }, () => row);
}

/**
 * 배치 트레이스에 쓰는 판 5종. 각각 다른 종류의 함정을 담고 있다.
 *
 * 1번 판이 이 트레이스의 핵심이다. T스핀 더블 자리를 **스폰 높이 근처**에 만들어 뒀다.
 * 바닥에 만들면 조각이 15칸을 내려가야 하는데, 그동안 락다운 타이머가 돌아
 * "회전할 기회"가 사라진다. 함정을 위로 올려야 스핀이 실제로 성립한다.
 */
export const BOARDS: readonly (readonly string[])[] = [
  // 0) 빈 판 — 스폰·기본 회전·바닥 킥
  [],
  // 1) T스핀 더블 자리: 오버행 2개(x=2,5) + 3칸 방 + 1칸 노치(x=4)
  ['..#..#....', '###...####', '####.#####', ...rep('#########.', 15)],
  // 2) 계단 — 벽킥과 끼워넣기가 많이 나온다
  [
    '#.........', '##........', '###.......', '####......',
    '#####.....', '######....', '#######...', '########..',
  ],
  // 3) 이미 꽉 찬 줄이 섞인 판 — 락 순간의 줄 지우기 경로
  ['##########', ...rep('#########.', 4)],
  // 4) 왼쪽 1칸 우물 — I 를 세워 꽂으면 테트리스, B2B 가 붙는다
  rep('.#########', 12),
];

/** 배치 트레이스의 연산 하나: 키를 누르거나(press), 시간을 흘리거나(wait). */
export type PlaceOp = { press: number } | { wait: number };

/** 배치 트레이스가 조작할 수 있어야 하는 것들. */
export interface PlaceTarget {
  init(seed: number): void;
  /** 굳은 블록 배열을 직접 덮어쓴다 (paintBoard 로). */
  paint(rows: readonly string[]): void;
  setPiece(piece: number): void;
  press(act: number): void;
  update(dtMs: number): void;
  board(): Uint8Array;
  stats(): Int32Array;
}

/**
 * 손으로 짠 "스핀 단어" — 소프트드롭으로 가라앉힌 뒤 회전해서 킥으로 밀어 넣는다.
 *
 * 왜 손으로 짜는가: 무작위 단어 48개로는 T스핀이 한 번도 안 나온다(실제로 0회였다).
 * T스핀은 "가라앉힌 다음 회전"이라는 순서가 반드시 필요한데, 무작위 단어에는
 * 시간을 흘리는 연산 자체가 없기 때문이다.
 *
 * 1번 판 + T조각 + 첫 단어가 정식 T스핀 더블이 되도록 킥 표를 따라가며 맞췄다:
 *   CW(rot1) → LEFT → 소프트드롭 1칸 → CW 에서 k=0,1 이 막히고 k=2 {+1,-1} 이
 *   조각을 오른쪽 아래로 밀어 노치에 앉힌다 → 앞 코너 2개 + 뒤 1개 = 정식.
 */
export const SPIN_WORDS: readonly PlaceOp[][] = [
  [{ press: ACT.CW }, { press: ACT.LEFT }, { press: ACT.SOFT }, { wait: 100 }, { press: ACT.CW }, { press: ACT.HARD }],
  [{ press: ACT.CCW }, { press: ACT.RIGHT }, { press: ACT.SOFT }, { wait: 100 }, { press: ACT.CCW }, { press: ACT.HARD }],
  [{ press: ACT.SOFT }, { wait: 100 }, { wait: 100 }, { press: ACT.CW }, { press: ACT.HARD }],
  [{ press: ACT.CW }, { press: ACT.CW }, { press: ACT.SOFT }, { wait: 100 }, { press: ACT.CCW }, { press: ACT.HARD }],
  [{ press: ACT.LEFT }, { press: ACT.SOFT }, { wait: 100 }, { press: ACT.CW }, { press: ACT.CW }, { press: ACT.HARD }],
  [{ press: ACT.RIGHT }, { press: ACT.CW }, { press: ACT.SOFT }, { wait: 100 }, { press: ACT.FLIP }, { press: ACT.HARD }],
  // 하드드롭 없이 락다운 유예로 굳는 경로 (500ms)
  [{ press: ACT.CW }, { press: ACT.SOFT }, { wait: 100 }, { wait: 100 }, { wait: 100 }, { wait: 100 }, { wait: 100 }, { wait: 100 }],
  // 홀드로 조각을 바꿔치기한 뒤 두는 경로
  [{ press: ACT.HOLD }, { press: ACT.CW }, { press: ACT.LEFT }, { press: ACT.HARD }],
];

/** 무작위 입력 단어 — 하드드롭으로 끝나는 짧은 키 시퀀스. */
export function randomWords(count = 48): PlaceOp[][] {
  const r = scriptRng(0x1d872b41);
  const KEYS = [ACT.LEFT, ACT.RIGHT, ACT.CW, ACT.CCW, ACT.FLIP, ACT.SOFT, ACT.HOLD];
  const out: PlaceOp[][] = [];
  for (let i = 0; i < count; i++) {
    const n = 1 + (r() % 6);
    const w: PlaceOp[] = [];
    for (let k = 0; k < n; k++) w.push({ press: KEYS[r() % KEYS.length] as number });
    w.push({ press: ACT.HARD }); // 반드시 굳혀서 결과가 보드에 남게 한다
    out.push(w);
  }
  return out;
}

/** 배치 트레이스가 쓰는 단어 전체 = 손으로 짠 것 + 무작위. */
export function inputWords(): PlaceOp[][] {
  return [...SPIN_WORDS, ...randomWords()];
}

export interface PlacementCase {
  /** 판 인덱스 · 조각 · 단어 인덱스 */
  b: number;
  p: number;
  w: number;
  /** 결과: [보드해시, 점수, 지운줄, T스핀, 상태, 공격, 누적줄, B2B] */
  r: number[];
}

export interface PlacementResult {
  cases: PlacementCase[];
}

/** 배치 트레이스를 전수로 돌린다. 판 5 × 조각 7 × 단어 56 = 1960 경우. */
export function runPlacementTrace(t: PlaceTarget, seed = 0x2545f491): PlacementResult {
  const words = inputWords();
  const cases: PlacementCase[] = [];
  for (let b = 0; b < BOARDS.length; b++) {
    for (let p = 0; p < 7; p++) {
      for (let w = 0; w < words.length; w++) {
        t.init(seed);
        t.paint(BOARDS[b] as readonly string[]);
        t.setPiece(p);
        for (const op of words[w] as PlaceOp[]) {
          if ('press' in op) t.press(op.press);
          else t.update(op.wait);
        }
        const s = t.stats();
        cases.push({
          b, p, w,
          r: [
            boardHash(t.board()),
            s[ST.SCORE] as number,
            s[ST.CLEAR] as number,
            s[ST.TSPIN] as number,
            s[ST.STATE] as number,
            s[ST.ATTACK] as number,
            s[ST.LINES] as number,
            s[ST.B2B] as number,
          ],
        });
      }
    }
  }
  return { cases };
}

// ── 3부: 연쇄 트레이스 (콤보 · B2B · 레벨업 · 상쇄) ────────────────────
//
// 배치 트레이스는 경우마다 init() 하므로 락이 딱 한 번씩만 일어난다.
// 그래서 **여러 번의 클리어가 이어져야 드러나는 규칙**을 하나도 못 밟는다:
//   콤보 누적, Back-to-Back ×1.5, 10줄마다 레벨업, 대기 가비지의 상쇄와 솟아오름.
// 여기서는 인스턴스를 유지한 채 판만 다시 심어서 그 연쇄를 강제로 만든다.
// 판을 다시 심어도 콤보·B2B·레벨은 stats 에 남아 있으므로 연쇄가 끊기지 않는다.

/** 연쇄 트레이스가 조작할 수 있어야 하는 것들 = 앞의 두 인터페이스를 합친 것. */
export interface ComboTarget extends TraceTarget, PlaceTarget {}

/** 한 라운드: 판을 심고 → 조각을 지정하고 → (가비지 예약) → 입력 단어를 넣는다. */
export interface ComboRound {
  board: readonly string[];
  piece: number;
  word: PlaceOp[];
  garbage?: number;
}

export interface ComboScenario {
  name: string;
  rounds: ComboRound[];
}

const TETRIS_WELL: readonly string[] = [...rep('.#########', 4), '#########.'];
const SINGLE_WELL: readonly string[] = ['.#########', '#########.'];
const NO_CLEAR: readonly string[] = ['#########.'];

/** I 를 세워서 왼쪽 끝 우물에 꽂는다. 벽에 막히면 코어가 알아서 멈추므로 6번이면 충분하다. */
const W_I_LEFT: PlaceOp[] = [
  { press: ACT.CW },
  ...rep('', 6).map(() => ({ press: ACT.LEFT })),
  { press: ACT.HARD },
];
/** 그냥 떨어뜨린다 — 줄이 안 지워지는 락(콤보 끊김 · 가비지 솟아오름)을 만든다. */
const W_DROP: PlaceOp[] = [{ press: ACT.HARD }];

function times<T>(n: number, f: (i: number) => T): T[] {
  return Array.from({ length: n }, (_, i) => f(i));
}

export const COMBO_SCENARIOS: readonly ComboScenario[] = [
  {
    // 테트리스만 8연속 → B2B 가 계속 붙고(×1.5), 콤보가 0→7 로 자라고, 32줄에 레벨 4
    name: '테트리스 8연속',
    rounds: times(8, () => ({ board: TETRIS_WELL, piece: 0, word: W_I_LEFT })),
  },
  {
    // 테트리스와 싱글을 번갈아 → 싱글에서 B2B 가 끊기고 다음 테트리스에서 다시 붙는다
    name: '테트리스와 싱글 교차',
    rounds: times(10, (i) => ({
      board: i % 2 === 0 ? TETRIS_WELL : SINGLE_WELL,
      piece: 0,
      word: W_I_LEFT,
    })),
  },
  {
    // T스핀 더블 6연속 → T스핀도 "어려운 클리어"라 B2B 가 붙는다
    name: 'T스핀 더블 6연속',
    rounds: times(6, () => ({ board: BOARDS[1] as readonly string[], piece: 5, word: SPIN_WORDS[0] as PlaceOp[] })),
  },
  {
    // 지우기와 못 지우기를 번갈아 → 콤보가 매번 끊기고, 예약한 가비지가 실제로 솟는다
    name: '콤보 끊기와 가비지 솟아오름',
    rounds: times(12, (i) => (i % 2 === 0
      ? { board: SINGLE_WELL, piece: 0, word: W_I_LEFT, garbage: 3 }
      : { board: NO_CLEAR, piece: 3, word: W_DROP })),
  },
];

export interface ComboStep {
  /** 시나리오 인덱스 · 라운드 인덱스 */
  s: number;
  i: number;
  /** [보드해시, 점수, 이번획득, 지운줄, T스핀, 콤보, B2B, 레벨, 누적줄, 공격, 대기, 퍼펙트] */
  r: number[];
}

export interface ComboResult {
  steps: ComboStep[];
}

/** 연쇄 시나리오를 전부 돌린다. */
export function runComboTrace(t: ComboTarget, seed = 0x13579bdf): ComboResult {
  const steps: ComboStep[] = [];
  for (let s = 0; s < COMBO_SCENARIOS.length; s++) {
    const sc = COMBO_SCENARIOS[s] as ComboScenario;
    t.init(seed);
    for (let i = 0; i < sc.rounds.length; i++) {
      const rd = sc.rounds[i] as ComboRound;
      t.paint(rd.board);
      if (rd.garbage) t.queueGarbage(rd.garbage);
      t.setPiece(rd.piece);
      for (const op of rd.word) {
        if ('press' in op) t.press(op.press);
        else t.update(op.wait);
      }
      const st = t.stats();
      steps.push({
        s, i,
        r: [
          boardHash(t.board()),
          st[ST.SCORE] as number, st[ST.GAIN] as number, st[ST.CLEAR] as number,
          st[ST.TSPIN] as number, st[ST.COMBO] as number, st[ST.B2B] as number,
          st[ST.LEVEL] as number, st[ST.LINES] as number, st[ST.ATTACK] as number,
          st[ST.PENDING] as number, st[ST.PERFECT] as number,
        ],
      });
    }
  }
  return { steps };
}

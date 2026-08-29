// ai.ts — ai.cpp 의 이식. 코어 위에 얹는 "판을 읽고 한 수를 고르는" 층.
//
// 설계 원칙 세 가지는 C++ 판 그대로다:
//   1. 게임 규칙은 core.ts 안에만 있다. 여기서 규칙을 다시 쓰지 않는다.
//   2. 탐색은 board 의 *사본* 위에서만 한다. 진행 중인 판을 절대 건드리지 않는다.
//   3. 가중치 8개는 바깥에서 갈아 끼운다. 재컴파일 없이 AI가 바뀐다.
//
// 이식에서 가장 조심한 것: **float32**.
// C++ 의 weights/last_feat 는 `float` 이고, wasm 은 f32.mul / f32.add 를 쓴다.
// TS 의 number 는 전부 float64 라 그냥 곱하고 더하면 값이 미세하게 달라지고,
// 그 미세한 차이가 `s > best_s` 비교를 뒤집어 **다른 수를 고르게** 만든다.
// 그래서 곱셈과 덧셈마다 Math.fround 로 f32 로 접는다. wasm 에는 FMA 명령이 없으므로
// 이 흉내가 비트 단위로 정확하다.

import { Tetris, SHAPES, W, H, SPAWN_X, SPAWN_Y, ST, STATE } from './core.js';

/** 보드 평가에 쓰는 특징 8가지. 순서가 곧 weights[] 의 순서다. */
export const F = {
  LINES: 0, // 이 수로 지워지는 줄 수  (많을수록 좋다)
  AGG: 1, // 열 높이의 총합  (낮을수록 좋다)
  HOLES: 2, // 덮인 빈칸 개수  (적을수록 좋다)
  BUMP: 3, // 이웃한 열 높이차의 총합  (작을수록 좋다)
  WELLS: 4, // 우물 깊이의 누적 비용  (작을수록 좋다)
  ROWT: 5, // 행 전이 수 (Dellacherie)  (작을수록 좋다)
  COLT: 6, // 열 전이 수 (Dellacherie)  (작을수록 좋다)
  LAND: 7, // 조각이 놓인 높이  (낮을수록 좋다)
  COUNT: 8,
} as const;

export const FEATURE_NAMES: readonly string[] = [
  'F_LINES', 'F_AGG', 'F_HOLES', 'F_BUMP', 'F_WELLS', 'F_ROWT', 'F_COLT', 'F_LAND',
];

// ── 사본 위에서 도는 규칙 3종 ────────────────────────────────────────
// collide/clearLines 와 같은 일을 하지만 코어의 board 대신 인자로 받은 배열을 본다.
// "같은 코드를 두 번 쓰는 것"처럼 보이지만, 코어를 포인터화하면 핫패스가 느려진다.
// 규칙의 진짜 사본은 여기 세 함수뿐이고 나머지는 전부 코어를 쓴다.
function simCollide(b: Uint8Array, piece: number, rot: number, px: number, py: number): boolean {
  const m = (SHAPES[piece] as readonly number[])[rot] as number;
  for (let i = 0; i < 16; i++) {
    if (!(m & (1 << i))) continue;
    const bx = px + (i & 3);
    const by = py + (i >> 2);
    if (bx < 0 || bx >= W || by >= H) return true;
    if (by < 0) continue;
    if (b[by * W + bx]) return true;
  }
  return false;
}

/** (rot, x) 로 스폰 줄에서 곧장 떨어뜨렸을 때 멈추는 y. 스폰 줄이 막혀 있으면 -1. */
function simDrop(b: Uint8Array, piece: number, rot: number, x: number): number {
  let y = SPAWN_Y;
  if (simCollide(b, piece, rot, x, y)) return -1;
  while (!simCollide(b, piece, rot, x, y + 1)) y++;
  return y;
}

/** 스폰 자리(SPAWN_X)에서 목표 x 까지 스폰 줄을 따라 한 칸씩 미끄러질 수 있는가.
 *  AI가 고른 수를 나중에 *실제 키 입력*으로 재현해야 하므로, 도달 불가능한 자리를
 *  후보에서 빼 둔다. 끼워 넣기(tuck)·스핀은 이 탐색의 범위 밖이다. */
function simReachable(b: Uint8Array, piece: number, rot: number, x: number): boolean {
  if (simCollide(b, piece, rot, SPAWN_X, SPAWN_Y)) return false;
  const step = x > SPAWN_X ? 1 : -1;
  for (let cx = SPAWN_X; cx !== x; cx += step) {
    if (simCollide(b, piece, rot, cx + step, SPAWN_Y)) return false;
  }
  return true;
}

function simPlace(b: Uint8Array, piece: number, rot: number, x: number, y: number): void {
  const m = (SHAPES[piece] as readonly number[])[rot] as number;
  for (let i = 0; i < 16; i++) {
    if (!(m & (1 << i))) continue;
    const bx = x + (i & 3), by = y + (i >> 2);
    if (by >= 0 && by < H && bx >= 0 && bx < W) b[by * W + bx] = piece + 1;
  }
}

function simClear(b: Uint8Array): number {
  let n = 0;
  for (let y = H - 1; y >= 0; y--) {
    let full = true;
    for (let x = 0; x < W; x++) {
      if (!b[y * W + x]) { full = false; break; }
    }
    if (!full) continue;
    n++;
    for (let yy = y; yy > 0; yy--) b.copyWithin(yy * W, (yy - 1) * W, (yy - 1) * W + W);
    b.fill(0, 0, W);
    y++; // 끌어내렸으니 같은 y 를 다시 본다
  }
  return n;
}

/** 조각 모양의 가장 아래 행 인덱스(0~3). 착지 높이 계산에 쓴다. */
function shapeBottom(piece: number, rot: number): number {
  const m = (SHAPES[piece] as readonly number[])[rot] as number;
  let r = 0;
  for (let i = 0; i < 16; i++) {
    if (m & (1 << i)) {
      const y = i >> 2;
      if (y > r) r = y;
    }
  }
  return r;
}

/**
 * 특징 추출.
 *
 * @param b      줄을 지운 *뒤*의 보드
 * @param lines  이 수로 지워진 줄 수
 * @param landH  조각 맨 아랫줄의 바닥 기준 높이 (바닥줄 = 1)
 * @param out    결과를 담을 Float32Array (길이 8)
 *
 * O(H·W) 시간, 추가 공간은 열 높이 배열 10칸뿐.
 */
export function features(b: Uint8Array, lines: number, landH: number, out: Float32Array): void {
  const h = new Array<number>(W);
  let holes = 0;
  for (let x = 0; x < W; x++) {
    let y = 0;
    while (y < H && !b[y * W + x]) y++;
    h[x] = H - y; // 열 높이 = 가장 높은 블록까지
    for (let yy = y + 1; yy < H; yy++) if (!b[yy * W + x]) holes++;
  }

  let agg = 0, bump = 0, wells = 0;
  for (let x = 0; x < W; x++) agg += h[x] as number;
  for (let x = 0; x + 1 < W; x++) bump += Math.abs((h[x] as number) - (h[x + 1] as number));
  for (let x = 0; x < W; x++) {
    // 양옆(벽은 천장 높이로 친다)보다 낮게 파인 만큼이 우물이다.
    const l = x === 0 ? H : (h[x - 1] as number);
    const r = x === W - 1 ? H : (h[x + 1] as number);
    const d = Math.min(l, r) - (h[x] as number);
    if (d > 0) wells += (d * (d + 1)) / 2; // 깊이 d 의 비용 1+2+…+d
  }

  // 행/열 전이: 채움↔빈칸이 뒤집히는 횟수. 벽과 바닥은 "채워진 것"으로 센다.
  // 울퉁불퉁하고 구멍 많은 판일수록 커진다 — 높이만으로는 안 보이는 결을 잡아낸다.
  let rowt = 0;
  for (let y = 0; y < H; y++) {
    let prev = 1; // 왼쪽 벽
    for (let x = 0; x < W; x++) {
      const c = b[y * W + x] ? 1 : 0;
      if (c !== prev) rowt++;
      prev = c;
    }
    if (!prev) rowt++; // 오른쪽 벽
  }
  let colt = 0;
  for (let x = 0; x < W; x++) {
    let prev = 0; // 천장 위는 비어 있다
    for (let y = 0; y < H; y++) {
      const c = b[y * W + x] ? 1 : 0;
      if (c !== prev) colt++;
      prev = c;
    }
    if (!prev) colt++; // 바닥
  }

  out[F.LINES] = lines;
  out[F.AGG] = agg;
  out[F.HOLES] = holes;
  out[F.BUMP] = bump;
  out[F.WELLS] = wells;
  out[F.ROWT] = rowt;
  out[F.COLT] = colt;
  out[F.LAND] = landH;
}

/** 가중치와 특징의 내적 — **float32 로**. Math.fround 를 빼면 wasm 과 다른 수를 고른다. */
export function scoreOf(weights: Float32Array, f: Float32Array): number {
  let s = 0;
  for (let i = 0; i < F.COUNT; i++) {
    s = Math.fround(s + Math.fround((weights[i] as number) * (f[i] as number)));
  }
  return s;
}

/** 기본 가중치 — weights.json 의 'max'. `make train`(개체 32 · 50세대)이 낸 실측값이고,
 *  부 2 의 C++/JS 학습 결과와 소수점까지 같다(코어·AI 파리티가 맞으니 당연한 결과다). */
export const DEFAULT_WEIGHTS: readonly number[] = [
  0.07328, 0.064795, -0.477997, 0.210324, -0.008971, -0.391833, -0.504655, -0.556259,
];

/**
 * 코어 하나에 붙는 AI.
 *
 * 탐색용 보드 사본(sim)과 특징 버퍼를 인스턴스마다 하나씩 들고 재사용한다.
 * 후보 하나마다 240바이트를 새로 할당하면 한 수에 100번 가까이 GC 를 자극한다.
 */
export class Ai {
  readonly weights = new Float32Array(F.COUNT);
  /** 마지막으로 고른 수의 특징 벡터 (시각화·테스트용) */
  readonly lastFeat = new Float32Array(F.COUNT);
  private readonly sim = new Uint8Array(H * W);
  private readonly buf = new Float32Array(F.COUNT);

  /** 직전 판이 누적한 공격 줄 수 */
  playAttack = 0;
  /** 직전 판이 실제로 놓은 조각 수 */
  playPlaced = 0;

  constructor(readonly game: Tetris, weights: readonly number[] = DEFAULT_WEIGHTS) {
    this.setWeights(weights);
  }

  setWeights(w: readonly number[] | Float32Array): void {
    for (let i = 0; i < F.COUNT; i++) this.weights[i] = (w[i] as number) ?? 0;
  }

  /**
   * 1수 탐색.
   *
   * 후보 = (홀드 쓸까 말까) × (회전 4) × (x −3‥9) ≈ 최대 104개,
   * 실제 유효한 건 30~80개. 결과는 정수 하나로 접어 반환한다:
   *   (useHold << 8) | (rot << 4) | (x + 3)
   * x 에 +3 을 더하는 건 −3 까지 가능한 좌표를 4비트 무부호로 담기 위해서다.
   *
   * 반환 -1 = 둘 수 있는 수가 없다(게임오버 포함).
   */
  plan(): number {
    const g = this.game;
    if (g.stats[ST.STATE] !== STATE.PLAY) return -1;

    let best = -1;
    let bestS = 0;
    let have = false;
    const f = this.buf;

    for (let useHold = 0; useHold < 2; useHold++) {
      let piece: number;
      if (!useHold) {
        piece = g.curPiece;
      } else {
        if (g.holdUsed) continue; // 조각당 홀드 1회
        piece = g.holdPiece < 0 ? (g.nextQ[0] as number) : g.holdPiece;
      }
      for (let rot = 0; rot < 4; rot++) {
        const shapes = SHAPES[piece] as readonly number[];
        if (rot > 0 && shapes[rot] === shapes[0]) continue; // O 조각
        for (let x = -3; x < W; x++) {
          const y = simDrop(g.board, piece, rot, x);
          if (y < 0) continue;
          if (!simReachable(g.board, piece, rot, x)) continue;

          this.sim.set(g.board);
          simPlace(this.sim, piece, rot, x, y);
          const landH = H - (y + shapeBottom(piece, rot)); // 바닥줄 = 1
          const lines = simClear(this.sim);
          features(this.sim, lines, landH, f);
          const s = scoreOf(this.weights, f);

          if (!have || s > bestS) {
            have = true;
            bestS = s;
            best = (useHold << 8) | (rot << 4) | (x + 3);
            this.lastFeat.set(f);
          }
        }
      }
    }
    return best;
  }

  /** 고른 수를 실제 판에 둔다. 규칙을 우회하지 않는다 —
   *  홀드는 doHold(), 낙하는 hardDrop() 을 그대로 쓴다. */
  apply(packed: number): void {
    const g = this.game;
    if (packed < 0 || g.stats[ST.STATE] !== STATE.PLAY) return;
    const x = (packed & 15) - 3;
    const rot = (packed >> 4) & 3;
    const useHold = (packed >> 8) & 1;

    if (useHold) {
      g.doHold();
      if (g.stats[ST.STATE] !== STATE.PLAY) return;
    }
    if (!g.collide(g.curPiece, rot, x, g.curY)) {
      g.curRot = rot;
      g.curX = x;
    }
    g.lastWasRot = 0; // 회전으로 들어간 게 아니므로 T스핀 판정 없음
    g.lastKick = 0;
    g.hardDrop();
    g.buildView();
  }

  /** 한 수 두고 그 수를 반환한다. */
  step(): number {
    const p = this.plan();
    if (p >= 0) this.apply(p);
    return p;
  }

  /** 지금 판을 그대로(조각을 놓지 않고) 평가한다 — "숫자를 눈으로 보는" 슬라이드용. */
  evalHere(): number {
    features(this.game.board, 0, 0, this.lastFeat);
    return scoreOf(this.weights, this.lastFeat);
  }

  /**
   * 한 판을 끝까지(또는 maxPieces 개까지) 둔다. GA 의 적합도 함수가 이걸 부른다.
   *
   * every > 0 이면 그만큼 놓을 때마다 가비지 1줄이 예약된다 — "비가 새는 배" 모드.
   * 왜 이게 필요한가: 가비지가 없으면 웬만한 가중치도 400조각을 안 죽고 버틴다.
   * 전원이 만점을 받으면 GA 는 누가 더 나은지 구별할 수 없다(적합도 천장).
   *
   * @returns 지운 줄 수. 공격/조각 수는 playAttack / playPlaced 로 따로 읽는다.
   */
  play(seed: number, maxPieces: number, every = 0): number {
    const g = this.game;
    g.init(seed);
    this.playAttack = 0;
    this.playPlaced = 0;
    while (g.stats[ST.STATE] === STATE.PLAY && this.playPlaced < maxPieces) {
      if (every > 0 && this.playPlaced > 0 && this.playPlaced % every === 0) g.queueGarbage(1);
      const p = this.plan();
      if (p < 0) break;
      this.apply(p);
      this.playAttack += g.stats[ST.ATTACK] as number;
      this.playPlaced++;
    }
    return g.stats[ST.LINES] as number;
  }
}

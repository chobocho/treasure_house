// core.ts — tetris.cpp(C++/WASM 판)의 규칙을 TypeScript 로 1:1 이식한 것.
//
// 이식의 원칙은 하나다: **결과가 비트 단위로 같아야 한다.**
// 그래서 "TS 답게" 고쳐 쓰고 싶은 곳(예: 배열 대신 객체, 정수 나눗셈 대신 실수)을
// 전부 참았다. RNG 한 줄만 달라져도 골든 트레이스가 통째로 어긋나기 때문이다.
//
// C++ 원본과 다른 점은 딱 하나: 전역 변수 대신 클래스 필드를 쓴다.
// wasm 모듈은 인스턴스를 새로 만들면 상태가 새로 생기지만, TS 모듈은 그렇지 않다.
// 8인 대전에서 인스턴스 8개가 필요하므로 상태를 클래스에 담았다.

// ── 판의 크기 ────────────────────────────────────────────────────────
export const W = 10; // 필드 가로 (칸)
export const VIS = 20; // 화면에 보이는 세로 (칸)
export const HIDDEN = 4; // 천장 위 숨은 줄 — 위쪽 월킥(-2칸)과 밀려 올라간 스택을 흡수한다 (스폰은 그 아래 보이는 줄)
export const H = VIS + HIDDEN; // 실제 배열 세로 = 24
export const SPAWN_X = 3;
export const SPAWN_Y = HIDDEN; // 4x4 박스의 좌상단 = 보이는 필드의 맨 윗줄

export const DAS_MS = 170; // 좌우 키를 누르고 자동반복이 시작되기까지
export const ARR_MS = 40; // 자동반복 1칸당 간격
export const SOFT_DIV = 20; // 소프트드롭 = 중력의 20배
export const LOCK_MS = 500; // 바닥에 닿은 뒤 굳기까지의 유예
export const LOCK_RESET = 15; // 유예를 되살릴 수 있는 최대 횟수

export const GARBAGE = 8; // 가비지 줄의 색 인덱스 (조각 색 1~7 과 겹치지 않게)
export const GARBAGE_CAP = 8; // 한 번의 락에서 올라올 수 있는 최대 줄 수

// 액션 코드 — C++ enum 과 같은 값. UI·AI·네트워크가 공유하는 유일한 "조작 프로토콜".
export const ACT = {
  LEFT: 0, RIGHT: 1, SOFT: 2, CW: 3, CCW: 4, HARD: 5, HOLD: 6, PAUSE: 7, FLIP: 8,
} as const;
export type Act = (typeof ACT)[keyof typeof ACT];

// stats[] 인덱스 — 두 번째 프로토콜. wasm 판에서 JS 가 선형 메모리를 읽던 그 배치를
// 그대로 유지한다. 덕분에 부 1 의 테스트 하니스를 거의 그대로 쓸 수 있다.
export const ST = {
  SCORE: 0, LINES: 1, LEVEL: 2, COMBO: 3, B2B: 4, STATE: 5, HOLD: 6,
  NEXT0: 7, NEXT1: 8, NEXT2: 9, NEXT3: 10, NEXT4: 11,
  CLEAR: 12, TSPIN: 13, GAIN: 14, PIECES: 15, ELAPSED: 16, GRAVITY: 17,
  PIECE: 18, ROT: 19, X: 20, Y: 21, GHOST: 22, EVENT: 23, ROWMASK: 24,
  PERFECT: 25, LOCKPCT: 26,
  ATTACK: 27, // 이번 락으로 상대에게 보낸 줄 수 (상쇄 후)
  PENDING: 28, // 아직 올라오지 않고 대기 중인 가비지 줄 수
  GARBAGE_RECV: 29, // 지금까지 실제로 밀려 올라온 누적 줄 수
  COUNT: 30,
} as const;

export const STATE = { PLAY: 0, OVER: 1, PAUSE: 2 } as const;

// 각 조각의 각 회전 상태를 16비트 정수 하나로 표현한다.
// 비트 인덱스 = y*4 + x  (y 는 아래로 증가, x 는 오른쪽으로 증가)
//
//   0x0071 = 0000 0000 0111 0001 → bit0, bit4, bit5, bit6
//
//     x→ 0 1 2 3
//   y=0  ■ . . .      J 조각의 스폰 상태
//   y=1  ■ ■ ■ .
//   y=2  . . . .
//   y=3  . . . .
//
// 이 표현의 장점: 충돌 검사가 16번의 비트 테스트로 끝나고,
// 조각 데이터 전체가 7×4 개의 수로 끝난다.
export const SHAPES: readonly (readonly number[])[] = [
  [0x00f0, 0x2222, 0x0f00, 0x4444], // 0 I — 하늘색
  [0x0071, 0x0226, 0x0470, 0x0322], // 1 J — 파랑
  [0x0074, 0x0622, 0x0170, 0x0223], // 2 L — 주황
  [0x0066, 0x0066, 0x0066, 0x0066], // 3 O — 노랑 (회전해도 그대로)
  [0x0036, 0x0462, 0x0360, 0x0231], // 4 S — 초록
  [0x0072, 0x0262, 0x0270, 0x0232], // 5 T — 보라
  [0x0063, 0x0264, 0x0630, 0x0132], // 6 Z — 빨강
];

// 회전이 벽/블록에 막히면 그냥 실패시키지 않고, 정해진 순서로 5개 위치를 시도한다.
// 이 표가 곧 "현대 테트리스의 손맛"이다. T스핀도 여기서 태어난다.
//
// 원본 SRS 표는 y축이 위로 +1 이다. 우리 좌표계는 아래로 +1 이므로
// 적용할 때 y 부호를 뒤집는다 (tryRotate 참고).
//
// [from_rotation][시도순서][x, y]
type KickTable = readonly (readonly (readonly [number, number])[])[];

const KICK_JLSTZ_CW: KickTable = [
  [[0, 0], [-1, 0], [-1, +1], [0, -2], [-1, -2]], // 0→1
  [[0, 0], [+1, 0], [+1, -1], [0, +2], [+1, +2]], // 1→2
  [[0, 0], [+1, 0], [+1, +1], [0, -2], [+1, -2]], // 2→3
  [[0, 0], [-1, 0], [-1, -1], [0, +2], [-1, +2]], // 3→0
];
const KICK_JLSTZ_CCW: KickTable = [
  [[0, 0], [+1, 0], [+1, +1], [0, -2], [+1, -2]], // 0→3
  [[0, 0], [+1, 0], [+1, -1], [0, +2], [+1, +2]], // 1→0
  [[0, 0], [-1, 0], [-1, +1], [0, -2], [-1, -2]], // 2→1
  [[0, 0], [-1, 0], [-1, -1], [0, +2], [-1, +2]], // 3→2
];
// I 조각은 회전축이 칸 경계에 있어서 전용 표를 쓴다.
const KICK_I_CW: KickTable = [
  [[0, 0], [-2, 0], [+1, 0], [-2, -1], [+1, +2]], // 0→1
  [[0, 0], [-1, 0], [+2, 0], [-1, +2], [+2, -1]], // 1→2
  [[0, 0], [+2, 0], [-1, 0], [+2, +1], [-1, -2]], // 2→3
  [[0, 0], [+1, 0], [-2, 0], [+1, -2], [-2, +1]], // 3→0
];
const KICK_I_CCW: KickTable = [
  [[0, 0], [-1, 0], [+2, 0], [-1, +2], [+2, -1]], // 0→3
  [[0, 0], [+2, 0], [-1, 0], [+2, +1], [-1, -2]], // 1→0
  [[0, 0], [+1, 0], [-2, 0], [+1, -2], [-2, +1]], // 2→1
  [[0, 0], [-2, 0], [+1, 0], [-2, -1], [+1, +2]], // 3→2
];

// 가이드라인 공식: (0.8 - 0.007*(level-1))^(level-1) 초/칸.
// C++ 판은 -nostdlib 라 pow() 를 못 써서 미리 계산해 굳혔다. TS 는 Math.pow 를 쓸 수
// 있지만, 부동소수점 반올림이 언어마다 미세하게 다를 수 있어 **표를 그대로 가져왔다**.
// 결정론이 성능보다 중요하다.
export const GRAVITY_MS: readonly number[] = [
  1000, // [0] 미사용(레벨은 1부터)
  1000, 793, 618, 473, 355, 262, 190, 135, // 레벨 1~8
  94, 64, 43, 28, 18, 11, 7, 4, // 레벨 9~16
  3, 2, 1, 1, // 레벨 17~20
];

// 콤보 공격 표 — 대전 규칙에서만 쓴다.
const COMBO_ATK: readonly number[] = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5];

/**
 * 줄을 지웠을 때 상대에게 보낼 가비지 줄 수.
 *
 * 표 자체는 현대 대전 테트리스의 사실상 표준을 따랐다.
 *   싱글 0 / 더블 1 / 트리플 2 / 테트리스 4
 *   T스핀 싱글 2 / 더블 4 / 트리플 6, 미니 T스핀 0 / 미니 더블 1
 *   Back-to-Back +1, 콤보 보너스 표, 퍼펙트 클리어 +10
 * 싱글이 0 인 게 핵심이다 — 한 줄씩 지우는 플레이는 공격이 되지 않는다.
 *
 * @param b2bBefore 이번 락이 stats[ST.B2B] 를 덮어쓰기 *전*의 값
 */
export function attackFor(
  n: number, tsp: number, b2bBefore: number, combo: number, perfect: boolean,
): number {
  if (n <= 0) return 0;
  const PLAIN = [0, 0, 1, 2, 4]; // -, 싱글, 더블, 트리플, 테트리스
  const TSPIN = [0, 2, 4, 6, 6]; // 정식 T스핀
  const MINI = [0, 0, 1, 1, 1]; // 미니 T스핀
  let atk = (tsp === 2 ? TSPIN[n] : tsp === 1 ? MINI[n] : PLAIN[n]) as number;

  // "어려운 클리어"의 정의는 점수 규칙과 같다 — 테트리스 또는 T스핀.
  const difficult = tsp > 0 || n === 4;
  if (difficult && b2bBefore) atk += 1;

  let c = combo;
  if (c < 0) c = 0;
  if (c > 12) c = 12;
  atk += COMBO_ATK[c] as number;
  if (perfect) atk += 10;
  return atk;
}

/**
 * 테트리스 코어 1인분.
 *
 * 시간은 밀리초 정수로만 흐른다(`update(dtMs)`). 부동소수점 dt 를 쓰면 같은 입력
 * 시퀀스가 기기마다 다른 결과를 내서 온라인 대전의 락스텝이 깨진다.
 */
export class Tetris {
  /** 굳은 블록: 0=빈칸, 1~7=조각 색, 8=가비지. 크기 H*W. */
  readonly board = new Uint8Array(H * W);
  /** 화면 버퍼(굳은 블록만). 크기 VIS*W. */
  readonly cells = new Uint8Array(VIS * W);
  /** 오버레이: 1~7=현재조각, 8~14=고스트. 크기 VIS*W. */
  readonly overlay = new Uint8Array(VIS * W);
  /** 숫자 상태 전부. 인덱스는 ST 를 쓴다. */
  readonly stats = new Int32Array(ST.COUNT);

  curPiece = 0;
  curRot = 0;
  curX = 0;
  curY = 0;
  holdPiece = -1;
  holdUsed = 0;

  private bag = new Int32Array(7);
  private bagIdx = 7;
  /** 다음 조각 큐(앞 5개만 노출) */
  nextQ = new Int32Array(7);
  private rngState = 0;

  private gravAcc = 0;
  private lockTimer = 0;
  private lockResets = 0;
  private grounded = 0;
  private dasDir = 0;
  private dasTimer = 0;
  private arrTimer = 0;
  private softHeld = 0;

  /** 마지막 이동이 회전이었는가 — T스핀 판정의 전제 조건 */
  lastWasRot = 0;
  /** 성공한 킥의 인덱스. 5번째(4)면 미니 T스핀이 정식으로 올라간다 */
  lastKick = 0;
  private eventId = 0;
  /** 상대가 보냈지만 아직 필드에 올라오지 않은 줄 */
  private pendingGarbage = 0;

  constructor(seed = 1) {
    this.init(seed);
  }

  // ── RNG ────────────────────────────────────────────────────────────
  // xorshift32. C++ 의 u32 연산을 JS 로 옮길 때 함정은 `<<` 가 int32 를 낸다는 것.
  // 매 단계 `>>> 0` 으로 무부호 32비트로 되돌려야 C++ 와 같은 수열이 나온다.
  private rnd(): number {
    let s = this.rngState;
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    this.rngState = s;
    return s;
  }

  /** 7-bag: 7종을 한 봉지에 넣고 섞어서 하나씩 꺼낸다.
   *  "S/Z만 10번 연속" 같은 사고가 원천적으로 불가능해진다.
   *  최악 대기: 같은 조각 사이 최대 12개 (봉지 앞 + 다음 봉지 뒤). */
  private refillBag(): void {
    for (let i = 0; i < 7; i++) this.bag[i] = i;
    for (let i = 6; i > 0; i--) {
      // Fisher-Yates
      const j = this.rnd() % (i + 1);
      const t = this.bag[i] as number;
      this.bag[i] = this.bag[j] as number;
      this.bag[j] = t;
    }
    this.bagIdx = 0;
  }

  private pullBag(): number {
    if (this.bagIdx >= 7) this.refillBag();
    return this.bag[this.bagIdx++] as number;
  }

  // ── 충돌·낙하 ──────────────────────────────────────────────────────
  /** (piece, rot) 모양을 (px, py) 에 놓았을 때 겹치는가?
   *   * 좌우/바닥 밖  → 충돌
   *   * 천장 위(y<0)  → 충돌 아님 (조각이 위로 삐져나오는 건 합법)
   *   * 굳은 블록  → 충돌 */
  collide(piece: number, rot: number, px: number, py: number): boolean {
    const m = (SHAPES[piece] as readonly number[])[rot] as number;
    for (let i = 0; i < 16; i++) {
      if (!(m & (1 << i))) continue;
      const bx = px + (i & 3);
      const by = py + (i >> 2);
      if (bx < 0 || bx >= W || by >= H) return true;
      if (by < 0) continue;
      if (this.board[by * W + bx]) return true;
    }
    return false;
  }

  /** 고스트(착지 예상 위치) 계산: 부딪힐 때까지 내린다. */
  ghostY(): number {
    let y = this.curY;
    while (!this.collide(this.curPiece, this.curRot, this.curX, y + 1)) y++;
    return y;
  }

  private fillQueue(): void {
    for (let i = 0; i < 7; i++) this.nextQ[i] = this.pullBag();
  }

  private spawnNext(): void {
    this.curPiece = this.nextQ[0] as number;
    for (let i = 0; i < 6; i++) this.nextQ[i] = this.nextQ[i + 1] as number;
    this.nextQ[6] = this.pullBag();

    this.curRot = 0;
    this.curX = SPAWN_X;
    this.curY = SPAWN_Y;
    this.holdUsed = 0;
    this.grounded = 0; this.lockTimer = 0; this.lockResets = 0;
    this.lastWasRot = 0; this.lastKick = 0;
    this.stats[ST.PIECES]++;

    // 블록아웃: 스폰 위치가 이미 막혔다 → 게임 오버
    if (this.collide(this.curPiece, this.curRot, this.curX, this.curY)) {
      this.stats[ST.STATE] = STATE.OVER;
    }
  }

  private tryMove(dx: number, dy: number): boolean {
    if (this.collide(this.curPiece, this.curRot, this.curX + dx, this.curY + dy)) return false;
    this.curX += dx;
    this.curY += dy;
    this.lastWasRot = 0;
    return true;
  }

  /** 회전 시도. dir: +1 = 시계, -1 = 반시계.
   *  5개 킥 후보를 순서대로 밀어 보고 처음 성공한 곳에 앉힌다. */
  tryRotate(dir: number): boolean {
    const from = this.curRot;
    const to = (this.curRot + (dir > 0 ? 1 : 3)) & 3;
    // I 조각만 전용 표. O 조각은 어차피 모양이 같아서 첫 후보 (0,0) 에서 바로 성공한다.
    const tbl = (this.curPiece === 0
      ? dir > 0 ? KICK_I_CW[from] : KICK_I_CCW[from]
      : dir > 0 ? KICK_JLSTZ_CW[from] : KICK_JLSTZ_CCW[from]) as readonly (readonly [number, number])[];

    for (let k = 0; k < 5; k++) {
      const kick = tbl[k] as readonly [number, number];
      const nx = this.curX + kick[0];
      const ny = this.curY - kick[1]; // ← y 부호 반전 (표는 위가 +)
      if (!this.collide(this.curPiece, to, nx, ny)) {
        this.curRot = to; this.curX = nx; this.curY = ny;
        this.lastWasRot = 1; // T스핀 판정에 쓰인다
        this.lastKick = k; // 5번째(k===4) 킥은 미니 T스핀을 정식으로 올린다
        if (this.grounded && this.lockResets < LOCK_RESET) {
          this.lockTimer = 0;
          this.lockResets++;
        }
        return true;
      }
    }
    return false;
  }

  // ── T스핀 판정 ─────────────────────────────────────────────────────
  /** 벽/바닥은 "막힌 것"으로 센다. 천장 위는 뚫린 것으로 센다. */
  private filled(x: number, y: number): number {
    if (x < 0 || x >= W || y >= H) return 1;
    if (y < 0) return 0;
    return this.board[y * W + x] !== 0 ? 1 : 0;
  }

  /** T 조각의 중심(cx,cy) 기준 네 대각 코너 중,
   *   * "앞" 두 코너 = T 가 가리키는 방향 쪽 두 개
   *   * 앞 2개 + 뒤 1개 이상이 막힘 → 정식 T스핀
   *   * 앞 1개 + 뒤 2개가 막힘  → 미니 T스핀
   *   * 단, 5번째 킥으로 들어갔으면 미니 패턴도 정식으로 친다
   *  반환: 0=없음 1=미니 2=정식 */
  private detectTspin(): number {
    if (this.curPiece !== 5 || !this.lastWasRot) return 0;
    const cx = this.curX + 1, cy = this.curY + 1;
    // 회전 상태별 "앞쪽" 두 코너의 오프셋
    const FRONT = [
      [-1, -1, +1, -1], // rot0: 위쪽을 가리킴 → 위 두 코너
      [+1, -1, +1, +1], // rot1: 오른쪽
      [-1, +1, +1, +1], // rot2: 아래
      [-1, -1, -1, +1], // rot3: 왼쪽
    ];
    const BACK = [
      [-1, +1, +1, +1], [-1, -1, -1, +1], [-1, -1, +1, -1], [+1, -1, +1, +1],
    ];
    const fr = FRONT[this.curRot] as number[];
    const bk = BACK[this.curRot] as number[];
    const f = this.filled(cx + (fr[0] as number), cy + (fr[1] as number))
      + this.filled(cx + (fr[2] as number), cy + (fr[3] as number));
    const b = this.filled(cx + (bk[0] as number), cy + (bk[1] as number))
      + this.filled(cx + (bk[2] as number), cy + (bk[3] as number));
    if (f === 2 && b >= 1) return 2;
    if (f === 1 && b === 2) return this.lastKick === 4 ? 2 : 1;
    return 0;
  }

  // ── 대전 규칙: 가비지 밀어 올리기 ──────────────────────────────────
  /** n 줄을 바닥에서 밀어 올린다. hole 은 뚫려 있는 칸의 x.
   *  한 번에 올라오는 n 줄은 같은 구멍을 공유한다("클린 가비지") — 구멍이 매 줄
   *  달라지면 사실상 복구가 불가능해서 대전이 성립하지 않는다.
   *  hole < 0 이면 이 인스턴스의 RNG 가 고른다.
   *  천장 밖으로 밀려난 줄은 그냥 사라진다(배열이 곧 필드 전체이므로). */
  private pushRows(n: number, hole: number): void {
    if (n <= 0) return;
    if (n > H) n = H;
    if (hole < 0 || hole >= W) hole = this.rnd() % W;

    const b = this.board;
    for (let y = 0; y < H - n; y++) b.copyWithin(y * W, (y + n) * W, (y + n) * W + W);
    for (let y = H - n; y < H; y++) {
      b.fill(GARBAGE, y * W, y * W + W);
      b[y * W + hole] = 0;
    }
    this.stats[ST.GARBAGE_RECV] += n;
  }

  /** 꽉 찬 줄을 지우고 위를 끌어내린다. 지운 줄 수를 반환. */
  private clearLines(): number {
    let n = 0;
    let mask = 0;
    const b = this.board;
    for (let y = H - 1; y >= 0; y--) {
      let full = true;
      for (let x = 0; x < W; x++) {
        if (!b[y * W + x]) { full = false; break; }
      }
      if (!full) continue;
      n++;
      if (y >= HIDDEN) mask |= 1 << (y - HIDDEN);
      for (let yy = y; yy > 0; yy--) b.copyWithin(yy * W, (yy - 1) * W, (yy - 1) * W + W);
      b.fill(0, 0, W);
      y++; // 같은 y 를 다시 검사
    }
    this.stats[ST.ROWMASK] = mask;
    return n;
  }

  // ── 락 ─────────────────────────────────────────────────────────────
  /** 가이드라인 점수표를 그대로 구현한다.
   *   싱글 100 / 더블 300 / 트리플 500 / 테트리스 800  (×레벨)
   *   T스핀 0/1/2/3줄 = 400/800/1200/1600, 미니 = 100/200/400
   *   Back-to-Back(어려운 클리어 연속) ×1.5
   *   콤보 50 × 콤보수 × 레벨
   *   퍼펙트 클리어 보너스 (필드를 완전히 비움) */
  private lockPiece(): void {
    const tsp = this.detectTspin();

    const m = (SHAPES[this.curPiece] as readonly number[])[this.curRot] as number;
    for (let i = 0; i < 16; i++) {
      if (!(m & (1 << i))) continue;
      const bx = this.curX + (i & 3), by = this.curY + (i >> 2);
      if (by >= 0 && by < H && bx >= 0 && bx < W) this.board[by * W + bx] = this.curPiece + 1;
    }

    const n = this.clearLines();
    const lvl = this.stats[ST.LEVEL] as number;
    let base = 0, difficult = false;
    const b2bBefore = this.stats[ST.B2B] as number; // 아래에서 덮어쓰기 전에 붙잡아 둔다
    let perfect = false;

    if (tsp === 2) {
      base = [400, 800, 1200, 1600, 1600][n] as number;
      difficult = n > 0;
    } else if (tsp === 1) {
      base = [100, 200, 400, 400, 400][n] as number;
      difficult = n > 0;
    } else {
      base = [0, 100, 300, 500, 800][n] as number;
      difficult = n === 4;
    }

    let gain = base * lvl;

    if (n > 0) {
      // Back-to-Back ×1.5 — C++ 의 int 나눗셈이므로 반드시 내림한다
      if (difficult && this.stats[ST.B2B]) gain = Math.trunc((gain * 3) / 2);
      this.stats[ST.B2B] = difficult ? 1 : 0;
      this.stats[ST.COMBO] = (this.stats[ST.COMBO] as number) + 1; // -1 → 0(첫 클리어) → 1 → ...
      gain += 50 * (this.stats[ST.COMBO] as number) * lvl;
      this.stats[ST.LINES] += n;
      this.stats[ST.LEVEL] = 1 + Math.trunc((this.stats[ST.LINES] as number) / 10);
      if ((this.stats[ST.LEVEL] as number) > 20) this.stats[ST.LEVEL] = 20;

      let empty = true; // 퍼펙트 클리어?
      for (let i = 0; i < H * W; i++) {
        if (this.board[i]) { empty = false; break; }
      }
      if (empty) {
        gain += 1000 * lvl;
        this.stats[ST.PERFECT]++;
        perfect = true;
      }
    } else {
      this.stats[ST.COMBO] = -1; // 콤보 끊김
    }

    this.stats[ST.SCORE] += gain;
    this.stats[ST.GAIN] = gain;
    this.stats[ST.CLEAR] = n;
    this.stats[ST.TSPIN] = tsp;
    this.stats[ST.GRAVITY] = GRAVITY_MS[this.stats[ST.LEVEL] as number] as number;

    // ── 대전: 공격 계산 → 상쇄 → 가비지 적용 ────────────────────────
    // 순서가 규칙의 전부다. 내가 보낼 공격은 먼저 *내* 대기줄을 지우고(상쇄),
    // 남은 만큼만 상대에게 간다. 그래서 맞받아치면 가비지가 올라오지 않는다.
    let atk = attackFor(n, tsp, b2bBefore, this.stats[ST.COMBO] as number, perfect);
    const cancel = Math.min(atk, this.pendingGarbage);
    this.pendingGarbage -= cancel;
    atk -= cancel;
    this.stats[ST.ATTACK] = atk;

    // 대기 중인 가비지는 "줄을 못 지운 락"에서만 실제로 솟아오른다.
    // 이 유예가 없으면 상쇄할 기회 자체가 없다.
    if (n === 0 && this.pendingGarbage > 0) {
      const k = Math.min(this.pendingGarbage, GARBAGE_CAP);
      this.pushRows(k, -1);
      this.pendingGarbage -= k;
    }
    this.stats[ST.PENDING] = this.pendingGarbage;

    this.eventId++;
    this.stats[ST.EVENT] = this.eventId;

    this.spawnNext();
  }

  private hardDropInternal(): void {
    let d = 0;
    while (this.tryMove(0, 1)) d++;
    this.stats[ST.SCORE] += d * 2; // 하드드롭 1칸당 2점
    this.lockPiece();
  }

  /** AI 가 고른 수를 두는 경로에서도 쓰인다 — 규칙을 우회하지 않기 위해 공개한다. */
  hardDrop(): void {
    this.hardDropInternal();
  }

  /** 홀드. 조각당 1회 제한 — 무한 스왑 방지. */
  doHold(): void {
    if (this.holdUsed) return;
    const p = this.holdPiece;
    this.holdPiece = this.curPiece;
    this.stats[ST.HOLD] = this.holdPiece;
    if (p < 0) {
      this.spawnNext();
    } else {
      this.curPiece = p; this.curRot = 0; this.curX = SPAWN_X; this.curY = SPAWN_Y;
      this.grounded = 0; this.lockTimer = 0; this.lockResets = 0; this.lastWasRot = 0;
      if (this.collide(this.curPiece, this.curRot, this.curX, this.curY)) {
        this.stats[ST.STATE] = STATE.OVER;
      }
    }
    this.holdUsed = 1;
  }

  /** cells/overlay/stats 의 표시용 필드를 현재 상태로 갱신한다. */
  buildView(): void {
    for (let y = 0; y < VIS; y++) {
      this.cells.set(this.board.subarray((y + HIDDEN) * W, (y + HIDDEN) * W + W), y * W);
    }
    this.overlay.fill(0);

    if (this.stats[ST.STATE] === STATE.OVER) return;

    const gy = this.ghostY();
    const m = (SHAPES[this.curPiece] as readonly number[])[this.curRot] as number;
    for (let i = 0; i < 16; i++) {
      // 고스트 먼저(현재 조각이 덮어씀)
      if (!(m & (1 << i))) continue;
      const bx = this.curX + (i & 3), by = gy + (i >> 2) - HIDDEN;
      if (by >= 0 && by < VIS && bx >= 0 && bx < W) this.overlay[by * W + bx] = this.curPiece + 8;
    }
    for (let i = 0; i < 16; i++) {
      if (!(m & (1 << i))) continue;
      const bx = this.curX + (i & 3), by = this.curY + (i >> 2) - HIDDEN;
      if (by >= 0 && by < VIS && bx >= 0 && bx < W) this.overlay[by * W + bx] = this.curPiece + 1;
    }
    this.stats[ST.PIECE] = this.curPiece;
    this.stats[ST.ROT] = this.curRot;
    this.stats[ST.X] = this.curX;
    this.stats[ST.Y] = this.curY - HIDDEN;
    this.stats[ST.GHOST] = gy - HIDDEN;
    for (let i = 0; i < 5; i++) this.stats[ST.NEXT0 + i] = this.nextQ[i] as number;
    this.stats[ST.LOCKPCT] = this.grounded ? Math.trunc((this.lockTimer * 100) / LOCK_MS) : 0;
  }

  // ── 공개 API (wasm 판의 ts_* 익스포트와 1:1 대응) ───────────────────
  init(seed: number): void {
    this.rngState = (seed >>> 0) || 0x9e3779b9;
    this.board.fill(0);
    this.stats.fill(0);
    this.stats[ST.LEVEL] = 1;
    this.stats[ST.COMBO] = -1;
    this.stats[ST.HOLD] = -1;
    this.stats[ST.STATE] = STATE.PLAY;
    this.stats[ST.GRAVITY] = GRAVITY_MS[1] as number;
    this.holdPiece = -1; this.holdUsed = 0;
    this.gravAcc = 0; this.lockTimer = 0; this.lockResets = 0; this.grounded = 0;
    this.dasDir = 0; this.dasTimer = 0; this.arrTimer = 0; this.softHeld = 0;
    this.eventId = 0;
    this.pendingGarbage = 0;
    this.bagIdx = 7;
    this.fillQueue();
    this.spawnNext();
    this.buildView();
  }

  /** dtMs 만큼 시간을 진행시킨다. rAF 루프가 매 프레임 호출한다. */
  update(dtMs: number): void {
    if (this.stats[ST.STATE] !== STATE.PLAY) return;
    if (dtMs > 100) dtMs = 100; // 탭 전환 후 거대한 dt 방지
    this.stats[ST.ELAPSED] += dtMs;

    // 1) DAS/ARR — 좌우 자동반복
    if (this.dasDir) {
      this.dasTimer += dtMs;
      if (this.dasTimer >= DAS_MS) {
        this.arrTimer += dtMs;
        while (this.arrTimer >= ARR_MS) {
          this.arrTimer -= ARR_MS;
          if (this.tryMove(this.dasDir, 0) && this.grounded && this.lockResets < LOCK_RESET) {
            this.lockTimer = 0;
            this.lockResets++;
          }
        }
      }
    }

    // 2) 중력 — 소프트드롭 중이면 20배 빠르게
    let g = GRAVITY_MS[this.stats[ST.LEVEL] as number] as number;
    if (this.softHeld) {
      g = Math.trunc(g / SOFT_DIV);
      if (g < 1) g = 1;
    }
    this.gravAcc += dtMs;
    while (this.gravAcc >= g) {
      this.gravAcc -= g;
      const before = this.curY;
      this.tryMove(0, 1); // 실패해도 괜찮다 — 착지 판정은 아래에서 매 프레임 한다
      if (this.softHeld && this.curY > before) this.stats[ST.SCORE] += 1; // 소프트드롭 1칸 1점
      if (this.stats[ST.STATE] !== STATE.PLAY) return;
    }

    // 3) 락다운 — "닿아 있는가"를 중력 틱이 아니라 매 프레임 검사한다.
    //    중력 틱에서만 검사하면 레벨1(1000ms/칸)에서 착지 후 최대 1초를 그냥 서 있게 된다.
    if (this.collide(this.curPiece, this.curRot, this.curX, this.curY + 1)) {
      this.grounded = 1;
      this.lockTimer += dtMs;
      if (this.lockTimer >= LOCK_MS) {
        this.lockPiece();
        this.gravAcc = 0;
      }
    } else {
      this.grounded = 0;
      this.lockTimer = 0; // 옆으로 빠져나가 다시 공중에 떴다
    }
    this.buildView();
  }

  press(act: number): void {
    if (act === ACT.PAUSE) {
      if (this.stats[ST.STATE] === STATE.PLAY) this.stats[ST.STATE] = STATE.PAUSE;
      else if (this.stats[ST.STATE] === STATE.PAUSE) this.stats[ST.STATE] = STATE.PLAY;
      return;
    }
    if (this.stats[ST.STATE] !== STATE.PLAY) return;

    switch (act) {
      case ACT.LEFT:
      case ACT.RIGHT: {
        const d = act === ACT.LEFT ? -1 : +1;
        this.dasDir = d; this.dasTimer = 0; this.arrTimer = 0;
        if (this.tryMove(d, 0) && this.grounded && this.lockResets < LOCK_RESET) {
          this.lockTimer = 0;
          this.lockResets++;
        }
        break;
      }
      case ACT.SOFT: this.softHeld = 1; this.gravAcc = 0; break;
      case ACT.CW: this.tryRotate(+1); break;
      case ACT.CCW: this.tryRotate(-1); break;
      case ACT.FLIP: this.tryRotate(+1); this.tryRotate(+1); break; // 180도
      case ACT.HARD: this.hardDropInternal(); break;
      case ACT.HOLD: this.doHold(); break;
      default: break;
    }
    this.buildView();
  }

  release(act: number): void {
    if (act === ACT.LEFT && this.dasDir < 0) this.dasDir = 0;
    if (act === ACT.RIGHT && this.dasDir > 0) this.dasDir = 0;
    if (act === ACT.SOFT) this.softHeld = 0;
  }

  /** 심판이 상대의 ST.ATTACK 을 읽어 이쪽에 쌓아 준다. 규칙은 전부 코어 안에 있고
   *  바깥은 두 인스턴스 사이에서 숫자 하나를 옮기는 배달부일 뿐이다. */
  queueGarbage(n: number): void {
    if (n <= 0) return;
    this.pendingGarbage += n;
    this.stats[ST.PENDING] = this.pendingGarbage;
  }

  /** 대기열을 거치지 않고 지금 당장 밀어 올린다 — 테스트와 데모용.
   *  holeX < 0 이면 RNG 가 고른다. */
  garbage(n: number, holeX: number): void {
    this.pushRows(n, holeX);
    // 진행 중인 조각이 솟아오른 줄에 파묻히면 위로 빼 준다.
    while (this.collide(this.curPiece, this.curRot, this.curX, this.curY) && this.curY > -HIDDEN) {
      this.curY--;
    }
    if (this.collide(this.curPiece, this.curRot, this.curX, this.curY)) {
      this.stats[ST.STATE] = STATE.OVER;
    }
    this.buildView();
  }

  /** 테스트·데모 전용 훅: 지금 조각을 지정한 종류로 바꿔 스폰 상태로 되돌린다.
   *  게임 로직은 이 함수를 절대 호출하지 않는다. 특정 상황(T스핀 자리, 테트리스
   *  자리)을 재현하려면 "이 조각이 지금 나와야 한다"를 강제할 방법이 필요하다. */
  setPiece(piece: number): void {
    if (piece < 0 || piece > 6) return;
    this.curPiece = piece; this.curRot = 0; this.curX = SPAWN_X; this.curY = SPAWN_Y;
    this.holdUsed = 0; this.grounded = 0; this.lockTimer = 0; this.lockResets = 0;
    this.lastWasRot = 0; this.lastKick = 0;
    if (this.collide(this.curPiece, this.curRot, this.curX, this.curY)) {
      this.stats[ST.STATE] = STATE.OVER;
    }
    this.buildView();
  }

  /** 대기 중인 가비지 줄 수 (읽기 전용 접근자 — 테스트와 UI 용) */
  get pending(): number {
    return this.pendingGarbage;
  }
}

// ── 도구 함수 ──────────────────────────────────────────────────────────
/** 보드를 32비트 정수 하나로 굳힌다 — "두 구현이 같은 판을 만들었는가"를 볼 때 쓴다.
 *  FNV-1a. 충돌 확률은 골든 트레이스 수천 스텝 규모에서 무시할 만하다. */
export function boardHash(b: Uint8Array): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < b.length; i++) {
    h ^= b[i] as number;
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h;
}

/** 보이는 20줄을 사람이 읽을 수 있는 문자열로.
 *  Tetris 인스턴스가 아니라 배열을 받는다 — wasm 의 보드도 같은 함수로 찍어 보려고. */
export function dumpBoard(b: Uint8Array): string {
  const out: string[] = [];
  for (let y = HIDDEN; y < H; y++) {
    let s = '';
    for (let x = 0; x < W; x++) {
      const v = b[y * W + x] as number;
      s += v === 0 ? '.' : v === GARBAGE ? '#' : String(v);
    }
    out.push(s);
  }
  return out.join('\n');
}

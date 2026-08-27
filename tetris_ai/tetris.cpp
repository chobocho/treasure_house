typedef unsigned char  u8;
typedef unsigned short u16;
typedef signed   char  i8;
typedef unsigned int   u32;
typedef __SIZE_TYPE__  usize;

// export_name 속성 = "이 심볼을 이 이름 그대로 wasm 익스포트 테이블에 올려라".
// extern "C" 는 C++ 네임 맹글링(_Z6ts_initj)을 막아 준다. 둘 다 필요하다.
#define EXPORT(name) extern "C" __attribute__((export_name(#name), used))

// -nostdlib 이라도 컴파일러는 구조체 복사/배열 초기화를 memcpy/memset 호출로
// 낮춰 버릴 수 있다. 그러면 wasm-ld 가 "undefined symbol: memset" 으로 죽는다.
// 그래서 우리가 직접 최소 구현을 제공한다. (이게 프리스탠딩의 대가다)
extern "C" void* memset(void* d, int c, usize n) {
  u8* p = (u8*)d;
  while (n--) *p++ = (u8)c;
  return d;
}
extern "C" void* memcpy(void* d, const void* s, usize n) {
  u8* p = (u8*)d; const u8* q = (const u8*)s;
  while (n--) *p++ = *q++;
  return d;
}
enum {
  W          = 10,   // 필드 가로 (칸)
  VIS        = 20,   // 화면에 보이는 세로 (칸)
  HIDDEN     = 4,    // 천장 위 숨은 줄 — 스폰과 위쪽 월킥(-2칸)을 흡수한다
  H          = VIS + HIDDEN,  // 실제 배열 세로 = 24
  SPAWN_X    = 3,
  SPAWN_Y    = HIDDEN,        // 4x4 박스의 좌상단 = 보이는 필드의 맨 윗줄
                              // (숨은 4줄은 위로 밀어내는 월킥과 블록아웃 판정용 여유)

  DAS_MS     = 170,  // 좌우 키를 누르고 자동반복이 시작되기까지
  ARR_MS     = 40,   // 자동반복 1칸당 간격
  SOFT_DIV   = 20,   // 소프트드롭 = 중력의 20배
  LOCK_MS    = 500,  // 바닥에 닿은 뒤 굳기까지의 유예
  LOCK_RESET = 15,   // 유예를 되살릴 수 있는 최대 횟수

  GARBAGE    = 8,    // 가비지 줄의 색 인덱스 (조각 색 1~7 과 겹치지 않게)
  GARBAGE_CAP = 8,   // 한 번의 락에서 올라올 수 있는 최대 줄 수
                     // — 상한이 없으면 20줄이 한꺼번에 솟아 즉사한다
};

// 액션 코드 (JS 와 공유하는 유일한 "프로토콜")
enum {
  ACT_LEFT = 0, ACT_RIGHT = 1, ACT_SOFT = 2, ACT_CW = 3,
  ACT_CCW  = 4, ACT_HARD  = 5, ACT_HOLD = 6, ACT_PAUSE = 7, ACT_FLIP = 8,
};

// stats[] 배열의 인덱스 = JS 와 공유하는 두 번째 프로토콜
enum {
  ST_SCORE = 0, ST_LINES, ST_LEVEL, ST_COMBO, ST_B2B, ST_STATE,
  ST_HOLD, ST_NEXT0, ST_NEXT1, ST_NEXT2, ST_NEXT3, ST_NEXT4,
  ST_CLEAR, ST_TSPIN, ST_GAIN, ST_PIECES, ST_ELAPSED, ST_GRAVITY,
  ST_PIECE, ST_ROT, ST_X, ST_Y, ST_GHOST, ST_EVENT, ST_ROWMASK,
  ST_PERFECT, ST_LOCKPCT,
  ST_ATTACK,        // 이번 락으로 상대에게 보낸 줄 수 (상쇄 후)
  ST_PENDING,       // 아직 올라오지 않고 대기 중인 가비지 줄 수
  ST_GARBAGE_RECV,  // 지금까지 실제로 밀려 올라온 누적 줄 수
  ST_COUNT
};
enum { STATE_PLAY = 0, STATE_OVER = 1, STATE_PAUSE = 2 };
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
// 조각 데이터 전체가 7×4×2 = 56바이트다. 캐시에 통째로 들어간다.
static const u16 SHAPES[7][4] = {
  { 0x00F0, 0x2222, 0x0F00, 0x4444 },  // 0 I — 하늘색
  { 0x0071, 0x0226, 0x0470, 0x0322 },  // 1 J — 파랑
  { 0x0074, 0x0622, 0x0170, 0x0223 },  // 2 L — 주황
  { 0x0066, 0x0066, 0x0066, 0x0066 },  // 3 O — 노랑 (회전해도 그대로)
  { 0x0036, 0x0462, 0x0360, 0x0231 },  // 4 S — 초록
  { 0x0072, 0x0262, 0x0270, 0x0232 },  // 5 T — 보라
  { 0x0063, 0x0264, 0x0630, 0x0132 },  // 6 Z — 빨강
};
// 회전이 벽/블록에 막히면 그냥 실패시키지 않고, 정해진 순서로 5개 위치를 시도한다.
// 이 표가 곧 "현대 테트리스의 손맛"이다. T스핀도 여기서 태어난다.
//
// 원본 SRS 표는 y축이 위로 +1 이다. 우리 좌표계는 아래로 +1 이므로
// 적용할 때 y 부호를 뒤집는다 (아래 try_rotate 참고).
//
// [from_rotation][시도순서][x, y]
static const i8 KICK_JLSTZ_CW[4][5][2] = {
  {{0,0},{-1,0},{-1,+1},{0,-2},{-1,-2}},   // 0→1
  {{0,0},{+1,0},{+1,-1},{0,+2},{+1,+2}},   // 1→2
  {{0,0},{+1,0},{+1,+1},{0,-2},{+1,-2}},   // 2→3
  {{0,0},{-1,0},{-1,-1},{0,+2},{-1,+2}},   // 3→0
};
static const i8 KICK_JLSTZ_CCW[4][5][2] = {
  {{0,0},{+1,0},{+1,+1},{0,-2},{+1,-2}},   // 0→3
  {{0,0},{+1,0},{+1,-1},{0,+2},{+1,+2}},   // 1→0
  {{0,0},{-1,0},{-1,+1},{0,-2},{-1,-2}},   // 2→1
  {{0,0},{-1,0},{-1,-1},{0,+2},{-1,+2}},   // 3→2
};
// I 조각은 회전축이 칸 경계에 있어서 전용 표를 쓴다.
static const i8 KICK_I_CW[4][5][2] = {
  {{0,0},{-2,0},{+1,0},{-2,-1},{+1,+2}},   // 0→1
  {{0,0},{-1,0},{+2,0},{-1,+2},{+2,-1}},   // 1→2
  {{0,0},{+2,0},{-1,0},{+2,+1},{-1,-2}},   // 2→3
  {{0,0},{+1,0},{-2,0},{+1,-2},{-2,+1}},   // 3→0
};
static const i8 KICK_I_CCW[4][5][2] = {
  {{0,0},{-1,0},{+2,0},{-1,+2},{+2,-1}},   // 0→3
  {{0,0},{+2,0},{-1,0},{+2,+1},{-1,-2}},   // 1→0
  {{0,0},{+1,0},{-2,0},{+1,-2},{-2,+1}},   // 2→1
  {{0,0},{-2,0},{+1,0},{-2,-1},{+1,+2}},   // 3→2
};
// 가이드라인 공식: (0.8 - 0.007*(level-1))^(level-1) 초/칸.
// pow() 는 libm 에 있고 우리는 -nostdlib 다. 그래서 미리 계산해 ms 단위로 굳혔다.
// 부동소수점 런타임 의존성 0, 결정론 100%, 조회 O(1).
static const u16 GRAVITY_MS[21] = {
  1000,                                    // [0] 미사용(레벨은 1부터)
  1000, 793, 618, 473, 355, 262, 190, 135, // 레벨 1~8
    94,  64,  43,  28,  18,  11,   7,   4, // 레벨 9~16
     3,   2,   1,   1,                     // 레벨 17~20
};
// 힙이 없으니 상태는 모두 여기 있다. 이 블록이 곧 세이브 파일이다.
static u8  board[H * W];        // 굳은 블록: 0=빈칸, 1~7=조각 색
static u8  cells[VIS * W];      // JS 가 읽는 화면 버퍼(굳은 블록만)
static u8  overlay[VIS * W];    // JS 가 읽는 오버레이: 1~7=현재조각, 8~14=고스트
static int stats[ST_COUNT];     // JS 가 읽는 숫자 상태

static int cur_piece, cur_rot, cur_x, cur_y;
static int hold_piece, hold_used;
static int bag[7], bag_idx;
static int next_q[7];           // 다음 조각 큐(앞 5개만 노출)
static u32 rng_state;

static int grav_acc;            // 중력 누적 ms
static int lock_timer, lock_resets, grounded;
static int das_dir, das_timer, arr_timer, soft_held;
static int last_was_rot, last_kick;
static int event_id;
static int pending_garbage;     // 상대가 보냈지만 아직 필드에 올라오지 않은 줄
// rand() 가 없다. 그런데 사실 필요도 없다 — 13줄이면 충분하다.
static u32 rnd() {
  rng_state ^= rng_state << 13;
  rng_state ^= rng_state >> 17;
  rng_state ^= rng_state << 5;
  return rng_state;
}
// 7-bag: 7종을 한 봉지에 넣고 섞어서 하나씩 꺼낸다.
// "S/Z만 10번 연속" 같은 사고가 원천적으로 불가능해진다.
// 최악 대기: 같은 조각 사이 최대 12개 (봉지 앞 + 다음 봉지 뒤).
static void refill_bag() {
  for (int i = 0; i < 7; i++) bag[i] = i;
  for (int i = 6; i > 0; i--) {           // Fisher-Yates
    int j = (int)(rnd() % (u32)(i + 1));
    int t = bag[i]; bag[i] = bag[j]; bag[j] = t;
  }
  bag_idx = 0;
}
static int pull_bag() {
  if (bag_idx >= 7) refill_bag();
  return bag[bag_idx++];
}
// (piece, rot) 모양을 (px, py) 에 놓았을 때 겹치는가?
//  * 좌우/바닥 밖  → 충돌
//  * 천장 위(y<0)  → 충돌 아님 (조각이 위로 삐져나오는 건 합법)
//  * 굳은 블록  → 충돌
static int collide(int piece, int rot, int px, int py) {
  u16 m = SHAPES[piece][rot];
  for (int i = 0; i < 16; i++) {
    if (!(m & (1 << i))) continue;
    int bx = px + (i & 3);
    int by = py + (i >> 2);
    if (bx < 0 || bx >= W || by >= H) return 1;
    if (by < 0) continue;
    if (board[by * W + bx]) return 1;
  }
  return 0;
}

// 고스트(착지 예상 위치) 계산: 부딪힐 때까지 내린다.
static int ghost_y() {
  int y = cur_y;
  while (!collide(cur_piece, cur_rot, cur_x, y + 1)) y++;
  return y;
}
static void fill_queue() {
  for (int i = 0; i < 7; i++) next_q[i] = pull_bag();
}
static void spawn_next() {
  cur_piece = next_q[0];
  for (int i = 0; i < 6; i++) next_q[i] = next_q[i + 1];
  next_q[6] = pull_bag();

  cur_rot = 0;
  cur_x = SPAWN_X;
  cur_y = SPAWN_Y;
  hold_used = 0;
  grounded = 0; lock_timer = 0; lock_resets = 0;
  last_was_rot = 0; last_kick = 0;
  stats[ST_PIECES]++;

  // 블록아웃: 스폰 위치가 이미 막혔다 → 게임 오버
  if (collide(cur_piece, cur_rot, cur_x, cur_y))
    stats[ST_STATE] = STATE_OVER;
}
static int try_move(int dx, int dy) {
  if (collide(cur_piece, cur_rot, cur_x + dx, cur_y + dy)) return 0;
  cur_x += dx; cur_y += dy;
  last_was_rot = 0;
  return 1;
}

// 회전 시도. dir: +1 = 시계, -1 = 반시계.
// 5개 킥 후보를 순서대로 밀어 보고 처음 성공한 곳에 앉힌다.
static int try_rotate(int dir) {
  int from = cur_rot;
  int to   = (cur_rot + (dir > 0 ? 1 : 3)) & 3;
  // I 조각만 전용 표. O 조각은 어차피 모양이 같아서 첫 후보 (0,0) 에서 바로 성공한다.
  const i8 (*tbl)[2] = (cur_piece == 0)
      ? ((dir > 0) ? KICK_I_CW[from]     : KICK_I_CCW[from])
      : ((dir > 0) ? KICK_JLSTZ_CW[from] : KICK_JLSTZ_CCW[from]);

  for (int k = 0; k < 5; k++) {
    int nx = cur_x + tbl[k][0];
    int ny = cur_y - tbl[k][1];        // ← y 부호 반전 (표는 위가 +)
    if (!collide(cur_piece, to, nx, ny)) {
      cur_rot = to; cur_x = nx; cur_y = ny;
      last_was_rot = 1;                // T스핀 판정에 쓰인다
      last_kick = k;                   // 5번째(k==4) 킥은 항상 정식 T스핀
      if (grounded && lock_resets < LOCK_RESET) { lock_timer = 0; lock_resets++; }
      return 1;
    }
  }
  return 0;
}
// T 조각의 중심(cx,cy) 기준 네 대각 코너 중,
//   * "앞" 두 코너 = T 가 가리키는 방향 쪽 두 개
//   * 앞 2개 + 뒤 1개 이상이 막힘 → 정식 T스핀
//  * 앞 1개 + 뒤 2개가 막힘  → 미니 T스핀
//   * 단, 5번째 킥으로 들어갔으면 무조건 정식
// 반환: 0=없음 1=미니 2=정식
static int filled(int x, int y) {
  if (x < 0 || x >= W || y >= H) return 1;   // 벽/바닥은 "막힌 것"으로 센다
  if (y < 0) return 0;
  return board[y * W + x] != 0;
}
static int detect_tspin() {
  if (cur_piece != 5 || !last_was_rot) return 0;
  int cx = cur_x + 1, cy = cur_y + 1;
  // 회전 상태별 "앞쪽" 두 코너의 오프셋
  static const i8 FRONT[4][4] = {
    {-1,-1, +1,-1},   // rot0: 위쪽을 가리킴 → 위 두 코너
    {+1,-1, +1,+1},   // rot1: 오른쪽
    {-1,+1, +1,+1},   // rot2: 아래
    {-1,-1, -1,+1},   // rot3: 왼쪽
  };
  static const i8 BACK[4][4] = {
    {-1,+1, +1,+1}, {-1,-1, -1,+1}, {-1,-1, +1,-1}, {+1,-1, +1,+1},
  };
  int f = filled(cx + FRONT[cur_rot][0], cy + FRONT[cur_rot][1])
        + filled(cx + FRONT[cur_rot][2], cy + FRONT[cur_rot][3]);
  int b = filled(cx + BACK[cur_rot][0],  cy + BACK[cur_rot][1])
        + filled(cx + BACK[cur_rot][2],  cy + BACK[cur_rot][3]);
  if (f == 2 && b >= 1) return 2;
  if (f == 1 && b == 2) return (last_kick == 4) ? 2 : 1;
  return 0;
}
// ── 대전 규칙 1: 공격 표 ────────────────────────────────────────────
// 줄을 지우면 상대 필드 바닥에 그만큼의 "가비지"를 밀어 넣는다.
// 표 자체는 현대 대전 테트리스의 사실상 표준을 따랐다.
//   싱글 0 / 더블 1 / 트리플 2 / 테트리스 4
//   T스핀 싱글 2 / 더블 4 / 트리플 6, 미니 T스핀 0 / 미니 더블 1
//   Back-to-Back +1, 콤보 보너스 표, 퍼펙트 클리어 +10
// 싱글이 0 인 게 핵심이다 — 한 줄씩 지우는 플레이는 공격이 되지 않는다.
static const int COMBO_ATK[13] = { 0,0,1,1,1,2,2,3,3,4,4,4,5 };
static int attack_for(int n, int tsp, int b2b_before, int combo, int perfect) {
  if (n <= 0) return 0;
  static const int PLAIN[5] = { 0, 0, 1, 2, 4 };   // -, 싱글, 더블, 트리플, 테트리스
  static const int TSPIN[5] = { 0, 2, 4, 6, 6 };   // 정식 T스핀
  static const int MINI [5] = { 0, 0, 1, 1, 1 };   // 미니 T스핀
  int atk = (tsp == 2) ? TSPIN[n] : (tsp == 1) ? MINI[n] : PLAIN[n];

  // "어려운 클리어"의 정의는 점수 규칙과 같다 — 테트리스 또는 T스핀.
  // b2b_before 는 이번 락이 stats[ST_B2B] 를 덮어쓰기 *전*의 값이어야 한다.
  int difficult = (tsp > 0) || (n == 4);
  if (difficult && b2b_before) atk += 1;

  int c = combo; if (c < 0) c = 0; if (c > 12) c = 12;
  atk += COMBO_ATK[c];
  if (perfect) atk += 10;
  return atk;
}

// ── 대전 규칙 2: 가비지 밀어 올리기 ──────────────────────────────────
// n 줄을 바닥에서 밀어 올린다. hole 은 뚫려 있는 칸의 x.
// 한 번에 올라오는 n 줄은 같은 구멍을 공유한다("클린 가비지") — 구멍이 매 줄
// 달라지면 사실상 복구가 불가능해서 대전이 성립하지 않는다.
// hole < 0 이면 이 인스턴스의 RNG 가 고른다.
// 천장 밖으로 밀려난 줄은 그냥 사라진다(배열이 곧 필드 전체이므로).
static void push_rows(int n, int hole) {
  if (n <= 0) return;
  if (n > H) n = H;
  if (hole < 0 || hole >= W) hole = (int)(rnd() % (u32)W);

  for (int y = 0; y < H - n; y++)
    memcpy(&board[y * W], &board[(y + n) * W], W);
  for (int y = H - n; y < H; y++) {
    memset(&board[y * W], GARBAGE, W);
    board[y * W + hole] = 0;
  }
  stats[ST_GARBAGE_RECV] += n;
}

// 가이드라인 점수표를 그대로 구현한다.
//  싱글 100 / 더블 300 / 트리플 500 / 테트리스 800  (×레벨)
//   T스핀 0/1/2/3줄 = 400/800/1200/1600, 미니 = 100/200/400
//   Back-to-Back(어려운 클리어 연속) ×1.5
//   콤보 50 × 콤보수 × 레벨
//   퍼펙트 클리어 보너스 (필드를 완전히 비움)
static int clear_lines() {
  int n = 0;
  u32 mask = 0;
  for (int y = H - 1; y >= 0; y--) {
    int full = 1;
    for (int x = 0; x < W; x++) if (!board[y * W + x]) { full = 0; break; }
    if (!full) continue;
    n++;
    if (y >= HIDDEN) mask |= 1u << (y - HIDDEN);
    for (int yy = y; yy > 0; yy--)                 // 위 줄들을 한 칸씩 끌어내린다
      memcpy(&board[yy * W], &board[(yy - 1) * W], W);
    memset(&board[0], 0, W);
    y++;                                           // 같은 y 를 다시 검사
  }
  stats[ST_ROWMASK] = (int)mask;
  return n;
}

static void lock_piece() {
  int tsp = detect_tspin();

  u16 m = SHAPES[cur_piece][cur_rot];
  for (int i = 0; i < 16; i++) {
    if (!(m & (1 << i))) continue;
    int bx = cur_x + (i & 3), by = cur_y + (i >> 2);
    if (by >= 0 && by < H && bx >= 0 && bx < W)
      board[by * W + bx] = (u8)(cur_piece + 1);
  }

  int n = clear_lines();
  int lvl = stats[ST_LEVEL];
  int base = 0, difficult = 0;
  int b2b_before = stats[ST_B2B];   // 아래에서 덮어쓰기 전에 붙잡아 둔다
  int perfect = 0;

  if (tsp == 2)       { static const int T[5] = {400, 800, 1200, 1600, 1600}; base = T[n]; difficult = (n > 0); }
  else if (tsp == 1)  { static const int T[5] = {100, 200,  400,  400,  400}; base = T[n]; difficult = (n > 0); }
  else                { static const int L[5] = {  0, 100,  300,  500,  800}; base = L[n]; difficult = (n == 4); }

  int gain = base * lvl;

  if (n > 0) {
    if (difficult && stats[ST_B2B]) gain = gain * 3 / 2;    // Back-to-Back ×1.5
    stats[ST_B2B]   = difficult ? 1 : 0;                    // 어려운 클리어면 다음을 위해 유지
    stats[ST_COMBO] = stats[ST_COMBO] + 1;                  // -1 → 0(첫 클리어) → 1 → 2 ...
    gain += 50 * stats[ST_COMBO] * lvl;
    stats[ST_LINES] += n;
    stats[ST_LEVEL]  = 1 + stats[ST_LINES] / 10;
    if (stats[ST_LEVEL] > 20) stats[ST_LEVEL] = 20;

    int empty = 1;                                          // 퍼펙트 클리어?
    for (int i = 0; i < H * W; i++) if (board[i]) { empty = 0; break; }
    if (empty) { gain += 1000 * lvl; stats[ST_PERFECT]++; perfect = 1; }
  } else {
    stats[ST_COMBO] = -1;                                   // 콤보 끊김
  }

  stats[ST_SCORE] += gain;
  stats[ST_GAIN]   = gain;
  stats[ST_CLEAR]  = n;
  stats[ST_TSPIN]  = tsp;
  stats[ST_GRAVITY]= GRAVITY_MS[stats[ST_LEVEL]];

  // ── 대전: 공격 계산 → 상쇄 → 가비지 적용 ────────────────────────
  // 순서가 규칙의 전부다. 내가 보낼 공격은 먼저 *내* 대기줄을 지우고(상쇄),
  // 남은 만큼만 상대에게 간다. 그래서 맞받아치면 가비지가 올라오지 않는다.
  int atk = attack_for(n, tsp, b2b_before, stats[ST_COMBO], perfect);
  int cancel = (atk < pending_garbage) ? atk : pending_garbage;
  pending_garbage -= cancel;
  atk             -= cancel;
  stats[ST_ATTACK] = atk;

  // 대기 중인 가비지는 "줄을 못 지운 락"에서만 실제로 솟아오른다.
  // 이 유예가 없으면 상쇄할 기회 자체가 없다.
  if (n == 0 && pending_garbage > 0) {
    int k = (pending_garbage < GARBAGE_CAP) ? pending_garbage : GARBAGE_CAP;
    push_rows(k, -1);
    pending_garbage -= k;
  }
  stats[ST_PENDING] = pending_garbage;

  event_id++;
  stats[ST_EVENT]  = event_id;

  spawn_next();
}
static void step_down() {
  try_move(0, 1);                       // 실패해도 괜찮다 — 착지 판정은 ts_update 가 매 프레임 한다
}
static void hard_drop() {
  int d = 0;
  while (try_move(0, 1)) d++;
  stats[ST_SCORE] += d * 2;             // 하드드롭 1칸당 2점
  lock_piece();
}
static void do_hold() {
  if (hold_used) return;                // 조각당 1회 제한 — 무한 스왑 방지
  int p = hold_piece;
  hold_piece = cur_piece;
  stats[ST_HOLD] = hold_piece;
  if (p < 0) {
    spawn_next();
  } else {
    cur_piece = p; cur_rot = 0; cur_x = SPAWN_X; cur_y = SPAWN_Y;
    grounded = 0; lock_timer = 0; lock_resets = 0; last_was_rot = 0;
    if (collide(cur_piece, cur_rot, cur_x, cur_y)) stats[ST_STATE] = STATE_OVER;
  }
  hold_used = 1;
}
static void build_view() {
  for (int y = 0; y < VIS; y++)
    memcpy(&cells[y * W], &board[(y + HIDDEN) * W], W);
  memset(overlay, 0, sizeof(overlay));

  if (stats[ST_STATE] == STATE_OVER) return;

  int gy = ghost_y();
  u16 m = SHAPES[cur_piece][cur_rot];
  for (int i = 0; i < 16; i++) {                 // 고스트 먼저(현재 조각이 덮어씀)
    if (!(m & (1 << i))) continue;
    int bx = cur_x + (i & 3), by = gy + (i >> 2) - HIDDEN;
    if (by >= 0 && by < VIS && bx >= 0 && bx < W)
      overlay[by * W + bx] = (u8)(cur_piece + 8);
  }
  for (int i = 0; i < 16; i++) {
    if (!(m & (1 << i))) continue;
    int bx = cur_x + (i & 3), by = cur_y + (i >> 2) - HIDDEN;
    if (by >= 0 && by < VIS && bx >= 0 && bx < W)
      overlay[by * W + bx] = (u8)(cur_piece + 1);
  }
  stats[ST_PIECE] = cur_piece;
  stats[ST_ROT]   = cur_rot;
  stats[ST_X]     = cur_x;
  stats[ST_Y]     = cur_y - HIDDEN;
  stats[ST_GHOST] = gy - HIDDEN;
  for (int i = 0; i < 5; i++) stats[ST_NEXT0 + i] = next_q[i];
  stats[ST_LOCKPCT] = grounded ? (lock_timer * 100 / LOCK_MS) : 0;
}
EXPORT(ts_init) void ts_init(u32 seed) {
  rng_state = seed ? seed : 0x9E3779B9u;
  memset(board, 0, sizeof(board));
  memset(stats, 0, sizeof(stats));
  stats[ST_LEVEL] = 1;
  stats[ST_COMBO] = -1;
  stats[ST_HOLD]  = -1;
  stats[ST_STATE] = STATE_PLAY;
  stats[ST_GRAVITY] = GRAVITY_MS[1];
  hold_piece = -1; hold_used = 0;
  grav_acc = 0; lock_timer = 0; lock_resets = 0; grounded = 0;
  das_dir = 0; das_timer = 0; arr_timer = 0; soft_held = 0;
  event_id = 0;
  pending_garbage = 0;
  bag_idx = 7;
  fill_queue();
  spawn_next();
  build_view();
}
// dt_ms 만큼 시간을 진행시킨다. JS 의 rAF 루프가 매 프레임 호출한다.
EXPORT(ts_update) void ts_update(int dt_ms) {
  if (stats[ST_STATE] != STATE_PLAY) return;
  if (dt_ms > 100) dt_ms = 100;          // 탭 전환 후 거대한 dt 방지
  stats[ST_ELAPSED] += dt_ms;

  // 1) DAS/ARR — 좌우 자동반복
  if (das_dir) {
    das_timer += dt_ms;
    if (das_timer >= DAS_MS) {
      arr_timer += dt_ms;
      while (arr_timer >= ARR_MS) {
        arr_timer -= ARR_MS;
        if (try_move(das_dir, 0) && grounded && lock_resets < LOCK_RESET) {
          lock_timer = 0; lock_resets++;
        }
      }
    }
  }

  // 2) 중력 — 소프트드롭 중이면 20배 빠르게
  int g = GRAVITY_MS[stats[ST_LEVEL]];
  if (soft_held) { g = g / SOFT_DIV; if (g < 1) g = 1; }
  grav_acc += dt_ms;
  while (grav_acc >= g) {
    grav_acc -= g;
    int before = cur_y;
    step_down();
    if (soft_held && cur_y > before) stats[ST_SCORE] += 1;   // 소프트드롭 1칸 1점
    if (stats[ST_STATE] != STATE_PLAY) return;
  }

  // 3) 락다운 — "닿아 있는가"를 중력 틱이 아니라 매 프레임 검사한다.
  //    중력 틱에서만 검사하면 레벨1(1000ms/칸)에서 착지 후 최대 1초를 그냥 서 있게 된다.
  if (collide(cur_piece, cur_rot, cur_x, cur_y + 1)) {
    grounded = 1;
    lock_timer += dt_ms;
    if (lock_timer >= LOCK_MS) { lock_piece(); grav_acc = 0; }
  } else {
    grounded = 0; lock_timer = 0;       // 옆으로 빠져나가 다시 공중에 떴다
  }
  build_view();
}
EXPORT(ts_press) void ts_press(int act) {
  if (act == ACT_PAUSE) {
    if (stats[ST_STATE] == STATE_PLAY)      stats[ST_STATE] = STATE_PAUSE;
    else if (stats[ST_STATE] == STATE_PAUSE) stats[ST_STATE] = STATE_PLAY;
    return;
  }
  if (stats[ST_STATE] != STATE_PLAY) return;

  switch (act) {
    case ACT_LEFT:  case ACT_RIGHT: {
      int d = (act == ACT_LEFT) ? -1 : +1;
      das_dir = d; das_timer = 0; arr_timer = 0;
      if (try_move(d, 0) && grounded && lock_resets < LOCK_RESET) { lock_timer = 0; lock_resets++; }
      break;
    }
    case ACT_SOFT: soft_held = 1; grav_acc = 0; break;
    case ACT_CW:   try_rotate(+1); break;
    case ACT_CCW:  try_rotate(-1); break;
    case ACT_FLIP: try_rotate(+1); try_rotate(+1); break;   // 180도
    case ACT_HARD: hard_drop(); break;
    case ACT_HOLD: do_hold(); break;
  }
  build_view();
}

EXPORT(ts_release) void ts_release(int act) {
  if (act == ACT_LEFT  && das_dir < 0) das_dir = 0;
  if (act == ACT_RIGHT && das_dir > 0) das_dir = 0;
  if (act == ACT_SOFT) soft_held = 0;
}
// 포인터 반환 함수들 = JS 가 선형 메모리에서 어디를 봐야 하는지 알려 준다.
// 굳은 블록의 원본 배열(H×W = 24×10). 위 4줄은 숨은 줄이다.
// 세이브/로드, 리플레이, 그리고 테스트에서 특정 상황을 심는 데 쓴다.
// 심판(JS)이 상대의 ST_ATTACK 을 읽어 이쪽에 쌓아 준다. 규칙은 전부 C++ 안에 있고
// JS 는 두 인스턴스 사이에서 숫자 하나를 옮기는 배달부일 뿐이다.
EXPORT(ts_queue_garbage) void ts_queue_garbage(int n) {
  if (n <= 0) return;
  pending_garbage += n;
  stats[ST_PENDING] = pending_garbage;
}
// 대기열을 거치지 않고 지금 당장 밀어 올린다 — 테스트와 데모용.
// hole_x < 0 이면 RNG 가 고른다.
EXPORT(ts_garbage) void ts_garbage(int n, int hole_x) {
  push_rows(n, hole_x);
  // 진행 중인 조각이 솟아오른 줄에 파묻히면 위로 빼 준다.
  while (collide(cur_piece, cur_rot, cur_x, cur_y) && cur_y > -HIDDEN) cur_y--;
  if (collide(cur_piece, cur_rot, cur_x, cur_y)) stats[ST_STATE] = STATE_OVER;
  build_view();
}

// 테스트·데모 전용 훅: 지금 조각을 지정한 종류로 바꿔 스폰 상태로 되돌린다.
// 게임 로직은 이 함수를 절대 호출하지 않는다. 특정 상황(T스핀 자리, 테트리스
// 자리)을 재현하려면 "이 조각이 지금 나와야 한다"를 강제할 방법이 필요하다.
EXPORT(ts_set_piece) void ts_set_piece(int piece) {
  if (piece < 0 || piece > 6) return;
  cur_piece = piece; cur_rot = 0; cur_x = SPAWN_X; cur_y = SPAWN_Y;
  hold_used = 0; grounded = 0; lock_timer = 0; lock_resets = 0;
  last_was_rot = 0; last_kick = 0;
  if (collide(cur_piece, cur_rot, cur_x, cur_y)) stats[ST_STATE] = STATE_OVER;
  build_view();
}

EXPORT(ts_board)   int ts_board()   { return (int)(usize)board;   }
EXPORT(ts_rows)    int ts_rows()    { return (H << 16) | HIDDEN;  }
EXPORT(ts_cells)   int ts_cells()   { return (int)(usize)cells;   }
EXPORT(ts_overlay) int ts_overlay() { return (int)(usize)overlay; }
EXPORT(ts_stats)   int ts_stats()   { return (int)(usize)stats;   }
EXPORT(ts_dims)    int ts_dims()    { return (W << 16) | VIS;     }
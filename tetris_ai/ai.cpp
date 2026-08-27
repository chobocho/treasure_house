// ai.cpp — 부 1 의 테트리스 코어 위에 얹는 "판을 읽고 한 수를 고르는" 층.
//
// 설계 원칙 세 가지:
//   1. 게임 규칙은 tetris.cpp 안에만 있다. 여기서 규칙을 다시 쓰지 않는다.
//   2. 탐색은 board 의 *사본* 위에서만 한다. 진행 중인 판을 절대 건드리지 않는다.
//      (부 1 의 어트랙트 봇이 못 했던 게 바로 이거다)
//   3. 가중치 8개는 JS 가 선형 메모리에 직접 써 넣는다. 재컴파일 없이 AI가 바뀐다.
#include "tetris.cpp"

// 보드 평가에 쓰는 특징 8가지. 순서가 곧 weights[] 의 순서다 — JS 와의 세 번째 프로토콜.
enum {
  F_LINES,  // 이 수로 지워지는 줄 수  (많을수록 좋다)
  F_AGG,  // 열 높이의 총합  (낮을수록 좋다)
  F_HOLES,  // 덮인 빈칸 개수  (적을수록 좋다)
  F_BUMP,  // 이웃한 열 높이차의 총합  (작을수록 좋다)
  F_WELLS,  // 우물 깊이의 누적 비용  (작을수록 좋다)
  F_ROWT,  // 행 전이 수 (Dellacherie)  (작을수록 좋다)
  F_COLT,  // 열 전이 수 (Dellacherie)  (작을수록 좋다)
  F_LAND,  // 조각이 놓인 높이  (낮을수록 좋다)
  F_COUNT = 8
};

static float weights[F_COUNT];      // JS 가 Float32Array 로 덮어쓴다
static float last_feat[F_COUNT];    // 마지막으로 계산한 특징 벡터 (시각화·테스트용)
static u8    sim[H * W];            // 탐색 전용 보드 사본 — 240바이트, 스택 대신 정적

// ── 사본 위에서 도는 규칙 3종 ────────────────────────────────────────
// collide/clear_lines 와 같은 일을 하지만 전역 board 대신 인자로 받은 배열을 본다.
// "같은 코드를 두 번 쓰는 것"처럼 보이지만, 원본을 포인터화하면 부 1 의 핫패스가
// 느려진다. 규칙의 진짜 사본은 여기 세 함수뿐이고 나머지는 전부 원본을 쓴다.
static int sim_collide(const u8* b, int piece, int rot, int px, int py) {
  u16 m = SHAPES[piece][rot];
  for (int i = 0; i < 16; i++) {
    if (!(m & (1 << i))) continue;
    int bx = px + (i & 3);
    int by = py + (i >> 2);
    if (bx < 0 || bx >= W || by >= H) return 1;
    if (by < 0) continue;
    if (b[by * W + bx]) return 1;
  }
  return 0;
}

// (rot, x) 로 스폰 줄에서 곧장 떨어뜨렸을 때 멈추는 y. 스폰 줄이 막혀 있으면 -1.
static int sim_drop(const u8* b, int piece, int rot, int x) {
  int y = SPAWN_Y;
  if (sim_collide(b, piece, rot, x, y)) return -1;
  while (!sim_collide(b, piece, rot, x, y + 1)) y++;
  return y;
}

// 스폰 자리(SPAWN_X)에서 목표 x 까지 스폰 줄을 따라 한 칸씩 미끄러질 수 있는가.
// AI가 고른 수를 나중에 *실제 키 입력*으로 재현해야 하므로, 도달 불가능한 자리를
// 후보에서 빼 둔다. 끼워 넣기(tuck)·스핀은 이 탐색의 범위 밖이다.
static int sim_reachable(const u8* b, int piece, int rot, int x) {
  if (sim_collide(b, piece, rot, SPAWN_X, SPAWN_Y)) return 0;
  int step = (x > SPAWN_X) ? 1 : -1;
  for (int cx = SPAWN_X; cx != x; cx += step)
    if (sim_collide(b, piece, rot, cx + step, SPAWN_Y)) return 0;
  return 1;
}

static void sim_place(u8* b, int piece, int rot, int x, int y) {
  u16 m = SHAPES[piece][rot];
  for (int i = 0; i < 16; i++) {
    if (!(m & (1 << i))) continue;
    int bx = x + (i & 3), by = y + (i >> 2);
    if (by >= 0 && by < H && bx >= 0 && bx < W) b[by * W + bx] = (u8)(piece + 1);
  }
}

static int sim_clear(u8* b) {
  int n = 0;
  for (int y = H - 1; y >= 0; y--) {
    int full = 1;
    for (int x = 0; x < W; x++) if (!b[y * W + x]) { full = 0; break; }
    if (!full) continue;
    n++;
    for (int yy = y; yy > 0; yy--) memcpy(&b[yy * W], &b[(yy - 1) * W], W);
    memset(&b[0], 0, W);
    y++;                       // 끌어내렸으니 같은 y 를 다시 본다
  }
  return n;
}

// 조각 모양의 가장 아래 행 인덱스(0~3). 착지 높이 계산에 쓴다.
static int shape_bottom(int piece, int rot) {
  u16 m = SHAPES[piece][rot];
  int r = 0;
  for (int i = 0; i < 16; i++) if (m & (1 << i)) { int y = i >> 2; if (y > r) r = y; }
  return r;
}

// ── 특징 추출 ────────────────────────────────────────────────────────
// b        : 줄을 지운 *뒤*의 보드
// lines    : 이 수로 지워진 줄 수
// land_h   : 조각 맨 아랫줄의 바닥 기준 높이 (바닥줄 = 1)
static void features(const u8* b, int lines, int land_h, float* f) {
  int h[W];
  int holes = 0;
  for (int x = 0; x < W; x++) {
    int y = 0;
    while (y < H && !b[y * W + x]) y++;
    h[x] = H - y;                                  // 열 높이 = 가장 높은 블록까지
    for (int yy = y + 1; yy < H; yy++) if (!b[yy * W + x]) holes++;
  }

  int agg = 0, bump = 0, wells = 0;
  for (int x = 0; x < W; x++) agg += h[x];
  for (int x = 0; x + 1 < W; x++) { int d = h[x] - h[x + 1]; bump += (d < 0) ? -d : d; }
  for (int x = 0; x < W; x++) {
    // 양옆(벽은 천장 높이로 친다)보다 낮게 파인 만큼이 우물이다.
    int l = (x == 0)     ? H : h[x - 1];
    int r = (x == W - 1) ? H : h[x + 1];
    int m = (l < r) ? l : r;
    int d = m - h[x];
    if (d > 0) wells += d * (d + 1) / 2;           // 깊이 d 의 비용 1+2+…+d
  }

  // 행/열 전이: 채움↔빈칸이 뒤집히는 횟수. 벽과 바닥은 "채워진 것"으로 센다.
  // 울퉁불퉁하고 구멍 많은 판일수록 커진다 — 높이만으로는 안 보이는 결을 잡아낸다.
  int rowt = 0;
  for (int y = 0; y < H; y++) {
    int prev = 1;                                   // 왼쪽 벽
    for (int x = 0; x < W; x++) { int c = b[y * W + x] ? 1 : 0; if (c != prev) rowt++; prev = c; }
    if (!prev) rowt++;                              // 오른쪽 벽
  }
  int colt = 0;
  for (int x = 0; x < W; x++) {
    int prev = 0;                                   // 천장 위는 비어 있다
    for (int y = 0; y < H; y++) { int c = b[y * W + x] ? 1 : 0; if (c != prev) colt++; prev = c; }
    if (!prev) colt++;                              // 바닥
  }

  f[F_LINES] = (float)lines;
  f[F_AGG]   = (float)agg;
  f[F_HOLES] = (float)holes;
  f[F_BUMP]  = (float)bump;
  f[F_WELLS] = (float)wells;
  f[F_ROWT]  = (float)rowt;
  f[F_COLT]  = (float)colt;
  f[F_LAND]  = (float)land_h;
}

static float score_of(const float* f) {
  float s = 0.f;
  for (int i = 0; i < F_COUNT; i++) s += weights[i] * f[i];
  return s;
}

// ── 1수 탐색 ─────────────────────────────────────────────────────────
// 후보 = (홀드 쓸까 말까) × (회전 4) × (x −3‥9) ≈ 최대 104개, 실제 유효한 건 30~80개.
// 결과는 정수 하나로 접어 반환한다:  (use_hold << 8) | (rot << 4) | (x + 3)
//   x 에 +3 을 더하는 건 −3 까지 가능한 좌표를 4비트 무부호로 담기 위해서다.
EXPORT(ai_plan) int ai_plan() {
  if (stats[ST_STATE] != STATE_PLAY) return -1;

  int best = -1;
  float best_s = 0.f;
  int   have = 0;
  float f[F_COUNT];

  for (int use_hold = 0; use_hold < 2; use_hold++) {
    int piece;
    if (!use_hold) {
      piece = cur_piece;
    } else {
      if (hold_used) continue;                      // 조각당 홀드 1회
      piece = (hold_piece < 0) ? next_q[0] : hold_piece;
    }
    for (int rot = 0; rot < 4; rot++) {
      if (rot > 0 && SHAPES[piece][rot] == SHAPES[piece][0]) continue;   // O 조각
      for (int x = -3; x < W; x++) {
        int y = sim_drop(board, piece, rot, x);
        if (y < 0) continue;
        if (!sim_reachable(board, piece, rot, x)) continue;

        memcpy(sim, board, sizeof(sim));
        sim_place(sim, piece, rot, x, y);
        int land_h = H - (y + shape_bottom(piece, rot));   // 바닥줄 = 1
        int lines  = sim_clear(sim);
        features(sim, lines, land_h, f);
        float s = score_of(f);

        if (!have || s > best_s) {
          have = 1; best_s = s;
          best = (use_hold << 8) | (rot << 4) | (x + 3);
          for (int i = 0; i < F_COUNT; i++) last_feat[i] = f[i];
        }
      }
    }
  }
  return best;
}

// 고른 수를 실제 판에 둔다. 규칙을 우회하지 않는다 —
// 홀드는 do_hold(), 낙하는 hard_drop() 을 그대로 쓴다.
EXPORT(ai_apply) void ai_apply(int packed) {
  if (packed < 0 || stats[ST_STATE] != STATE_PLAY) return;
  int x        = (packed        & 15) - 3;
  int rot      = (packed >> 4)  & 3;
  int use_hold = (packed >> 8)  & 1;

  if (use_hold) {
    do_hold();
    if (stats[ST_STATE] != STATE_PLAY) return;
  }
  if (!collide(cur_piece, rot, x, cur_y)) { cur_rot = rot; cur_x = x; }
  last_was_rot = 0; last_kick = 0;      // 회전으로 들어간 게 아니므로 T스핀 판정 없음
  hard_drop();
  build_view();
}

EXPORT(ai_step) int ai_step() {
  int p = ai_plan();
  if (p >= 0) ai_apply(p);
  return p;
}

static int play_attack;      // 직전 판이 누적한 공격 줄 수
static int play_placed;      // 직전 판이 실제로 놓은 조각 수

// 한 판을 끝까지(또는 max_pieces 개까지) 둔다. GA 의 적합도 함수가 이걸 부른다.
// every > 0 이면 그만큼 놓을 때마다 가비지 1줄이 예약된다 — "비가 새는 배" 모드.
// 왜 이게 필요한가: 가비지가 없으면 웬만한 가중치도 400조각을 안 죽고 버틴다.
// 전원이 만점을 받으면 GA 는 누가 더 나은지 구별할 수 없다(적합도 천장).
static int play_game(u32 seed, int max_pieces, int every) {
  ts_init(seed);
  play_attack = 0;
  play_placed = 0;
  while (stats[ST_STATE] == STATE_PLAY && play_placed < max_pieces) {
    if (every > 0 && play_placed > 0 && play_placed % every == 0) ts_queue_garbage(1);
    int p = ai_plan();
    if (p < 0) break;
    ai_apply(p);
    play_attack += stats[ST_ATTACK];
    play_placed++;
  }
  return stats[ST_LINES];
}
EXPORT(ai_play)      int ai_play(u32 seed, int max_pieces) { return play_game(seed, max_pieces, 0); }
EXPORT(ai_play_hard) int ai_play_hard(u32 seed, int max_pieces, int every) { return play_game(seed, max_pieces, every); }
EXPORT(ai_play_attack) int ai_play_attack() { return play_attack; }
EXPORT(ai_play_placed) int ai_play_placed() { return play_placed; }

// 지금 판을 그대로(조각을 놓지 않고) 평가한다 — "숫자를 눈으로 보는" 슬라이드용.
EXPORT(ai_eval_here) float ai_eval_here() {
  features(board, 0, 0, last_feat);
  return score_of(last_feat);
}

EXPORT(ai_weights_ptr)   int ai_weights_ptr()   { return (int)(usize)weights;   }
EXPORT(ai_features_ptr)  int ai_features_ptr()  { return (int)(usize)last_feat; }
EXPORT(ai_feature_count) int ai_feature_count() { return F_COUNT; }

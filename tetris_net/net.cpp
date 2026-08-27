// net.cpp — 2편의 AI 코어 위에 얹는 "여럿이 붙는 판"을 위한 층.
//
// 설계 원칙은 2편 ai.cpp 와 같다. 규칙은 아래층(tetris.cpp)에만 있고,
// 이 파일은 아래층을 **공개 익스포트로만** 부린다. 그래서 1·2편 소스는 한 줄도
// 고치지 않았다 — 그 두 덱에 실린 줄 번호가 그대로 살아 있어야 하기 때문이다.
//
// 1:1 이었던 2편과 이 층이 다른 점은 딱 셋이다.
//   1. 가비지가 "몇 줄"이 아니라 **덩어리 목록**이다 (누가 보냈나 · 구멍이 어디나 · 얼마나 묵었나)
//   2. 구멍 위치를 내 난수가 아니라 **서버가 정해서 내려준다** — 관전 화면이 8석 모두 같아야 하니까
//   3. 화면 전체를 초당 10번 남에게 보내야 하므로 **런렝스로 접는 익스포트**가 있다
#include "../tetris_ai/ai.cpp"

enum {
  NG_MAXQ  = 24,        // 대기 덩어리 상한. 넘으면 마지막 덩어리에 합쳐 넣는다
  NG_SNAP  = VIS * W,   // 스냅샷 최대 바이트 수 (전부 런길이 1인 최악)
  NG_DELAY = 900,       // 대기열이 이만큼 묵으면 줄을 지웠어도 솟아오른다
};

// 가비지 덩어리 하나. JS 가 Int32Array 로 통째로 읽어 대기 게이지를 그린다.
struct Chunk { int n; int from; int hole; int age; };

static Chunk ngq[NG_MAXQ];
static int   ngq_n;
static int   ng_delay;
static int   ng_cap;
static int   ng_out;          // 아직 서버로 보내지 않은 공격 줄 수 (상쇄를 마친 값)
static int   ng_src;          // 마지막으로 내 판에 줄을 밀어 올린 좌석 — 막타 귀속용
static u8    ng_snap[NG_SNAP];

static void ngq_pop() {
  for (int i = 1; i < ngq_n; i++) ngq[i - 1] = ngq[i];
  if (ngq_n > 0) ngq_n--;
}
static void ng_sync_pending() {
  int t = 0;
  for (int i = 0; i < ngq_n; i++) t += ngq[i].n;
  stats[ST_PENDING] = t;
}

// ── 락 한 번에 일어나는 일 전부 ──────────────────────────────────────
// 순서가 규칙이다. 2편과 같은 순서지만 대상이 "숫자 하나"에서 "덩어리 목록"으로 바뀌었다.
//   1) 내가 낸 공격으로 내 대기열을 앞에서부터 깎는다 (상쇄)
//   2) 남은 공격은 서버로 보낼 몫으로 쌓아 둔다
//   3) 줄을 못 지웠거나 대기열이 묵었으면, 앞에서부터 cap 줄까지 밀어 올린다
static void ng_on_lock() {
  int atk = stats[ST_ATTACK];

  while (atk > 0 && ngq_n > 0) {
    if (ngq[0].n > atk) { ngq[0].n -= atk; atk = 0; }
    else                { atk -= ngq[0].n; ngq_pop(); }
  }
  ng_out += atk;
  stats[ST_ATTACK] = atk;             // JS 는 이 값을 그대로 서버에 실어 보낸다

  int overdue = (ngq_n > 0 && ngq[0].age >= ng_delay);
  if (ngq_n > 0 && (stats[ST_CLEAR] == 0 || overdue)) {
    int budget = ng_cap;
    while (ngq_n > 0 && budget > 0 && stats[ST_STATE] == STATE_PLAY) {
      int k = (ngq[0].n < budget) ? ngq[0].n : budget;
      ng_src = ngq[0].from;
      ts_garbage(k, ngq[0].hole);     // 아래층의 공개 익스포트를 그대로 쓴다
      budget   -= k;
      ngq[0].n -= k;
      if (ngq[0].n == 0) ngq_pop();
    }
  }
  ng_sync_pending();
}

// ── 아래층을 감싸는 세 개의 문 ────────────────────────────────────────
// 락이 났는지는 stats[ST_EVENT] 가 늘었는지로 안다. 아래층을 고치지 않고
// "락 훅"을 만드는 방법이 이것뿐이다 — 그리고 이걸로 충분하다.
EXPORT(ng_init) void ng_init(u32 seed) {
  ts_init(seed);
  ngq_n = 0; ng_out = 0; ng_src = -1;
  ng_delay = NG_DELAY; ng_cap = GARBAGE_CAP;
  for (int i = 0; i < NG_MAXQ; i++) { ngq[i].n = ngq[i].from = ngq[i].hole = ngq[i].age = 0; }
  ng_sync_pending();
}

EXPORT(ng_update) int ng_update(int dt_ms) {
  if (dt_ms > 100) dt_ms = 100;        // 아래층과 같은 상한을 써야 나이가 어긋나지 않는다
  for (int i = 0; i < ngq_n; i++) ngq[i].age += dt_ms;
  int ev = stats[ST_EVENT];
  ts_update(dt_ms);
  if (stats[ST_EVENT] != ev) { ng_on_lock(); return 1; }
  return 0;
}

EXPORT(ng_press) void ng_press(int act) {
  int ev = stats[ST_EVENT];
  ts_press(act);
  if (stats[ST_EVENT] != ev) ng_on_lock();
}
EXPORT(ng_release) void ng_release(int act) { ts_release(act); }

// AI 가 고른 한 수를 두는 문. 2편의 ai_apply 와 같지만 락 훅을 지나간다.
EXPORT(ng_apply) void ng_apply(int packed) {
  int ev = stats[ST_EVENT];
  ai_apply(packed);
  if (stats[ST_EVENT] != ev) ng_on_lock();
}
EXPORT(ng_step) int ng_step() {
  int p = ai_plan();
  if (p >= 0) ng_apply(p);
  return p;
}

// ── 서버와 주고받는 두 방향 ──────────────────────────────────────────
// 들어오는 쪽: 서버의 grb 메시지 하나 = 여기 호출 한 번.
EXPORT(ng_queue) void ng_queue(int n, int from, int hole) {
  if (n <= 0) return;
  if (hole < 0 || hole >= W) hole = 0;
  if (ngq_n >= NG_MAXQ) { ngq[NG_MAXQ - 1].n += n; ng_sync_pending(); return; }
  ngq[ngq_n].n = n; ngq[ngq_n].from = from; ngq[ngq_n].hole = hole; ngq[ngq_n].age = 0;
  ngq_n++;
  ng_sync_pending();
}
// 나가는 쪽: 읽으면 비워진다. 못 읽고 지나간 프레임이 있어도 줄 수가 사라지지 않는다.
EXPORT(ng_take_attack) int ng_take_attack() { int a = ng_out; ng_out = 0; return a; }

EXPORT(ng_pending)   int ng_pending()   { int t = 0; for (int i = 0; i < ngq_n; i++) t += ngq[i].n; return t; }
EXPORT(ng_queue_len) int ng_queue_len() { return ngq_n; }
EXPORT(ng_queue_max) int ng_queue_max() { return NG_MAXQ; }
EXPORT(ng_queue_ptr) int ng_queue_ptr() { return (int)(usize)ngq; }
EXPORT(ng_last_source) int ng_last_source() { return ng_src; }
EXPORT(ng_set_delay) void ng_set_delay(int ms) { ng_delay = ms < 0 ? 0 : ms; }
EXPORT(ng_set_cap)   void ng_set_cap(int n)    { ng_cap = (n < 1) ? 1 : (n > H ? H : n); }

// 가장 높이 쌓인 열의 높이. 서버의 ko/even 타겟팅이 이 숫자 하나로 판을 읽는다.
// O(H×W) = 240회 — 초당 10번 부르는 값이라 이 정도면 공짜다.
EXPORT(ng_height) int ng_height() {
  for (int y = 0; y < H; y++)
    for (int x = 0; x < W; x++)
      if (board[y * W + x]) return H - y;
  return 0;
}

// ── 화면 스냅샷 (protocol.md §6) ──────────────────────────────────────
// 200칸을 런렝스로 접는다.  바이트 = (런길이-1) << 4 | 칸값
// 런길이는 1~16, 칸값은 0(빈칸)·1~7(조각색)·8(가비지)이라 각각 4비트에 딱 맞는다.
// 빈 판이 13바이트, 최악(한 칸씩 색이 바뀌는 판)이 200바이트다.
EXPORT(ng_snapshot) int ng_snapshot() {
  int n = 0, i = 0;
  while (i < NG_SNAP) {
    u8 v = cells[i];
    int run = 1;
    while (i + run < NG_SNAP && cells[i + run] == v && run < 16) run++;
    ng_snap[n++] = (u8)(((run - 1) << 4) | (v & 15));
    i += run;
  }
  return n;
}
EXPORT(ng_snap_ptr) int ng_snap_ptr() { return (int)(usize)ng_snap; }

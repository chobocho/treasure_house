// native_main.cpp — wasm 이 아니라 *네이티브*로 같은 코드를 돌리는 진입점.
//
// 왜 이걸 만드나: wasm 은 선형 메모리 밖으로 나가면 조용히 0을 읽거나 트랩만 낸다.
// 배열 한 칸을 넘어가는 실수를 잡아 주는 도구가 없다. 그래서 똑같은 소스를
// g++ -fsanitize=address,undefined 로 한 번 더 빌드해서 돌려 본다.
// 여기서 깨끗하면 wasm 에서도 깨끗하다 — 같은 코드니까.
//
//   g++ -O1 -g -fsanitize=address,undefined -o tetris_ai_native native_main.cpp
//   ./tetris_ai_native 1 2 3
//
// tetris.cpp 는 프리스탠딩용으로 memset/memcpy 를 직접 정의한다. 네이티브에서는
// libc 것과 충돌하므로, 포함하기 전에 이름을 바꿔치기해서 둘 다 살려 둔다.
#define memset ts_memset
#define memcpy ts_memcpy
#include "ai.cpp"
#undef memset
#undef memcpy

#include <cstdio>
#include <cstdlib>

// GA 이전의 "사람이 손으로 찍은" 기준 가중치. 부호만 상식대로 준 것이고,
// 이 값이 얼마나 어설픈지는 GA 결과와 비교하는 슬라이드에서 드러난다.
static const float BASELINE[F_COUNT] = {
   0.60f,   // F_LINES  줄을 지우면 좋다
  -0.35f,   // F_AGG    높이 총합
  -0.55f,   // F_HOLES  구멍
  -0.20f,   // F_BUMP   울퉁불퉁함
  -0.25f,   // F_WELLS  우물
  -0.20f,   // F_ROWT   행 전이
  -0.25f,   // F_COLT   열 전이
  -0.15f,   // F_LAND   착지 높이
};

static void print_board() {
  printf("   +----------+\n");
  for (int y = HIDDEN; y < H; y++) {
    printf("%2d |", y - HIDDEN);
    for (int x = 0; x < W; x++) {
      u8 v = board[y * W + x];
      putchar(v == 0 ? '.' : (v == GARBAGE ? '#' : (char)('0' + v)));
    }
    printf("|\n");
  }
  printf("   +----------+\n");
}

int main(int argc, char** argv) {
  for (int i = 0; i < F_COUNT; i++) weights[i] = BASELINE[i];

  // 인자로 가중치 8개를 주면 그걸 쓴다: ./tetris_ai_native -w w0 w1 … w7 [seed…]
  int argi = 1;
  if (argc > 1 && argv[1][0] == '-' && argv[1][1] == 'w') {
    if (argc < 10) { fprintf(stderr, "-w 는 가중치 8개가 필요하다\n"); return 2; }
    for (int i = 0; i < F_COUNT; i++) weights[i] = (float)atof(argv[2 + i]);
    argi = 10;
  }

  int seeds[64], ns = 0;
  for (; argi < argc && ns < 64; argi++) seeds[ns++] = atoi(argv[argi]);
  if (ns == 0) { seeds[0] = 1; seeds[1] = 2; seeds[2] = 3; ns = 3; }

  long total_lines = 0, total_atk = 0;
  for (int i = 0; i < ns; i++) {
    int lines = ai_play((u32)seeds[i], 400);
    int atk   = ai_play_attack();
    total_lines += lines; total_atk += atk;
    printf("seed %-6d  조각 %4d  지운 줄 %4d  공격 %4d  상태 %s\n",
           seeds[i], stats[ST_PIECES], lines, atk,
           stats[ST_STATE] == STATE_OVER ? "게임오버" : "생존");
  }
  printf("\n마지막 판의 필드 (%d 은 가비지):\n", GARBAGE);
  print_board();
  printf("\n평균: 지운 줄 %.1f, 공격 %.1f (%d 판)\n",
         (double)total_lines / ns, (double)total_atk / ns, ns);

  // 가비지·상쇄 경로도 한 번 밟아 본다 (ASan 이 볼 수 있게)
  ts_init(12345);
  ts_queue_garbage(4);
  for (int i = 0; i < 40 && stats[ST_STATE] == STATE_PLAY; i++) ai_step();
  ts_garbage(3, 5);
  ts_garbage(2, -1);
  for (int i = 0; i < 40 && stats[ST_STATE] == STATE_PLAY; i++) ai_step();
  printf("가비지 경로: 받은 줄 %d, 대기 %d, 상태 %d\n",
         stats[ST_GARBAGE_RECV], stats[ST_PENDING], stats[ST_STATE]);
  return 0;
}

// 상수표와 유닛·건물표 — SPEC §0, §25.
//
//    이 파일은 다른 모듈을 하나도 참조하지 않고, 함수도 (표를 만드는 것 말고는)
//    없다. 숫자만 있다. 같은 상수를 두 군데 적으면 한 쪽만 고치는 날이 오고,
//    그날 세 언어가 갈린다. 그래서 `fixed` 에 있는 FP_* 와 D_* 를 여기에 **다시**
//    적어 두었지만, 그 둘이 같은지는 test_fixed 가 대조한다. `fixed` 는 의존이
//    없어야 가장 먼저 포팅되므로 여기를 참조하지 않는다.

// ── §0 화면과 맵 ────────────────────────────────────────────────────────────
export const SCR_W = 320;
export const SCR_H = 200;
export const TILE = 16;
export const MAP_W = 64;
export const MAP_H = 64;
export const VIEW_X = 0;
export const VIEW_Y = 0;
export const VIEW_W = 256;                 // 16타일
export const VIEW_H = 176;                 // 11타일 — 176 + 24 = 200 이 화면 높이다
export const PANEL_X = 256;
export const PANEL_W = 64;
export const MINI_X = 256;
export const MINI_Y = 0;
export const MINI_W = 64;
export const MINI_H = 64;
export const BAR_Y = 176;
export const BAR_H = 24;

// ── §0 고정소수점 (fixed 와 같은 값이어야 한다) ─────────────────────────────
export const FP_BITS = 16;
export const FP_ONE = 65536;
export const FP_HALF = 32768;
export const FP_DIAG = 46341;
export const FP_SQRT2M1 = 27146;

// ── §0 하드웨어와 시간 ──────────────────────────────────────────────────────
export const PAL_SIZE = 256;
export const DAC_MAX = 63;
export const TICK_US = 54925;              // 18.2065 Hz. 실제 54,925.4 µs
export const PIT_HZ = 1193182;

// ── §0 시뮬레이션 ───────────────────────────────────────────────────────────
export const ORDER_DELAY = 2;
export const MAX_ENT = 256;
export const GEN_MOD = 256;
export const MAX_PLAYER = 4;
export const SIGHT_MAX = 8;
export const CLUSTER = 8;
export const BUCKET = 8;
export const D_STRAIGHT = 10;
export const D_DIAG = 14;

// ── §0 해시와 CRC ───────────────────────────────────────────────────────────
export const FNV_OFFSET = 2166136261;
export const FNV_PRIME = 16777619;
export const CRC_POLY = 0x1021;
export const CRC_INIT = 0xFFFF;

// ── §25 종류 번호 ───────────────────────────────────────────────────────────
// 유닛 0..4, 건물 10..15. 5..9 를 비워 둔 것은 "유닛인가"를 번호 하나로
// 판별하려는 유혹을 막기 위해서다 — 판별은 IS_BUILDING 표가 한다.
export const INF = 0;
export const ARCHER = 1;
export const TANK = 2;
export const MORTAR = 3;
export const HARV = 4;
export const HQ = 10;
export const REF = 11;
export const BARR = 12;
export const FACT = 13;
export const POW = 14;
export const TOWER = 15;

export const KIND_COUNT = 16;

// {종류: 값} 을 길이 16 배열로. 언어가 달라도 같은 모양을 갖도록 배열로 둔다.
function tab(pairs: Array<[number, number]>): number[] {
  const t: number[] = [];
  for (let k = 0; k < KIND_COUNT; k += 1) t.push(0);
  for (const [k, v] of pairs) t[k] = v;
  return t;
}

export const NAME: string[] = ['', '', '', '', '', '', '', '', '', '',
                               '', '', '', '', '', ''];
for (const [k, n] of [[INF, '보병'], [ARCHER, '사수'], [TANK, '전차'],
                      [MORTAR, '박격포'], [HARV, '채집기'], [HQ, '사령부'],
                      [REF, '정제소'], [BARR, '병영'], [FACT, '공장'],
                      [POW, '발전소'], [TOWER, '방어탑']] as Array<[number, string]>) {
  NAME[k] = n;
}

export const HP = tab([[INF, 40], [ARCHER, 30], [TANK, 90], [MORTAR, 35],
                       [HARV, 60], [HQ, 400], [REF, 250], [BARR, 200],
                       [FACT, 300], [POW, 150], [TOWER, 120]]);
export const BASIC = tab([[INF, 6], [ARCHER, 4], [TANK, 12], [MORTAR, 10],
                          [TOWER, 8]]);
export const PIERCE = tab([[INF, 3], [ARCHER, 6], [TANK, 8], [MORTAR, 12],
                           [TOWER, 6]]);
export const ARMOUR = tab([[INF, 1], [ARCHER, 0], [TANK, 4], [MORTAR, 0],
                           [HARV, 3], [HQ, 3], [REF, 5], [BARR, 4], [FACT, 5],
                           [POW, 3], [TOWER, 5]]);
export const RANGE = tab([[INF, 1], [ARCHER, 4], [TANK, 3], [MORTAR, 6],
                          [TOWER, 5]]);
export const RELOAD = tab([[INF, 12], [ARCHER, 16], [TANK, 24], [MORTAR, 40],
                           [TOWER, 20]]);
// 16.16 px/틱. 1.5 px/틱 = 0.094 타일/틱 — 47타일 대각선에 752틱이 든다(대각 보정 포함, §25.4).
export const SPEED = tab([[INF, 98304], [ARCHER, 91750], [TANK, 131072],
                          [MORTAR, 65536], [HARV, 78643]]);
export const SIGHT = tab([[INF, 4], [ARCHER, 5], [TANK, 5], [MORTAR, 4],
                          [HARV, 3], [HQ, 6], [REF, 4], [BARR, 4], [FACT, 4],
                          [POW, 3], [TOWER, 6]]);
export const COST = tab([[INF, 100], [ARCHER, 140], [TANK, 300], [MORTAR, 260],
                         [HARV, 150], [REF, 300], [BARR, 400], [FACT, 600],
                         [POW, 200], [TOWER, 250]]);
export const BUILD_TICKS = tab([[INF, 60], [ARCHER, 80], [TANK, 150],
                                [MORTAR, 140], [HARV, 90], [REF, 180],
                                [BARR, 200], [FACT, 300], [POW, 120],
                                [TOWER, 120]]);
// 유닛은 인구 소비, 건물은 인구 제공 — 어느 쪽인지는 IS_BUILDING 이 정한다.
export const POP = tab([[INF, 1], [ARCHER, 1], [TANK, 2], [MORTAR, 2],
                        [HARV, 1], [HQ, 10], [POW, 10]]);
export const FOOT = tab([[INF, 1], [ARCHER, 1], [TANK, 1], [MORTAR, 1],
                         [HARV, 1], [HQ, 3], [REF, 2], [BARR, 2], [FACT, 3],
                         [POW, 2], [TOWER, 1]]);
export const IS_BUILDING = tab([[HQ, 1], [REF, 1], [BARR, 1], [FACT, 1],
                                [POW, 1], [TOWER, 1]]);
// §4.3 통행 비트 번호와 같은 값이다: 0 = 보병, 1 = 차량. 차량은 언덕에 못 오른다.
export const MOVE_KIND = tab([[TANK, 1], [HARV, 1]]);

// ── §17.1 FSM 상태 번호 ─────────────────────────────────────────────────────
// 전투 유닛과 채집기가 state 바이트 하나를 나눠 쓴다. 겹치면 상태 해시가
// 같은 값을 두 뜻으로 읽게 되므로 번호는 여기 한 곳에서만 정한다.
export const ST_IDLE = 0;
export const ST_MOVE = 1;
export const ST_ATTACK = 2;
export const ST_FLEE = 3;
export const ST_SEEK = 4;
export const ST_TO_ORE = 5;
export const ST_MINE = 6;
export const ST_TO_BASE = 7;
export const ST_UNLOAD = 8;
export const ST_BUILD = 9;

// ── §25.3 기술 트리 (DAG) ───────────────────────────────────────────────────
// 선행 목록은 **번호 오름차순**으로 적는다. 위상 정렬의 타이브레이크가 세 언어에서
// 같아야 하기 때문이다. FACT 만 선행이 둘이고, 그래서 위상 정렬이 실제로 필요하다.
export const PREREQ: number[][] = [];
for (let k = 0; k < KIND_COUNT; k += 1) PREREQ.push([]);
PREREQ[HARV] = [HQ];
PREREQ[REF] = [HQ];
PREREQ[BARR] = [HQ];
PREREQ[INF] = [BARR];
PREREQ[ARCHER] = [BARR];
PREREQ[TOWER] = [BARR];
PREREQ[FACT] = [BARR, POW];
PREREQ[TANK] = [FACT];
PREREQ[MORTAR] = [FACT];

// ── §25.4 시작 조건 ─────────────────────────────────────────────────────────
export const START_CREDITS = 1000;
export const START_HARV = 2;
export const SCENARIO_TICKS = 1200;

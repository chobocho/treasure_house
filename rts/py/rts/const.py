# -*- coding: utf-8 -*-
"""상수표와 유닛·건물표 — SPEC §0, §25.

   이 파일은 다른 모듈을 하나도 참조하지 않고, 함수도 없다. 숫자만 있다.
   같은 상수를 두 군데 적으면 한 쪽만 고치는 날이 오고, 그날 세 언어가 갈린다.
   그래서 `fixed` 에 있는 FP_* 와 D_* 도 여기에 **다시** 정의하지 않고,
   §0 표에 있다는 이유로 여기에 두고 `fixed` 가 여기를 읽는 편이 옳아 보이지만
   그렇게 하지 않았다 — `fixed` 는 의존이 없어야 세 언어에서 가장 먼저 포팅된다.
   두 곳에 있는 값은 `test_const` 와 `test_fixed` 가 서로 대조한다.
"""

# ── §0 화면과 맵 ────────────────────────────────────────────────────────────
SCR_W = 320
SCR_H = 200
TILE = 16
MAP_W = 64
MAP_H = 64
VIEW_X = 0
VIEW_Y = 0
VIEW_W = 256                      # 16타일
VIEW_H = 176                      # 11타일 — 176 + 24 = 200 이 정확히 화면 높이다
PANEL_X = 256
PANEL_W = 64
MINI_X = 256
MINI_Y = 0
MINI_W = 64
MINI_H = 64
BAR_Y = 176
BAR_H = 24

# ── §0 고정소수점 (fixed 와 같은 값이어야 한다) ─────────────────────────────
FP_BITS = 16
FP_ONE = 65536
FP_HALF = 32768
FP_DIAG = 46341
FP_SQRT2M1 = 27146

# ── §0 하드웨어와 시간 ──────────────────────────────────────────────────────
PAL_SIZE = 256
DAC_MAX = 63
TICK_US = 54925                   # 18.2065 Hz. 실제 54,925.4 µs — 오차 0.0007 %
PIT_HZ = 1193182

# ── §0 시뮬레이션 ───────────────────────────────────────────────────────────
ORDER_DELAY = 2
MAX_ENT = 256
GEN_MOD = 256
MAX_PLAYER = 4
SIGHT_MAX = 8
CLUSTER = 8
BUCKET = 8
D_STRAIGHT = 10
D_DIAG = 14

# ── §0 해시와 CRC ───────────────────────────────────────────────────────────
FNV_OFFSET = 2166136261
FNV_PRIME = 16777619
CRC_POLY = 0x1021
CRC_INIT = 0xFFFF

# ── §25 종류 번호 ───────────────────────────────────────────────────────────
# 유닛 0..4, 건물 10..15. 5..9 를 비워 둔 것은 "유닛인가"를 번호 하나로
# 판별하려는 유혹을 막기 위해서다 — 판별은 IS_BUILDING 표가 한다.
INF, ARCHER, TANK, MORTAR, HARV = 0, 1, 2, 3, 4
HQ, REF, BARR, FACT, POW, TOWER = 10, 11, 12, 13, 14, 15

KIND_COUNT = 16
_U = [0] * KIND_COUNT


def _tab(pairs):
    """{종류: 값} 을 길이 16 배열로. 세 언어가 같은 모양을 갖도록 배열로 둔다."""
    t = list(_U)
    for k, v in pairs:
        t[k] = v
    return t


NAME = ['', '', '', '', '', '', '', '', '', '',
        '', '', '', '', '', '']
for _k, _n in ((INF, '보병'), (ARCHER, '사수'), (TANK, '전차'),
               (MORTAR, '박격포'), (HARV, '채집기'), (HQ, '사령부'),
               (REF, '정제소'), (BARR, '병영'), (FACT, '공장'),
               (POW, '발전소'), (TOWER, '방어탑')):
    NAME[_k] = _n

#                 INF ARCHER TANK MORTAR HARV       HQ  REF BARR FACT POW TOWER
HP = _tab([(INF, 40), (ARCHER, 30), (TANK, 90), (MORTAR, 35), (HARV, 60),
           (HQ, 400), (REF, 250), (BARR, 200), (FACT, 300), (POW, 150),
           (TOWER, 120)])
BASIC = _tab([(INF, 6), (ARCHER, 4), (TANK, 12), (MORTAR, 10), (TOWER, 8)])
PIERCE = _tab([(INF, 3), (ARCHER, 6), (TANK, 8), (MORTAR, 12), (TOWER, 6)])
ARMOUR = _tab([(INF, 1), (ARCHER, 0), (TANK, 4), (MORTAR, 0), (HARV, 3),
               (HQ, 3), (REF, 5), (BARR, 4), (FACT, 5), (POW, 3), (TOWER, 5)])
RANGE = _tab([(INF, 1), (ARCHER, 4), (TANK, 3), (MORTAR, 6), (TOWER, 5)])
RELOAD = _tab([(INF, 12), (ARCHER, 16), (TANK, 24), (MORTAR, 40), (TOWER, 20)])
# 16.16 px/틱. 1.5 px/틱 = 0.094 타일/틱 — 47타일 대각선에 500틱이 든다.
SPEED = _tab([(INF, 98304), (ARCHER, 91750), (TANK, 131072),
              (MORTAR, 65536), (HARV, 78643)])
SIGHT = _tab([(INF, 4), (ARCHER, 5), (TANK, 5), (MORTAR, 4), (HARV, 3),
              (HQ, 6), (REF, 4), (BARR, 4), (FACT, 4), (POW, 3), (TOWER, 6)])
COST = _tab([(INF, 100), (ARCHER, 140), (TANK, 300), (MORTAR, 260),
             (HARV, 150), (REF, 300), (BARR, 400), (FACT, 600), (POW, 200),
             (TOWER, 250)])
BUILD_TICKS = _tab([(INF, 60), (ARCHER, 80), (TANK, 150), (MORTAR, 140),
                    (HARV, 90), (REF, 180), (BARR, 200), (FACT, 300),
                    (POW, 120), (TOWER, 120)])
# 유닛은 인구 소비, 건물은 인구 제공 — 어느 쪽인지는 IS_BUILDING 이 정한다.
POP = _tab([(INF, 1), (ARCHER, 1), (TANK, 2), (MORTAR, 2), (HARV, 1),
            (HQ, 10), (POW, 10)])
FOOT = _tab([(INF, 1), (ARCHER, 1), (TANK, 1), (MORTAR, 1), (HARV, 1),
             (HQ, 3), (REF, 2), (BARR, 2), (FACT, 3), (POW, 2), (TOWER, 1)])
IS_BUILDING = _tab([(HQ, 1), (REF, 1), (BARR, 1), (FACT, 1), (POW, 1),
                    (TOWER, 1)])
# §4.3 통행 비트 번호와 같은 값이다: 0 = 보병, 1 = 차량. 차량은 언덕에 못 오른다.
MOVE_KIND = _tab([(TANK, 1), (HARV, 1)])

# ── §25.3 기술 트리 (DAG) ───────────────────────────────────────────────────
# 선행 목록은 **번호 오름차순**으로 적는다. 위상 정렬의 타이브레이크가 세 언어에서
# 같아야 하기 때문이다. FACT 만 선행이 둘이고, 그래서 위상 정렬이 실제로 필요하다.
PREREQ = [[] for _ in range(KIND_COUNT)]
PREREQ[HARV] = [HQ]
PREREQ[REF] = [HQ]
PREREQ[BARR] = [HQ]
PREREQ[INF] = [BARR]
PREREQ[ARCHER] = [BARR]
PREREQ[TOWER] = [BARR]
PREREQ[FACT] = [BARR, POW]
PREREQ[TANK] = [FACT]
PREREQ[MORTAR] = [FACT]

# ── §25.4 시작 조건 ─────────────────────────────────────────────────────────
START_CREDITS = 1000
START_HARV = 2
SCENARIO_TICKS = 1200

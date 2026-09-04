# -*- coding: utf-8 -*-
"""헥스 좌표계 — SPEC §1, §4.4, §9.1.

   이 모듈은 전부 정수 연산이다. 도스 시절 8086 에는 FPU 가 없었고,
   386 이후에도 코프로세서는 옵션이었다. 부동소수를 한 번 쓰면 그 값이
   맵·경로·시야 계산 전체로 번져 기종마다 결과가 달라진다 — 그래서
   원본 게임들도, 이 포트도, 좌표 계층에서 부동소수를 쓰지 않는다.

   좌표 표현은 세 가지다.
     · 축좌표(axial)  (q, r)      — 계산의 기본형. 저장은 2워드.
     · 큐브(cube)     (x, y, z)   — x+y+z==0. 거리·회전·보간이 대칭적이라 쉽다.
     · 오프셋(offset) (col, row)  — 화면·배열과 1:1. 저장·렌더링 전용.
"""

# SPEC §1.5 — 방향 인덱스는 세이브 파일과 골든 트레이스에 그대로 들어간다.
# 순서를 바꾸면 저장된 경로가 전부 어긋나므로 이 표는 불변이다.
DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
DIR_NAMES = ('E', 'NE', 'NW', 'W', 'SW', 'SE')

SCALE = 1024          # SPEC §9.1 — 라인 보간의 고정소수 단위
NUDGE = (1, 1, -2)    # 합이 0이라 x+y+z==0 평면을 벗어나지 않는다


# ---------------------------------------------------------------- 큐브 변환
def to_cube(q, r):
    """축좌표 → 큐브. y 는 저장하지 않고 필요할 때 만든다(메모리 2/3)."""
    return (q, -q - r, r)


def from_cube(x, y, z):
    return (x, z)


# ------------------------------------------------------------ 오프셋 변환
def axial_to_oddr(q, r):
    """축좌표 → odd-r 오프셋(뾰족머리·행 어긋남). SPEC §1.3.

       (r - (r & 1)) >> 1 은 floor(r/2) 를 음수까지 맞게 계산한다.
       파이썬의 >> 는 산술 시프트라 음수에서도 내림이 보장된다.
    """
    return (q + ((r - (r & 1)) >> 1), r)


def oddr_to_axial(col, row):
    return (col - ((row - (row & 1)) >> 1), row)


def axial_to_oddq(q, r):
    """축좌표 → odd-q 오프셋(납작머리·열 어긋남). SPEC §1.4."""
    return (q, r + ((q - (q & 1)) >> 1))


def oddq_to_axial(col, row):
    return (col, row - ((col - (col & 1)) >> 1))


# ------------------------------------------------------------------- 거리
def distance(aq, ar, bq, br):
    """헥스 거리. SPEC §1.6 — O(1).

       큐브에서는 |dx|+|dy|+|dz| 의 절반인데, y = -x-z 이므로 y 를 만들지 않고
       |dq| + |dr| + |dq+dr| 로 바로 쓴다. 나눗셈은 항상 짝수를 2로 나누므로
       시프트 한 번이면 된다.
    """
    dq = aq - bq
    dr = ar - br
    return (abs(dq) + abs(dr) + abs(dq + dr)) >> 1


def neighbor(q, r, d):
    dq, dr = DIRS[d]
    return (q + dq, r + dr)


def neighbors(q, r):
    return [(q + dq, r + dr) for dq, dr in DIRS]


# ------------------------------------------------------------ 회전·반사
def rotate_cw(x, y, z):
    """원점 기준 시계 방향 60도. SPEC §1.7 — 좌표를 밀고 부호만 뒤집는다."""
    return (-y, -z, -x)


def rotate_ccw(x, y, z):
    return (-z, -x, -y)


def rotate_about(q, r, cq, cr, steps):
    """중심 (cq,cr) 둘레로 steps*60도 회전. steps 는 음수도 된다."""
    x, y, z = to_cube(q - cq, r - cr)
    for _ in range(steps % 6):
        x, y, z = rotate_cw(x, y, z)
    return (x + cq, z + cr)


def reflect_q(x, y, z):
    """q 축 대칭 — y 와 z 를 맞바꾼다."""
    return (x, z, y)


# ----------------------------------------------------------------- 링·나선
def ring(cq, cr, n):
    """중심에서 거리가 정확히 n 인 헥스 6n 개. SPEC §1.8 — O(n).

       시작점을 SW(dir 4) 로 n 칸 간 자리에 두고 dir 0..5 순서로 n 칸씩 걷는다.
       거리 판정을 하지 않고 걷기만 하므로 곱셈·나눗셈이 없다.
    """
    if n == 0:
        return [(cq, cr)]
    q = cq + DIRS[4][0] * n
    r = cr + DIRS[4][1] * n
    out = []
    for d in range(6):
        dq, dr = DIRS[d]
        for _ in range(n):
            out.append((q, r))
            q += dq
            r += dr
    return out


def spiral(cq, cr, n):
    """반경 n 이내 전부, 안쪽부터. 개수 1 + 3n(n+1). 시야 계산이 이걸 쓴다."""
    out = [(cq, cr)]
    for k in range(1, n + 1):
        out.extend(ring(cq, cr, k))
    return out


# --------------------------------------------------------------- 큐브 반올림
def round_div(n, d):
    """d > 0 인 반올림 나눗셈, 동점은 0에서 먼 쪽으로. SPEC §4.4.

       파이썬의 round() 는 은행가 반올림(0.5를 짝수로)이라 여기서 쓰면
       루아·타입스크립트와 답이 갈린다. 그래서 직접 정의한다.
    """
    if n >= 0:
        return (2 * n + d) // (2 * d)
    return -((-2 * n + d) // (2 * d))


def cube_round(xf, yf, zf, scale=SCALE):
    """고정소수 큐브 좌표를 가장 가까운 헥스로. SPEC §4.4 — 축좌표로 돌려준다.

       셋 다 따로 반올림하면 x+y+z != 0 이 될 수 있다. 그래서 오차가 가장 큰
       축 하나를 버리고 나머지 둘로 다시 만든다. 비교 순서(dx 먼저, 다음 dy)는
       모서리에 정확히 걸친 점의 소속을 정하는 규칙이라 세 언어가 같아야 한다.
    """
    rx = round_div(xf, scale)
    ry = round_div(yf, scale)
    rz = round_div(zf, scale)
    dx = abs(rx * scale - xf)
    dy = abs(ry * scale - yf)
    dz = abs(rz * scale - zf)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return (rx, rz)


# ------------------------------------------------------------------- 라인
def line(aq, ar, bq, br):
    """A 에서 B 까지 한 칸씩 이어지는 헥스 목록(양 끝 포함). SPEC §9.1.

       보간을 1/1024 단위 정수로 한다. 넛지(+1,+1,-2)/1024 는 모서리에 정확히
       걸치는 점을 한쪽으로 밀어 준다 — 넛지가 없으면 (0,0)→(2,-1) 같은 선이
       두 갈래가 되어 언어마다, 심지어 최적화 옵션마다 답이 달라진다.
       O(N), 곱셈 3회/칸.
    """
    n = distance(aq, ar, bq, br)
    ax, ay, az = to_cube(aq, ar)
    bx, by, bz = to_cube(bq, br)
    ax = ax * SCALE + NUDGE[0]
    ay = ay * SCALE + NUDGE[1]
    az = az * SCALE + NUDGE[2]
    bx *= SCALE
    by *= SCALE
    bz *= SCALE
    if n == 0:
        return [cube_round(ax, ay, az)]
    out = []
    for i in range(n + 1):
        ti = i * SCALE // n
        out.append(cube_round(ax + ((bx - ax) * ti) // SCALE,
                              ay + ((by - ay) * ti) // SCALE,
                              az + ((bz - az) * ti) // SCALE))
    return out

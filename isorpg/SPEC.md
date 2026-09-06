# IsoRPG 엔진 명세 (normative)

파이썬 · 루아 · 타입스크립트 세 구현은 이 문서를 **정확히** 따른다.
어긋나면 골든 벡터가 즉시 틀어지도록 설계되어 있다.

명시적으로 "실수"라고 적지 않은 모든 연산은 **정수 연산**이다.
부동소수점이 허용되는 곳은 단 두 군데다.

* `tools/gen_prim.py` — 정수 루틴을 검증하기 위한 *독립* 참조 계산 (엔진 밖)
* `tools/gen_*.py` — 골든 데이터 생성기 (엔진 밖)

엔진 본체(`py/isorpg`, `lua/isorpg`, `ts/src`)에는 부동소수점 연산이 하나도 없다.

---

## 0. 상수

| 이름 | 값 | 뜻 |
|---|---|---|
| `TW` | 32 | 타일 마름모 가로 지름 (px) |
| `TH` | 16 | 타일 마름모 세로 지름 (px) |
| `TZ` | 8 | 높이 1단계가 화면에서 올라가는 픽셀 |
| `SCR_W` | 320 | 화면 폭 (Mode 13h) |
| `SCR_H` | 200 | 화면 높이 |
| `MAP_W` | 48 | 맵 가로 타일 수 |
| `MAP_H` | 48 | 맵 세로 타일 수 |
| `MAXH` | 15 | 최대 높이 단계 (4비트) |
| `FP_BITS` | 16 | 고정소수점 소수부 비트 |
| `FP_ONE` | 65536 | 고정소수점 1.0 |
| `LIGHT_LEVELS` | 16 | 명암 단계 (0 = 암흑, 15 = 원색) |
| `PAL_SIZE` | 256 | 팔레트 항목 수 |
| `DAC_MAX` | 63 | VGA DAC 채널 최대값 (6비트) |
| `TICK_US` | 54925 | 한 틱의 마이크로초 (PIT 18.2065 Hz) |

`TICK_US` 는 `round(65536 * 1000000 / 1193182)` 이 아니라 **정확히 54925** 로 고정한다.
세 언어가 같은 정수를 쓰기만 하면 되고, 실제 PIT 값과의 오차(0.02 %)는 덱 13부에서 따로 다룬다.

---

## 1. 정수 연산 규약

세 언어의 나눗셈·나머지·시프트 의미가 전부 다르다. 그래서 엔진은 아래 세 함수만 쓴다.
`/`, `//`, `%`, `>>`, `&` 를 좌표나 고정소수점 값에 **직접 쓰지 않는다.**

```
floordiv(a, b)   b > 0 일 때, a/b 를 -무한대 방향으로 내림한 정수
fmod(a, b)       a - b * floordiv(a, b)   (항상 0 <= 결과 < b)
ashr(a, k)       floordiv(a, 2^k)
```

* 파이썬: `a // b`, `a % b` 가 이미 이 의미다.
* 루아 5.1: `math.floor(a / b)` — a, b 가 2^53 을 넘지 않아야 한다.
* 타입스크립트: `Math.floor(a / b)` — `>>` 는 32비트로 잘리므로 **금지**.

정수는 세 언어 모두 배정밀도 부동소수점(53비트 가수)에 정확히 담기는 범위,
즉 `|x| < 2^53` 안에서만 다룬다. 이 상계를 넘을 수 있는 곳은 §2.2 와 §5.3 뿐이며
두 곳 모두 분할 곱셈으로 우회한다.

### 1.1 바이트 패킹

맵 한 칸은 1바이트다.

```
cell = terrain | (height << 4)        terrain 0..15, height 0..15
terrain_of(cell) = fmod(cell, 16)
height_of(cell)  = floordiv(cell, 16)
```

---

## 2. 고정소수점 — 모듈 `fixed`

16.16 형식. 값 `x` 는 실수 `x / 65536` 을 뜻한다.

### 2.1 변환

```
fp(n)        = n * 65536
fp_floor(x)  = floordiv(x, 65536)
fp_round(x)  = floordiv(x + 32768, 65536)
fp_frac(x)   = fmod(x, 65536)
```

`fp_floor` 는 음수에서도 내림이다. `fp_floor(-1) = -1`, `fp_floor(-65536) = -1`,
`fp_floor(-65537) = -2`.

### 2.2 곱셈

`a * b` 는 최대 2^62 까지 커져 배정밀도에 담기지 않는다. 그래서 `a` 를 상·하위로 쪼갠다.

```
fp_mul(a, b):
    ah = floordiv(a, 65536)
    al = a - ah * 65536              # 0 <= al < 65536
    return ah * b + floordiv(al * b, 65536)
```

**정리 2.1** `|a| < 2^31`, `|b| < 2^37` 이면 `fp_mul(a,b) == floordiv(a*b, 65536)` 이고
중간값이 모두 2^53 미만이다.

*증명.* `a = ah*2^16 + al` 이므로 `a*b = ah*b*2^16 + al*b`.
양변을 2^16 으로 나눠 내림하면 `ah*b` 가 정수이므로
`floordiv(a*b, 2^16) = ah*b + floordiv(al*b, 2^16)`.
중간값: `|ah| < 2^15`, `|ah*b| < 2^52`; `al < 2^16`, `|al*b| < 2^53`. ∎

곱셈은 **내림**이다. 반올림 곱이 필요하면 `fp_mulr(a,b) = floordiv(a*b + 32768, 65536)` 을
같은 방식으로 분할해 쓴다(엔진에서는 광원 감쇠에서만 쓴다).

### 2.3 나눗셈

```
fp_div(a, b):    b != 0
    return floordiv(a * 65536, b)
```

`|a| < 2^37` 이면 `a * 65536 < 2^53` 이라 정확하다. 엔진의 모든 좌표는 `|a| < 2^27` 이다.

### 2.4 정수 제곱근

```
isqrt(n):    n >= 0
    if n < 2: return n
    x = n
    y = floordiv(x + 1, 2)
    while y < x:
        x = y
        y = floordiv(x + floordiv(n, x), 2)
    return x
```

**정리 2.2** `isqrt(n) = floor(sqrt(n))`, 그리고 뉴턴 반복은 단조 감소하므로 반드시 끝난다.
`n < 2^43` 에서 모든 중간값이 2^53 미만이다.

```
fp_sqrt(x) = isqrt(x * 65536)        x >= 0, x < 2^27
```

### 2.5 팔각 거리 근사 (alpha max plus beta min)

```
OCT_A = 983      # round(0.960433870103 * 1024)
OCT_B = 407      # round(0.397824734759 * 1024)

oct_dist(dx, dy):
    ax = |dx| ; ay = |dy|
    hi = max(ax, ay) ; lo = min(ax, ay)
    return floordiv(OCT_A * hi + OCT_B * lo, 1024)
```

상대 오차의 최대값은 테스트 `test_fixed.py` 가 0..255 전 각도에 대해 실측해 출력한다.
덱에는 실측값만 싣는다 — 문헌값을 그대로 옮겨 적지 않는다.

### 2.6 사인/코사인 표 — CORDIC

각도 단위는 **brad**(binary radian): 한 바퀴 = 256. `SIN[a]`, `COS[a]` 는 16.16 값이다.
표는 실행 시각에 **정수 CORDIC** 으로 만든다. 데이터 파일이 아니라 알고리즘이므로
세 언어가 같은 값을 얻는 것이 곧 이식이 맞다는 증거가 된다.

CORDIC 상수. 각 반복의 회전각을 brad 로 환산해 16.16 으로 반올림한 것이다.

```
N_ITER = 20 ; GUARD = 8
ATAN_BRAD[i] = round( atan(2^-i) / (2*pi) * 256 * 65536 )      i = 0..19
             = 2097152 1238021 654136 332050 166669 83416 41718 20860
               10430 5215 2608 1304 652 326 163 81 41 20 10 5
K_INV        = 10188014        # round( 65536 * 2^GUARD / prod_i sqrt(1 + 4^-i) )
```

`ATAN_BRAD[0] = 32 * 65536` — 45도가 정확히 32 brad 라서 첫 항이 딱 떨어진다.
`sum(ATAN_BRAD) / 65536 = 71.03 brad > 64 brad` 이므로 1사분면 전체를 덮는다(수렴 조건).

회전 CORDIC. 안쪽에서는 `GUARD = 8` 비트를 더 들고 다니다가 끝에서 반올림해 버린다.
이 여덟 비트가 없으면 20번의 내림이 누적돼 최대 오차가 5까지 벌어진다.

```
cordic(theta):                         # theta 는 16.16 brad
    t = fmod(theta, 256 * 65536)
    quad = floordiv(t, 64 * 65536)     # 0..3
    t = t - quad * 64 * 65536
    x = K_INV ; y = 0 ; z = t
    for i in 0..N_ITER-1:
        d  = +1 if z >= 0 else -1
        nx = x - d * floordiv(y, 2^i)
        ny = y + d * floordiv(x, 2^i)
        z  = z - d * ATAN_BRAD[i]
        x, y = nx, ny
    x = floordiv(x + 128, 256) ; y = floordiv(y + 128, 256)      # GUARD 반올림 제거
    quad == 0: (cos, sin) = ( x,  y)
    quad == 1: (cos, sin) = (-y,  x)
    quad == 2: (cos, sin) = (-x, -y)
    quad == 3: (cos, sin) = ( y, -x)
```

`floordiv(v, 2^i)` 는 음수에서도 내림이다.

표는 `SIN[a] = cordic(fp(a)).sin`, `COS[a] = cordic(fp(a)).cos`, `a = 0..255`.
`test_fixed` 는 표의 모든 항목이 `round(65536*sin(2*pi*a/256))` 과 **±1** 이내임을 확인한다.
허용 오차 1은 명세의 일부다 — 세 언어의 CORDIC 결과는 서로 **완전히 같아야** 하고,
참값과의 오차만 ±1 을 허용한다.

실측 확인:

```
  SIN[0]  = 0        COS[0]  = 65536
  SIN[32] = 46341    COS[32] = 46341        # 45도. 대각 이동 계수 DIAG_FACTOR 와 같은 수다
  SIN[64] = 65536    COS[64] = 0
  최대 오차 1
```

---

## 3. 투영 — 모듈 `proj`

### 3.1 기저

타일 `(tx, ty)` 의 마름모는 **꼭대기 꼭짓점**이 월드 픽셀

```
Vx(tx, ty) = (tx - ty) * (TW/2) = 16 * (tx - ty)
Vy(tx, ty) = (tx + ty) * (TH/2) =  8 * (tx + ty)
```

에 놓인다. 마름모의 중심은 `(Vx, Vy + TH/2) = (Vx, Vy + 8)`.
높이 `h` 인 타일은 화면에서 `h * TZ` 만큼 **위로** 올라간다.

```
tile_to_screen(tx, ty, h) -> (Vx(tx,ty), Vy(tx,ty) - h * TZ)
```

행렬로 쓰면

```
      | 16  -16 |            |  8   16 |
  M = |  8    8 |    M^-1 = -+---------+ / 256
                             | -8   16 |

  det M = 16*8 - (-16)*8 = 256
```

**정리 3.1** `det M = 256 = 2^8` 이라 역행렬 성분이 전부 `k/256` 꼴이고,
2:1 비율(`TW = 2*TH`)일 때만 `M^-1 * 256` 의 성분이 `±8, 16` 처럼 **2의 거듭제곱 배수**가 된다.
그래서 역투영이 시프트만으로 끝난다. 이것이 도스 게임이 30도 등각이 아니라
2:1 다이메트릭을 고른 산술적 이유다.

### 3.2 월드 좌표(고정소수점) → 화면

엔티티는 타일 단위 16.16 좌표 `(fx, fy)` 와 정수 높이 `h` 를 갖는다.

```
world_to_screen(fx, fy, h):
    sx = floordiv((fx - fy) * 16, 65536)
    sy = floordiv((fx + fy) *  8, 65536) - h * TZ
    return (sx, sy)
```

`|fx|, |fy| < 48 * 65536 < 2^22` 이므로 `(fx+fy)*16 < 2^27` — 안전하다.

### 3.3 화면 → 타일 : 대수적 역

```
screen_to_tile(px, py):
    tx = floordiv(px + 2 * py, 32)
    ty = floordiv(2 * py - px, 32)
```

**정리 3.2** 이 식은 픽셀 `(px, py)` 를 품는 마름모의 타일을 정확히 하나 준다.

*증명.* `a = px + 2py`, `b = 2py - px` 로 두면 `(a,b) <- (px,py)` 는 가역 선형변환이다
(야코비 행렬식 `1*2 - 2*(-1) = 4 != 0`).

타일 `(tx,ty)` 의 중심 `(cx, cy) = (16(tx-ty), 8(tx+ty)+8)` 을 대입하면

```
  a_c = cx + 2*cy = 16(tx-ty) + 16(tx+ty) + 16 = 32*tx + 16
  b_c = 2*cy - cx = 16(tx+ty) + 16 - 16(tx-ty) = 32*ty + 16
```

중심 기준 상대 좌표 `u = px - cx`, `v = py - cy` 에 대해 마름모 내부 조건은
`|u|/16 + |v|/8 <= 1`, 곧 `|u| + 2|v| <= 16` 이다. `A = u + 2v`, `B = 2v - u` 로 두면
`u = (A-B)/2`, `2v = (A+B)/2` 이므로

```
  |u| + |2v| = |A-B|/2 + |A+B|/2 = max(|A|, |B|)
```

(마지막 등식은 `|p|+|q| = max(|p+q|, |p-q|)` 의 다른 표기다.) 따라서 내부 조건은
`max(|A|, |B|) <= 16` 이고, `A = a - a_c`, `B = b - b_c` 이므로

```
  타일 (tx,ty) 의 마름모  =  { (a,b) : 32*tx <= a <= 32*tx + 32,  32*ty <= b <= 32*ty + 32 }
```

`(a,b)` 공간에서 변 32짜리 정사각형이고, 이 정사각형들은 격자를 이뤄 평면을 빈틈없이 덮는다.
반개구간으로 자르면 `tx = floordiv(a, 32)`, `ty = floordiv(b, 32)` 가 정확히 하나를 준다. ∎

경계 픽셀은 `floor` 규칙에 따라 `a`, `b` 가 큰 쪽 타일이 가져간다. 겹침도 빈틈도 없다.

### 3.4 화면 → 타일 : 도스식 사각형 + 모서리 마스크

`px = 32*rc + ox`, `py = 16*rr + oy` (`0 <= ox < 32`, `0 <= oy < 16`) 로 쓰면 §3.3 은

```
tx = (rc + rr) + floordiv(ox + 2*oy, 32)
ty = (rr - rc) + floordiv(2*oy - ox, 32)
```

가 된다. `ox + 2oy` 는 `[0, 61]`, `2oy - ox` 는 `[-31, 30]` 이므로

```
A(ox,oy) = floordiv(ox + 2*oy, 32) ∈ {0, 1}
B(ox,oy) = floordiv(2*oy - ox, 32) ∈ {-1, 0}
```

**네 가지 경우뿐이다.** 이것이 도스 게임이 쓰던 32x16 모서리 마스크의 정체다.

```
MASK[oy*32 + ox] = 2 * A + (B + 1)          값은 0..3

pick_mask(px, py):
    rc = floordiv(px, 32) ; ox = px - 32*rc
    rr = floordiv(py, 16) ; oy = py - 16*rr
    m  = MASK[oy*32 + ox]
    return (rc + rr + floordiv(m, 2), rr - rc + fmod(m, 2) - 1)
```

마스크는 두 직선

```
  ox + 2*oy = 32        (기울기 -1/2, 사각형 중심 (16,8) 통과)
  2*oy - ox = 0         (기울기 +1/2, 같은 중심 통과)
```

이 사각형을 넷으로 자른 모양이다. 네 조각은 각각 넓이 128 px²,
곧 마름모 넓이(32*16/2 = 256)의 **절반**이다. 사각형 하나에 마름모 두 개 몫(512 px²)이
들어간다는 계산과 맞는다.

`golden/pick_mask.txt` 는 이 표를 16줄 × 32글자로 적은 것이다.
`test_prim` 은 화면 전체 64,000 픽셀과 카메라 오프셋 여러 개에 대해
`pick_mask == screen_to_tile` 임을 **전수 확인**한다.

### 3.5 가시 타일 범위

뷰포트를 `[x0, x1) x [y0, y1)` 라 하자(월드 픽셀). 여백을 준 뒤 네 모서리를 역투영한다.

```
MARGIN_X = TW/2 = 16
MARGIN_Y = TH/2 + MAXH * TZ + SPRITE_MAX_H = 8 + 120 + 32 = 160

visible_range(x0, y0, x1, y1):
    X0 = x0 - MARGIN_X ; X1 = x1 + MARGIN_X
    Y0 = y0 - MARGIN_Y ; Y1 = y1 + MARGIN_Y
    a_min = X0 + 2*Y0 ; a_max = X1 + 2*Y1
    b_min = 2*Y0 - X1 ; b_max = 2*Y1 - X0
    tx0 = floordiv(a_min, 32) ; tx1 = floordiv(a_max, 32)
    ty0 = floordiv(b_min, 32) ; ty1 = floordiv(b_max, 32)
    맵 경계로 자른 [max(tx0,0), min(tx1,MAP_W-1)] x [max(ty0,0), min(ty1,MAP_H-1)] 반환
```

**정리 3.3** `a = px + 2py` 는 `(px,py)` 의 선형함수이므로 볼록다각형(직사각형) 위에서
최대·최소를 꼭짓점에서 취한다. `a` 의 계수가 둘 다 양수라 최소는 `(X0,Y0)`,
최대는 `(X1,Y1)` 에서 난다. `b = 2py - px` 는 `px` 계수가 음수이므로
최소는 `(X1,Y0)`, 최대는 `(X0,Y1)` 이다. ∎

---

## 4. 카메라 — 모듈 `camera`

카메라는 **정수 픽셀** 오프셋 `(camX, camY)` 다. 화면 픽셀 `(px,py)` 의 월드 픽셀은
`(px + camX, py + camY)`.

```
DEADZONE_X = 48        # 화면 중앙에서 이만큼 벗어나야 카메라가 따라간다
DEADZONE_Y = 24

follow(camX, camY, tgtX, tgtY):        # tgtX,tgtY 는 대상의 월드 픽셀
    cx = tgtX - camX - SCR_W/2         # 화면 중앙 기준 어긋난 양
    cy = tgtY - camY - SCR_H/2
    if cx >  DEADZONE_X: camX += cx - DEADZONE_X
    if cx < -DEADZONE_X: camX += cx + DEADZONE_X
    if cy >  DEADZONE_Y: camY += cy - DEADZONE_Y
    if cy < -DEADZONE_Y: camY += cy + DEADZONE_Y
    return clamp_cam(camX, camY)
```

월드 픽셀 경계(맵 48x48 기준):

```
WORLD_X0 = -16 * (MAP_H - 1) - 16          = -768
WORLD_X1 =  16 * (MAP_W - 1) + 16          =  768
WORLD_Y0 = -MAXH * TZ                      = -120
WORLD_Y1 =  8 * (MAP_W + MAP_H - 2) + 16   =  768

clamp_cam: camX 를 [WORLD_X0, WORLD_X1 - SCR_W] 로, camY 를 [WORLD_Y0, WORLD_Y1 - SCR_H] 로 자른다.
```

---

## 5. 맵 — 모듈 `map`

### 5.1 지형표

`id` 는 셀 바이트의 하위 4비트다. `move` 는 이동 비용(10 = 기본), `opaque` 는 시야 차단.

| id | 이름 | 통행 | move | opaque | 램프 |
|---|---|---|---|---|---|
| 0 | DEEP | 불가 | 0 | 아니오 | water |
| 1 | WATER | 불가 | 0 | 아니오 | water |
| 2 | SAND | 가능 | 12 | 아니오 | sand |
| 3 | GRASS | 가능 | 10 | 아니오 | grass |
| 4 | DIRT | 가능 | 10 | 아니오 | dirt |
| 5 | ROCK | 가능 | 14 | 아니오 | rock |
| 6 | FOREST | 가능 | 16 | 예 | forest |
| 7 | MOUNTAIN | 불가 | 0 | 예 | rock |
| 8 | ROAD | 가능 | 8 | 아니오 | road |
| 9 | FLOOR | 가능 | 10 | 아니오 | floor |
| 10 | WALL | 불가 | 0 | 예 | wall |
| 11 | BRIDGE | 가능 | 10 | 아니오 | wood |
| 12 | SNOW | 가능 | 13 | 아니오 | snow |
| 13 | SWAMP | 가능 | 20 | 아니오 | swamp |
| 14 | LAVA | 불가 | 0 | 아니오 | lava |
| 15 | VOID | 불가 | 0 | 예 | void |

### 5.2 LCG (볼랜드 계열)

```
LCG_A = 22695477 ; LCG_C = 1 ; LCG_M = 4294967296        # 2^32

next_state(s):                       # s 는 0 <= s < 2^32
    sh = floordiv(s, 65536)
    sl = s - sh * 65536
    lo = LCG_A * sl + LCG_C          # < 22695477 * 65536 + 1 < 2^41
    hi = LCG_A * sh                  # < 2^41
    return fmod(fmod(hi, 65536) * 65536 + lo, LCG_M)

rand15(s) = fmod(floordiv(next_state(s), 65536), 32768)   # 0..32767
```

**정리 5.1 (분할 곱의 정확성)** `a*s mod 2^32` 를 위와 같이 계산하면 중간값이
모두 2^42 미만이라 배정밀도에서 정확하다.

*증명.* `s = sh*2^16 + sl` 이므로 `a*s = a*sh*2^16 + a*sl`.
`mod 2^32` 를 취할 때 `a*sh*2^16 mod 2^32 = (a*sh mod 2^16)*2^16`.
`a*sh < 22695477 * 2^16 < 2^41`, `a*sl + 1 < 2^41`,
합은 `65535*65536 + 2^41 < 2^42 < 2^53`. ∎

볼랜드 계열 `rand()` 의 승수 22695477 과 증분 1 은 확인됐지만, 문헌에 따라 법을
2^31 로 적기도 한다. 두 경우 `rand15` 가 쓰는 비트(30..16)의 값은 **완전히 같다** —
2^31 로 줄여도 잘려 나가는 것은 비트 31뿐이기 때문이다. 이 명세는 2^32 를 쓰고,
덱에서는 "출력 비트로 말한다" 는 쪽으로 서술한다 (`deck/claims.md` D23).

**정리 5.2 (Hull–Dobell)** `m = 2^32`, `c = 1`, `a = 22695477` 은 세 조건
(① `gcd(c,m)=1` ② `a-1 = 22695476` 이 `m` 의 유일한 소인수 2로 나누어짐
③ `4 | m` 이고 `4 | a-1` — `22695476 = 4 * 5673869`)을 모두 만족하므로
주기가 정확히 2^32 다. 조건과 출처는 `deck/claims.md` D24 참조.

난수 흐름은 `Rng` 객체 하나로 관리한다. `Rng(seed)` → `next()` 는 상태를 갱신하고
`rand15` 를 돌려준다. **호출 순서가 명세의 일부다.**

```
rand_below(r, n)  = fmod(r.next(), n)          # n <= 32768
roll(r, n, m)     = sum of (fmod(r.next(), m) + 1) for i in 1..n
```

### 5.3 다이아몬드-스퀘어

```
DS_N     = 64                   # 격자 65 x 65
DS_SEED  = 1                    # LCG 초기 상태
DS_CORNER = [512, 400, 430, 560]     # 좌상 우상 좌하 우하
DS_SCALE = 380
DS_ROUGH_NUM = 55 ; DS_ROUGH_DEN = 100

gen_height():
    size = DS_N + 1
    h = size x size 정수 배열, 전부 0
    h[0][0]=DS_CORNER[0]; h[0][DS_N]=DS_CORNER[1]
    h[DS_N][0]=DS_CORNER[2]; h[DS_N][DS_N]=DS_CORNER[3]
    r = Rng(DS_SEED) ; step = DS_N ; scale = DS_SCALE
    while step > 1:
        half = floordiv(step, 2)
        # --- 다이아몬드 단계: 정사각형 네 꼭짓점의 평균 + 흔들림
        for y = half, half+step, ... < size:
            for x = half, half+step, ... < size:
                s = h[y-half][x-half] + h[y-half][x+half]
                  + h[y+half][x-half] + h[y+half][x+half]
                h[y][x] = floordiv(s, 4) + jitter(r, scale)
        # --- 스퀘어 단계: 마름모 네 꼭짓점(격자 밖은 제외)의 평균 + 흔들림
        for y = 0, half, 2*half, ... < size:
            xs = half if fmod(floordiv(y, half), 2) == 0 else 0
            for x = xs, xs+step, ... < size:
                s = 0 ; n = 0
                for (dx,dy) in [(-half,0),(half,0),(0,-half),(0,half)]:
                    if 0 <= x+dx < size and 0 <= y+dy < size:
                        s += h[y+dy][x+dx] ; n += 1
                h[y][x] = floordiv(s, n) + jitter(r, scale)
        step = half
        scale = floordiv(scale * DS_ROUGH_NUM, DS_ROUGH_DEN)
    모든 칸을 [0, 1023] 로 자른다
    return h

jitter(r, scale) = fmod(r.next(), 2*scale + 1) - scale
```

반복 순서(y 바깥, x 안쪽, 다이아몬드 먼저)는 난수 소비 순서를 정하므로 **명세의 일부**다.

### 5.4 지형·높이 배정

`v = h[y + DS_OFF][x + DS_OFF]`, `DS_OFF = floordiv(DS_N + 1 - MAP_W, 2) = 8`.

```
terrain_of_value(v):
    v < 300 -> DEEP      v < 360 -> WATER    v < 395 -> SAND
    v < 620 -> GRASS     v < 700 -> FOREST   v < 790 -> ROCK
    else    -> MOUNTAIN

height_of_value(v):
    v < 360 -> 0
    else    -> clamp(floordiv(v - 360, 48), 0, 12)
```

### 5.5 마을 스탬프

생성 뒤 고정 좌표에 마을을 찍는다. 순서대로 적용한다.

```
TOWN_X0=18 TOWN_Y0=18 TOWN_X1=30 TOWN_Y1=30      # 반개구간

for ty in [TOWN_Y0, TOWN_Y1): for tx in [TOWN_X0, TOWN_X1):
    height = 2
    terrain = WALL   if tx in {TOWN_X0, TOWN_X1-1} or ty in {TOWN_Y0, TOWN_Y1-1}
            else ROAD if tx == 24 or ty == 24
            else FLOOR
문(門): (24, TOWN_Y0), (24, TOWN_Y1-1), (TOWN_X0, 24), (TOWN_X1-1, 24) 는 ROAD 로 되돌린다.
길: tx = 24, ty in [0, TOWN_Y0) 와 ty in [TOWN_Y1, MAP_H) 는 ROAD, height = 2 로 평탄화.
```

### 5.6 RLE 저장/적재

`golden/map.txt` 형식(UTF-8 텍스트, LF):

```
ISORPG-MAP 1 48 48
<run> <run> ...        # 한 줄에 최대 16개, run 은 "count:cell" (count 1..255)
```

`save_rle` 는 셀을 행 우선(`y` 바깥, `x` 안쪽)으로 훑어 같은 값을 묶는다.
`load_rle` 는 그 역이며, 총 개수가 `MAP_W*MAP_H` 가 아니면 오류다.

세 엔진은 모두 `gen_map()` 을 자체 실행해 얻은 맵이 `golden/map.txt` 와
바이트 단위로 같은지 검사한다.

---

## 6. 그리기 순서 — 모듈 `sort`

### 6.1 바닥 타일

바닥은 정렬이 필요 없다. `d = tx + ty` 오름차순, 같으면 `tx` 오름차순으로 그리면
언제나 옳다(뒤쪽 타일이 먼저).

**정리 6.1** 타일 `A` 의 마름모가 `B` 의 마름모를 가릴 수 있으려면
`A.tx >= B.tx` 이고 `A.ty >= B.ty` 이며 둘 중 하나는 진부등호여야 한다.
그러면 `A.tx + A.ty > B.tx + B.ty` 이므로 `d` 오름차순이 곧 화가 알고리즘이다. ∎
(높이가 있는 절벽은 마름모가 아니므로 §6.2 로 넘어간다.)

### 6.2 상자 관계

정렬 대상은 **축 정렬 상자**다. 타일 단위 반개구간 `[x0,x1) x [y0,y1)` 와
높이 반개구간 `[z0,z1)` 를 갖는다. 1x1 물체는 `x1=x0+1`, `y1=y0+1`.

```
behind(A, B)  =  A.x1 <= B.x0  or  A.y1 <= B.y0  or  A.z1 <= B.z0
```

`behind(A,B)` 가 참이면 A 를 먼저 그린다.

**주의 (덱의 핵심 함정)** 이 관계는 반대칭이 아니다.
`A.x1 <= B.x0` 이면서 `B.y1 <= A.y0` 이면 `behind(A,B)` 와 `behind(B,A)` 가 모두 참이다.
그래서 그래프에 **순환**이 생길 수 있다. 실제로는 화면에서 겹치지 않는 두 상자의
순서는 아무래도 상관없으므로, 간선은 **화면 경계상자가 겹치는 쌍에만** 건다.
그래도 세 상자가 도는 순환은 남으며(`golden/sortcase.txt` 의 6번), 이때는 잘라야 한다.

### 6.3 화면 경계상자

```
box_bbox(b):
    (x,y) in {(x0,y0),(x1,y0),(x0,y1),(x1,y1)} 와 z in {z0,z1} 의 8개 조합에 대해
        sx = 16*(x - y) ;  sy = 8*(x + y) - z*TZ
    (min sx, min sy, max sx, max sy)

bbox_overlap(a, b) = not (a.x1 <= b.x0 or b.x1 <= a.x0 or a.y1 <= b.y0 or b.y1 <= a.y0)
```

**보조정리 6.2** `behind(A,B)` 와 `behind(B,A)` 가 **x 조건과 y 조건 때문에** 동시에 참이면
두 상자의 화면 경계상자는 절대 겹치지 않는다.

*증명.* `A.x1 <= B.x0` 이고 `B.y1 <= A.y0` 라 하자. 그러면
`A.x1 - A.y0 <= B.x0 - B.y1` 이고, 양변에 16을 곱하면 좌변은 A 의 `max sx`,
우변은 B 의 `min sx` 다. 따라서 `A.maxsx <= B.minsx` — 겹치지 않는다. ∎

그러므로 `bbox_overlap` 으로 거른 뒤에도 남는 상호 관계는 **x-z 나 y-z 조합뿐**이다.
`golden/sortcase.txt` 의 5번이 그 예다(x 로는 A 가 뒤, z 로는 B 가 뒤).
이때는 간선을 걸지 않고 `depth_key` 로 정한다.

3-순환은 여전히 가능하다. 6번 사례가 실제 예다:
`0 -> 1` (y), `1 -> 2` (z), `2 -> 0` (x) 로 정확히 한 방향씩 돌아간다.

### 6.4 위상 정렬

```
depth_key(A) = (A.x0 + A.y0, A.z0, A.id)          # 사전식

topo_sort(items):
    간선: 화면 경계상자가 겹치는 모든 쌍 (i,j) 에 대해
          behind(i,j) and not behind(j,i)  ->  i -> j
          (양쪽 다 참이면 간선을 걸지 않는다 — 순서 무의미)
    진입차수 0 인 것을 depth_key 오름차순 우선순위 큐에 넣는다 (칸 알고리즘)
    큐가 비었는데 남은 것이 있으면 = 순환
        남은 것 중 depth_key 가 가장 작은 하나를 강제로 방출하고 그 진입간선을 모두 지운다
        (이 사건을 cycle_breaks 로 센다)
    출력 순서를 반환한다
```

우선순위 큐의 동점은 `id` 로 갈리므로 결과는 **완전 결정적**이다.
`cycle_breaks` 는 트레이스에 실려 세 언어에서 같아야 한다.

---

## 7. 래스터 — 모듈 `raster`

### 7.1 프레임버퍼

`fb` 는 길이 `SCR_W * SCR_H = 64000` 인 바이트 배열이다. 인덱스 `y * 320 + x`.
파이썬은 `bytearray`, 루아는 1-기반 정수 테이블, 타입스크립트는 `Uint8Array`.
**루아 인덱스만 1-기반이고, 나머지 모든 좌표 계산은 세 언어가 동일하다.**

### 7.2 팔레트와 광원표

`golden/palette.txt` 형식:

```
ISORPG-PAL 1 256
<idx> <r> <g> <b>        # r,g,b 는 6비트 DAC 값 0..63
```

광원표는 적재 직후 계산한다.

```
LIGHT[l * 256 + c] = argmin_{k in 0..255} dist2( pal[k], scale(pal[c], l) )
    scale((r,g,b), l) = ( floordiv(r*l, 15), floordiv(g*l, 15), floordiv(b*l, 15) )
    dist2 = (dr*dr + dg*dg + db*db)
    동점이면 인덱스가 작은 쪽
```

`LIGHT[15*256 + c] == c` 여야 한다(테스트가 확인한다).

### 7.3 스프라이트

`golden/tiles.rle` 형식(텍스트):

```
ISORPG-TILES 1 <sprite 개수>
SPRITE <id> <name> <w> <h> <ox> <oy>
<row 0>
...
<row h-1>
```

한 `<row>` 는 공백으로 나뉜 `count:color` 런의 나열이고, `count` 의 합은 정확히 `w` 다.
`color == 0` 은 **투명**이다. `(ox, oy)` 는 그리기 기준점(anchor)으로,
스프라이트를 `(x, y)` 에 그리면 실제 좌상단은 `(x - ox, y - oy)` 다.

### 7.4 블릿

```
blit_rle(fb, spr, x, y, light):
    top = y - spr.oy
    for row in 0..spr.h-1:
        py = top + row
        if py < 0 or py >= SCR_H: continue
        px = x - spr.ox
        for (count, color) in spr.rows[row]:
            if color != 0:
                a = max(px, 0) ; b = min(px + count, SCR_W)
                if a < b:
                    v = LIGHT[light * 256 + color]
                    fb[py*SCR_W + a .. py*SCR_W + b) 를 v 로 채운다
            px += count
```

클리핑은 **런 단위**로만 한다 — 픽셀마다 조건을 걸지 않는 것이 도스식이다.
런 하나가 화면 왼쪽/오른쪽으로 걸치면 `[a,b)` 로 잘린다.

### 7.5 더티 렉트

`Dirty` 는 사각형 목록을 갖는다. `add(x,y,w,h)` 는 화면 경계로 자른 뒤 넣고,
`merge()` 는 겹치거나 맞닿은 사각형을 합친다(합쳐진 넓이가 두 넓이 합의 1.5배 이하일 때만).
`merge` 는 목록이 안정될 때까지 반복하고, 결과는 `(y, x)` 오름차순으로 정렬해 결정적으로 만든다.

### 7.6 팔레트 사이클링

물 램프는 팔레트 인덱스 `WATER_LO..WATER_HI` (§ `gen_palette.py` 가 정한다).
`cycle(n)` 은 그 구간을 왼쪽으로 `fmod(n, WATER_HI - WATER_LO + 1)` 칸 회전시킨다.
프레임버퍼는 건드리지 않는다 — 이것이 도스 시절 "공짜 애니메이션"의 핵심이다.

### 7.7 PPM 출력

```
6비트 -> 8비트:  expand(v) = v * 4 + floordiv(v, 16)        # 0->0, 63->255
헤더: "P6\n320 200\n255\n"    (15바이트)
본문: 픽셀마다 expand(r), expand(g), expand(b)              (192000바이트)
합계 192015 바이트
```

---

## 8. 경로 탐색 — 모듈 `path`

### 8.1 여덟 방향

인덱스 순서는 **명세**다(세이브·트레이스에 그대로 들어간다).

| d | 이름 | dx | dy | 대각 |
|---|---|---|---|---|
| 0 | E | +1 | 0 | 아니오 |
| 1 | SE | +1 | +1 | 예 |
| 2 | S | 0 | +1 | 아니오 |
| 3 | SW | -1 | +1 | 예 |
| 4 | W | -1 | 0 | 아니오 |
| 5 | NW | -1 | -1 | 예 |
| 6 | N | 0 | -1 | 아니오 |
| 7 | NE | +1 | -1 | 예 |

화면에서 `+x` 는 오른쪽-아래, `+y` 는 왼쪽-아래로 간다. 이름은 **화면 기준**이다:
타일 `+x` 방향이 화면 남동쪽으로 보이므로 `d=0` 을 E 라 부르는 것은 관례일 뿐이며,
덱 6부에서 이 명명 함정을 따로 다룬다.

### 8.2 통행 규칙

```
STEP_BASE[d] = 14 if 대각 else 10
CLIMB_MAX    = 1

passable(tx, ty):
    맵 안이고 TERRAIN[terrain].move > 0
step_ok(from, to, d):
    passable(to)
    and |height(to) - height(from)| <= CLIMB_MAX
    and (대각이 아니거나, 두 직교 이웃 (from.x+dx, from.y) 와 (from.x, from.y+dy) 가 모두 passable)
step_cost(to, d) = floordiv(STEP_BASE[d] * TERRAIN[terrain(to)].move, 10)
```

마지막 조건이 **모서리 자르기 금지**다. 벽 사이 대각선 통과를 막는다.

### 8.3 옥타일 휴리스틱

```
h(a, b):
    dx = |a.x - b.x| ; dy = |a.y - b.y|
    return 10 * (dx + dy) - 6 * min(dx, dy)
```

위 식은 "모든 걸음이 10/14 로 균일할 때"의 최단거리다. 그런데 이 엔진에서 가장 싼 지형은
ROAD(`move = 8`)이고 그때 직진 비용은 `floordiv(10*8, 10) = 8` 이라 10보다 작다.
그대로 쓰면 실제 비용을 **넘겨짚어** 허용성이 깨진다. 그래서 최소 지형 비용을 곱한다.

```
MIN_MOVE = 8                          # 지형표에서 move > 0 인 것 중 최소값 (ROAD)
h(a, b) = floordiv( (10 * (dx + dy) - 6 * min(dx, dy)) * MIN_MOVE, 10 )
```

**정리 8.1 (허용성)** `h(a,b)` 는 `a` 에서 `b` 까지 실제 비용의 하계다.

*증명.* 임의의 경로가 직진 `p` 번, 대각 `q` 번이라 하자. 8방향 격자에서
`p + q >= max(dx,dy)` 이고 `p + 2q >= dx + dy` 이므로 `q <= min(dx,dy)` 인 경우가
비용 최소이고, 그때 걸음 수는 `dx + dy - min(dx,dy)` 번(그중 대각 `min(dx,dy)` 번)이다.
모든 걸음의 비용은 `floordiv(STEP_BASE * move, 10) >= floordiv(STEP_BASE * 8, 10)`,
곧 직진 `>= 8`, 대각 `>= 11` 이다. 한편

```
  h = floordiv( (10*(dx+dy) - 6*min) * 8, 10 )
    = floordiv( 80*(dx+dy) - 48*min, 10 )
    <= 8*(dx+dy) - 4.8*min
```

이고 실제 최소 비용은 `8*(dx+dy-2*min) + 11*min = 8*(dx+dy) - 5*min` 이다.
`-4.8*min >= -5*min` 이므로 `h <= 실제 최소 비용`. ∎

**정리 8.2 (일관성)** 이웃 `n` 으로 가는 걸음마다 `h(a,b) - h(n,b) <= step_cost(n,d)`.

*증명.* `H(dx,dy) = 80*(dx+dy) - 48*min(dx,dy)` 라 두면 `h = floordiv(H, 10)`.
직진 한 걸음은 `dx+dy` 를 1 줄이고 `min` 은 최대 1 늘리므로 `H` 는 최대 80 준다
→ `h` 감소 최대 8, 실제 직진 비용 `>= 8`.
대각 한 걸음은 `dx+dy` 를 2, `min` 을 1 줄이므로 `H` 는 최대 `160 - 48 = 112` 준다
→ `h` 감소 최대 `floordiv(112,10) = 11`, 실제 대각 비용 `>= floordiv(14*8,10) = 11`. ∎
(두 경우 모두 등호가 가능하다. 일관성은 아슬아슬하게 성립한다 — ROAD 지형의
`move` 를 8 아래로 내리면 즉시 깨진다는 뜻이고, 덱 10부에서 이 경계를 실험으로 보인다.)

### 8.4 다익스트라(양동이 큐)와 A*

두 알고리즘 모두 같은 열린 목록 구조를 쓴다.

```
BUCKET_N = 64          # 최대 간선 비용 floordiv(14*20,10)=28 보다 크면 충분하다
```

양동이 큐는 원형 배열이다. `push(cost, node)` 는 `fmod(cost, BUCKET_N)` 번 양동이에 넣고,
`pop_min` 은 현재 커서부터 한 바퀴 돌며 처음 비지 않은 양동이의 **마지막** 원소를 꺼낸다
(스택 방식 — 결정적이고 캐시에 좋다).

**정리 8.3** 모든 간선 비용이 `[0, BUCKET_N)` 이면 활성 키의 폭이 `BUCKET_N` 미만이므로
원형 양동이 큐가 이진 힙과 같은 순서로 최소값을 준다.

A* 는 같은 큐에 `f = g + h` 를 키로 넣는다. `f` 의 폭도 `BUCKET_N` 미만이다
(일관성이 성립하므로 `f` 는 경로를 따라 단조 증가하고 한 걸음에 최대 28 늘어난다).

동점 처리: 같은 `f` 안에서는 나중에 넣은 것이 먼저 나온다(스택). 결과 경로는
동점이 있어도 결정적이다.

### 8.5 부분 타일 이동

엔티티는 타일 단위 16.16 좌표를 갖는다.

```
SPEED       = 13107       # 한 틱에 0.2타일 = floordiv(fp(1), 5). 18.2Hz 기준 초당 3.6타일
DIAG_FACTOR = 46341       # round(65536 / sqrt(2))

move_step(fx, fy, d):
    s = SPEED
    if 대각: s = fp_mul(s, DIAG_FACTOR)
    return (fx + DIRX[d] * s, fy + DIRY[d] * s)
```

**정리 8.4** `46341 / 65536 = 0.7071075...` 이고 `1/sqrt(2) = 0.7071068...` 이므로
상대 오차는 `1.1e-6` 미만이다. 즉 대각 이동 속도는 직진 속도와 백만분의 일 수준까지 같다.

목적지 타일이 막혀 있으면 축별로 미끄러진다(먼저 x, 다음 y). 규칙은 `game` 모듈에 있다.

---

## 9. 시야·안개·조명 — 모듈 `los`

### 9.1 브레젠험

```
line(x0, y0, x1, y1) -> 타일 목록 (양 끝 포함)
    dx = |x1-x0| ; sx = +1 if x0 < x1 else -1
    dy = -|y1-y0| ; sy = +1 if y0 < y1 else -1
    err = dx + dy
    반복: 점 (x,y) 를 담는다. (x,y) == (x1,y1) 이면 종료
          e2 = 2*err
          if e2 >= dy: err += dy ; x += sx
          if e2 <= dx: err += dx ; y += sy
```

오차항 `err` 는 "이상적 직선에서 벗어난 양 × 2·dx" 를 정수로 들고 다니는 값이다.
유도는 덱 11부에 있다.

### 9.2 시야

```
EYE = 2                                   # 눈높이 (높이 단계)

visible(src, dst):
    선 위의 중간 타일 t (양 끝 제외) 마다:
        TERRAIN[terrain(t)].opaque 이면 차단
        height(t) > max(height(src), height(dst)) + EYE - 1 이면 차단
    아니면 보임
```

### 9.3 안개

타일마다 2비트: `bit0 = 한 번이라도 봤다`, `bit1 = 지금 보인다`.
매 시야 갱신 때 `bit1` 을 전부 지우고, 반경 `SIGHT_R = 9` 안의 타일에 대해
`visible()` 을 돌려 다시 세운다. `bit0` 은 지우지 않는다.

### 9.4 조명 단계

```
light_of(tile):
    bit1 (지금 보임): 
        d = oct_dist((tx-px)*256, (ty-py)*256)
        return clamp(15 - floordiv(10 * d, SIGHT_R * 256), 5, 15)
    bit0 만 (기억):  return 4
    아무것도 아님:   return 0
```

---

## 10. 난수와 전투 — 모듈 `dice`

### 10.1 분포 (합성곱)

```
dist(n, m) -> 길이 n*m+1 정수 배열, 인덱스 s 는 합이 s 인 경우의 수
    c = [1]                            # 0면 주사위: 합 0 이 1가지
    n 번 반복:
        새 배열 c2 를 0으로 채우고
        for s in c 의 인덱스: for f in 1..m: c2[s+f] += c[s]
        c = c2
    return c
```

`sum(dist(n,m)) == m^n` 이다(테스트가 확인).
기대값 `n*(m+1)/2`, 분산 `n*(m*m-1)/12` 는 정수 분수로 비교한다
(`sum(s*c[s])*2 == n*(m+1)*m^n` 형태로 곱셈만 써서).

### 10.2 명중과 피해

```
to_hit(atk, def) = 11 + def - atk          # 1d20 이 이 값 이상이면 명중
p_hit(atk, def)  = clamp(21 - to_hit, 1, 19)   # 20면 중 명중하는 눈의 수 (1은 항상 실패, 20은 항상 성공)

attack(r, A, B):
    roll = fmod(r.next(), 20) + 1
    if roll == 1: 빗나감
    elif roll == 20 or roll >= to_hit(A.atk, B.def): 명중
    else: 빗나감
    피해 = max(1, roll_dice(r, A.dn, A.dm) + A.dbonus - B.armor)
```

`roll == 20` 일 때 피해는 두 배로 하지 않는다(도스 RPG 관례가 제각각이라 단순화).

### 10.3 성장

```
xp_to_next(L) = 20 * L * L + 30 * L         # L=1 -> 50, L=2 -> 140, L=3 -> 270
level_up: maxhp += 4 + fmod(r.next(), 5) ; atk += 1 ; if fmod(L,2)==0: def += 1
```

---

## 11. 저장 — 모듈 `save`

### 11.1 CRC-16/CCITT-FALSE

```
poly 0x1021, init 0xFFFF, 입력·출력 반전 없음, xorout 0x0000
표 만들기:
    for i in 0..255:
        c = i * 256
        8번 반복: c = fmod(c*2, 65536) xor (0x1021 if c >= 32768 else 0)
        TBL[i] = c
crc16(bytes):
    c = 0xFFFF
    for b in bytes: c = fmod(c*256, 65536) xor TBL[ fmod(floordiv(c,256) xor b, 256) ]
    return c
```

`xor` 는 16비트 정수 두 개에 대한 비트 배타적 논리합이다. 루아 5.1 에는 없으므로
`fixed` 모듈이 순수 산술 `xor16(a,b)` 를 제공한다(8비트씩 4번, 표 없이 나눗셈 루프).
세 언어 모두 이 함수를 쓴다 — 그래야 결과가 같다는 것이 자명해진다.

검증값: `crc16("123456789") == 0x29B1` (`deck/claims.md` D26).

### 11.2 세이브 형식

바이트열이다. 리틀 엔디언 없음 — **모두 빅 엔디언**으로 쓴다.

```
"ISO1"                       4바이트 매직
u16 tick_lo, u16 tick_hi     틱 카운터 (32비트)
u32 rng_state
u16 entity 수
엔티티마다: u8 kind, i32 fx, i32 fy, u8 h, u16 hp, u16 maxhp,
            u8 lv, u32 xp, u8 atk, u8 def, u8 armor, u8 dir, u8 alive
u16 안개 바이트 수, 그만큼의 바이트 (타일 4개당 1바이트, 2비트씩)
u16 crc16(위 전체)
```

`i32` 는 2의 보수 빅 엔디언이다: `u32 = fmod(v, 4294967296)`.
`load` 는 CRC 를 검사하고 틀리면 오류다. `save -> load -> save` 가 바이트 동일해야 한다.

---

## 12. 게임 루프 — 모듈 `game`

### 12.1 엔티티

```
kind: 0 = 플레이어, 1 = 몬스터, 2 = 상자, 3 = NPC
필드: fx, fy (16.16 타일), h, hp, maxhp, lv, xp, atk, def, armor, dir, alive, anim
```

배치는 고정이다(맵 생성 뒤).

```
플레이어: 타일 (24, 34), 즉 fx = fp(24) + 32768, fy = fp(34) + 32768   (타일 중앙)
몬스터 6마리: (20,20) (28,21) (21,28) (29,29) (24,16) (16,24) 순서대로 id 1..6
상자 3개: (22,22) (26,26) (24,20)
NPC 2명: (23,25) (25,23)
```

### 12.2 틱

한 틱은 다음 순서로 진행한다. **순서가 명세다.**

1. 입력 적용(스크립트에서 온 키 상태)
2. 플레이어 이동(§8.5, 막히면 축별 미끄러짐)
3. 몬스터 갱신: 플레이어가 `AGGRO_R = 7` 안이고 `visible` 이면 A* 로 한 칸씩 접근,
   인접하면 `ATTACK_EVERY = 12` 틱마다 공격
4. 플레이어 공격 명령이 있으면 처리
5. 안개·조명 갱신
6. 카메라 추적
7. 틱 카운터 증가

### 12.3 스크립트

`golden/script.txt` 는 한 줄에 명령 하나다. `#` 로 시작하는 줄과 빈 줄은 무시.

```
hold <dir> <ticks>     방향키를 그 틱 수만큼 누른 채로 진행
wait <ticks>           아무 입력 없이 진행
act                    한 틱 동안 상호작용 키
atk                    한 틱 동안 공격 키
save                   현재 상태를 메모리 슬롯에 저장 (틱 소비 없음)
load                   메모리 슬롯에서 복원 (틱 소비 없음)
mark <label>           트레이스에 표식만 남긴다 (틱 소비 없음)
```

### 12.4 트레이스

매 틱 끝에 한 줄을 뱉는다. **키 순서와 공백 없음까지 명세**다.

```
{"t":<tick>,"px":<fx>,"py":<fy>,"ph":<h>,"hp":<hp>,"lv":<lv>,"xp":<xp>,
 "rng":<rng 상태>,"cam":[<camX>,<camY>],"seen":<bit0 세워진 타일 수>,
 "vis":<bit1 세워진 타일 수>,"cyc":<누적 cycle_breaks>,"crc":<지금 세이브의 crc16>}
```

(실제 출력은 한 줄이며 줄바꿈이 없다.) `mark` 는 별도 줄
`{"mark":"<label>","t":<tick>}` 을 낸다.

정수만 싣는다. 부동소수점 표기 차이가 끼어들 여지를 아예 없앤다.

---

## 13. CLI — 모듈 `main`

```
prim                    골든 프리미티브 결과를 표준출력에 (골든과 대조용)
trace                   골든 스크립트를 돌려 트레이스를 표준출력에
render <file.ppm> [n]   n 틱까지 진행한 뒤 한 프레임을 PPM 으로 (기본 n = 마지막)
bench                   구간별 성능 측정 (수치는 기계마다 다르므로 파리티 대상 아님)
play                    프런트엔드에서만 (pygame / LÖVE / Canvas)
```

`prim`, `trace`, `render` 의 출력은 세 언어에서 **바이트 단위로 같아야 한다.**
`bench` 만 예외다.

---

## 14. 파일 목록과 책임

| 파일 | 책임 |
|---|---|
| `golden/prim.txt` | 프리미티브 기대값 (독립 계산으로 생성) |
| `golden/pick_mask.txt` | 32x16 모서리 마스크 |
| `golden/cordic.txt` | CORDIC 상수 검증표 |
| `golden/palette.txt` | 256색 팔레트 (6비트 DAC) |
| `golden/tiles.rle` | 스프라이트 뱅크 |
| `golden/map.txt` | 생성된 맵의 RLE (엔진이 재생성해 대조) |
| `golden/sortcase.txt` | 상자 정렬 사례 6개와 기대 순서 |
| `golden/script.txt` | 시나리오 입력 |
| `golden/trace.jsonl` | 파이썬 참조에서 얼린 트레이스 |

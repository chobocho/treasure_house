// 16.16 고정소수점 · 정수 기하 · 거리 척도 — SPEC §1, §2.
//
//    파이썬 원본을 그대로 옮긴다. 파이썬만 생각하면 한 줄이면 끝나는 함수들이
//    이렇게 쪼개져 있는 이유는 자바스크립트 때문이다. JS 의 정수는 배정밀도
//    부동소수점(가수 53비트)에 얹혀 있고 `>>` `&` `|` `^` 는 32비트로 잘린다.
//    그래서 이 모듈은
//      · 시프트를 쓰지 않고 (floordiv 로만)
//      · 곱셈 중간값이 2^53 을 넘지 않게 쪼개서
//      · 비트 연산자 대신 산술로
//    계산한다. 이 파일 전체에 비트 연산자가 한 개도 없다는 것이 규약이다.
//
//    이 파일은 다른 모듈을 하나도 참조하지 않는다. 나머지 전부가 여기에 기댄다.

export const FP_BITS = 16;
export const FP_ONE = 65536;
export const FP_HALF = 32768;
export const FP_DIAG = 46341;         // 1/√2 의 16.16 반올림 (46340.950…)
export const FP_SQRT2M1 = 27146;      // √2−1 의 16.16 반올림 (27145.951…)

export const D_STRAIGHT = 10;
export const D_DIAG = 14;

// SPEC §2.7 — 화면 좌표이므로 y 는 아래로 증가한다.
export const DX = [0, 1, 1, 1, 0, -1, -1, -1];
export const DY = [-1, -1, 0, 1, 1, 1, 0, -1];
export const DNAME = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
export const DCOST = [D_STRAIGHT, D_DIAG, D_STRAIGHT, D_DIAG,
                      D_STRAIGHT, D_DIAG, D_STRAIGHT, D_DIAG];

// 2의 거듭제곱 표 — `1 << k` 를 쓰지 않기 위한 것이다. k 가 31 을 넘어도
// 안전해야 하므로 (fnv 는 2^32 를 다룬다) 표로 미리 굳혀 둔다.
const POW2: number[] = [];
for (let k = 0; k <= 53; k += 1) POW2.push(Math.pow(2, k));

export function pow2(k: number): number {
  return POW2[k];
}

// ── SPEC §1 정수 연산 규약 ──────────────────────────────────────────────────
// 파이썬의 // 와 % 를 **알고리즘까지** 그대로 옮긴다. Math.floor(a/b) 로 줄이면
// 나눗셈이 한 번 반올림된 뒤 내림이 되어 2^53 근처에서 한 칸씩 어긋난다.
export function floordiv(a: number, b: number): number {
  let mod = a % b;                     // JS 의 % 는 절단 나머지 — 정확하다
  let div = (a - mod) / b;             // a - mod 는 b 의 배수라 나눗셈이 정확하다
  if (mod !== 0 && (b < 0) !== (mod < 0)) {
    mod += b;
    div -= 1;
  }
  const fl = Math.floor(div);
  return (div - fl > 0.5) ? fl + 1 : fl;   // CPython float_floor_div 와 같은 보정
}

export function fmod(a: number, b: number): number {
  let mod = a % b;
  if (mod !== 0 && (b < 0) !== (mod < 0)) mod += b;
  return mod;
}

export function ashr(a: number, k: number): number {
  return floordiv(a, POW2[k]);
}

export function ashl(a: number, k: number): number {
  return a * POW2[k];
}

// ── SPEC §1.1 비트 연산의 산술 대체 ─────────────────────────────────────────
export function bit(v: number, k: number): number {
  return fmod(floordiv(v, POW2[k]), 2);
}

export function setbit(v: number, k: number): number {
  return v + (1 - bit(v, k)) * POW2[k];
}

export function clrbit(v: number, k: number): number {
  return v - bit(v, k) * POW2[k];
}

// 바이트 두 개의 XOR — 여덟 번 도는 것이 전부다.
// JS 의 ^ 는 32비트로 잘리므로 여기서는 쓰지 않는다(SPEC §1.1). 한 곳에서만
// 규칙을 어겨도 반드시 다른 곳에서 샌다.
export function xor8(x: number, y: number): number {
  let r = 0;
  let p = 1;
  let a = x;
  let b = y;
  for (let k = 0; k < 8; k += 1) {
    if ((a % 2) !== (b % 2)) r += p;
    a = floordiv(a, 2);
    b = floordiv(b, 2);
    p *= 2;
  }
  return r;
}

// 32비트 값의 하위 8비트에만 XOR — FNV-1a(SPEC §18.4)가 쓴다.
export function xorLow8(h: number, b: number): number {
  return h - fmod(h, 256) + xor8(fmod(h, 256), b);
}

// ── SPEC §2.1 변환 ──────────────────────────────────────────────────────────
export function fp(n: number): number {
  return n * FP_ONE;
}

export function fpFloor(x: number): number {
  return floordiv(x, FP_ONE);
}

export function fpRound(x: number): number {
  return floordiv(x + FP_HALF, FP_ONE);
}

export function fpFrac(x: number): number {
  return fmod(x, FP_ONE);
}

// ── SPEC §2.3 곱셈 (분할 곱) ────────────────────────────────────────────────
// floor(a*b / 65536). a 를 상·하위로 쪼개 중간값을 2^53 아래로 붙든다.
// a = ah·2^16 + al 이므로 a·b/2^16 = ah·b + al·b/2^16 이고, 첫 항이 정수라
// 바닥함수 밖으로 나온다 (SPEC 정리 2.1). 쪼개지 않으면 a·b 가 2^53 을 넘는다.
export function fpMul(a: number, b: number): number {
  const ah = floordiv(a, FP_ONE);
  const al = fmod(a, FP_ONE);
  return ah * b + floordiv(al * b, FP_ONE);
}

export function fpDiv(a: number, b: number): number {
  if (b === 0) throw new Error('fp_div: b == 0');   // 호출자의 버그다
  return floordiv(a * FP_ONE, b);
}

// ── SPEC §2.5 정수 제곱근 ───────────────────────────────────────────────────
// 뉴턴 반복. 초기값과 종료 조건까지 명세다 — 세 언어가 같은 횟수를 돈다.
export function isqrt(n: number): number {
  if (n < 2) return n;
  let x = n;
  let y = floordiv(x + 1, 2);
  while (y < x) {
    x = y;
    y = floordiv(x + floordiv(n, x), 2);
  }
  return x;
}

export function fpSqrt(x: number): number {
  return isqrt(x * FP_ONE);            // x < 2^31 이므로 x*65536 < 2^47 — 안전하다
}

// ── SPEC §2.6 거리 척도 ─────────────────────────────────────────────────────
function mxmn(dx: number, dy: number): [number, number] {
  const ax = dx >= 0 ? dx : -dx;
  const ay = dy >= 0 ? dy : -dy;
  return ax >= ay ? [ax, ay] : [ay, ax];
}

// L1 (맨해튼) — 4방향 이동의 정확한 걸음 수.
export function d1(dx: number, dy: number): number {
  return (dx >= 0 ? dx : -dx) + (dy >= 0 ? dy : -dy);
}

// L∞ (체비셰프) — 8방향 이동의 정확한 걸음 수. 사거리 판정은 전부 이것.
export function dinf(dx: number, dy: number): number {
  return mxmn(dx, dy)[0];
}

// 옥타일 8분의 3 근사. √2−1 = 0.41421 을 3/8 로 바꾼 도스식 값.
export function d83(dx: number, dy: number): number {
  const [mx, mn] = mxmn(dx, dy);
  return mx + floordiv(3 * mn, 8);
}

// 경로 비용 단위의 옥타일 거리. 직선 10, 대각 14 — A* 휴리스틱이 이것이다.
export function doct(dx: number, dy: number): number {
  const [mx, mn] = mxmn(dx, dy);
  return D_STRAIGHT * mx + (D_DIAG - D_STRAIGHT) * mn;
}

// alpha-max-beta-min. 마지막 반올림(+32768)이 없으면 dab(1,0) = 0 이 된다.
// 거리 1 이 0 으로 나오면 사거리 판정과 타깃 선택이 통째로 무너진다.
// 골든 벡터를 처음 만들 때 오차 −100 % 로 드러난 자리다(SPEC §2.6).
export function dab(dx: number, dy: number): number {
  const [mx, mn] = mxmn(dx, dy);
  return floordiv(62943 * mx + 26072 * mn + FP_HALF, FP_ONE);
}

// ── SPEC §2.7 8방향 판별 ────────────────────────────────────────────────────
// 비교만으로 8방향을 고른다. 나눗셈도 삼각함수도 없다.
// 경계는 22.5°이고 tan 22.5° = √2−1 = 0.414214 다. 5/12 = 0.416667 로 바꾸면
// 경계각이 22.62° — 0.12° 넓어질 뿐이다. √2−1 의 연분수 수렴분수가
// 1/2, 2/5, 5/12, 12/29 … (펠 수의 비)이므로 5/12 는 우연이 아니다.
export function atan8(dx: number, dy: number): number {
  if (dx === 0 && dy === 0) return 2;          // 규약: 정지 상태는 E 를 본다
  const ax = dx >= 0 ? dx : -dx;
  const ay = dy >= 0 ? dy : -dy;
  const mx = ax >= ay ? ax : ay;
  const mn = ax >= ay ? ay : ax;
  const diag = 12 * mn > 5 * mx;
  if (ax >= ay) {                              // 동서가 주축
    if (dx > 0) {
      if (diag) return dy < 0 ? 1 : 3;
      return 2;
    }
    if (diag) return dy < 0 ? 7 : 5;
    return 6;
  }
  if (dy < 0) {                                // 남북이 주축
    if (diag) return dx > 0 ? 1 : 7;
    return 0;
  }
  if (diag) return dx > 0 ? 3 : 5;
  return 4;
}

// ── SPEC §20.1 CRC-16/CCITT-FALSE ───────────────────────────────────────────
// 여기 있는 이유: tmap(맵 파일)과 replay(리플레이 꼬리)가 둘 다 쓰는데,
// fixed 는 아무것도 참조하지 않으므로 순환이 생기지 않는다.
export function xor16(a: number, b: number): number {
  return xor8(floordiv(a, 256), floordiv(b, 256)) * 256
    + xor8(fmod(a, 256), fmod(b, 256));
}

// ── SPEC §18.4 FNV-1a 32비트 ────────────────────────────────────────────────
export const FNV_OFFSET = 2166136261;
export const FNV_PRIME = 16777619;

// 바이트 하나. XOR 은 하위 8비트만 바뀌므로 xor8 로 끝나고,
// 곱셈은 분할한다 — hl * 16777619 < 2^40 이라 53비트 가수에 담긴다.
export function fnv1aStep(h: number, b: number): number {
  const x = xorLow8(h, b);
  const hh = floordiv(x, 65536);
  const hl = fmod(x, 65536);
  return fmod(hl * FNV_PRIME + fmod(hh * FNV_PRIME, 65536) * 65536, 4294967296);
}

export function fnv1a(data: ArrayLike<number>): number {
  let h = FNV_OFFSET;
  for (let i = 0; i < data.length; i += 1) h = fnv1aStep(h, data[i]);
  return h;
}

// poly 0x1021, init 0xFFFF, 반사 없음. crc16(b'123456789') == 0x29B1.
// `c >= 32768` 이 "최상위 비트가 1"과 같다. 이것이 GF(2) 위의 다항식
// 나눗셈이며, 곱셈 2 가 다항식의 x 곱이다.
export function crc16(data: ArrayLike<number>): number {
  let c = 65535;
  for (let i = 0; i < data.length; i += 1) {
    c = xor16(c, data[i] * 256);
    for (let k = 0; k < 8; k += 1) {
      if (c >= 32768) c = xor16(fmod(c * 2, 65536), 0x1021);
      else c = fmod(c * 2, 65536);
    }
  }
  return c;
}

// ASCII 문자열을 바이트 배열로 — 골든과 시험이 자주 쓴다.
export function ascii(s: string): number[] {
  const out: number[] = [];
  for (let i = 0; i < s.length; i += 1) out.push(s.charCodeAt(i));
  return out;
}

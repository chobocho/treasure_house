// 16.16 고정소수점 — SPEC §2.
//
// 타입스크립트의 정수는 배정밀도 부동소수점(가수 53비트) 위에 얹혀 있다.
// `>>`, `<<`, `&`, `|`, `^` 는 피연산자를 32비트 정수로 잘라 버리므로
// 16.16 값(최대 2^37)이나 2^32 LCG 상태에 쓰면 소리 없이 값이 망가진다.
// 그래서 이 모듈은 시프트를 한 번도 쓰지 않고 `Math.floor` 와 곱셈·나눗셈만 쓴다.
// 파이썬·루아 구현과 코드가 한 줄씩 대응하도록 일부러 한 줄짜리 함수도 남겨 뒀다.

export const FP_BITS = 16;
export const FP_ONE = 65536;

/** b > 0 일 때 -무한대 방향 내림. JS 의 `/` 는 실수 나눗셈이라 floor 가 필요하다. */
export function floordiv(a: number, b: number): number {
  return Math.floor(a / b);
}

/** 항상 0 <= 결과 < b. JS 의 `%` 는 피제수 부호를 따라가므로 그대로 쓸 수 없다. */
export function fmod(a: number, b: number): number {
  return a - b * Math.floor(a / b);
}

// 2의 거듭제곱 표. `1 << i` 로 만들 수도 있지만 i 가 31을 넘는 순간
// 조용히 틀리는 코드가 되므로, 시프트를 아예 쓰지 않는 쪽으로 통일한다.
const POW2: number[] = (() => {
  const t: number[] = [];
  let v = 1;
  for (let i = 0; i < 54; i++) {
    t.push(v);
    v *= 2;
  }
  return t;
})();

export function pow2(k: number): number {
  return POW2[k] as number;
}

/** 산술 우시프트 = 2^k 로 내림 나눗셈. 음수에서도 내림이다. */
export function ashr(a: number, k: number): number {
  return Math.floor(a / pow2(k));
}

export function fp(n: number): number {
  return n * FP_ONE;
}

export function fpFloor(x: number): number {
  return Math.floor(x / FP_ONE);
}

export function fpRound(x: number): number {
  return Math.floor((x + FP_ONE / 2) / FP_ONE);
}

export function fpFrac(x: number): number {
  return fmod(x, FP_ONE);
}

/** floor(a*b / 65536). a 를 상·하위 16비트로 쪼개 중간값을 2^53 아래로 묶는다.
 *
 *  a*b 를 그대로 곱하면 2^62 까지 커져 배정밀도 가수를 넘고, 넘는 순간
 *  예외도 경고도 없이 하위 비트가 사라진다. 그것이 이 함수가 존재하는 이유다.
 *  |a| < 2^31, |b| < 2^37 이면 |ah*b| < 2^52, |al*b| < 2^53. (정리 2.1) */
export function fpMul(a: number, b: number): number {
  const ah = Math.floor(a / FP_ONE);
  const al = a - ah * FP_ONE; // 0 <= al < 65536
  return ah * b + Math.floor((al * b) / FP_ONE);
}

/** 반올림 곱. 광원 감쇠처럼 한쪽으로 쏠리면 곤란한 곳에만 쓴다. */
export function fpMulr(a: number, b: number): number {
  const ah = Math.floor(a / FP_ONE);
  const al = a - ah * FP_ONE;
  return ah * b + Math.floor((al * b + FP_ONE / 2) / FP_ONE);
}

/** floor(a*65536 / b). |a| < 2^37 이면 a*65536 이 2^53 미만이다. */
export function fpDiv(a: number, b: number): number {
  return Math.floor((a * FP_ONE) / b);
}

/** floor(sqrt(n)). 뉴턴 반복 — 단조 감소라 반드시 멈춘다. (정리 2.2)
 *
 *  `Math.sqrt` 를 쓰지 않는다. 반올림 방향이 명세에 없고, 2^43 근처에서
 *  floor(Math.sqrt(n)) 이 참값보다 1 크게 나오는 입력이 실제로 있기 때문이다.
 *  나눗셈만 쓰는 이 형태는 세 언어가 글자 그대로 같다. */
export function isqrt(n: number): number {
  if (n < 2) return n;
  let x = n;
  let y = Math.floor((x + 1) / 2);
  while (y < x) {
    x = y;
    y = Math.floor((x + Math.floor(n / x)) / 2);
  }
  return x;
}

export function fpSqrt(x: number): number {
  return isqrt(x * FP_ONE);
}

// 알파 맥스 플러스 베타 민 — 최소최대오차 최적 계수를 1024배 해 반올림한 것.
export const OCT_A = 983;
export const OCT_B = 407;

/** sqrt(dx^2+dy^2) 의 정수 근사. 곱셈 두 번과 나눗셈 한 번. */
export function octDist(dx: number, dy: number): number {
  const ax = dx >= 0 ? dx : -dx;
  const ay = dy >= 0 ? dy : -dy;
  const hi = ax > ay ? ax : ay;
  const lo = ax > ay ? ay : ax;
  return Math.floor((OCT_A * hi + OCT_B * lo) / 1024);
}

// ---------------------------------------------------------------- CORDIC (SPEC §2.6)
export const N_ITER = 20;
export const GUARD = 8;
export const ATAN_BRAD: number[] = [
  2097152, 1238021, 654136, 332050, 166669, 83416, 41718, 20860,
  10430, 5215, 2608, 1304, 652, 326, 163, 81, 41, 20, 10, 5,
];
export const K_INV = 10188014;

/** 16.16 brad 각도 -> [cos, sin] 16.16.
 *
 *  안쪽에서 가드 8비트를 들고 다니다 끝에서 반올림해 버린다.
 *  `y / 2^i` 를 `y >> i` 로 쓰고 싶어지는 자리인데, x·y 가 가드 때문에
 *  최대 2^24 를 넘나들어 32비트 안에는 들어가지만 음수 시프트 규칙이
 *  파이썬의 내림과 어긋난다. 그래서 여기서도 Math.floor 로 통일한다. */
export function cordic(theta: number): [number, number] {
  let t = fmod(theta, 256 * FP_ONE);
  const quad = Math.floor(t / (64 * FP_ONE));
  t -= quad * 64 * FP_ONE;
  let x = K_INV;
  let y = 0;
  let z = t;
  for (let i = 0; i < N_ITER; i++) {
    const d = z >= 0 ? 1 : -1;
    const p = pow2(i);
    const nx = x - d * Math.floor(y / p);
    const ny = y + d * Math.floor(x / p);
    z -= d * (ATAN_BRAD[i] as number);
    x = nx;
    y = ny;
  }
  x = Math.floor((x + 128) / 256);
  y = Math.floor((y + 128) / 256);
  if (quad === 0) return [x, y];
  if (quad === 1) return [-y, x];
  if (quad === 2) return [-x, -y];
  return [y, -x];
}

function buildTrig(): [number[], number[]] {
  const c: number[] = new Array<number>(256).fill(0);
  const s: number[] = new Array<number>(256).fill(0);
  for (let a = 0; a < 256; a++) {
    const cs = cordic(a * FP_ONE);
    c[a] = cs[0];
    s[a] = cs[1];
  }
  return [c, s];
}

const _trig = buildTrig();
export const COS: number[] = _trig[0];
export const SIN: number[] = _trig[1];

function nibTable(): number[] {
  const t: number[] = new Array<number>(256).fill(0);
  for (let a = 0; a < 16; a++) {
    for (let b = 0; b < 16; b++) {
      let r = 0;
      let p = 1;
      let x = a;
      let y = b;
      for (let k = 0; k < 4; k++) {
        if (x % 2 !== y % 2) r += p;
        x = Math.floor(x / 2);
        y = Math.floor(y / 2);
        p *= 2;
      }
      t[a * 16 + b] = r;
    }
  }
  return t;
}

export const NIB_XOR: number[] = nibTable();

/** 8비트 배타적 논리합. 니블 표 두 번이면 끝난다.
 *
 *  JS 에는 `^` 가 있고 8비트라면 안전하지만, 루아 5.1 판과 코드를 같게 두려고
 *  세 언어 모두 이 산술 형태를 쓴다. 어느 언어에서 읽어도 같은 함수임이 자명해진다. */
export function xor8(a: number, b: number): number {
  return (
    (NIB_XOR[Math.floor(a / 16) * 16 + Math.floor(b / 16)] as number) * 16 +
    (NIB_XOR[(a % 16) * 16 + (b % 16)] as number)
  );
}

/** 표 없이 만든 16비트 배타적 논리합. 한 비트씩 16번 — O(16). */
export function xor16(a: number, b: number): number {
  let r = 0;
  let p = 1;
  let x = a;
  let y = b;
  for (let i = 0; i < 16; i++) {
    if (x % 2 !== y % 2) r += p;
    x = Math.floor(x / 2);
    y = Math.floor(y / 2);
    p *= 2;
  }
  return r;
}

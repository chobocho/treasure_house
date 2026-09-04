// 헥스 좌표계 — SPEC §1, §4.4, §9.1
//
// 자바스크립트의 수는 IEEE754 배정밀도 하나뿐이다. 정수처럼 보이는 값도
// 실은 실수라, 도스식 정수 연산을 옮길 때 두 가지를 조심해야 한다.
//   1. 나눗셈 `/` 는 절대 정수를 주지 않는다. 반드시 Math.floor 나 `>>` 로 맞춘다.
//   2. `|0`, `>>`, `&` 는 값을 32비트로 잘라 버린다. 2^31 이 넘는 값에 쓰면
//      음수가 된다 — 32비트 LCG(rng.ts)에서 `>>> 0` 이 필요한 이유다.
// 여기서 다루는 좌표는 전부 작은 수라 `>>` 로 충분하다.

export type Axial = readonly [number, number];

// SPEC §1.5 — 방향 인덱스는 세이브·골든 트레이스의 일부라 순서가 불변이다.
export const DIRS: ReadonlyArray<readonly [number, number]> = [
  [1, 0], [1, -1], [0, -1], [-1, 0], [-1, 1], [0, 1],
];
export const DIR_NAMES = ['E', 'NE', 'NW', 'W', 'SW', 'SE'] as const;

export const SCALE = 1024;              // SPEC §9.1 고정소수 단위
export const NUDGE: readonly [number, number, number] = [1, 1, -2];

export function toCube(q: number, r: number): [number, number, number] {
  return [q, -q - r, r];
}

export function axialToOddr(q: number, r: number): [number, number] {
  return [q + ((r - (r & 1)) >> 1), r];
}

export function oddrToAxial(col: number, row: number): [number, number] {
  return [col - ((row - (row & 1)) >> 1), row];
}

export function axialToOddq(q: number, r: number): [number, number] {
  return [q, r + ((q - (q & 1)) >> 1)];
}

export function oddqToAxial(col: number, row: number): [number, number] {
  return [col, row - ((col - (col & 1)) >> 1)];
}

export function distance(aq: number, ar: number, bq: number, br: number): number {
  const dq = aq - bq;
  const dr = ar - br;
  return (Math.abs(dq) + Math.abs(dr) + Math.abs(dq + dr)) >> 1;
}

export function neighbor(q: number, r: number, d: number): [number, number] {
  const dd = DIRS[d]!;
  return [q + dd[0], r + dd[1]];
}

export function neighbors(q: number, r: number): Array<[number, number]> {
  return DIRS.map((d) => [q + d[0], r + d[1]] as [number, number]);
}

export function rotateCw(x: number, y: number, z: number): [number, number, number] {
  return [-y, -z, -x];
}

export function rotateCcw(x: number, y: number, z: number): [number, number, number] {
  return [-z, -x, -y];
}

export function rotateAbout(q: number, r: number, cq: number, cr: number,
                            steps: number): [number, number] {
  let [x, y, z] = toCube(q - cq, r - cr);
  for (let i = 0; i < ((steps % 6) + 6) % 6; i++) {
    [x, y, z] = rotateCw(x, y, z);
  }
  return [x + cq, z + cr];
}

export function reflectQ(x: number, y: number, z: number): [number, number, number] {
  return [x, z, y];
}

export function ring(cq: number, cr: number, n: number): Array<[number, number]> {
  if (n === 0) return [[cq, cr]];
  let q = cq + DIRS[4]![0] * n;
  let r = cr + DIRS[4]![1] * n;
  const out: Array<[number, number]> = [];
  for (let d = 0; d < 6; d++) {
    const dd = DIRS[d]!;
    for (let k = 0; k < n; k++) {
      out.push([q, r]);
      q += dd[0];
      r += dd[1];
    }
  }
  return out;
}

export function spiral(cq: number, cr: number, n: number): Array<[number, number]> {
  const out: Array<[number, number]> = [[cq, cr]];
  for (let k = 1; k <= n; k++) out.push(...ring(cq, cr, k));
  return out;
}

// d > 0 인 반올림 나눗셈, 동점은 0에서 먼 쪽. SPEC §4.4
// Math.round 는 -0.5 를 0 으로 올려 버려(항상 +∞ 방향) 파이썬·루아와 갈린다.
export function roundDiv(n: number, d: number): number {
  if (n >= 0) return Math.floor((2 * n + d) / (2 * d));
  return -Math.floor((-2 * n + d) / (2 * d));
}

export function cubeRound(xf: number, yf: number, zf: number,
                          scale: number = SCALE): [number, number] {
  let rx = roundDiv(xf, scale);
  let ry = roundDiv(yf, scale);
  let rz = roundDiv(zf, scale);
  const dx = Math.abs(rx * scale - xf);
  const dy = Math.abs(ry * scale - yf);
  const dz = Math.abs(rz * scale - zf);
  if (dx > dy && dx > dz) rx = -ry - rz;
  else if (dy > dz) ry = -rx - rz;
  else rz = -rx - ry;
  return [rx, rz];
}

export function line(aq: number, ar: number, bq: number, br: number): Array<[number, number]> {
  const n = distance(aq, ar, bq, br);
  let [ax, ay, az] = toCube(aq, ar);
  let [bx, by, bz] = toCube(bq, br);
  ax = ax * SCALE + NUDGE[0];
  ay = ay * SCALE + NUDGE[1];
  az = az * SCALE + NUDGE[2];
  bx *= SCALE; by *= SCALE; bz *= SCALE;
  if (n === 0) return [cubeRound(ax, ay, az)];
  const out: Array<[number, number]> = [];
  for (let i = 0; i <= n; i++) {
    const ti = Math.floor((i * SCALE) / n);
    out.push(cubeRound(ax + Math.floor(((bx - ax) * ti) / SCALE),
                       ay + Math.floor(((by - ay) * ti) / SCALE),
                       az + Math.floor(((bz - az) * ti) / SCALE)));
  }
  return out;
}

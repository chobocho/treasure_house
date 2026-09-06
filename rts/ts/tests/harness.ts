// 세 언어 공통의 아주 작은 테스트 하네스 (py/tests/harness.py 의 이식).
//
//    프레임워크를 쓰지 않는 이유는 하나다. 같은 테스트를 파이썬·루아·타입스크립트로
//    옮겨야 하는데, 프레임워크가 다르면 출력이 달라지고 출력이 달라지면 덱에 실을
//    로그도 달라진다. 그래서 '이름 · 기대 · 실제' 만 찍는다.
//
//    파이썬 하네스는 파일마다 별도 프로세스라 done() 에서 sys.exit 한다.
//    여기서는 run.ts 가 한 프로세스에서 전부 돌리므로 done() 은 요약만 찍고
//    실패 여부를 전역에 누적한다 — 종료 코드는 run.ts 가 정한다.

import * as fs from 'fs';
import * as path from 'path';

import { pyRepr } from '../src/fmt';

export const BASE = path.join(__dirname, '..', '..', '..');
export const GOLDEN = path.join(BASE, 'golden');

let ok = 0;
let bad = 0;
let name = '?';
let totalOk = 0;
let totalBad = 0;

export function title(n: string): void {
  name = n;
  ok = 0;
  bad = 0;
  process.stdout.write('== ' + n + ' ==\n');
}

// 파이썬의 == 는 리스트·튜플을 내용으로 비교한다. 여기서도 같은 뜻이 되도록
// 배열을 재귀로 훑는다. (파이썬은 튜플과 리스트를 구별하지만 여기서는 둘 다
// 배열이 되므로 그 구별만은 잃는다 — 단언의 뜻이 달라지는 자리는 없다.)
export function deepEq(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i += 1) {
      if (!deepEq(a[i], b[i])) return false;
    }
    return true;
  }
  return false;
}

export function check(what: string, got: unknown, want: unknown): boolean {
  const same = deepEq(got, want);
  if (same) {
    ok += 1;
  } else {
    bad += 1;
    process.stdout.write('  실패 ' + what + '\n');
    process.stdout.write('    기대 ' + pyRepr(want) + '\n');
    process.stdout.write('    실제 ' + pyRepr(got) + '\n');
  }
  return same;
}

export function checkTrue(what: string, cond: unknown): boolean {
  return check(what, Boolean(cond), true);
}

export function note(s: string): void {
  process.stdout.write('  ' + s + '\n');
}

export function golden(n: string): string {
  return fs.readFileSync(path.join(GOLDEN, n), 'utf8');
}

export function goldenBytes(n: string): number[] {
  const buf = fs.readFileSync(path.join(GOLDEN, n));
  const out: number[] = [];
  for (let i = 0; i < buf.length; i += 1) out.push(buf[i]);
  return out;
}

export function done(): void {
  process.stdout.write(name + ': 통과 ' + ok + ' · 실패 ' + bad + '\n');
  totalOk += ok;
  totalBad += bad;
}

export function totals(): [number, number] {
  return [totalOk, totalBad];
}

// ── 파이썬스러운 소품들 — 시험 코드가 원본과 눈으로 대조되도록 ──────────────
export function range(a: number, b?: number, step?: number): number[] {
  const lo = b === undefined ? 0 : a;
  const hi = b === undefined ? a : b;
  const st = step === undefined ? 1 : step;
  const out: number[] = [];
  if (st > 0) for (let v = lo; v < hi; v += st) out.push(v);
  else for (let v = lo; v > hi; v += st) out.push(v);
  return out;
}

export function sum(a: ArrayLike<number>): number {
  let t = 0;
  for (let i = 0; i < a.length; i += 1) t += a[i];
  return t;
}

export function maxOf(a: ArrayLike<number>): number {
  let m = a[0];
  for (let i = 1; i < a.length; i += 1) if (a[i] > m) m = a[i];
  return m;
}

export function minOf(a: ArrayLike<number>): number {
  let m = a[0];
  for (let i = 1; i < a.length; i += 1) if (a[i] < m) m = a[i];
  return m;
}

// 파이썬 sorted(set(x)) — 값의 중복을 없애고 오름차순으로.
export function sortedSet(a: ArrayLike<number>): number[] {
  const seen = new Set<number>();
  for (let i = 0; i < a.length; i += 1) seen.add(a[i]);
  const out = Array.from(seen);
  out.sort((x, y) => x - y);
  return out;
}

export function sortedNums(a: ArrayLike<number>): number[] {
  const out: number[] = [];
  for (let i = 0; i < a.length; i += 1) out.push(a[i]);
  out.sort((x, y) => x - y);
  return out;
}

// 배열(튜플)의 사전식 비교 — 파이썬의 튜플 비교와 같다.
export function cmpArr(a: number[], b: number[]): number {
  const n = a.length < b.length ? a.length : b.length;
  for (let i = 0; i < n; i += 1) {
    if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  }
  return a.length - b.length;
}

export function sortedTuples(a: number[][]): number[][] {
  const out = a.map((t) => t.slice());
  out.sort(cmpArr);
  return out;
}

// glibc 계열 LCG — 여러 시험이 표본을 만들 때 쓴다. 1103515245 * r 은 2^61 까지
// 커져 배정밀도 가수(53비트)를 넘으므로 여기서도 분할 곱을 쓴다.
export function lcg31(r: number): number {
  const A = 1103515245;
  const hi = Math.floor(r / 65536);
  const lo = r % 65536;
  return (A * lo + ((A * hi) % 32768) * 65536 + 12345) % 2147483648;
}

// 한 줄을 공백으로 쪼갠다 (파이썬 str.split() 과 같다 — 앞뒤 공백은 버린다).
export function fields(line: string): string[] {
  const t = line.trim();
  return t === '' ? [] : t.split(/\s+/);
}

export function ints(line: string): number[] {
  return fields(line).map((s) => parseInt(s, 10));
}

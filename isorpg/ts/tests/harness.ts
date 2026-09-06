// 세 언어 공통의 아주 작은 테스트 하네스 (파이썬 py/tests/harness.py 와 같은 출력).
//
// 파이썬 쪽은 파일 하나가 곧 프로세스 하나라 done() 에서 sys.exit 를 부른다.
// 노드에서는 한 프로세스가 열두 모듈을 이어 돌리는 편이 훨씬 빠르므로
// done() 은 실패 수만 돌려주고, 종료 코드는 run.ts 가 마지막에 한 번만 정한다.
import * as fs from 'fs';
import * as path from 'path';

// dist/tests -> dist -> ts -> isorpg
export const BASE = path.resolve(__dirname, '..', '..', '..');
export const GOLDEN = path.join(BASE, 'golden');

let okCount = 0;
let badCount = 0;
let curName = '?';

export function title(name: string): void {
  curName = name;
  okCount = 0;
  badCount = 0;
  console.log('== ' + name + ' ==');
}

/** 파이썬의 %r 자리. 배열·객체까지 눈으로 견줄 수 있으면 충분하다. */
export function show(v: unknown): string {
  if (typeof v === 'string') return JSON.stringify(v);
  if (v instanceof Uint8Array) return '[' + Array.from(v).join(',') + ']';
  if (Array.isArray(v)) return '[' + v.map(show).join(', ') + ']';
  return String(v);
}

/** 파이썬의 == 는 리스트·튜플을 값으로 견준다. JS 의 === 는 참조를 견주므로
 *  구조 비교를 직접 만든다. 이것이 이식에서 가장 자주 새는 구멍이다. */
export function deepEq(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  const au = a instanceof Uint8Array;
  const bu = b instanceof Uint8Array;
  if (au || bu) {
    if (!au || !bu) return false;
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) if (!deepEq(a[i], b[i])) return false;
    return true;
  }
  return false;
}

export function check(what: string, got: unknown, want: unknown): boolean {
  if (deepEq(got, want)) {
    okCount += 1;
    return true;
  }
  badCount += 1;
  console.log('  실패 ' + what);
  console.log('    기대 ' + show(want));
  console.log('    실제 ' + show(got));
  return false;
}

export function checkTrue(what: string, cond: boolean): boolean {
  return check(what, !!cond, true);
}

export function note(text: string): void {
  console.log('  ' + text);
}

export function golden(name: string): string {
  return fs.readFileSync(path.join(GOLDEN, name), 'utf8');
}

/** 요약 한 줄을 찍고 실패 수를 돌려준다. */
export function done(): number {
  console.log(curName + ': 통과 ' + okCount + ' · 실패 ' + badCount);
  return badCount;
}

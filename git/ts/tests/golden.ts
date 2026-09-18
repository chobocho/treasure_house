// 시험 도우미 — golden/ 을 읽고 재료를 바이트로 만든다.
//
// golden/ 은 진짜 git 이 만든 기준 바이트다(SPEC.md §16.2). 시험은 git
// 을 부르지 않고 이 파일들만 읽는다. 재료 문법은 SPEC.md §2.1·§16.4
// 이고, tools/make_golden.py 의 make() 와 같은 규칙이다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { GitError } from '../src/errors';

// 짓고 나면 이 파일은 build/ts/tests/ 에 있다 — git/ 은 셋 위다
export const GOLDEN = path.resolve(__dirname, '../../../golden');

export function gpath(...parts: string[]): string {
  return path.join(GOLDEN, ...parts);
}

export function read(...parts: string[]): Buffer {
  return fs.readFileSync(gpath(...parts));
}

// 주석(#)과 머리 줄을 뺀 행들. 각 행은 칸 이름 → 값.
export function tsv(...parts: string[]): Record<string, string>[] {
  const rows: Record<string, string>[] = [];
  let head: string[] | null = null;
  for (const line of read(...parts).toString('utf8').split('\n')) {
    if (!line || line.startsWith('#')) continue;
    const cols = line.split('\t');
    if (head === null) {
      head = cols;
      continue;
    }
    const row: Record<string, string> = {};
    head.forEach((h, i) => {
      if (i < cols.length) row[h] = cols[i];
    });
    rows.push(row);
  }
  return rows;
}

// text: 재료의 이스케이프 — \n \t \\ \" \xHH.
export function unescape(s: string): Buffer {
  const raw = Buffer.from(s, 'utf8');
  const out: number[] = [];
  for (let i = 0; i < raw.length; i++) {
    if (raw[i] !== 0x5c || i + 1 >= raw.length) {
      out.push(raw[i]);
      continue;
    }
    const n = String.fromCharCode(raw[i + 1]);
    if (n === 'x') {
      out.push(parseInt(raw.subarray(i + 2, i + 4).toString(), 16));
      i += 3;
    } else {
      out.push(n === 'n' ? 10 : n === 't' ? 9 : raw[i + 1]);
      i += 1;
    }
  }
  return Buffer.from(out);
}

// 재료 한 줄 → 바이트 (SPEC.md §2.1). O(결과 길이).
export function make(recipe: string): Buffer {
  const at = recipe.indexOf(':');
  const kind = at < 0 ? recipe : recipe.slice(0, at);
  const arg = at < 0 ? '' : recipe.slice(at + 1);
  switch (kind) {
    case 'empty':
      return Buffer.alloc(0);
    case 'text':
      return unescape(arg);
    case 'repeat': {
      const [byte, n] = arg.split(':');
      return Buffer.alloc(Number(n), parseInt(byte, 16));
    }
    case 'counter':
      return Buffer.from(
        Array.from({ length: Number(arg) }, (_, i) => i % 251));
    case 'seq': {
      const [a, b] = arg.split(':').map(Number);
      let s = '';
      for (let i = a; i <= b; i++) s += `${i}\n`;
      return Buffer.from(s);
    }
    case 'golden':
      return read(arg);
  }
  throw new Error(`모르는 재료: ${recipe}`);
}

// fn() 이 **진짜** GitError 를 던지는가.
//
// 껍데기(notImplemented)도 GitError 를 던지므로 그냥 assert.throws 로
// 보면 구현 전에 이미 통과한다 — 거짓 초록이다. 코드 99 는 "아직 안
// 짰다" 라서 여기서 떨어뜨린다. 던져진 오류를 돌려준다.
export function assertGitError(fn: () => unknown): GitError {
  let got: unknown = null;
  try {
    fn();
  } catch (e) {
    got = e;
  }
  assert.ok(got instanceof GitError, `GitError 가 아니다: ${got}`);
  assert.notEqual(got.code, 99, 'not implemented');
  return got;
}

// 시험마다 새 임시 디렉터리. 지우는 쪽은 rmTree.
export function tempdir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'mygit-'));
}

export function rmTree(dir: string): void {
  fs.rmSync(dir, { recursive: true, force: true });
}

// git 이 C 식으로 이스케이프한 경로(따옴표 안쪽) → 바이트.
//
// \t \n \" \\ 와 세 자리 8진 \ooo 만 나온다(SPEC.md §8.2). 시험에서
// git 의 출력을 읽을 때만 쓴다.
export function unescapeC(s: string): Buffer {
  const esc: Record<string, number> = { a: 7, b: 8, t: 9, n: 10, v: 11,
    f: 12, r: 13, '"': 34, '\\': 92 };
  const out: number[] = [];
  for (let i = 0; i < s.length;) {
    if (s[i] !== '\\') {
      out.push(...Buffer.from(s[i++]));
    } else if (s[i + 1] in esc) {
      out.push(esc[s[i + 1]]);
      i += 2;
    } else {
      out.push(parseInt(s.slice(i + 1, i + 4), 8));
      i += 4;
    }
  }
  return Buffer.from(out);
}

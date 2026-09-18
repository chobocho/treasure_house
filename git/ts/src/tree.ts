// tree (SPEC.md §4.3) — 디렉터리 하나를 객체 하나로.
//
// 항목 = "<모드> <이름>\0<객체 이름 20바이트>". 이름과 권한은 blob 이
// 아니라 트리가 갖는다 — 같은 내용의 파일 둘은 blob 하나를 나눠 쓴다.
//
// **정렬 규칙이 전부다.** 항목은 이름의 바이트로 정렬하되 하위 트리는
// 이름 뒤에 '/' 가 붙은 것처럼 비교한다. 규칙을 한 글자만 어겨도
// 내용은 같고 이름이 다른 트리가 생기고, git 은 그것을 다른 역사로
// 본다.
//
// 이름·경로는 "바이트 문자열" 이다 — latin1 로 풀어 글자 하나가 바이트
// 하나인 string. JS 의 문자열 비교는 UTF-16 단위라 한글이 섞이면
// 바이트 차례와 어긋나지만(SPEC.md §1.5), 모든 글자가 0‥255 이면
// 문자열 비교가 곧 바이트 비교다. 올바른 UTF-8 이 아닌 이름도 그대로
// 살아남는다.
import { GitError } from './errors';
import * as objects from './objects';

export const DIR = '40000';
// 트리 몸의 항목 하나와, 경로로 펼친 항목 하나
export type TreeEntry = [mode: string, name: string, oid: string];
export type PathEntry = [mode: string, oid: string, path: string];

// 정렬 열쇠. 하위 트리는 이름에 '/' 를 붙여 비교한다.
export function treeEntryKey(mode: string, name: string): string {
  return mode === DIR ? name + '/' : name;
}

// 트리 몸 → [모드, 이름, 객체 이름 16진]. 적힌 차례 그대로.
// O(몸의 길이). 몸이 중간에 끊기면 오류다.
export function parseTree(body: Buffer): TreeEntry[] {
  const out: TreeEntry[] = [];
  for (let i = 0; i < body.length;) {
    const sp = body.indexOf(0x20, i);
    const nul = body.indexOf(0, sp + 1);
    if (sp < 0 || nul < 0 || nul + 21 > body.length) {
      throw new GitError('fatal: mygit: corrupt tree object');
    }
    out.push([body.toString('latin1', i, sp),
      body.toString('latin1', sp + 1, nul),
      body.toString('hex', nul + 1, nul + 21)]);
    i = nul + 21;
  }
  return out;
}

// [모드, 이름, 객체 이름] → 트리 몸. 정렬은 여기서 한다.
//
// 모드는 앞에 0 을 붙이지 않는다 — 디렉터리는 '40000' 다섯 글자다.
// '040000' 은 cat-file -p 가 찍어 보일 때의 꼴일 뿐이다.
export function serializeTree(entries: TreeEntry[]): Buffer {
  const key = ([m, n]: TreeEntry) => treeEntryKey(m, n);
  const ents = [...entries].sort((x, y) =>
    key(x) < key(y) ? -1 : key(x) > key(y) ? 1 : 0);
  return Buffer.concat(ents.flatMap(([m, n, o]) =>
    [Buffer.from(`${m} ${n}\0`, 'latin1'), Buffer.from(o, 'hex')]));
}

// [모드, blob 이름, 경로] → 뿌리 트리 이름.
//
// 경로를 '/' 로 나눠 디렉터리마다 트리를 짓고, 아래에서 위로 쓴다.
// blob 이 저장소에 있는지는 보지 않는다(git write-tree 는 본다 — 이
// 함수를 부르는 쪽이 인덱스에 올릴 때 이미 써 두었다).
// O(항목 수 × 깊이 + 정렬).
export function writeTree(gitdir: string, entries: PathEntry[]):
  string {
  const here: TreeEntry[] = [];
  const subdirs = new Map<string, PathEntry[]>();
  for (const [mode, oid, p] of entries) {
    const slash = p.indexOf('/');
    if (slash < 0) {
      here.push([mode, p, oid]);
      continue;
    }
    const head = p.slice(0, slash);
    if (!subdirs.has(head)) subdirs.set(head, []);
    subdirs.get(head)!.push([mode, oid, p.slice(slash + 1)]);
  }
  for (const [name, sub] of subdirs) {
    here.push([DIR, name, writeTree(gitdir, sub)]);
  }
  return objects.writeObject(gitdir, 'tree', serializeTree(here));
}

// 트리를 재귀로 펼쳐 [모드, 이름, 경로]. 하위 트리는 항목으로
// 남기지 않고 그 안을 펼친다. 차례는 트리 차례이고, 전체 경로의
// 바이트 차례와 같다(SPEC.md §4.3).
export function flattenTree(gitdir: string, oid: string, prefix = ''):
  PathEntry[] {
  const [type, body] = objects.readObject(gitdir, oid);
  if (type !== 'tree') {
    throw new GitError(`fatal: mygit: ${oid} is not a tree`);
  }
  return parseTree(body).flatMap(([mode, name, sub]): PathEntry[] =>
    mode === DIR ? flattenTree(gitdir, sub, prefix + name + '/')
      : [[mode, sub, prefix + name]]);
}

// cat-file -p 가 찍는 형식 — 모드에서 정해진다.
export function typeOfMode(mode: string): string {
  if (mode === DIR) return 'tree';
  if (mode === '160000') return 'commit';
  return 'blob';
}

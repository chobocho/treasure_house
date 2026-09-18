// 작업 트리 (SPEC.md §8) — 경로 따옴표, 훑기, status.
//
// status 는 세 가지를 견준다: HEAD 트리, 인덱스, 디스크의 파일. 두 칸
// 글자(XY)가 곧 "어느 두 곳이 다른가" 다 — X 는 HEAD 와 인덱스, Y 는
// 인덱스와 작업 트리. 6부가 이 세 영역을 명령마다 캡처로 보인다.
//
// 경로는 바이트 문자열(latin1, tree.ts 머리 주석)로 다루고, 파일
// 시스템에 건넬 때만 fsPath 로 진짜 바이트(Buffer)를 만든다 — node 의
// fs 는 Buffer 경로를 받으면 UTF-8 로 되풀지 않고 그대로 쓴다.
import * as fs from 'node:fs';
import * as index from './index';
import * as objects from './objects';
import * as refs from './refs';
import * as tree from './tree';

// 파일 하나의 모습 — [모드, blob 이름]. Python 의 튜플 비교(==) 자리에
// same 을 쓴다. 둘 다 없음(null·undefined)도 같은 것으로 본다.
export type Stat = [mode: number, oid: string];
export const same = (a?: Stat | null, b?: Stat | null) =>
  a?.[0] === b?.[0] && a?.[1] === b?.[1];

// 뿌리(보통 문자열) + 경로(바이트 문자열) → 파일 시스템의 경로 바이트.
export function fsPath(root: string, p: string): Buffer {
  return Buffer.concat([Buffer.from(root),
    Buffer.from(p && '/' + p, 'latin1')]);
}

// \a \b \t \n \v \f \r 와 따옴표·역슬래시는 두 글자로 쓴다
const SHORT: Record<number, string> = { 7: 'a', 8: 'b', 9: 't',
  10: 'n', 11: 'v', 12: 'f', 13: 'r', 34: '"', 92: '\\' };

// 경로 바이트 → git 이 사람에게 찍는 꼴 (core.quotePath=true).
//
// 제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
// 전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space=true 는
// status 의 규칙 — 공백만 있어도 감싼다(공백 자체는 그대로).
// 한글은 UTF-8 여섯 바이트가 \355\225… 로 찍힌다. O(경로 길이).
// 그래서 돌려주는 문자열은 언제나 ASCII 다.
export function quotePath(p: string, space = false): string {
  let need = space && p.includes(' ');
  let body = '';
  for (let i = 0; i < p.length; i++) {
    const b = p.charCodeAt(i);
    if (b in SHORT) {
      body += '\\' + SHORT[b];
      need = true;
    } else if (b < 32 || b >= 127) {
      body += '\\' + b.toString(8).padStart(3, '0');
      need = true;
    } else {
      body += p[i];
    }
  }
  return need ? `"${body}"` : body;
}

// 작업 트리의 보통 파일 경로들, 전체 경로의 바이트 차례.
//
// 어느 깊이에서든 '.git' 은 건너뛰고, 심볼릭 링크와 장치 파일은
// 없는 것으로 본다(SPEC.md §8.1). 빈 디렉터리는 아무것도 아니다.
// readdir 의 Dirent 는 링크를 따라가지 않으므로 링크는 isFile·
// isDirectory 어느 쪽도 아니다. O(파일 수 · log).
export function walkWorktree(root: string): string[] {
  const out: string[] = [];
  const visit = (prefix: string): void => {
    const ents = fs.readdirSync(fsPath(root, prefix.slice(0, -1)),
      { withFileTypes: true, encoding: 'buffer' });
    for (const ent of ents) {
      const name = ent.name.toString('latin1');
      if (name === '.git') continue;
      if (ent.isDirectory()) visit(prefix + name + '/');
      else if (ent.isFile()) out.push(prefix + name);
    }
  };
  visit('');
  return out.sort();
}

// [모드, blob 이름] 또는 파일이 없으면 null. 늘 해시한다 — stat
// 캐시를 믿지 않으니 racy git 이 없다(SPEC.md §7.2).
export function fileState(root: string, p: string): Stat | null {
  const full = fsPath(root, p);
  const st = fs.lstatSync(full, { throwIfNoEntry: false });
  if (!st?.isFile()) return null;
  const mode = st.mode & 0o100 ? 0o100755 : 0o100644;
  return [mode, objects.hashObject('blob', fs.readFileSync(full))];
}

// 충돌 경로의 두 글자 — 단계 1, 2, 3 이 있는가('1'·'0' 세 자리) → XY
// (git 과 같다)
const UNMERGED: Record<string, string> = { '011': 'AA', '111': 'UU',
  '110': 'UD', '101': 'DU', '010': 'AU', '001': 'UA', '100': 'DD' };

// 추적하지 않는 파일들을 git 의 normal 모드로 접는다(§8.3).
//
// 파일마다 위쪽 디렉터리부터 보며, 그 아래에 인덱스 항목이 하나도
// 없는 첫 디렉터리가 있으면 "그 디렉터리/" 로 접는다. O(파일 × 깊이).
function untracked(files: string[], tracked: Set<string>): string[] {
  const dirs = new Set<string>();
  for (const t of tracked) {
    const parts = t.split('/');
    for (let i = 1; i < parts.length; i++) {
      dirs.add(parts.slice(0, i).join('/'));
    }
  }
  const out = new Set<string>();
  for (const f of files) {
    if (tracked.has(f)) continue;
    const parts = f.split('/');
    let shown = f;
    for (let i = 1; i < parts.length; i++) {
      const d = parts.slice(0, i).join('/');
      if (!dirs.has(d)) {
        shown = d + '/';
        break;
      }
    }
    out.add(shown);
  }
  return [...out].sort();
}

// 트리 → {경로: [모드, 이름]}. 트리가 없으면(첫 커밋 전) 빈 표.
export function treeMap(gitdir: string, treeOid: string | null):
  Map<string, Stat> {
  if (!treeOid) return new Map();
  return new Map(tree.flattenTree(gitdir, treeOid)
    .map(([m, o, p]) => [p, [parseInt(m, 8), o]]));
}

// 여러 표의 열쇠를 모아 바이트 차례로
export const sortedKeys = (...maps: { keys(): Iterable<string> }[]) =>
  [...new Set(maps.flatMap((m) => [...m.keys()]))].sort();

// git status --porcelain 과 같은 줄들(SPEC.md §8.3).
//
// X = HEAD 트리 ↔ 인덱스, Y = 인덱스 ↔ 작업 트리. 추적 중인 것을
// 경로 차례로 먼저, 그다음 '?? ' 줄들. O(파일 수 × 해시).
export function status(root: string, gitdir: string): string[] {
  const [, head] = refs.readHead(gitdir);
  const base = treeMap(gitdir, head && refs.peel(gitdir, head, 'tree'));
  const stage0 = new Map<string, Stat>();
  const stages = new Map<string, Set<number>>();
  for (const e of index.readIndex(gitdir)) {
    if (e.stage) {
      if (!stages.has(e.path)) stages.set(e.path, new Set());
      stages.get(e.path)!.add(e.stage);
    } else {
      stage0.set(e.path, [e.mode, e.oid]);
    }
  }
  const rows: string[] = [];
  for (const p of sortedKeys(base, stage0, stages)) {
    let xy: string;
    const got = stages.get(p);
    if (got) {
      xy = UNMERGED[[1, 2, 3].map((k) => +got.has(k)).join('')];
    } else {
      const x = !stage0.has(p) ? 'D' : !base.has(p) ? 'A'
        : same(stage0.get(p), base.get(p)) ? ' ' : 'M';
      let y = ' ';
      if (stage0.has(p)) {
        const now = fileState(root, p);
        if (now === null) y = 'D';
        else if (!same(now, stage0.get(p))) y = 'M';
      }
      xy = x + y;
    }
    if (xy !== '  ') rows.push(`${xy} ${quotePath(p, true)}`);
  }
  const tracked = new Set([...stage0.keys(), ...stages.keys()]);
  for (const p of untracked(walkWorktree(root), tracked)) {
    rows.push(`?? ${quotePath(p, true)}`);
  }
  return rows;
}

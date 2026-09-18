// 참조 (SPEC.md §6) — 브랜치는 40글자가 든 파일 하나다.
//
// refs/heads/main 은 커밋 이름 한 줄이고, HEAD 는 보통
// "ref: refs/heads/main" 이라는 이름표를 가리키는 이름표다. 커밋이
// 생기면 브랜치 파일의 한 줄이 바뀔 뿐이다 — 브랜치를 만드는 값이 싼
// 까닭이 이것이다.
//
// gc 뒤의 저장소는 참조를 packed-refs 한 파일에 모아 두므로 읽을 때는
// 둘 다 본다(느슨한 파일이 이긴다). 쓸 때는 느슨한 파일만 쓴다.
import * as fs from 'node:fs';
import * as path from 'node:path';
import { GitError } from './errors';
import * as objects from './objects';

export const ZERO = '0'.repeat(40);
export type Ref = ['sym' | 'oid', string];
export type Reflog = [old: string, next: string, ident: string,
  message: string];

function readText(file: string): string | null {
  try {
    return fs.readFileSync(file, 'utf8');
  } catch {
    return null;
  }
}

// packed-refs → {이름: 40글자}. '#' 머리와 '^' 줄은 건너뛴다.
function packedRefs(gitdir: string): Map<string, string> {
  const out = new Map<string, string>();
  const text = readText(path.join(gitdir, 'packed-refs')) ?? '';
  for (const line of text.split('\n')) {
    if (!line || '#^'.includes(line[0])) continue;
    const sp = line.indexOf(' ');
    out.set(line.slice(sp + 1), line.slice(0, sp));
  }
  return out;
}

// ['sym', 대상] · ['oid', 40글자] · null. 느슨한 파일이 먼저다.
export function readRef(gitdir: string, name: string): Ref | null {
  const text = readText(path.join(gitdir, name))?.trim();
  if (text !== undefined) {
    return text.startsWith('ref: ') ? ['sym', text.slice(5)]
      : ['oid', text];
  }
  const oid = packedRefs(gitdir).get(name);
  return oid ? ['oid', oid] : null;
}

// 심볼릭 참조를 따라가 40글자. 없거나 태어나지 않았으면 null.
export function resolveRef(gitdir: string, name: string):
  string | null {
  for (let k = 0; k < 5; k++) {
    const r = readRef(gitdir, name);
    if (r === null) return null;
    if (r[0] === 'oid') return r[1];
    name = r[1];
  }
  throw new GitError(`fatal: mygit: symbolic ref loop at ${name}`);
}

// [HEAD 가 가리키는 브랜치 참조 이름 또는 null, 커밋 또는 null].
export function readHead(gitdir: string):
  [string | null, string | null] {
  const r = readRef(gitdir, 'HEAD');
  if (r === null) throw new GitError('fatal: mygit: HEAD is missing');
  if (r[0] === 'sym') return [r[1], resolveRef(gitdir, r[1])];
  return [null, r[1]];
}

// prefix 아래 참조 [이름, 40글자], 이름의 바이트 차례.
export function listRefs(gitdir: string, prefix = 'refs/'):
  [string, string][] {
  const found = new Map([...packedRefs(gitdir)]
    .filter(([n]) => n.startsWith(prefix)));
  const visit = (rel: string): void => {
    const dir = path.join(gitdir, rel);
    if (!fs.existsSync(dir)) return;
    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      const name = path.posix.join(rel, ent.name);
      if (ent.isDirectory()) {
        visit(name);
      } else if (!ent.name.endsWith('.lock')) {
        const oid = resolveRef(gitdir, name);
        if (oid) found.set(name, oid);
      }
    }
  };
  visit(prefix);
  // 이름은 UTF-8 로 푼 문자열이라, 바이트 차례는 되돌려 견준다
  return [...found].sort(([a], [b]) =>
    Buffer.compare(Buffer.from(a), Buffer.from(b)));
}

// <경로>.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §6.1). 'wx' 는
// O_CREAT|O_EXCL — 이미 있으면 누군가 쓰는 중이다.
function writeLocked(file: string, text: string): void {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  try {
    fs.writeFileSync(file + '.lock', text, { flag: 'wx' });
  } catch (e) {
    if ((e as NodeJS.ErrnoException).code !== 'EEXIST') throw e;
    throw new GitError(`fatal: mygit: unable to lock ${file}`);
  }
  fs.renameSync(file + '.lock', file);
}

// reflog 한 줄(SPEC.md §6.3) — "옛 새 신원<TAB>메시지".
export function appendReflog(gitdir: string, name: string,
  old: string | null, next: string | null, ident: string,
  message: string): void {
  const file = path.join(gitdir, 'logs', name);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file,
    `${old ?? ZERO} ${next ?? ZERO} ${ident}\t${message}\n`);
}

// [옛, 새, 신원, 메시지], 오래된 것부터. 없으면 [].
export function readReflog(gitdir: string, name: string): Reflog[] {
  const text = readText(path.join(gitdir, 'logs', name)) ?? '';
  return text.split('\n').filter((l) => l).map((line) => {
    const tab = line.indexOf('\t');
    const head = tab < 0 ? line : line.slice(0, tab);
    const [old, next] = head.split(' ', 2);
    const ident = head.slice(old.length + next.length + 2);
    return [old, next, ident, tab < 0 ? '' : line.slice(tab + 1)];
  });
}

// 참조 하나를 바꾸고 reflog 를 남긴다. next 가 null 이면 지운다.
//
// HEAD 가 이 브랜치를 가리키고 있으면 HEAD 의 reflog 에도 같은 줄을
// 남긴다 — git 과 같다(커밋 하나가 두 로그에 모두 보이는 까닭).
// packed-refs 에만 있는 참조를 지우는 일은 줄임이다(SPEC.md §6.1).
export function updateRef(gitdir: string, name: string,
  next: string | null, old: string | null, message: string,
  ident: string): void {
  const file = path.join(gitdir, name);
  if (next === null) {
    if (!fs.existsSync(file)) {
      throw new GitError(
        `fatal: mygit: cannot delete packed ref ${name}`);
    }
    fs.rmSync(file);
    fs.rmSync(path.join(gitdir, 'logs', name), { force: true });
    return;
  }
  writeLocked(file, next + '\n');
  appendReflog(gitdir, name, old, next, ident, message);
  const head = readRef(gitdir, 'HEAD');
  if (name !== 'HEAD' && head?.[0] === 'sym' && head[1] === name) {
    appendReflog(gitdir, 'HEAD', old, next, ident, message);
  }
}

// HEAD 를 브랜치(refs/heads/…)나 커밋(분리)으로. reflog 는 부르는
// 쪽이 적는다 — 메시지가 명령마다 다르다(§6.3 의 표).
export function setHead(gitdir: string, target: string): void {
  writeLocked(path.join(gitdir, 'HEAD'),
    target.startsWith('refs/') ? `ref: ${target}\n` : target + '\n');
}

// ── 이름 풀기 (SPEC.md §6.2) ──────────────────────────────────────

// 뒤붙이 없는 이름 → 40글자 또는 null. §6.2 의 1‥5 차례.
function base(gitdir: string, name: string): string | null {
  if (/^[0-9a-f]{40}$/.test(name) && objects.findObject(gitdir, name)) {
    return name;
  }
  if (['HEAD', 'ORIG_HEAD', 'MERGE_HEAD'].includes(name)) {
    return resolveRef(gitdir, name);
  }
  if (name.startsWith('refs/')) {
    const oid = resolveRef(gitdir, name);
    if (oid) return oid;
  }
  for (const cand of [`refs/tags/${name}`, `refs/heads/${name}`,
    `refs/remotes/${name}`, `refs/remotes/${name}/HEAD`]) {
    const oid = resolveRef(gitdir, cand);
    if (oid) return oid;
  }
  try {
    return objects.findObject(gitdir, name);
  } catch (e) {
    if (e instanceof GitError) return null; // 모호한 앞부분은 못 푼 것
    throw e;
  }
}

// 태그를 벗겨 want('commit'·'tree')를 얻는다. 못 얻으면 null.
export function peel(gitdir: string, oid: string, want: string):
  string | null {
  for (let k = 0; k < 10; k++) {
    const [t, body] = objects.readObject(gitdir, oid);
    if (t === want) return oid;
    const first = body.toString('latin1').split('\n', 1)[0];
    if (t === 'tag') oid = first.slice(7);          // "object <40>"
    else if (t === 'commit' && want === 'tree') oid = first.slice(5);
    else return null;
  }
  return null;
}

function parents(gitdir: string, oid: string): string[] {
  const [, body] = objects.readObject(gitdir, oid);
  return body.toString('latin1').split('\n\n', 1)[0].split('\n')
    .filter((l) => l.startsWith('parent ')).map((l) => l.slice(7));
}

// <rev> → 40글자 또는 null. ~n · ^n · ^0 · ^{tree} · ^{commit}.
//
// 뒤붙이는 왼쪽부터 차례로 적용한다. O(뒤붙이의 길이 × 객체 읽기).
export function revParse(gitdir: string, spec: string): string | null {
  let i = 0;
  while (i < spec.length && !'~^'.includes(spec[i])) i++;
  let oid = i ? base(gitdir, spec.slice(0, i)) : null;
  while (oid && i < spec.length) {
    const op = spec[i++];
    if (op === '^' && spec[i] === '{') {
      const end = spec.indexOf('}', i);
      if (end < 0) return null;
      const want = spec.slice(i + 1, end);
      i = end + 1;
      oid = peel(gitdir, oid, want || 'commit');
      continue;
    }
    let j = i;
    while (j < spec.length && spec[j] >= '0' && spec[j] <= '9') j++;
    const n = j > i ? Number(spec.slice(i, j)) : 1;
    i = j;
    oid = peel(gitdir, oid, 'commit');
    if (oid === null) return null;
    if (op === '~') {
      for (let k = 0; k < n && oid; k++) {
        oid = parents(gitdir, oid)[0] ?? null;
      }
    } else if (n) {
      oid = parents(gitdir, oid)[n - 1] ?? null;
    }
  }
  return oid;
}

// SPEC.md §9.2 의 브랜치 이름 규칙(check-ref-format 의 일부).
export function validBranchName(name: string): boolean {
  if (!name || name === '@' || name.includes('..') ||
    name.includes('@{')) {
    return false;
  }
  for (const c of name) {
    const n = c.charCodeAt(0);
    if (' ~^:?*[\\'.includes(c) || n < 32 || n === 127) return false;
  }
  if ('-./'.includes(name[0]) ||
    ['/', '.', '.lock'].some((s) => name.endsWith(s))) {
    return false;
  }
  return !name.includes('//');
}

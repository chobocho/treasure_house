// 인덱스 (SPEC.md §7) — .git/index, 다음 커밋이 될 트리의 초안.
//
// 작업 트리와 저장소 사이의 이 파일 하나가 "스테이징" 의 실체다.
// 항목마다 경로·모드·blob 이름과 함께 파일의 stat 칸(시각·크기·inode)
// 을 적어 두는데, git 은 그것으로 "안 바뀐 파일" 을 해시 없이 가려낸다.
// mygit 은 칸을 채워 두기만 하고 자신은 믿지 않는다(§7.2) — 늘
// 해시한다.
//
// 판 2 로 쓰고, 판 2·3 을 읽는다. 확장(TREE·REUC…)은 읽을 때 건너뛰고
// 쓰지 않는다. 수는 전부 빅 엔디언. 경로는 바이트 문자열(tree.ts).
import * as fs from 'node:fs';
import * as path from 'node:path';
import { GitError } from './errors';
import { sha1 } from './sha1';

const ENTRY = 62; // stat 10칸(4바이트씩) · 이름 20 · flags 2
const MAX_NAME = 0xfff;
const GIGA = 1_000_000_000n;

// 인덱스 항목 하나. 경로는 바이트 문자열, 이름은 16진 40글자.
export class IndexEntry {
  ctimeS = 0;
  ctimeNs = 0;
  mtimeS = 0;
  mtimeNs = 0;
  dev = 0;
  ino = 0;
  uid = 0;
  gid = 0;
  assumeValid = false;
  skipWorktree = false;

  constructor(public path: string, public oid: string,
    public mode: number, public stage = 0, public size = 0) {}
}

// 32비트로 자른 bigint stat 칸
const u32 = (n: bigint) => Number(n & 0xffffffffn);

// 작업 트리 파일의 stat 으로 항목을 채운다(SPEC.md §7.2).
//
// 모드는 소유자 실행 비트만 본다 — git 과 같다(그룹·기타는 버린다).
// dev·ino·size 는 32비트로 자른다. 나노초까지 얻으려고 bigint 로 stat
// 한다 — ctimeMs 같은 실수 칸은 나노초 자리를 잃는다.
export function entryFromStat(p: string, full: Buffer | string,
  oid: string): IndexEntry {
  const st = fs.statSync(full, { bigint: true });
  const mode = st.mode & 0o100n ? 0o100755 : 0o100644;
  const e = new IndexEntry(p, oid, mode, 0, u32(st.size));
  [e.ctimeS, e.ctimeNs] = [Number(st.ctimeNs / GIGA),
    Number(st.ctimeNs % GIGA)];
  [e.mtimeS, e.mtimeNs] = [Number(st.mtimeNs / GIGA),
    Number(st.mtimeNs % GIGA)];
  [e.dev, e.ino, e.uid, e.gid] = [st.dev, st.ino, st.uid, st.gid]
    .map(u32);
  return e;
}

// 인덱스 바이트 → IndexEntry 들. 끝 SHA-1 이 틀리면 오류.
//
// 판 3 은 flags 의 비트 14 가 서 있는 항목 뒤에 2바이트 확장 flags 가
// 더 있다(skip-worktree 가 거기 산다). O(파일 크기).
export function parseIndex(data: Buffer): IndexEntry[] {
  const corrupt = new GitError('fatal: mygit: index file corrupt');
  if (data.length < 32 || data.toString('latin1', 0, 4) !== 'DIRC') {
    throw corrupt;
  }
  if (!sha1(data.subarray(0, -20)).equals(data.subarray(-20))) {
    throw corrupt;
  }
  const ver = data.readUInt32BE(4);
  if (ver === 4) {
    throw new GitError('fatal: mygit: index v4 unsupported');
  }
  if (ver !== 2 && ver !== 3) {
    throw new GitError(`fatal: mygit: index version ${ver}`);
  }
  const out: IndexEntry[] = [];
  let pos = 12;
  for (let k = data.readUInt32BE(8); k > 0; k--) {
    const f = (i: number) => data.readUInt32BE(pos + 4 * i);
    const flags = data.readUInt16BE(pos + 60);
    const oid = data.toString('hex', pos + 40, pos + 60);
    const e = new IndexEntry('', oid, f(6), (flags >> 12) & 3, f(9));
    [e.ctimeS, e.ctimeNs, e.mtimeS, e.mtimeNs, e.dev, e.ino] =
      [0, 1, 2, 3, 4, 5].map(f);
    [e.uid, e.gid] = [f(7), f(8)];
    e.assumeValid = Boolean(flags & 0x8000);
    let start = pos + ENTRY;
    if (flags & 0x4000) {                     // 판 3 의 확장 flags
      e.skipWorktree = Boolean(data.readUInt16BE(start) & 0x4000);
      start += 2;
    }
    const end = data.indexOf(0, start);       // 이름 길이 0xfff 넘어도
    e.path = data.toString('latin1', start, end);
    pos += Math.floor((start - pos + e.path.length + 8) / 8) * 8;
    out.push(e);
  }
  return out;
}

// IndexEntry 들 → 판 2 인덱스 바이트. 경로·단계 차례로 정렬한다.
//
// 항목 길이 = (62 + 이름 길이 + 8) & ~7 — 이름 뒤 NUL 이 1‥8 개.
// 판 2 에는 확장 flags 가 없으므로 skip-worktree 는 여기서 사라진다
// (mygit 은 그 비트를 쓰지 않는다 — 읽기만 한다).
export function serializeIndex(entries: IndexEntry[]): Buffer {
  const ents = [...entries].sort((a, b) =>
    a.path < b.path ? -1 : a.path > b.path ? 1 : a.stage - b.stage);
  const head = Buffer.alloc(12);
  head.write('DIRC', 'latin1');
  head.writeUInt32BE(2, 4);
  head.writeUInt32BE(ents.length, 8);
  const parts = [head];
  for (const e of ents) {
    const name = Buffer.from(e.path, 'latin1');
    const rec = Buffer.alloc((ENTRY + name.length + 8) & ~7);
    [e.ctimeS, e.ctimeNs, e.mtimeS, e.mtimeNs, e.dev, e.ino, e.mode,
      e.uid, e.gid, e.size]
      .forEach((v, i) => rec.writeUInt32BE(v, 4 * i));
    rec.write(e.oid, 40, 'hex');
    const flags = (e.stage << 12) | Math.min(name.length, MAX_NAME) |
      (e.assumeValid ? 0x8000 : 0);
    rec.writeUInt16BE(flags, 60);
    name.copy(rec, ENTRY);                    // 남은 자리는 이미 NUL
    parts.push(rec);
  }
  const body = Buffer.concat(parts);
  return Buffer.concat([body, sha1(body)]);
}

// .git/index 를 읽는다. 없으면(첫 add 전) 빈 목록.
export function readIndex(gitdir: string): IndexEntry[] {
  const p = path.join(gitdir, 'index');
  return fs.existsSync(p) ? parseIndex(fs.readFileSync(p)) : [];
}

// index.lock 에 쓰고 이름을 바꿔 넣는다(SPEC.md §7.4).
export function writeIndex(gitdir: string, entries: IndexEntry[]):
  void {
  const p = path.join(gitdir, 'index');
  try {
    fs.writeFileSync(p + '.lock', serializeIndex(entries),
      { flag: 'wx' });
  } catch (e) {
    if ((e as NodeJS.ErrnoException).code !== 'EEXIST') throw e;
    throw new GitError(`fatal: mygit: unable to lock ${p}`);
  }
  fs.renameSync(p + '.lock', p);
}

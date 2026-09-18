// 객체 (SPEC.md §4.1 · §4.6) — 이름은 내용의 SHA-1 이다.
//
// 이름 = SHA-1("<형식> <크기>\0" + 몸). 같은 내용은 어느 저장소에서
// 누가 만들어도 같은 이름을 얻는다 — git 이 "내용 주소 저장소" 인
// 까닭이 이 한 줄이다. 느슨한 객체는 그 바이트를 zlib 으로 눌러
// .git/objects/<앞 2글자>/<나머지 38글자> 에 둔다.
import { randomBytes } from 'node:crypto';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { GitError } from './errors';
import { Sha1 } from './sha1';
import * as zlib from './zlib';

export const TYPES = ['blob', 'tree', 'commit', 'tag'];

function header(type: string, body: Uint8Array): Buffer {
  return Buffer.from(`${type} ${body.length}\0`);
}

// 객체 이름(16진 40글자). 저장소를 건드리지 않는다. 머리와 몸을
// 이어 붙이지 않고 차례로 흘려 넣는다 — 큰 blob 을 복사하지 않는다.
export function hashObject(type: string, body: Uint8Array): string {
  return new Sha1().update(header(type, body)).update(body).digest()
    .toString('hex');
}

export function objectPath(gitdir: string, oid: string): string {
  return path.join(gitdir, 'objects', oid.slice(0, 2), oid.slice(2));
}

// 느슨한 객체 하나를 쓰고 이름을 돌려준다.
//
// 이미 있으면 아무것도 하지 않는다 — 이름이 같으면 내용도 같기
// 때문이다(0444 라 덮어쓰려 하면 실패하기도 한다). 임시 파일에 다 쓴
// 뒤 이름을 바꿔 넣어, 도중에 죽어도 반쯤 쓴 객체가 남지 않는다.
export function writeObject(gitdir: string, type: string,
  body: Uint8Array): string {
  const oid = hashObject(type, body);
  const file = objectPath(gitdir, oid);
  if (fs.existsSync(file)) return oid;
  const dir = path.dirname(file);
  fs.mkdirSync(dir, { recursive: true });
  const tmp = path.join(dir,
    `tmp_obj_${randomBytes(6).toString('hex')}`);
  try {
    const raw = Buffer.concat([header(type, body), body]);
    fs.writeFileSync(tmp, zlib.compress(raw),
      { flag: 'wx', mode: 0o444 });
    fs.renameSync(tmp, file);
  } catch (e) {
    fs.rmSync(tmp, { force: true });
    throw e;
  }
  return oid;
}

// 풀린 바이트 → [형식, 몸]. 머리의 크기가 몸과 다르면 오류.
function parseRaw(raw: Buffer, oid: string): [string, Buffer] {
  const nul = raw.indexOf(0);
  const parts = raw.subarray(0, Math.max(nul, 0)).toString('latin1')
    .split(' ');
  if (nul < 0 || parts.length !== 2 || !/^\d+$/.test(parts[1])) {
    throw new GitError(`fatal: mygit: bad object header in ${oid}`);
  }
  const body = raw.subarray(nul + 1);
  if (!TYPES.includes(parts[0]) || Number(parts[1]) !== body.length) {
    throw new GitError(`fatal: mygit: object ${oid} is corrupt`);
  }
  return [parts[0], body];
}

// [형식, 몸] — 느슨한 객체를 먼저 본다. 없으면 GitError.
export function readObject(gitdir: string, oid: string):
  [string, Buffer] {
  const file = objectPath(gitdir, oid);
  if (fs.existsSync(file)) {
    return parseRaw(zlib.decompress(fs.readFileSync(file)), oid);
  }
  throw new GitError(`fatal: mygit: object ${oid} not found`);
}

// 느슨한 객체의 이름 전부. objects/xx/ 디렉터리를 훑는다.
export function allLoose(gitdir: string): string[] {
  const root = path.join(gitdir, 'objects');
  const out: string[] = [];
  for (const d of fs.readdirSync(root).sort()) {
    if (d.length !== 2) continue;
    for (const f of fs.readdirSync(path.join(root, d)).sort()) {
      if (f.length === 38) out.push(d + f);
    }
  }
  return out;
}

// 앞부분(4글자 이상)으로 찾는다: 하나면 그 이름, 없으면 null.
//
// 둘 이상이면 git 처럼 모호하다고 멈춘다. 4글자보다 짧으면 찾지
// 않는다(git 의 최소 줄임 길이와 같다). O(느슨한 객체 수).
export function findObject(gitdir: string, prefix: string):
  string | null {
  const p = prefix.toLowerCase();
  if (p.length < 4 || !/^[0-9a-f]+$/.test(p)) return null;
  const ids = allLoose(gitdir);
  if (p.length === 40) return ids.includes(p) ? p : null;
  const hits = ids.filter((o) => o.startsWith(p));
  if (hits.length > 1) {
    throw new GitError(`error: short object ID ${prefix} is ambiguous`);
  }
  return hits[0] ?? null;
}

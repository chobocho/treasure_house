// zlib 겉옷과 느슨한 객체의 시험 — SPEC.md §3 · §4.1 · §4.6, 2단계.
//
// golden/objects/ 는 진짜 git 이 쓴 파일 그대로이고(고정·동적 허프만
// 블록이 섞여 있다), golden/stored/ 는 C++ 이 쓸 저장 블록 꼴인데 진짜
// git 이 읽고 fsck --strict 를 통과한 것이다(golden/stored_ok.txt).
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as objects from '../src/objects';
import * as zlib from '../src/zlib';
import * as golden from './golden';

const OBJS = golden.tsv('objects', 'objects.tsv');
const HELLO = 'ce013625030ba8dba906f756967f9e9ca394464a';

// 풀린 객체 바이트 → [형식, 크기, 몸].
function split(raw: Buffer): [string, number, Buffer] {
  const nul = raw.indexOf(0);
  const [t, n] = raw.subarray(0, nul).toString().split(' ');
  return [t, Number(n), raw.subarray(nul + 1)];
}

describe('zlib', () => {
  test('s3_2 inflates every git written object', () => {
    const btypes = new Set<string>();
    for (const row of OBJS) {
      const raw = zlib.decompress(golden.read('objects', row.id));
      const [t, n, body] = split(raw);
      assert.deepEqual([t, n], [row.type, Number(row.size)]);
      assert.equal(body.length, n);
      btypes.add(row.btype);
    }
    // 고정(1)과 동적(2) 허프만이 둘 다 있어야 이 시험이 뜻이 있다
    assert.deepEqual([...btypes].sort(), ['1', '2']);
  });

  test('s3_2 inflates stored blocks', () => {
    for (const name of fs.readdirSync(golden.gpath('stored'))) {
      const raw = zlib.decompress(golden.read('stored', name));
      const [, n, body] = split(raw);
      assert.equal(body.length, n, name);
    }
  });

  test('s3_1 round trip', () => {
    for (const data of [Buffer.alloc(0), Buffer.from('x'),
      golden.make('counter:70000')]) {
      assert.deepEqual(zlib.decompress(zlib.compress(data)), data);
    }
  });

  test('s3_2 prefix reports consumed bytes', () => {
    // 팩 안에서는 스트림이 끝나는 곳을 알아야 다음 항목을 읽는다
    const a = zlib.compress(Buffer.from('first stream'));
    const b = zlib.compress(Buffer.from('second'));
    const data = Buffer.concat([Buffer.from('JUNK'), a, b]);
    let [out, used] = zlib.decompressPrefix(data, 4);
    assert.deepEqual([out.toString(), used],
      ['first stream', a.length]);
    [out, used] = zlib.decompressPrefix(data, 4 + used);
    assert.deepEqual([out.toString(), used], ['second', b.length]);
  });

  test('s3_2 bad adler is an error', () => {
    const raw = Buffer.from(golden.read('objects', HELLO));
    raw[raw.length - 1] ^= 0xff;
    golden.assertGitError(() => zlib.decompress(raw));
  });

  test('s3 adler32', () => {
    assert.equal(zlib.adler32(Buffer.from('Wikipedia')), 0x11e60398);
    assert.equal(zlib.adler32(Buffer.alloc(0)), 1);
  });
});

describe('hash', () => {
  test('s4_1 known names', () => {
    assert.equal(objects.hashObject('blob', Buffer.from('hello\n')),
      HELLO);
    assert.equal(objects.hashObject('blob', Buffer.alloc(0)),
      'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391');
    assert.equal(objects.hashObject('tree', Buffer.alloc(0)),
      '4b825dc642cb6eb9a060e54bf8d69288fbee4904');
  });

  test('s4_1 every golden object hashes to its name', () => {
    for (const row of OBJS) {
      const raw = zlib.decompress(golden.read('objects', row.id));
      const [t, , body] = split(raw);
      assert.equal(objects.hashObject(t, body), row.id);
    }
  });
});

// 이 파일 시스템이 0444 를 지키는가.
//
// 이 덱을 만든 기계(안드로이드 위 proot)의 저장소 디렉터리는 쓰기
// 비트를 지우지 못한다 — 진짜 git 이 쓴 객체도 여기서는 0644 로
// 보인다(2026-09-18 확인). 권한을 못 지키는 곳에서 0444 를 단언하면
// 구현이 아니라 기계를 시험하게 된다.
function honoursReadonly(where: string): boolean {
  const probe = path.join(where, 'probe');
  fs.writeFileSync(probe, '');
  fs.chmodSync(probe, 0o444);
  fs.renameSync(probe, probe + '2');
  const ok = (fs.statSync(probe + '2').mode & 0o777) === 0o444;
  fs.rmSync(probe + '2');
  return ok;
}

describe('repo', () => {
  let tmp = '';
  let gitdir = '';
  beforeEach(() => {
    tmp = golden.tempdir();
    gitdir = path.join(tmp, '.git');
    fs.mkdirSync(path.join(gitdir, 'objects', 'pack'),
      { recursive: true });
  });
  afterEach(() => golden.rmTree(tmp));

  function plant(oid: string): void {
    const d = path.join(gitdir, 'objects', oid.slice(0, 2));
    fs.mkdirSync(d, { recursive: true });
    fs.writeFileSync(path.join(d, oid.slice(2)),
      golden.read('objects', oid));
  }

  test('s4_6 path and content', () => {
    const oid = objects.writeObject(gitdir, 'blob',
      Buffer.from('hello\n'));
    assert.equal(oid, HELLO);
    const p = path.join(gitdir, 'objects', 'ce', HELLO.slice(2));
    const raw = zlib.decompress(fs.readFileSync(p));
    assert.equal(raw.toString(), 'blob 6\0hello\n');
  });

  test('s4_6 readonly', (t) => {
    if (!honoursReadonly(tmp)) {
      t.skip('이 파일 시스템은 0444 를 지키지 않는다');
      return;
    }
    objects.writeObject(gitdir, 'blob', Buffer.from('hello\n'));
    const p = path.join(gitdir, 'objects', 'ce', HELLO.slice(2));
    assert.equal(fs.statSync(p).mode & 0o777, 0o444);
  });

  test('s4_6 second write is a no op', () => {
    objects.writeObject(gitdir, 'blob', Buffer.from('hello\n'));
    // 파일이 0444 여도 두 번째 쓰기가 실패하면 안 된다
    objects.writeObject(gitdir, 'blob', Buffer.from('hello\n'));
    const d = path.join(gitdir, 'objects', 'ce');
    assert.deepEqual(fs.readdirSync(d), [HELLO.slice(2)]);
  });

  test('s4_6 no temp files left', () => {
    objects.writeObject(gitdir, 'blob', Buffer.alloc(1000, 'x'));
    const d = path.join(gitdir, 'objects');
    for (const sub of fs.readdirSync(d)) {
      for (const f of fs.readdirSync(path.join(d, sub))) {
        assert.equal((sub + f).length, 40, f);
      }
    }
  });

  test('s4_6 reads what git wrote', () => {
    for (const row of OBJS) {
      plant(row.id);
      const [t, body] = objects.readObject(gitdir, row.id);
      assert.deepEqual([t, body.length], [row.type, Number(row.size)]);
    }
  });

  test('s4_6 reads what it wrote', () => {
    const oid = objects.writeObject(gitdir, 'commit',
      Buffer.from('x\n'));
    const [t, body] = objects.readObject(gitdir, oid);
    assert.deepEqual([t, body.toString()], ['commit', 'x\n']);
  });

  test('s4_6 missing object', () => {
    golden.assertGitError(() => objects.readObject(gitdir, HELLO));
  });

  test('s4_6 size mismatch is an error', () => {
    const d = path.join(gitdir, 'objects', 'ce');
    fs.mkdirSync(d);
    fs.writeFileSync(path.join(d, HELLO.slice(2)),
      zlib.compress(Buffer.from('blob 7\0hello\n')));
    golden.assertGitError(() => objects.readObject(gitdir, HELLO));
  });

  test('s4_6 prefix', () => {
    for (const row of OBJS) plant(row.id);
    for (const { id } of OBJS) {
      assert.equal(objects.findObject(gitdir, id.slice(0, 7)), id);
      assert.equal(objects.findObject(gitdir, id), id);
    }
    assert.equal(objects.findObject(gitdir, 'ffffff'), null);
  });

  test('s4_6 ambiguous prefix', () => {
    // 앞 네 글자가 같아질 때까지 blob 을 만들어 본다 — 65,536 칸에
    // 생일 문제라 수백 번이면 짝이 나온다
    const seen = new Map<string, Buffer>();
    let oid = '';
    for (let k = 0; ; k++) {
      const body = Buffer.from(`${k}\n`);
      oid = objects.hashObject('blob', body);
      const twin = seen.get(oid.slice(0, 4));
      if (twin) {
        objects.writeObject(gitdir, 'blob', twin);
        objects.writeObject(gitdir, 'blob', body);
        break;
      }
      seen.set(oid.slice(0, 4), body);
    }
    golden.assertGitError(
      () => objects.findObject(gitdir, oid.slice(0, 4)));
  });

  test('s4_6 short prefix is refused', () => {
    plant(HELLO);
    assert.equal(objects.findObject(gitdir, 'ce0'), null);
  });
});

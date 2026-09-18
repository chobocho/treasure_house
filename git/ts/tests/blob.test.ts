// blob — hash-object · cat-file 의 시험. SPEC.md §1 · §9, 3단계.
//
// 오라클은 golden/objects/ 의 blob 들(진짜 git 이 쓴 파일)과
// golden/errors.tsv 의 오류 문장이다. 명령은 cli.run 으로 과정 안에서
// 부른다 — 새 node 를 띄우지 않아 빠르고, 출력 바이트를 그대로 본다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as cli from '../src/cli';
import * as zlib from '../src/zlib';
import * as golden from './golden';

const OBJS = golden.tsv('objects', 'objects.tsv');
const ERRORS = new Map(golden.tsv('errors.tsv')
  .map((r) => [r.command, r]));

function bodyOf(oid: string): Buffer {
  const raw = zlib.decompress(golden.read('objects', oid));
  return raw.subarray(raw.indexOf(0) + 1);
}

// 표준 오류의 첫 줄과 코드 — errors.tsv 의 한 행과 견준다.
function firstLine([code, , err]: cli.Result): [number, string] {
  return [code, err.toString().split('\n')[0]];
}

function want(command: string): [number, string] {
  const row = ERRORS.get(command)!;
  return [Number(row.exit), row['stderr-first-line']];
}

// 임시 디렉터리. withRepo 면 .git 뼈대를 손으로 만든다(init 은
// 5단계의 일이라 여기서는 쓰지 않는다).
function sandbox(withRepo: boolean) {
  const box = { tmp: '', root: '', env: {} as Record<string, string> };
  beforeEach(() => {
    box.tmp = golden.tempdir();
    box.root = path.join(box.tmp, 'w');
    fs.mkdirSync(box.root);
    if (withRepo) {
      const g = path.join(box.root, '.git');
      for (const d of ['objects/pack', 'refs/heads', 'refs/tags']) {
        fs.mkdirSync(path.join(g, d), { recursive: true });
      }
      fs.writeFileSync(path.join(g, 'HEAD'), 'ref: refs/heads/main\n');
    }
    // 위로 올라가다 이 덱의 저장소를 찾지 않게 (SPEC.md §1.1)
    box.env = { ...process.env as Record<string, string>,
      GIT_CEILING_DIRECTORIES: box.tmp };
  });
  afterEach(() => golden.rmTree(box.tmp));
  return {
    box,
    mygit: (args: string[], stdin = Buffer.alloc(0)) =>
      cli.run(args, box.root, box.env, stdin),
    put: (name: string, data: Uint8Array) =>
      fs.writeFileSync(path.join(box.root, name), data),
  };
}

describe('hash-object', () => {
  const { mygit, put } = sandbox(true);

  test('s9 every golden blob has its git name', async () => {
    let n = 0;
    for (const row of OBJS) {
      if (row.type !== 'blob') continue;
      put('f', bodyOf(row.id));
      const [code, out, err] = await mygit(['hash-object', 'f']);
      assert.deepEqual([code, out.toString(), err.toString()],
        [0, row.id + '\n', '']);
      n++;
    }
    assert.ok(n >= 3);
  });

  test('s9 stdin', async () => {
    const [, out] = await mygit(['hash-object', '--stdin'],
      Buffer.from('hello\n'));
    assert.equal(out.toString(),
      'ce013625030ba8dba906f756967f9e9ca394464a\n');
  });

  test('s9 type option', async () => {
    const [, out] = await mygit(['hash-object', '-t', 'tree',
      '--stdin']);
    assert.equal(out.toString(),
      '4b825dc642cb6eb9a060e54bf8d69288fbee4904\n');
  });

  test('s9 write then read back', async () => {
    const data = golden.make('counter:5000');
    put('f', data);
    const [, out] = await mygit(['hash-object', '-w', 'f']);
    const oid = out.toString().trim();
    const show = async (...a: string[]) => {
      const [code, o, e] = await mygit(['cat-file', ...a]);
      return [code, o, e.toString()];
    };
    assert.deepEqual(await show('-t', oid), [0, Buffer.from('blob\n'),
      '']);
    assert.deepEqual(await show('-s', oid), [0, Buffer.from('5000\n'),
      '']);
    assert.deepEqual(await show('-p', oid), [0, data, '']);
    // 앞부분 7글자로도 찾는다
    assert.deepEqual((await show('-p', oid.slice(0, 7)))[1], data);
  });

  test('s1_4 missing file', async () => {
    assert.deepEqual(firstLine(await mygit(['hash-object', 'nope'])),
      want('hash-object nope'));
  });
});

describe('cat-file', () => {
  const { box, mygit } = sandbox(true);

  function plant(oid: string): void {
    const d = path.join(box.root, '.git', 'objects', oid.slice(0, 2));
    fs.mkdirSync(d, { recursive: true });
    fs.writeFileSync(path.join(d, oid.slice(2)),
      golden.read('objects', oid));
  }

  test('s9 commit and tag print their bodies', async () => {
    for (const row of OBJS) {
      if (!['commit', 'tag', 'blob'].includes(row.type)) continue;
      plant(row.id);
      const [code, out] = await mygit(['cat-file', '-p', row.id]);
      assert.deepEqual([code, out], [0, bodyOf(row.id)]);
      const [, t] = await mygit(['cat-file', '-t', row.id]);
      assert.equal(t.toString(), row.type + '\n');
    }
  });

  test('s1_4 not a valid object name', async () => {
    assert.deepEqual(firstLine(await mygit(['cat-file', '-p', 'nope'])),
      want('cat-file -p nope'));
  });
});

describe('outside repo', () => {
  const { mygit, put } = sandbox(false);

  test('s1_4 not a repository', async () => {
    assert.deepEqual(firstLine(await mygit(['cat-file', '-t', 'abcd'])),
      want('status'));
  });

  test('s1_1 hash-object needs no repo', async () => {
    put('f', Buffer.from('hello\n'));
    assert.equal((await mygit(['hash-object', 'f']))[0], 0);
  });

  test('s1_4 unknown command', async () => {
    const [code, , err] = await mygit(['frobnicate']);
    assert.equal(code, 1);
    assert.equal(err.toString(),
      "mygit: 'frobnicate' is not a mygit command.\n");
  });
});

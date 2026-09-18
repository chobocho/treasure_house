// tree 의 시험 — SPEC.md §4.3 · §8.2, 4단계 "정렬 규칙이 전부다".
//
// 오라클은 golden/trees/ — 경우마다 진짜 git 이 인덱스에 올린
// (모드·blob·경로) 목록(<경우>.tsv)과 write-tree 의 이름(trees.tsv),
// 그리고 ls-tree -r -t 의 출력(<경우>.ls)이다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as cli from '../src/cli';
import * as objects from '../src/objects';
import * as tree from '../src/tree';
import { quotePath } from '../src/worktree';
import * as zlib from '../src/zlib';
import * as golden from './golden';

const CASES = golden.tsv('trees', 'trees.tsv');
const OBJS = golden.tsv('objects', 'objects.tsv');

// <경우>.tsv → [모드, blob 이름, 경로]. 경로는 바이트 문자열(latin1).
function entriesOf(name: string): tree.PathEntry[] {
  const out: tree.PathEntry[] = [];
  const text = golden.read('trees', name + '.tsv').toString('latin1');
  for (const line of text.split('\n')) {
    if (!line || line.startsWith('#')) continue;
    const [mode, oid, ...p] = line.split('\t');
    out.push([mode, oid, p.join('\t')]);
  }
  return out;
}

// ls-tree 가 따옴표로 감싼 경로를 바이트 문자열로 되돌린다(시험 전용).
function unquote(p: string): string {
  const raw = p.startsWith('"') ? golden.unescapeC(p.slice(1, -1))
    : Buffer.from(p);
  return raw.toString('latin1');
}

function gitRepo() {
  const box = { tmp: '', gitdir: '' };
  beforeEach(() => {
    box.tmp = golden.tempdir();
    box.gitdir = path.join(box.tmp, '.git');
    fs.mkdirSync(path.join(box.gitdir, 'objects', 'pack'),
      { recursive: true });
  });
  afterEach(() => golden.rmTree(box.tmp));
  return box;
}

describe('write-tree', () => {
  const box = gitRepo();

  test('s4_3 twelve trees have git names', () => {
    assert.equal(CASES.length, 12);
    for (const row of CASES) {
      const got = tree.writeTree(box.gitdir, entriesOf(row.case));
      assert.equal(got, row.tree, row.case);
    }
  });

  test('s4_3 every subtree git listed was written', () => {
    for (const row of CASES) {
      tree.writeTree(box.gitdir, entriesOf(row.case));
      const ls = golden.read('trees', row.case + '.ls').toString();
      for (const line of ls.split('\n')) {
        if (!line) continue;
        const meta = line.split('\t')[0].split(' ');
        if (meta[1] === 'tree') {
          const [t] = objects.readObject(box.gitdir, meta[2]);
          assert.equal(t, 'tree', line);
        }
      }
    }
  });

  test('s4_3 flatten gives back the input', () => {
    for (const row of CASES) {
      const ents = entriesOf(row.case);
      const oid = tree.writeTree(box.gitdir, ents);
      assert.deepEqual(tree.flattenTree(box.gitdir, oid), ents,
        row.case);
    }
  });
});

describe('sort rule', () => {
  test('s4_3 directory sorts as if it ended in slash', () => {
    const z = '0'.repeat(40);
    const ents: tree.TreeEntry[] = [['100644', 'ab', z],
      ['40000', 'a', z], ['100644', 'a=b', z], ['100644', 'a.b', z],
      ['100644', 'a-b', z]];
    const body = tree.serializeTree(ents);
    const names = tree.parseTree(body).map(([, n]) => n);
    assert.deepEqual(names, ['a-b', 'a.b', 'a', 'a=b', 'ab']);
  });

  test('s4_3 plain name sort would be wrong', () => {
    // 이름만으로 정렬하면 a 가 맨 앞 — 규칙이 왜 있는지 보여 준다
    assert.ok(tree.treeEntryKey('100644', 'a-b') <
      tree.treeEntryKey('40000', 'a'));
    assert.ok(tree.treeEntryKey('100644', 'a') <
      tree.treeEntryKey('100644', 'a-b'));
  });

  test('s4_3 mode is not zero padded in the body', () => {
    const body = tree.serializeTree([['40000', 'd', '1'.repeat(40)]]);
    assert.ok(body.toString('latin1').startsWith('40000 d\0'));
  });
});

describe('parse', () => {
  test('s4_3 round trip on git trees', () => {
    let n = 0;
    for (const row of OBJS) {
      if (row.type !== 'tree') continue;
      const raw = zlib.decompress(golden.read('objects', row.id));
      const body = raw.subarray(raw.indexOf(0) + 1);
      assert.deepEqual(tree.serializeTree(tree.parseTree(body)), body);
      n++;
    }
    assert.ok(n >= 2);
  });
});

describe('quote', () => {
  test('s8_2 quoting', () => {
    const q = (s: string, space = false) =>
      quotePath(Buffer.from(s).toString('latin1'), space);
    assert.equal(q('plain.txt'), 'plain.txt');
    assert.equal(q('sp ace'), 'sp ace');
    assert.equal(q('sp ace', true), '"sp ace"');
    assert.equal(q('tab\tx'), '"tab\\tx"');
    assert.equal(q('q"uote'), '"q\\"uote"');
    assert.equal(q('back\\slash'), '"back\\\\slash"');
    assert.equal(q('한글.txt'), '"\\355\\225\\234\\352\\270\\200.txt"');
    assert.equal(q('del\x7f'), '"del\\177"');
  });
});

describe('cat-file tree', () => {
  const box = gitRepo();

  test('s9 cat-file -p tree matches ls-tree top level', async () => {
    const root = path.dirname(box.gitdir);
    const env = { ...process.env, GIT_CEILING_DIRECTORIES: box.tmp };
    for (const row of CASES) {
      tree.writeTree(box.gitdir, entriesOf(row.case));
      const ls = golden.read('trees', row.case + '.ls').toString();
      const want = ls.split('\n')
        .filter((l) => l && !unquote(l.split('\t')[1]).includes('/'))
        .map((l) => l + '\n').join('');
      const [code, out] = await cli.run(['cat-file', '-p', row.tree],
        root, env);
      assert.deepEqual([code, out.toString()], [0, want], row.case);
    }
  });
});

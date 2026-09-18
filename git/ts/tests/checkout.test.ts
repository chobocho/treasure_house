// 작업 트리 바꾸기의 시험 — SPEC.md §9.3, 9단계 "checkout · switch".
//
// 큰 오라클은 golden/scen/checkout.scn(진짜 git 의 switch·checkout
// 출력과 reflog)이다. 여기서는 장면이 직접 보지 않는 두 가지 — 파일이
// 없어져 비게 된 디렉터리가 지워지는가, 실행 비트가 작업 트리에
// 살아나는가 — 를 본다. git 도 둘 다 그렇게 한다(SPEC.md §9.3 끝 문단).
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as cli from '../src/cli';
import * as golden from './golden';

const ENV = {
  GIT_AUTHOR_NAME: 'A', GIT_AUTHOR_EMAIL: 'a@x',
  GIT_AUTHOR_DATE: '1700000000 +0900',
  GIT_COMMITTER_NAME: 'C', GIT_COMMITTER_EMAIL: 'c@x',
  GIT_COMMITTER_DATE: '1700000000 +0900',
};

describe('two way', () => {
  let tmp = '';
  let root = '';
  const ok = async (...args: string[]): Promise<Buffer> => {
    const [code, out, err] = await cli.run(args, root,
      { ...process.env, ...ENV, GIT_CEILING_DIRECTORIES: tmp });
    assert.equal(code, 0, `${args.join(' ')}: ${out}${err}`);
    return out;
  };
  const put = (rel: string, data: string, mode = 0o644) => {
    const p = path.join(root, rel);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, data);
    fs.chmodSync(p, mode);
  };
  beforeEach(async () => {
    tmp = golden.tempdir();
    root = path.join(tmp, 'w');
    fs.mkdirSync(root);
    await ok('init');
  });
  afterEach(() => golden.rmTree(tmp));

  test('s9_3 emptied directories are removed', async () => {
    put('keep', 'k\n');
    await ok('add', '.');
    await ok('commit', '-m', 'base');
    await ok('switch', '-c', 'deep');
    put('a/b/c.txt', 'c\n');
    await ok('add', '.');
    await ok('commit', '-m', 'deep');
    await ok('switch', 'main');
    assert.ok(!fs.existsSync(path.join(root, 'a')));
    await ok('switch', 'deep');
    assert.equal(fs.readFileSync(path.join(root, 'a', 'b', 'c.txt'),
      'utf8'), 'c\n');
  });

  test('s9_3 exec bit is written', async () => {
    put('run', '#!/bin/sh\n', 0o755);
    await ok('add', '.');
    await ok('commit', '-m', 'x');
    await ok('switch', '-c', 'side');
    fs.rmSync(path.join(root, 'run'));
    await ok('add', '.');
    await ok('commit', '-m', 'gone');
    await ok('switch', 'main');
    assert.ok(fs.statSync(path.join(root, 'run')).mode & 0o100);
  });

  test('s9_3 status is clean after switch', async () => {
    put('f', '1\n');
    await ok('add', '.');
    await ok('commit', '-m', 'one');
    await ok('switch', '-c', 'b2');
    put('f', '2\n');
    put('g/h', 'h\n');
    await ok('add', '.');
    await ok('commit', '-m', 'two');
    for (const name of ['main', 'b2', 'main']) {
      await ok('switch', name);
      assert.equal((await ok('status')).toString(), '');
    }
  });
});

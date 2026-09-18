// 인덱스의 시험 — SPEC.md §7, 6단계 "인덱스 — 스테이징의 실체".
//
// golden/index/ 의 세 파일은 진짜 git 이 쓴 인덱스다: 확장 없음(git add
// 직후), TREE 확장(git commit 뒤), 판 3(skip-worktree 가 켜진 항목).
// plain.bin 은 plain.raw 의 stat 칸을 §7.3 으로 지운 것이다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as index from '../src/index';
import * as golden from './golden';

type Summary = [number, string, number, string];

// golden/index/ls-stage.txt → [모드, 이름, 단계, 경로(바이트 문자열)].
function lsStage(): Summary[] {
  const text = golden.read('index', 'ls-stage.txt').toString();
  return text.split('\n').filter((l) => l).map((line) => {
    const [meta, p] = line.split('\t');
    const [mode, oid, stage] = meta.split(' ');
    const raw = p.startsWith('"') ? golden.unescapeC(p.slice(1, -1))
      : Buffer.from(p);
    return [parseInt(mode, 8), oid, Number(stage),
      raw.toString('latin1')];
  });
}

function summary(entries: index.IndexEntry[]): Summary[] {
  return entries.map((e) => [e.mode, e.oid, e.stage, e.path]);
}

describe('read git', () => {
  test('s7_1 plain', () => {
    const ents = index.parseIndex(golden.read('index', 'plain.raw'));
    assert.deepEqual(summary(ents), lsStage());
  });

  test('s7_5 tree extension is skipped', () => {
    const ents = index.parseIndex(golden.read('index', 'tree-ext.raw'));
    assert.deepEqual(summary(ents), lsStage());
  });

  test('s7_1 version 3', () => {
    const ents = index.parseIndex(golden.read('index', 'v3.raw'));
    assert.deepEqual(summary(ents), lsStage());
    assert.deepEqual(ents.filter((e) => e.skipWorktree)
      .map((e) => e.path), ['run.sh']);
  });

  test('s7_5 bad checksum', () => {
    const raw = Buffer.from(golden.read('index', 'plain.raw'));
    raw[raw.length - 1] ^= 1;
    golden.assertGitError(() => index.parseIndex(raw));
  });
});

describe('write', () => {
  test('s7_2 round trip is byte identical', () => {
    const raw = golden.read('index', 'plain.raw');
    assert.deepEqual(index.serializeIndex(index.parseIndex(raw)), raw);
  });

  test('s7_3 normalized equals golden', () => {
    const ents = index.parseIndex(golden.read('index', 'plain.raw'));
    for (const e of ents) {
      e.ctimeS = e.ctimeNs = e.mtimeS = e.mtimeNs = 0;
      e.dev = e.ino = e.uid = e.gid = 0;
    }
    assert.deepEqual(index.serializeIndex(ents),
      golden.read('index', 'plain.bin'));
  });

  test('s7_2 version 3 is written as version 2', () => {
    const ents = index.parseIndex(golden.read('index', 'v3.raw'));
    const data = index.serializeIndex(ents);
    assert.equal(data.readUInt32BE(4), 2);
  });

  test('s7_2 long path and padding', () => {
    for (const n of [1, 2, 7, 8, 9, 100, 4094, 4095, 4096, 5000]) {
      const e = new index.IndexEntry('d/' + 'x'.repeat(n),
        '1'.repeat(40), 0o100644);
      const data = index.serializeIndex([e]);
      // 항목 길이는 8의 배수, NUL 은 1‥8 개
      const body = data.length - 12 - 20;
      assert.equal(body % 8, 0, String(n));
      const pad = body - 62 - e.path.length;
      assert.ok(pad >= 1 && pad <= 8, String(n));
      assert.equal(index.parseIndex(data)[0].path, e.path, String(n));
    }
  });

  test('s7_1 sorted by path bytes then stage', () => {
    const ents = ([['b', 0], ['a/x', 0], ['a-b', 0], ['c', 3], ['c', 1],
      ['c', 2]] as [string, number][]).map(([p, s]) =>
      new index.IndexEntry(p, '1'.repeat(40), 0o100644, s));
    const back = index.parseIndex(index.serializeIndex(ents));
    assert.deepEqual(back.map((e) => [e.path, e.stage]),
      [['a-b', 0], ['a/x', 0], ['b', 0], ['c', 1], ['c', 2], ['c', 3]]);
  });
});

describe('stat', () => {
  let tmp = '';
  beforeEach(() => {
    tmp = golden.tempdir();
  });
  afterEach(() => golden.rmTree(tmp));

  test('s7_2 exec bit and size', () => {
    const p = path.join(tmp, 'run.sh');
    fs.writeFileSync(p, '#!/bin/sh\n');
    fs.chmodSync(p, 0o755);
    let e = index.entryFromStat('run.sh', p, '2'.repeat(40));
    assert.deepEqual([e.mode, e.size], [0o100755, 10]);
    fs.chmodSync(p, 0o644);
    e = index.entryFromStat('run.sh', p, '2'.repeat(40));
    assert.equal(e.mode, 0o100644);
    const ns = fs.statSync(p, { bigint: true }).mtimeNs;
    assert.deepEqual([e.mtimeS, e.mtimeNs],
      [Number(ns / 1_000_000_000n), Number(ns % 1_000_000_000n)]);
  });

  test('s7_4 write and read back', () => {
    const g = path.join(tmp, '.git');
    fs.mkdirSync(g);
    assert.deepEqual(index.readIndex(g), []);
    index.writeIndex(g, [new index.IndexEntry('a', '3'.repeat(40),
      0o100644)]);
    assert.deepEqual(summary(index.readIndex(g)),
      [[0o100644, '3'.repeat(40), 0, 'a']]);
    assert.ok(!fs.existsSync(path.join(g, 'index.lock')));
  });
});

// diff 의 시험 — SPEC.md §11, 8단계 "diff — Myers 알고리즘".
//
// golden/diff/ 는 진짜 `git -c diff.indentHeuristic=false diff
// --no-index` 의 출력이다. agree 30쌍은 바이트까지 같아야 하고, tie
// 3쌍은 git 이 같은 길이의 **다른** 편집 스크립트를 고르는 쌍이다 —
// 거기서는 지운 줄·끼운 줄의 수가 같고 출력은 달라야 한다(SPEC.md
// §11.2). 세 영역 사이의 diff 는 golden/scen/diff.scn 이 장면 시험으로
// 본다. 선형 공간 변형(결정 7)은 Python 에만 있어 그 시험은 없다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as cli from '../src/cli';
import * as diff from '../src/diff';
import * as golden from './golden';

const AGREE = golden.tsv('diff', 'agree.tsv');
const TIE = golden.tsv('diff', 'tie.tsv');

describe('against git', () => {
  let tmp = '';
  beforeEach(() => {
    tmp = golden.tempdir();
  });
  afterEach(() => golden.rmTree(tmp));

  function runPair(stem: string): Promise<cli.Result> {
    for (const ext of ['a', 'b']) {
      fs.writeFileSync(path.join(tmp, `${stem}.${ext}`),
        golden.read('diff', `${stem}.${ext}`));
    }
    return cli.run(['diff', '--no-index', `${stem}.a`, `${stem}.b`],
      tmp, { ...process.env, GIT_CEILING_DIRECTORIES: tmp });
  }

  test('s11 agree pairs are byte identical', async () => {
    assert.equal(AGREE.length, 30);
    for (const row of AGREE) {
      const [code, out, err] = await runPair(row.name);
      assert.deepEqual([code, out, err.toString()],
        [Number(row.exit), golden.read('diff', row.name + '.diff'), ''],
        row.name);
    }
  });

  test('s11_2 tie pairs same size different choice', async () => {
    assert.equal(TIE.length, 3);
    for (const row of TIE) {
      const [, out] = await runPair(row.name);
      const body = out.toString('latin1').split('\n')
        .filter((l) => !l.startsWith('---') && !l.startsWith('+++'));
      const count = (c: string) =>
        body.filter((l) => l.startsWith(c)).length;
      assert.deepEqual([count('-'), count('+')],
        [Number(row.minus), Number(row.plus)], row.name);
      assert.notDeepEqual(out, golden.read('diff', row.name + '.diff'),
        row.name + ' — 분류가 틀렸다');
    }
  });
});

describe('pieces', () => {
  const lines = (s: string) => diff.splitLines(Buffer.from(s));

  test('s11_1 lines keep their newline', () => {
    assert.deepEqual(lines('a\nb\nc'), ['a\n', 'b\n', 'c']);
    assert.deepEqual(lines(''), []);
    assert.deepEqual(lines('\n'), ['\n']);
  });

  test('s11_2 minimal edit count', () => {
    const [ra, rb] = diff.myers(lines('a\nb\nc\na\nb\nb\na\n'),
      lines('c\nb\na\nb\na\nc\n'));
    // Myers 논문 그림 1 의 예 — 가장 짧은 편집 스크립트는 5
    assert.equal([...ra, ...rb].filter((x) => x).length, 5);
  });

  test('s11_3 hunk header counts', () => {
    let text = diff.unifiedDiff(lines('x\n'), []);
    assert.ok(text.startsWith('@@ -1 +0,0 @@\n'), text);
    text = diff.unifiedDiff([], lines('x\ny\n'));
    assert.ok(text.startsWith('@@ -0,0 +1,2 @@\n'), text);
  });

  test('s11_3 identical inputs have no hunks', () => {
    const a = lines('same\n');
    assert.equal(diff.unifiedDiff(a, a), '');
  });
});

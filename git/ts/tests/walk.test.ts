// 역사 걷기·merge-base·branch -d 의 시험 — SPEC.md §9.1 · §9.2 · §10,
// 7단계 "log · DAG 순회 · merge-base".
//
// golden/dag/<역사>/git 은 진짜 git 이 만든 .git 이고, expect.txt 는 그
// 저장소에서 git 이 찍은 log·merge-base 출력이다. equal 은 모든 커밋의
// 날짜가 같아(§10.1 의 "먼저 온 것이 먼저" 규칙이 차례를 전부 정한다),
// dated 는 날짜가 모두 다르고, criss 는 가장 좋은 공통 조상이 둘이다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, test } from 'node:test';
import * as cli from '../src/cli';
import * as refs from '../src/refs';
import * as walk from '../src/walk';
import * as golden from './golden';

const HISTORIES = ['equal', 'dated', 'criss'];

// expect.txt → [인자들, 기대 stdout, 기대 코드].
function expectations(name: string): [string[], string, number][] {
  const text = golden.read('dag', name, 'expect.txt').toString();
  return text.split('$ git ').slice(1).map((block) => {
    const nl = block.indexOf('\n');
    const rest = block.slice(nl + 1);
    const eq = rest.lastIndexOf('= ');
    return [block.slice(0, nl).split(' '), rest.slice(0, eq),
      Number(rest.slice(eq + 2).trim())];
  });
}

// golden/dag/<name>/git 을 임시 작업 트리의 .git 으로 옮긴다.
function makeDag(name: string) {
  const tmp = golden.tempdir();
  const root = path.join(tmp, 'w');
  const gitdir = path.join(root, '.git');
  fs.cpSync(golden.gpath('dag', name, 'git'), gitdir,
    { recursive: true });
  for (const d of ['objects/pack', 'refs/tags']) {
    fs.mkdirSync(path.join(gitdir, d), { recursive: true });
  }
  const env = { ...process.env, GIT_CEILING_DIRECTORIES: tmp,
    GIT_COMMITTER_NAME: 'C O Mitter',
    GIT_COMMITTER_EMAIL: 'committer@example.com',
    GIT_COMMITTER_DATE: '1700000000 +0900' };
  return {
    tmp, root, gitdir,
    mygit: (...args: string[]) => cli.run(args, root, env),
  };
}

type Dag = ReturnType<typeof makeDag>;

function dag(name = 'equal'): { d: Dag } {
  const box = {} as { d: Dag };
  beforeEach(() => {
    box.d = makeDag(name);
  });
  afterEach(() => golden.rmTree(box.d.tmp));
  return box;
}

describe('against git', () => {
  test('s10 log and merge-base match git', async () => {
    let n = 0;
    for (const name of HISTORIES) {
      const d = makeDag(name);
      try {
        for (const [args, body, code] of expectations(name)) {
          const [c, out] = await d.mygit(...args);
          assert.deepEqual([c, out.toString()], [code, body],
            `${name}: ${args.join(' ')}`);
          n++;
        }
      } finally {
        golden.rmTree(d.tmp);
      }
    }
    assert.ok(n >= 14);
  });
});

describe('walk', () => {
  const box = dag();

  test('s10_1 equal dates first in first out', () => {
    // SPEC.md §10.1 의 예: I M2 G H M1 F D E C B A
    const head = refs.revParse(box.d.gitdir, 'HEAD')!;
    const order = walk.walkLog(box.d.gitdir, [head]);
    assert.equal(order.length, 11);
    assert.equal(order[0], head);
  });

  test('s10_2 is ancestor', () => {
    const g = box.d.gitdir;
    const head = refs.revParse(g, 'HEAD')!;
    const t = refs.revParse(g, 't')!;
    assert.ok(walk.isAncestor(g, t, head));
    assert.ok(!walk.isAncestor(g, head, t));
    assert.ok(walk.isAncestor(g, head, head));
  });
});

describe('branch delete', () => {
  const box = dag();

  test('s9_2 delete merged branch', async () => {
    const t = refs.revParse(box.d.gitdir, 't')!;
    const [code, out, err] = await box.d.mygit('branch', '-d', 't');
    assert.deepEqual([code, out.toString(), err.toString()],
      [0, `Deleted branch t (was ${t.slice(0, 7)}).\n`, '']);
    assert.equal(refs.resolveRef(box.d.gitdir, 'refs/heads/t'), null);
  });

  test('s9_2 refuses unmerged branch', async () => {
    await box.d.mygit('branch', 'old', 'HEAD~1');
    // HEAD 를 뒤로 돌려 old 가 HEAD 에서 닿지 않게 한다
    refs.setHead(box.d.gitdir, refs.revParse(box.d.gitdir, 'HEAD~2')!);
    const [code, , err] = await box.d.mygit('branch', '-d', 'old');
    assert.deepEqual([code, err.toString()],
      [1, "error: the branch 'old' is not fully merged\n"]);
  });

  test('s9_2 refuses current branch', async () => {
    const [code, , err] = await box.d.mygit('branch', '-d', 'main');
    assert.deepEqual([code, err.toString()],
      [1, "error: cannot delete branch 'main' used by worktree at " +
        `'${box.d.root}'\n`]);
  });
});

describe('log errors', () => {
  const box = dag();

  test('s1_4 unknown revision', async () => {
    const [code, , err] = await box.d.mygit('log', 'nope');
    assert.equal(code, 128);
    assert.equal(err.toString().split('\n')[0],
      "fatal: ambiguous argument 'nope': unknown revision or path " +
      'not in the working tree.');
  });

  test('s9_1 limit', async () => {
    const [, out] = await box.d.mygit('log', '--oneline', '-n', '3');
    assert.equal(out.toString().split('\n').length, 4);
  });
});

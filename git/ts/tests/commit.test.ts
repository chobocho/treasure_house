// commit·tag·신원 줄과 참조의 시험 — SPEC.md §4.4 · §4.5 · §6, 5단계.
//
// 가장 강한 오라클은 "같은 입력에서 같은 이름" 이다. golden/objects 의
// 커밋(b23b7a5…)과 태그(5702a43…)는 tools/gitenv.sh 의 고정 환경에서
// 진짜 git 이 만들었다 — mygit 이 같은 트리·같은 환경으로 만든 커밋과
// 태그는 바이트까지 같아야 하고, 그러면 이름도 같다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { after, afterEach, before, beforeEach, describe, test }
  from 'node:test';
import * as cli from '../src/cli';
import * as commit from '../src/commit';
import * as objects from '../src/objects';
import * as refs from '../src/refs';
import * as zlib from '../src/zlib';
import * as golden from './golden';

const OBJS = golden.tsv('objects', 'objects.tsv').map((r) => r.id);
const ERRORS = new Map(golden.tsv('errors.tsv')
  .map((r) => [r.command, r]));
const COMMIT = 'b23b7a5fefc32902eb83feac2800cf158140dcb1';
const TAG = '5702a431dba432bfe47c3b3fdda3835a8f542f5c';
const ENV = {
  GIT_AUTHOR_NAME: 'A U Thor',
  GIT_AUTHOR_EMAIL: 'author@example.com',
  GIT_AUTHOR_DATE: '1700000000 +0900',
  GIT_COMMITTER_NAME: 'C O Mitter',
  GIT_COMMITTER_EMAIL: 'committer@example.com',
  GIT_COMMITTER_DATE: '1700000000 +0900',
};

function bodyOf(oid: string): Buffer {
  const raw = zlib.decompress(golden.read('objects', oid));
  return raw.subarray(raw.indexOf(0) + 1);
}

describe('ident and date', () => {
  test('s4_4 parse ident', () => {
    assert.deepEqual(commit.parseIdent(
      'A U Thor <author@example.com> 1700000000 +0900'),
    ['A U Thor', 'author@example.com', 1700000000, '+0900']);
  });

  test('s9_1 date matches git log', () => {
    // golden/scen/hello.scn: git log 이 찍은 두 날짜
    assert.equal(commit.formatDate(1700000000, '+0900'),
      'Wed Nov 15 07:13:20 2023 +0900');
    assert.equal(commit.formatDate(1700000060, '+0900'),
      'Wed Nov 15 07:14:20 2023 +0900');
  });

  test('s9_1 date other zones agree with Date', () => {
    // 달력 계산은 손으로 한다 — 표준 Date 는 증인으로만. toUTCString
    // 은 "Wed, 15 Nov 2023 07:13:20 GMT" 꼴이라 칸을 옮겨 견준다.
    for (const secs of [0, 86399, 951782400, 1700000000, 2000000000,
      1709251199, 4102444800]) {
      for (const tz of ['+0000', '-0700', '+0530', '-1200', '+1400']) {
        const sign = tz[0] === '-' ? -1 : 1;
        const off = sign * (Number(tz.slice(1, 3)) * 3600 +
          Number(tz.slice(3)) * 60);
        const [wd, d, mon, y, hms] = new Date((secs + off) * 1000)
          .toUTCString().replace(',', '').split(' ');
        const want = `${wd} ${mon} ${Number(d)} ${hms} ${y} ${tz}`;
        assert.equal(commit.formatDate(secs, tz), want);
      }
    }
  });

  test('s1_3 missing env is an error', () => {
    const env: Record<string, string> = { ...ENV };
    delete env.GIT_AUTHOR_DATE;
    let e = golden.assertGitError(
      () => commit.identFromEnv(env, 'AUTHOR'));
    assert.equal(e.message, 'fatal: mygit: GIT_AUTHOR_DATE is not set');
    env.GIT_AUTHOR_DATE = 'yesterday';
    e = golden.assertGitError(() => commit.identFromEnv(env, 'AUTHOR'));
    assert.equal(e.message, 'fatal: mygit: GIT_AUTHOR_DATE is not ' +
      "'<seconds> <+hhmm>'");
  });
});

describe('messages', () => {
  test('s4_4 cleanup matches git', () => {
    // SPEC.md §4.4 의 예 — 진짜 git commit -m 으로 확인한 것
    assert.equal(
      commit.cleanupMessage('\n\n  lead  \n\nx   \n \n\n\ny\n\n'),
      '  lead\n\nx\n\ny\n');
    assert.equal(commit.cleanupMessage('one'), 'one\n');
    assert.equal(commit.cleanupMessage(' \n \n'), '');
  });

  test('s4_4 subject joins the first paragraph', () => {
    assert.equal(commit.subjectOf('second\n\nbody line\n'), 'second');
    assert.equal(commit.subjectOf('second\nbody line\n\npara2\n'),
      'second body line');
  });
});

describe('objects', () => {
  test('s4_4 parse and rebuild git commit', () => {
    const body = bodyOf(COMMIT);
    const c = commit.parseCommit(body);
    assert.deepEqual(c.parents, []);
    assert.deepEqual(commit.serializeCommit(c.tree, c.parents, c.author,
      c.committer, c.message), body);
  });

  test('s4_5 tag bytes match git', () => {
    const tagger = `C O Mitter <committer@example.com> ${ENV
      .GIT_COMMITTER_DATE}`;
    assert.deepEqual(commit.serializeTag(COMMIT, 'commit', 'v1', tagger,
      'tag message\n'), bodyOf(TAG));
  });
});

// .git 을 mygit init 으로 만드는 임시 저장소.
function repo() {
  const box = { tmp: '', root: '', gitdir: '' };
  const env = () => ({ ...ENV, GIT_CEILING_DIRECTORIES: box.tmp });
  beforeEach(() => {
    box.tmp = golden.tempdir();
    box.root = path.join(box.tmp, 'w');
    fs.mkdirSync(box.root);
    box.gitdir = path.join(box.root, '.git');
  });
  afterEach(() => golden.rmTree(box.tmp));
  const mygit = (...args: string[]) => cli.run(args, box.root, env());
  return {
    box,
    mygit,
    plantAll(): void {
      for (const oid of OBJS) {
        const p = objects.objectPath(box.gitdir, oid);
        fs.mkdirSync(path.dirname(p), { recursive: true });
        fs.writeFileSync(p, golden.read('objects', oid));
      }
    },
    // 표준 오류 첫 줄과 코드 — errors.tsv 의 한 행과 견준다
    async firstLine(...args: string[]): Promise<[number, string]> {
      const [code, , err] = await mygit(...args);
      return [code, err.toString().split('\n')[0]];
    },
  };
}

function want(command: string): [number, string] {
  const row = ERRORS.get(command)!;
  return [Number(row.exit), row['stderr-first-line']];
}

const read = (p: string) => fs.readFileSync(p, 'utf8');

describe('init', () => {
  const { box, mygit } = repo();

  test('s5_1 layout and message', async () => {
    const [code, out, err] = await mygit('init');
    assert.deepEqual([code, err.toString()], [0, '']);
    assert.equal(out.toString(),
      `Initialized empty Git repository in ${box.root}/.git/\n`);
    assert.equal(read(path.join(box.gitdir, 'HEAD')),
      'ref: refs/heads/main\n');
    assert.equal(read(path.join(box.gitdir, 'config')), '[core]\n' +
      '\trepositoryformatversion = 0\n\tfilemode = true\n' +
      '\tbare = false\n\tlogallrefupdates = true\n');
    for (const d of ['objects/pack', 'refs/heads', 'refs/tags']) {
      assert.ok(fs.statSync(path.join(box.gitdir, d)).isDirectory());
    }
  });

  test('s5_1 reinit touches nothing', async () => {
    await mygit('init');
    fs.writeFileSync(path.join(box.gitdir, 'HEAD'),
      'ref: refs/heads/dev\n');
    const [, out] = await mygit('init');
    assert.equal(out.toString(),
      `Reinitialized existing Git repository in ${box.root}/.git/\n`);
    assert.equal(read(path.join(box.gitdir, 'HEAD')),
      'ref: refs/heads/dev\n');
  });

  test('s5_1 init into a new directory', async () => {
    const [code] = await mygit('init', 'sub');
    assert.equal(code, 0);
    assert.ok(fs.existsSync(path.join(box.root, 'sub', '.git')));
  });
});

describe('commit-tree and tag', () => {
  const { box, mygit, plantAll, firstLine } = repo();
  const treeOf = () => commit.parseCommit(bodyOf(COMMIT)).tree;

  test('s4_4 commit-tree reproduces git commit', async () => {
    await mygit('init');
    plantAll();
    const [code, out, err] = await mygit('commit-tree', treeOf(), '-m',
      'objects');
    assert.deepEqual([code, out.toString(), err.toString()],
      [0, COMMIT + '\n', '']);
  });

  test('s4_4 parents and messages', async () => {
    await mygit('init');
    plantAll();
    let [, out] = await mygit('commit-tree', treeOf(), '-p', COMMIT,
      '-m', 'a', '-m', 'b');
    const load = (o: Buffer) => commit.parseCommit(
      objects.readObject(box.gitdir, o.toString().trim())[1]);
    const c = load(out);
    assert.deepEqual([c.parents, c.message], [[COMMIT], 'a\n\nb\n']);
    [, out] = await mygit('commit-tree', treeOf(), '-m', '  m1  ');
    assert.equal(load(out).message, '  m1  \n');
  });

  test('s4_5 annotated tag reproduces git tag', async () => {
    await mygit('init');
    plantAll();
    await mygit('branch', 'main', COMMIT);
    const [code, out, err] = await mygit('tag', '-a', 'v1', '-m',
      'tag message');
    assert.deepEqual([code, out.length, err.length], [0, 0, 0]);
    assert.equal(refs.resolveRef(box.gitdir, 'refs/tags/v1'), TAG);
  });

  test('s1_4 errors', async () => {
    await mygit('init');
    plantAll();
    await mygit('branch', 'main', COMMIT);
    for (const cmd of ['commit-tree nope -m x', 'branch x nope',
      'tag t nope', 'branch main', 'branch a..b']) {
      assert.deepEqual(await firstLine(...cmd.split(' ')), want(cmd),
        cmd);
    }
    await mygit('tag', 't');
    assert.deepEqual(await firstLine('tag', 't'), want('tag t'));
  });
});

describe('branch and reflog', () => {
  const { box, mygit, plantAll } = repo();

  test('s9_2 list and create', async () => {
    await mygit('init');
    plantAll();
    assert.equal((await mygit('branch', 'main', COMMIT))[0], 0);
    await mygit('branch', 'topic');
    assert.equal((await mygit('branch'))[1].toString(),
      '* main\n  topic\n');
    assert.equal(refs.resolveRef(box.gitdir, 'refs/heads/topic'),
      COMMIT);
  });

  test('s6_3 branch reflog', async () => {
    await mygit('init');
    plantAll();
    await mygit('branch', 'main', COMMIT);
    await mygit('branch', 'topic', 'main');
    assert.deepEqual(refs.readReflog(box.gitdir, 'refs/heads/topic'),
      [['0'.repeat(40), COMMIT,
        'C O Mitter <committer@example.com> 1700000000 +0900',
        'branch: Created from main']]);
    const [, out] = await mygit('reflog', 'topic');
    assert.equal(out.toString(),
      `${COMMIT.slice(0, 7)} topic@{0}: branch: Created from main\n`);
  });

  test('s6_3 reflog line bytes', async () => {
    await mygit('init');
    refs.appendReflog(box.gitdir, 'HEAD', '0'.repeat(40), COMMIT,
      'X <x@y> 1 +0000', 'commit (initial): t');
    assert.equal(read(path.join(box.gitdir, 'logs', 'HEAD')),
      `${'0'.repeat(40)} ${COMMIT} X <x@y> 1 +0000\t` +
      'commit (initial): t\n');
  });
});

// golden/dag/equal — 진짜 git 이 만든 역사. 이름과 7글자는 그
// 저장소에서 git log --oneline 이 찍은 것(expect.txt)이다.
describe('rev-parse', () => {
  let tmp = '';
  let gitdir = '';
  const ids = new Map<string, string>();
  before(() => {
    tmp = golden.tempdir();
    gitdir = path.join(tmp, '.git');
    fs.cpSync(golden.gpath('dag', 'equal', 'git'), gitdir,
      { recursive: true });
    fs.mkdirSync(path.join(gitdir, 'objects', 'pack'),
      { recursive: true });
    const text = golden.read('dag', 'equal', 'expect.txt').toString();
    const block = text.split('$ git log --oneline\n')[1]
      .split('= 0')[0];
    block.trim().split('\n').forEach((line, k) => {
      const sp = line.indexOf(' ');
      ids.set(`${k}:${line.slice(sp + 1)}`, line.slice(0, sp));
    });
  });
  after(() => golden.rmTree(tmp));

  const rp = (spec: string) =>
    refs.revParse(gitdir, spec)?.slice(0, 7) ?? null;

  test('s6_2 names and suffixes', () => {
    const i = (k: string) => ids.get(k)!;
    assert.equal(rp('HEAD'), i('0:I'));
    assert.equal(rp('main'), i('0:I'));
    assert.equal(rp('refs/heads/main'), i('0:I'));
    assert.equal(rp('main~1'), i("1:Merge branch 't'"));
    assert.equal(rp('HEAD~2'), i('2:G'));        // 첫 부모
    assert.equal(rp('HEAD~1^2'), i('3:H'));      // 둘째 부모
    assert.equal(rp('HEAD^^'), i('2:G'));
    assert.equal(rp('t'), i('3:H'));
    assert.equal(rp(i('2:G')), i('2:G'));        // 앞부분
    assert.equal(rp('HEAD^0'), i('0:I'));
    assert.equal(rp('nope'), null);
    assert.equal(rp('HEAD~99'), null);
  });

  test('s6_2 tree suffix', () => {
    const oid = refs.revParse(gitdir, 'HEAD^{tree}')!;
    assert.equal(objects.readObject(gitdir, oid)[0], 'tree');
  });
});

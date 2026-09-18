// 장면 시험 — golden/scen/*.scn 을 mygit 으로 다시 돌린다
// (SPEC.md §16.4).
//
// 장면의 기대 출력은 진짜 git 2.55.0 이 채웠다. 이 실행기는 같은 명령을
// 빈 임시 디렉터리에서 mygit 으로 돌리고, 명령마다 표준 출력·표준 오류·
// 종료 코드를 한 글자씩 견준다. 장면은 자기에게 필요한 명령이 다
// 생기는 단계(STEP)부터 켜진다 — 그 전에는 이유를 달고 건너뛴다.
// 12단계를 마치면 건너뛰는 장면이 하나도 없어야 한다.
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { test } from 'node:test';
import * as cli from '../src/cli';
import { STEP } from '../src/errors';
import * as index from '../src/index';
import * as refs from '../src/refs';
import { quotePath } from '../src/worktree';
import * as golden from './golden';

// 장면 → 켜지는 단계 (그 장면이 쓰는 명령이 모두 생기는 단계)
const NEEDS: Record<string, number> = { plumbing: 6, status: 6,
  hello: 7, diff: 8, checkout: 9, errors: 10, clone: 12 };
const ENV = {
  GIT_AUTHOR_NAME: 'A U Thor',
  GIT_AUTHOR_EMAIL: 'author@example.com',
  GIT_COMMITTER_NAME: 'C O Mitter',
  GIT_COMMITTER_EMAIL: 'committer@example.com',
};

const stepOf = (name: string) =>
  name.startsWith('merge-') ? 10 : NEEDS[name];

// SPEC.md §16.4 — 공백으로 가르고 "…" 는 한 덩어리.
function splitArgs(line: string): string[] {
  const args: string[] = [];
  let cur: string | null = null;
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (quoted) {
      if (c === '\\' && i + 1 < line.length) {
        const n = line[++i];
        cur += n === 'n' ? '\n' : n === 't' ? '\t' : n;
      } else if (c === '"') {
        quoted = false;
      } else {
        cur += c;
      }
    } else if (c === '"') {
      quoted = true;
      cur ??= '';
    } else if (/\s/.test(c)) {
      if (cur !== null) args.push(cur);
      cur = null;
    } else {
      cur = (cur ?? '') + c;
    }
  }
  if (cur !== null) args.push(cur);
  return args;
}

// .scn → [명령 줄, 기대 줄들]. 기대 줄은 '> ' · '! ' · '= ' 로
// 시작하거나 '%noeol' 이다.
function parse(text: string): [string, string[]][] {
  const steps: [string, string[]][] = [];
  for (const line of text.split('\n')) {
    if (!line || line.startsWith('#')) continue;
    if (['> ', '! ', '= '].includes(line.slice(0, 2)) ||
      line === '%noeol') {
      steps[steps.length - 1][1].push(line);
    } else {
      steps.push([line, []]);
    }
  }
  return steps;
}

type Got = [out: Buffer, err: Buffer, code: number];

// 실제 결과를 .scn 의 기대 줄 꼴로 — 같은 규칙으로 견주려고.
function render([out, err, code]: Got): string[] {
  const rows: string[] = [];
  for (const [prefix, data] of [['> ', out], ['! ', err]] as const) {
    const text = data.toString('utf8');
    if (!text) continue;
    const body = text.endsWith('\n') ? text.slice(0, -1) : text;
    rows.push(...body.split('\n').map((l) => prefix + l));
    if (!text.endsWith('\n')) rows.push('%noeol');
  }
  if (code) rows.push(`= ${code}`);
  return rows;
}

class Scene {
  cwd: string;
  env: Record<string, string | undefined>;

  constructor(readonly root: string) {
    this.cwd = root;
    this.env = { ...process.env, ...ENV,
      GIT_CEILING_DIRECTORIES: path.dirname(root) };
    this.date(1700000000);
  }

  date(secs: number): void {
    for (const who of ['AUTHOR', 'COMMITTER']) {
      this.env[`GIT_${who}_DATE`] = `${secs} +0900`;
    }
  }

  gitdir(): string {
    return new cli.Ctx(this.cwd, this.env, Buffer.alloc(0)).gitdir();
  }

  // 한 줄을 돌려 [표준 출력, 표준 오류, 코드]. 손질 줄은 null.
  async do(line: string): Promise<Got | null> {
    const a = splitArgs(line);
    const p = a.length > 1 ? path.join(this.cwd, a[1]) : '';
    const text = (s: string): Got =>
      [Buffer.from(s), Buffer.alloc(0), 0];
    switch (a[0]) {
      case '@date':
        this.date(Number(a[1]));
        return null;
      case '@cd':
        this.cwd = path.join(this.root, a[1]);
        return null;
      case 'write':
      case 'append':
        fs.mkdirSync(path.dirname(p), { recursive: true });
        fs.writeFileSync(p, golden.make(a[2]),
          { flag: a[0] === 'append' ? 'a' : 'w' });
        return null;
      case 'chmod':
        fs.chmodSync(p, parseInt(a[2], 8));
        return null;
      case 'rm':
        fs.rmSync(p);
        return null;
      case 'mkdir':
        fs.mkdirSync(p, { recursive: true });
        return null;
      case 'mygit': {
        const args = a.slice(1)
          .map((x) => x.replace('<ROOT>', this.root));
        const [code, out, err] = await cli.run(args, this.cwd,
          this.env);
        return [out, err, code];
      }
      case 'cat':
        return [fs.readFileSync(p), Buffer.alloc(0), 0];
      case 'stage':
        return text(index.readIndex(this.gitdir()).map((e) =>
          `${e.mode.toString(8).padStart(6, '0')} ${e.oid} ${e.stage}` +
          `\t${quotePath(e.path)}\n`).join(''));
      case 'ref':
        return text(`${refs.revParse(this.gitdir(), a[1])}\n`);
    }
    throw new Error(`모르는 장면 줄: ${line}`);
  }
}

for (const f of fs.readdirSync(golden.gpath('scen')).sort()) {
  const name = f.slice(0, -4);
  test(`s16_4 ${name}`, async (t) => {
    if (STEP < stepOf(name)) {
      t.skip(`${stepOf(name)}단계에서 켜진다`);
      return;
    }
    const tmp = golden.tempdir();
    try {
      const root = path.join(tmp, 'scene');
      fs.mkdirSync(root);
      const sc = new Scene(root);
      const text = golden.read('scen', f).toString('utf8');
      for (const [k, [line, want]] of parse(text).entries()) {
        const got = await sc.do(line);
        if (got === null) {
          assert.deepEqual(want, [], line);
          continue;
        }
        assert.deepEqual(render(got),
          want.map((w) => w.replace('<ROOT>', root)),
          `${name} 장면 ${k}번째 줄: ${line}`);
      }
    } finally {
      golden.rmTree(tmp);
    }
  });
}

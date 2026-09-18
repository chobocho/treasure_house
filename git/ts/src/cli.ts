// 명령줄 (SPEC.md §1 · §9) — 인자를 읽고, 모듈을 부르고, 찍는다.
//
// 출력은 이 파일만 한다. 다른 모듈은 값을 돌려주거나 GitError 를
// 던질 뿐이다 — 그래야 시험이 출력을 가로채지 않고 반환값을 본다.
// run() 은 과정 안에서 부를 수 있는 꼴 [코드, 표준 출력, 표준 오류]
// 이고, main.ts 가 그것을 진짜 표준 스트림에 잇는다.
//
// 명령은 맨 아래 COMMANDS 표에 이름으로 붙는다. 단계가 늘 때마다 한
// 줄씩 는다. run 이 async 인 까닭은 fetch-pack 하나다 — 자식 git 과의
// 대화는 기다림이다(12단계). 나머지 명령은 모두 동기로 돈다.
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as commit from './commit';
import { GitError } from './errors';
import * as objects from './objects';
import * as refs from './refs';
import * as tree from './tree';
import * as worktree from './worktree';

type Env = Record<string, string | undefined>;
export type Result = [code: number, out: Buffer, err: Buffer];
type Command = (ctx: Ctx, args: string[]) => number | Promise<number>;

const NOT_A_REPO = 'fatal: not a git repository (or any of the ' +
  'parent directories): .git';

// 명령 하나가 도는 동안의 문맥 — 현재 디렉터리·환경·입출력.
export class Ctx {
  readonly cwd: string;
  readonly env: Env;
  private out: Buffer[] = [];
  private err: Buffer[] = [];
  private top: string | null = null;

  constructor(cwd: string | undefined, env: Env | undefined,
    private stdin: Buffer | null) {
    this.cwd = path.resolve(cwd ?? process.cwd());
    this.env = { ...(env ?? process.env) };
  }

  // 표준 입력 전부. 필요한 명령(--stdin)만 부른다 — 늘 읽으면 입력이
  // 닫히지 않은 파이프에서 부를 때 멈춘다.
  readStdin(): Buffer {
    this.stdin ??= fs.readFileSync(0);
    return this.stdin;
  }

  say(text: string | Uint8Array): void {
    this.out.push(Buffer.from(text));
  }

  warn(text: string | Uint8Array): void {
    this.err.push(Buffer.from(text));
  }

  result(code: number): Result {
    return [code, Buffer.concat(this.out), Buffer.concat(this.err)];
  }

  // 작업 트리의 뿌리 — .git 을 품은 디렉터리(SPEC.md §1.1).
  //
  // 현재 디렉터리부터 위로 올라가며 .git 을 찾는다.
  // GIT_CEILING_DIRECTORIES 에 적힌 디렉터리 안으로는 올라가지
  // 않는다 — 현재 디렉터리 자신은 언제나 본다. O(깊이).
  root(): string {
    if (this.top) return this.top;
    const spec = this.env.GIT_CEILING_DIRECTORIES ?? '';
    const ceil = new Set(spec.split(':').filter((p) => p)
      .map((p) => path.resolve(p)));
    for (let d = this.cwd; ;) {
      if (isDir(path.join(d, '.git'))) return (this.top = d);
      const up = path.dirname(d);
      if (up === d || ceil.has(up)) throw new GitError(NOT_A_REPO);
      d = up;
    }
  }

  gitdir(): string {
    return path.join(this.root(), '.git');
  }

  // 명령줄의 경로 → 절대 경로(현재 디렉터리 기준).
  path(name: string): string {
    return path.resolve(this.cwd, name);
  }
}

function isDir(p: string): boolean {
  return fs.statSync(p, { throwIfNoEntry: false })?.isDirectory() ??
    false;
}

// <rev> → 객체 이름. 없으면 null (SPEC.md §6.2).
function resolve(ctx: Ctx, name: string): string | null {
  return refs.revParse(ctx.gitdir(), name);
}

const AMBIGUOUS = (name: string) => `fatal: ambiguous argument ` +
  `'${name}': unknown revision or path not in the working tree.\n` +
  "Use '--' to separate paths from revisions, like this:\n" +
  "'git <command> [<revision>...] -- [<file>...]'";

function ident(ctx: Ctx, who = 'COMMITTER'): string {
  return commit.identFromEnv(ctx.env, who);
}

// [켜진 짧은 옵션 집합, 값 옵션 표, 나머지 인자].
//
// 모르는 옵션은 SPEC.md §1.4 의 "unknown option" 오류다. '--' 뒤는
// 전부 인자로 본다.
function parseFlags(args: string[], flags: string[],
  valued: string[] = []):
  [Set<string>, Map<string, string>, string[]] {
  const on = new Set<string>();
  const vals = new Map<string, string>();
  const rest: string[] = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--') {
      rest.push(...args.slice(i + 1));
      break;
    }
    if (valued.includes(a)) {
      if (i + 1 === args.length) {
        throw new GitError(`fatal: mygit: option '${a}' needs a value`);
      }
      vals.set(a, args[++i]);
    } else if (flags.includes(a)) {
      on.add(a);
    } else if (a.startsWith('-') && a !== '-') {
      throw new GitError(`fatal: mygit: unknown option '${a}'`);
    } else {
      rest.push(a);
    }
  }
  return [on, vals, rest];
}

// ── 3단계: hash-object · cat-file ─────────────────────────────────

// libc 의 strerror 문장. node 는 ENOENT 같은 코드만 주는데 git 은
// 문장을 찍는다(SPEC.md §1.4 의 hash-object 줄).
const STRERROR: Record<string, string> = {
  ENOENT: 'No such file or directory',
  EACCES: 'Permission denied',
  EISDIR: 'Is a directory',
};

function cmdHashObject(ctx: Ctx, args: string[]): number {
  const [on, vals, rest] = parseFlags(args, ['-w', '--stdin'], ['-t']);
  const type = vals.get('-t') ?? 'blob';
  if (!objects.TYPES.includes(type)) {
    throw new GitError(`fatal: mygit: unknown object type '${type}'`);
  }
  const bodies = on.has('--stdin') ? [ctx.readStdin()] : rest.map(
    (name) => {
      try {
        return fs.readFileSync(ctx.path(name));
      } catch (e) {
        const code = (e as NodeJS.ErrnoException).code ?? '';
        throw new GitError(`fatal: could not open '${name}' for ` +
          `reading: ${STRERROR[code] ?? code}`);
      }
    });
  for (const body of bodies) {
    const oid = on.has('-w')
      ? objects.writeObject(ctx.gitdir(), type, body)
      : objects.hashObject(type, body);
    ctx.say(oid + '\n');
  }
  return 0;
}

// cat-file -p 의 몸. blob·commit·tag 는 그대로, 트리는 항목마다
// "%06o 형식 이름\t경로" (SPEC.md §9, 경로 따옴표는 §8.2).
function pretty(type: string, body: Buffer): Buffer | string {
  if (type !== 'tree') return body;
  return tree.parseTree(body).map(([mode, name, oid]) =>
    `${mode.padStart(6, '0')} ${tree.typeOfMode(mode)} ${oid}\t` +
    `${worktree.quotePath(name)}\n`).join('');
}

function cmdCatFile(ctx: Ctx, args: string[]): number {
  const [on, , rest] = parseFlags(args, ['-t', '-s', '-p']);
  if (on.size !== 1 || rest.length !== 1) {
    throw new GitError('usage: mygit cat-file (-t | -s | -p) <object>',
      129);
  }
  const oid = resolve(ctx, rest[0]);
  if (oid === null) {
    throw new GitError(`fatal: Not a valid object name ${rest[0]}`);
  }
  const [type, body] = objects.readObject(ctx.gitdir(), oid);
  if (on.has('-t')) ctx.say(type + '\n');
  else if (on.has('-s')) ctx.say(`${body.length}\n`);
  else ctx.say(pretty(type, body));
  return 0;
}

// ── 5단계: init · commit-tree · branch · tag · reflog ────────────
const CONFIG = '[core]\n\trepositoryformatversion = 0\n' +
  '\tfilemode = true\n\tbare = false\n\tlogallrefupdates = true\n';

// top/.git 을 SPEC.md §5.1 의 꼴로. → [.git 경로, 이미 있었나].
function makeRepo(top: string): [string, boolean] {
  const g = path.join(path.resolve(top), '.git');
  const again = isDir(g);
  for (const d of ['objects/pack', 'refs/heads', 'refs/tags']) {
    fs.mkdirSync(path.join(g, d), { recursive: true });
  }
  for (const [name, text] of [['HEAD', 'ref: refs/heads/main\n'],
    ['config', CONFIG]]) {
    const p = path.join(g, name);
    if (!fs.existsSync(p)) fs.writeFileSync(p, text);
  }
  return [g, again];
}

// SPEC.md §5.1 — 이미 있으면 아무것도 덮어쓰지 않는다.
function cmdInit(ctx: Ctx, args: string[]): number {
  const [, , rest] = parseFlags(args, []);
  const top = rest.length ? ctx.path(rest[0]) : ctx.cwd;
  const [g, again] = makeRepo(top);
  ctx.say(`${again ? 'Reinitialized existing' : 'Initialized empty'}` +
    ` Git repository in ${g}/\n`);
  return 0;
}

// -p 와 -m 은 몇 번이든, 준 차례대로. 메시지는 원문 그대로 + 줄바꿈
// — 공백 정리는 commit 명령만 한다(SPEC.md §4.4).
function cmdCommitTree(ctx: Ctx, args: string[]): number {
  let treeArg: string | null = null;
  const parents: string[] = [];
  const msgs: string[] = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '-p' || a === '-m') {
      const val = args[++i];
      if (val === undefined) {
        throw new GitError(`fatal: mygit: option '${a}' needs a value`);
      }
      if (a === '-m') {
        msgs.push(val);
        continue;
      }
      const oid = resolve(ctx, val);
      if (oid === null) {
        throw new GitError(`fatal: not a valid object name ${val}`);
      }
      parents.push(oid);
    } else if (a.startsWith('-')) {
      throw new GitError(`fatal: mygit: unknown option '${a}'`);
    } else {
      treeArg = a;
    }
  }
  if (treeArg === null || !msgs.length) {
    throw new GitError('usage: mygit commit-tree <tree> ' +
      '[-p <parent>]... -m <message>...', 129);
  }
  const oid = resolve(ctx, treeArg);
  const t = oid ? refs.peel(ctx.gitdir(), oid, 'tree') : null;
  if (t === null) {
    throw new GitError(`fatal: not a valid object name ${treeArg}`);
  }
  const body = commit.serializeCommit(t, parents, ident(ctx, 'AUTHOR'),
    ident(ctx), msgs.join('\n\n') + '\n');
  ctx.say(objects.writeObject(ctx.gitdir(), 'commit', body) + '\n');
  return 0;
}

const HEADS = 'refs/heads/';

function listBranches(ctx: Ctx): number {
  const g = ctx.gitdir();
  const [cur, head] = refs.readHead(g);
  if (cur === null && head) {
    ctx.say(`* (HEAD detached at ${head.slice(0, 7)})\n`);
  }
  for (const [name] of refs.listRefs(g, HEADS)) {
    ctx.say((name === cur ? '* ' : '  ') + name.slice(HEADS.length) +
      '\n');
  }
  return 0;
}

function cmdBranch(ctx: Ctx, args: string[]): number {
  const [, , rest] = parseFlags(args, []);
  if (!rest.length) return listBranches(ctx);
  const name = rest[0];
  const g = ctx.gitdir();
  if (!refs.validBranchName(name)) {
    throw new GitError(`fatal: '${name}' is not a valid branch name`);
  }
  if (refs.resolveRef(g, HEADS + name)) {
    throw new GitError(`fatal: a branch named '${name}' already ` +
      'exists');
  }
  const start = rest[1] ?? 'HEAD';
  let oid = resolve(ctx, start);
  oid = oid ? refs.peel(g, oid, 'commit') : null;
  if (oid === null) {
    throw new GitError(`fatal: not a valid object name: '${start}'`);
  }
  refs.updateRef(g, HEADS + name, oid, null,
    `branch: Created from ${start}`, ident(ctx));
  return 0;
}

function cmdTag(ctx: Ctx, args: string[]): number {
  const [on, vals, rest] = parseFlags(args, ['-a'], ['-m']);
  const g = ctx.gitdir();
  if (!rest.length) {
    for (const [name] of refs.listRefs(g, 'refs/tags/')) {
      ctx.say(name.slice('refs/tags/'.length) + '\n');
    }
    return 0;
  }
  const name = rest[0];
  const target = rest[1] ?? 'HEAD';
  if (refs.readRef(g, 'refs/tags/' + name)) {
    throw new GitError(`fatal: tag '${name}' already exists`);
  }
  let oid = resolve(ctx, target);
  if (oid === null) {
    throw new GitError(`fatal: Failed to resolve '${target}' as a ` +
      'valid ref.');
  }
  if (on.has('-a') || vals.has('-m')) {
    const [type] = objects.readObject(g, oid);
    const msg = commit.cleanupMessage(vals.get('-m') ?? '');
    const body = commit.serializeTag(oid, type, name, ident(ctx), msg);
    oid = objects.writeObject(g, 'tag', body);
  }
  // 태그는 reflog 를 남기지 않는다 — logallrefupdates 는 브랜치와
  // HEAD 만 기록한다(git 과 같다)
  const file = path.join(g, 'refs', 'tags', name);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, oid + '\n');
  return 0;
}

// reflog 가 읽을 파일의 참조 이름. HEAD · 브랜치 · refs/…
function reflogName(ctx: Ctx, name: string): string | null {
  return [name, HEADS + name].find((cand) =>
    fs.existsSync(path.join(ctx.gitdir(), 'logs', cand))) ?? null;
}

// 새것부터 '<7글자> <ref>@{n}: <메시지>' (SPEC.md §6.3).
function cmdReflog(ctx: Ctx, args: string[]): number {
  const rest = parseFlags(args, [])[2].filter((a) => a !== 'show');
  const name = rest[0] ?? 'HEAD';
  const log = reflogName(ctx, name);
  if (log === null) {
    if (name === 'HEAD') return 0;
    throw new GitError(AMBIGUOUS(name));
  }
  refs.readReflog(ctx.gitdir(), log).reverse()
    .forEach(([, next, , msg], k) =>
      ctx.say(`${next.slice(0, 7)} ${name}@{${k}}: ${msg}\n`));
  return 0;
}

// ── 틀 ────────────────────────────────────────────────────────────
const COMMANDS = new Map<string, Command>([
  ['hash-object', cmdHashObject],
  ['cat-file', cmdCatFile],
  ['init', cmdInit],
  ['commit-tree', cmdCommitTree],
  ['branch', cmdBranch],
  ['tag', cmdTag],
  ['reflog', cmdReflog],
]);

// 명령 하나를 돌린다 → [종료 코드, 표준 출력, 표준 오류]. stdin 이
// null 이면 진짜 표준 입력을 (필요할 때만) 읽는다.
export async function run(args: string[], cwd?: string, env?: Env,
  stdin: Buffer | null = Buffer.alloc(0)): Promise<Result> {
  const ctx = new Ctx(cwd, env, stdin);
  if (!args.length) {
    ctx.warn('usage: mygit <command> [<args>]\n');
    return ctx.result(129);
  }
  const fn = COMMANDS.get(args[0]);
  if (fn === undefined) {
    ctx.warn(`mygit: '${args[0]}' is not a mygit command.\n`);
    return ctx.result(1);
  }
  let code: number;
  try {
    code = await fn(ctx, args.slice(1));
  } catch (e) {
    if (!(e instanceof GitError)) throw e;
    ctx.warn(e.message + '\n');
    code = e.code;
  }
  return ctx.result(code);
}

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
import * as diff from './diff';
import { GitError } from './errors';
import * as index from './index';
import * as objects from './objects';
import * as refs from './refs';
import * as tree from './tree';
import * as walk from './walk';
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
  const [on, , rest] = parseFlags(args, ['-d']);
  if (on.has('-d')) return deleteBranch(ctx, rest);
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

// branch -d — HEAD 에서 닿는 브랜치만 지운다(SPEC.md §9.2).
function deleteBranch(ctx: Ctx, rest: string[]): number {
  const g = ctx.gitdir();
  const [cur, head] = refs.readHead(g);
  for (const name of rest) {
    const ref = HEADS + name;
    const oid = refs.resolveRef(g, ref);
    if (ref === cur) {
      throw new GitError(`error: cannot delete branch '${name}' used ` +
        `by worktree at '${ctx.root()}'`, 1);
    }
    if (oid === null) {
      throw new GitError(`error: branch '${name}' not found.`, 1);
    }
    if (head === null || !walk.isAncestor(g, oid, head)) {
      throw new GitError(`error: the branch '${name}' is not fully ` +
        'merged', 1);
    }
    refs.updateRef(g, ref, null, oid, '', '');
    ctx.say(`Deleted branch ${name} (was ${oid.slice(0, 7)}).\n`);
  }
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

// ── 6단계: add · rm --cached · status · write-tree · commit ───────

// 명령줄 경로 → 작업 트리 뿌리에서의 경로 바이트 문자열('' 은 뿌리).
function relPath(ctx: Ctx, spec: string): string {
  return Buffer.from(path.relative(ctx.root(), ctx.path(spec)))
    .toString('latin1');
}

const under = (p: string, rel: string) =>
  !rel || p === rel || p.startsWith(rel + '/');

const noMatch = (spec: string) =>
  new GitError(`fatal: pathspec '${spec}' did not match any files`);

// pathspec 아래의 파일을 올리고, 사라진 파일은 뺀다(SPEC.md §9).
//
// 모든 pathspec 을 먼저 검사한다 — 하나라도 맞는 것이 없으면 아무것도
// 바꾸지 않고 멈춘다(git 과 같다).
function cmdAdd(ctx: Ctx, args: string[]): number {
  const [, , rest] = parseFlags(args, []);
  const [root, g] = [ctx.root(), ctx.gitdir()];
  const ents = index.readIndex(g);
  const files = worktree.walkWorktree(root);
  const plan = rest.map((spec): [string[], Set<string>] => {
    const rel = relPath(ctx, spec);
    const hitF = files.filter((f) => under(f, rel));
    const hitI = new Set(ents.map((e) => e.path)
      .filter((p) => under(p, rel)));
    if (!hitF.length && !hitI.size) throw noMatch(spec);
    return [hitF, hitI];
  });
  const byPath = new Map<string, index.IndexEntry[]>();
  for (const e of ents) {
    byPath.set(e.path, [...byPath.get(e.path) ?? [], e]);
  }
  for (const [hitF, hitI] of plan) {
    for (const f of hitF) {
      const full = worktree.fsPath(root, f);
      const oid = objects.writeObject(g, 'blob', fs.readFileSync(full));
      byPath.set(f, [index.entryFromStat(f, full, oid)]);
    }
    for (const p of hitI) if (!hitF.includes(p)) byPath.delete(p);
  }
  index.writeIndex(g, [...byPath.values()].flat());
  return 0;
}

// 찍는 경로는 따옴표 없이 그대로다 — git 의 rm 이 그렇게 찍는다.
function cmdRm(ctx: Ctx, args: string[]): number {
  const [on, , rest] = parseFlags(args, ['--cached']);
  if (!on.has('--cached')) {
    throw new GitError('fatal: mygit: only rm --cached is supported');
  }
  const g = ctx.gitdir();
  const ents = index.readIndex(g);
  const have = new Set(ents.map((e) => e.path));
  const gone = new Set(rest.map((spec) => {
    const rel = relPath(ctx, spec);
    if (!have.has(rel)) throw noMatch(spec);
    return rel;
  }));
  for (const p of [...gone].sort()) {
    ctx.say(`rm '${Buffer.from(p, 'latin1').toString('utf8')}'\n`);
  }
  index.writeIndex(g, ents.filter((e) => !gone.has(e.path)));
  return 0;
}

function cmdStatus(ctx: Ctx, args: string[]): number {
  parseFlags(args, ['--porcelain', '-s', '--short']);
  for (const row of worktree.status(ctx.root(), ctx.gitdir())) {
    ctx.say(row + '\n');
  }
  return 0;
}

// 인덱스(단계 0) → 트리 이름. 충돌 경로가 있으면 쓸 수 없다.
function indexTree(ctx: Ctx): string {
  const ents = index.readIndex(ctx.gitdir());
  if (ents.some((e) => e.stage)) {
    throw new GitError('error: Committing is not possible because ' +
      'you have unmerged files.\nfatal: Exiting because of an ' +
      'unresolved conflict.');
  }
  return tree.writeTree(ctx.gitdir(),
    ents.map((e) => [e.mode.toString(8), e.oid, e.path]));
}

function cmdWriteTree(ctx: Ctx, args: string[]): number {
  parseFlags(args, []);
  ctx.say(indexTree(ctx) + '\n');
  return 0;
}

// 트리를 쓰고, 커밋하고, 브랜치를 옮긴다(SPEC.md §9 · §6.3).
//
// 부모는 HEAD 와, 머지를 마무리하는 중이면 MERGE_HEAD. 출력은 git 의
// 요약 첫 줄만 — Author 줄과 변경 통계는 줄임이다.
function cmdCommit(ctx: Ctx, args: string[]): number {
  const msgs: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] !== '-m') {
      throw new GitError(`fatal: mygit: unknown option '${args[i]}'`);
    }
    msgs.push(args[++i] ?? '');
  }
  const g = ctx.gitdir();
  const [branch, head] = refs.readHead(g);
  const mergeHead = refs.resolveRef(g, 'MERGE_HEAD');
  const t = indexTree(ctx);
  if (head && !mergeHead && refs.peel(g, head, 'tree') === t) {
    ctx.say('nothing to commit\n');
    return 1;
  }
  const msg = commit.cleanupMessage(msgs.join('\n\n'));
  if (!msg) {
    throw new GitError('Aborting commit due to empty commit message.',
      1);
  }
  const parents = [head, mergeHead].filter((p): p is string => !!p);
  const body = commit.serializeCommit(t, parents, ident(ctx, 'AUTHOR'),
    ident(ctx), msg);
  const oid = objects.writeObject(g, 'commit', body);
  const subj = commit.subjectOf(msg);
  const kind = !head ? 'commit (initial)'
    : mergeHead ? 'commit (merge)' : 'commit';
  refs.updateRef(g, branch ?? 'HEAD', oid, head, `${kind}: ${subj}`,
    ident(ctx));
  for (const f of ['MERGE_HEAD', 'MERGE_MSG']) {
    fs.rmSync(path.join(g, f), { force: true });
  }
  const where = branch ? branch.slice(HEADS.length) : 'detached HEAD';
  const root = head ? '' : ' (root-commit)';
  ctx.say(`[${where}${root} ${oid.slice(0, 7)}] ${subj}\n`);
  return 0;
}

// ── 7단계: log · merge-base ───────────────────────────────────────

// 커밋 하나를 git log 의 꼴로(SPEC.md §9.1).
function logEntry(ctx: Ctx, oid: string, oneline: boolean): string {
  const [, body] = objects.readObject(ctx.gitdir(), oid);
  const c = commit.parseCommit(body);
  const short = (o: string) => o.slice(0, 7);
  if (oneline) return `${short(oid)} ${commit.subjectOf(c.message)}\n`;
  const [name, mail, secs, tz] = commit.parseIdent(c.author);
  const rows = [`commit ${oid}`];
  if (c.parents.length > 1) {
    rows.push('Merge: ' + c.parents.map(short).join(' '));
  }
  rows.push(`Author: ${name} <${mail}>`,
    `Date:   ${commit.formatDate(secs, tz)}`, '');
  const msg = c.message.endsWith('\n') ? c.message.slice(0, -1)
    : c.message;
  rows.push(...msg.split('\n').map((line) => '    ' + line));
  return rows.join('\n') + '\n';
}

function cmdLog(ctx: Ctx, args: string[]): number {
  const [on, vals, rest] = parseFlags(args, ['--oneline'], ['-n']);
  const g = ctx.gitdir();
  let start: string | null;
  if (rest.length) {
    start = resolve(ctx, rest[0]);
    start = start && refs.peel(g, start, 'commit');
    if (start === null) throw new GitError(AMBIGUOUS(rest[0]));
  } else {
    const [branch, head] = refs.readHead(g);
    if (head === null) {
      throw new GitError(`fatal: your current branch ` +
        `'${branch?.slice(HEADS.length)}' does not have any ` +
        'commits yet');
    }
    start = head;
  }
  let order = walk.walkLog(g, [start]);
  if (vals.has('-n')) order = order.slice(0, Number(vals.get('-n')));
  const oneline = on.has('--oneline');
  ctx.say(order.map((oid) => logEntry(ctx, oid, oneline))
    .join(oneline ? '' : '\n'));
  return 0;
}

function cmdMergeBase(ctx: Ctx, args: string[]): number {
  const [on, , rest] = parseFlags(args, ['--all']);
  if (rest.length !== 2) {
    throw new GitError('usage: mygit merge-base [--all] <a> <b>', 129);
  }
  const g = ctx.gitdir();
  const [a, b] = rest.map((name) => {
    const oid = resolve(ctx, name);
    const c = oid && refs.peel(g, oid, 'commit');
    if (c) return c;
    throw new GitError(`fatal: Not a valid object name ${name}`);
  });
  const best = walk.mergeBases(g, a, b);
  if (!best.length) return 1;
  for (const oid of on.has('--all') ? best : best.slice(0, 1)) {
    ctx.say(oid + '\n');
  }
  return 0;
}

// ── 8단계: diff ───────────────────────────────────────────────────

// [모드, 이름, 바이트] — 디스크의 파일에서. 없으면 null.
function diskSide(full: Buffer | string): diff.Side | null {
  const st = fs.statSync(full, { throwIfNoEntry: false });
  if (!st?.isFile()) return null;
  const data = fs.readFileSync(full);
  const mode = st.mode & 0o100 ? 0o100755 : 0o100644;
  return [mode, objects.hashObject('blob', data), data];
}

// <rev> 의 트리를 펼쳐 {경로: [모드, 이름]}.
function revTree(ctx: Ctx, rev: string): Map<string, worktree.Stat> {
  const g = ctx.gitdir();
  const oid = resolve(ctx, rev);
  const t = oid && refs.peel(g, oid, 'tree');
  if (!t) throw new GitError(AMBIGUOUS(rev));
  return worktree.treeMap(g, t);
}

type Stat = worktree.Stat | undefined;

// SPEC.md §11.5 의 네 꼴. --no-index 만 다르면 1 로 끝난다.
function cmdDiff(ctx: Ctx, args: string[]): number {
  const [on, , rest] = parseFlags(args, ['--cached', '--no-index']);
  if (on.has('--no-index')) {
    if (rest.length !== 2) {
      throw new GitError('usage: mygit diff --no-index <a> <b>', 129);
    }
    const [a, b] = rest.map((p) => Buffer.from(p).toString('latin1'));
    const text = diff.fileDiff(a, b, diskSide(ctx.path(rest[0])),
      diskSide(ctx.path(rest[1])));
    ctx.say(Buffer.from(text, 'latin1'));
    return text ? 1 : 0;
  }
  const g = ctx.gitdir();
  const root = ctx.root();
  const worktreeSide = !rest.length && !on.has('--cached');
  const pairs: [string, Stat, Stat][] = [];  // 바이트는 나중에
  const both = (a: Map<string, worktree.Stat>,
    b: Map<string, worktree.Stat>) => {
    for (const p of worktree.sortedKeys(a, b)) {
      pairs.push([p, a.get(p), b.get(p)]);
    }
  };
  if (rest.length === 2) {
    both(revTree(ctx, rest[0]), revTree(ctx, rest[1]));
  } else if (on.has('--cached')) {
    const [, head] = refs.readHead(g);
    both(head ? revTree(ctx, head) : new Map(),
      new Map(index.readIndex(g).filter((e) => e.stage === 0)
        .map((e) => [e.path, [e.mode, e.oid]])));
  } else if (worktreeSide) {
    const ents = index.readIndex(g);
    const unmerged = new Set(ents.filter((e) => e.stage)
      .map((e) => e.path));
    for (const e of ents) {
      if (unmerged.has(e.path)) continue;   // 충돌 경로는 줄임
      const now = diskSide(worktree.fsPath(root, e.path));
      pairs.push([e.path, [e.mode, e.oid], now ? [now[0], now[1]]
        : undefined]);
    }
  } else {
    throw new GitError(AMBIGUOUS(rest[0]));
  }
  for (const [p, old, nu] of pairs) {
    if (worktree.same(old, nu)) continue;
    const o = old ? diff.blobSide(g, ...old) : null;
    const n = !nu ? null : worktreeSide
      ? diskSide(worktree.fsPath(root, p)) : diff.blobSide(g, ...nu);
    ctx.say(Buffer.from(diff.fileDiff(p, p, o, n), 'latin1'));
  }
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
  ['add', cmdAdd],
  ['rm', cmdRm],
  ['status', cmdStatus],
  ['write-tree', cmdWriteTree],
  ['commit', cmdCommit],
  ['log', cmdLog],
  ['merge-base', cmdMergeBase],
  ['diff', cmdDiff],
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

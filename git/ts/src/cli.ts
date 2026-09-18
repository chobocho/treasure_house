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
import { GitError } from './errors';
import * as objects from './objects';
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
//
// 3단계에서는 16진 이름과 앞부분만 푼다. 참조와 뒤붙이(~ ^)는 5단계의
// refs.revParse 가 맡는다.
function resolve(ctx: Ctx, name: string): string | null {
  return objects.findObject(ctx.gitdir(), name);
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

// ── 틀 ────────────────────────────────────────────────────────────
const COMMANDS = new Map<string, Command>([
  ['hash-object', cmdHashObject],
  ['cat-file', cmdCatFile],
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

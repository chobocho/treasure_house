# -*- coding: utf-8 -*-
"""명령줄 (SPEC.md §1 · §9) — 인자를 읽고, 모듈을 부르고, 찍는다.

출력은 이 파일만 한다. 다른 모듈은 값을 돌려주거나 GitError 를
던질 뿐이다 — 그래야 시험이 출력을 가로채지 않고 반환값을 본다.
run() 은 과정 안에서 부를 수 있는 꼴(코드, 표준 출력, 표준 오류)이고,
main() 은 그것을 진짜 표준 스트림에 잇는다.

명령은 COMMANDS 표에 이름으로 붙는다. 단계가 늘 때마다 한 줄씩 는다.
"""
import os
import sys

from mygit import GitError, objects, tree, worktree

COMMANDS = {}

NOT_A_REPO = ('fatal: not a git repository (or any of the parent '
              'directories): .git')


def command(name):
    def put(fn):
        COMMANDS[name] = fn
        return fn
    return put


class Ctx(object):
    """명령 하나가 도는 동안의 문맥 — 현재 디렉터리·환경·입출력."""

    def __init__(self, cwd, env, stdin):
        self.cwd = os.path.abspath(cwd or os.getcwd())
        self.env = dict(os.environ if env is None else env)
        self.stdin = stdin
        self.out = bytearray()
        self.err = bytearray()
        self._root = None

    def read_stdin(self):
        """표준 입력 전부. 필요한 명령(--stdin)만 부른다 — 늘 읽으면
        입력이 닫히지 않은 파이프에서 부를 때 멈춘다."""
        if self.stdin is None:
            self.stdin = sys.stdin.buffer.read()
        return self.stdin

    def say(self, text):
        if isinstance(text, str):
            text = text.encode('utf-8')
        self.out += text

    def warn(self, text):
        if isinstance(text, str):
            text = text.encode('utf-8')
        self.err += text

    def root(self):
        """작업 트리의 뿌리 — .git 을 품은 디렉터리(SPEC.md §1.1).

        현재 디렉터리부터 위로 올라가며 .git 을 찾는다.
        GIT_CEILING_DIRECTORIES 에 적힌 디렉터리 안으로는 올라가지
        않는다 — 현재 디렉터리 자신은 언제나 본다. O(깊이).
        """
        if self._root:
            return self._root
        spec = self.env.get('GIT_CEILING_DIRECTORIES', '')
        ceil = set(os.path.abspath(p) for p in spec.split(':') if p)
        d = self.cwd
        while True:
            if os.path.isdir(os.path.join(d, '.git')):
                self._root = d
                return d
            up = os.path.dirname(d)
            if up == d or up in ceil:
                raise GitError(NOT_A_REPO)
            d = up

    def gitdir(self):
        return os.path.join(self.root(), '.git')

    def path(self, name):
        """명령줄의 경로 → 절대 경로(현재 디렉터리 기준)."""
        return os.path.join(self.cwd, name)


def resolve(ctx, name):
    """<rev> → 객체 이름. 없으면 None (SPEC.md §6.2).

    3단계에서는 16진 이름과 앞부분만 푼다. 참조와 뒤붙이(~ ^)는
    5단계의 refs.rev_parse 가 맡는다.
    """
    return objects.find_object(ctx.gitdir(), name)


def parse_flags(args, flags, valued=()):
    """(켜진 짧은 옵션 집합, 값 옵션 사전, 나머지 인자).

    모르는 옵션은 SPEC.md §1.4 의 "unknown option" 오류다. '--' 뒤는
    전부 인자로 본다.
    """
    on, vals, rest = set(), {}, []
    it = iter(args)
    for a in it:
        if a == '--':
            rest.extend(it)
            break
        if a in valued:
            try:
                vals[a] = next(it)
            except StopIteration:
                raise GitError("fatal: mygit: option '%s' needs a value"
                               % a)
        elif a in flags:
            on.add(a)
        elif a.startswith('-') and a != '-':
            raise GitError("fatal: mygit: unknown option '%s'" % a)
        else:
            rest.append(a)
    return on, vals, rest


# ── 3단계: hash-object · cat-file ──────────────────────────────────
@command('hash-object')
def cmd_hash_object(ctx, args):
    on, vals, rest = parse_flags(args, ('-w', '--stdin'), ('-t',))
    type_ = vals.get('-t', 'blob')
    if type_ not in objects.TYPES:
        raise GitError("fatal: mygit: unknown object type '%s'" % type_)
    if '--stdin' in on:
        bodies = [ctx.read_stdin()]
    else:
        bodies = []
        for name in rest:
            try:
                with open(ctx.path(name), 'rb') as f:
                    bodies.append(f.read())
            except OSError as e:
                raise GitError("fatal: could not open '%s' for reading:"
                               ' %s' % (name, e.strerror))
    for body in bodies:
        if '-w' in on:
            oid = objects.write_object(ctx.gitdir(), type_, body)
        else:
            oid = objects.hash_object(type_, body)
        ctx.say(oid + '\n')
    return 0


def pretty(ctx, type_, body):
    """cat-file -p 의 몸. blob·commit·tag 는 그대로, 트리는 항목마다
    "%06o 형식 이름\t경로" (SPEC.md §9, 경로 따옴표는 §8.2)."""
    if type_ != 'tree':
        return body
    rows = []
    for mode, name, oid in tree.parse_tree(body):
        rows.append('%06o %s %s\t%s\n'
                    % (int(mode, 8), tree.type_of_mode(mode), oid,
                       worktree.quote_path(name)))
    return ''.join(rows)


@command('cat-file')
def cmd_cat_file(ctx, args):
    on, _vals, rest = parse_flags(args, ('-t', '-s', '-p'))
    if len(on) != 1 or len(rest) != 1:
        raise GitError('usage: mygit cat-file (-t | -s | -p) <object>',
                       129)
    oid = resolve(ctx, rest[0])
    if oid is None:
        raise GitError('fatal: Not a valid object name %s' % rest[0])
    type_, body = objects.read_object(ctx.gitdir(), oid)
    if '-t' in on:
        ctx.say(type_ + '\n')
    elif '-s' in on:
        ctx.say('%d\n' % len(body))
    else:
        ctx.say(pretty(ctx, type_, body))
    return 0


# ── 틀 ─────────────────────────────────────────────────────────────
def run(args, cwd=None, env=None, stdin=b''):
    """명령 하나를 돌린다 → (종료 코드, 표준 출력, 표준 오류)."""
    ctx = Ctx(cwd, env, stdin)
    if not args:
        ctx.warn('usage: mygit <command> [<args>]\n')
        return 129, bytes(ctx.out), bytes(ctx.err)
    fn = COMMANDS.get(args[0])
    if fn is None:
        ctx.warn("mygit: '%s' is not a mygit command.\n" % args[0])
        return 1, bytes(ctx.out), bytes(ctx.err)
    try:
        code = fn(ctx, args[1:])
    except GitError as e:
        ctx.warn(e.message + '\n')
        code = e.code
    return code, bytes(ctx.out), bytes(ctx.err)


def main():
    code, out, err = run(sys.argv[1:], stdin=None)
    sys.stdout.buffer.write(out)
    sys.stderr.buffer.write(err)
    return code

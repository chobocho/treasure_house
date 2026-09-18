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

from mygit import (GitError, commit, diff, index, objects, refs, tree,
                   walk, worktree)

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
    """<rev> → 객체 이름. 없으면 None (SPEC.md §6.2)."""
    return refs.rev_parse(ctx.gitdir(), name)


AMBIGUOUS = ("fatal: ambiguous argument '%s': unknown revision or path "
             "not in the working tree.\n"
             "Use '--' to separate paths from revisions, like this:\n"
             "'git <command> [<revision>...] -- [<file>...]'")


def ident(ctx, who='COMMITTER'):
    return commit.ident_from_env(ctx.env, who)


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


# ── 5단계: init · commit-tree · branch · tag · reflog ─────────────
CONFIG = ('[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n'
          '\tbare = false\n\tlogallrefupdates = true\n')


@command('init')
def cmd_init(ctx, args):
    """SPEC.md §5.1 — 이미 있으면 아무것도 덮어쓰지 않는다."""
    _on, _v, rest = parse_flags(args, ())
    top = ctx.path(rest[0]) if rest else ctx.cwd
    g = os.path.join(os.path.abspath(top), '.git')
    again = os.path.isdir(g)
    for d in ('objects/pack', 'refs/heads', 'refs/tags'):
        os.makedirs(os.path.join(g, d), exist_ok=True)
    for name, text in (('HEAD', 'ref: refs/heads/main\n'),
                       ('config', CONFIG)):
        p = os.path.join(g, name)
        if not os.path.exists(p):
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
    ctx.say('%s Git repository in %s/\n'
            % ('Reinitialized existing' if again else
               'Initialized empty', g))
    return 0


@command('commit-tree')
def cmd_commit_tree(ctx, args):
    """-p 와 -m 은 몇 번이든, 준 차례대로. 메시지는 원문 그대로 +
    줄바꿈 — 공백 정리는 commit 명령만 한다(SPEC.md §4.4)."""
    tree_, parents, msgs = None, [], []
    it = iter(args)
    for a in it:
        if a in ('-p', '-m'):
            val = next(it, None)
            if val is None:
                raise GitError("fatal: mygit: option '%s' needs a value"
                               % a)
            if a == '-m':
                msgs.append(val)
                continue
            oid = resolve(ctx, val)
            if oid is None:
                raise GitError('fatal: not a valid object name %s'
                               % val)
            parents.append(oid)
        elif a.startswith('-'):
            raise GitError("fatal: mygit: unknown option '%s'" % a)
        else:
            tree_ = a
    if tree_ is None or not msgs:
        raise GitError('usage: mygit commit-tree <tree> '
                       '[-p <parent>]... -m <message>...', 129)
    oid = resolve(ctx, tree_)
    t = refs.peel(ctx.gitdir(), oid, 'tree') if oid else None
    if t is None:
        raise GitError('fatal: not a valid object name %s' % tree_)
    body = commit.serialize_commit(t, parents, ident(ctx, 'AUTHOR'),
                                   ident(ctx), '\n\n'.join(msgs) + '\n')
    ctx.say(objects.write_object(ctx.gitdir(), 'commit', body) + '\n')
    return 0


def list_branches(ctx):
    g = ctx.gitdir()
    cur, head = refs.read_head(g)
    if cur is None and head:
        ctx.say('* (HEAD detached at %s)\n' % head[:7])
    for name, _oid in refs.list_refs(g, 'refs/heads/'):
        mark = '* ' if name == cur else '  '
        ctx.say(mark + name[len('refs/heads/'):] + '\n')
    return 0


@command('branch')
def cmd_branch(ctx, args):
    on, _v, rest = parse_flags(args, ('-d',))
    if '-d' in on:
        return delete_branch(ctx, rest)
    if not rest:
        return list_branches(ctx)
    name = rest[0]
    g = ctx.gitdir()
    if not refs.valid_branch_name(name):
        raise GitError("fatal: '%s' is not a valid branch name" % name)
    if refs.resolve_ref(g, 'refs/heads/' + name):
        raise GitError("fatal: a branch named '%s' already exists"
                       % name)
    start = rest[1] if len(rest) > 1 else 'HEAD'
    oid = resolve(ctx, start)
    oid = refs.peel(g, oid, 'commit') if oid else None
    if oid is None:
        raise GitError("fatal: not a valid object name: '%s'" % start)
    refs.update_ref(g, 'refs/heads/' + name, oid, None,
                    'branch: Created from %s' % start, ident(ctx))
    return 0


def delete_branch(ctx, rest):
    """branch -d — HEAD 에서 닿는 브랜치만 지운다(SPEC.md §9.2)."""
    g = ctx.gitdir()
    cur, head = refs.read_head(g)
    for name in rest:
        ref = 'refs/heads/' + name
        oid = refs.resolve_ref(g, ref)
        if ref == cur:
            raise GitError("error: cannot delete branch '%s' used by "
                           "worktree at '%s'" % (name, ctx.root()), 1)
        if oid is None:
            raise GitError("error: branch '%s' not found." % name, 1)
        if head is None or not walk.is_ancestor(g, oid, head):
            raise GitError("error: the branch '%s' is not fully merged"
                           % name, 1)
        refs.update_ref(g, ref, None, oid, '', '')
        ctx.say('Deleted branch %s (was %s).\n' % (name, oid[:7]))
    return 0


@command('tag')
def cmd_tag(ctx, args):
    on, vals, rest = parse_flags(args, ('-a',), ('-m',))
    g = ctx.gitdir()
    if not rest:
        for name, _oid in refs.list_refs(g, 'refs/tags/'):
            ctx.say(name[len('refs/tags/'):] + '\n')
        return 0
    name = rest[0]
    target = rest[1] if len(rest) > 1 else 'HEAD'
    if refs.read_ref(g, 'refs/tags/' + name):
        raise GitError("fatal: tag '%s' already exists" % name)
    oid = resolve(ctx, target)
    if oid is None:
        raise GitError("fatal: Failed to resolve '%s' as a valid ref."
                       % target)
    if '-a' in on or '-m' in vals:
        type_, _ = objects.read_object(g, oid)
        msg = commit.cleanup_message(vals.get('-m', ''))
        body = commit.serialize_tag(oid, type_, name, ident(ctx), msg)
        oid = objects.write_object(g, 'tag', body)
    # 태그는 reflog 를 남기지 않는다 — logallrefupdates 는 브랜치와
    # HEAD 만 기록한다(git 과 같다)
    path = os.path.join(g, 'refs', 'tags', name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(oid + '\n')
    return 0


def reflog_name(ctx, name):
    """reflog 가 읽을 파일의 참조 이름. HEAD · 브랜치 · refs/…"""
    g = ctx.gitdir()
    for cand in (name, 'refs/heads/' + name):
        if os.path.exists(os.path.join(g, 'logs', cand)):
            return cand
    return None


@command('reflog')
def cmd_reflog(ctx, args):
    """새것부터 '<7글자> <ref>@{n}: <메시지>' (SPEC.md §6.3)."""
    _on, _v, rest = parse_flags(args, ())
    rest = [a for a in rest if a != 'show']
    name = rest[0] if rest else 'HEAD'
    log = reflog_name(ctx, name)
    if log is None:
        if name == 'HEAD':
            return 0
        raise GitError(AMBIGUOUS % name)
    for k, (_o, new, _i, msg) in enumerate(
            reversed(refs.read_reflog(ctx.gitdir(), log))):
        ctx.say('%s %s@{%d}: %s\n' % (new[:7], name, k, msg))
    return 0


# ── 6단계: add · rm --cached · status · write-tree · commit ────────
def rel_path(ctx, spec):
    """명령줄 경로 → 작업 트리 뿌리에서의 경로 바이트('' 은 뿌리)."""
    p = os.path.relpath(ctx.path(spec), ctx.root())
    return b'' if p == '.' else os.fsencode(p).replace(b'\\', b'/')


def under(path, rel):
    return not rel or path == rel or path.startswith(rel + b'/')


@command('add')
def cmd_add(ctx, args):
    """pathspec 아래의 파일을 올리고, 사라진 파일은 뺀다(SPEC.md §9).

    모든 pathspec 을 먼저 검사한다 — 하나라도 맞는 것이 없으면 아무것도
    바꾸지 않고 멈춘다(git 과 같다).
    """
    _on, _v, rest = parse_flags(args, ())
    root, g = ctx.root(), ctx.gitdir()
    ents = index.read_index(g)
    files = worktree.walk_worktree(root)
    plan = []
    for spec in rest:
        rel = rel_path(ctx, spec)
        hit_f = [f for f in files if under(f, rel)]
        hit_i = set(e.path for e in ents if under(e.path, rel))
        if not hit_f and not hit_i:
            raise GitError("fatal: pathspec '%s' did not match any "
                           "files" % spec)
        plan.append((hit_f, hit_i))
    by_path = {}
    for e in ents:
        by_path.setdefault(e.path, []).append(e)
    for hit_f, hit_i in plan:
        for f in hit_f:
            full = os.path.join(os.fsencode(root), f)
            with open(full, 'rb') as fh:
                oid = objects.write_object(g, 'blob', fh.read())
            by_path[f] = [index.entry_from_stat(f, full, oid)]
        for p in hit_i - set(hit_f):
            by_path.pop(p, None)
    index.write_index(g, [e for es in by_path.values() for e in es])
    return 0


@command('rm')
def cmd_rm(ctx, args):
    on, _v, rest = parse_flags(args, ('--cached',))
    if '--cached' not in on:
        raise GitError('fatal: mygit: only rm --cached is supported')
    g = ctx.gitdir()
    ents = index.read_index(g)
    have = set(e.path for e in ents)
    gone = set()
    for spec in rest:
        rel = rel_path(ctx, spec)
        if rel not in have:
            raise GitError("fatal: pathspec '%s' did not match any "
                           "files" % spec)
        gone.add(rel)
    for p in sorted(gone):
        ctx.say("rm '%s'\n" % p.decode('utf-8', 'surrogateescape'))
    index.write_index(g, [e for e in ents if e.path not in gone])
    return 0


@command('status')
def cmd_status(ctx, args):
    parse_flags(args, ('--porcelain', '-s', '--short'))
    for row in worktree.status(ctx.root(), ctx.gitdir()):
        ctx.say(row + '\n')
    return 0


def index_tree(ctx):
    """인덱스(단계 0) → 트리 이름. 충돌 경로가 있으면 쓸 수 없다."""
    ents = index.read_index(ctx.gitdir())
    if any(e.stage for e in ents):
        raise GitError('error: Committing is not possible because you '
                       'have unmerged files.\n'
                       'fatal: Exiting because of an unresolved '
                       'conflict.')
    return tree.write_tree(ctx.gitdir(), [('%o' % e.mode, e.oid, e.path)
                                          for e in ents])


@command('write-tree')
def cmd_write_tree(ctx, args):
    parse_flags(args, ())
    ctx.say(index_tree(ctx) + '\n')
    return 0


@command('commit')
def cmd_commit(ctx, args):
    """트리를 쓰고, 커밋하고, 브랜치를 옮긴다(SPEC.md §9 · §6.3).

    부모는 HEAD 와, 머지를 마무리하는 중이면 MERGE_HEAD. 출력은
    git 의 요약 첫 줄만 — Author 줄과 변경 통계는 줄임이다.
    """
    msgs = []
    it = iter(args)
    for a in it:
        if a == '-m':
            msgs.append(next(it, ''))
        else:
            raise GitError("fatal: mygit: unknown option '%s'" % a)
    g = ctx.gitdir()
    branch, head = refs.read_head(g)
    merge_head = refs.resolve_ref(g, 'MERGE_HEAD')
    t = index_tree(ctx)
    if head and not merge_head and \
            refs.peel(g, head, 'tree') == t:
        ctx.say('nothing to commit\n')
        return 1
    msg = commit.cleanup_message('\n\n'.join(msgs))
    if not msg:
        raise GitError('Aborting commit due to empty commit message.',
                       1)
    parents = [p for p in (head, merge_head) if p]
    body = commit.serialize_commit(t, parents, ident(ctx, 'AUTHOR'),
                                   ident(ctx), msg)
    oid = objects.write_object(g, 'commit', body)
    subj = commit.subject_of(msg)
    kind = 'commit (initial)' if not head else \
        'commit (merge)' if merge_head else 'commit'
    refs.update_ref(g, branch or 'HEAD', oid, head,
                    '%s: %s' % (kind, subj), ident(ctx))
    for f in ('MERGE_HEAD', 'MERGE_MSG'):
        p = os.path.join(g, f)
        if os.path.exists(p):
            os.remove(p)
    where = branch[len('refs/heads/'):] if branch else 'detached HEAD'
    ctx.say('[%s%s %s] %s\n' % (where, '' if head else ' (root-commit)',
                                 oid[:7], subj))
    return 0


# ── 7단계: log · merge-base ─────────────────────────────────────────
def log_entry(ctx, oid, oneline):
    """커밋 하나를 git log 의 꼴로(SPEC.md §9.1)."""
    _t, body = objects.read_object(ctx.gitdir(), oid)
    c = commit.parse_commit(body)
    if oneline:
        return '%s %s\n' % (oid[:7], commit.subject_of(c['message']))
    name, mail, secs, tz = commit.parse_ident(c['author'])
    rows = ['commit ' + oid]
    if len(c['parents']) > 1:
        rows.append('Merge: ' + ' '.join(p[:7] for p in c['parents']))
    rows += ['Author: %s <%s>' % (name, mail),
             'Date:   ' + commit.format_date(secs, tz), '']
    msg = c['message'][:-1] if c['message'].endswith('\n') \
        else c['message']
    rows += ['    ' + line for line in msg.split('\n')]
    return '\n'.join(rows) + '\n'


@command('log')
def cmd_log(ctx, args):
    on, vals, rest = parse_flags(args, ('--oneline',), ('-n',))
    g = ctx.gitdir()
    if rest:
        start = resolve(ctx, rest[0])
        start = refs.peel(g, start, 'commit') if start else None
        if start is None:
            raise GitError(AMBIGUOUS % rest[0])
    else:
        branch, start = refs.read_head(g)
        if start is None:
            raise GitError("fatal: your current branch '%s' does not "
                           "have any commits yet"
                           % branch[len('refs/heads/'):])
    order = walk.walk_log(g, [start])
    if '-n' in vals:
        order = order[:int(vals['-n'])]
    oneline = '--oneline' in on
    ctx.say(('' if oneline else '\n').join(
        log_entry(ctx, oid, oneline) for oid in order))
    return 0


@command('merge-base')
def cmd_merge_base(ctx, args):
    on, _v, rest = parse_flags(args, ('--all',))
    if len(rest) != 2:
        raise GitError('usage: mygit merge-base [--all] <a> <b>', 129)
    g = ctx.gitdir()
    ids = []
    for name in rest:
        oid = resolve(ctx, name)
        oid = refs.peel(g, oid, 'commit') if oid else None
        if oid is None:
            raise GitError('fatal: Not a valid object name %s' % name)
        ids.append(oid)
    best = walk.merge_bases(g, ids[0], ids[1])
    if not best:
        return 1
    for oid in (best if '--all' in on else best[:1]):
        ctx.say(oid + '\n')
    return 0


# ── 8단계: diff ─────────────────────────────────────────────────────
def _disk_side(path):
    """(모드, 이름, 바이트) — 디스크의 파일에서. 없으면 None."""
    if not os.path.isfile(path):
        return None
    with open(path, 'rb') as f:
        data = f.read()
    mode = 0o100755 if os.stat(path).st_mode & 0o100 else 0o100644
    return mode, objects.hash_object('blob', data), data


def _tree_map(ctx, rev):
    """<rev> 의 트리를 펼쳐 {경로: (모드, 이름)}."""
    g = ctx.gitdir()
    oid = resolve(ctx, rev)
    t = refs.peel(g, oid, 'tree') if oid else None
    if t is None:
        raise GitError(AMBIGUOUS % rev)
    return {p: (int(m, 8), o) for m, o, p in tree.flatten_tree(g, t)}


@command('diff')
def cmd_diff(ctx, args):
    """SPEC.md §11.5 의 네 꼴. --no-index 만 다르면 1 로 끝난다."""
    on, _v, rest = parse_flags(args, ('--cached', '--no-index'))
    if '--no-index' in on:
        if len(rest) != 2:
            raise GitError('usage: mygit diff --no-index <a> <b>', 129)
        old, new = (_disk_side(ctx.path(p)) for p in rest)
        text = diff.file_diff(os.fsencode(rest[0]),
                              os.fsencode(rest[1]), old, new)
        ctx.say(text)
        return 1 if text else 0
    g = ctx.gitdir()
    root = os.fsencode(ctx.root())
    pairs = []              # (경로, 옛 쪽, 새 쪽) — 바이트는 나중에
    if len(rest) == 2:
        a, b = _tree_map(ctx, rest[0]), _tree_map(ctx, rest[1])
        for p in sorted(set(a) | set(b)):
            pairs.append((p, a.get(p), b.get(p)))
    elif '--cached' in on:
        _br, head = refs.read_head(g)
        a = _tree_map(ctx, head) if head else {}
        b = {e.path: (e.mode, e.oid) for e in index.read_index(g)
             if e.stage == 0}
        for p in sorted(set(a) | set(b)):
            pairs.append((p, a.get(p), b.get(p)))
    elif not rest:
        unmerged = set(e.path for e in index.read_index(g) if e.stage)
        for e in index.read_index(g):
            if e.stage or e.path in unmerged:
                continue          # 충돌 경로는 건너뛴다(줄임)
            new = _disk_side(os.path.join(root, e.path))
            pairs.append((e.path, (e.mode, e.oid),
                          new[:2] if new else None))
    else:
        raise GitError(AMBIGUOUS % rest[0])
    for p, old, new in pairs:
        if old == new:
            continue
        o = diff.blob_side(g, *old) if old else None
        if new and len(rest) == 0 and '--cached' not in on:
            n = _disk_side(os.path.join(root, p))
        else:
            n = diff.blob_side(g, *new) if new else None
        ctx.say(diff.file_diff(p, p, o, n))
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

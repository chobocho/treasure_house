# -*- coding: utf-8 -*-
"""collab — 원격과 협업(12부).

bare 저장소 hub 를 두고 alice 와 bob 이 각자 복제본에서 일한다.

  · 먼저 push 한 사람이 이긴다 — 늦은 쪽의 거절, 그리고 pull 의 세
    방식(merge · rebase · ff-only).
  · --force-with-lease — 내가 마지막으로 본 값일 때만 덮어쓰기.
  · refspec · fetch --prune · remote show.
  · 태그 push, 포크(upstream 과 origin 두 원격).
  · 메일로 주고받는 패치 — format-patch 와 am, Signed-off-by.
  · request-pull, describe.
"""
from exps.util import commit, tick


def people(ctx, hub):
    """hub(bare) 와 그것을 복제한 alice · bob."""
    seed = ctx.repo(hub + '_seed')
    commit(seed, 0, 'base', {'app.txt': 'a\nb\nc\n'})
    h = ctx.repo(hub, init=False)
    h.sh('git clone -q --bare ../%s_seed .' % hub)
    out = []
    for who in ('alice', 'bob'):
        r = ctx.repo('%s_%s' % (hub, who), init=False)
        r.sh('git clone -q ../%s .' % hub)
        r.env['GIT_AUTHOR_NAME'] = r.env['GIT_COMMITTER_NAME'] = who
        r.env['GIT_AUTHOR_EMAIL'] = r.env['GIT_COMMITTER_EMAIL'] = \
            '%s@example.com' % who
        out.append(r)
    return h, out[0], out[1]


def race(ctx):
    h, a, b = people(ctx, 'hub')
    commit(a, 1, 'alice: top', {'app.txt': 'A\nb\nc\n'})
    commit(b, 2, 'bob: bottom', {'app.txt': 'a\nb\nC\n'})
    a.cap('git push -q origin main 2>&1 && git log --oneline')
    b.cap('git push origin main 2>&1', ok=None)
    b.cap('git status -sb', label='hub_bob.before')
    # pull 의 세 방식 — 같은 상태에서 각각
    b.sh('git branch keep')
    tick(b, 3)
    b.cap('git -c pull.rebase=false pull -q --no-edit origin main && '
          'git log --oneline --graph', label='hub_bob.merge')
    b.sh('git reset -q --hard keep')
    b.cap('git pull -q --rebase origin main && git log --oneline --graph',
          label='hub_bob.rebase')
    b.sh('git reset -q --hard keep')
    b.cap('git -c pull.ff=only pull origin main 2>&1', ok=None,
          label='hub_bob.ffonly')
    b.sh('git reset -q --hard keep')
    b.cap('git pull origin main 2>&1 | head -12', ok=None,
          label='hub_bob.default')


def lease(ctx):
    h, a, b = people(ctx, 'lease')
    commit(a, 1, 'alice 1', {'a.txt': '1\n'})
    a.sh('git push -q origin main')
    b.sh('git pull -q origin main')
    # alice 가 자기 커밋을 고쳐 강제로 올린다 — hub 는 그녀가 본 그대로
    tick(a, 2)
    a.sh('git commit -q --amend -m "alice 1 (fixed)"')
    a.cap('git push --force-with-lease origin main 2>&1 | tail -1')
    # bob 은 그 사이에 fetch 하지 않고 자기 역사를 고쳐 강제로 올리려 한다
    tick(b, 3)
    commit(b, 3, 'bob 2', {'b.txt': '2\n'})
    b.cap('git push --force-with-lease origin main 2>&1', ok=None)
    b.cap('git fetch -q && git log --oneline -1 origin/main')


def refspecs(ctx):
    h, a, b = people(ctx, 'refs3')
    a.sh('git switch -q -c feat && git push -q -u origin feat && '
         'git switch -q main')
    b.cap('git config --get remote.origin.fetch')
    b.cap('git fetch -q && git branch -r')
    a.sh('git push -q origin --delete feat')
    b.cap('git fetch -q && git branch -r', label='refs3_bob.stale')
    b.cap('git fetch --prune 2>&1 && git branch -r',
          label='refs3_bob.pruned')
    b.cap("git fetch -q origin 'refs/heads/*:refs/remotes/mirror/*' && "
          "git branch -r", label='refs3_bob.custom')
    b.cap('git remote show origin')


def tags(ctx):
    h, a, b = people(ctx, 'tagpush')
    tick(a, 1)
    a.sh('git tag -a v1.0 -m "release 1.0" && git tag light')
    a.cap('git push origin main 2>&1 | tail -1; git ls-remote --tags origin')
    a.cap('git push -q --follow-tags origin main && '
          'git ls-remote --tags origin', label='tagpush_alice.follow')
    a.cap('git push -q origin light && git ls-remote --tags origin',
          label='tagpush_alice.light')
    a.cap('git describe --tags')
    commit(a, 2, 'after', {'n.txt': 'n\n'})
    a.cap('git describe', label='tagpush_alice.after')


def fork(ctx):
    h, a, b = people(ctx, 'upst')
    f = ctx.repo('upst_fork', init=False)
    f.sh('git clone -q --bare ../upst .')
    c = ctx.repo('upst_contrib', init=False)
    c.sh('git clone -q ../upst_fork . && '
         'git remote add upstream ../upst')
    c.cap('git remote -v')
    commit(a, 5, 'upstream moves on', {'u.txt': 'u\n'})
    a.sh('git push -q origin main')
    c.sh('git switch -q -c topic')
    commit(c, 6, 'my topic', {'t.txt': 't\n'})
    c.cap('git fetch -q upstream && git rebase -q upstream/main && '
          'git log --oneline')
    c.cap('git push -q origin topic && git ls-remote origin topic')
    c.cap('git request-pull upstream/main ../upst_fork topic | head -12')


def patches(ctx):
    h, a, b = people(ctx, 'mail')
    commit(a, 1, 'fix typo in app', {'app.txt': 'a\nb\nc\nd\n'})
    tick(a, 1)
    a.sh('git commit -q --amend -s --no-edit')
    a.cap('git log -1 --format=%B')
    a.cap('git format-patch -1 -o ../mail-out && '
          'ls ../mail-out')
    a.cap('sed -n "1,12p" ../mail-out/0001-fix-typo-in-app.patch')
    tick(b, 2)
    b.cap('git am -q ../mail-out/0001-fix-typo-in-app.patch && '
          'git log -1 --format="%an / %cn — %s"')
    b.cap('git interpret-trailers --parse < ../mail-out/'
          '0001-fix-typo-in-app.patch | head -3')


def run(ctx):
    race(ctx)
    lease(ctx)
    refspecs(ctx)
    tags(ctx)
    fork(ctx)
    patches(ctx)

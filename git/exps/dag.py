# -*- coding: utf-8 -*-
"""dag — 커밋 그래프와 merge-base (7·9부).

main 과 side 가 서로를 두 번 합친 criss-cross 역사를 만든다. 가장
좋은 공통 조상이 둘이 되는 모양이다. log --graph 는 캡처로만 싣는다
(손으로 그린 ASCII 그래프는 금지 — PLAN.md §0.8).
"""
from exps.util import commit, tick


def run(ctx):
    r = ctx.repo('dag')
    commit(r, 0, 'A', {'f': 'A\n'})
    commit(r, 1, 'B', {'f': 'B\n'})
    r.sh('git branch side HEAD~1')
    commit(r, 2, 'C', {'g': 'C\n'})
    r.sh('git switch -q side')
    commit(r, 3, 'D', {'h': 'D\n'})
    # 서로를 한 번씩 합친다 — 공통 조상이 둘(B 와 D)
    tick(r, 4)
    r.sh('git merge -q --no-edit main')          # E = D + C
    r.sh('git switch -q main')
    tick(r, 5)
    r.sh('git merge -q --no-edit side~1')        # F = C + D
    commit(r, 6, 'G', {'g': 'G\n'})
    r.sh('git switch -q side')
    commit(r, 7, 'H', {'h': 'H\n'})
    r.sh('git switch -q main')
    r.cap('git log --graph --oneline --all')
    r.cap('git log --all --format="%h %p %s"')   # 도해 dag 의 원료
    r.cap('git merge-base main side')
    r.cap('git merge-base --all main side')
    # 덱 데모(merge-base 고르기)의 둘째 정답 — B(2c14ef0) 와 D(2e14562)
    r.cap('git merge-base 2c14ef0 2e14562 | xargs git log -1 --format="%h %s"')
    r.cap('git log --oneline $(git merge-base --all main side)',
          label='dag.bases')
    r.cap('git rev-list --count main')
    r.cap('git rev-list --count main..side')
    r.cap('git log --oneline --first-parent main')
    r.cap('git log --oneline --ancestry-path HEAD~2..main')
    r.cap('git log --oneline main..side')
    r.cap('git log --oneline main...side')
    r.cap('git log --oneline --topo-order main')
    r.cap('git log --oneline --date-order main')
    r.cap('git merge-base --is-ancestor HEAD~2 main; echo $?')

# -*- coding: utf-8 -*-
"""fetch_docs.py — git 공식 문서를 docs/ 로 받는다 (make docs).

    python3 tools/fetch_docs.py

출처는 mirror/git.git 의 **v2.55.0 태그**다(PLAN.md §2 — 이 기계의
git 과 같은 판). 태그에 박힌 문서라서 "언제 받았느냐" 에 따라 내용이
바뀌지 않는다. mirror 는 blob 없는 부분 복제이므로 Documentation 의
blob 만 id 로 한 번에 받아 온 뒤 읽는다(git 이 하나씩 받으러 가면
수백 번 왕복한다).

이름 붙이는 법 — <!--CITE key=…--> 의 키가 곧 파일 이름이다:
  Documentation/gitformat-pack.adoc      → docs/gitformat-pack.txt
  Documentation/technical/reftable.adoc  → docs/technical-reftable.txt
  Documentation/RelNotes/2.23.0.adoc     → docs/relnotes-2.23.0.txt
  Documentation/git-merge.adoc           → docs/git-merge.txt
내용은 tools/adoc_text.py 로 절 제목을 `§<TAB>제목` 꼴로 바꾼 것이다.
docs/ 는 커밋하지 않는 캐시다(.gitignore). O(문서 수).
"""
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import adoc_text                                       # noqa: E402

MIRROR = os.path.join(BASE, 'mirror', 'git.git')
DOCS = os.path.join(BASE, 'docs')
TAG = 'v2.55.0'

# 역사 장이 인용하는 메일. lore.kernel.org 는 봇 확인 화면으로 막혀
# 있어(2026-09-18) MARC 의 mbox 꼴을 받는다 — 머리(Date·Message-Id)가
# 그대로 남아 날짜를 원문에서 읽을 수 있다. (키, 목록, MARC 번호)
MAILS = [
    ('kernel-scm-saga', 'linux-kernel', '111280216717070'),
    ('meet-new-maintainer', 'git', '112243466603239'),
    ('announce-1.0.0', 'git', '113515203321888'),
]
UA = 'Mozilla/5.0 (treasure_house git deck; research)'


def git(*args, stdin=None, lazy=True):
    """mirror 에서 git 한 번. lazy=False 면 없는 blob 을 받으러 가지
    않는다(GIT_NO_LAZY_FETCH) — 있는지 셀 때 하나씩 받으면 안 된다."""
    env = dict(os.environ)
    if not lazy:
        env['GIT_NO_LAZY_FETCH'] = '1'
    return subprocess.run(('git', '-C', MIRROR) + args, input=stdin,
                          env=env, stdout=subprocess.PIPE,
                          check=True).stdout


def key_of(path):
    """Documentation/ 아래 경로 → 인용 키."""
    rel = path[len('Documentation/'):-len('.adoc')]
    if rel.startswith('RelNotes/'):
        return 'relnotes-' + rel[len('RelNotes/'):]
    return rel.replace('/', '-')


def main():
    if not os.path.isdir(MIRROR):
        print('  mirror/git.git 이 없다 — make mirror 먼저')
        return 1
    rows = git('ls-tree', '-r', TAG, 'Documentation/').decode()
    items = []
    for line in rows.split('\n'):
        if not line.endswith('.adoc'):
            continue
        meta, path = line.split('\t', 1)
        items.append((meta.split()[2], path))
    missing = git('cat-file', '--batch-check',
                  stdin=''.join(o + '\n' for o, _ in items).encode(),
                  lazy=False)
    need = [l.split()[0] for l in missing.decode().split('\n')
            if l.endswith('missing')]
    for k in range(0, len(need), 200):
        # 부분 복제에서 blob 을 id 로 받는다 — 200개씩 한 번에
        git('fetch', '-q', '--no-tags', 'origin', *need[k:k + 200])
    os.makedirs(DOCS, exist_ok=True)
    for oid, path in items:
        text = git('cat-file', 'blob', oid).decode('utf-8', 'replace')
        with open(os.path.join(DOCS, key_of(path) + '.txt'), 'w',
                  encoding='utf-8', newline='\n') as f:
            f.write(adoc_text.convert(text))
    got = 0
    for key, lst, mid in MAILS:
        path = os.path.join(DOCS, 'mail-%s.txt' % key)
        if os.path.exists(path):
            continue
        url = 'https://marc.info/?l=%s&m=%s&q=mbox' % (lst, mid)
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        data = urllib.request.urlopen(req, timeout=60).read()
        with open(path, 'wb') as f:
            f.write(data)
        got += 1
        time.sleep(1)                      # 남의 서버에 예의를
    print('docs/ — %s 의 문서 %d개 (새로 받은 blob %d개) · 메일 %d통'
          ' (새로 %d)' % (TAG, len(items), len(need), len(MAILS), got))
    return 0


if __name__ == '__main__':
    sys.exit(main())

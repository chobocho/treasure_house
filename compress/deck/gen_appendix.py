# -*- coding: utf-8 -*-
"""부록의 '소스 전문' 부분을 만든다.

    python3 deck/gen_appendix.py > /tmp/x.html

전문 게재를 손으로 적으면 반드시 어딘가 빠진다. 파일이 143개이고
그중 하나라도 빼면 조립기의 커버리지 검사가 오류를 낸다 — 그러니
목록을 손으로 관리할 이유가 없다. 디렉터리를 훑어서 만든다.

여기서 내는 것은 <!--FULLSRC--> 지시자뿐이다. 실제로 자르고 채우는
일은 조립기(build_deck.py + chunks.py)가 한다.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

# (언어 이름, 디렉터리, 확장자, 접두어) — 부록의 절 순서다.
GROUPS = [
    ('파이썬 — 참조 구현', 'src/py/compresslib', ('.py',), 'py'),
    ('C++', 'src/cpp', ('.h',), 'cpp'),
    ('Go', 'src/go', ('.go',), 'go'),
    ('TypeScript', 'src/ts', ('.ts',), 'ts'),
    ('자바', 'src/java/compresslib', ('.java',), 'java'),
    ('명령줄 도구 다섯', 'cli',
     ('.py', '.go', '.cpp', '.java', '.ts'), 'cli'),
    ('코퍼스·벤치·상호운용', None, ('.py',), 'ev'),
    ('빌드와 도구', 'EXTRA', (), 'bt'),
]

# 디렉터리로 안 잡히는 것들. 이 목록이 비면 pending.txt 도 빈다.
EXTRA = ['Makefile', 'go.mod', 'src/py/compresslib/__init__.py',
         'tools/flock_java.sh', 'tools/gen_tables.py',
         'tools/record.sh', 'tools/render_figs.sh',
         'tools/rewrap.py', 'tools/width.py']

# 마지막 무리는 디렉터리가 여럿이라 따로 적는다.
EVIDENCE_DIRS = ['corpus', 'bench', 'interop']

SKIP = ('_test.go', '.test.ts', 'RunTests.java', '__init__.py')


def files_in(d, exts):
    out = []
    for root, dirs, names in os.walk(os.path.join(BASE, d)):
        dirs[:] = [x for x in dirs
                   if x not in ('node_modules', '__pycache__', 'tests')]
        for n in sorted(names):
            if n.endswith(exts) and not n.endswith(SKIP):
                rel = os.path.relpath(os.path.join(root, n), BASE)
                out.append(rel.replace(os.sep, '/'))
    return sorted(out)


def main():
    parts = []
    n_files = 0
    n_lines = 0
    for title, d, exts, prefix in GROUPS:
        if d == 'EXTRA':
            paths = EXTRA
        elif d is None:
            paths = []
            for e in EVIDENCE_DIRS:
                paths += files_in(e, exts)
        else:
            paths = files_in(d, exts)
        parts.append(
            '<article class="card" id="ap-%s">\n'
            '<p class="chnum">부록</p>\n<h2>%s</h2>\n'
            '<p class="chsub">파일 %d개 — 한 줄도 빠짐없이</p>\n'
            '</article>'
            % (prefix, title, len(paths)))
        for i, p in enumerate(paths):
            name = os.path.basename(p)
            lines = io.open(os.path.join(BASE, p),
                            encoding='utf-8').read().split('\n')
            if lines and lines[-1] == '':
                lines.pop()
            n_files += 1
            n_lines += len(lines)
            parts.append('<!--FULLSRC file=%s prefix=%s-%d title=%s-->'
                         % (p, prefix, i + 1, name))
    sys.stderr.write('  파일 %d개 · %d줄\n' % (n_files, n_lines))
    print('\n\n'.join(parts))


if __name__ == '__main__':
    main()

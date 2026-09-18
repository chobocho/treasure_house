# -*- coding: utf-8 -*-
"""golden_cases.py — 기준 바이트를 만들 **입력과 명령**만 적은 곳.

   기대값은 한 글자도 여기 없다. tools/make_golden.py 가 이 입력을 진짜
   git 2.55.0 에 넣어 기대값을 받아 golden/ 에 쓴다(SPEC.md §16.2).
   그래서 이 파일을 고치는 것은 "시험 문제를 바꾸는 것" 이고, golden/ 을
   손으로 고치는 일은 없다.

   재료(recipe) 문법은 SPEC.md §2.1 과 §16.4 를 따른다.
"""

# ── §2 SHA-1 시험 벡터 100개 ──────────────────────────────────────
# 경계: 55바이트까지는 덧붙임이 한 블록에 들어가고, 56바이트부터는 한
# 블록이 더 필요하다(0x80 한 바이트 + 길이 8바이트). 64의 배수 언저리를
# 촘촘히 두는 까닭이다.
_REPEAT_61 = [1, 2, 3, 4, 8, 15, 16, 17, 31, 32, 33, 47, 48, 49, 54,
              55, 56, 57, 58, 62, 63, 64, 65, 66, 100, 111, 112, 113,
              119, 120, 121, 127, 128, 129, 191, 192, 193, 255, 256,
              257, 511, 512, 513, 1000, 1023, 1024, 1025, 2000, 4096,
              8191, 8192, 8193, 10000]
_COUNTER = [1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 55, 56, 63, 64, 65,
            251, 252, 4095, 4096, 4097, 65535, 65536, 65537, 100000,
            1048576]

SHA1_VECTORS = (
    [('empty', 'empty'),
     ('abc', 'text:abc'),
     ('hello-nl', 'text:hello\\n'),
     ('fips-448', 'text:abcdbcdecdefdefgefghfghighijhijkijkl'
                  'jklmklmnlmnomnopnopq'),
     ('fox-dog', 'text:The quick brown fox jumps over the lazy dog'),
     ('fox-cog', 'text:The quick brown fox jumps over the lazy cog'),
     ('hangul', 'text:한글\\n'),
     ('git-nl', 'text:git\\n'),
     # 객체 머리를 붙인 바이트 그대로 — 이 SHA-1 이 곧 객체 이름
     ('blob-hello-raw', 'text:blob 6\\x00hello\\n'),
     ('tree-empty-raw', 'text:tree 0\\x00')]
    + [('a-%d' % n, 'repeat:61:%d' % n) for n in _REPEAT_61]
    + [('zero-%d' % n, 'repeat:00:%d' % n) for n in (1, 55, 56, 64, 65)]
    + [('ff-%d' % n, 'repeat:ff:%d' % n)
       for n in (1, 55, 56, 64, 65, 1000)]
    + [('counter-%d' % n, 'counter:%d' % n) for n in _COUNTER])

# ── §4.3 트리 12개 ─────────────────────────────────────────────────
# (이름, [(경로, 재료, 모드)]). 모드는 644 또는 755.
TREE_CASES = [
    ('one-file', [('a.txt', 'text:a\\n', 644)]),
    ('two-files', [('b', 'text:b\\n', 644), ('a', 'text:a\\n', 644)]),
    ('exec-bit', [('run.sh', 'text:#!/bin/sh\\n', 755),
                  ('data', 'text:x\\n', 644)]),
    ('nested', [('src/main.c', 'text:int main(void){return 0;}\\n',
                 644),
                ('README', 'text:hi\\n', 644)]),
    ('deep', [('a/b/c/d/e.txt', 'text:deep\\n', 644)]),
    # 3부·부록 A 4단계의 함정 — 디렉터리 a 는 "a/" 로 비교된다
    ('sort-trap', [('a-b', 'text:1\\n', 644), ('a.b', 'text:2\\n', 644),
                   ('a/x', 'text:3\\n', 644), ('a=b', 'text:4\\n', 644),
                   ('ab', 'text:5\\n', 644)]),
    ('prefix-trap', [('foo', 'text:f\\n', 644),
                     ('foo.txt', 'text:t\\n', 644),
                     ('foo-bar/x', 'text:x\\n', 644),
                     ('foo0', 'text:0\\n', 644)]),
    ('empty-file', [('empty', 'empty', 644),
                    ('full', 'text:x\\n', 644)]),
    ('many', [('f%02d' % i, 'text:%d\\n' % i, 644) for i in range(20)]),
    ('hangul', [('한글.txt', 'text:가\\n', 644),
                ('영어.md', 'text:e\\n', 644)]),
    ('space-name', [('with space', 'text:s\\n', 644),
                    ('tab\tname', 'text:t\\n', 644)]),
    ('only-subdir', [('d/e/f', 'text:f\\n', 644),
                     ('d/g', 'text:g\\n', 644)]),
]

# ── §16.4 장면들 ───────────────────────────────────────────────────
# 명령만 적는다. 기대 출력(> ! =)은 make_golden.py 가 git 으로 채운다.
SCENARIOS = {}

# 5단계 — init · 커밋 · log · 참조 · 태그 · reflog
SCENARIOS['hello'] = r'''
mygit init
write hello.txt text:hello\n
write run.sh text:#!/bin/sh\necho\x20hi\n
chmod run.sh 755
mkdir src
write src/a.py text:print(1)\n
mygit add .
mygit commit -m first
@date 1700000060
append hello.txt text:world\n
mygit add hello.txt
mygit commit -m "second\n\nbody line"
mygit log
mygit log --oneline
mygit cat-file -t HEAD
mygit cat-file -s HEAD
mygit cat-file -p HEAD
mygit cat-file -p HEAD^{tree}
mygit branch
mygit branch topic HEAD~1
mygit branch
mygit tag v0.1 HEAD~1
@date 1700000120
mygit tag -a v1.0 -m "release 1.0"
mygit tag
mygit cat-file -p v1.0
mygit log --oneline v0.1
mygit reflog
mygit reflog topic
mygit init
'''

# 5단계 — plumbing 과 메시지 규칙(§4.4)
SCENARIOS['plumbing'] = r'''
mygit init
write a.txt text:plumbing\n
mygit hash-object a.txt
mygit hash-object -w a.txt
mygit add a.txt
mygit write-tree
mygit commit -m "  lead  \n\nx   \n \n\n\ny\n\n"
mygit cat-file -p HEAD
mygit commit-tree HEAD^{tree} -m "  m1  "
mygit commit-tree HEAD^{tree} -p HEAD -m a -m b
ref HEAD
ref HEAD^{tree}
'''

# 6단계 — 인덱스와 status
SCENARIOS['status'] = r'''
mygit init
mygit status
write a text:a\n
write b text:b\n
mkdir d/e
write d/e/f text:f\n
mygit status
mygit add a d
mygit status
stage
mygit commit -m one
mygit status
append a text:more\n
rm b
write c text:c\n
chmod d/e/f 755
mygit status
mygit add .
mygit status
stage
mygit rm --cached c
mygit status
mygit add nope
mygit rm --cached nope
write 한글.txt text:가\n
write "sp ace" text:s\n
mygit status
mygit add .
mygit status
'''

# 8단계 — 세 영역 사이의 diff (SPEC.md §11.5). --no-index 쌍은
# golden/diff/ 가 따로 갖는다.
SCENARIOS['diff'] = r'''
mygit init
write a text:one\ntwo\nthree\n
write b text:keep\n
write gone text:bye\n
mkdir d
write d/x text:x1\n
mygit add .
mygit commit -m one
append a text:four\n
rm gone
write new text:fresh\n
chmod b 755
mygit diff
mygit add .
mygit diff
mygit diff --cached
mygit commit -m two
mygit diff HEAD~1 HEAD
mygit diff HEAD HEAD~1
write 한글.txt text:가\n
write d/x text:x2\n
chmod d/x 755
mygit add .
mygit diff --cached
mygit diff
'''


# 9단계 — switch · checkout · branch 지우기
SCENARIOS['checkout'] = r'''
mygit init
write a text:a1\n
write b text:b1\n
mygit add .
mygit commit -m base
mygit tag t0
mygit branch feat
mygit switch feat
write c text:c1\n
write a text:a2\n
mygit add .
mygit commit -m feat
mygit switch main
cat a
mygit status
append b text:local\n
mygit switch feat
mygit status
cat b
mygit switch main
write a text:mine\n
mygit switch feat
write a text:a1\n
mygit status
write c text:untracked\n
mygit switch feat
rm c
mygit checkout t0
mygit switch main
mygit switch -c new
mygit switch new
mygit switch main
mygit branch -d new
mygit branch -d feat
mygit branch -d main
mygit switch feat~1
mygit switch nope
mygit checkout nope
mygit checkout feat
mygit checkout main
mygit reflog
'''


def _merge(name, base, ours, theirs, extra=''):
    """3-way 합치기 장면 하나. 파일 f 의 세 판을 재료로 받는다.

       base 로 첫 커밋 → 브랜치 t 에서 theirs → main 에서 ours →
       merge t.
       날짜를 1분씩 다르게 둬 커밋 이름이 사건마다 달라지게 한다.
    """
    SCENARIOS['merge-' + name] = r'''
mygit init
write f %s
mygit add f
mygit commit -m base
mygit branch t
mygit switch t
@date 1700000060
write f %s
%s
mygit add .
mygit commit -m theirs
mygit switch main
@date 1700000120
write f %s
mygit add .
mygit commit -m ours
@date 1700000180
mygit merge t
cat f
stage
mygit status
mygit log
''' % (base, theirs, extra, ours)


_B20 = 'seq:1:20'
# 10단계 — golden/merge 의 경우들 (SPEC.md §12)
_merge('clean-far', _B20,
       r'text:1\nTWO\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n'
       r'17\n18\n19\n20\n',
       r'text:1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n'
       r'17\nEIGHTEEN\n19\n20\n')
_merge('conflict', 'text:a\\nb\\nc\\n', 'text:a\\nb2\\nc\\n',
       'text:a\\nB\\nc\\n')
_merge('adjacent', 'text:a\\nb\\nc\\nd\\n', 'text:a\\nB\\nc\\nd\\n',
       'text:a\\nb\\nC\\nd\\n')
_merge('one-apart', 'text:a\\nb\\nc\\nd\\ne\\n',
       'text:a\\nB\\nc\\nd\\ne\\n', 'text:a\\nb\\nc\\nD\\ne\\n')
_merge('identical', _B20,
       r'text:1\nX\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n'
       r'17\n18\n19\n20\n',
       r'text:1\nX\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n'
       r'17\n18\n19\nY\n')
_merge('refine', 'text:a\\nb\\nz\\n', 'text:a\\nq\\nw\\ne\\nz\\n',
       'text:a\\nq\\nr\\ne\\nz\\n')
_merge('join-3', 'text:a\\nb\\nm1\\nm2\\nm3\\nd\\ne\\n',
       'text:a\\n1\\nm1\\nm2\\nm3\\n2\\ne\\n',
       'text:a\\n3\\nm1\\nm2\\nm3\\n4\\ne\\n')
_merge('split-4', 'text:a\\nb\\nm1\\nm2\\nm3\\nm4\\nd\\ne\\n',
       'text:a\\n1\\nm1\\nm2\\nm3\\nm4\\n2\\ne\\n',
       'text:a\\n3\\nm1\\nm2\\nm3\\nm4\\n4\\ne\\n')
# 서로 다른 파일만 바꾼 합치기 — 내용 합치기 없이 트리 규칙만으로 끝난다
_merge('other-file', 'text:a\\n', 'text:a\\nours\\n', 'text:a\\n',
       extra='write g text:theirs\\n')
_merge('add-add', 'text:a\\n', 'text:a\\n', 'text:a\\n',
       extra='write x text:from-t\\n')

# add/add 는 main 쪽에도 x 를 만들어야 한다 — 위 틀에 끼울 자리가 없어
# 장면을 따로 적는다.
SCENARIOS['merge-add-add'] = SCENARIOS['merge-add-add'].replace(
    'write f text:a\\n\nmygit add .\nmygit commit -m ours',
    'write f text:a\\n\nwrite x text:from-main\\n\nmygit add .\n'
    'mygit commit -m ours')

SCENARIOS['merge-ff'] = r'''
mygit init
write f text:a\n
mygit add f
mygit commit -m base
mygit branch t
mygit switch t
@date 1700000060
write g text:g\n
mygit add g
mygit commit -m add-g
mygit switch main
mygit merge t
mygit merge t
mygit log --oneline
mygit reflog
cat .git/ORIG_HEAD
'''

# 충돌을 풀고 커밋하기, 그리고 main 이 아닌 브랜치로 합치기
SCENARIOS['merge-resolve'] = SCENARIOS['merge-conflict'] + r'''
cat .git/MERGE_MSG
cat .git/MERGE_HEAD
write f text:a\nboth\nc\n
mygit add f
mygit status
@date 1700000240
mygit commit -m "merge t by hand"
mygit log --oneline
mygit reflog
'''

# 한쪽만 지운 경로 — B = O 면 T, B = T 면 O, 지운 것도 같다(§12.2)
SCENARIOS['merge-delete'] = r'''
mygit init
write a text:a\n
write b text:b\n
write d text:d\n
mygit add .
mygit commit -m base
mygit branch t
mygit switch t
@date 1700000060
rm d
write c text:c\n
mygit add .
mygit commit -m theirs
mygit switch main
@date 1700000120
rm b
mygit add .
mygit commit -m ours
@date 1700000180
mygit merge t
stage
mygit status
mygit log --oneline
'''
SCENARIOS['merge-into-dev'] = SCENARIOS['merge-other-file'].replace(
    'mygit init\n', 'mygit init\nmygit switch -c dev\n', 1).replace(
    'mygit switch main', 'mygit switch dev')

# 오류 계약(SPEC.md §1.4) — 저장소 r 과 저장소가 아닌 x
SCENARIOS['errors'] = r'''
mkdir r
mkdir x
@cd x
mygit status
@cd r
mygit init
write f text:1\n
mygit add f
mygit commit -m one
mygit cat-file -p nope
mygit merge-base main nope
mygit commit-tree nope -m x
mygit branch x nope
mygit switch nope
mygit checkout nope
mygit tag t nope
mygit merge nope
mygit log nope
mygit diff nope main
mygit reflog nope
mygit add nope
mygit rm --cached nope
mygit hash-object nope
mygit branch main
mygit branch a..b
mygit tag t
mygit tag t
'''

# 12단계 — 멍청한 로컬 복제
SCENARIOS['clone'] = r'''
mkdir src
@cd src
mygit init
write a text:a\n
mygit add a
mygit commit -m one
mygit branch dev
mygit tag v1
@cd .
mygit clone src dst
@cd dst
mygit log --oneline
mygit branch
mygit status
cat .git/config
cat .git/HEAD
cat .git/refs/remotes/origin/HEAD
ref origin/main
ref origin/dev
ref v1
mygit reflog
'''

# ── §11 diff 쌍 30개 ───────────────────────────────────────────────
# (이름, 옛 바이트, 새 바이트). 사람이 실제로 고치는 꼴을 중심으로,
# 덩어리 경계(문맥 3줄·사이 6/7줄)와 끝 줄바꿈·이진·함수 문맥을 섞었다.
_C = (b'#include <stdio.h>\n\nstatic int add(int a, int b)\n{\n'
      b'\treturn a + b;\n}\n\nint main(void)\n{\n\tint x = 1;\n'
      b'\tint y = 2;\n\tprintf("%d\\n", add(x, y));\n\treturn 0;\n}\n')
_PY = (b'import sys\n\n\ndef parse(line):\n    key, _, value = '
       b'line.partition("=")\n    return key.strip(), value.strip()\n'
       b'\n\ndef main():\n    for line in sys.stdin:\n'
       b'        print(parse(line))\n\n\nif __name__ == "__main__":\n'
       b'    main()\n')
_N40 = b''.join(b'line %d\n' % i for i in range(1, 41))
_N200 = b''.join(b'row %03d\n' % i for i in range(1, 201))


def _sub(data, old, new, count=1):
    assert old in data, old
    return data.replace(old, new, count)


def _lines(data, edits):
    """줄 번호(1부터)로 고친다.

    edits = {번호: 새 줄 바이트 또는 None(지움)}.
    """
    out = []
    for i, ln in enumerate(data.split(b'\n')[:-1], 1):
        v = edits.get(i, ln)
        if v is not None:
            out.append(v + b'\n')
    return b''.join(out)


DIFF_PAIRS = [
    ('c-modify', _C, _sub(_C, b'int y = 2;', b'int y = 20;')),
    ('c-insert', _C, _sub(_C, b'\treturn 0;\n', b'\tputs("bye");\n'
                                                 b'\treturn 0;\n')),
    ('c-delete', _C, _sub(_C, b'\tint y = 2;\n', b'')),
    ('c-new-func', _C, _sub(_C, b'int main(void)\n',
                            b'static int sub(int a, int b)\n{\n'
                            b'\treturn a - b;\n}\n\nint main(void)\n')),
    ('py-modify', _PY, _sub(_PY, b'value.strip()',
                            b'value.strip().lower()')),
    ('py-two-hunks', _PY, _sub(_sub(_PY, b'import sys\n',
                                    b'import os\nimport sys\n'),
                               b'    main()\n',
                               b'    sys.exit(main())\n')),
    ('gap-6', _N40, _lines(_N40, {3: b'THREE', 10: b'TEN'})),
    ('gap-7', _N40, _lines(_N40, {3: b'THREE', 11: b'ELEVEN'})),
    ('first-line', _N40, _lines(_N40, {1: b'FIRST'})),
    ('last-line', _N40, _lines(_N40, {40: b'LAST'})),
    ('prepend', _N40, b'new top\n' + _N40),
    ('append', _N40, _N40 + b'new bottom\n'),
    ('from-empty', b'', b'hello\nworld\n'),
    ('to-empty', b'hello\nworld\n', b''),
    ('eol-added', b'a\nb\nc', b'a\nb\nc\n'),
    ('eol-removed', b'a\nb\nc\n', b'a\nb\nc'),
    ('eol-both-missing', b'a\nb\nc', b'a\nB\nc'),
    ('one-line-noeol', b'x', b'y\n'),
    ('whitespace-only', b'a\nb \nc\n', b'a\nb\nc\n'),
    ('crlf', b'a\r\nb\r\nc\r\n', b'a\r\nB\r\nc\r\n'),
    ('hangul', '첫 줄\n둘째 줄\n셋째 줄\n'.encode(),
     '첫 줄\n두 번째 줄\n셋째 줄\n'.encode()),
    ('long-func', b'f' + b'x' * 100 + b'   \n' + b''.join(
        b' %d\n' % i for i in range(10)),
     b'f' + b'x' * 100 + b'   \n' + b''.join(
         (b' Z\n' if i == 8 else b' %d\n' % i) for i in range(10))),
    ('no-func-context',
     b''.join(b' indented %d\n' % i for i in range(12)),
     b''.join((b' changed\n' if i == 9 else b' indented %d\n' % i)
              for i in range(12))),
    ('many-scattered', _N200,
     _lines(_N200, {5: b'A', 50: b'B', 51: None, 120: b'C',
                    199: b'D'})),
    ('block-moved', _N40, _lines(_N40, {i: None for i in range(5, 10)})
     .replace(b'line 30\n', b'line 30\n' + b''.join(
         b'line %d\n' % i for i in range(5, 10)))),
    ('blank-between', b'a\n\nb\n\nc\n', b'a\n\nb\n\nx\n\nc\n'),
    ('dup-slide', b'a\nb\nb\nb\nc\n', b'a\nb\nb\nc\n'),
    ('dup-insert', b'x\n}\n\ny\n}\n', b'x\n}\n\nz\n}\n\ny\n}\n'),
    ('replace-all', b'one\ntwo\nthree\n', b'uno\ndos\ntres\n'),
    ('binary', b'GIF89a\x00\x01\x02', b'GIF89a\x00\x01\x03'),
]

# git 이 같은 길이의 **다른** 스크립트를 고르는 쌍(SPEC.md §11.2 tie).
# 앞방향 Myers 원형과 git 을 무작위로 견주어 찾은 것 가운데 코드처럼
# 보이는 것만 골랐다(2026-09-18). 분류가 맞는지는 8단계 시험이 확인한다.
DIFF_TIE_PAIRS = [
    ('return-dup', b'x = 1\n\n\nprint(x)\n\n    return y\n'
                   b'    return y\n\nif x:\nif x:\n',
     b'x = 1\n\n\nprint(x)\nnew2\n    return y\nif x:\nif x:\n'),
    ('incr-dup', b'    i++;\n    i++;\nint f(void)\n    i++;\n'
                 b'    i++;\n    return 0;\n',
     b'    i++;\n    i++;\n    i++;\nint f(void)\n    i++;\n'
     b'    y = 4;\n    return 0;\n'),
    ('brace-dup', b'    return y\nx = 1\n}\n    return y\n}\n'
                  b'    return y\n',
     b'}\ndef f():\nif x:\nx = 1\n\nprint(x)\ndef f():\nif x:\n'
     b'if x:\nx = 1\n'),
]

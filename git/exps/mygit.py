# -*- coding: utf-8 -*-
"""mygit — 다섯 구현이 같은 대본에서 같은 저장소를 만드는가(부록 A).

대본의 명령을 Python·Go·TypeScript·Java·C++ 의 mygit 으로 각각 새
저장소에서 돌린다. 명령마다 표준 출력·표준 오류·종료 코드를 Python
의 것과 견주고, 끝난 저장소를 진짜 git 으로 연다: fsck --strict 가
깨끗한가, 객체 목록(이름·형식·크기)이 Python 의 저장소와 같은가.

pack-objects 의 출력(팩 이름)만은 견주지 않는다 — 팩 이름은 팩
바이트의 SHA-1 이고, 압축된 바이트는 언어마다 달라도 된다(SPEC.md
§3.1). 그 대신 팩 안의 객체 목록을 git verify-pack 으로 견준다.
"""
import os
import subprocess

from build_deck import gitslug

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(HERE, 'build')
LANGS = [('Python', 'PYTHONPATH=%s/py python3 -m mygit' % HERE),
         ('Go', '%s/mygit-go' % B),
         ('TypeScript', 'node %s/ts/src/main.js' % B),
         ('Java', 'sh %s/tools/flock_java.sh java -cp %s/java '
          'mygit.Main' % (HERE, B)),
         ('C++', '%s/mygit-cpp' % B)]

# (단계, 명령) — {m} 이 그 언어의 mygit. 파일 손질은 셸이 한다.
SCRIPT = [
    (5, '{m} init'),
    (1, '{m} hash-object --stdin < /dev/null'),
    (2, 'printf "hello\\n" > h.txt && {m} hash-object -w h.txt'),
    (3, '{m} cat-file -p ce01362'),
    (6, 'mkdir -p src && printf "int x;\\n" > src/x.c && {m} add .'),
    (6, '{m} status'),
    (6, '{m} commit -m first'),
    (4, '{m} cat-file -p HEAD^{tree}'),
    (5, '{m} branch topic'),
    (5, '{m} tag v1'),
    (9, '{m} switch topic'),
    (6, 'printf "hello\\ntopic\\n" > h.txt && {m} add h.txt'),
    (6, '{m} commit -m topic'),
    (9, '{m} switch main'),
    (6, 'printf "int y;\\n" > src/y.c && {m} add src'),
    (6, '{m} commit -m main'),
    (8, '{m} diff topic main'),
    (10, '{m} merge topic'),
    (7, '{m} log --oneline'),
    (7, '{m} merge-base main topic'),
    (5, '{m} reflog'),
    (11, '{m} pack-objects --delta pk'),
    (12, '{m} clone . ../copy'),
]


def run_lang(ctx, m):
    """한 언어의 대본 — 저장소 이름은 언어와 무관하게 mygit 이다.
    출력에 경로가 찍히므로(init·clone) 이름이 같아야 견줄 수 있다."""
    r = ctx.repo('mygit', init=False)
    r.sh('rm -rf ../mygit-copy')
    outs = []
    for step, cmd in SCRIPT:
        c = cmd.replace('{m}', m).replace('../copy', '../mygit-copy')
        p = subprocess.run(['sh', '-c', c], cwd=r.path, env=r.env,
                           stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        outs.append((step, cmd, p.returncode,
                     r.norm(p.stdout.decode('utf-8', 'replace')),
                     r.norm(p.stderr.decode('utf-8', 'replace'))))
    return r, outs


def facts(r):
    """진짜 git 이 본 저장소 — fsck 결과와 객체 목록."""
    fsck = subprocess.run(['git', 'fsck', '--strict'], cwd=r.path,
                          env=r.env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).returncode
    objs = r.sh('git cat-file --batch-all-objects --batch-check')
    packed = r.sh('for i in pk-*.idx; do git verify-pack -v "$i"; done '
                  '| grep -E "^[0-9a-f]{40} " | cut -d" " -f1 | sort')
    return fsck, objs, packed


def run(ctx):
    subprocess.run(['make', '-s', '-C', HERE, 'build'], check=True,
                   stdout=subprocess.DEVNULL)
    results = {}
    for lang, m in LANGS:
        r, outs = run_lang(ctx, m)
        results[lang] = (outs, facts(r))
    # Python 의 대본 한 벌은 캡처로 남긴다(부록 A 의 따라 하기)
    for step, cmd, code, out, err in results['Python'][0]:
        shown = cmd.replace('{m}', 'mygit').replace('../copy',
                                                    '../mygit-copy')
        text = out + err + ('[exit %d]\n' % code if code else '')
        ctx.save('mygit__%s.txt' % gitslug(shown),
                  '$ %s\n%s' % (shown, text))
    ref_outs, ref_facts = results['Python']
    steps = sorted(set(s for s, _ in SCRIPT))
    rows = []
    for step in steps:
        row = [step]
        for lang, _ in LANGS:
            outs, fx = results[lang]
            same = all(o[2:] == ref_outs[k][2:] or o[1].split()[1:2] ==
                       ['pack-objects']
                       for k, o in enumerate(outs) if o[0] == step)
            ok = same and fx[0] == 0 and fx[1] == ref_facts[1] and \
                fx[2] == ref_facts[2]
            row.append('ok' if ok else '✗')
        rows.append(row)
    ctx.table('parity', ['단계'] + [l for l, _ in LANGS], rows,
              '같은 대본 %d줄 · 출력·fsck·객체 목록을 Python 과 대조'
              % len(SCRIPT))
    bad = [(lang, k, o) for lang, _ in LANGS
           for k, o in enumerate(results[lang][0])
           if o[2:] != ref_outs[k][2:] and 'pack-objects' not in o[1]]
    for lang, k, o in bad:
        print('  ✗ %s 대본 %d번째: %s' % (lang, k, o[1]))
        print('    얻음 %r\n    기대 %r' % (o[2:], ref_outs[k][2:]))

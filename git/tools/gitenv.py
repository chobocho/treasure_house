# -*- coding: utf-8 -*-
"""gitenv.py — tools/gitenv.sh 가 만드는 환경을 파이썬으로 가져온다.

   run_all.py · tools/make_golden.py · tools/spec_examples.py 가
   진짜 git 을 부를 때 쓰는 환경 변수는 전부 gitenv.sh 한 곳에서
   온다. 여기서 같은 값을 다시 적으면 두 곳이 언젠가 어긋난다 —
   그래서 sh 로 그 파일을 읽힌 뒤 `env -0` 으로 결과를 받아 온다.
   시간 O(환경 크기).

       env = gitenv.load('/path/to/scratch')
       out = gitenv.git(env, cwd, 'cat-file', '-p', 'HEAD')
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, 'gitenv.sh')


def load(scratch):
    """gitenv.sh 를 source 한 뒤의 환경 전체를 dict 로."""
    base = dict(os.environ)
    base['GITENV_SCRATCH'] = scratch
    raw = subprocess.run(['sh', '-c', '. "$0" && env -0', SCRIPT],
                         env=base, check=True,
                         stdout=subprocess.PIPE).stdout
    env = {}
    for item in raw.split(b'\0'):
        if b'=' in item:
            k, v = item.split(b'=', 1)
            env[k.decode()] = v.decode()
    return env


def git(env, cwd, *args, stdin=None, check=True):
    """진짜 git 을 한 번 부른다.

    (종료 코드, stdout 바이트, stderr 바이트) 를 돌려준다.
    """
    p = subprocess.run(('git',) + args, cwd=cwd, env=env, input=stdin,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise RuntimeError('git %s → %d\n%s'
                           % (' '.join(args), p.returncode,
                              p.stderr.decode('utf-8', 'replace')))
    return p.returncode, p.stdout, p.stderr

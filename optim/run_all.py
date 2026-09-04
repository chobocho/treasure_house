# -*- coding: utf-8 -*-
"""예제를 전부 실제로 실행해 출력을 out/manifest.json 에 남긴다.

   덱에 실리는 실행 결과는 여기서 나온 것만 쓴다. 손으로 옮겨 적은 출력은
   시간이 지나면 반드시 소스와 어긋나기 때문이다. 하나라도 0 이 아닌 코드로
   끝나면 전체를 실패로 처리한다 — 깨진 예제가 덱에 실리는 일을 막는다.

   사용법:  python3 optim/run_all.py [이름 ...]
"""
import io
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(BASE, 'out')

# 데모 스크립트는 py/demo_*.py 규약을 따른다 — 목록을 손으로 관리하지 않는다.
def discover():
    jobs = []
    for root, dirs, files in os.walk(os.path.join(BASE, 'py')):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in sorted(files):
            if f.startswith('demo_') and f.endswith('.py'):
                rel = os.path.relpath(os.path.join(root, f), BASE)
                jobs.append((f[5:-3], rel))
    return sorted(jobs)


def main(argv):
    want = set(argv)
    jobs = [j for j in discover() if not want or j[0] in want]
    if not jobs:
        print('실행할 데모가 없다.')
        return 1
    os.makedirs(OUTDIR, exist_ok=True)

    mpath = os.path.join(OUTDIR, 'manifest.json')
    manifest = {}
    if os.path.exists(mpath):
        manifest = json.loads(io.open(mpath, encoding='utf-8').read())

    env = dict(os.environ, PYTHONPATH=BASE, PYTHONIOENCODING='utf-8', PYTHONHASHSEED='0')
    bad = 0
    for name, rel in jobs:
        t0 = time.time()
        p = subprocess.run([sys.executable, rel], cwd=BASE, env=env,
                           capture_output=True, text=True)
        dt = time.time() - t0
        if p.returncode != 0:
            bad += 1
            print('  ✘ %-28s exit=%d\n%s' % (name, p.returncode, p.stderr.strip()[:1200]))
            continue
        if p.stderr.strip():
            bad += 1
            print('  ✘ %-28s stderr 있음\n%s' % (name, p.stderr.strip()[:800]))
            continue
        manifest[name] = {'cmd': 'python3 %s' % rel, 'stdout': p.stdout,
                          'sec': round(dt, 2)}
        print('  ✔ %-28s %5.2fs  %d줄' % (name, dt, p.stdout.count('\n')))

    io.open(mpath, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True))
    print('\n%d개 실행, 실패 %d개 → out/manifest.json' % (len(jobs), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

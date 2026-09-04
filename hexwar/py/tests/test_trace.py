# -*- coding: utf-8 -*-
"""골든 트레이스 대조 — 지금 구현이 얼려 둔 트레이스와 한 줄이라도 다르면 실패.
   루아·타입스크립트 포트도 같은 파일을 같은 방식으로 대조한다."""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, 'py'))

from hexwar import main as MAIN            # noqa: E402


def main():
    want = [json.loads(l) for l in
            io.open(os.path.join(BASE, 'golden', 'trace.jsonl'), encoding='utf-8')
            if l.strip()]
    buf = io.StringIO()
    MAIN.run_trace(buf)
    got = [json.loads(l) for l in buf.getvalue().split('\n') if l.strip()]

    if len(got) != len(want):
        print('스텝 수 불일치: %d != %d' % (len(got), len(want)))
        return 1
    bad = 0
    for a, b in zip(got, want):
        for k in sorted(b):
            if a.get(k) != b[k]:
                if bad < 10:
                    print('스텝 %d "%s" 의 %s: %r != %r' % (b['step'], b['ev'], k,
                                                            a.get(k), b[k]))
                bad += 1
    if bad:
        print('FAIL — %d개 필드 불일치' % bad)
        return 1
    print('trace OK — %d스텝 · 프레임 해시 %d개 일치'
          % (len(want), sum(1 for x in want if 'fbHash' in x)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

# -*- coding: utf-8 -*-
"""10부 — 흐름으로 다시 읽기.

go.mod 사다리: 이 기계의 go 1.27.1 이 언어 버전(go 줄)으로 막는 기능마다,
막는 판에서는 컴파일되고 한 판 아래에서는 거절되는지 실제로 본다. 목록은
설치된 go 의 타입 검사기(types2)가 버전을 검사하는 자리에서 골랐다
(scratch/brief/langgates.txt). '막는 판' 은 노트의 판이 아니라 컴파일러가
실제로 요구하는 판이다 — 제네릭 타입 별칭은 노트로는 1.24(1.23 은 실험)
이지만 컴파일러는 go 1.23 에서도 받는다. 그 차이는 표에 적는다.
"""
import re

LADDER = [  # (예제, 컴파일러가 요구하는 판, 한 판 아래, 이름)
    ('alias', '1.9', '1.8', '타입 별칭'),
    ('literals', '1.13', '1.12', '수 리터럴의 _ 와 0b'),
    ('shift', '1.13', '1.12', '부호 있는 이동 횟수'),
    ('overlap', '1.14', '1.13', '겹치는 인터페이스 메서드'),
    ('arrayptr', '1.17', '1.16', '슬라이스 → 배열 포인터'),
    ('generics', '1.18', '1.17', '타입 매개변수'),
    ('arrayconv', '1.20', '1.19', '슬라이스 → 배열 값'),
    ('minmax', '1.21', '1.20', 'min·max·clear'),
    ('rangeint', '1.22', '1.21', '정수 range'),
    ('rangefunc', '1.23', '1.22', '함수 range(이터레이터)'),
    ('genalias', '1.23', '1.22', '제네릭 타입 별칭(노트는 1.24)'),
    ('newexpr', '1.26', '1.25', 'new(식)'),
    ('genmethod', '1.27', '1.26', '제네릭 메서드'),
    ('promoted', '1.27', '1.26', '끌어올린 필드를 리터럴에서'),
]
POS = re.compile(r'^\./main\.go:\d+:\d+: (.*)$', re.M)


def run(ctx):
    rows, data = [], []
    for ex, gate, below, name in LADDER:
        src = 'ex/10/ladder/' + ex
        ctx.go(src, v=gate)
        text = ctx.go(src, v=below, expect=1)
        msg = POS.search(text).group(1)
        msg = re.sub(r' \(-lang was set to go[\d.]+; check go\.mod\)$', '',
                     msg)
        rows.append((name, gate, msg))
        data.append('%s\t%s\t%s' % (ex, gate, name))
    ctx.table('ladder', ['기능', '필요한 go 줄', '한 판 아래에서 컴파일러가 하는 말'],
              rows, caption='go 1.27.1 이 go.mod 의 go 줄로 막는 기능 전부 '
                            '(types2 의 버전 검사에서 고름)')
    ctx.save('ladder_data.txt', '\n'.join(data) + '\n')
    run_modern(ctx)
    run_compat(ctx)


MODERN = [('go1', '1.0'), ('sortslice', '1.8'), ('generic', '1.18'),
          ('slices', '1.22'), ('iter', '1.23')]


def run_modern(ctx):
    """코드 현대화 갤러리 — 같은 일, 다섯 시대의 문체, 같은 출력.

    그리고 가장 옛 문체를 go 1.27 로 올린 사본에 go fix -diff(1.26 이후의
    modernizer)를 돌려, 지금의 도구가 무엇을 고치자고 하는지 본다."""
    outs = []
    for ex, v in MODERN:
        outs.append(ctx.go('ex/10/modern/' + ex))
    if len(set(outs)) != 1:
        raise RuntimeError('갤러리의 다섯 출력이 서로 다르다: %r' % outs)
    ctx.go('ex/10/modern/go1', v='1.27', cmd='go fix -diff .', tag='fix',
           expect=None)


def run_compat(ctx):
    """호환성 약속의 비용 — 블로그 compat(2023) 의 net.TCPAddr 예.

    Go 1 에서 되던 이름 없는 두 값 리터럴은 1.1 에서 Zone 이 더해져
    깨졌다. 지금 컴파일러도 같은 이유로 거절하고, 값을 다 채운 이름 없는
    리터럴은 컴파일되지만 go vet 이 짚는다."""
    ctx.go('ex/10/compat/tcpaddr', cmd='go build .', tag='build', expect=1)
    ctx.go('ex/10/compat/unkeyed')
    ctx.go('ex/10/compat/unkeyed', cmd='go vet .', tag='vet', expect=1)

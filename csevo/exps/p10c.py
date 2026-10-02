# -*- coding: utf-8 -*-
"""10부 뒤 조각 — C# 9.0 의 다듬기(6장), 코드 생성기 지원과 nullable
보강(7장), 정리(8장)의 증거. 예제는 ex/10/ 아래의 tn*·sl*·tc*·cov*·
ee*·ld*·lfa*·mi*·pm*·nl*·v9* 이다. (레코드·init 은 p10, 최상위 문·패턴·
nint 는 p10b 가 같은 ex/10 에 다른 이름으로 쓴다)

대상 형식 조건식을 C# 8.0 으로 내린 거절(CS8957)은 한 줄이 200칸을 넘어
캡처로 싣지 못한다 — LONGLINE 이 거절과 오류 번호만 확인한다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 6장 — 대상 형식 new · static 람다 · 조건식
    'tnbasic', 'tnwork', 'tnover', 'tntree', 'slstatic', 'slcache',
    'slnested', 'tccond',
    # 6장 — 공변 반환 · 확장 GetEnumerator · _ 매개변수 · 지역 함수
    'covbasic', 'covreflect', 'covimpl', 'eerange', 'eeorder', 'eeasync',
    'ldbasic', 'lfaattr', 'lfaextern',
    # 7장 — 모듈 초기화자 · partial 메서드 · nullable 보강 · 변성
    'mibasic', 'miorder', 'mimeta', 'pmgen', 'nltq', 'nlmnn', 'nldefault',
    'nlctor', 'v9varstatic',
    # 8장 — 같은 프로그램 두 벌
    'v9old', 'v9new',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['tnbad', 'covbad', 'mibad', 'pmbad', 'pmregex']

# C# 8.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가). 8장의 표가 이
# 캡처들에서 컴파일러가 댄 기능 이름과 오류 번호를 뽑는다
GATED8 = [
    ('tnbasic', '대상 형식 new()'),
    ('slstatic', 'static 익명 함수'),
    ('covbasic', '공변 반환'),
    ('eerange', '확장 GetEnumerator'),
    ('eeasync', '확장 GetAsyncEnumerator'),
    ('ldbasic', '람다의 _ 매개변수'),
    ('lfaattr', '지역 함수의 특성'),
    ('lfaextern', 'extern 지역 함수'),
    ('mibasic', '모듈 초기화자'),
    ('pmgen', 'partial 메서드의 확장'),
    ('nlmnn', '[MemberNotNull]·[MemberNotNullWhen]'),
    ('v9varstatic', 'static 멤버의 변성'),
]

# 다른 버전으로도 돌려 보는 것 — (예제, 언어 버전, 종료 코드)
OTHER = [
    ('covimpl', '8.0', 0),        # 8.0 과 9.0 이 같다 — 인터페이스는 그대로
    ('nlctor', '8.0', 0),         # 생성자 분석은 언어 버전에 묶이지 않았다
    ('v9new', '8.0', 1),          # 8장 — C# 9 판을 8.0 으로 내리면
]

# -define 으로 켜는 갈래 — (예제, 기호, 언어 버전, 종료 코드)
DEFINES = [
    ('tnover', 'B2', None, 1),
    ('slstatic', 'BAD', None, 1),
    ('slnested', 'BAD', None, 1),
    ('tcover', 'PAIR', None, 0),
    ('tcover', 'PAIR', '8.0', 0),
    ('tcover', 'NUL', None, 0),
    ('lfaattr', 'DEBUG', None, 0),
    ('lfaattr', 'BAD', None, 1),
    ('mibad', 'LOCAL', None, 1),
    ('nlmnn', 'BAD', None, ABORT),
    ('nldefault', 'BAD', None, 1),
]

# 오류 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 거절과 오류 번호만
# 확인한다(슬라이드는 그렇게 밝힌다). 8장의 표에는 이름과 번호만 실린다.
# (예제, 언어 버전, 기호, 오류 번호들, 표의 기능 이름)
LONGLINE = [
    ('tccond', '8.0', None, ['CS8957'], '대상 형식 조건식'),
    ('nltq', '8.0', None, ['CS8627'], '제약 없는 T?'),
    ('nldefault', '8.0', None, ['CS8627', 'CS8400'], 'where T : default'),
]


class Retry(object):
    """스왑이 찬 날에는 csc 하나가 60초를 넘기기도 한다. 시간 초과만 두
    번까지 다시 돌린다 — 출력이 다른 것은 다시 돌리지 않는다."""

    def __init__(self, ctx):
        self.ctx = ctx

    def cs(self, *args, **kw):
        for attempt in range(3):
            try:
                return self.ctx.cs(*args, **kw)
            except subprocess.TimeoutExpired:
                if attempt == 2:
                    raise

    def table(self, *args, **kw):
        return self.ctx.table(*args, **kw)


def gate_rows(found):
    """C# 8.0 캡처 → 표의 줄. 'Feature' 꼴이 아닌 거절은 이름 칸에
    '(전용 문장 …)' 을 적는다. O(캡처 길이)."""
    rows = []
    for ex, title, text in found:
        names = []
        for m in re.finditer(r"error CS\d+: Feature '([^']+)'", text):
            if m.group(1) not in names:
                names.append(m.group(1))
        other = re.findall(r'error (CS\d+): (?!Feature)', text)
        if other:
            names.append('(전용 문장 %s)' % ' '.join(sorted(set(other))))
        codes = sorted(set(re.findall(r'error (CS\d+)', text)))
        count = len(re.findall(r'\berror CS', text))
        rows.append((title, 'ex/10/' + ex, ' · '.join(names),
                     ' '.join(codes), str(count)))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/10/' + d)
    for d in FAIL:
        ctx.cs('ex/10/' + d, expect=1)
    found = []
    for d, title in GATED8:
        found.append((d, title, ctx.cs('ex/10/' + d, v='8.0', expect=1)))
    for d, v, code in OTHER:
        ctx.cs('ex/10/' + d, v=v, expect=code)
    for d, sym, v, code in DEFINES:
        ctx.cs('ex/10/' + d, v=v, flags='-define:' + sym,
               tag=sym.lower(), expect=code)
    for d, v, sym, errs, title in LONGLINE:
        flags = '-define:' + sym if sym else None
        code, text = csver.execute(os.path.join(csver.BASE, 'ex/10/' + d),
                                   'csrun', v=v, flags=flags,
                                   name='p10c-check-' + d)
        if code != 1 or any('error ' + e not in text for e in errs):
            raise RuntimeError('[p10c] %s(-langversion:%s) 는 %s 이어야 한다'
                               '\n%s' % (d, v, ' '.join(errs), text))
        found.append((d, title + ' (캡처 없음)', text))
    ctx.table('p10c_gates8',
              ['기능', '예제', '컴파일러가 댄 이름', '오류 번호', '오류 수'],
              gate_rows(found),
              caption='6장·7장의 예제를 -langversion:8.0 으로 컴파일한 '
                      '캡처에서 뽑은 표')

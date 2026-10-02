# -*- coding: utf-8 -*-
"""9부 뒤 조각 — C# 8.0 의 기본 인터페이스 메서드(6장), 작은 기능들(7장),
9부 정리(8장)의 증거.
예제는 ex/09/ 아래의 dim*·ro*·sl*·co*·v8* 이다. (nullable 은 p09, 패턴·
인덱스·비동기 스트림은 p09b 가 같은 ex/09 에 다른 이름으로 쓴다)

경고가 증거인 예제(EXPECT_WARN)는 종료 코드 0 으로 그대로 캡처한다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 6장 — 기본 인터페이스 메서드
    'dimwhy', 'dimadd', 'dimclass', 'dimimpl', 'dimderived',
    'dimdiamond', 'dimclasswin', 'dimreabs', 'dimmods', 'dimprot',
    'dimstate', 'dimstruct', 'dimalloc', 'dimruntime', 'dimmeta',
    'dimtrait', 'dimvsext', 'dimbase', 'dimsa11',
    # 7장 — readonly 멤버
    'romem', 'rowarn', 'rocopy', 'roauto', 'rometa', 'robcl',
    # 7장 — static 지역 함수, 이름 가리기
    'slstatic', 'slmeta', 'sllambda9', 'v8shadow', 'v8shadowtp',
    # 7장 — ??=
    'coassign', 'colazy', 'conullable',
    # 7장 — 비관리 생성 형식, 중첩 stackalloc, 작은 변화들
    'v8unmgd', 'v8unmgdgen', 'v8nested', 'v8nestedcond', 'v8small',
    'v8obsacc',
    # 8장 — 정리
    'v8old', 'v8new', 'v8break',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['roerr', 'slfix', 'coerr', 'v8nestedptr']

# #if 기호를 켠 캡처 — (예제, 기호, 종료 코드)
DEFINES = [
    ('dimwhy', 'V2', 1), ('dimderived', 'NONEW', 0),
    ('dimdiamond', 'BAD', 1), ('dimreabs', 'BAD', 1), ('dimprot', 'BAD', 1),
    ('dimstate', 'BAD', 1), ('dimbase', 'BAD', 1),
    ('roauto', 'WARN', 0), ('roauto', 'BAD', 1), ('roerr', 'DECL', 1),
    ('slstatic', 'BAD', 1), ('sllambda9', 'BAD', 1), ('v8shadow', 'BAD', 1),
    ('coerr', 'AND', 1),
]

# 오류 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 거절과 오류 번호만
# 확인한다(슬라이드는 그렇게 밝힌다). (예제, 기호, 오류 번호)
LONGLINE = [('dimclass', 'BAD', 'CS1061'), ('v8unmgdgen', 'BAD', 'CS8377')]

# C# 7.3 으로 내리면 거절되는 것 — 언어 버전 짝 (가). 8장의 표가 이
# 캡처들에서 컴파일러가 댄 기능 이름과 오류 번호를 뽑는다
GATED73 = [
    ('dimadd', '기본 구현'),
    ('dimmods', 'static·private·sealed 멤버'),
    ('romem', 'readonly 멤버'),
    ('coassign', '??='),
    ('v8shadow', '이름 가리기 + static 지역 함수'),
    ('v8unmgd', '비관리 생성 형식'),
    ('v8unmgdgen', 'sizeof(Coords<T>)'),
    ('v8nested', '식 안의 stackalloc'),
    ('v8small', '@$ · 열린 T 의 is null'),
    ('v8obsacc', '접근자의 [Obsolete]'),
    ('v8new', '8장의 프로그램 전체'),
]

# 다른 버전으로 돌려 보는 것 — (예제, 언어 버전, 종료 코드)
OTHER = [
    ('dimsa11', '8.0', 1), ('dimsa11', '10.0', 1),
    ('sllambda9', '8.0', 1),
    ('v8nestedcond', '7.1', 1),
    ('v8shadowtp', '7.3', 0),      # 경고는 7.3 에서도 같다 — 게이트 아님
    ('v8break', '7.3', 0),         # CS8513 만 빠진다 — 버전에 묶인 경고
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
    """C# 7.3 캡처 → 표의 줄. 'Feature' 꼴이 아닌 거절(CS8401 등)은 이름
    칸에 '(전용 문장)' 을 적는다. O(캡처 길이)."""
    rows = []
    for ex, title, text in found:
        names = []
        for m in re.finditer(r"error CS\d+: Feature '([^']+)'", text):
            if m.group(1) not in names:
                names.append(m.group(1))
        other = [c for c in re.findall(r'error (CS\d+): (?!Feature)', text)]
        if other:
            names.append('(전용 문장 %s)' % ' '.join(sorted(set(other))))
        codes = sorted(set(re.findall(r'error (CS\d+)', text)))
        count = len(re.findall(r'\berror CS', text))
        rows.append((title, 'ex/09/' + ex, ' · '.join(names),
                     ' '.join(codes), str(count)))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/09/' + d)
    for d in FAIL:
        ctx.cs('ex/09/' + d, expect=1)
    for d, sym, code in DEFINES:
        ctx.cs('ex/09/' + d, flags='-define:' + sym,
               tag='bad' if sym == 'BAD' else sym.lower(), expect=code)
    found = []
    for d, title in GATED73:
        found.append((d, title, ctx.cs('ex/09/' + d, v='7.3', expect=1)))
    for d, v, code in OTHER:
        ctx.cs('ex/09/' + d, v=v, expect=code)
    for d, sym, err in LONGLINE:
        code, text = csver.execute(os.path.join(csver.BASE, 'ex/09/' + d),
                                   'csrun', v='8.0', flags='-define:' + sym,
                                   name='p09c-check-' + d)
        if code != 1 or 'error ' + err not in text:
            raise RuntimeError('[p09c] %s(-define:%s) 는 %s 이어야 한다\n%s'
                               % (d, sym, err, text))

    ctx.table('p09c_gates73',
              ['기능', '예제', '컴파일러가 댄 이름', '오류 번호', '오류 수'],
              gate_rows(found),
              caption='6장·7장의 예제를 -langversion:7.3 으로 컴파일한 '
                      '캡처에서 뽑은 표')

# -*- coding: utf-8 -*-
"""16부 앞 조각 — 흐름으로 다시 읽기의 1장 연표 · 2장 네 갈래 · 3장
langversion 사다리의 증거. 예제는 ex/16/ 아래의 st*·ld* 이다(p16b 는 같은
ex/16 에 er*·kw*·cp*·nx* 를 쓴다). 1장의 표는 실험이 아니라
deck/gen_tables.py 가 data/ 에서 만든다(tbl_p16_rel_* 등).

사다리(ldrungs)는 버전마다 컴파일러 게이트 하나를 #if 기호(R1 … R14)
뒤에 둔 파일 하나다. 언어 버전 17개 × 기호 17개를 모두 판정한다.

  · 통과 칸 — 그 언어 버전 이하의 기호를 한꺼번에 켜고 한 번 컴파일한다.
    오류가 하나도 없으면 켠 기호 전부가 그 버전에서 통과한 것이다(오류가
    있으면 숨을 곳이 없다). 경고는 줄 번호로 기호에 돌린다.
  · 거절 칸 — 기호 하나씩 따로 컴파일한다. 한 컴파일에 거절이 여럿이면
    파서의 거절이 바인더의 거절을 가리기 때문이다(14부·15부에서 본 일).

컴파일은 17 + 136 번, 실행은 하지 않는다(CSRUN_COMPILE_ONLY). 시간
O(버전 수 × 기호 수), 표는 O(같은 것)."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/16/'
RUNGS_SRC = os.path.join(csver.BASE, EX + 'ldrungs', 'Program.cs')

# 사다리의 칸 — (기호, 게이트가 요구하는 언어 버전, 표에 쓸 이름)
RUNGS = [
    ('R1', '1', 'module 특성 대상'),
    ('R2', '2', '제네릭'),
    ('R3', '3', '람다'),
    ('R4', '4', '명명 인수'),
    ('R5', '5', 'async'),
    ('R6', '6', '보간 문자열'),
    ('R7', '7.0', '튜플'),
    ('R7_1', '7.1', 'default 리터럴'),
    ('R7_2', '7.2', 'private protected'),
    ('R7_3', '7.3', '튜플 =='),
    ('R8', '8.0', '??='),
    ('R9', '9.0', 'new()'),
    ('R10', '10.0', '파일 범위 namespace'),
    ('R11', '11.0', '원시 문자열'),
    ('R12', '12.0', '컬렉션 식'),
    ('R13', '13.0', 'Lock 객체'),
    ('R14', '14.0', '?.='),
]
# 언어 버전 — 컴파일러가 받는 번호 꼴 전부(ISO-1·ISO-2 는 1·2 의 별칭)
LVS = ['1', '2', '3', '4', '5', '6', '7.0', '7.1', '7.2', '7.3', '8.0',
       '9.0', '10.0', '11.0', '12.0', '13.0', '14.0']
SPLIT = LVS.index('8.0')        # 표를 둘로 — 접힌 화면 폭

COMPILE = 'CSRUN_COMPILE_ONLY=1 csrun'


def vkey(v):
    """'7.3' → (7, 3), '14.0' → (14, 0). 버전 비교용."""
    a, _, b = v.partition('.')
    return int(a), int(b or 0)


class Retry(object):
    """스왑이 찬 날에는 csc 하나가 60초를 넘기기도 한다. 시간 초과만 두
    번까지 다시 돌린다 — 출력이 다른 것은 다시 돌리지 않는다(p15c 와 같다)."""

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


def execute(ex, cmd, v, flags, name):
    """캡처로 남기지 않는 실행 — 시간 초과만 두 번까지 다시."""
    src = os.path.join(csver.BASE, EX + ex)
    for attempt in range(3):
        try:
            return csver.execute(src, cmd, v=v, flags=flags, name=name)
        except subprocess.TimeoutExpired:
            if attempt == 2:
                raise


def rung_lines():
    """소스의 줄 번호 → 그 줄을 감싼 #if 기호. O(줄 수)."""
    out, cur = {}, None
    with open(RUNGS_SRC, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            m = re.match(r'#if (R[0-9_]+)$', s)
            if m:
                cur = m.group(1)
            elif s == '#endif':
                cur = None
            elif cur:
                out[i] = cur
    return out


DIAG = re.compile(r'Program\.cs\((\d+),\d+\): (error|warning) (CS\d+): (.*)')


def diags(text):
    """컴파일러 출력 → [(줄, 'error'|'warning', 번호, 문장)]."""
    return [(int(a), b, c, d) for a, b, c, d in DIAG.findall(text)]


def feature_of(msg):
    """"Feature 'X' is not available in C# N …" → ('X', 'N'). 아니면
    (None, None)."""
    m = re.match(r"Feature '([^']*)' is not available in C# (\d+(?:\.\d+)?)",
                 msg)
    return m.groups() if m else (None, None)


def ladder(ctx):
    """사다리 전체 → (칸 표, 거절 기록). 칸은 {(기호, 언어 버전): 글자}."""
    where = rung_lines()
    cell, refused = {}, {}
    for v in LVS:
        ok = [r for r, need, _ in RUNGS if vkey(need) <= vkey(v)]
        code, text = execute('ldrungs', COMPILE, v, '-define:' + ';'.join(ok),
                             'p16-ladder-ok-' + v)
        found = diags(text)
        if code != 0 or any(k == 'error' for _, k, _, _ in found):
            raise RuntimeError('[p16] 사다리: C# %s 이하의 기호를 켠 컴파일이 '
                               '실패했다\n%s' % (v, text))
        warned = set(where.get(line) for line, _, _, _ in found)
        for r in ok:
            cell[(r, v)] = '△' if r in warned else '✓'
        for r, need, _ in RUNGS:
            if vkey(need) <= vkey(v):
                continue
            # 게이트 한 단계 아래는 캡처로 남긴다 — 덱이 싣는다
            if LVS.index(need) - 1 == LVS.index(v):
                text = ctx.cs(EX + 'ldrungs', v=v, flags='-define:' + r,
                              tag=r.lower(), expect=1)
            else:
                code, text = execute('ldrungs', COMPILE, v, '-define:' + r,
                                     'p16-ladder-%s-%s' % (r, v))
                if code != 1:
                    raise RuntimeError('[p16] %s 를 C# %s 로: 종료 %d\n%s'
                                       % (r, v, code, text))
            errs = [d for d in diags(text) if d[1] == 'error']
            if not errs:
                raise RuntimeError('[p16] %s(C# %s) 에 오류 줄이 없다\n%s'
                                   % (r, v, text))
            if any(where.get(line) != r for line, _, _, _ in errs):
                raise RuntimeError('[p16] %s(C# %s) 의 오류가 다른 칸에 '
                                   '있다\n%s' % (r, v, text))
            cell[(r, v)] = '✗'
            refused[(r, v)] = errs
    return cell, refused


def ladder_tables(ctx, cell, refused):
    names = dict((r, '%s %s' % (need, name)) for r, need, name in RUNGS)
    for k, cols in ((1, LVS[:SPLIT]), (2, LVS[SPLIT:])):
        rows = [[names[r]] + [cell[(r, v)] for v in cols]
                for r, _, _ in RUNGS]
        ctx.table('p16_ladder_%d' % k, ['기능 \\ 언어 버전'] + cols, rows,
                  caption='✓ 통과 · △ 경고만 · ✗ 거절 — csc 를 %d번 돌린 '
                  '결과(%s–%s)' % (len(LVS) + len(refused), cols[0],
                                   cols[-1]))
    # 언어 버전마다 — 거절된 칸의 수, 첫 오류의 번호들, 문장이 말하는 버전
    rows = []
    for v in LVS[:-1]:
        mine = [(r, refused[(r, v)][0]) for r, _, _ in RUNGS
                if (r, v) in refused]
        codes = sorted(set(e[2] for _, e in mine))
        said = sorted(set(feature_of(e[3])[1] or '—' for _, e in mine))
        rows.append([v, str(len(mine)), ' '.join(codes),
                     ' '.join('C# ' + s if s != '—' else s for s in said)])
    ctx.table('p16_ladder_codes', ['-langversion', '거절된 칸', '첫 오류의 번호',
                                   '문장 속 버전'], rows,
              caption='거절 칸마다 첫 오류 — 기능이 달라도 번호는 언어 버전이 '
              '정한다')
    # 칸마다 — 한 단계 아래의 거절과, 더 아래에서 문장이 바뀌는 곳
    rows = []
    for r, need, name in RUNGS:
        below = [v for v in LVS if vkey(v) < vkey(need)]
        if not below:
            rows.append(['%s %s' % (need, name), '—', '—', '—'])
            continue
        e = refused[(r, below[-1])][0]
        feat = feature_of(e[3])[0] or e[3][:40]
        # 더 아래 버전에서 첫 오류가 다른 기능을 말하면, 이웃한 버전끼리
        # 묶어 '1–6 tuples' 처럼 적는다. O(버전 수)
        groups = []
        for v in below[:-1]:
            f = feature_of(refused[(r, v)][0][3])[0] or \
                refused[(r, v)][0][3][:40]
            if f == feat:
                continue
            if groups and groups[-1][2] == f and \
                    LVS.index(groups[-1][1]) + 1 == LVS.index(v):
                groups[-1][1] = v
            else:
                groups.append([v, v, f])
        other = ', '.join('%s%s %s' % (a, '' if a == b else '–' + b, f)
                          for a, b, f in groups)
        rows.append(['%s %s' % (need, name), below[-1] + ': ' + e[2], feat,
                     other or '—'])
    ctx.table('p16_ladder_rungs', ['기능', '한 단계 아래', '문장의 기능 이름',
                                   '더 아래에서 먼저 걸리는 것'], rows,
              caption='게이트 한 단계 아래의 첫 오류 — 더 아래로 내리면 '
              '다른 기능이 먼저 걸리는 칸이 있다')


def run(ctx):
    ctx = Retry(ctx)
    # 2장 — 언어와 라이브러리, 런타임, 도구
    ctx.cs(EX + 'stlib')
    ctx.cs(EX + 'strt')
    for v, tag in (('14.0', None), ('1', None), ('7.3', None),
                   ('default', None), ('latest', None),
                   ('latestmajor', None), ('preview', None),
                   ('ISO-2', None)):
        ctx.cs(EX + 'stver', v=v, tag=tag, expect=1)
    # 3장 — TFM 마다의 기본값(MSBuild 의 평가), 받는 언어 버전 목록
    ctx.cs(EX + 'ldtfm', v='14.0',
           cmd='dotnet msbuild -nologo -v:m -t:Ladder -nr:false -m:1')
    ctx.cs(EX + 'stver', flags='-langversion:?', tag='list',
           env='CSRUN_COMPILE_ONLY=1')
    # record 는 사다리에 올리지 못한다 — C# 8.0 에서는 다른 문법으로 읽힌다
    ctx.cs(EX + 'ldrecord')
    ctx.cs(EX + 'ldrecord', v='8.0', expect=1)
    # 사다리 — 기호 없이 한 번(ok), 그리고 표
    ctx.cs(EX + 'ldrungs')
    ctx.cs(EX + 'ldrungs', v='1', flags='-define:R1', tag='r1')
    cell, refused = ladder(ctx)
    ladder_tables(ctx, cell, refused)

# -*- coding: utf-8 -*-
"""16부 뒤 조각 — 같은 프로그램 다섯 시대(4장), 호환성(5장), 다음 버전(6장),
정리(7장)의 증거. 예제는 ex/16/ 아래의 er*·kw*·cp*·nx* 이다(p16 은 같은
ex/16 에 tl*·st*·ld* 로 쓴다).

4장: 주문 목록을 묶어 합계를 찍는 한 프로그램을 C# 1.2·2.0·3.0·7.3·14 의
문체로 다섯 번 썼다. 다섯 출력이 바이트까지 같아야 하고(아니면 멈춘다),
옛 판은 모두 C# 14.0 으로도 컴파일·실행되어 같은 출력을 내야 한다.
소스의 크기(줄·코드 줄·토큰)는 여기서 세어 표(tbl_p16b_eras)로 낸다 —
손으로 센 숫자는 덱에 없다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/16/'

# 4장 — (예제, 시대 이름, csproj 의 언어 버전)
ERAS = [
    ('er12', 'C# 1.2', '1'),
    ('er2', 'C# 2.0', '2'),
    ('er3', 'C# 3.0', '3'),
    ('er73', 'C# 7.3', '7.3'),
    ('er14', 'C# 14', '14.0'),
]
# 이 컴파일러가 받는 언어 버전 — 낮은 것부터(PLAN.md §0.6)
VERSIONS = ['1', '2', '3', '4', '5', '6', '7.0', '7.1', '7.2', '7.3',
            '8.0', '9.0', '10.0', '11.0', '12.0', '13.0', '14.0']


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


# ------------------------------------------------------------- 소스 세기
# 토큰은 정규식으로 자른다: 주석은 버리고, 문자열(보간·원시 포함)은 통째로
# 한 토큰, 이름·숫자는 한 토큰, 두 글자 연산자는 한 토큰, 나머지는 글자
# 하나가 한 토큰. 컴파일러의 토큰과 똑같지는 않지만 다섯 판을 같은 자로 잰다.
TOKEN = re.compile(r'''
    (?P<comment>//[^\n]*|/\*.*?\*/)
  | (?P<raw>\$*"""[\s\S]*?""")
  | (?P<str>[$@]*"(?:[^"\\\n]|\\.)*")
  | (?P<chr>'(?:[^'\\\n]|\\.)')
  | (?P<word>[A-Za-z_]\w*|\d+)
  | (?P<op>=>|==|!=|>=|<=|&&|\|\||\+\+|--|\+=|-=|\.\.|\?\?)
  | (?P<ws>\s+)
  | (?P<other>.)
''', re.S | re.X)


def tokens(text):
    """주석·공백을 뺀 토큰 수. O(길이)."""
    n = 0
    for m in TOKEN.finditer(text):
        if m.lastgroup not in ('comment', 'ws'):
            n += 1
    return n


def measure(d):
    """예제 디렉터리의 .cs 전부 → (파일 수, 줄, 코드 줄, 토큰).
    코드 줄은 빈 줄과 // 로만 된 줄(첫 줄의 슬라이드 머리 포함)을 뺀 것."""
    src = os.path.join(csver.BASE, EX + d)
    files = sorted(f for f in os.listdir(src) if f.endswith('.cs'))
    lines = code = toks = 0
    for f in files:
        with open(os.path.join(src, f), encoding='utf-8') as fh:
            text = fh.read()
        rows = text.split('\n')
        if rows and rows[-1] == '':
            rows.pop()
        lines += len(rows)
        code += sum(1 for r in rows
                    if r.strip() and not r.strip().startswith('//'))
        toks += tokens(text)
    return len(files), lines, code, toks


def diag_summary(text):
    """거절 출력 → '오류 N개 (CS…, CS…)'. 같은 번호는 한 번만, 나온 차례로."""
    codes = re.findall(r': error (CS\d+):', text)
    seen = []
    for c in codes:
        if c not in seen:
            seen.append(c)
    return '오류 %d개 (%s)' % (len(codes), ', '.join(seen))


def eras(ctx):
    """다섯 판을 돌려 출력을 견주고, 판마다 언어 버전을 한 칸씩 내려
    처음 거절되는 곳을 찾는다. O(판 × 버전) 번의 csc."""
    out = {}
    for d, name, v in ERAS:
        out[d] = ctx.cs(EX + d)
    first = out[ERAS[0][0]]
    for d, name, v in ERAS[1:]:
        if out[d] != first:
            raise RuntimeError('[p16b] %s 의 출력이 er12 와 다르다\n%s\n---\n%s'
                               % (d, first, out[d]))
    rows = []
    for d, name, v in ERAS:
        if v != '14.0':                 # 옛 판을 오늘의 언어 버전으로
            now = ctx.cs(EX + d, v='14.0')
            if now != first:
                raise RuntimeError('[p16b] %s 를 14.0 으로 돌린 출력이 다르다'
                                   '\n%s' % (d, now))
            today = '같은 출력'
        else:
            today = '(이 판)'
        # 한 칸씩 내린다 — 받는 동안은 출력이 같아야 하고, 처음 거절되는
        # 버전의 진단을 요약한다
        lowest, refused = v, '—'
        for lv in reversed(VERSIONS[:VERSIONS.index(v)]):
            text = ctx.cs(EX + d, v=lv, expect=(0, 1))
            if '[exit 1]' in text:
                refused = 'C# %s: %s' % (lv, diag_summary(text))
                break
            if text != first:
                raise RuntimeError('[p16b] %s 를 %s 로 돌린 출력이 다르다\n%s'
                                   % (d, lv, text))
            lowest = lv
        nfiles, lines, code, toks = measure(d)
        rows.append((name, v, nfiles, lines, code, toks, today, lowest,
                     refused))
    # C# 14 판을 C# 7.3 으로 — 최상위 문부터 무너진다
    ctx.cs(EX + 'er14', v='7.3', expect=1)
    ctx.table('p16b_eras',
              ['시대', 'csproj', '파일', '줄', '코드 줄', '토큰',
               'C# 14.0 으로', '가장 낮게', '처음 거절'],
              rows, caption='다섯 판의 크기는 실험 묶음이 소스에서 센 것이다 '
              '(코드 줄 = 빈 줄과 주석 줄을 뺀 줄, 토큰 = 주석을 뺀 정규식 '
              '토큰 — 문자열 하나가 한 토큰). 오른쪽 세 칸은 csc 를 돌린 결과다 '
              '— 언어 버전을 한 칸씩 내려 같은 출력이 나온 가장 낮은 버전과, '
              '처음 거절된 버전의 오류 수·번호.')


def today(ctx):
    """다섯 판을 오늘의 컴파일러(C# 14.0)로 — 경고 웨이브를 모두 켜고
    (-warn:9999), 다시 nullable 참조 형식까지 켜서(-nullable:enable) 나온
    경고를 센다. nullable 경고 줄은 200칸을 넘는 것이 있어 캡처로 싣지
    않고 csver.execute 로 돌려 번호만 표에 옮긴다. O(판 × 2) 번의 csc."""
    rows = []
    for d, name, v in ERAS:
        cells = [name]
        for fl in ('-warn:9999', '-warn:9999 -nullable:enable'):
            code, text = csver.execute(
                os.path.join(csver.BASE, EX + d), 'CSRUN_COMPILE_ONLY=1 csrun',
                v='14.0', flags=fl, name='p16b-today-' + d)
            if code != 0:
                raise RuntimeError('[p16b] %s 를 C# 14.0 %s 로 컴파일 못 했다'
                                   '\n%s' % (d, fl, text))
            codes = re.findall(r': warning (CS\d+):', text)
            seen = []
            for c in codes:
                if c not in seen:
                    seen.append(c)
            cells.append('%d개' % len(codes) +
                         (' (%s)' % ', '.join(seen) if seen else ''))
        rows.append(tuple(cells))
    ctx.table('p16b_today', ['시대', '-warn:9999', '+ -nullable:enable'],
              rows, caption='다섯 판을 -langversion:14.0 으로 컴파일만 한 '
              '결과 — 경고 수(같은 번호는 한 번만 적었다). 실험 묶음이 '
              '진단 줄에서 센 것이다.')
    # 옛 판 하나는 캡처로 — 웨이브를 다 켜도 조용하다
    ctx.cs(EX + 'er12', v='14.0', flags='-warn:9999', tag='w9999')


# ------------------------------------------------------------- 5장
# 문맥 키워드를 이름으로 쓴 꼴 — (예제, 기호, 낱말, 그 낱말을 들여온 기능의
# MessageID, 쓴 자리). 버전은 data/langgates.tsv 가 MessageID 로 정한다 —
# 여기에 버전 숫자를 적지 않는다.
KW = [
    ('kwold', 'YIELD', 'yield', 'IDS_FeatureIterators', '지역 변수'),
    ('kwold', 'PARTIAL', 'partial', 'IDS_FeaturePartialTypes',
     '형식 이름 · 반환 형식'),
    ('kwold', 'VAR', 'var', 'IDS_FeatureImplicitLocal', '형식 이름'),
    ('kwold', 'FROM', 'from', 'IDS_FeatureQueryExpression', '지역 변수'),
    ('kwold', 'DYNAMIC', 'dynamic', 'IDS_FeatureDynamic', '형식 이름'),
    ('kwold', 'ASYNC', 'async · await', 'IDS_FeatureAsync',
     '반환 형식 · 지역 변수'),
    ('kwold', 'WHEN', 'when', 'IDS_FeatureExceptionFilter', '지역 변수'),
    ('kwold', 'NAMEOF', 'nameof', 'IDS_FeatureNameof', '메서드 이름'),
    ('kwold', 'DISCARD', '_', 'IDS_FeatureDiscards', '지역 변수'),
    ('kwold', 'UNMANAGED', 'unmanaged',
     'IDS_FeatureUnmanagedGenericTypeConstraint', '형식 이름 · 제약'),
    ('kwold', 'NOTNULL', 'notnull',
     'IDS_FeatureNotNullGenericTypeConstraint', '형식 이름 · 제약'),
    ('kwnew', 'RECORD', 'record', 'IDS_FeatureRecords', '형식 이름'),
    ('kwnew', 'NOT', 'not', 'IDS_FeatureNotPattern', '패턴 속 형식 이름'),
    ('kwnew', 'NINT', 'nint', 'IDS_FeatureNativeInt', '형식 이름'),
    ('kwnew', 'INIT', 'init', 'IDS_FeatureInitOnlySetters', '필드 이름'),
    ('kwnew', 'REQUIRED', 'required', 'IDS_FeatureRequiredMembers',
     '형식 이름'),
    ('kwnew', 'SCOPED', 'scoped', 'IDS_FeatureRefFields', '형식 이름'),
    ('kwnew', 'FILE', 'file', 'IDS_FeatureFileTypes', '형식 이름'),
    ('kwnew', 'ALLOWS', 'allows', 'IDS_FeatureAllowsRefStructConstraint',
     '형식 이름'),
    ('kwnew', 'FIELD', 'field', 'IDS_FeatureFieldKeyword',
     '속성 접근자 안의 필드'),
    ('kwnew', 'EXTENSION', 'extension', 'IDS_FeatureExtensions',
     '형식 이름'),
]

# 경고 웨이브 — csc 에 넘겨 볼 -warn: 값(컴파일만)
WARN = ['0', '4', '5', '6', '7', '8', '9', '10', '11', '9999', '-1', 'x']


def gates():
    """data/langgates.tsv → {MessageID: 버전}."""
    path = os.path.join(csver.BASE, 'data', 'langgates.tsv')
    out = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or line.startswith('msgid'):
                continue
            cols = line.rstrip('\n').split('\t')
            out[cols[0]] = cols[2]
    return out


def lv_of(gate):
    """게이트의 버전('7' · '8' · '14') → 컴파일러에 넘기는 꼴('7.0' …)."""
    for v in VERSIONS:
        if v == gate or v == gate + '.0':
            return v
    raise RuntimeError('[p16b] 모르는 버전 %r' % gate)


def outcome(code, text):
    """실행 결과 → 표의 칸: 오류면 첫 오류 번호, 아니면 '됨' 에 출력(값일
    때만 — 형식 이름 'Program+…' 은 뺀다)과 경고 번호."""
    if code != 0:
        m = re.search(r': error (CS\d+):', text)
        return '오류 %s' % (m.group(1) if m else '?')
    warns = []
    for c in re.findall(r': warning (CS\d+):', text):
        if c not in warns:
            warns.append(c)
    body = [l for l in text.split('\n')
            if l.strip() and ': warning CS' not in l]
    shown = ' / '.join(l for l in body if not l.startswith('Program+'))
    return ('됨' + (' (%s)' % shown if shown else '')
            + (' · 경고 ' + ', '.join(warns) if warns else ''))


def trial(d, v, sym):
    """kw 예제 하나를 기호 하나로 돌린다 → 표의 칸. 캡처로 남기지 않는다
    — 진단 줄이 200칸을 넘는 낱말(field 의 CS9258, partial 의 CS0267)이
    있어서다. 슬라이드에 싣는 몇은 run() 이 따로 ctx.cs 로 뜬다."""
    for attempt in range(3):            # Retry 와 같은 까닭
        try:
            code, text = csver.execute(
                os.path.join(csver.BASE, EX + d), 'csrun', v=v,
                flags='-define:' + sym, name='p16b-kw-' + d)
            break
        except subprocess.TimeoutExpired:
            if attempt == 2:
                raise
    if code not in (0, 1):
        raise RuntimeError('[p16b] %s -define:%s (C# %s) → 종료 %d\n%s'
                           % (d, sym, v, code, text))
    return outcome(code, text)


def std_contextual():
    """표준 초안(docs/standard/lexical-structure.txt)의 contextual_keyword
    문법 블록 → 낱말 집합. 손으로 옮겨 적지 않는다. O(파일 길이)."""
    path = os.path.join(csver.BASE, 'docs', 'standard',
                        'lexical-structure.txt')
    with open(path, encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'^contextual_keyword\n(.*?)^\s*;', text, re.M | re.S)
    if not m:
        raise RuntimeError('[p16b] 표준 초안에서 contextual_keyword 를 못 찾았다')
    return set(re.findall(r"'(\w+)'", m.group(1)))


def keywords(ctx):
    """낱말마다 들어오기 한 버전 앞 · 들어온 버전 · C# 14.0 에서 돌리고,
    들어온 버전과 14.0 의 결과가 다르면 바뀐 판을 찾는다. O(낱말 × 버전)
    번의 csc."""
    gate = gates()
    std = std_contextual()
    if len(std) != 30:                  # 표준 초안의 목록 — 슬라이드가 "30개"
        raise RuntimeError('[p16b] 표준 초안의 문맥 키워드가 %d개' % len(std))
    halves = {'kwold': [], 'kwnew': []}
    for d, sym, word, msgid, where in KW:
        v = lv_of(gate[msgid])
        pre = VERSIONS[VERSIONS.index(v) - 1]
        r_pre = trial(d, pre, sym)
        r_v = trial(d, v, sym)
        r_now = r_v if v == '14.0' else trial(d, '14.0', sym)
        changed = ''
        if r_v != r_now:
            # 13.0 부터 아래로 — 들어온 판과 같은 결과가 처음 나오는 판의
            # 바로 위가 바뀐 판이다(결과가 판을 따라 한 번만 바뀐다고 본다).
            # 늦게 바뀐 낱말(partial)은 한 번에 끝난다.
            mid = VERSIONS[VERSIONS.index(v) + 1:-1]
            changed = ' (C# %s 부터)' % (mid[0] if mid else '14.0')
            for i in range(len(mid) - 1, -1, -1):
                if trial(d, mid[i], sym) == r_v:
                    up = mid[i + 1] if i + 1 < len(mid) else '14.0'
                    changed = ' (C# %s 부터)' % up
                    break
        words = re.findall(r'\w+', word)
        in_std = '있음' if all(w in std for w in words) else '없음'
        halves[d].append((word, 'C# %s' % gate[msgid], in_std,
                          r_pre, r_v, r_now + changed))
    head = ['낱말', '들어온 판', '표준 초안', '한 판 앞', '들어온 판에서',
            'C# 14.0']
    ctx.table('p16b_kw', head, halves['kwold'],
              caption='ex/16/kwold — 낱말마다 -define 하나. "들어온 판" 은 '
              'data/langgates.tsv 의 게이트 버전, "표준 초안" 은 '
              'lexical-structure 의 contextual_keyword 목록에 있는가이고, '
              '오른쪽 세 칸은 csc 로 컴파일해 돌린 결과다(괄호는 출력한 값).')
    ctx.table('p16b_kw2', head, halves['kwnew'],
              caption='ex/16/kwnew — 같은 방법. 결과가 들어온 판과 14.0 '
              '사이에서 바뀌면 처음 바뀐 판을 괄호에 적었다.')


def waves(ctx):
    """cpwave 를 -warn: 값마다 컴파일만 해서 나온 경고 번호를 표로."""
    rows = []
    for w in WARN:
        text = ctx.cs(EX + 'cpwave', flags='-warn:' + w,
                      env='CSRUN_COMPILE_ONLY=1', tag='w' + w.replace('-', 'm'),
                      expect=(0, 1))
        if '[exit ' in text:
            m = re.search(r'error (CS\d+): (.*)', text)
            rows.append(('-warn:' + w, '거절', m.group(1) if m else '?'))
            continue
        seen = []
        for c in re.findall(r': warning (CS\d+):', text):
            if c not in seen:
                seen.append(c)
        rows.append(('-warn:' + w, '받음', ', '.join(seen) or '(없음)'))
    ctx.cs(EX + 'cpwave')                   # 기본 수준으로 돌린 결과
    ctx.table('p16b_waves', ['플래그', 'csc', '나온 경고(나온 차례)'], rows,
              caption='ex/16/cpwave 를 -warn: 값마다 컴파일만 한 결과 — '
              '실험 묶음이 진단 줄에서 뽑았다.')


def breaking(ctx):
    """docs/roslyn 의 깨지는 변경 문서마다 첫 줄 · § 제목 수 · 번호 매긴
    줄 수 · 줄 수. 문서마다 형식이 달라(제목마다 한 항목, 번호 목록, 글머리
    목록) 하나의 '항목 수' 로 줄이지 않는다. O(문서 길이)."""
    base = os.path.join(csver.BASE, 'docs', 'roslyn')
    order = ['VS2015', 'VS2017', 'post-VS2017', 'VS2019', 'post-VS2019',
             'DotNet-5', 'post-DotNet-5', 'DotNet-6', 'DotNet-7',
             'DotNet-8', 'DotNet-9', 'DotNet-10']
    rows = []
    for key in order:
        name = 'Compiler-Breaking-Changes-%s.txt' % key
        with open(os.path.join(base, name), encoding='utf-8') as f:
            lines = f.read().split('\n')
        if lines and lines[-1] == '':
            lines.pop()
        heads = sum(1 for l in lines if l.startswith('§\t'))
        nums = sum(1 for l in lines if re.match(r'\d+\. ', l))
        bullets = sum(1 for l in lines if l.startswith('- '))
        rows.append((key, heads, nums, bullets, len(lines)))
    ctx.table('p16b_brk', ['문서(… - X)', '§ 제목', '번호 줄', '글머리 줄', '줄'],
              rows, caption='docs/roslyn/Compiler-Breaking-Changes-*.txt '
              '를 실험 묶음이 센 것 — 문서마다 적는 형식이 다르다.')


def doc_tally(ctx):
    """덱이 모은 '문서와 다른 곳' 표 — deck/sections 의 id 가 -docs 로
    끝나는 장마다 표의 줄 수(머리 줄 뺌)를 센다. 그 장들이 바뀌면 이 표도
    바뀐다 — 손으로 센 합계는 덱에 없다. O(조각 크기)."""
    sec = os.path.join(csver.BASE, 'deck', 'sections')
    art = re.compile(r'<article[^>]*id="(p(\d+)-[^"]*docs)"[^>]*>(.*?)</article>',
                     re.S)
    rows, total = [], 0
    for name in sorted(os.listdir(sec)):
        if not name.endswith('.html'):
            continue
        with open(os.path.join(sec, name), encoding='utf-8') as f:
            text = f.read()
        for m in art.finditer(text):
            if m.group(2) == '16':      # 이 장 자신(p16-cp-docs)은 장부가 아니다
                continue
            n = m.group(3).count('<tr>') - 1
            if n < 1:
                raise RuntimeError('[p16b] #%s 에 표가 없다' % m.group(1))
            rows.append((int(m.group(2)), m.group(1), n))
            total += n
    rows.sort(key=lambda r: r[0])     # 안정 정렬 — 부 안에서는 조각 파일 차례
    out = [('%d부' % p, i, str(n)) for p, i, n in rows]
    out.append(('합계', '%d장' % len(rows), str(total)))
    ctx.table('p16b_docs', ['부', '장 id', '줄'], out,
              caption='deck/sections 에서 id 가 -docs 로 끝나는 장의 표를 '
              '실험 묶음이 센 것(머리 줄 뺌). 문서끼리 다른 곳과 문서와 '
              '컴파일러가 다른 곳이 섞여 있다.')


def run(ctx):
    ctx = Retry(ctx)
    eras(ctx)
    # 선언의 오류가 본문의 게이트를 가린다 — er3 을 C# 2 로 내린 거절이
    # 다섯뿐인 까닭을 작은 파일로
    ctx.cs(EX + 'erstage')
    ctx.cs(EX + 'erstage', v='2', expect=1)
    ctx.cs(EX + 'erstage', v='2', flags='-define:DECL', tag='decl', expect=1)
    today(ctx)
    keywords(ctx)
    # 5장에 싣는 캡처 — 진단 줄이 짧은 것만
    ctx.cs(EX + 'kwold', v='14.0', flags='-define:VAR -warn:7', tag='var7')
    ctx.cs(EX + 'kwnew', v='9.0', flags='-define:RECORD', tag='record')
    ctx.cs(EX + 'kwnew', v='10.0', flags='-define:REQUIRED', tag='required')
    ctx.cs(EX + 'kwnew', v='11.0', flags='-define:REQUIRED', tag='required',
           expect=1)
    ctx.cs(EX + 'kwnew', v='13.0', flags='-define:FIELD', tag='field')
    # @ 를 붙여 옛 이름을 지킨다 — 기본 수준과 -warn:7
    ctx.cs(EX + 'cpat')
    ctx.cs(EX + 'cpat', flags='-warn:7', tag='w7')
    waves(ctx)
    breaking(ctx)
    doc_tally(ctx)

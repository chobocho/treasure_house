# -*- coding: utf-8 -*-
"""data_check.py — 손으로 쓴 data/*.tsv 의 칸·출처 규칙.

(make data-check 가 부른다.)

    python3 tools/data_check.py            # 표 전부
    python3 tools/data_check.py law.tsv    # 표 하나

이 덱에서 가장 틀리기 쉬운 것은 코드가 아니라 날짜·대수·조문이다
(PLAN.md §0.3–§0.5). 표에 들어온 사실은 덱의 TABLE 과 claims 검사가
그대로 믿으므로, 기억에서 나온 행은 여기서 막는다:

  - 칸 이름이 정확히 맞는가, 필수 칸이 비지 않았는가
  - source 가 cite_keys.tsv 의 키이거나 https:// 주소인가 —
    위키백과는 출처가 아니다(그 글이 인용한 문서를 적는다)
  - 날짜가 YYYY / YYYY-MM / YYYY-MM-DD 인가 (달력에 있는 날인가)
  - 종류 칸이 정해진 값 가운데 하나인가
  - 2025년 이후 행, 그리고 '지금 상태' 표(법령·펌웨어·도구)의 모든
    행은 verified-how 가 'fetched 날짜' 나 'websearch 날짜' 로
    시작하는가 — 지식 한계 뒤의 사실은 받은 글로만 쓴다(§0.5)
  - 법령 행의 조문 번호가 받아 둔 법령 글(docs/)에 진짜 있는가,
    verified-how 에 'docs §제목' 을 적었으면 그 제목 줄이 있는가

행 수가 최소에 못 미치면 경고만 한다('(미달)') — 연표·쇼·제품 표는
8단계에서 채우므로 그 전에도 이 검사를 돌릴 수 있어야 한다.
오류가 하나라도 있으면 끝 코드 1.

시간 O(표의 행 수 × 출처 수 + 인용한 문서 크기). 문서는 한 번 읽는다.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BASE, 'deck'))
import cites                                            # noqa: E402

UNKNOWN = '미확인'
TL_KINDS = ('military', 'hobby', 'multirotor', 'consumer', 'racing',
            'delivery', 'show', 'law')


def _t(cols, **kw):
    """표 규칙 하나. kinds 는 칸 → 허용 값, date 는 날짜 칸 이름."""
    d = {'cols': tuple(cols.split()), 'kinds': {}, 'date': None,
         'year_only': False, 'current': False, 'minimum': 0,
         'unknown_ok': (), 'ints': (), 'article': None}
    d.update(kw)
    return d


# 표 이름 → 규칙. current=True 는 '지금 상태' 를 적는 표라 모든 행에
# 받은 날이 있어야 한다(법령 조문·라이선스·제품 기능은 바뀐다).
TABLES = {
    'law.tsv': _t(
        'jurisdiction rule article requirement(ko) source verified-how',
        kinds={'jurisdiction': ('KR', 'US', 'EU')}, current=True,
        minimum=40, article='article'),
    'firmware.tsv': _t(
        'project first-release licence language attitude-representation'
        ' source verified-how', date='first-release', current=True,
        minimum=7,
        unknown_ok=('first-release', 'attitude-representation')),
    'tools_show.tsv': _t(
        'tool vendor kind open-source file-formats notes(ko) source'
        ' verified-how',
        kinds={'kind': ('design', 'server', 'live', 'sim', 'hardware'),
               'open-source': ('yes', 'no', 'partial')},
        current=True, minimum=12),
    'timeline.tsv': _t(
        'date event(ko) kind source verified-how', date='date',
        kinds={'kind': TL_KINDS}, minimum=220),
    'shows.tsv': _t(
        'date place organiser drone-count record source verified-how',
        date='date', kinds={'record': ('Guinness', 'claimed', 'none')},
        ints=('drone-count',), minimum=60),
    'products.tsv': _t(
        'year maker product class notable-for(ko) source verified-how',
        date='year', year_only=True, minimum=80),
    'quotes.tsv': _t('quote(en) who where date source', date='date'),
}
ORDER = ('law.tsv', 'firmware.tsv', 'tools_show.tsv', 'timeline.tsv',
         'shows.tsv', 'products.tsv', 'quotes.tsv')

DATE = re.compile(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$')
MDAYS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
VERIFIED = re.compile(r'^(fetched|websearch) \d{4}-\d{2}-\d{2}(\b|$)')
WIKI = re.compile(r'^https://[^/]*\bwikipedia\.org(/|$)')
QUOTED = re.compile(r'docs §(.+)$')
KR_ART = re.compile(r'^제\d+조(의\d+)?$')
CFR_ART = re.compile(r'^§(\d+\.\d+)$')


# ------------------------------------------------------------ 칸 하나
def valid_date(s, year_only=False):
    """YYYY | YYYY-MM | YYYY-MM-DD 이고 달력에 있는 날인가."""
    m = DATE.match(s or '')
    if not m:
        return False
    y, mo, d = m.groups()
    if year_only:
        return mo is None
    if mo is None:
        return True
    mo = int(mo)
    if not 1 <= mo <= 12:
        return False
    if d is None:
        return True
    d = int(d)
    leap = int(y) % 4 == 0 and (int(y) % 100 != 0 or int(y) % 400 == 0)
    last = MDAYS[mo - 1] if mo != 2 else (29 if leap else 28)
    return 1 <= d <= last


def is_wikipedia(url):
    """위키백과(어느 언어·모바일이든) 주소인가."""
    return bool(WIKI.match(url or ''))


def source_problem(src, keys):
    """출처 칸이 괜찮으면 None, 아니면 까닭. ';' 로 여럿을 적는다."""
    parts = [p.strip() for p in (src or '').split(';')]
    if not any(parts):
        return 'source 칸이 비었다'
    for p in parts:
        if p.startswith('https://'):
            if is_wikipedia(p):
                return ('source %s — 위키백과는 출처가 아니다 '
                        '(그 글이 인용한 문서를 적을 것)' % p)
        elif p.startswith('http://'):
            return 'source %s — https:// 주소만 받는다' % p
        elif p not in keys:
            return 'source %s — cite_keys.tsv 에 없는 키' % p
    return None


def verified_ok(s):
    """'fetched YYYY-MM-DD' 나 'websearch YYYY-MM-DD' 로 시작하는가."""
    return bool(VERIFIED.match(s or ''))


def _heads(text):
    return set(ln[2:] for ln in text.split('\n')
               if ln.startswith('§\t'))


def article_in_text(article, text):
    """조문 번호가 받은 글에 있는가.

    한국 법령 '제N조(의M)' 은 '§ 제N조' 제목 줄이, CFR '§N.M' 은
    '§ #N.M' 줄이 정확히 있어야 한다 — 제131조의2 만 있는데 제131조
    가 통과하면 안 되기 때문이다. 그 밖(EU 'Article 4',
    'UAS.OPEN.020')은 본문에서 찾되, 뒤에 숫자·'.숫자'·'의' 가 이어지면
    다른 조문이므로 받지 않는다(Article 4 ≠ Article 40).
    """
    article = (article or '').strip()
    if not article:
        return False
    if KR_ART.match(article):
        return article in _heads(text)
    m = CFR_ART.match(article)
    if m:
        return '#' + m.group(1) in _heads(text)
    pat = re.compile(re.escape(article) + r'(?![0-9의]|\.[0-9])')
    return bool(pat.search(text))


# ------------------------------------------------------------ 표 하나
class Result(object):
    """표 하나의 검사 결과 — 오류는 끝 코드를, 경고는 안내만 바꾼다."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.rows = 0


def _read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def _doc_text(base, keys, key, cache):
    """키의 docs/ 글. 없으면 None."""
    f = keys.get(key, {}).get('file')
    if not f:
        return None
    p = os.path.join(base, 'docs', f)
    if p not in cache:
        cache[p] = _read(p) if os.path.exists(p) else None
    return cache[p]


def _check_law(base, keys, row, where, res, cache):
    """조문 번호와 'docs §제목' 을 인용한 법령 글에서 찾는다."""
    srcs = [s.strip() for s in row['source'].split(';')
            if s.strip() in keys]
    if not srcs:
        return                     # 주소 출처 — 대조할 받은 글이 없다
    texts = []
    for s in srcs:
        t = _doc_text(base, keys, s, cache)
        if t is None:
            res.errors.append('%s docs/%s 가 없다 (make docs)'
                              % (where, keys[s].get('file')))
            return
        texts.append(t)
    art = row['article']
    if not any(article_in_text(art, t) for t in texts):
        res.errors.append('%s 조문 %s 가 %s 의 받은 글에 없다'
                          % (where, art, ', '.join(srcs)))
    m = QUOTED.search(row.get('verified-how', ''))
    if m:
        head = m.group(1).strip()
        if not any(head in _heads(t) for t in texts):
            res.errors.append('%s verified-how 의 제목 §%s 가 '
                              '받은 글의 § 줄에 없다'
                              % (where, head))


def _check_row(base, keys, spec, row, where, res, cache):
    cols = spec['cols']
    vh = row.get('verified-how')
    for c in cols:
        if c != 'verified-how' and not row[c]:
            res.errors.append('%s %s 칸이 비었다' % (where, c))
    for c, allowed in spec['kinds'].items():
        if row[c] and row[c] not in allowed:
            res.errors.append('%s %s=%s — 허용: %s'
                              % (where, c, row[c], '|'.join(allowed)))
    for c in spec['ints']:
        if row[c] and not re.match(r'^[1-9]\d*$', row[c]):
            res.errors.append('%s %s=%s — 자연수만(쉼표 없이)'
                              % (where, c, row[c]))
    unknown = [c for c in spec['unknown_ok'] if row[c] == UNKNOWN]
    if unknown and UNKNOWN not in (vh or ''):
        res.errors.append('%s %s 가 미확인인데 verified-how 에 '
                          '그 까닭(미확인)이 없다'
                          % (where, ', '.join(unknown)))
    dc = spec['date']
    recent = False
    if dc and row[dc] and not (dc in spec['unknown_ok']
                               and row[dc] == UNKNOWN):
        if not valid_date(row[dc], spec['year_only']):
            res.errors.append('%s %s=%s — %s' % (
                where, dc, row[dc],
                'YYYY' if spec['year_only']
                else 'YYYY | YYYY-MM | YYYY-MM-DD'))
        else:
            recent = int(row[dc][:4]) >= 2025
    if row['source']:
        why = source_problem(row['source'], keys)
        if why:
            res.errors.append('%s %s' % (where, why))
    if vh is not None and (spec['current'] or recent):
        if not verified_ok(vh):
            res.errors.append(
                '%s verified-how=%r — %s 행은 "fetched YYYY-MM-DD" 나 '
                '"websearch YYYY-MM-DD" 로 시작해야 한다'
                % (where, vh, '2025년 이후' if recent else '지금 상태'))
    if spec['article'] and row[spec['article']]:
        _check_law(base, keys, row, where, res, cache)


def check_table(base, name):
    """data/<name> 하나를 본다. O(행 수 × 출처 수)."""
    res = Result()
    spec = TABLES[name]
    p = os.path.join(base, 'data', name)
    if not os.path.exists(p):
        res.errors.append('data/%s 가 없다' % name)
        return res
    keys = cites.index(base)
    cache = {}
    head = None
    for n, line in enumerate(_read(p).split('\n'), 1):
        if not line.strip() or line.startswith('#'):
            continue
        cells = [c.strip() for c in line.split('\t')]
        where = '%s:%d' % (name, n)
        if head is None:
            head = tuple(cells)
            if head != spec['cols']:
                res.errors.append('%s 칸 이름이 %s 가 아니다'
                                  % (where, ' | '.join(spec['cols'])))
                return res
            continue
        res.rows += 1
        if len(cells) != len(head):
            res.errors.append('%s 칸 수 %d — %d 이어야 한다'
                              % (where, len(cells), len(head)))
            continue
        _check_row(base, keys, spec, dict(zip(head, cells)), where, res,
                   cache)
    if head is None:
        res.errors.append('data/%s 에 칸 이름 줄이 없다' % name)
    if res.rows < spec['minimum']:
        res.warnings.append('%s %d행 / 최소 %d (미달)'
                            % (name, res.rows, spec['minimum']))
    return res


def main(argv, base=BASE, out=sys.stdout):
    names = argv or list(ORDER)
    bad = 0
    for name in names:
        if name not in TABLES:
            out.write('  모르는 표: %s\n' % name)
            bad += 1
            continue
        r = check_table(base, name)
        mark = ' (미달)' if r.warnings else ''
        out.write('  %-15s %4d행  오류 %d%s\n'
                  % (name, r.rows, len(r.errors), mark))
        for e in r.errors:
            out.write('    ! %s\n' % e)
        bad += len(r.errors)
    verdict = '오류 %d건' % bad if bad else '통과'
    out.write('  data-check: %s\n' % verdict)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

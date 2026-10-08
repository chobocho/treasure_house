# -*- coding: utf-8 -*-
"""make_data.py — docs/ 의 공식 문서에서 data/ 의 생성 표를 만들고 검사한다.

    python3 tools/make_data.py           # make data — 생성 표를 다시 쓴다
    python3 tools/make_data.py --check   # make data-check — 대조만

만드는 표 (손으로 고치지 않는다 — PLAN.md §1):
  langgates.tsv  MessageID | 기능 이름 | 필요한 언어 버전
                 ← docs/roslyn/MessageID.cs 의 RequiredVersion() 스위치와
                   CSharpResources.resx 의 기능 이름(오류 메시지에 찍히는 글자)
  dotnet.tsv     제품 | 버전 | GA 날짜 | 출처   ← docs/releases/<채널>.json
                 (.NET Framework 1.0–4.8.1 은 손으로 쓰는 dotnet_fx.tsv 가 맡는다)
  cite_keys.tsv  인용 키 | 배지 이름 | docs/ 파일   ← docs/FETCHED.txt 의 경로
  releases.tsv   버전 | 나온 달 | VS | .NET | 출처
                 ← 버전 기록의 'C# version N' + '*Released Month YYYY*' 와
                   Language-Version-History 의 'C# N - .NET X and Visual Studio Y'
                 (PLAN.md §1 은 손으로 쓰는 표라 했지만, 두 문서에서 기계로
                 옮길 수 있어 생성 표로 바꿨다 — 손으로 옮기면 한 칸씩 틀린다)

게이트 표가 이 덱의 바닥 증거다. "records 는 C# 9" 는 사람의 기억도 문서의
산문도 아니고, 설치된 컴파일러와 같은 커밋의 RequiredVersion() 이 내는 답이다.
버전은 return 줄에서 읽는다 — 소스 주석은 틀릴 수 있다(2026-10-01 에 받은
판은 C# 14 묶음 위에도 "C# 13.0 features" 라고 적혀 있다).

--check 는 생성 표를 다시 만들어 파일과 같은지 보고, 사람이 쓰는
data/features/pNN.tsv 를 검사한다: 버전이 releases.tsv 에 있는가, kind 가
여섯 가지 가운데 하나인가, 인용(키·절)이 docs/ 에 진짜 있는가, msgid 칸이
있으면 그 게이트의 버전이 행의 버전과 같은가, id·slide-id 가 겹치지 않는가.
**기억으로 적은 버전이 여기서 걸린다.**

시간 O(문서 크기).
"""
import io
import json
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DOCS = os.path.join(BASE, 'docs')
DATA = os.path.join(BASE, 'data')
sys.path.insert(0, os.path.join(BASE, 'deck'))
import cites                                            # noqa: E402

KINDS = ('lang', 'runtime', 'compiler', 'library', 'ecosystem', 'platform')


def read(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return f.read()


def vkey(v):
    """'7.3' → (7, 3), '14' → (14,). 버전 차례로 줄 세울 때."""
    return tuple(int(x) for x in v.split('.'))


def enum_version(name):
    """'CSharp7_3' → '7.3', 'CSharp9' → '9' (끝의 .0 없는 꼴, cites.vnorm)."""
    return name[len('CSharp'):].replace('_', '.')


# ---------------------------------------------------------------- 게이트
CASE = re.compile(r'^\s*case MessageID\.(\w+)\s*:')
RET = re.compile(r'^\s*return LanguageVersion\.(CSharp\d+(?:_\d+)?)\s*;')
RESX = re.compile(r'<data name="(\w+)"[^>]*>\s*<value>([^<]*)</value>', re.S)


def langgates(msgid_text, resx_text):
    """→ [(MessageID, 기능 이름, 버전)] 버전·이름 차례. O(파일 줄 수).

    RequiredVersion() 안에서 case 줄을 모으다가 return 줄을 만나면 그
    버전을 붙인다. 주석 처리된 return(//return LanguageVersion.Preview)은
    정규식이 '^\\s*return' 이라 안 걸린다."""
    # resx 는 XML 이라 &lt;switch expression&gt; 처럼 엔티티로 담는다. 표 생성기가 다시
    # 이스케이프하므로 여기서 풀어 둬야 화면에 컴파일러가 찍는 글자 그대로 나온다.
    names = dict((k, html.unescape(v.strip())) for k, v in RESX.findall(resx_text))
    lines = msgid_text.split('\n')
    start = next((i for i, l in enumerate(lines)
                  if 'LanguageVersion RequiredVersion(' in l), None)
    if start is None:
        return []
    rows, pending = [], []
    for line in lines[start:]:
        m = CASE.match(line)
        if m:
            pending.append(m.group(1))
            continue
        m = RET.match(line)
        if m:
            v = enum_version(m.group(1))
            rows += [(p, names.get(p, ''), v) for p in pending]
            pending = []
        elif line.strip().startswith('default:'):
            break
    return sorted(rows, key=lambda r: (vkey(r[2]), r[0]))


# ---------------------------------------------------------------- 버전 표
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
HIST_HEAD = re.compile(r'^§\tC# version (\d+(?:\.\d+)?)$')
HIST_DATE = re.compile(r'^\*Released (%s) (\d{4})\*$' % '|'.join(MONTHS))
LVH_HEAD = re.compile(r'^§\tC# (\d+(?:\.\d+)?) - (?:(\.NET[^§]*?) and )?'
                      r'(Visual Studio.*)$')


def releases_rows(hist, lvh):
    """버전 기록(이름·나온 달) + Language-Version-History(VS·.NET 짝) →
    [(버전, YYYY-MM, VS, .NET, 출처)] 버전 차례. 버전 이름은 버전 기록의
    표기 그대로('8.0', '9'). 버전 기록에 없는 것(아직 안 나온 C# 15)은 뺀다.
    O(문서 줄 수)."""
    pair = {}
    for line in lvh.split('\n'):
        m = LVH_HEAD.match(line)
        if m:
            pair[cites.vnorm(m.group(1))] = (m.group(3), m.group(2) or '')
    rows, cur = [], None
    for line in hist.split('\n'):
        m = HIST_HEAD.match(line)
        if m:
            cur = m.group(1)
            continue
        m = HIST_DATE.match(line.strip())
        if m and cur:
            vs, net = pair.get(cites.vnorm(cur), ('', ''))
            rows.append((cur, '%s-%02d' % (m.group(2),
                                           MONTHS.index(m.group(1)) + 1),
                         vs, net, 'history·lvh'))
            cur = None
    return sorted(rows, key=lambda r: vkey(r[0]))


# ---------------------------------------------------------------- .NET
def product_name(channel):
    """채널 → (제품 이름, 표기 버전). 5.0 부터 'Core' 를 뗐다."""
    if vkey(channel) >= (5, 0):
        return '.NET', cites.vnorm(channel)
    return '.NET Core', channel


PUBLISHED = re.compile(r'article:published_time"\s+content="(\d{4}-\d\d-\d\d)')


def raw_announcement(major):
    """devblogs 의 "Announcing .NET N" 원본 HTML(docs/raw/blog/…), 없으면 None."""
    p = os.path.join(DOCS, 'raw', 'blog', 'announcing-dotnet-%s.txt' % major)
    return read(p) if os.path.exists(p) else None


def reissued(r):
    """x.y.0 항목이 뒤의 재배포로 덮였는가 — 대표 SDK 가 그 항목의 첫 SDK
    (가장 낮은 판)가 아니면 날짜도 재배포 날이다. 9.0.json 의 9.0.0 이
    그렇다(2024-12-03, SDK 9.0.101)."""
    sdks = [s.get('version', '') for s in r.get('sdks') or []]
    main = (r.get('sdk') or {}).get('version')
    if len(sdks) < 2 or not main:
        return False
    return main != min(sdks, key=lambda v: [int(x) for x in
                                            re.findall(r'\d+', v)])


def ga_row(channel, data, src, announce=raw_announcement):
    """채널의 releases.json → GA(x.y.0) 행, 아직 안 나왔으면 None.

    재배포로 날짜가 덮인 항목은 발표 글의 게시일을 쓰고 출처도 그 글로
    적는다. 발표 글을 안 받았으면 멈춘다 — 틀린 날을 조용히 싣지 않게.
    """
    want = channel + '.0'
    for r in data.get('releases', []):
        if r.get('release-version') == want:
            prod, ver = product_name(channel)
            if not reissued(r):
                return (prod, ver, r['release-date'], src)
            major = channel.split('.')[0]
            m = PUBLISHED.search(announce(major) or '')
            if not m:
                sys.exit('make_data: %s 의 %s 은 재배포로 날짜가 덮였다(%s) — '
                         'tools/fetch_docs.py BLOGS 에 announcing-dotnet-%s 를 '
                         '더하고 받을 것' % (src, want, r['release-date'], major))
            return (prod, ver, m.group(1), 'blog/announcing-dotnet-%s.txt' % major)
    return None


def dotnet_rows():
    out = []
    d = os.path.join(DOCS, 'releases')
    for name in sorted(os.listdir(d), key=lambda n: vkey(n[:-5])):
        if not name.endswith('.json'):
            continue
        row = ga_row(name[:-5], json.loads(read(os.path.join(d, name))),
                     'releases/' + name)
        if row:
            out.append(row)
    return out


# ---------------------------------------------------------------- 인용 키
NAMES = {
    'history': 'C# 버전 기록 (The history of C#)',
    'lvh': 'csharplang Language-Version-History',
    'msgid': 'Roslyn MessageID.cs (SDK 10.0.112 의 커밋)',
    'langversion': 'Roslyn LanguageVersion.cs (SDK 10.0.112 의 커밋)',
    'ecma-334': 'ECMA-334 표준 페이지',
    'std-readme': 'C# 표준 저장소 README',
    'whatsnew-relationships': '언어와 라이브러리의 관계',
    'whatsnew-version-update': '언어 버전 갱신 고려 사항',
    'whatsnew-breaking': 'C# 의 깨지는 변경',
}


# <title> 이 없는 역사 문서(웹 아카이브의 옛 페이지)는 본문 첫 제목에서 손으로 옮긴다.
HIST_NAMES = {
    'ms-truth-about-delegates': 'Microsoft 기술 문서 “The Truth about Delegates”',
    'sun-about-delegates': 'Sun 백서 “About Microsoft\'s "Delegates"”',
}


def hist_name(stem, titles, paths):
    """역사 문서의 배지 이름. 받은 <title> 에서 사이트 꼬리('- Source',
    '| Microsoft Learn', Computerworld 의 검색어 꼬리)를 떼고 출처를 앞에 단다.
    Computerworld 연재는 쪽마다 제목이 같아 'N/전체쪽' 을 붙여야 줄이 갈린다."""
    if stem in HIST_NAMES:
        return HIST_NAMES[stem]
    t = titles.get('history/' + stem, stem)
    m = re.match(r'artima - (.+)$', t)
    if m:
        return 'Artima 인터뷰 “%s”' % m.group(1)
    m = re.match(r'(cw-.+)-(\d+)$', stem)
    if m:
        total = sum(1 for q in paths
                    if re.match(r'history/%s-\d+\.txt$' % re.escape(m.group(1)), q))
        head = t.split(' - ')[0]     # 뒤는 검색어 꼬리와 사이트 이름
        return 'Computerworld 인터뷰 “%s” %s/%d쪽' % (head, m.group(2), total)
    m = re.match(r'(.+?)\s+-\s+Source$', t)
    if m:
        return 'Microsoft 보도자료 “%s”' % m.group(1)
    m = re.match(r'(.+?)\s+\|\s+Microsoft Learn$', t)
    if m:
        return 'Microsoft Learn “%s”' % m.group(1)
    return t


def cite_keys(paths, titles):
    """FETCHED 의 경로들 → [(키, 이름, 파일)] 키 차례."""
    rows = []
    for p in paths:
        if p.startswith('raw/'):
            continue
        m = re.match(r'whatsnew/csharp-(\d+(?:-\d+)?)\.txt$', p)
        if m:
            v = m.group(1).replace('-', '.')
            rows.append(('whatsnew-' + v, "What's new in C# %s" % v, p))
            continue
        m = re.match(r'whatsnew/(.+)\.txt$', p)
        if m:
            key = {'csharp-version-history': 'history',
                   'relationships-between-language-and-library':
                       'whatsnew-relationships',
                   'version-update-considerations': 'whatsnew-version-update',
                   'breaking-changes': 'whatsnew-breaking'}.get(m.group(1),
                                                               m.group(1))
            rows.append((key, NAMES.get(key, key), p))
            continue
        m = re.match(r'csharplang/proposals/csharp-(\d+\.\d+)/(.+)\.txt$', p)
        if m:
            key = 'prop-%s-%s' % (cites.vnorm(m.group(1)),
                                  m.group(2).replace('/', '-'))
            rows.append((key, 'C# %s 기능 명세 %s' % (cites.vnorm(m.group(1)),
                                                    m.group(2)), p))
            continue
        m = re.match(r'history/(.+)\.txt$', p)
        if m:
            rows.append(('hist-' + m.group(1),
                         hist_name(m.group(1), titles, paths), p))
            continue
        m = re.match(r'standard/(.+)\.txt$', p)
        if m:
            rows.append(('std-' + m.group(1),
                         'C# 표준 초안 %s.md' % m.group(1), p))
            continue
        m = re.match(r'blog/(.+)\.txt$', p)
        if m:
            rows.append(('blog-' + m.group(1),
                         'devblogs “%s”' % titles.get(m.group(1), m.group(1)),
                         p))
            continue
        m = re.match(r'releases/(.+)\.json$', p)
        if m:
            rows.append(('rel-' + m.group(1),
                         '.NET %s releases.json' % m.group(1), p))
            continue
        fixed = {'csharplang/Language-Version-History.txt': 'lvh',
                 'roslyn/MessageID.cs': 'msgid',
                 'roslyn/LanguageVersion.cs': 'langversion',
                 'ecma-334.txt': 'ecma-334',
                 'csharpstandard/README.txt': 'std-readme',
                 'releases-index.json': 'rel-index'}
        if p in fixed:
            rows.append((fixed[p], NAMES.get(fixed[p], fixed[p]), p))
            continue
        m = re.match(r'roslyn/(.+)\.txt$', p)
        if m:
            rows.append(('roslyn-' + m.group(1).lower(),
                         'Roslyn 문서 ' + m.group(1).replace('-', ' '), p))
            continue
        if p.endswith('.cs'):
            continue
        rows.append((p.rsplit('.', 1)[0], p, p))
    return sorted(rows)


def blog_titles():
    """docs/raw/blog/<slug>.txt(받은 HTML)의 <title> — 배지 이름에 쓴다.
    본문의 첫 제목은 글의 첫 소제목('Out variables')이라 쓸 수 없다.
    devblogs 의 꼬리(' - .NET Blog')는 뗀다."""
    import html
    out = {}
    for sub, pre in (('blog', ''), ('history', 'history/')):
        d = os.path.join(DOCS, 'raw', sub)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            m = re.search(r'<title>(.*?)</title>', read(os.path.join(d, name)),
                          re.S)
            if m:
                t = html.unescape(re.sub(r'\s+', ' ', m.group(1))).strip()
                t = re.sub(r'\s+-\s+\.NET Blog$', '', t)
                out[pre + name[:-4]] = t
    return out


# ---------------------------------------------------------------- features
def check_features(base, rows):
    """features/pNN.tsv 의 행들({칸: 값}) → 틀린 것마다 한 줄."""
    versions = set(cites.vnorm(r['version'])
                   for r in cites._rows(base, 'releases.tsv'))
    gates = dict((r['msgid'], cites.vnorm(r['required-version']))
                 for r in cites._rows(base, 'langgates.tsv'))
    bad, ids, sids = [], {}, {}
    for r in rows:
        rid, v, kind = r.get('id', ''), r.get('version', ''), r.get('kind', '')
        key, sec = r.get('cite-key', ''), r.get('cite-sec', '')
        where = '%s %s' % (r.get('_file', 'features'), rid)
        ids[rid] = ids.get(rid, 0) + 1
        sid = r.get('slide-id', '')
        if sid:
            sids[sid] = sids.get(sid, 0) + 1
        if cites.vnorm(v) not in versions:
            bad.append('%s: 버전 %s 가 releases.tsv 에 없다' % (where, v))
        if kind not in KINDS:
            bad.append('%s: kind %r 는 %s 가운데 하나가 아니다'
                       % (where, kind, '·'.join(KINDS)))
        why = cites.resolve(base, key, sec)
        if why:
            bad.append('%s: %s' % (where, why))
        mid = r.get('msgid', '')
        if mid:
            if mid not in gates:
                bad.append('%s: msgid %s 가 langgates.tsv 에 없다'
                           % (where, mid))
            elif gates[mid] != cites.vnorm(v):
                bad.append('%s: 버전 %s 인데 컴파일러 게이트(%s)는 C# %s'
                           % (where, v, mid, gates[mid]))
    for k, n in sorted(ids.items()):
        if n > 1:
            bad.append('features: id %s 가 %d번' % (k, n))
    for k, n in sorted(sids.items()):
        if n > 1:
            bad.append('features: slide-id %s 가 %d번' % (k, n))
    return bad


# ---------------------------------------------------------------- 파일
def tsv(comment, head, rows):
    return ('# %s\n' % comment + '\t'.join(head) + '\n'
            + ''.join('\t'.join(r) + '\n' for r in rows))


def build():
    """{data/ 파일 이름: 내용}. docs/ 가 없으면 None."""
    if not os.path.exists(os.path.join(DOCS, 'FETCHED.txt')):
        return None
    fetched = [l.split('\t')[0] for l in
               read(os.path.join(DOCS, 'FETCHED.txt')).split('\n')
               if l and not l.startswith('#')]
    gates = langgates(read(os.path.join(DOCS, 'roslyn', 'MessageID.cs')),
                      read(os.path.join(DOCS, 'roslyn',
                                        'CSharpResources.resx')))
    gen = '생성 표 — tools/make_data.py 가 %s 에서 만든다. 손으로 고치지 말 것.'
    return {
        'releases.tsv': tsv(gen % 'docs/whatsnew/csharp-version-history.txt'
                            '(이름·나온 달)과 docs/csharplang/'
                            'Language-Version-History.txt(VS·.NET 짝)',
                            ['version', 'date', 'vs', 'framework', 'source'],
                            releases_rows(
                                read(os.path.join(DOCS, 'whatsnew',
                                     'csharp-version-history.txt')),
                                read(os.path.join(DOCS, 'csharplang',
                                     'Language-Version-History.txt')))),
        'langgates.tsv': tsv(gen % 'docs/roslyn/MessageID.cs·'
                             'CSharpResources.resx(SDK 10.0.112 의 커밋)',
                             ['msgid', 'feature', 'required-version'], gates),
        'dotnet.tsv': tsv(gen % 'docs/releases/<채널>.json(dotnet/core)',
                          ['product', 'version', 'date', 'source'],
                          dotnet_rows()),
        'cite_keys.tsv': tsv(gen % 'docs/FETCHED.txt 와 블로그 제목',
                             ['key', 'name', 'file'],
                             cite_keys(fetched, blog_titles())),
    }


def main(argv):
    made = build()
    if made is None:
        print('  docs/ 가 없다 — make docs 먼저 (PLAN.md §4 2단계)')
        return 1
    if '--check' not in argv:
        for name, text in sorted(made.items()):
            with io.open(os.path.join(DATA, name), 'w', encoding='utf-8',
                         newline='\n') as f:
                f.write(text)
        print('data/ — 생성 표 %d개: %s' % (len(made), ', '.join(
            '%s %d행' % (n, t.count('\n') - 2) for n, t in sorted(made.items()))))
        return 0
    bad = []
    for name, text in sorted(made.items()):
        p = os.path.join(DATA, name)
        if not os.path.exists(p) or read(p) != text:
            bad.append('data/%s 가 docs/ 와 어긋난다 — make data' % name)
    rows = cites.feature_rows(BASE)
    bad += check_features(BASE, rows)
    for b in bad:
        print('  ✗ ' + b)
    print('자료 검사: 생성 표 %d개 · 기능 목록(data/features/) %d행 — 어긋남 %d건'
          % (len(made), len(rows), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

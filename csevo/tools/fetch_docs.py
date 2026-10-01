# -*- coding: utf-8 -*-
"""fetch_docs.py — C# 의 공식 문서를 docs/ 로 받는다 (make docs).

    python3 tools/fetch_docs.py            # 전부 다시 받는다
    python3 tools/fetch_docs.py --missing  # 없는 것만

이 덱의 두 심판 가운데 하나다(PLAN.md §0.3). 역사에 관한 모든 문장 —
"C# N 에서 X 가 들어왔다", 버전이 나온 달, 설계자의 말 — 은 여기서 받은
문서의 한 줄로 되짚을 수 있어야 한다.

무엇을 받나 (PLAN.md §2):
  · dotnet/docs 의 whats-new — 버전 기록, C# 12–15 페이지, 언어와
    라이브러리의 관계, 버전 갱신 고려 사항, 깨지는 변경. 옛 페이지(C# 6,
    7.x, 8, 9, 10, 11)는 main 에서 지워졌으므로 **지운 커밋의 부모**에서
    받는다(커밋은 2026-10-01 에 GitHub API 로 찾아 아래에 못 박았다).
  · dotnet/csharplang 의 Language-Version-History.md 와 proposals/csharp-N/
    아래의 기능 명세 전부(inactive·rejected 는 빼고). 목록은 코드에 적지
    않고 저장소 트리(API 한 번)에서 읽는다.
  · Roslyn — **설치된 SDK 와 같은 커밋**(dotnet/dotnet VMR 95017c711e)의
    MessageID.cs(기능 → 필요한 언어 버전, 컴파일러 자신의 답),
    LanguageVersion.cs, 기능 상태 문서, 컴파일러의 깨지는 변경 문서들.
  · dotnet/core 의 releases-index.json 과 채널마다의 releases.json(.NET
    Core 1.0 → .NET 11 의 날짜), ECMA-334 페이지, csharpstandard README,
    devblogs 글(BLOGS).

모든 GitHub 원문은 커밋 해시로 고정한다 — main 은 받는 날마다 바뀌고,
인용한 줄이 다음 주에 사라지면 덱의 배지가 근거를 잃는다.

어디에 두나: 원문은 docs/raw/<경로>, 변환한 글은 docs/<경로>. 파일마다
docs/FETCHED.txt 에 '경로 | 주소 | 날짜 | sha256(원문) | 첫 제목' 한 줄.
docs/ 는 커밋하지 않는 캐시다(.gitignore) — FETCHED.txt 만 커밋해
"그날 무엇을 봤는가" 를 남긴다.

남의 서버에 예의를: 요청 사이 0.3초, 실패는 세 번까지 다시. GitHub API 는
인증 없이 시간당 60번이라 트리 한 번만 부른다. O(문서 수) 요청, 합계 수십 MB.
"""
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DOCS = os.path.join(BASE, 'docs')
sys.path.insert(0, HERE)
import html_text                                       # noqa: E402
import md_text                                         # noqa: E402

UA = 'Mozilla/5.0 (treasure_house csevo deck; research)'
RAW = 'https://raw.githubusercontent.com/'

# 2026-10-01 의 각 저장소 머리. 다시 못 박을 때는 PLAN.md 진행 기록에 적는다.
DOCS_SHA = '91cc9093b4a0158adc95b433cb97fcccb1b3db10'      # dotnet/docs
CSLANG_SHA = '93d55a09e48c7f36f312bffe2e5b83e8d18031b1'    # dotnet/csharplang
CORE_SHA = '44927bc821d37f596e317c4316335632bd38c79b'      # dotnet/core
STD_SHA = '107068a0fee88b13e9c46ff64f98343ff29ff8ee'       # csharpstandard
# 설치된 SDK 10.0.112 의 'dotnet --info' 가 적는 커밋(dotnet/dotnet VMR).
# 기능 게이트는 이 커밋의 Roslyn 에서 읽어야 이 기계의 csc 와 같은 답이다.
VMR_SHA = '95017c711e'

WHATSNEW = RAW + 'dotnet/docs/%s/docs/csharp/whats-new/%s.md'
ROSLYN = RAW + 'dotnet/dotnet/%s/src/roslyn/' % VMR_SHA

# main 에서 지워진 whats-new 페이지 → 지운 커밋의 부모 커밋.
# (지운 커밋: 11 1d845f4125 · 10 09e749dd92 · 9 b1838f6e22 · 8 2b52afdb01 ·
#  7 8f8e42895c · 7-1/7-2/7-3 e10155851b(csharp-7.md 로 합침) · 6 83f5cf1e66)
OLD_WHATSNEW = [
    ('csharp-11', '655ed4584ee2a847e878579f39c7e9aecc7607fb'),
    ('csharp-10', '772130226077864743f6da617b1d5f82b539d9e1'),
    ('csharp-9', 'f5cd8d5cb5651b0d34650a51fb7f40e7df4d84aa'),
    ('csharp-8', '9a7439f38d32d7dd399672c06ee4286fd3e1a1e8'),
    ('csharp-7', '265578d6a7bc3c7014af69f54546135279af4d44'),
    ('csharp-7-1', '2a31988ac13f38395e7cfa16e97a9c9ff451db6c'),
    ('csharp-7-2', '2a31988ac13f38395e7cfa16e97a9c9ff451db6c'),
    ('csharp-7-3', '2a31988ac13f38395e7cfa16e97a9c9ff451db6c'),
    ('csharp-6', 'd3acaab7be1b9ddd4d9038bedf49869a0ff88106'),
]
CURRENT_WHATSNEW = ['csharp-version-history', 'csharp-12', 'csharp-13',
                    'csharp-14', 'csharp-15',
                    'relationships-between-language-and-library',
                    'version-update-considerations', 'breaking-changes']

# Roslyn 문서 (VMR 안의 경로) — 컴파일러가 버전마다 일부러 깬 것들.
ROSLYN_DOCS = [
    'docs/Language Feature Status.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - VS2015.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - VS2017.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - post VS2017.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - VS2019.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - post VS2019.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - DotNet 5.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - post DotNet 5.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - DotNet 6.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - DotNet 7.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - DotNet 8.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - DotNet 9.md',
    'docs/compilers/CSharp/Compiler Breaking Changes - DotNet 10.md',
    'docs/compilers/CSharp/Deviations from Standard.md',
    'docs/compilers/CSharp/Warnversion Warning Waves.md',
]
ROSLYN_SRC = [
    ('roslyn/MessageID.cs',
     'src/Compilers/CSharp/Portable/Errors/MessageID.cs'),
    ('roslyn/LanguageVersion.cs',
     'src/Compilers/CSharp/Portable/LanguageVersion.cs'),
    # 기능 이름 — 'Feature 'records' is not available …' 의 'records' 가
    # 여기서 온다(<data name="IDS_FeatureRecords"><value>records</value>).
    ('roslyn/CSharpResources.resx',
     'src/Compilers/CSharp/Portable/CSharpResources.resx'),
]

# 고정 문서: (docs/ 아래 경로, 주소, 종류)
FIXED = [
    ('csharplang/Language-Version-History.txt',
     RAW + 'dotnet/csharplang/%s/Language-Version-History.md' % CSLANG_SHA,
     'md'),
    ('csharpstandard/README.txt',
     RAW + 'dotnet/csharpstandard/%s/README.md' % STD_SHA, 'md'),
    ('ecma-334.txt',
     'https://ecma-international.org/publications-and-standards/standards/'
     'ecma-334/', 'html'),
    ('releases-index.json',
     RAW + 'dotnet/core/%s/release-notes/releases-index.json' % CORE_SHA,
     'json'),
]

# C# 표준(ECMA-334 의 다음 판 초안, csharpstandard 의 standard/) — C# 1–5
# 의 기능은 버전별 문서가 짧아 명세 본문을 근거로 인용한다. 목록은
# 2026-10-01 의 저장소 트리에서 옮겼다.
STANDARD = [
    'README', 'arrays', 'attributes', 'basic-concepts', 'bibliography',
    'classes', 'conformance', 'conversions', 'delegates',
    'documentation-comments', 'enums', 'exceptions', 'expressions',
    'foreword', 'general-description', 'grammar', 'interfaces',
    'introduction', 'lexical-structure', 'namespaces',
    'normative-references', 'patterns', 'portability-issues', 'ranges',
    'scope', 'standard-library', 'statements', 'structs',
    'terms-and-definitions', 'types', 'unsafe-code', 'variables',
]

# 받을 devblogs 글 — devblogs.microsoft.com/dotnet/<꼬리>/. 부를 쓰다
# 인용할 글이 늘면 여기에 더하고 make docs 를 다시 돌린다(2026-10-01 에
# 200 으로 답한 것만 적었다).
BLOGS = [
    'whats-new-in-csharp-7-0', 'new-features-in-c-7-0', 'building-c-8-0',
    'c-9-0-on-the-record', 'welcome-to-csharp-10', 'welcome-to-csharp-11',
    'announcing-csharp-12', 'introducing-csharp-14', 'announcing-dotnet-10',
    'csharp-15-union-types',
]

# 1부(C# 이전)와 버전 부의 "왜" — 공식 문서 밖의 1차 자료. 위키백과는
# 인용하지 않고, 위키백과가 인용한 원자료를 직접 받는다(PLAN.md §0.4).
#   · PDC 2000 — Microsoft Learn 의 행사 페이지(C# 발표·시연, 날짜·장소)
#   · Sun 과의 자바 소송 합의 보도자료(2001-01-23)
#   · Artima "A Conversation with Anders Hejlsberg" 8편(2003) — 설계자 본인의
#     말로 된 설계 이유(가상 메서드 기본값, checked exception, 대리자, 제네릭 …)
HISTORY = [
    ('pdc-2000', 'https://learn.microsoft.com/en-us/shows/pdc-2000/'),
    ('ms-sun-settlement-2001',
     'https://news.microsoft.com/source/2001/01/23/microsoft-reaches-'
     'agreement-to-settle-contract-dispute-with-sun-microsystems/'),
] + [('artima-' + slug, 'https://www.artima.com/articles/' + slug)
     for slug in ('the-c-design-process',
                  'the-trouble-with-checked-exceptions',
                  'delegates-components-and-simplexity',
                  'versioning-virtual-and-override',
                  'contracts-and-interoperability',
                  'inappropriate-abstractions', 'generics-in-c-java-and-c',
                  'clr-design-choices')]
# news.microsoft.com 은 스크립트 같은 UA 를 403 으로 막는다(2026-10-01 확인).
BROWSER_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def ua_for(url):
    return BROWSER_UA if 'news.microsoft.com' in url else UA


TREE_URL = ('https://api.github.com/repos/dotnet/csharplang/git/trees/%s'
            '?recursive=1' % CSLANG_SHA)
PROPOSAL = re.compile(r'^proposals/csharp-\d+\.\d+/.+\.md$')


def proposal_items(tree):
    """csharplang 트리 → 출시(또는 예정) 버전 폴더의 명세 .md 전부.
    inactive·rejected 는 아직(또는 끝내) 언어가 아니다. 경로 차례. O(트리)."""
    paths = sorted(t['path'] for t in tree.get('tree', [])
                   if t.get('type') == 'blob' and PROPOSAL.match(t['path']))
    return [dict(path='csharplang/%s.txt' % p[:-3],
                 url=RAW + 'dotnet/csharplang/%s/%s'
                 % (CSLANG_SHA, urllib.parse.quote(p)), kind='md')
            for p in paths]


def _vkey(v):
    return tuple(int(x) for x in v.split('.'))


def channel_items(index):
    """releases-index.json → 채널마다의 releases.json (같은 커밋의 저장소
    사본 — builds.dotnet 의 주소는 날마다 바뀐다). 버전 차례."""
    chans = sorted((r['channel-version'] for r in index['releases-index']),
                   key=_vkey)
    return [dict(path='releases/%s.json' % c,
                 url=RAW + 'dotnet/core/%s/release-notes/%s/releases.json'
                 % (CORE_SHA, c), kind='json') for c in chans]


def _slug(name):
    return re.sub(r'[^A-Za-z0-9.]+', '-', name).strip('-')


def plan(tree, index):
    """받을 것 전부: [{'path', 'url', 'kind'}]. kind 는 md·html·raw·json."""
    items = [dict(path=p, url=u, kind=k) for p, u, k in FIXED]
    for name in CURRENT_WHATSNEW:
        items.append(dict(path='whatsnew/%s.txt' % name,
                          url=WHATSNEW % (DOCS_SHA, name), kind='md'))
    for name, sha in OLD_WHATSNEW:
        items.append(dict(path='whatsnew/%s.txt' % name,
                          url=WHATSNEW % (sha, name), kind='md'))
    for p, src in ROSLYN_SRC:
        items.append(dict(path=p, url=ROSLYN + src, kind='raw'))
    for d in ROSLYN_DOCS:
        name = _slug(os.path.splitext(os.path.basename(d))[0])
        items.append(dict(path='roslyn/%s.txt' % name,
                          url=ROSLYN + urllib.parse.quote(d), kind='md'))
    for name in STANDARD:
        items.append(dict(path='standard/%s.txt' % name,
                          url=RAW + 'dotnet/csharpstandard/%s/standard/%s.md'
                          % (STD_SHA, name), kind='md'))
    items += proposal_items(tree)
    items += channel_items(index)
    for name, url in HISTORY:
        items.append(dict(path='history/%s.txt' % name, url=url,
                          kind='html'))
    for slug in BLOGS:
        items.append(dict(path='blog/%s.txt' % slug,
                          url='https://devblogs.microsoft.com/dotnet/%s/'
                          % slug, kind='html'))
    return items


def first_heading(text):
    """'§' 제목 줄의 글, 없으면 첫 비지 않은 줄."""
    first = ''
    for line in text.split('\n'):
        if line.startswith('§\t'):
            return line[2:]
        if not first and line.strip():
            first = line.strip()
    return first


def fetched_line(path, url, date, data, head):
    return '\t'.join((path, url, date, hashlib.sha256(data).hexdigest(),
                      head))


def get(url):
    """주소 하나를 받는다. 세 번까지 다시, 30초 제한, 리다이렉트는 따라간다."""
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': ua_for(url),
                'Accept': 'text/html,application/xhtml+xml,*/*'})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except (urllib.error.URLError, OSError) as e:
            last = e
            if isinstance(e, urllib.error.HTTPError) and e.code == 404:
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError('%s — %s' % (url, last))


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def cached(rel, url, missing_only):
    """docs/raw/<rel> 이 있고 --missing 이면 그것을, 아니면 받아서 둔다."""
    p = os.path.join(DOCS, 'raw', rel)
    if missing_only and os.path.exists(p):
        with open(p, 'rb') as f:
            return f.read(), False
    data = get(url)
    save(p, data)
    return data, True


def head_of(path, kind, text):
    if kind == 'json':
        return '%d bytes of JSON' % len(text.encode('utf-8'))
    if path.endswith('.resx'):
        return '%d <data> entries' % text.count('<data name=')
    if path.endswith('.cs'):
        m = re.search(r'^\s*(?:internal|public)?\s*(?:static\s+)?'
                      r'(?:partial\s+)?(?:class|enum)\s+(\w+)', text, re.M)
        return m.group(0).strip() if m else first_heading(text)
    return first_heading(text)


def main(argv):
    missing_only = '--missing' in argv
    today = datetime.date.today().isoformat()
    os.makedirs(DOCS, exist_ok=True)
    tree_raw, _ = cached('csharplang-tree.json', TREE_URL, missing_only)
    idx_raw, _ = cached('releases-index.json', FIXED[3][1], missing_only)
    tree = json.loads(tree_raw.decode('utf-8'))
    if tree.get('truncated'):
        print('  ✗ csharplang 트리가 잘렸다 — 명세 목록이 모자랄 수 있다')
        return 1
    index = json.loads(idx_raw.decode('utf-8'))
    log, bad, n_new = [], [], 0
    log.append(fetched_line('raw/csharplang-tree.json', TREE_URL, today,
                            tree_raw, '%d entries' % len(tree['tree'])))
    for it in plan(tree, index):
        dst = os.path.join(DOCS, it['path'])
        raw_dst = os.path.join(DOCS, 'raw', it['path'])
        if missing_only and os.path.exists(dst) and os.path.exists(raw_dst):
            with open(raw_dst, 'rb') as f:
                data = f.read()
        else:
            try:
                data = idx_raw if it['url'] == FIXED[3][1] else get(it['url'])
            except RuntimeError as e:
                bad.append(str(e))
                continue
            n_new += 1
            time.sleep(0.3)
        text = data.decode('utf-8', 'replace')
        if it['kind'] == 'html':
            text = html_text.convert(text)
        elif it['kind'] == 'md':
            text = md_text.convert(text)
        save(raw_dst, data)
        save(dst, text.encode('utf-8'))
        log.append(fetched_line(it['path'], it['url'], today, data,
                                head_of(it['path'], it['kind'], text)))
    with open(os.path.join(DOCS, 'FETCHED.txt'), 'w', encoding='utf-8',
              newline='\n') as f:
        f.write('# make docs 가 쓴다 — 경로\t주소\t받은 날\tsha256(원문)\t첫 제목\n')
        f.write('\n'.join(log) + '\n')
    for b in bad:
        print('  ✗ ' + b)
    print('docs/ — 문서 %d개 (이번에 받은 것 %d) · 실패 %d · 명세 %d개'
          % (len(log), n_new, len(bad), len(proposal_items(tree))))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

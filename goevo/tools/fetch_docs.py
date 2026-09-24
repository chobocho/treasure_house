# -*- coding: utf-8 -*-
"""fetch_docs.py — Go 의 공식 문서를 docs/ 로 받는다 (make docs).

    python3 tools/fetch_docs.py            # 전부 다시 받는다
    python3 tools/fetch_docs.py --missing  # 없는 것만

이 덱의 두 심판 가운데 하나다(PLAN.md §0.3). 역사에 관한 모든 문장 —
"1.N 에서 X 가 들어왔다", 릴리스 날짜, 설계자의 말 — 은 여기서 받은
문서의 한 줄로 되짚을 수 있어야 한다.

무엇을 받나 (PLAN.md §2):
  · 릴리스 페이지 go.dev/doc/devel/release — 모든 버전과 날짜. 이것을
    **먼저** 받아 큰 릴리스 목록을 읽고, 그 목록대로 노트와 API 목록을
    받는다. 버전 목록을 코드에 적어 두지 않는다 — 기억으로 적은 목록은
    새 릴리스가 나오면 조용히 낡는다.
  · 릴리스 노트 go.dev/doc/go1.N (Go 1 은 go1), 그리고 다음 버전의
    초안(tip.golang.org/doc/go1.<최신+1>) → docs/relnotes/go1.N.txt,
    go1.M-draft.txt
  · API 목록 api/go1.N.txt — 이 기계의 go 와 같은 태그(TAG)에서. 그
    버전이 더한 공개 기호의 정확한 목록이라, "X 는 1.N 에 들어왔다" 의
    바닥 증거다. GOROOT(Termux)에는 api/ 가 없어 받는다.
  · 명세(같은 태그), go1compat, godebug, toolchain, FAQ, 모듈 참조,
    Go 1 이전 기록(pre_go1·weekly), 제안 과정 README, 2012 Splash 발표문,
    블로그 색인과 BLOGS 의 글들, GitHub 태그 목록(tags.json).

어디에 두나: 원문은 docs/raw/<경로>, 변환한 글은 docs/<경로>. 파일마다
docs/FETCHED.txt 에 '경로 | 주소 | 날짜 | sha256(원문) | 첫 제목' 한 줄.
docs/ 는 커밋하지 않는 캐시다(.gitignore) — FETCHED.txt 만 커밋해
"그날 무엇을 봤는가" 를 남긴다.

남의 서버에 예의를: 요청 사이 0.3초, 실패는 세 번까지 다시.
O(문서 수) 요청, 합계 수 MB.
"""
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DOCS = os.path.join(BASE, 'docs')
sys.path.insert(0, HERE)
import html_text                                       # noqa: E402

# 이 기계의 go 와 같은 판. 명세·API 목록을 이 태그에서 받는다 — master 는
# 받는 날마다 바뀐다(2026-09-24: master 의 명세는 "August 7, 2026",
# 태그는 "May 26, 2026" 였다).
TAG = 'go1.27.1'
RAW = 'https://raw.githubusercontent.com/golang/go/%s/' % TAG
UA = 'Mozilla/5.0 (treasure_house goevo deck; research)'

# 고정 문서: (docs/ 아래 경로, 주소, 종류)
FIXED = [
    ('release.txt', 'https://go.dev/doc/devel/release', 'html'),
    ('spec.txt', RAW + 'doc/go_spec.html', 'html'),
    ('go1compat.txt', 'https://go.dev/doc/go1compat', 'html'),
    ('godebug.txt', 'https://go.dev/doc/godebug', 'html'),
    ('toolchain.txt', 'https://go.dev/doc/toolchain', 'html'),
    ('faq.txt', 'https://go.dev/doc/faq', 'html'),
    ('modref.txt', 'https://go.dev/ref/mod', 'html'),
    ('gomod-ref.txt', 'https://go.dev/doc/modules/gomod-ref', 'html'),
    ('pre_go1.txt', 'https://go.dev/doc/devel/pre_go1', 'html'),
    ('weekly.txt', 'https://go.dev/doc/devel/weekly', 'html'),
    ('splash.txt', 'https://go.dev/talks/2012/splash.article', 'html'),
    ('proposal-README.txt',
     'https://raw.githubusercontent.com/golang/proposal/master/README.md',
     'md'),
    ('blog/index.txt', 'https://go.dev/blog/all', 'html'),
]

# 받을 블로그 글 — go.dev/blog/all 의 주소 꼬리. 부를 쓰다 인용할 글이
# 늘면 여기에 더하고 make docs 를 다시 돌린다. 고른 기준: 릴리스 발표,
# 해마다의 생일 글(역사), 설계 결정을 설명한 글.
BLOGS = [
    # 발표·생일
    'hello-world', '1year', '2years', '3years', '4years', '5years',
    '6years', '7years', '8years', '9years', '10years', '11years',
    '12years', '13years', '14years', '15years', '16years',
    'go1-preview', 'go1', 'go1-path', 'stable-releases',
    'go1.1', 'go1.2', 'go1.3', 'go1.4', 'go1.5', 'go1.6', 'go1.7',
    'go1.8', 'go1.9', 'go1.10', 'go1.11', 'go1.12', 'go1.13', 'go1.14',
    'go1.15', 'go1.16', 'go1.17', 'go1.18', 'go1.19', 'go1.20',
    'go1.21', 'go1.22', 'go1.23', 'go1.24', 'go1.25', 'go1.26', 'go1.27',
    # 설계와 변화
    'declaration-syntax', 'introducing-gofix', 'gofmt', 'first-go-program',
    'race-detector', 'cover', 'generate', 'context', 'go15gc',
    'ismmkeynote', 'go119runtime', 'greenteagc', 'go1.7-binary-size',
    'subtests', 'toward-go2', 'go2draft', 'go2-here-we-come',
    'go2-next-steps', 'experiment', 'versioning-proposal', 'modules2019',
    'using-go-modules', 'module-mirror-launch', 'go116-module-changes',
    'v2-go-modules', 'go1.13-errors', 'why-generics', 'generics-next-step',
    'generics-proposal', 'intro-generics', 'when-generics', 'fuzz-beta',
    'get-familiar-with-workspaces', 'supply-chain', 'ports', 'pgo-preview',
    'pgo', 'compat', 'toolchain', 'rebuild', 'slog', 'wasi',
    'loopvar-preview', 'routing-enhancements', 'randv2', 'chacha8rand',
    'generic-slice-functions', 'range-functions', 'unique', 'alias-names',
    'gotelemetry', 'swisstable', 'synctest', 'wasmexport',
    'cleanups-and-weak', 'osroot', 'coretypes', 'testing-b-loop',
    'error-syntax', 'generic-interfaces', 'fips140',
    'container-aware-gomaxprocs', 'testing-time', 'jsonv2-exp',
    'flight-recorder', 'gofix', 'allocation-optimizations', 'inliner',
    'type-construction-and-cycle-detection', 'generic-methods',
    'goroutine-leak-profiles', 'size-specialized-allocations',
    'integration-test-coverage', 'comparable', 'execution-traces-2024',
]

MAJOR = re.compile(r'^§\tgo(1(?:\.\d+)?)(?:\.0)? \(released \d{4}-\d{2}-\d{2}\)',
                   re.M)


def _vkey(v):
    return tuple(int(x) for x in v.split('.'))


def majors(release_txt):
    """릴리스 페이지 텍스트 → 큰 릴리스 ['1', '1.1', …] (버전 차례)."""
    return sorted(set(MAJOR.findall(release_txt)), key=_vkey)


def plan(release_txt):
    """받을 것 전부: [{'path', 'url', 'kind'}]. kind 는 html·md·raw·json."""
    items = [dict(path=p, url=u, kind=k) for p, u, k in FIXED]
    vs = majors(release_txt)
    for v in vs:
        name = 'go1' if v == '1' else 'go' + v
        items.append(dict(path='relnotes/%s.txt' % name,
                          url='https://go.dev/doc/' + name, kind='html'))
        items.append(dict(path='api/%s.txt' % name,
                          url=RAW + 'api/%s.txt' % name, kind='raw'))
    if vs:
        last = _vkey(vs[-1])
        nxt = '%d.%d' % (last[0], last[1] + 1 if len(last) > 1 else 1)
        # go.dev 의 다음 버전 노트는 조각이 비어 있다(2026-09-24). 작업 중인
        # 초안은 master 의 doc/next/ 를 그리는 tip 사이트에만 있다.
        items.append(dict(path='relnotes/go%s-draft.txt' % nxt,
                          url='https://tip.golang.org/doc/go' + nxt,
                          kind='html'))
    for slug in BLOGS:
        items.append(dict(path='blog/%s.txt' % slug,
                          url='https://go.dev/blog/' + slug, kind='html'))
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
    """주소 하나를 받는다. 세 번까지 다시, 20초 제한, 리다이렉트는 따라간다."""
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=20) as r:
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


def tags():
    """GitHub 태그 목록을 쪽마다 받아 하나로. 인증 없이 시간당 60번이라
    쪽 수(대여섯)만큼만 부른다. 날짜는 없다 — 인용하는 태그만 따로 본다."""
    out, page = [], 1
    while True:
        data = get('https://api.github.com/repos/golang/go/tags'
                   '?per_page=100&page=%d' % page)
        rows = json.loads(data.decode('utf-8'))
        if not rows:
            break
        out += [{'name': r['name'], 'sha': r['commit']['sha']} for r in rows]
        page += 1
        time.sleep(0.5)
    return json.dumps(out, indent=1).encode('utf-8')


def main(argv):
    missing_only = '--missing' in argv
    today = datetime.date.today().isoformat()
    os.makedirs(DOCS, exist_ok=True)
    rel = get(FIXED[0][1])
    rel_txt = html_text.convert(rel.decode('utf-8'))
    log, bad, n_new = [], [], 0
    for it in plan(rel_txt):
        dst = os.path.join(DOCS, it['path'])
        raw_dst = os.path.join(DOCS, 'raw', it['path'])
        if missing_only and os.path.exists(dst) and os.path.exists(raw_dst):
            with open(raw_dst, 'rb') as f:
                data = f.read()
        else:
            try:
                data = rel if it['url'] == FIXED[0][1] else get(it['url'])
            except RuntimeError as e:
                bad.append(str(e))
                continue
            n_new += 1
            time.sleep(0.3)
        text = data.decode('utf-8', 'replace')
        if it['kind'] == 'html':
            text = html_text.convert(text)
        elif it['kind'] == 'md':
            text = html_text.convert_md(text)
        save(raw_dst, data)
        save(dst, text.encode('utf-8'))
        log.append(fetched_line(it['path'], it['url'], today, data,
                                first_heading(text)))
    tj = os.path.join(DOCS, 'tags.json')
    if not (missing_only and os.path.exists(tj)):
        data = tags()
        save(tj, data)
        n_new += 1
    with open(tj, 'rb') as f:
        data = f.read()
    log.append(fetched_line('tags.json', 'https://api.github.com/repos/'
                            'golang/go/tags', today, data,
                            '%d tags' % len(json.loads(data.decode()))))
    with open(os.path.join(DOCS, 'FETCHED.txt'), 'w', encoding='utf-8',
              newline='\n') as f:
        f.write('# make docs 가 쓴다 — 경로\t주소\t받은 날\tsha256(원문)\t첫 제목\n')
        f.write('\n'.join(log) + '\n')
    for b in bad:
        print('  ✗ ' + b)
    print('docs/ — 문서 %d개 (이번에 받은 것 %d) · 실패 %d · 큰 릴리스 %d개'
          % (len(log), n_new, len(bad), len(majors(rel_txt))))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

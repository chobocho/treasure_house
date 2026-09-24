# -*- coding: utf-8 -*-
"""make_data.py — docs/ 의 공식 문서에서 data/ 의 생성 표를 만들고 검사한다.

    python3 tools/make_data.py           # make data — 표 넷을 다시 쓴다
    python3 tools/make_data.py --check   # make data-check — 대조만

만드는 표 (손으로 고치지 않는다 — PLAN.md §1, §3.2):
  releases.tsv   버전 | 날짜 | major/minor | 노트 키      ← docs/release.txt
  api_added.tsv  버전 | 새 패키지 수 | 새 기호 수 | 새 패키지  ← docs/api/go1.N.txt
  godebug.tsv    설정 | 패키지 | 처음 적힌 버전 | 기본값 바뀐 버전 | 옛 값
                 ← $GOROOT/src/internal/godebugs/table.go(설치된 go 의 표)
                   + docs/godebug.txt 의 "GODEBUG History" 절
  cite_keys.tsv  인용 키 | 배지 이름 | docs/ 파일   ← docs/FETCHED.txt 의 경로
                 + 블로그 색인의 제목(릴리스 노트·API 목록 키는 releases.tsv 가 맡는다)

GODEBUG 표의 '기본값 바뀐 버전' 은 Go 소스의 표(Changed 칸)가 바닥
증거다 — 문서 산문에서 읽으면 "1.22 에서 바뀌었다 / 1.23 에서 바뀔 것이다"
를 가르지 못한다. '처음 적힌 버전' 은 문서의 버전 절 가운데 그 이름이
나오는 가장 옛 절이다(문서가 역사를 적기 시작한 1.5 앞은 '-').
PLAN.md §1 의 meaning 칸은 두지 않았다 — 뜻은 슬라이드에서 한국어로
풀고, 표에는 기계가 옮길 수 있는 것만 둔다.

--check 는 넷을 다시 만들어 파일과 같은지 보고, 사람이 쓰는
features.tsv 를 검사한다: 버전이 릴리스(또는 초안)에 있는가, kind 가
여섯 가지 가운데 하나인가, 인용(키·절)이 docs/ 에 진짜 있는가, 인용이
노트·API 목록이면 그 버전이 행의 버전과 같은가, 표준 라이브러리 행은
버전 붙은 인용을 달았는가, id·slide-id 가 겹치지 않는가. **기억으로 적은
버전이 여기서 걸린다.**

시간 O(문서 크기), API 목록은 합계 16만 줄 남짓.
"""
import html
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DOCS = os.path.join(BASE, 'docs')
DATA = os.path.join(BASE, 'data')
sys.path.insert(0, os.path.join(BASE, 'deck'))
import cites                                            # noqa: E402

GOROOT_TABLE = '/data/data/com.termux/files/usr/lib/go/src/internal/' \
               'godebugs/table.go'
KINDS = ('lang', 'toolchain', 'runtime', 'stdlib', 'ecosystem', 'platform')

REL = re.compile(r'^(?:§\t)?(go1(?:\.\d+){0,2}) \(released '
                 r'(\d{4}-\d{2}-\d{2})\)', re.M)


def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def vkey(v):
    """'go1.22.0' · '1.22' → (1, 22, 0) · (1, 22). 버전 차례로 줄 세울 때."""
    return tuple(int(x) for x in re.sub(r'^go', '', v).split('.'))


# ---------------------------------------------------------------- releases
def releases(release_txt):
    """릴리스 페이지 텍스트 → [(버전, 날짜, kind, 노트 키)] 버전 차례.

    큰 릴리스는 go1 · go1.N(1.20 까지) · go1.N.0(1.21 부터) 이다.
    같은 버전이 두 번 나오면(색인과 본문) 처음 것 하나만 둔다."""
    seen = {}
    for m in REL.finditer(release_txt):
        v, d = m.group(1), m.group(2)
        if v in seen:
            continue
        parts = vkey(v)
        major = len(parts) == 1 or len(parts) == 2 or parts[2] == 0
        if major:
            ver = '1.0' if parts == (1,) else '%d.%d' % parts[:2]
            seen[v] = (v, d, 'major', 'relnotes-' + ver)
        else:
            seen[v] = (v, d, 'minor', '')
    return sorted(seen.values(), key=lambda r: vkey(r[0]))


# ---------------------------------------------------------------- api
def pkg_of(line):
    """'pkg a/b (goos-arch), func F' → ('a/b', 'func F'). 기호 줄이 아니면 None."""
    m = re.match(r'^pkg ([^\s,]+)(?: \([^)]*\))?, (.*)$', line)
    return (m.group(1), m.group(2)) if m else None


def api_added(files):
    """[(버전, 본문)] (버전 차례) → [(버전, 새 패키지 수, 새 기호 수, 새 패키지)].

    기호는 플랫폼 꼬리를 뗀 (패키지, 선언) 의 가짓수다 — go1.txt 에는
    같은 상수가 운영체제·아키텍처마다 한 줄씩 있다. '//deprecated' 줄은
    더한 것이 아니라 낡았다는 표시라 세지 않는다. 새 패키지는 앞선 어느
    파일에도 없던 경로다. O(줄 수)."""
    seen_pkgs, out = set(), []
    for ver, text in files:
        syms, pkgs = set(), set()
        for line in text.split('\n'):
            if line.rstrip().endswith('//deprecated'):
                continue
            p = pkg_of(line.strip())
            if p:
                syms.add(p)
                pkgs.add(p[0])
        new = sorted(pkgs - seen_pkgs)
        seen_pkgs |= pkgs
        v = '1.0' if ver == '1' else ver
        out.append((v, str(len(new)), str(len(syms)), ', '.join(new)))
    return out


# ---------------------------------------------------------------- godebug
def godebug_rows(table_go, godebug_txt):
    """Go 소스의 설정 표 + 문서 → [(설정, 패키지, 처음 적힌 버전, 바뀐 버전, 옛 값)]."""
    sections, cur = [], None
    in_hist = False
    for line in godebug_txt.split('\n'):
        if line.startswith('§\t'):
            h = line[2:]
            m = re.match(r'^Go (1\.\d+)$', h)
            if m:
                cur = [m.group(1), []]
                sections.append(cur)
                continue
            in_hist = in_hist or h == 'GODEBUG History'
            cur = None
        elif cur is not None:
            cur[1].append(line)
    rows = []
    for m in re.finditer(r'^\s*\{Name: "([^"]+)", Package: "([^"]+)"([^}]*)\}',
                         table_go, re.M):
        name, pkg, rest = m.group(1), m.group(2), m.group(3)
        ch = re.search(r'Changed: (\d+)', rest)
        old = re.search(r'Old: "([^"]*)"', rest)
        word = re.compile(r'(?<![\w])%s(?![\w])' % re.escape(name))
        first = [v for v, body in sections if word.search('\n'.join(body))]
        first = min(first, key=vkey) if first else '-'
        rows.append((name, pkg, first, '1.%s' % ch.group(1) if ch else '-',
                     old.group(1) if old else '-'))
    return rows


# ---------------------------------------------------------------- 인용 키
def blog_titles(index_html):
    """블로그 색인 원문 → {주소 꼬리: (제목, 날짜)}."""
    out = {}
    for m in re.finditer(r'<a href="/blog/([^"]+)">([^<]*)</a>, '
                         r'<span class="date">([^<]*)</span>', index_html):
        out[m.group(1)] = (html.unescape(m.group(2)).strip(), m.group(3))
    return out


NAMES = {
    'spec': 'Go 언어 명세', 'go1compat': 'Go 1 호환성 문서',
    'godebug': 'GODEBUG 문서', 'toolchain': 'Go 툴체인 문서',
    'faq': 'Go FAQ', 'modref': 'Go 모듈 참조', 'gomod-ref': 'go.mod 참조',
    'pre_go1': 'Go 1 이전 릴리스 기록', 'weekly': 'Go 주간 스냅숏 기록',
    'splash': 'Go at Google (2012 SPLASH 발표문)',
    'proposal-README': 'Go 제안 과정 README', 'release': 'Go 릴리스 기록',
}


def cite_keys(paths, titles):
    """FETCHED 의 경로들 → [(키, 이름, 파일)]. 노트·API 키는 releases.tsv 몫."""
    rows = []
    for p in paths:
        if p.startswith('api/') or p == 'blog/index.txt' or \
                not p.endswith('.txt'):
            continue
        m = re.match(r'relnotes/go(1\.\d+)-draft\.txt$', p)
        if m:
            rows.append(('relnotes-' + m.group(1),
                         'Go %s 릴리스 노트(초안)' % m.group(1), p))
            continue
        if p.startswith('relnotes/'):
            continue
        m = re.match(r'blog/(.+)\.txt$', p)
        if m:
            t, d = titles.get(m.group(1), (m.group(1), ''))
            rows.append(('blog-' + m.group(1),
                         'Go 블로그 “%s” (%s)' % (t, d) if d else
                         'Go 블로그 “%s”' % t, p))
            continue
        key = p[:-4]
        rows.append((key, NAMES.get(key, key), p))
    return sorted(rows)


# ---------------------------------------------------------------- features
def check_features(base, rows):
    """features.tsv 의 행들({칸: 값}) → 틀린 것마다 한 줄."""
    majors = set()
    for r in cites._rows(base, 'releases.tsv'):
        if r.get('kind') == 'major':
            majors.add(r['relnotes-key'][len('relnotes-'):])
    keys = cites.index(base)
    majors |= set(k[len('relnotes-'):] for k in keys
                  if k.startswith('relnotes-'))
    bad, ids, sids = [], {}, {}
    for r in rows:
        rid, v, kind = r.get('id', ''), r.get('version', ''), r.get('kind', '')
        key, sec = r.get('cite-key', ''), r.get('cite-sec', '')
        where = '%s %s' % (r.get('_file', 'features.tsv'), rid)
        ids[rid] = ids.get(rid, 0) + 1
        sid = r.get('slide-id', '')
        if sid:
            sids[sid] = sids.get(sid, 0) + 1
        if v not in majors:
            bad.append('%s: 버전 %s 가 releases.tsv·초안에 없다' % (where, v))
        if kind not in KINDS:
            bad.append('%s: kind %r 는 %s 가운데 하나가 아니다'
                       % (where, kind, '·'.join(KINDS)))
        why = cites.resolve(base, key, sec)
        if why:
            bad.append('%s: %s' % (where, why))
        m = re.match(r'(?:relnotes|api)-(1\.\d+)$', key)
        if m and m.group(1) != v:
            bad.append('%s: 버전 %s 인데 인용은 %s (%s) — 어느 쪽이 맞나'
                       % (where, v, m.group(1), key))
        if kind == 'stdlib' and not m:
            bad.append('%s: 표준 라이브러리 행은 api-%s 나 relnotes-%s 를 '
                       '인용해야 한다' % (where, v, v))
    for k, n in sorted(ids.items()):
        if n > 1:
            bad.append('features.tsv: id %s 가 %d번' % (k, n))
    for k, n in sorted(sids.items()):
        if n > 1:
            bad.append('features.tsv: slide-id %s 가 %d번' % (k, n))
    return bad


# ---------------------------------------------------------------- 파일
def tsv(comment, head, rows):
    return ('# %s\n' % comment + '\t'.join(head) + '\n'
            + ''.join('\t'.join(r) + '\n' for r in rows))


def build():
    """{data/ 파일 이름: 내용}. docs/ 가 없으면 None."""
    if not os.path.exists(os.path.join(DOCS, 'release.txt')):
        return None
    rel = releases(read(os.path.join(DOCS, 'release.txt')))
    majors = [r for r in rel if r[2] == 'major']
    files = []
    for r in majors:
        name = 'go1' if r[0] == 'go1' else 'go%d.%d' % vkey(r[0])[:2]
        p = os.path.join(DOCS, 'api', name + '.txt')
        if os.path.exists(p):
            files.append((name[2:] or '1', read(p)))
    fetched = [l.split('\t')[0] for l in
               read(os.path.join(DOCS, 'FETCHED.txt')).split('\n')
               if l and not l.startswith('#')]
    titles = blog_titles(read(os.path.join(DOCS, 'raw', 'blog', 'index.txt')))
    gd = godebug_rows(read(GOROOT_TABLE), read(os.path.join(DOCS,
                                                            'godebug.txt')))
    gen = '생성 표 — tools/make_data.py 가 %s 에서 만든다. 손으로 고치지 말 것.'
    return {
        'releases.tsv': tsv(gen % 'docs/release.txt(go.dev/doc/devel/release)',
                            ['version', 'date', 'kind', 'relnotes-key'], rel),
        'api_added.tsv': tsv(gen % 'docs/api/go1.N.txt',
                             ['version', 'new-packages', 'new-symbols',
                              'sample-packages'], api_added(files)),
        'godebug.tsv': tsv(gen % '$GOROOT/src/internal/godebugs/table.go'
                           '(go1.27.1)와 docs/godebug.txt',
                           ['setting', 'package', 'introduced-in',
                            'default-changed-in', 'old-value'], gd),
        'cite_keys.tsv': tsv(gen % 'docs/FETCHED.txt 와 블로그 색인',
                             ['key', 'name', 'file'],
                             cite_keys(fetched, titles)),
    }


def main(argv):
    made = build()
    if made is None:
        print('  docs/ 가 없다 — make docs 먼저 (PLAN.md §5 2단계)')
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

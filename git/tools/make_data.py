# -*- coding: utf-8 -*-
"""make_data.py — data/releases.tsv · data/cves.tsv 를 mirror 에서.

    python3 tools/make_data.py            # 두 표를 새로 쓴다
    python3 tools/make_data.py --check    # 지금 것과 같은지만 본다

손으로 적으면 반드시 틀리는 두 표다 — 릴리스 66개의 날짜와 CVE 40개가
고쳐진 판의 목록. 날짜는 mirror/git.git 의 태그(태그를 단 사람의 날짜,
그 사람의 시간대)에서, CVE 는 docs/ 에 받아 둔 릴리스 노트(make docs)
에서 읽는다. 사람이 쓴 것은 CVE 의 한국어 요약 한 줄뿐이고, 그 줄도
출처 칸이 가리키는 릴리스 노트의 문단을 옮긴 것이다.

first-feature 칸은 그 판 릴리스 노트의 "UI, Workflows & Features" 절
첫 항목을 **원문 그대로** 줄인 것이다. "대표 기능" 이 아니다 — 무엇이
대표인지는 사람이 고르는 일이라, 표에는 고르지 않은 것만 싣는다.
O(릴리스 노트 크기).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
MIRROR = os.path.join(BASE, 'mirror', 'git.git')
DOCS = os.path.join(BASE, 'docs')
DATA = os.path.join(BASE, 'data')

# CVE 의 영역·한국어 요약은 data/cves_ko.tsv 에 사람이 적는다 —
# 출처는 그 CVE 를 처음 적은 릴리스 노트의 문단이고, 옮긴 것 외에
# 더하지 않는다.
# cURL 의 CVE 가 git 의 노트에 한 번 나온다(http.delegation 을 들인
# 까닭). git 의 결함이 아니라 표에서 뺀다.
NOT_GIT = {'CVE-2011-2192'}


def vkey(v):
    return [int(x) for x in re.findall(r'\d+', v)]


def git(*args):
    return subprocess.run(('git', '-C', MIRROR) + args, check=True,
                          stdout=subprocess.PIPE).stdout.decode()


def first_feature(text):
    """"UI, Workflows & Features" 절의 첫 항목. 절이 없으면 '-'.

    절이 없는 옛 노트에서 아무 항목이나 집으면 버그 고침이 "첫 기능"
    으로 실린다 — 실제로 1.6.0 에서 그랬다. 그래서 비워 둔다.
    """
    # 밑줄 꼴 제목은 adoc_text 가 '§<TAB>제목' 으로 바꿔 두었다
    m = re.search(r'\n(?:§\t)?UI, Workflows (&|and) Features[ \t]*\n',
                  text)
    if not m:
        return '-'
    body = text[m.end() - 1:]
    b = re.search(r'\n \* (.*?)(?=\n\s*\n|\n \* )', body, re.S)
    if not b:
        return '-'
    one = re.sub(r'\s+', ' ', b.group(1)).strip()
    if len(one) > 140:
        one = one[:140].rsplit(' ', 1)[0] + ' …'
    return one.replace('\t', ' ')


def releases():
    rows = git('for-each-ref', '--format=%(refname:short)\t'
               '%(taggerdate:short)\t%(*committerdate:short)',
               'refs/tags/v*').split('\n')
    out = [('version', 'date', 'first-feature', 'relnotes-file',
            'verified-how')]
    for r in sorted((r for r in rows if r), key=lambda r: vkey(r)):
        tag, tdate, cdate = r.split('\t')
        if not re.match(r'^v\d+\.\d+\.0$', tag):
            continue
        ver = tag[1:]
        f = os.path.join(DOCS, 'relnotes-%s.txt' % ver)
        feat, rel = '-', '-'
        if os.path.exists(f):
            feat = first_feature(open(f, encoding='utf-8').read())
            rel = 'RelNotes/%s.adoc' % ver
        out.append((ver, tdate or cdate, feat, rel,
                    'mirror 태그 %s 의 taggerdate' % tag))
    return out


def cves():
    seen = {}
    for name in sorted(os.listdir(DOCS)):
        if not name.startswith('relnotes-'):
            continue
        ver = name[len('relnotes-'):-4]
        text = open(os.path.join(DOCS, name), encoding='utf-8').read()
        # 노트 원문의 두 가지 흠 — 2.17.1 은 "CVE-2018-11233 and 11235"
        # 로 줄여 적었고, 2.36.6 은 "CVS-2023-25815" 로 잘못 적었다.
        text = text.replace('CVE-2018-11233 and 11235',
                            'CVE-2018-11233 and CVE-2018-11235')
        text = text.replace('CVS-2023-25815', 'CVE-2023-25815')
        for c in set(re.findall(r'CVE-\d{4}-\d{4,}', text)):
            seen.setdefault(c, []).append(ver)
    out = [('cve', 'year', 'affected', 'noted-in', 'summary', 'source')]
    for c in sorted(seen, key=vkey):
        if c in NOT_GIT:
            continue
        vers = sorted(seen[c], key=vkey)
        area, ko = ko_rows()[c]        # 요약이 없으면 여기서 멈춘다
        src = 'Documentation/RelNotes/%s.adoc (v2.55.0)' % vers[0]
        out.append((c, c.split('-')[1], area, ' '.join(vers), ko, src))
    return out


def ko_rows():
    """data/cves_ko.tsv → {cve: (영역, 요약)}."""
    out = {}
    path = os.path.join(DATA, 'cves_ko.tsv')
    for line in open(path, encoding='utf-8'):
        if line.startswith('#') or line.startswith('cve\t'):
            continue
        c, area, ko = line.rstrip('\n').split('\t')
        out[c] = (area, ko)
    return out


def tsv(head, rows):
    return head + ''.join('\t'.join(str(x) for x in r) + '\n'
                          for r in rows)


def events():
    """data/events.tsv(사람이 적음) + 모든 x.y.0 릴리스 → 연표.

    release:X.Y.Z 는 releases.tsv 의 날짜로 푼다. 같은 날짜를 두 곳에
    손으로 적으면 언젠가 어긋나기 때문이다. 정렬은 날짜 글자 차례
    (YYYY < YYYY-MM < YYYY-MM-DD 가 같은 해 안에서 앞에 온다).
    """
    rel = {r[0]: r for r in releases()[1:]}
    rows = []
    path = os.path.join(DATA, 'events.tsv')
    for line in open(path, encoding='utf-8'):
        if line.startswith('#') or line.startswith('when\t'):
            continue
        when, ev, src, how = line.rstrip('\n').split('\t')
        if when.startswith('release:'):
            when = tag_date(when[len('release:'):])
        rows.append((when, ev, src, how))
    for ver, date, feat, rn, how in rel.values():
        note = ''
        if feat != '-':
            note = ' — 노트의 새 기능 첫 항목: ' + feat
        rows.append((date, 'git %s 릴리스%s' % (ver, note),
                     'git 저장소 태그 v%s' % ver, how))
    rows.sort(key=lambda r: r[0])
    return [('date', 'event', 'source', 'verified-how')] + rows


KIND = {'mainporcelain': 'porcelain',
        'ancillarymanipulators': 'ancillary',
        'ancillaryinterrogators': 'ancillary',
        'plumbingmanipulators': 'plumbing',
        'plumbinginterrogators': 'plumbing',
        'synchingrepositories': 'plumbing', 'synchelpers': 'plumbing',
        'purehelpers': 'plumbing', 'foreignscminterface': 'foreign',
        'guide': 'guide', 'userinterfaces': 'guide',
        'developerinterfaces': 'guide'}


def name_line(cmd):
    """docs/<cmd>.txt 의 NAME 절 한 줄(영어 원문 그대로)."""
    p = os.path.join(DOCS, cmd + '.txt')
    if not os.path.exists(p):
        return '-'
    lines = open(p, encoding='utf-8').read().split('\n')
    for i, ln in enumerate(lines):
        if ln == '§\tNAME':
            for nxt in lines[i + 1:]:
                if nxt.strip():
                    return nxt.strip().split(' - ', 1)[-1]
    return '-'


def commands():
    """v2.55.0 의 command-list.txt(명령마다 종류) → 명령어 사전의 뼈대.

    한국어 한 줄 설명은 data/commands_ko.tsv 에 사람이 적는다(17부를
    쓸 때). 비어 있으면 '-' 로 둔다 — 없는 설명을 지어내지 않는다.
    """
    ko = {}
    path = os.path.join(DATA, 'commands_ko.tsv')
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            if line.startswith('#') or line.startswith('command\t'):
                continue
            c, text = line.rstrip('\n').split('\t')[:2]
            ko[c] = text
    out = [('command', 'category', 'kind', 'name-line', 'summary-ko')]
    for line in git('show', 'v2.55.0:command-list.txt').split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cmd, cat = line.split()[:2]
        out.append((cmd, cat, KIND.get(cat, cat), name_line(cmd),
                    ko.get(cmd, '-')))
    return out


def tag_date(ver):
    """태그 v<ver> 의 날짜 — 보수 판(2.30.3 등)도 된다.

    없으면 멈춘다 — 날짜를 모르는 사건을 연표에 넣지 않는다.
    """
    d = git('for-each-ref', '--format=%(taggerdate:short)',
            'refs/tags/v' + ver).strip()
    if not d:
        raise KeyError('태그 v%s 가 없거나 날짜가 없다' % ver)
    return d


def contributors():
    """v2.55.0 까지 머지 커밋을 뺀 커밋 수 상위 25명(.mailmap 반영)."""
    out = [('rank', 'person', 'commits', 'verified-how')]
    lines = git('shortlog', '-sn', '--no-merges', 'v2.55.0')
    for k, line in enumerate(lines.split('\n')[:25], 1):
        n, name = line.strip().split('\t')
        out.append((k, name, n,
                    'mirror: git shortlog -sn --no-merges v2.55.0'))
    return out


def growth():
    """판마다 누적 커밋 수와 기여자 수 — 모든 x.y.0 태그."""
    out = [('version', 'date', 'commits', 'contributors')]
    for ver, date, _f, _r, _h in releases()[1:]:
        n = git('rev-list', '--count', 'v' + ver).strip()
        who = git('shortlog', '-sn', 'v' + ver).strip().split('\n')
        out.append((ver, date, n, len(who)))
    return out


HEADS = {
    'releases.tsv': (
        '# 릴리스 — 모든 x.y.0 태그. tools/make_data.py 가\n'
        '# mirror 에서 만든다(손으로 고치지 말 것). first-feature 는\n'
        '# 그 판 노트의 새 기능 절 첫 항목을 원문 그대로 줄인 것이다\n'
        '# (대표 기능이 아니다). 1.0.0‥1.4.0 은 노트 파일이 없다.\n'),
    'cves.tsv': (
        '# 보안 결함 — docs/ 의 릴리스 노트에 적힌 CVE 전부\n'
        '# (cURL 의 것 하나 뺌). tools/make_data.py 가 만든다.\n'
        '# noted-in 은 그 CVE 를 이름으로 적은 모든 노트의 판 —\n'
        '# 고친 판만이 아니라 "c.f." 로 언급만 한 판도 들어가고,\n'
        '# CVE 이름 없이 앞 판의 수정을 합친 판은 빠진다.\n'
        '# affected·summary 는 data/cves_ko.tsv.\n'),
    'timeline.tsv': (
        '# 연표 — tools/make_data.py 가 data/events.tsv(사람이\n'
        '# 적음)와 모든 x.y.0 릴리스를 합쳐 만든다. 고칠 곳은\n'
        '# events.tsv.\n'),
    'contributors.tsv': (
        '# 기여자 — v2.55.0 까지 머지를 뺀 커밋 수 상위 25명.\n'
        '# .mailmap 이 한 사람의 여러 주소를 합친다. make_data.py.\n'),
    'commands.tsv': (
        '# 명령 — v2.55.0 의 command-list.txt 전부. name-line 은\n'
        '# 그 명령 문서의 NAME 줄 원문, summary-ko 는\n'
        '# data/commands_ko.tsv.\n'),
    'growth.tsv': (
        '# 자람 — x.y.0 마다 누적 커밋 수(rev-list --count)와\n'
        '# 기여자 수(shortlog -sn 의 줄 수). make_data.py.\n'),
}


def main(argv):
    if not os.path.isdir(DOCS):
        print('  docs/ 가 없다 — make docs 먼저')
        return 1
    made = {}
    for name, fn in (('releases.tsv', releases), ('cves.tsv', cves),
                     ('timeline.tsv', events),
                     ('contributors.tsv', contributors),
                     ('commands.tsv', commands),
                     ('growth.tsv', growth)):
        made[name] = tsv(HEADS[name], fn())
    bad = 0
    for name, text in made.items():
        p = os.path.join(DATA, name)
        if '--check' in argv:
            if open(p, encoding='utf-8').read() != text:
                print('  ✗ data/%s 가 mirror 와 다르다' % name)
                bad += 1
            continue
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        n = sum(1 for l in text.split('\n')[:-1] if l[:1] != '#') - 1
        print('data/%s — %d행' % (name, n))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

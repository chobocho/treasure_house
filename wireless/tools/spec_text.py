#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""3GPP 규격 zip → 조항 제목이 살아 있는 평문. 표준 라이브러리만 쓴다.

    python3 tools/spec_text.py 38211-i60.zip            # 표준 출력으로
    python3 tools/spec_text.py 38211-i60.zip -o 38.211.txt
    python3 tools/spec_text.py --fetch 38.211      # 최신판을 specs/ 로
    python3 tools/spec_text.py --fetch-list data/specs_fetch.txt

왜 이것이 필요한가: 이 덱은 규격을 인용한다. 인용을 기억으로 적으면
조항 번호가 반드시 어긋나고, 어긋나도 아무 시험이 빨개지지 않는다.
그래서 규격 원문을 실제로 받아 조항 제목만 뽑아 두고,
`deck/check_claims.py` 가 덱의 `<!--SPEC ts=… clause=…-->` 을
그것과 맞댄다.

내보내는 꼴은 한 줄에 하나다. 조항 제목 줄은

    4.2<TAB>Numerologies

처럼 번호와 제목이 탭으로 갈리고, 본문은 그냥 한 줄씩 나온다.
검사기는 "줄머리가 그 조항 번호이고 곧바로 공백·탭이 온다" 만 본다.

3gpp.org 는 중간 인증서를 안 보내므로 내려받기는 반드시
tools/fetch.sh 를 거친다(PLAN.md §2). LibreOffice 는 이 기계에
없지만 .docx 는 그냥 zip 이고 본문은 word/document.xml 하나라
직접 읽으면 된다.

시간 O(문서 크기), 공간은 문서 하나 분량.
"""
import io
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SPECS = os.path.join(BASE, 'specs')
FETCH = os.path.join(HERE, 'fetch.sh')
ARCHIVE = 'https://www.3gpp.org/ftp/Specs/archive'

# <w:p> 안의 <w:t> 를 이어 붙이면 문단 하나가 된다. 스타일이 Heading*
# 이면 그 문단은 조항 제목이다.
P_RE = re.compile(br'<w:p[ >].*?</w:p>|<w:p/>', re.S)
T_RE = re.compile(br'<w:t(?:\s[^>]*)?>(.*?)</w:t>', re.S)
STYLE_RE = re.compile(br'<w:pStyle w:val="([^"]+)"')
TAB_RE = re.compile(br'<w:tab/>')
# "4.2" · "4.2.1" · "A.3" 처럼 시작하는 제목
CLAUSE_RE = re.compile(r'^([0-9A-Z](?:\.[0-9]+)*)\s+(\S.*)$')


def fetch(url, out=None):
    """tools/fetch.sh 로 받는다. 실패하면 예외."""
    cmd = ['sh', FETCH, url] + ([out] if out else [])
    r = subprocess.run(cmd, capture_output=not out)
    if r.returncode != 0:
        raise IOError('내려받기 실패: %s' % url)
    return r.stdout if not out else None


def unescape(b):
    s = b.decode('utf-8', 'replace')
    for a, c in (('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'),
                 ('&apos;', "'"), ('&amp;', '&')):
        s = s.replace(a, c)
    return s


def docx_paragraphs(raw):
    """(스타일, 글) 목록.

    w:tab 은 공백으로 편다 — 조항 제목의 번호와 이름을 가르는 것이
    그 탭이기 때문이다.
    """
    out = []
    for m in P_RE.finditer(raw):
        p = m.group(0)
        st = STYLE_RE.search(p)
        style = st.group(1).decode('ascii', 'replace') if st else ''
        p = TAB_RE.sub(b'<w:t> </w:t>', p)
        text = ''.join(unescape(t) for t in T_RE.findall(p))
        out.append((style, re.sub(r'\s+', ' ', text).strip()))
    return out


def from_docx(path_or_bytes):
    z = zipfile.ZipFile(path_or_bytes)
    names = [n for n in z.namelist() if n == 'word/document.xml']
    if not names:
        raise ValueError('word/document.xml 이 없다 — .docx 가 아니다')
    return docx_paragraphs(z.read(names[0]))


def from_doc(raw):
    """옛 이진 .doc 의 응급 처방 — 텍스트 조각만 긁는다.

    조항 제목의 서식 정보는 못 살린다. 그래서 '번호 + 제목' 꼴로 보이는
    줄만 제목으로 인정한다. 2005년 이전 문서에만 쓰는 길이다.
    """
    txt = raw.decode('latin-1', 'replace')
    txt = re.sub(r'[^\x09\x0a\x0d\x20-\x7e\xa0-\xff]+', '\n', txt)
    return [('', l.strip()) for l in txt.split('\n') if l.strip()]


def render(paras):
    """조항 제목은 '번호<TAB>제목', 나머지는 그대로 한 줄씩."""
    out = []
    for style, text in paras:
        if not text:
            continue
        m = CLAUSE_RE.match(text)
        heading = (style.lower().startswith('heading')
                   or style in ('TT', 'TAH'))
        if m and (heading or len(text) < 90):
            out.append('%s\t%s' % (m.group(1), m.group(2)))
        else:
            out.append(text)
    return '\n'.join(out) + '\n'


def extract(path):
    """zip(규격 꾸러미) 또는 .docx 하나를 받아 평문으로."""
    z = zipfile.ZipFile(path)
    inner = [n for n in z.namelist()
             if n.lower().endswith(('.docx', '.doc'))]
    if not inner and 'word/document.xml' in z.namelist():
        return render(from_docx(path))
    if not inner:
        raise ValueError('%s 안에 문서가 없다: %s'
                         % (path, z.namelist()[:5]))
    # 여러 개면 가장 큰 것이 본문이다
    # (부록·표지가 따로 든 꾸러미가 있다)
    inner.sort(key=lambda n: z.getinfo(n).file_size, reverse=True)
    raw = z.read(inner[0])
    if inner[0].lower().endswith('.docx'):
        return render(from_docx(io.BytesIO(raw)))
    return render(from_doc(raw))


def latest_zip(num):
    """38.211 → 그 규격 폴더에서 가장 최신 판의 zip URL.

    파일 이름이 38211-i60.zip 꼴이라 사전 순으로 가장 뒤가 최신이다
    (판 글자는 릴리스 순서와 같은 알파벳을 쓴다).
    """
    folder = '%s/%s_series/%s/' % (ARCHIVE, num.split('.')[0], num)
    html = fetch(folder).decode('utf-8', 'replace')
    pat = r'([0-9]{4,5}(?:-[0-9]+)?-[0-9a-z]{2,3}\.zip)'
    names = sorted(set(re.findall(pat, html)))
    if not names:
        raise IOError('%s 에 zip 이 없다' % folder)
    return folder + names[-1], names[-1]


def fetch_spec(num, force=False):
    """규격 하나를 받아 specs/<번호>.txt 로 뽑는다.

    이미 있으면 건너뛴다 — 몇 번 돌려도 같다.
    """
    out = os.path.join(SPECS, '%s.txt' % num)
    if os.path.exists(out) and not force:
        return out, False
    if not os.path.isdir(SPECS):
        os.makedirs(SPECS)
    url, name = latest_zip(num)
    zp = os.path.join(SPECS, 'zips', name)
    if not os.path.isdir(os.path.dirname(zp)):
        os.makedirs(os.path.dirname(zp))
    if not os.path.exists(zp):
        fetch(url, zp)
    io.open(out, 'w', encoding='utf-8', newline='\n').write(extract(zp))
    return out, True


def main(argv):
    if '--fetch-list' in argv:
        p = argv[argv.index('--fetch-list') + 1]
        nums = []
        for line in io.open(p, encoding='utf-8').read().split('\n')[1:]:
            line = line.split('#')[0].strip()
            if line:
                nums.append(line.split('\t')[0].strip())
        got = new = 0
        for n in nums:
            try:
                _out, fresh = fetch_spec(n)
                got += 1
                new += 1 if fresh else 0
            except Exception as e:                       # noqa: BLE001
                print('  ✗ %s — %s' % (n, e))
        print('규격 %d/%d개 준비됨 (새로 받은 것 %d개)'
              % (got, len(nums), new))
        return 0
    if '--fetch' in argv:
        n = argv[argv.index('--fetch') + 1]
        out, fresh = fetch_spec(n)
        print('%s %s'
              % (out, '(새로 받음)' if fresh else '(이미 있음)'))
        return 0
    paths = [a for a in argv if not a.startswith('-')]
    if not paths:
        sys.stderr.write(__doc__)
        return 2
    text = extract(paths[0])
    if '-o' in argv:
        io.open(argv[argv.index('-o') + 1], 'w',
                encoding='utf-8', newline='\n').write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

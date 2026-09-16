# -*- coding: utf-8 -*-
"""한국어 말뭉치 받기 — 위키문헌의 공유저작물을 텍스트로.

    python3 corpus/fetch_ko.py           # 없는 것만 받는다
    python3 corpus/fetch_ko.py --check   # SOURCES.tsv 와 파일이 맞나

누구의 글인가 (PLAN.md §0.10): 1956년 이전에 세상을 떠난 작가의
작품만 싣는다. 저자 문서의 '사망 연도' 와 작품 문서의 PD 틀을 그대로
SOURCES.tsv 에 옮겨 적어, 공유저작물이라는 근거를 사람이 되짚게 한다.

되풀이해 받아도 같은 글이 나와야 한다. 그래서 처음 받을 때 작품
문서의 판 번호(revid)를 적어 두고, 다음부터는 그 판(oldid)을 받는다.
본문을 다른 문서에서 끌어오는(<pages …>) 작품은 뺀다 — 판 번호가
작품 문서만 고정하고, 끌려오는 쪽 문서는 고정하지 못하기 때문이다.
(윤동주의 시가 모두 그렇게 되어 있어 이 말뭉치에 없다.)

위키 문법을 걷어 내는 규칙은 strip() 한 곳에 모았다. 규칙이 바뀌면
말뭉치 전체를 다시 만든다. 시간 O(글자 수).
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'ko')
SOURCES = os.path.join(HERE, 'SOURCES.tsv')
API = 'https://ko.wikisource.org/w/api.php?'
UA = 'treasure_house-deck/1.0 (+github.com/chobocho/treasure_house)'
COLS = ['file', 'title', 'author', 'died', 'wikisource-url', 'revid',
        'fetched', 'license-basis']

# (저자, 작품 문서 이름). 차례가 곧 파일 차례다.
WORKS = [
    ('현진건', '운수 좋은 날'), ('현진건', '빈처'),
    ('현진건', '술 권하는 사회'), ('현진건', 'B사감과 러브레터'),
    ('현진건', '고향 (현진건)'), ('현진건', '할머니의 죽음'),
    ('현진건', '불'),
    ('이상', '봉별기'), ('이상', '종생기'), ('이상', '지주회시'),
    ('이상', '실화'), ('이상', '권태'), ('이상', '동해'),
    ('이상', '환시기'), ('이상', '단발'),
    ('김유정', '봄봄'), ('김유정', '동백꽃'), ('김유정', '만무방'),
    ('김유정', '금 따는 콩밭'), ('김유정', '산골 나그네'),
    ('김유정', '소낙비'), ('김유정', '총각과 맹꽁이'),
    ('한용운', '천일'), ('한용운', '쥐'), ('한용운', '일출'),
    ('한용운', '해촌의 석양'), ('한용운', '낙화'), ('한용운', '파리'),
    ('김소월', '가는 봄 삼월'), ('김소월', '가막덤불'),
    ('김소월', '고적한 날'), ('김소월', '공원의 밤'),
    ('김소월', '꿈자리'), ('김소월', '나무리벌 노래'),
]


def api(**kw):
    """요청 하나. 429(너무 잦다)면 오래 쉬고 다시 한다."""
    kw.update(format='json', formatversion=2)
    url = API + urllib.parse.urlencode(kw)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for n in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode('utf-8'))
            time.sleep(4)                  # 서버에 예의를 지킨다
            return data
        except urllib.error.HTTPError as e:
            if e.code != 429 or n == 5:
                raise
            time.sleep(60 * (n + 1))
    return {}


def wikitext(page=None, oldid=None):
    kw = dict(action='parse', prop='wikitext|revid')
    if oldid:
        kw['oldid'] = oldid
    else:
        kw['page'] = page
        kw['redirects'] = 1
    d = api(**kw)
    if 'error' in d:
        raise KeyError('%s: %s' % (page or oldid, d['error']['info']))
    return d['parse']['wikitext'], d['parse']['revid']


def died(author):
    """저자 문서의 {{저자 … |사망 연도 = 1934년}} 에서 연도만."""
    w, _ = wikitext('저자:' + author)
    m = re.search(r'\|\s*사망 연도\s*=\s*(\d{4})', w)
    return m.group(1) if m else '?'


def license_of(w):
    m = re.search(r'\{\{\s*(PD-[\w-]+)', w)
    return m.group(1) if m else '?'


def drop_templates(s):
    """{{…}} 를 중첩까지 통째로 지운다. O(글자 수)."""
    out, depth, i = [], 0, 0
    while i < len(s):
        if s.startswith('{{', i):
            depth += 1
            i += 2
        elif s.startswith('}}', i) and depth:
            depth -= 1
            i += 2
        else:
            if not depth:
                out.append(s[i])
            i += 1
    return ''.join(out)


def strip(w):
    """위키 문법 → 맨 글. 규칙은 전부 여기에만 있다.

    1. '== 라이선스 ==' · '== 저작권 ==' 부터 끝까지 버린다.
    2. 틀 {{…}}, 주석 <ref>…</ref>, HTML 주석을 지운다.
    3. [[분류:…]] 는 지우고 [[문서|글]] 은 글, [[문서]] 는 문서.
    4. 태그는 벗기고 안의 글만 남긴다.
    5. 한자만 든 괄호 (信條) 를 지운다 — 한글 모델에 드문 글자만 는다.
    6. 기본 다국어 평면 밖의 글자(장식 기호 🙝🙟)를 지운다.
    7. 줄 끝 공백을 지우고, 빈 줄 여럿은 하나로, 앞뒤 빈 줄은 없앤다.
    """
    w = re.split(r'\n==\s*(?:라이선스|저작권)\s*==', w)[0]
    w = drop_templates(w)
    w = re.sub(r'<ref[^>]*>.*?</ref>|<ref[^>]*/>', '', w, flags=re.S)
    w = re.sub(r'<!--.*?-->', '', w, flags=re.S)
    w = re.sub(r'\[\[분류:[^\]]*\]\]', '', w)
    w = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', w)
    w = re.sub(r'\[\[([^\]]*)\]\]', r'\1', w)
    w = re.sub(r'<[^>]+>', '', w)
    w = re.sub(r"'{2,}", '', w)
    w = re.sub(r'\([一-鿿]+\)', '', w)
    w = ''.join(c for c in w if ord(c) <= 0xFFFF)
    lines = [l.rstrip() for l in w.split('\n')]
    text = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip('\n')
    return text + '\n'


def read_sources():
    if not os.path.exists(SOURCES):
        return {}
    rows = {}
    for n, line in enumerate(io.open(SOURCES, encoding='utf-8')):
        cols = line.rstrip('\n').split('\t')
        if n == 0 or len(cols) < len(COLS):
            continue
        rows[cols[0]] = dict(zip(COLS, cols))
    return rows


def write_sources(rows):
    with io.open(SOURCES, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(COLS) + '\n')
        for name in sorted(rows):
            f.write('\t'.join(rows[name][c] for c in COLS) + '\n')


def fname(author, title):
    t = re.sub(r'\s*\([^)]*\)', '', title).replace(' ', '_')
    return 'ko/%s_%s.txt' % (author, t)


def main(argv):
    rows = read_sources()
    if '--check' in argv:
        bad = [w for w in WORKS if fname(*w) not in rows
               or not os.path.exists(os.path.join(HERE, fname(*w)))]
        for a, t in bad:
            print('  ✗ %s %s — 받지 않았다' % (a, t))
        print('작품 %d편 — 빠짐 %d편' % (len(WORKS), len(bad)))
        return 1 if bad else 0
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    deaths = {}
    for author, title in WORKS:
        name = fname(author, title)
        path = os.path.join(HERE, name)
        old = rows.get(name)
        if old and os.path.exists(path):
            continue
        if author not in deaths:
            deaths[author] = died(author)
        if old:
            w, rev = wikitext(oldid=old['revid'])
        else:
            w, rev = wikitext(title)
        if '<pages' in w:
            print('  ✗ %s — 본문을 끌어오는 문서라 뺀다' % title)
            continue
        with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(strip(w))
        rows[name] = dict(
            file=name, title=title, author=author,
            died=deaths[author],
            **{'wikisource-url': 'https://ko.wikisource.org/wiki/'
               + urllib.parse.quote(title.replace(' ', '_'))},
            revid=str(rev), fetched=time.strftime('%Y-%m-%d'),
            **{'license-basis': license_of(w)})
        write_sources(rows)               # 한 편마다 적어 둔다
        print('  받음 %s (%d바이트)' % (name, os.path.getsize(path)))
    write_sources(rows)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

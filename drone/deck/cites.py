# -*- coding: utf-8 -*-
"""인용 키 → (배지 이름, docs/ 안의 파일) — 조립기·사실 검사·자료 검사가 함께 쓴다.

<!--CITE key=px4-attitude sec="Attitude Controller"--> 의 key 는
data/cite_keys.tsv 한 곳에서만 나온다(PLAN.md §0.4, §1).

  칸: key | name | url | kind | licence | file
      name    배지에 적을 짧은 이름 (한국어 가능)
      url     받아 온 주소 — tools/fetch_docs.py 가 이 칸을 읽어 받는다
      kind    doc | code | paper | law | spec | history | press | web
      licence 문서의 라이선스(코드 발췌 규칙 §0.14 가 본다), 모르면 -
      file    docs/ 아래 텍스트 변환 파일 경로

절(sec)은 tools/html_text.py·pdf_sections.py 가 만든 '§<TAB>제목' 줄과
글자까지 같아야 한다. 앞머리만 맞는 것은 받지 않는다 — 기억으로 적은
"대충 그 절" 이 들어올 틈을 없앤다.

goevo/deck/cites.py 에서 물려받아 줄였다 — 이 덱에는 릴리스 노트·API
목록 같은 버전 문서가 없으므로 키는 표 하나에서만 온다.

시간 O(표 행 수 + 문서 크기). 문서는 한 번 읽어 캐시한다.
"""
import io
import os
import re

_TEXT = {}
KINDS = ('doc', 'code', 'paper', 'law', 'spec', 'history', 'press', 'web')


def _read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def rows(base, name):
    """data/<name> 을 {칸: 값} 목록으로. 첫 줄이 칸 이름, # 은 주석."""
    p = os.path.join(base, 'data', name)
    if not os.path.exists(p):
        return []
    head, out = None, []
    for line in _read(p).split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cols = [c.strip() for c in line.split('\t')]
        if head is None:
            head = cols
            continue
        out.append(dict(zip(head, cols)))
    return out


def index(base):
    """키 → {'name', 'url', 'kind', 'licence', 'file'}."""
    out = {}
    for row in rows(base, 'cite_keys.tsv'):
        if row.get('key'):
            out[row['key']] = {'name': row.get('name') or row['key'],
                               'url': row.get('url') or '',
                               'kind': row.get('kind') or '',
                               'licence': row.get('licence') or '-',
                               'file': row.get('file') or ''}
    return out


def _doc(path):
    if path not in _TEXT:
        _TEXT[path] = _read(path)
    return _TEXT[path]


def resolve(base, key, sec):
    """맞으면 None, 틀리면 까닭 한 줄. sec 이 비면 키만 본다."""
    ent = index(base).get(key)
    if ent is None:
        return '키 %s 가 data/cite_keys.tsv 에 없다' % key
    if not sec:
        return None
    if not ent['file']:
        return '%s — cite_keys.tsv 의 file 칸이 비어 있어 절을 볼 수 없다' % key
    p = os.path.join(base, 'docs', ent['file'])
    if not os.path.exists(p):
        return '%s — docs/%s 가 없다 (make docs)' % (key, ent['file'])
    pat = re.compile(r'^§\t%s$' % re.escape(sec), re.M)
    if not pat.search(_doc(p)):
        return '%s §%s — 그런 절 제목이 docs/%s 에 없다' % (key, sec,
                                                          ent['file'])
    return None

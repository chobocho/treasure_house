# -*- coding: utf-8 -*-
"""인용 키 → (배지 이름, docs/ 안의 파일) — 조립기·사실 검사·자료 검사가 함께 쓴다.

<!--CITE key=whatsnew-12 sec="Primary constructors"--> 의 key 는 한 곳에서만
나온다: data/cite_keys.tsv (key | name | file, file 은 docs/ 아래 경로).
버전 기록·버전별 whats-new·csharplang 제안·Roslyn 문서·MessageID.cs·
릴리스 색인·블로그 글이 전부 여기 한 줄씩이다(PLAN.md §2). goevo 에서는
releases.tsv 가 relnotes 키를 따로 냈지만, C# 은 버전마다 노트가 한 장씩
있는 꼴이 아니라(7.x 는 한 문서, 1.0–6.0 은 버전 기록 한 장) 표 하나로 모았다.

왜 모듈 하나로 떼었나: git 덱에서는 조립기가 키를, check_claims 가 파일을
따로 알았다. 규칙이 두 곳에 있으면 한쪽만 고쳐지는 날이 온다. 여기서는
make data-check(3단계)까지 셋이 쓰므로 한 곳에 둔다.

절(sec) 확인 규칙은 문서 종류에 따라 다르다.
  · 보통 문서 — tools/md_text.py 가 만든 '§<TAB>제목' 줄과 글자까지 같아야 한다.
  · 소스 파일(.cs, 예: Roslyn 의 MessageID.cs) — 제목이 없으므로 sec 이
    파일의 **한 줄 전체**(앞뒤 공백을 뺀 것)와 같아야 한다. 앞머리만 맞는
    것은 받지 않는다 — "records 는 C# 9" 를 증명하려면 그 case 줄을 통째로
    가리켜야 한다.

시간 O(표 행 수 + 문서 크기). 문서는 부를 때마다 다시 읽는다 — 조립 한 번에
인용이 수백 건이라도 문서 수는 수십 개라 캐시한다.
"""
import io
import os
import re

_TEXT = {}


def _read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def _rows(base, name):
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


def vnorm(v):
    """C# 버전 표기를 하나로 — 끝의 '.0' 은 뗀다. '8.0' → '8', '12' → '12',
    '1.0' → '1', '7.3' → '7.3', '1.2' → '1.2'.

    공식 문서도 컴파일러도 표기가 섞여 있다. 버전 기록 문서는 'C# version
    8.0' 과 'C# version 12' 를, Roslyn 오류는 'C# 8.0' 과 'C# 12.0' 을 쓴다.
    비교는 언제나 이 꼴로 한다."""
    v = (v or '').strip()
    return v[:-2] if v.endswith('.0') else v


def feature_rows(base):
    """기능 목록 전부 — data/features/pNN.tsv 를 파일 이름 차례로 잇는다.

    부마다 파일을 나눈 까닭: 서브에이전트 둘이 서로 다른 부를 동시에
    쓴다. 한 파일을 둘이 고치면 한쪽의 줄이 사라진다. 행마다 '_file'
    칸에 어느 파일에서 왔는지 적어 둔다(오류 메시지용)."""
    d = os.path.join(base, 'data', 'features')
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if not name.endswith('.tsv'):
            continue
        for r in _rows(base, os.path.join('features', name)):
            r['_file'] = 'data/features/' + name
            out.append(r)
    return out


def index(base):
    """키 → {'name': 배지에 적을 이름, 'file': docs/ 아래 경로}."""
    out = {}
    for row in _rows(base, 'cite_keys.tsv'):
        if row.get('key'):
            out[row['key']] = {'name': row.get('name') or row['key'],
                               'file': row.get('file') or ''}
    return out


def line_mode(ent):
    """절 대신 한 줄 전체를 맞춰 보는 문서인가 — 소스 파일."""
    return ent['file'].endswith('.cs')


def _doc(path):
    if path not in _TEXT:
        _TEXT[path] = _read(path)
    return _TEXT[path]


def resolve(base, key, sec):
    """맞으면 None, 틀리면 까닭 한 줄. sec 이 비면 키만 본다."""
    ent = index(base).get(key)
    if ent is None:
        return '키 %s 가 cite_keys.tsv 에 없다' % key
    if not sec:
        return None
    p = os.path.join(base, 'docs', ent['file'])
    if not os.path.exists(p):
        return '%s — docs/%s 가 없다 (make docs)' % (key, ent['file'])
    text = _doc(p)
    if line_mode(ent):
        pat = re.compile(r'^[ \t]*%s[ \t]*$' % re.escape(sec), re.M)
        what = '줄'
    else:
        pat = re.compile(r'^§\t%s$' % re.escape(sec), re.M)
        what = '절 제목'
    if not pat.search(text):
        return '%s §%s — 그런 %s이 docs/%s 에 없다' % (key, sec, what,
                                                      ent['file'])
    return None

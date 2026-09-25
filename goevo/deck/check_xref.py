#!/usr/bin/env python3
"""상호참조 검사 — "N부 M장" 이라고 적힌 것이 진짜 그 자리인가.

    python3 deck/check_xref.py

덱은 앞뒤로 계속 서로를 가리킨다("1부 6장에서 본 그 쿠키다"). 그 화살표는
글로만 적혀 있어서, 장을 하나 끼워 넣으면 **아무 소리 없이 전부 한 칸씩
어긋난다.** 14단계 전수 리뷰에서 이런 것을 다섯 건 찾았다. 그래서 도구로 옮겼다.

두 가지를 본다.

  1. `<a href="#id">N부 M장</a>` — 링크가 가리키는 슬라이드가 실제로
     그 부 그 장에 있는가. (id 가 실재하는지는 check_deck.js 가 본다.)
  2. 링크 없이 글로만 적은 "N부 M장" — 그 부에 그 장이 있기는 한가.

  3. 버전 배지 `<span class="vt v122">1.22</span>` (PLAN.md §1, §6) —
     · class 와 글자가 같은 버전인가 (v122 ↔ 1.22, v10 ↔ 1.0, v110 ↔ 1.10)
     · 그 버전이 data/releases.tsv 의 큰 릴리스이거나 인용 키가 있는
       초안(relnotes-1.28)인가
     · 배지를 단 장의 id 가 data/features.tsv 의 slide-id 에 있는가
     · features.tsv 의 slide-id 마다 덱에 그 장이 있고 배지가 정확히 하나인가
     "이 기능은 1.22" 라는 표시가 표와 따로 놀면, 독자가 가장 먼저 믿는
     글자가 가장 먼저 틀린다.

뜻이 맞는지(그 장이 정말 그 이야기를 하는지)는 기계가 못 본다. 사람이 본다.
"""
import glob
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cites  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SECTIONS = os.path.join(HERE, 'sections')
ART = re.compile(r'<article[^>]*id="([^"]+)"[^>]*>(.*?)</article>', re.S)
CHNUM = re.compile(r'<p class="chnum">([^<]+)</p>')


def scan():
    """슬라이드 id → (부, 장). 부·장 표지가 나올 때마다 갈아 끼운다."""
    files = []
    for f in sorted(glob.glob(os.path.join(SECTIONS, '*.html'))):
        files.append((os.path.basename(f), io.open(f, encoding='utf-8').read()))
    return scan_texts(files)


def scan_texts(files):
    """[(파일 이름, 글)] → scan() 과 같은 결과. 한 부가 여러 파일(08_·08b_)로
    나뉘면 뒤 파일에는 부 표지가 없으므로, 앞 두 자리가 같은 앞 파일의 부와
    장을 이어받는다. O(글 길이)."""
    where, chaps = {}, {}
    prev = (None, None, None)          # (앞 두 자리, 부, 장)
    for name, text in files:
        if name[:2] == prev[0]:
            part, chap = prev[1], prev[2]
        else:
            part = chap = None
        for m in ART.finditer(text):
            cm = CHNUM.search(m.group(2))
            if cm:
                v = cm.group(1).strip()
                if v.endswith('부'):
                    part, chap = v[:-1], None
                elif v.endswith('장'):
                    chap = v[:-1]
                    if part:
                        chaps[part] = max(chaps.get(part, 0), int(chap))
            where[m.group(1)] = (part, chap)
        prev = (name[:2], part, chap)
    return where, chaps


BADGE = re.compile(r'<span class="vt v(\d+)">([^<]*)</span>')


def badge_class(v):
    """'1.22' → 'v122'. 점만 뺀다 — 1.1(v11) 과 1.10(v110) 이 겹치지 않는다."""
    return 'v' + v.replace('.', '')


def known_versions():
    """배지에 쓸 수 있는 버전 — 큰 릴리스와, 노트 키가 있는 초안."""
    out = set()
    for key in cites.index(BASE):
        if key.startswith('relnotes-'):
            out.add(key[len('relnotes-'):])
    return out


def feature_ids():
    """data/features/pNN.tsv 전부의 slide-id (비어 있는 행은 개관 표에만 실린다)."""
    return set(r['slide-id'] for r in cites.feature_rows(BASE)
               if r.get('slide-id'))


def badge_errors(texts, releases, features):
    """texts: {파일 이름: 조각 본문}. 틀린 것마다 한 줄. O(조각 크기)."""
    bad, seen = [], {}
    for name in sorted(texts):
        for m in ART.finditer(texts[name]):
            aid, inner = m.group(1), m.group(2)
            if aid.startswith('p0-'):
                continue        # 0부는 범례 — 배지 견본을 보이는 자리다
            badges = BADGE.findall(inner)
            seen[aid] = len(badges)
            for cls, v in badges:
                if 'v' + cls != badge_class(v):
                    bad.append('%s: #%s 배지 class v%s 와 글자 %s 가 다르다'
                               % (name, aid, cls, v))
                elif v not in releases:
                    bad.append('%s: #%s 배지 %s — releases.tsv 에 없는 버전'
                               % (name, aid, v))
            if badges and aid not in features:
                bad.append('%s: #%s 에 배지가 있는데 features.tsv 에 없다'
                           % (name, aid))
            elif aid in features and len(badges) != 1:
                bad.append('%s: #%s 는 기능 장인데 배지가 %d개 (정확히 하나)'
                           % (name, aid, len(badges)))
    # 조각 파일 이름의 앞 두 자리가 부 번호다. 표지 한 장뿐인 부는 아직
    # 안 쓴 부라, 그 부를 가리키는 기능 장이 없는 것은 오류가 아니다
    # (3단계에서 features.tsv 를 먼저 다 채우고 5단계에서 부를 쓴다).
    written = set()
    for name in texts:
        if name[:2].isdigit() and len(ART.findall(texts[name])) > 1:
            written.add(int(name[:2]))
    for aid in sorted(features - set(seen)):
        m = re.match(r'p(\d+)-', aid)
        if m and int(m.group(1)) not in written:
            continue
        bad.append('features.tsv 의 slide-id #%s 가 덱에 없다' % aid)
    return bad


def main():
    where, chaps = scan()
    bad, n_link, n_text = [], 0, 0
    for f in sorted(glob.glob(os.path.join(SECTIONS, '*.html'))):
        name = os.path.basename(f)
        text = io.open(f, encoding='utf-8').read()
        for m in re.finditer(r'<a href="#([^"]+)">([^<]*)</a>', text):
            aid, label = m.group(1), m.group(2)
            pm = re.search(r'(\d+)부', label)
            cm = re.search(r'(\d+)(?:·\d+)*장', label)
            if not (pm or cm):
                continue
            n_link += 1
            p, c = where.get(aid, (None, None))
            if pm and p and p != pm.group(1):
                bad.append('%s: #%s 는 %s부인데 "%s" 라고 적혀 있다'
                           % (name, aid, p, label))
            elif cm and c and cm.group(1) != c:
                bad.append('%s: #%s 는 %s장인데 "%s" 라고 적혀 있다'
                           % (name, aid, c, label))
        for m in re.finditer(r'(\d+)부\s*(\d+)장', text):
            p, c = m.group(1), int(m.group(2))
            n_text += 1
            if p in chaps and c > chaps[p]:
                bad.append('%s: "%s" — %s부는 %d장까지다'
                           % (name, m.group(0), p, chaps[p]))
    texts = dict((os.path.basename(f), io.open(f, encoding='utf-8').read())
                 for f in glob.glob(os.path.join(SECTIONS, '*.html')))
    feats = feature_ids()
    vbad = badge_errors(texts, known_versions(), feats)
    n_badge = sum(len(BADGE.findall(t)) for t in texts.values())
    bad += vbad
    for line in bad:
        print('  ' + line)
    print('상호참조: 링크 %d개 · 글로 적은 것 %d개 · 버전 배지 %d개'
          '(기능 장 %d개) — 어긋남 %d건'
          % (n_link, n_text, n_badge, len(feats), len(bad)))
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()


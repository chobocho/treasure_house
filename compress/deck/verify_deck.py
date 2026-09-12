# -*- coding: utf-8 -*-
"""역검증 — 완성된 덱을 다시 읽어 소스·출력과 글자 단위로 대조한다.

   조립기가 채웠으니 맞을 수밖에 없다고 생각하기 쉽지만, 실제로는
     · 조각을 손으로 고쳐 넣은 코드가 섞여 들어가고
     · 소스를 고친 뒤 덱을 다시 만들지 않고 커밋하고
     · out/ 의 출력이 낡은 채로 남는다.
   이 도구는 그 셋을 전부 잡는다. "덱은 산출물일 뿐 원본이 아니다" 는 규율을
   기계로 강제하는 장치다.

       python3 deck/verify_deck.py
"""
import html
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(os.path.dirname(BASE), '압축_대백과사전.html')
OUTDIR = os.path.join(BASE, 'out')
TAG = re.compile(r'<[^>]+>')


def read(p):
    return io.open(p, encoding='utf-8').read()


def cut(text, spec):
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    if not spec:
        return '\n'.join(lines)
    a, b = (int(x) for x in spec.split('-'))
    return '\n'.join(lines[a - 1:b])


def plain(block):
    return html.unescape(TAG.sub('', block))


def main():
    if not os.path.exists(DECK):
        print('덱이 아직 없다 — python3 deck/build_deck.py 먼저')
        return 1
    doc = read(DECK)
    st = dict(code=0, code_ok=0, code_bad=0, untagged=0, out=0, out_ok=0, out_bad=0)
    problems = []

    arts = re.findall(r'<article[^>]*\sid="([^"]+)"[^>]*>(.*?)</article>', doc, re.S)
    for sid, body in arts:
        # '설명용' 배지가 붙은 화면의 코드 조각은 파일에서 잘라 온 것이 아니라
        # 설명하려고 그린 것이다. 그 사실이 화면에 배지로 적혀 있으므로
        # data-src 가 없다고 문제 삼지 않는다. 배지 없이 그린 조각은 문제다 —
        # 독자가 "이건 진짜 파일" 이라고 오해하기 때문이다.
        illus = 'class="tier ill"' in body
        for m in re.finditer(r'<pre><code([^>]*)>(.*?)</code></pre>', body, re.S):
            attrs, inner = m.group(1), m.group(2)
            if illus and 'data-src' not in attrs:
                st['illus'] = st.get('illus', 0) + 1
                continue
            src = re.search(r'data-src="([^"]+)"', attrs)
            if not src:
                if inner.count('\n') >= 2:
                    st['untagged'] += 1
                    problems.append(('data-src 없는 긴 코드', sid, plain(inner)[:48]))
                continue
            st['code'] += 1
            spec = re.search(r'data-lines="([^"]+)"', attrs)
            f = os.path.join(BASE, src.group(1))
            if not os.path.exists(f):
                st['code_bad'] += 1
                problems.append(('소스 없음', sid, src.group(1)))
                continue
            want = cut(read(f), spec.group(1) if spec else None)
            if plain(inner) == want:
                st['code_ok'] += 1
            else:
                st['code_bad'] += 1
                problems.append(('코드 불일치', sid, src.group(1)))

        for m in re.finditer(r'<pre class="term"([^>]*)>(.*?)</pre>', body, re.S):
            attrs, inner = m.group(1), m.group(2)
            o = re.search(r'data-out="([^"]+)"', attrs)
            if not o:
                continue
            st['out'] += 1
            spec = re.search(r'data-lines="([^"]+)"', attrs)
            f = os.path.join(OUTDIR, o.group(1))
            if not os.path.exists(f):
                st['out_bad'] += 1
                problems.append(('출력 없음', sid, o.group(1)))
                continue
            want = cut(read(f).rstrip('\n'), spec.group(1) if spec else None)
            if plain(inner) == want:
                st['out_ok'] += 1
            else:
                st['out_bad'] += 1
                problems.append(('출력 불일치', sid, o.group(1)))

    # 자기완결형 계약 — 덱 안에 바깥을 가리키는 자원이 없어야 한다
    for pat, why in ((r'<script[^>]+\bsrc=', '외부 스크립트'),
                     (r'<link[^>]+href="https?:', '외부 스타일시트'),
                     (r'<img[^>]+src="https?:', '외부 이미지'),
                     (r'@import\s+url\(', '외부 폰트/CSS')):
        if re.search(pat, doc):
            problems.append((why, '-', pat))

    # 실명·사내 호스트가 새어 나가지 않았는가
    for word in ('samsung', 'seunghwa', '@sec.', 'corp.'):
        if word.lower() in doc.lower():
            problems.append(('실명·실호스트 유출 의심', '-', word))

    print('슬라이드 %d장' % len(arts))
    print('코드 블록 %d개 — 일치 %d · 불일치 %d · data-src 없는 긴 코드 %d'
          % (st['code'], st['code_ok'], st['code_bad'], st['untagged']))
    print('출력 블록 %d개 — 일치 %d · 불일치 %d'
          % (st['out'], st['out_ok'], st['out_bad']))
    print("설명용으로 그린 조각 %d개 (화면에 '설명용' 배지가 붙어 있다)"
          % st.get('illus', 0))
    if problems:
        print('\n문제 %d건' % len(problems))
        for p in problems[:25]:
            print('  %-22s %-24s %s' % p)
        return 1
    print('역검증 통과 — 덱의 모든 코드·출력이 원본과 같다')
    return 0


if __name__ == '__main__':
    sys.exit(main())

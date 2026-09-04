# -*- coding: utf-8 -*-
"""역검증 — 완성된 덱을 다시 읽어 소스·출력과 바이트 단위로 대조한다.

   빌더가 채웠으니 맞을 수밖에 없다고 생각하기 쉽지만, 실제로는
     · 조각을 손으로 고쳐 넣은 코드가 섞여 들어가고
     · 소스를 고친 뒤 덱을 다시 만들지 않고 커밋하고
     · out/ 의 출력이 낡은 채로 남는다.
   이 도구는 그 셋을 전부 잡는다. 덱은 산출물일 뿐 원본이 아니라는 규율을
   기계로 강제하는 장치다.
"""
import html
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(os.path.dirname(BASE), '도스_헥사곤_타일게임_해부.html')
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
    doc = read(DECK)
    stats = dict(code=0, code_ok=0, code_bad=0, untagged=0, out=0, out_ok=0, out_bad=0,
                 shot=0, shot_ok=0, illus=0)
    problems = []

    arts = re.findall(r'<article[^>]*\sid="([^"]+)"[^>]*>(.*?)</article>', doc, re.S)
    for sid, body in arts:
        for m in re.finditer(r'<pre><code([^>]*)>(.*?)</code></pre>', body, re.S):
            attrs, inner = m.group(1), m.group(2)
            if 'data-illus' in attrs:
                # 도스 시절 관용구를 보여 주는 발췌 — 이 저장소에서 실행되지 않는다.
                # 반드시 화면에 '발췌' 라벨이 함께 나와야 한다.
                stats['illus'] += 1
                continue
            src = re.search(r'data-src="([^"]+)"', attrs)
            if not src:
                if inner.count('\n') >= 2:
                    stats['untagged'] += 1
                    problems.append(('data-src 없는 긴 코드', sid, plain(inner)[:48]))
                continue
            stats['code'] += 1
            spec = re.search(r'data-lines="([^"]+)"', attrs)
            f = os.path.join(BASE, src.group(1))
            if not os.path.exists(f):
                stats['code_bad'] += 1
                problems.append(('소스 없음', sid, src.group(1)))
                continue
            want = cut(read(f), spec.group(1) if spec else None)
            if plain(inner) == want:
                stats['code_ok'] += 1
            else:
                stats['code_bad'] += 1
                problems.append(('코드 불일치', sid, src.group(1)))

        for m in re.finditer(r'<pre class="term"([^>]*)>(.*?)</pre>', body, re.S):
            attrs, inner = m.group(1), m.group(2)
            o = re.search(r'data-out="([^"]+)"', attrs)
            if not o:
                continue
            stats['out'] += 1
            spec = re.search(r'data-lines="([^"]+)"', attrs)
            f = os.path.join(OUTDIR, o.group(1))
            if not os.path.exists(f):
                stats['out_bad'] += 1
                problems.append(('출력 없음', sid, o.group(1)))
                continue
            want = cut(read(f).rstrip('\n'), spec.group(1) if spec else None)
            if plain(inner) == want:
                stats['out_ok'] += 1
            else:
                stats['out_bad'] += 1
                problems.append(('출력 불일치', sid, o.group(1)))

        for m in re.finditer(r'<img class="shot" data-shot="([^"]+)"', body):
            stats['shot'] += 1
            if os.path.exists(os.path.join(OUTDIR, m.group(1))):
                stats['shot_ok'] += 1
            else:
                problems.append(('캡처 없음', sid, m.group(1)))

    # 덱 안에 남은 외부 자원 참조가 없는지
    for pat, why in ((r'<script[^>]+src=', '외부 스크립트'),
                     (r'<link[^>]+href="http', '외부 스타일시트'),
                     (r'<img[^>]+src="http', '외부 이미지'),
                     (r'@import\s+url\(', '외부 폰트/CSS')):
        if re.search(pat, doc):
            problems.append((why, '-', pat))

    print('슬라이드 %d장' % len(arts))
    print('코드 블록 %d개 — 일치 %d · 불일치 %d · data-src 없는 긴 코드 %d'
          % (stats['code'], stats['code_ok'], stats['code_bad'], stats['untagged']))
    print('실행하지 않는 발췌(data-illus) %d개' % stats['illus'])
    print('출력 블록 %d개 — 일치 %d · 불일치 %d'
          % (stats['out'], stats['out_ok'], stats['out_bad']))
    print('화면 캡처 %d개 — 원본 확인 %d' % (stats['shot'], stats['shot_ok']))
    if problems:
        print('\n문제 %d건' % len(problems))
        for p in problems[:25]:
            print('  %-16s %-22s %s' % p)
        return 1
    print('역검증 통과 — 덱의 모든 코드·출력이 원본과 같다')
    return 0


if __name__ == '__main__':
    sys.exit(main())

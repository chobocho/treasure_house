# -*- coding: utf-8 -*-
"""14~16부(세 언어 전체 소스) 조각을 만든다.

   줄 수와 조각 수를 손으로 적으면 소스를 고칠 때마다 어긋난다.
   설명 글만 사람이 쓰고, 숫자는 여기서 세어 넣는다.

   실행:  python3 tools/gen_fullsrc.py
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'deck'))
import chunks                                                  # noqa: E402

MODULES = [
    ('fixed', '16.16 고정소수점과 CORDIC',
     '이 파일만 다른 모듈을 하나도 참조하지 않는다. 나머지 전부가 여기에 기댄다. '
     '분할 곱셈(정리 2.1)·뉴턴 제곱근(정리 2.2)·팔각 거리·CORDIC 표·비트 연산 없는 xor 가 들어 있다. '
     '<b>시프트 연산자가 한 번도 나오지 않는다</b> — 그것이 세 언어를 건너는 값이다.'),
    ('proj', '투영과 역투영',
     '이 문서의 심장. 곱셈 두 번으로 투영하고 나눗셈 두 번으로 되돌린다. '
     '도스식 모서리 마스크와, 마름모 정의로 직접 찾는 느린 버전이 나란히 있다. '
     '느린 버전은 게임에서 쓰이지 않는다 — 빠른 식을 매번 검산하기 위해서만 있다.'),
    ('camera', '카메라',
     '가장 짧은 모듈. 데드존 추적과 클램프가 전부다. '
     '상태가 없어서 세이브에 카메라 좌표 두 개만 넣으면 정확히 복원된다.'),
    ('rng', '난수',
     '볼랜드 LCG 하나. 짧지만 <b>분할 곱</b>이 없으면 루아와 타입스크립트에서 조용히 틀린다. '
     '주기가 2<sup>32</sup> 인 것은 Hull–Dobell 로 보장되고, 하위 비트의 주기가 짧은 것도 그대로 남아 있다.'),
    ('gamemap', '지형 맵과 생성',
     '한 칸 1바이트, 지형표, 다이아몬드-스퀘어, 3×3 평활, 마을 스탬프, RLE. '
     '이름이 map 이 아닌 것은 파이썬 내장과 겹치지 않게 하려는 것이고, 세 언어가 같은 이름을 쓴다.'),
    ('sortdag', '그리기 순서',
     '상자 부분순서와 위상정렬. 순환을 감지해 끊는 곳이 여기다. '
     '간선 만들기를 화면 x 로 훑어 비교 횟수를 22분의 1로 줄였다.'),
    ('raster', '래스터',
     '팔레트·명암표·스프라이트 적재·런 단위 클리핑 블릿·더티 렉트·팔레트 사이클링·PPM. '
     '가장 긴 함수가 <code class="nb">build_light</code> 인데, 시작할 때 한 번만 돈다.'),
    ('path', '경로 탐색',
     '여덟 방향표, 모서리 자르기 금지, 옥타일 휴리스틱, 원형 양동이 큐, 다익스트라와 A*. '
     '휴리스틱에 나눗셈이 없는 것이 정리 8.1·8.2 를 짧게 만든다.'),
    ('los', '시야·안개·조명',
     '브레젠험 한 함수가 셋을 다 만든다. <code class="nb">recount</code> 는 세이브를 되돌린 뒤 '
     '파생 값을 다시 세우는 자리 — 이식자 둘이 독립적으로 지적해 생긴 함수다.'),
    ('dice', '주사위와 전투',
     '합성곱 분포, 명중 판정, 성장 곡선. 빗나갔을 때 피해 굴림을 건너뛰는 것까지 명세다.'),
    ('save', '저장과 CRC',
     'GF(2) 다항식 나눗셈과 빅 엔디언 직렬화. 비트 연산자를 쓰지 않고 CRC 를 만든다.'),
    ('game', '게임 상태와 틱',
     '가장 긴 파일. 엔티티, 여섯 단계짜리 틱, 시나리오 실행기, 트레이스, 렌더 파이프라인. '
     '렌더가 게임 상태를 바꾸지 않는다는 규율이 여기서 지켜진다.'),
    ('main', 'CLI',
     'prim / trace / render / bench. <code class="nb">prim_report</code> 의 서식 문자열 하나하나가 명세다 — '
     '세 언어가 같은 208줄을 찍어야 한다.'),
]

LANGS = [
    ('14', 'py', 'py/isorpg/%s.py', '파이썬', 'py',
     '파이썬 구현은 <b>참조</b>다. 표준 라이브러리만 쓰고, 골든 벡터를 여기서 얼린다. '
     '느리지만 읽기 쉽고, 무엇보다 <b>정수 자릿수 제한이 없어</b> 다른 두 언어의 분할 산술을 검산할 수 있다.'),
    ('15', 'lua', 'lua/isorpg/%s.lua', '루아 5.1', 'lua',
     '루아 구현은 <b>LuaJIT 과 LÖVE 11.5 양쪽</b>에서 돈다. 정수가 없고, 비트 연산자가 없고, '
     '테이블이 1-기반이며, <code class="nb">0</code> 이 참이다. 네 가지가 전부 함정이다.'),
    ('16', 'ts', 'ts/src/%s.ts', '타입스크립트', 'ts',
     '타입스크립트 구현은 <b>이 문서 안에서 살아 움직인다</b>. '
     '<code class="nb">&gt;&gt;</code> 가 32비트로 잘리므로 시프트를 아예 쓰지 않고, '
     '튜플 비교가 없어 비교자를 손으로 쓴다.'),
]


def count_lines(path):
    text = io.open(os.path.join(BASE, path), encoding='utf-8').read()
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines, text


def main():
    for num, lang, pat, name, prefix, intro in LANGS:
        out = []
        total_lines = 0
        total_chunks = 0
        rows = []
        for mod, title, _ in MODULES:
            path = pat % mod
            lines, text = count_lines(path)
            parts = chunks.split('\n'.join(lines), lang)
            total_lines += len(lines)
            total_chunks += len(parts)
            rows.append((mod, path, len(lines), len(parts), title))

        out.append('<article class="card section" id="s%s">' % num)
        out.append('<p class="chnum">%s부</p>' % num)
        out.append('<h2>%s 전문</h2>' % name)
        out.append('<p class="chsub">엔진 %d줄을 한 줄도 빼지 않고 싣는다.<br>'
                   '조각은 기계가 나눴고, 빠진 줄이 없음은 커버리지 검사가 증명한다</p>'
                   % total_lines)
        out.append('</article>\n')

        out.append('<article class="card" id="s%s-map">' % num)
        out.append('<h3>이 부의 지도</h3>')
        out.append('<p class="lead">%s</p>' % intro)
        out.append('<div class="tblwrap">\n<table class="kv">')
        out.append('<tr><th>모듈</th><th>줄</th><th>조각</th><th>내용</th></tr>')
        for mod, path, nl, nc, title in rows:
            out.append('<tr><td><code class="nb">%s</code></td><td class="num">%d</td>'
                       '<td class="num">%d</td><td>%s</td></tr>' % (mod, nl, nc, title))
        out.append('<tr><td><b>합계</b></td><td class="num"><b>%d</b></td>'
                   '<td class="num"><b>%d</b></td><td>—</td></tr>'
                   % (total_lines, total_chunks))
        out.append('</table>\n</div>')
        out.append('<div class="key">조각 나누는 자리는 <b>최상위 정의가 시작하는 줄</b>입니다. '
                   '함수 한가운데서 끊긴 코드는 읽히지 않기 때문입니다. '
                   '한 조각은 최대 46줄입니다.</div>')
        out.append('</article>\n')

        for (mod, title, desc), (_m, path, nl, nc, _t) in zip(MODULES, rows):
            out.append('<article class="card" id="s%s-f-%s">' % (num, mod))
            out.append('<h3>%s — %s</h3>' % (os.path.basename(path), title))
            out.append('<div class="src"><b>%s</b><span class="ln">%d줄</span>'
                       '<span>%d조각</span></div>' % (path, nl, nc))
            out.append('<p>%s</p>' % desc)
            out.append('</article>\n')
            out.append('<!--FULLSRC lang=%s file=%s prefix=%s-%s title=%s-->\n'
                       % (lang, path, prefix, mod, os.path.basename(path)))

        fn = os.path.join(BASE, 'deck', 'sections',
                          '%s-%s.html' % (num, prefix))
        io.open(fn, 'w', encoding='utf-8').write('\n'.join(out))
        print('%s  %d줄 %d조각 → %d장 예상'
              % (os.path.basename(fn), total_lines, total_chunks,
                 total_chunks + 2 + len(MODULES)))


if __name__ == '__main__':
    main()

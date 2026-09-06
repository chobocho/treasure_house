# -*- coding: utf-8 -*-
"""24~26부(세 언어 전체 소스) 조각을 만든다.

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
    ('fixed', '16.16 고정소수점과 거리 척도',
     '이 파일만 다른 모듈을 하나도 참조하지 않는다. 나머지 전부가 여기에 기댄다. '
     '분할 곱셈(정리 2.1)·뉴턴 제곱근(정리 2.2)·네 가지 거리 척도·비교만으로 하는 8방향 판별이 들어 있다. '
     '<b>시프트 연산자가 한 번도 나오지 않는다</b> — 그것이 세 언어를 건너는 값이다.'),
    ('const', '상수표와 유닛·건물표',
     '§0 의 상수와 §25 의 유닛·건물표가 여기 한 곳에 있다. 함수가 없고 숫자만 있다. '
     '같은 상수를 두 군데 적으면 한 쪽만 고치는 날이 오고, 그날 세 언어가 갈린다 — '
     '<code class="nb">test_const</code> 가 이 파일을 <code class="nb">SPEC.md</code> 의 '
     '마크다운 표와 직접 대조한다.'),
    ('rng', '난수',
     '볼랜드 계열 LCG 하나. 짧지만 <b>분할 곱</b>이 없으면 루아와 타입스크립트에서 조용히 틀린다. '
     '주기가 2<sup>32</sup> 인 것은 Hull–Dobell 로 보장되고, 모듈로 편향을 없애는 기각 루프가 붙어 있다.'),
    ('tmap', '지형 맵과 오토타일',
     '한 칸 1바이트씩 두 평면, 8이웃 비트마스크의 47클래스 정규화, 4모서리 16케이스, '
     '유니온–파인드 연결 성분, RLE 저장. 비트 연산자 없이 비트마스크를 다룬다.'),
    ('mapgen', '맵 생성',
     '셀룰러 오토마타·다이아몬드-스퀘어·정수 포아송 디스크·2회 대칭. '
     '재시도 상한이 있는 것이 중요하다 — 무한 루프는 디싱크보다 나쁘다.'),
    ('circle', '원 마스크',
     '미드포인트 래스터라이저 하나가 시야·스플래시·자원 스탬프를 전부 만든다. '
     '격자점 개수가 가우스 원 문제의 값과 같은지가 이 모듈의 검산이다.'),
    ('spatial', '엔티티와 공간 분할',
     '배열의 구조체(SoA), 인덱스+세대 핸들, 8×8 타일 버킷. '
     '버킷 안의 순서를 오름차순으로 유지하는 한 줄이 결정론을 지킨다.'),
    ('select', '선택과 명령',
     '픽킹·상자 선택·컨트롤 그룹·명령 큐. 이 모듈은 시뮬레이션 상태를 절대 쓰지 않는다 — '
     '명령을 만들어 네트워크 지연 큐에 넣을 뿐이다.'),
    ('path', '경로 탐색',
     '옥타일 휴리스틱과 그 허용성·일관성 증명, 양동이 큐 다익스트라, 손으로 쓴 이진 힙, '
     '도달 불가 목표의 대체점, 경로 캐시.'),
    ('hpa', '계층 경로 탐색',
     '8×8 클러스터·입구·추상 그래프·정련. 최적이 아니며, 그 초과 비율을 실측해 싣는다.'),
    ('jps', '점프 포인트 탐색',
     '가지치기 규칙과 재귀 점프. A* 와 비용이 같다는 것을 정리로 옮겨 적지 않고 전수 검사로 증명한다.'),
    ('flow', '흐름장과 클리어런스',
     '적분장·경사장·정사각 여유·브러시파이어. 유닛이 많아질수록 A* 를 이기는 지점이 어디인가.'),
    ('move', '이동과 충돌',
     '서브타일 보간, 대각 보정, 타일 예약 불변식, 밀치기와 교착 해소, 대형 회전. '
     '교착은 해결되지 않는다 — 24틱 뒤에 포기할 뿐이고, 그렇게 적었다.'),
    ('fog', '시야와 안개',
     '참조 카운트 세 평면과 그 불변식. 증분 갱신은 빠르지만 한 번 어긋나면 영원히 어긋나므로, '
     '전수 재계산 검증 주기가 명세에 박혀 있다.'),
    ('combat', '전투',
     '체비셰프 사거리, 워크래프트 II 의 피해 공식, 직선·포물선 투사체, 스플래시, 란체스터 시뮬레이터.'),
    ('econ', '경제와 기술 트리',
     '채집기 FSM 과 수입률 공식, 선불 생산 큐, 배치 판정, DAG 위상 정렬, 인구 상한.'),
    ('ai', 'AI',
     '유닛 FSM, 영향 지도(합성곱 세 번), 위협 지도, 여섯 줄짜리 빌드 오더, 정찰. '
     'AI 도 안개를 존중한다 — 그러지 않으면 게임이 아니다.'),
    ('sim', '시뮬레이션',
     '가장 긴 파일. SoA 엔티티, 아홉 단계 틱, 명령 정렬, 이벤트 로그, FNV-1a 상태 해시, 트리거. '
     '상태를 바꾸는 함수가 <code class="nb">step</code> 하나뿐이라는 규율이 여기서 지켜진다.'),
    ('net', '락스텝 네트워크',
     '지연·지터가 있는 인프로세스 네트워크와 디싱크 검출기. '
     '부동소수점 버그를 일부러 주입하는 스위치도 여기 있다.'),
    ('replay', '저장·리플레이·압축',
     'GF(2) 다항식 나눗셈(CRC-16), 명령 로그, RLE, LZSS. 상태는 한 바이트도 저장하지 않는다.'),
    ('speaker', 'PC 스피커',
     'PIT 분주값 표와 사각파 WAV 합성. 소리를 내지는 않지만 바이트가 같으면 소리도 같다.'),
    ('raster', '래스터',
     '팔레트·명암표·RLE 스프라이트·런 단위 클리핑 블릿·플레이어 색 리맵·좌우 반전·더티 렉트·PPM. '
     '세 언어가 바이트 단위로 같은 화면을 만드는 곳이 여기다.'),
    ('render', '화면 구성',
     '레이어 여덟 겹, y 정렬, 미니맵 축소와 역변환, 안개 오버레이, 패널. '
     '렌더가 게임 상태를 바꾸지 않는다는 규율이 여기서 지켜진다.'),
    ('main', 'CLI',
     'prim / trace / hashes / render / lockstep / replay / bench / speaker. '
     '<code class="nb">prim_report</code> 의 서식 문자열 하나하나가 명세다 — 세 언어가 같은 줄을 찍어야 한다.'),
]

# 언어 하나에만 있는 파일. 타입스크립트에는 printf 가 없어서 서식 도우미가
# 따로 필요했다 — 세 언어가 같은 모듈 목록을 갖는다는 원칙의 유일한 예외이며,
# 그래서 여기 따로 적는다.
EXTRA = {
    'ts': [('fmt', '서식 도우미',
            '자바스크립트에는 printf 가 없다. <code class="nb">prim</code> 보고서는 '
            '294줄이 열 맞춰 있고 한 칸만 어긋나도 <code class="nb">cmp</code> 가 실패하므로, '
            '자리맞춤과 16진 서식을 손으로 만들었다. '
            '<code class="nb">pyRepr</code> 은 13절의 파이썬 <code class="nb">%r</code> 을 재현한다.')],
}

LANGS = [
    ('24', 'py', 'py/rts/%s.py', '파이썬', 'py',
     '파이썬 구현은 <b>참조</b>다. 표준 라이브러리만 쓰고, 골든 벡터를 여기서 얼린다. '
     '느리지만 읽기 쉽고, 무엇보다 <b>정수 자릿수 제한이 없어</b> 다른 두 언어의 분할 산술을 검산할 수 있다.'),
    ('25', 'lua', 'lua/rts/%s.lua', '루아 5.1', 'lua',
     '루아 구현은 <b>LuaJIT 과 LÖVE 11.5 양쪽</b>에서 돈다. 정수가 없고, 비트 연산자가 없고, '
     '테이블이 1-기반이며, <code class="nb">0</code> 이 참이다. 네 가지가 전부 함정이다.'),
    ('26', 'ts', 'ts/src/%s.ts', '타입스크립트', 'ts',
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
        mods = MODULES + EXTRA.get(lang, [])
        for mod, title, _ in mods:
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

        for (mod, title, desc), (_m, path, nl, nc, _t) in zip(mods, rows):
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

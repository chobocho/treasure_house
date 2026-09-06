# -*- coding: utf-8 -*-
"""gen_appendix.py — 아직 덱에 안 실린 소스 줄을 찾아 부록 섹션을 만든다.

두 번 도는 구조다:
  1) 부록을 뺀 채로 덱을 한 번 조립해서 "어느 줄이 빠졌는지" 알아낸다
  2) 그 줄들을 조각으로 잘라 sections/10_appendix.html 을 쓴다

왜 손으로 안 하는가. 소스가 11,000줄이 넘고 파일이 60개가 넘는다.
"어느 줄이 아직 안 실렸나"를 사람이 추적하면 반드시 어딘가가 빠진다.
빠진 줄을 세는 도구가 이미 있으니, 그 도구에게 목록을 물어보는 편이 낫다.
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
SECD = os.path.join(HERE, 'sections')
OUTF = os.path.join(SECD, '10_appendix.html')

sys.path.insert(0, HERE)

# 커버리지 대상 = 모든 .go + go.mod + Makefile + ai/weights.json
SKIP_DIRS = {'out', 'deck', 'test', 'scratch'}


def covered_files():
    out = []
    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for f in sorted(files):
            if f.endswith('.go'):
                out.append(os.path.relpath(os.path.join(root, f), SRC))
    out += ['go.mod', 'Makefile', 'ai/weights.json']
    return sorted(out)


def measure():
    """부록을 뺀 채로 조립해서 커버리지를 얻는다."""
    if os.path.exists(OUTF):
        os.remove(OUTF)
    for mod in ('build_deck',):
        if mod in sys.modules:
            del sys.modules[mod]
    import build_deck as bd
    import json
    bd.SECTIONS = json.load(io.open(os.path.join(SECD, 'sections.json'), encoding='utf-8'))
    bd.build()
    return bd


def missing_ranges(bd, name):
    """아직 안 실린 줄 번호를 이어지는 구간 목록으로."""
    n = bd.nlines(name)
    cov = bd._cover.get(name)
    if cov is None:
        return [(1, n)]
    out, start = [], None
    for i in range(n):
        if cov[i] == 0:
            if start is None:
                start = i + 1
        elif start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, n))
    return out


# 자르기 좋은 자리 — 여기서 끊으면 슬라이드가 문장 중간에서 잘리지 않는다.
HARD = re.compile(r'^(?:func |type |var |const |import |package |// ──|\t*//go:|[A-Za-z_][\w./$()-]*:)')
LIMIT = 40


def split(name, lo, hi, lines):
    """[lo, hi] 를 LIMIT 줄 이하 조각으로 자른다. 함수 경계를 우선한다."""
    out = []
    start = lo
    while start <= hi:
        end = min(start + LIMIT - 1, hi)
        if end < hi:
            best = None
            for i in range(end, start + LIMIT // 2, -1):
                if HARD.match(lines[i]):      # 다음 줄이 새 블록의 시작
                    best = i
                    break
            if best is None:
                for i in range(end, start + LIMIT // 2, -1):
                    if lines[i - 1].strip() == '':
                        best = i - 1
                        break
            if best:
                end = best
        out.append((start, end))
        start = end + 1
    return out


# 파일마다 한 줄짜리 안내. 부록이 "덤프"가 아니라 지도가 되게 한다.
BLURB = {
    'core/': '규칙만 담은 층. Bubble Tea 를 import 하지 않는다.',
    'ai/': '8특징 평가와 1수 탐색. core 만 안다.',
    'ui/': '그리기와 키 배치. 게임 규칙은 모른다.',
    'game/': '1인용 Bubble Tea 모델.',
    'battle/': '1:1 규칙과 두 자리 모델.',
    'menu/': '시작 화면. 고른 모드의 모델로 바꿔 낀다.',
    'cmd/': '깃발을 읽고 모델 하나를 띄운다.',
    'examples/': '2~3부의 예제 사다리.',
    'tools/': '기록과 변환 도구.',
}


def blurb(name):
    for k, v in BLURB.items():
        if name.startswith(k):
            return v
    return '모듈과 빌드.'


def main():
    bd = measure()
    files = covered_files()

    slides = []
    for name in files:
        try:
            lines = bd.load(name)
        except IOError:
            continue
        gaps = missing_ranges(bd, name)
        if not gaps:
            continue
        chunks = []
        for lo, hi in gaps:
            chunks += split(name, lo, hi, lines)
        # 슬라이드 하나에 조각 셋까지
        for i in range(0, len(chunks), 3):
            part = chunks[i:i + 3]
            slides.append((name, part, i // 3 + 1, (len(chunks) + 2) // 3))

    body = []
    body.append('<!--SLIDE sec=10 t="부록을 읽는 법"-->\n'
                '<h1>부록 — 전체 소스</h1>\n'
                '<p class="lead">앞의 열 개 부에서 다 보여 주지 못한 줄을 여기 전부 싣는다.\n'
                '이 부록이 끝나면 <b>tetris_tui/ 의 모든 줄이 이 덱 안에 정확히 한 번씩</b> 있다.</p>\n'
                '<p>순서는 파일 이름순이다. 각 조각의 머리에 파일과 줄 번호가 적혀 있으니,\n'
                '저장소의 그 자리와 그대로 맞춰 볼 수 있다.</p>\n'
                '<div class="note"><b>왜 이런 부록을 두는가</b>\n'
                '문서가 코드의 "좋은 부분"만 보여 주면, 읽는 사람은 나머지가 어떻게 생겼는지\n'
                '끝내 모른다. 오류 처리도, 접근자도, Makefile 도 전부 프로그램의 일부다.\n'
                '빠짐없이 싣는 편이 정직하고, 빌더가 그걸 세어 준다.</div>\n')

    for name, part, idx, total in slides:
        title = name if total == 1 else '%s (%d/%d)' % (name, idx, total)
        head = ['<!--SLIDE sec=10 t="%s"-->' % title,
                '<h2>%s</h2>' % title]
        if idx == 1:
            head.append('<p class="small mut">%s</p>' % blurb(name))
        for lo, hi in part:
            head.append('<!--CODE file=%s lines=%d-%d cap="%s">' % (name, lo, hi, name) + '-->')
        body.append('\n'.join(head) + '\n')

    io.open(OUTF, 'w', encoding='utf-8', newline='').write('\n'.join(body))
    print('부록 %d장 생성 → sections/10_appendix.html' % (len(slides) + 1))


if __name__ == '__main__':
    main()

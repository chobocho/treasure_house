# -*- coding: utf-8 -*-
"""덱이 인용할 숫자를 한 파일에 모은다 — out/measure.txt (8단계).

   덱 본문에 숫자를 손으로 적지 않기 위한 장치다. 여기서 나온 값만
   `<!--OUT file=out/measure.txt lines=A-B-->` 로 인용한다. 숫자가 바뀌면
   이 파일이 바뀌고, 덱을 다시 조립하면 본문도 바뀐다.

   실행:  python3 tools/measure.py        (make measure 뒤에 돌릴 것)
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'out')
GOLDEN = os.path.join(BASE, 'golden')
sys.path.insert(0, os.path.join(BASE, 'py'))


def read(path):
    try:
        return io.open(path, encoding='utf-8').read()
    except IOError:
        return ''


def size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def lines_of(pattern_dir, ext):
    total, files = 0, 0
    d = os.path.join(BASE, pattern_dir)
    if not os.path.isdir(d):
        return 0, 0
    for name in sorted(os.listdir(d)):
        if name.endswith(ext):
            total += len(read(os.path.join(d, name)).split('\n')) - 1
            files += 1
    return total, files


def jsonl_stats(path):
    """트레이스 한 줄씩 — 이벤트 종류별 개수와 처음 일어난 틱."""
    text = read(path).strip()
    if not text:
        return None
    kinds = {}
    first = {}
    last = None
    for ln in text.split('\n'):
        d = json.loads(ln)
        last = d
        for e in d['ev']:
            kinds[e[0]] = kinds.get(e[0], 0) + 1
            if e[0] not in first:
                first[e[0]] = d['t']
    return kinds, first, last


EV = {0: 'SPAWN', 1: 'DIE', 2: 'HIT', 3: 'BUILD_DONE', 4: 'MINE',
      5: 'UNLOAD', 6: 'ORDER', 7: 'WIN', 8: 'MESSAGE'}


def main():
    o = []
    o.append('== 1. 소스 규모 ==')
    for d, ext, label in (('py/rts', '.py', '파이썬 엔진'),
                          ('py/tests', '.py', '파이썬 시험'),
                          ('lua/rts', '.lua', '루아 엔진'),
                          ('lua/tests', '.lua', '루아 시험'),
                          ('ts/src', '.ts', '타입스크립트 엔진'),
                          ('ts/tests', '.ts', '타입스크립트 시험'),
                          ('tools', '.py', '골든 생성기·도구')):
        n, f = lines_of(d, ext)
        o.append('%-18s %5d줄 · %2d파일' % (label, n, f))

    o.append('')
    o.append('== 2. 골든 파일 ==')
    for name in ('prim.txt', 'autotile.txt', 'circle.txt', 'palette.txt',
                 'sprites.txt', 'font.txt', 'script.txt', 'map_start.txt',
                 'trace.jsonl', 'hashes.txt', 'replay.bin'):
        p = os.path.join(GOLDEN, name)
        o.append('%-16s %8d바이트' % (name, size(p)))

    o.append('')
    o.append('== 3. 리플레이 대 상태 스냅샷 ==')
    rb = size(os.path.join(GOLDEN, 'replay.bin'))
    snap = 4096 * 1200
    o.append('리플레이(명령 로그, 1200틱)  %7d바이트' % rb)
    o.append('상태 스냅샷 추정(4KB × 1200틱) %7d바이트' % snap)
    if rb:
        o.append('비율 %d배 — 상태를 한 바이트도 저장하지 않는다' % (snap // rb))

    o.append('')
    o.append('== 4. 골든 시나리오 (스크립트 주도, AI 꺼짐) ==')
    st = jsonl_stats(os.path.join(GOLDEN, 'trace.jsonl'))
    if st:
        kinds, first, last = st
        o.append('길이 %d틱 · 마지막 엔티티 %d기' % (last['t'], last['n']))
        o.append('크레딧 %s · 인구 %s / %s'
                 % (last['cr'], last['su'], last['sc']))
        for k in sorted(kinds):
            o.append('  %-11s %4d건 (처음 %d틱)'
                     % (EV.get(k, str(k)), kinds[k], first[k]))

    o.append('')
    o.append('== 5. AI 대 AI (스크립트 없음) ==')
    for name, label in (('aigame.jsonl', '여섯 줄 규칙'),
                        ('aigame7.jsonl', '일곱 줄 (발전소 추가)')):
        st = jsonl_stats(os.path.join(OUT, name))
        if not st:
            continue
        kinds, first, last = st
        o.append('%s — 마지막 엔티티 %d기 · 인구 %s / %s'
                 % (label, last['n'], last['su'], last['sc']))
        def when(k):
            return '%d틱' % first[k] if k in first else '없음'

        o.append('  첫 명중 %s · 첫 사망 %s · 건물 완성 %d채'
                 % (when(2), when(1), kinds.get(3, 0)))

    o.append('')
    o.append('== 6. 성능 (make bench) ==')
    for ln in read(os.path.join(OUT, 'bench.txt')).strip().split('\n'):
        if ln:
            o.append(ln)

    o.append('')
    o.append('== 7. 락스텝과 디싱크 주입 ==')
    for ln in read(os.path.join(OUT, 'lockstep.txt')).strip().split('\n'):
        if ln:
            o.append(ln)

    o.append('')
    o.append('== 8. 압축 ==')
    from rts import replay as RP
    from rts import tmap as TM
    m = TM.TMap.load_text(read(os.path.join(GOLDEN, 'map_start.txt')))
    plane = bytes(bytearray(m.terrain))
    o.append('지형 평면 원본        %6d바이트' % len(plane))
    o.append('RLE                   %6d바이트 (%d%%)'
             % (len(RP.rle_encode(plane)),
                len(RP.rle_encode(plane)) * 100 // len(plane)))
    o.append('LZSS                  %6d바이트 (%d%%)'
             % (len(RP.lzss_encode(plane)),
                len(RP.lzss_encode(plane)) * 100 // len(plane)))

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    io.open(os.path.join(OUT, 'measure.txt'), 'w',
            encoding='utf-8').write('\n'.join(o) + '\n')
    print('\n'.join(o))


main()

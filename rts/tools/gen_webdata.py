# -*- coding: utf-8 -*-
"""ts/src/web/data.ts 생성 — golden/ 의 텍스트를 브라우저용 문자열 상수로 옮긴다.

   브라우저에는 파일이 없다. 그런데 엔진의 시작점은 맵 파일과 시나리오 스크립트를
   **읽는** 것이다(main.ts 의 golden()). 그래서 그 두 벌을 코드 안에 박아 둔다.

   손으로 박으면 언젠가 골든과 어긋난다 — 어긋난 순간 브라우저의 시뮬레이션은
   덱이 인용하는 숫자와 다른 게임이 되고, 그것을 알아챌 방법이 없다. 그래서
   생성한다. `make web` 이 매번 다시 만들므로 골든이 바뀌면 이 파일도 따라 바뀐다.

   한 줄에 한 원소인 배열로 낸다. 4KB 짜리 한 줄짜리 리터럴은 편집기에서도
   diff 에서도 읽을 수 없고, 이 저장소의 88칸 규칙도 어긴다.

   실행:  python3 tools/gen_webdata.py
"""
import io
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')
OUT = os.path.join(BASE, 'ts', 'src', 'web', 'data.ts')

HEAD = u'''// 골든 데이터 — **생성물이다. 손으로 고치지 말 것.**
//
// tools/gen_webdata.py 가 golden/ 에서 만든다. 브라우저에는 fs 가 없으므로
// 엔진이 파일에서 읽던 것(시작 맵·시나리오 스크립트·경로탐색 시험 맵)을
// 문자열로 들고 있는다. 팔레트와 스프라이트는 여기 없다 — raster.buildPalette()
// 와 raster.SPRITES 가 절차적으로 만들기 때문이다(§22.2·§22.7).

'''


def read(name):
    return io.open(os.path.join(GOLDEN, name), encoding='utf-8').read()


def lit(text):
    """텍스트를 줄 단위 배열 리터럴로. join('\\n') 이 원본을 그대로 되돌린다."""
    rows = text.split(u'\n')
    body = u',\n'.join(u"  %s" % json.dumps(r, ensure_ascii=False) for r in rows)
    return u'[\n%s,\n].join(\'\\n\')' % body


def main():
    parts = [HEAD]
    parts.append(u'// golden/map_start.txt — 64x64 · 2인 시작 위치. 시나리오와\n'
                 u'// 미니 RTS 데모가 같은 맵을 쓴다.\n')
    parts.append(u'export const MAP_START_TXT: string = %s;\n\n'
                 % lit(read('map_start.txt')))
    parts.append(u'// golden/script.txt — §18.6 시나리오. 트레이스를 만드는 입력이다.\n')
    parts.append(u'export const SCRIPT_TXT: string = %s;\n\n'
                 % lit(read('script.txt')))
    parts.append(u'// golden/map_1..6.txt — §8 경로탐색 시험 맵 여섯. 각 맵의 pairs 는\n'
                 u'// prim.txt 가 쓰는 것과 같은 출발·도착 쌍이다.\n')
    maps = []
    for i in range(1, 7):
        maps.append(lit(read('map_%d.txt' % i)))
    parts.append(u'export const MAPS_TXT: string[] = [\n%s,\n];\n'
                 % u',\n'.join(maps))
    text = u''.join(parts)
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(text)
    print(u'ts/src/web/data.ts  %d바이트 (맵 %d개 + 시작 맵 + 스크립트)'
          % (len(text.encode('utf-8')), 6))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""ts/src/web/data.ts 생성 — 골든 데이터를 브라우저용으로 소스에 박는다.

   덱 안에서 도는 미니 RPG 는 파일을 읽을 수 없다. 그래서 팔레트와 스프라이트,
   시나리오를 문자열 리터럴로 넣는다. 맵은 넣지 않는다 — 엔진이 씨앗에서 만든다.

   손으로 복사하지 않는 이유는 하나다. 골든이 바뀌면 이 파일도 같이 바뀌어야 하고,
   사람이 하면 반드시 어긋난다.

   실행:  python3 tools/gen_webdata.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')
OUT = os.path.join(BASE, 'ts', 'src', 'web', 'data.ts')

FILES = [('PALETTE_TXT', 'palette.txt'), ('TILES_RLE', 'tiles.rle'),
         ('SCRIPT_TXT', 'script.txt')]


def esc(s):
    return (s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${'))


def main():
    out = ['// 이 파일은 tools/gen_webdata.py 가 만든다. 손으로 고치지 말 것.',
           '// 골든 데이터를 브라우저용으로 박아 넣은 것이고, 내용은 golden/ 과 같다.',
           '']
    total = 0
    for name, fn in FILES:
        text = io.open(os.path.join(GOLDEN, fn), encoding='utf-8').read()
        total += len(text)
        out.append('/** golden/%s (%d바이트) */' % (fn, len(text.encode('utf-8'))))
        out.append('export const %s = `%s`;' % (name, esc(text)))
        out.append('')
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
    print('ts/src/web/data.ts  %d글자 (%d KB)' % (total, total // 1024))


if __name__ == '__main__':
    main()

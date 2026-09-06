# -*- coding: utf-8 -*-
"""deck/engine.js 생성 — 타입스크립트 엔진을 브라우저용 한 덩어리로 묶는다.

   덱은 자기완결형 파일 하나여야 하므로 번들러를 쓸 수 없다(그리고 쓰고 싶지도 않다).
   tsc 가 낸 CommonJS 모듈들을 아주 작은 로더로 감싸 이어 붙인다. 로더는 20줄이고,
   하는 일은 `require('./fixed')` 를 이름으로 찾아 주는 것뿐이다.

   fs 와 path 는 스텁을 준다. 브라우저 경로에서는 파일을 읽는 함수를 부르지 않고,
   골든 데이터는 ts/src/web/data.ts 에 문자열로 박혀 있다. 스텁이 불리면 즉시 터진다 —
   조용히 빈 값을 돌려주는 것보다 낫다.

   묶은 결과가 정말 같은 엔진인지는 tools/check_web.js 가 확인한다.

   실행:  cd ts && ./node_modules/.bin/tsc -p tsconfig.web.json
          python3 tools/bundle_web.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(BASE, 'ts', 'distweb')
OUT = os.path.join(BASE, 'deck', 'engine.js')

# 순서는 상관없다 — 로더가 필요할 때 평가한다. 읽기 좋으라고 의존 순서로 둔다.
# 엔진 24개 전부를 넣는다. 데모가 쓰지 않는 것(mapgen·net·replay·speaker)도
# 넣는 이유는 하나다 — "덱 안에서 도는 것은 ts/src 전부"라는 말이 참이어야 한다.
# main.ts 만 없다. 그것은 fs 로 골든 파일을 읽는 CLI 이고, 브라우저에는 파일이 없다.
MODULES = ['fmt', 'const', 'fixed', 'rng', 'tmap', 'mapgen', 'circle',
           'spatial', 'select', 'path', 'hpa', 'jps', 'flow', 'move', 'fog',
           'combat', 'econ', 'ai', 'sim', 'net', 'replay', 'speaker',
           'raster', 'render',
           'web/data', 'web/canvas', 'web/minirts']

LOADER = os.path.join(BASE, 'deck', 'base')


def read(name):
    return io.open(os.path.join(LOADER, name), encoding='utf-8').read()

def main():
    parts = [read('loader_head.js')]
    total = 0
    for name in MODULES:
        p = os.path.join(DIST, name + '.js')
        code = io.open(p, encoding='utf-8').read().rstrip('\n')
        total += len(code)
        # __dirname 을 인자로 받는다 — tsc 가 낸 코드에 그것이 남아 있고,
        # 브라우저에는 그런 전역이 없다. 없으면 모듈을 부르는 즉시 터진다.
        parts.append("  __def('%s', function (exports, require, module, __dirname) {\n"
                     "%s\n  });\n" % (name, code))
    parts.append(read('loader_tail.js'))
    text = ''.join(parts)
    io.open(OUT, 'w', encoding='utf-8').write(text)
    print('deck/engine.js  모듈 %d개  %d KB'
          % (len(MODULES), len(text.encode('utf-8')) // 1024))


if __name__ == '__main__':
    main()

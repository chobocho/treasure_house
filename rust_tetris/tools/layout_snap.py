# -*- coding: utf-8 -*-
"""layout_snap.py — 슬라이드 몇 장을 정해진 화면 크기로 정적 렌더링해 PNG 로 본다.

브라우저 자동화(Playwright)를 못 쓰는 기계에서 폭별 레이아웃을 눈으로 확인하는 대용품이다.
WeasyPrint(screen 미디어)로 그리므로 JS 는 돌지 않는다 — 하이라이트·페이지 번호·데모는 빠진다.
CSS 의 vh·미디어 쿼리는 페이지 크기를 따른다.

  python3 tools/layout_snap.py WxH id1 id2 ...   → scratch/layout/<W>x<H>-<id>.png
"""
import io, os, re, subprocess, sys

from weasyprint import HTML

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(os.path.dirname(SRC), 'Rust_테트리스_만들기.html')
OUT = os.path.join(SRC, 'scratch', 'layout')


def main():
    size, ids = sys.argv[1], sys.argv[2:]
    w, h = (int(v) for v in size.split('x'))
    doc = io.open(DECK, encoding='utf-8').read()
    doc = re.sub(r'<script\b.*?</script>', '', doc, flags=re.S)
    os.makedirs(OUT, exist_ok=True)
    for sid in ids:
        one = doc.replace(f'<article class="card" id="{sid}">',
                          f'<article class="card on" id="{sid}">', 1)
        one = re.sub(r'(<article class="card section[^"]*") id="' + sid + '"',
                     r'\1 on" id="' + sid + '"', one) if f'id="{sid}"' not in one.split('card on')[0] else one
        page = (f'<style>@page {{ size: {w}px {h}px; margin: 0 }}'
                ' html, body { height: auto !important; overflow: visible !important }'
                ' main.prose { overflow: visible !important }</style>')
        one = one.replace('</head>', page + '</head>', 1)
        pdf = os.path.join(OUT, f'{w}x{h}-{sid}.pdf')
        HTML(string=one, base_url=SRC, media_type='screen').write_pdf(pdf)
        png = pdf[:-4]
        subprocess.run(['pdftoppm', '-png', '-r', '96', '-singlefile', pdf, png], check=True)
        os.remove(pdf)
        print(png + '.png')


if __name__ == '__main__':
    main()

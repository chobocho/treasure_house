# -*- coding: utf-8 -*-
"""gen_system.py — 덱 전체를 관통하는 '전체 그림' SVG 를 부(部)마다 하나씩 만든다.

   왜 손으로 그리지 않나: 이 그림은 13번 나온다. 부마다 새로 등장한 상자가
   켜지고 나머지는 흐리게 남는다. 13장을 손으로 그리면 어느 한 장에서 상자가
   한 칸 밀리거나 색이 달라지고, 그 순간 "같은 그림이 자라는 중" 이라는 약속이
   깨진다. 자리와 색은 여기 한 곳에만 적고, 켜는 것만 부마다 고른다.

   폭 계약: viewBox 는 340 칸이다. 갤럭시 폴드 접힘(374px)에서 카드 안쪽 폭이
   334px 라 거의 1:1 로 그려진다. 그래서 글자 크기 12 는 화면에서도 약 11.8px —
   §5.9 의 "374px 에서 12px 이상" 을 지키는 가장 단순한 방법이다. 넓은 화면에서는
   width:100% 로 통째로 커진다.

       python3 deck/gen_system.py        # deck/figs/system_p0..p12.svg 를 새로 쓴다
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, 'figs')

W, H = 340, 274

# 상자: 키 → (x, y, 폭, 높이, 색 클래스, 제목, 한 줄 설명)
# 색은 head.html 의 --br/--app/--kc/--ad 와 같다. 색이 곧 "누구 이야기인지" 다.
BOXES = {
    'br':  (90,    6, 160, 44, 'br',  '브라우저',        '민지의 노트북'),
    'ing': (10,   72, 320, 44, 'app', 'Ingress',         '단지 경비실'),
    'app': (10,  140, 150, 54, 'app', '학식 예약 앱',    'Pod · 우리 서비스'),
    'kc':  (180, 140, 150, 54, 'kc',  'Keycloak',        'Pod · 통역사'),
    # 창고는 Keycloak 의 것이다 — 앱이 아니라 Keycloak 과 같은 보라로 묶는다
    'pg':  (10,  218, 150, 44, 'kc',  'PostgreSQL',      'Keycloak 의 창고'),
    'ad':  (180, 218, 150, 44, 'ad',  'AD 도메인 컨트롤러', '학교 학적부'),
}

# 화살표: (경로 d, 라벨, 라벨 x, 라벨 y, 앵커, 이 화살표가 살아나려면 켜져야 하는 상자들)
ARROWS = [
    ('M170,50 L170,70',                       'HTTPS',    176,  66, 'start', ('br', 'ing')),
    ('M85,116 L85,138',                       '앱 열기',   91,  133, 'start', ('ing', 'app')),
    ('M255,116 L255,138',                     '로그인',   261,  133, 'start', ('ing', 'kc')),
    ('M200,194 L200,207 L85,207 L85,216',     'SQL',      96,  204, 'start', ('kc', 'pg')),
    ('M255,194 L255,216',                     'LDAPS',   261,  212, 'start', ('kc', 'ad')),
]

# 부마다 켜지는 상자. 앞부에서 켠 것은 계속 켜진 채로 남는다 —
# 그림이 자라는 것이지 바뀌는 것이 아니라는 뜻이다.
LIT = {
    0:  ('br', 'ing', 'app', 'kc', 'pg', 'ad'),      # 표지 — 전체를 한 번 보여 준다
    1:  ('br',),                                      # 1부 웹
    2:  ('br', 'ing', 'app'),                         # 2부 쿠버네티스
    3:  ('br', 'ing', 'app', 'ad'),                   # 3부 AD
    4:  ('br', 'ing', 'app', 'ad', 'kc'),             # 4부 인증 위임(미니 IdP 자리)
    5:  ('br', 'ing', 'app', 'ad', 'kc'),             # 5부 Keycloak 이란
    6:  ('br', 'ing', 'app', 'ad', 'kc', 'pg'),       # 6부 k8s 에 올리기
    7:  ('br', 'ing', 'app', 'ad', 'kc', 'pg'),
    8:  ('br', 'ing', 'app', 'ad', 'kc', 'pg'),
    9:  ('br', 'ing', 'app', 'ad', 'kc', 'pg'),
    10: ('br', 'ing', 'app', 'ad', 'kc', 'pg'),
    11: ('br', 'ing', 'app', 'ad', 'kc', 'pg'),
    12: ('br', 'ing', 'app', 'ad', 'kc', 'pg'),
}


def svg_for(part):
    lit = set(LIT[part])
    out = ['<svg class="diag" viewBox="0 0 %d %d" role="img" '
           'aria-label="전체 그림 — %d부까지">' % (W, H, part),
           '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
           'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
           '<path d="M0,0 L10,5 L0,10 z"/></marker></defs>']

    for d, label, lx, ly, anchor, need in ARROWS:
        on = all(k in lit for k in need)
        cls = 'arw' if on else 'arw off'
        style = '' if on else ' stroke-dasharray="4 3" opacity=".35"'
        out.append('<path class="%s" d="%s"%s/>' % (cls, d, style))
        out.append('<text class="lbl" x="%d" y="%d" text-anchor="%s"%s>%s</text>'
                   % (lx, ly, anchor, '' if on else ' opacity=".45"', label))

    for key, (x, y, w, h, color, title, sub) in BOXES.items():
        on = key in lit
        cls = 'box %s' % color if on else 'box off'
        out.append('<rect class="%s" x="%d" y="%d" width="%d" height="%d" rx="8"/>'
                   % (cls, x, y, w, h))
        dim = '' if on else ' opacity=".45"'
        out.append('<text x="%d" y="%d" text-anchor="middle" font-size="13.5" '
                   'font-weight="700"%s>%s</text>'
                   % (x + w // 2, y + (20 if sub else h // 2 + 5), dim, title))
        if sub:
            out.append('<text class="lbl" x="%d" y="%d" text-anchor="middle" '
                       'font-size="12"%s>%s</text>'
                       % (x + w // 2, y + 37, dim, sub))
    out.append('</svg>')
    return '\n'.join(out) + '\n'


def main():
    os.makedirs(FIGS, exist_ok=True)
    for part in sorted(LIT):
        p = os.path.join(FIGS, 'system_p%d.svg' % part)
        io.open(p, 'w', encoding='utf-8', newline='\n').write(svg_for(part))
    print('전체 그림 %d장 → deck/figs/system_p*.svg' % len(LIT))


if __name__ == '__main__':
    main()

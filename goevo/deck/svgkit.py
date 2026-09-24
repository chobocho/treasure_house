# -*- coding: utf-8 -*-
"""svgkit — 덱에 인라인으로 실을 SVG 를 만드는 최소한의 도구.

   규칙 셋.

     1. **viewBox 폭은 340 이다.** 갤럭시 폴드 접힘이 374 px 이라,
        그보다 넓게 그리면 글자가 못 읽을 크기로 줄어든다. 조립기가
        360 을 넘는 viewBox 를 오류로 잡는다.
     2. **색은 CSS 변수로 쓴다.** var(--accent) 처럼 적으면 덱의 배색이
        바뀔 때 그림도 따라온다. 그림마다 색을 박아 두면 안 따라온다.
     3. **글자는 이미지가 아니라 글자다.** 축 이름도 범례도 <text> 로
        적는다. 그래야 확대해도 안 깨지고, 읽어 주는 기계도 읽는다.

   시간·공간 모두 O(그린 요소 수).
"""
import math

W = 340


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


class Fig(object):
    """SVG 한 장. 조각을 모았다가 마지막에 한 줄로 낸다."""

    def __init__(self, h=220, w=W, title=''):
        self.w = w
        self.h = h
        self.title = title
        self.parts = []

    def raw(self, s):
        self.parts.append(s)

    def line(self, x1, y1, x2, y2, cls='ax', extra=''):
        self.raw('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"'
                 ' class="%s"%s/>' % (x1, y1, x2, y2, cls, extra))

    def rect(self, x, y, w, h, cls='box', extra=''):
        self.raw('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f"'
                 ' class="%s"%s/>' % (x, y, w, h, cls, extra))

    def circle(self, x, y, r, cls='dot', extra=''):
        self.raw('<circle cx="%.2f" cy="%.2f" r="%.2f" class="%s"%s/>'
                 % (x, y, r, cls, extra))

    def text(self, x, y, s, cls='lbl', anchor='middle', extra=''):
        self.raw('<text x="%.2f" y="%.2f" class="%s"'
                 ' text-anchor="%s"%s>%s</text>'
                 % (x, y, cls, anchor, extra, esc(s)))

    def path(self, pts, cls='cv', extra=''):
        if not pts:
            return
        d = 'M %.2f %.2f' % pts[0]
        for p in pts[1:]:
            d += ' L %.2f %.2f' % p
        self.raw('<path d="%s" class="%s"%s/>' % (d, cls, extra))

    def poly(self, pts, cls='box', extra=''):
        d = ' '.join('%.2f,%.2f' % p for p in pts)
        self.raw('<polygon points="%s" class="%s"%s/>' % (d, cls,
                                                          extra))

    def render(self):
        head = ('<svg class="diag" viewBox="0 0 %d %d"'
                ' xmlns="http://www.w3.org/2000/svg"'
                ' role="img" aria-label="%s">'
                % (self.w, self.h, esc(self.title)))
        return (head + '\n' + STYLE + '\n'
                + '\n'.join(self.parts) + '\n</svg>')


# 글자 규칙은 svg.diag text.X 꼴로 적는다. 덱의 CSS 에 svg.diag text
# {font-size:12px} 가 있어서, .tick 처럼 약하게 적으면 덱 안에서만
# 모든 글자가 12px 로 커진다(PNG 로 따로 렌더하면 멀쩡해 보인다).
# 화살표는 .arw 가 아니라 .edge + .ah(촉) — 덱의 .arw 는 #ah 표지를
# 달아 촉이 겹친다.
# 그림 안에 최소한의 스타일을 같이 넣는다. var(--x, 기본값) 꼴이라
# 덱 안에서는 덱의 배색을 따르고, 파일 하나만 떼어 렌더해도(그림을
# 눈으로 검사할 때) 제 모습이 나온다. 이 두 줄이 없으면 SVG 기본값
# 대로 전부 검게 칠해져 아무것도 안 보인다 — 실제로 그랬다.
STYLE = """<style>
.diag text{font-family:-apple-system,"Noto Sans KR",sans-serif}
.frame{fill:none;stroke:var(--border,#c9d2da);stroke-width:1}
.ax{stroke:var(--muted,#5b6b7a);stroke-width:1;fill:none}
.grid{stroke:var(--border,#e1e7ec);stroke-width:.6;
 stroke-dasharray:2 3;fill:none}
svg.diag text.tick{font-size:8px;fill:var(--muted,#5b6b7a)}
svg.diag text.axname{font-size:9px;fill:var(--accent2,#1d3557);font-weight:700}
svg.diag text.key{font-size:9px;fill:var(--accent2,#1d3557);font-weight:700}
svg.diag text.cap{font-size:8.5px;fill:var(--muted,#5b6b7a)}
.cv{fill:none;stroke:var(--accent,#00add8);stroke-width:1.6}
.cv1{fill:none;stroke:var(--g1,#1d6fb8);stroke-width:1.6}
.cv2{fill:none;stroke:var(--g2,#2f7a52);stroke-width:1.6}
.cv3{fill:none;stroke:var(--g3,#b5561b);stroke-width:1.6}
.cv4{fill:none;stroke:var(--g4,#7a4a8c);stroke-width:1.6}
.cv5{fill:none;stroke:var(--g5,#a86b00);stroke-width:1.6}
.cv6{fill:none;stroke:var(--g6,#5c6b73);stroke-width:1.6}
.cvd{fill:none;stroke:var(--muted,#5b6b7a);stroke-width:1.2;
 stroke-dasharray:4 3}
.dot{fill:var(--accent,#00add8);stroke:none}
.dot2{fill:var(--special,#007d9c);stroke:none}
.dot5{fill:var(--g5,#a86b00);stroke:none}
.dotn{fill:var(--muted,#5b6b7a);opacity:.35;stroke:none}
.cell{fill:var(--panel,#fff);stroke:var(--border,#c9d2da);
 stroke-width:1}
.cell.a{fill:rgba(0,173,216,.16)}
.cell.b{fill:rgba(184,50,42,.14)}
.cell.c{fill:rgba(46,158,91,.14)}
.cell.d{fill:rgba(217,119,6,.16)}
.cell.e{fill:rgba(0,125,156,.14)}
.cell.f{fill:rgba(91,107,122,.12)}
.box{fill:var(--panel,#fafbfc);stroke:var(--border,#c9d2da);
 stroke-width:1.2}
.box.g1{stroke:var(--g1,#1d6fb8);fill:rgba(29,111,184,.12)}
.box.g2{stroke:var(--g2,#2f7a52);fill:rgba(47,122,82,.12)}
.box.g3{stroke:var(--g3,#b5561b);fill:rgba(181,86,27,.12)}
.box.g4{stroke:var(--g4,#7a4a8c);fill:rgba(122,74,140,.12)}
.box.g5{stroke:var(--g5,#a86b00);fill:rgba(168,107,0,.12)}
.box.g6{stroke:var(--g6,#5c6b73);fill:rgba(92,107,115,.12)}
.box.off{fill:none;stroke-dasharray:3 2}
.arw{stroke:var(--net,#7d8a96);stroke-width:1.4;fill:none}
.arw.hot{stroke:var(--special,#007d9c);stroke-width:2.2}
svg.diag text.lbl{font-size:11px;fill:var(--muted,#5b6b7a)}
.diag text{fill:var(--text,#1c2530)}
.tie{stroke:var(--net,#7d8a96);stroke-width:1;fill:none}
.tie.hot{stroke:var(--special,#007d9c);stroke-width:1.6}
.edge{stroke:var(--net,#7d8a96);stroke-width:1.3;fill:none}
.edge.hot{stroke:var(--special,#007d9c);stroke-width:1.8}
.edge.dim{stroke-dasharray:3 2;opacity:.6}
.ah{fill:var(--net,#7d8a96);stroke:none}
.ah.hot{fill:var(--special,#007d9c)}
.bar{fill:var(--g2,#2f7a52);opacity:.8;stroke:none}
.bar.a{fill:var(--accent,#00add8)}
svg.diag text.mono{font-family:"DeckMono","D2Coding",ui-monospace,
 monospace;font-size:8.5px}
svg.diag text.hot{fill:var(--special,#007d9c);font-weight:700;
 font-size:9.5px}
</style>"""


class Axes(object):
    """선 그래프용 축. 로그 눈금을 지원한다(BER 곡선 때문에).

    화면 좌표로 바꾸는 일만 한다 — 눈금 이름은 부르는 쪽이 정한다.
    """

    def __init__(self, fig, x0, y0, w, h, xlim, ylim,
                 ylog=False, xlog=False):
        self.f = fig
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.xlim, self.ylim = xlim, ylim
        self.ylog, self.xlog = ylog, xlog

    def _fx(self, v):
        a, b = self.xlim
        if self.xlog:
            v, a, b = math.log10(v), math.log10(a), math.log10(b)
        return self.x0 + (v - a) / (b - a) * self.w

    def _fy(self, v):
        a, b = self.ylim
        if self.ylog:
            v = max(v, 1e-300)
            v, a, b = math.log10(v), math.log10(a), math.log10(b)
        return self.y0 + self.h - (v - a) / (b - a) * self.h

    def frame(self):
        self.f.rect(self.x0, self.y0, self.w, self.h, 'frame')

    def xticks(self, vals, fmt='%g', label=''):
        for v in vals:
            x = self._fx(v)
            self.f.line(x, self.y0 + self.h, x, self.y0 + self.h + 3,
                        'ax')
            self.f.text(x, self.y0 + self.h + 12, fmt % v, 'tick')
        if label:
            self.f.text(self.x0 + self.w / 2,
                        self.y0 + self.h + 25, label, 'axname')

    def yticks(self, vals, fmt='%g', label=''):
        for v in vals:
            y = self._fy(v)
            self.f.line(self.x0 - 3, y, self.x0, y, 'ax')
            self.f.text(self.x0 - 5, y + 3, fmt % v, 'tick', 'end')
        if label:
            self.f.text(10, self.y0 + self.h / 2, label, 'axname',
                        'middle',
                        ' transform="rotate(-90 10 %.1f)"'
                        % (self.y0 + self.h / 2))

    def grid(self, xs=(), ys=()):
        for v in xs:
            x = self._fx(v)
            self.f.line(x, self.y0, x, self.y0 + self.h, 'grid')
        for v in ys:
            y = self._fy(v)
            self.f.line(self.x0, y, self.x0 + self.w, y, 'grid')

    def curve(self, pts, cls='cv'):
        self.f.path([(self._fx(x), self._fy(y)) for x, y in pts], cls)

    def dots(self, pts, r=1.6, cls='dot'):
        for x, y in pts:
            self.f.circle(self._fx(x), self._fy(y), r, cls)

    def at(self, x, y):
        return self._fx(x), self._fy(y)


def legend(fig, x, y, items, dy=11):
    """범례 — [(글, 클래스)] 를 세로로."""
    for i, (name, cls) in enumerate(items):
        yy = y + i * dy
        fig.line(x, yy - 3, x + 12, yy - 3, cls)
        fig.text(x + 16, yy, name, 'tick', 'start')

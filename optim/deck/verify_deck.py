# -*- coding: utf-8 -*-
"""역검증 — 완성된 덱을 다시 읽어 소스·출력과 대조한다.

   빌더가 채웠으니 맞을 수밖에 없다고 생각하기 쉽지만, 실제로 자주 벌어지는 일은
     · 조각 HTML 에 손으로 코드를 적어 넣고
     · 소스를 고친 뒤 덱을 다시 만들지 않고 커밋하고
     · out/manifest.json 이 낡은 채로 남는 것
   이다. 이 도구는 그 셋을 전부 잡는다. 덱은 산출물일 뿐 원본이 아니라는 규율을
   기계로 강제하는 장치다.

   사용법:  python3 optim/deck/verify_deck.py
"""
import html
import io
import json
import os
import re
import sys
from html.parser import HTMLParser

DECK = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(DECK)
ROOT = os.path.dirname(BASE)
TARGET = os.path.join(ROOT, '수학적_최적화_완전_가이드.html')

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
# 닫는 태그를 생략해도 되는 것들 — 이 덱에서는 쓰지 않지만 파서가 놀라지 않게 둔다
OPTIONAL = {'li', 'tr', 'td', 'th', 'option', 'p'}
BOX = '┌┐└┘├┤┬┴┼│'          # 폴드7 글꼴에서 폭이 어긋나는 괘선 문자


class Balance(HTMLParser):
    """태그 균형 검사. 코드 안 원시 '<' 가 태그로 파싱되는 사고를 잡는 것이 주목적."""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=False)
        self.stack = []
        self.bad = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for t, ln in self.stack[i + 1:]:
                    if t not in OPTIONAL:
                        self.bad.append('%d행: <%s> 가 닫히지 않았다' % (ln, t))
                del self.stack[i:]
                return
        self.bad.append('%d행: 짝 없는 </%s>' % (self.getpos()[0], tag))


def read(p):
    return io.open(p, encoding='utf-8').read()


def src_lines(path):
    lines = read(os.path.join(BASE, path)).split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def main():
    if not os.path.exists(TARGET):
        print('덱이 없다. build_deck.py 를 먼저 돌릴 것.')
        return 1
    doc = read(TARGET)
    # 본문만 남긴 사본 — <style>·<script> 안의 주석에 적힌 글자를 본문의 표기 위반으로
    # 잘못 신고하는 것을 막는다.
    body_only = re.sub(r'<script\b.*?</script>|<style\b.*?</style>', '', doc, flags=re.S)
    problems = []
    st = dict(pages=0, code=0, out=0, demo=0)

    # ── 1. 태그 균형 ────────────────────────────────────────────
    b = Balance()
    b.feed(doc)
    problems += ['[태그] ' + x for x in b.bad[:20]]
    for t, ln in b.stack:
        if t not in ('html', 'body', 'head') and t not in OPTIONAL:
            problems.append('[태그] %d행: <%s> 가 끝까지 안 닫혔다' % (ln, t))

    # ── 2. 슬라이드 id ──────────────────────────────────────────
    ids = re.findall(r'<article class="card[^"]*" id="([^"]+)"', body_only)
    st['pages'] = len(re.findall(r'<article class="card', body_only))
    if len(ids) != st['pages']:
        problems.append('[id] id 없는 슬라이드가 %d장 있다' % (st['pages'] - len(ids)))
    dup = {x for x in ids if ids.count(x) > 1}
    if dup:
        problems.append('[id] 중복된 id: %s' % ', '.join(sorted(dup)[:8]))

    # ── 3. 챕터 이동 목록이 실제 id 를 가리키는가 ────────────────
    idset = set(ids)
    nav = re.search(r'<select id="nav"[^>]*>(.*?)</select>', body_only, re.S)
    for v in re.findall(r'<option value="([^"]+)">', nav.group(1) if nav else ''):
        if v != 'top' and v not in idset:
            problems.append('[nav] 없는 슬라이드를 가리킨다: %s' % v)

    # ── 4. 코드 블록 = 실제 소스 ────────────────────────────────
    for m in re.finditer(r'<pre><code([^>]*)>(.*?)</code></pre>', body_only, re.S):
        attrs, inner = m.group(1), m.group(2)
        src = re.search(r'data-src="([^"]+)"', attrs)
        if not src:
            # data-src 없는 긴 코드 = 손으로 적었다는 뜻. 3줄 이상이면 걸러낸다.
            if inner.count('\n') >= 3 and 'data-lang="html"' not in attrs:
                problems.append('[코드] data-src 없는 긴 코드: %s' %
                                html.unescape(re.sub('<[^>]+>', '', inner))[:50].replace('\n', '⏎'))
            continue
        st['code'] += 1
        path = src.group(1)
        sym = re.search(r'data-sym="([^"]+)"', attrs)
        rng = re.search(r'data-lines="(\d+)-(\d+)"', attrs)
        lines = src_lines(path)
        shown = html.unescape(re.sub('<[^>]+>', '', inner))
        if rng:
            a, b2 = int(rng.group(1)), int(rng.group(2))
            want = '\n'.join(lines[a - 1:b2])
        else:
            want = None                      # 심볼 인용은 아래에서 부분열로 확인
        if want is not None and shown != want:
            problems.append('[코드] %s 가 소스와 다르다' % path)
        elif want is None:
            body = '\n'.join(lines)
            if shown not in body:
                problems.append('[코드] %s 의 인용이 소스에 없다 (%s)'
                                % (path, sym.group(1) if sym else '?'))

    # ── 5. 실행 출력 = manifest ─────────────────────────────────
    mpath = os.path.join(BASE, 'out', 'manifest.json')
    manifest = json.loads(read(mpath)) if os.path.exists(mpath) else {}
    for m in re.finditer(r'<div class="term[^"]*" data-out="([^"]+)">(.*?)</div>', body_only, re.S):
        name, inner = m.group(1), m.group(2)
        st['out'] += 1
        rec = manifest.get(name)
        if rec is None:
            problems.append('[출력] manifest 에 없다: %s' % name)
            continue
        shown = html.unescape(re.sub('<[^>]+>', '', inner))
        want = ('$ %s\n%s' % (rec['cmd'], rec['stdout'])).rstrip()
        if shown.rstrip() != want:
            problems.append('[출력] %s 가 실제 실행 결과와 다르다' % name)

    # ── 6. 괘선 문자 ────────────────────────────────────────────
    for ch in BOX:
        if ch in body_only:
            problems.append('[표기] 괘선 문자 %r 사용 — 폴드7에서 폭이 어긋난다' % ch)

    # ── 7. 데모 ─────────────────────────────────────────────────
    st['demo'] = len(set(re.findall(r"__demo\('([^']+)'", doc)))
    for d in set(re.findall(r'data-demo="([^"]+)"', doc)):
        if "__demo('%s'" % d not in doc:
            problems.append('[데모] 등록되지 않은 데모: %s' % d)

    print('검증: %s' % os.path.basename(TARGET))
    print('  슬라이드 %d장 · 소스 인용 %d블록 · 실행 출력 %d개 · 데모 %d개'
          % (st['pages'], st['code'], st['out'], st['demo']))
    if problems:
        print('\n문제 %d건:' % len(problems))
        for p in problems[:40]:
            print('  · %s' % p)
        return 1
    print('  문제 없음.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

# -*- coding: utf-8 -*-
"""덱 조립기 — 조각 HTML + 실제 파이썬 소스 + 실제 실행 출력을 하나로 붙인다.

   규율 하나: 덱 본문에 손으로 쓴 코드는 없다.
   모든 <pre><code> 는 data-src 로 진짜 파일의 진짜 줄을 가리키고, 여기서 그
   내용을 읽어 채운다. 모든 <div class="term"> 은 data-out 으로 run_all.py 가
   실제로 실행해 남긴 출력을 가리킨다. 그래서 소스를 고치면 덱이 따라오고,
   verify_deck.py 가 둘이 어긋나지 않았음을 매번 다시 확인한다.

   사용법:  python3 optim/deck/build_deck.py
"""
import html
import io
import json
import os
import re
import sys

DECK = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(DECK)                       # optim/
ROOT = os.path.dirname(BASE)                       # 저장소 루트
OUTDIR = os.path.join(BASE, 'out')
TARGET = os.path.join(ROOT, '수학적_최적화_완전_가이드.html')

LANG_OF = {'.py': 'py', '.sh': 'sh', '.json': 'json', '.txt': 'text'}

errors = []
covered = {}          # {파일: set(줄번호)} — 덱이 인용한 줄
stats = dict(code=0, out=0, pages=0, parts=0, chapters=0, demos=0, results=0)


def read(p):
    return io.open(p, encoding='utf-8').read()


def esc(s):
    return html.escape(s, quote=False)


def src_lines(path):
    lines = read(os.path.join(BASE, path)).split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def find_symbol(path, sym):
    """이름으로 함수/클래스/상수의 줄 범위를 찾는다.

       줄 번호를 손으로 적어 두면 소스를 고칠 때마다 덱이 조용히 엉뚱한 코드를
       보여 준다. 이름으로 가리키면 그 사고가 아예 생기지 않는다.
    """
    lines = src_lines(path)
    lo, hi = 0, len(lines)

    # "클래스.메서드" 는 그 클래스 범위 안에서만 찾는다.
    if '.' in sym:
        cls, sym = sym.split('.', 1)
        a, b = find_symbol(path, cls)
        lo, hi = a - 1, b

    pat = re.compile(r'^(?:def|class)\s+%s\b|^%s\s*(?:[:,]|=)' % (re.escape(sym), re.escape(sym)))
    start = None
    for i in range(lo, hi):
        if pat.match(lines[i].strip()):
            start = i
            break
    if start is None:
        errors.append('%s 에서 심볼 %s 을(를) 찾지 못함' % (path, sym))
        return 1, 1

    # 앞에 붙은 데코레이터와 주석 블록을 함께 가져온다 — 의도가 거기 적혀 있다.
    head = start
    while head > lo:
        prev = lines[head - 1].strip()
        if prev.startswith('@') or prev.startswith('#'):
            head -= 1
        else:
            break

    indent = len(lines[start]) - len(lines[start].lstrip())
    end = hi
    for i in range(start + 1, hi):
        ln = lines[i]
        if not ln.strip():
            continue
        cur = len(ln) - len(ln.lstrip())
        if cur <= indent:
            end = i
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return head + 1, end                            # 1-based, 양끝 포함


def mark(path, a, b):
    covered.setdefault(path, set()).update(range(a, b + 1))


def fill_code(m):
    """<pre><code data-src=...> 를 실제 소스로 채운다."""
    attrs = m.group(1)
    src = re.search(r'data-src="([^"]+)"', attrs)
    if not src:
        return m.group(0)
    path = src.group(1)
    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        errors.append('없는 소스 파일: %s' % path)
        return m.group(0)

    sym = re.search(r'data-sym="([^"]+)"', attrs)
    rng = re.search(r'data-lines="(\d+)-(\d+)"', attrs)
    lines = src_lines(path)
    if sym:
        a, b = find_symbol(path, sym.group(1))
    elif rng:
        a, b = int(rng.group(1)), int(rng.group(2))
    else:
        a, b = 1, len(lines)
    a = max(1, min(a, len(lines)))
    b = max(a, min(b, len(lines)))
    mark(path, a, b)
    stats['code'] += 1

    body = '\n'.join(lines[a - 1:b])
    lang = LANG_OF.get(os.path.splitext(path)[1], 'text')
    keep = ' '.join(x for x in (src.group(0), sym.group(0) if sym else '',
                                rng.group(0) if rng else '') if x)
    label = '%s <span class="ln">%d–%d행</span>' % (esc(path), a, b)
    return ('<p class="fname">%s</p>\n<pre><code data-lang="%s" %s>%s</code></pre>'
            % (label, lang, keep, esc(body)))


def fill_out(m, manifest):
    """<div class="term ..." data-out="이름"></div> 를 실제 실행 출력으로 채운다."""
    cls, name = m.group(1), m.group(2)
    rec = manifest.get(name)
    if rec is None:
        errors.append('실행 출력 없음: %s (run_all.py 를 먼저 돌릴 것)' % name)
        return m.group(0)
    stats['out'] += 1
    body = ('<span class="p">$</span> %s\n%s' % (esc(rec['cmd']), esc(rec['stdout']))).rstrip()
    return '<div class="term%s" data-out="%s">%s</div>' % (cls, esc(name), body)


KIND_OF = {'thm': '정리', 'prop': '명제', 'lem': '보조정리', 'cor': '따름정리',
           'defn': '정의'}


def collect_results(body):
    """본문에서 정리·명제·정의를 순서대로 긁어 온다.

       부록의 색인을 손으로 적지 않기 위해서다. 손으로 적으면 본문을 고칠 때마다
       어긋나고, 그 어긋남은 아무도 눈치채지 못한다. 이 저장소의 다른 색인(코드·출력)과
       같은 규율이다.
    """
    out = []
    part = chap = ''
    for m in re.finditer(r'<article class="card([^"]*)" id="([^"]+)">(.*?)</article>',
                         body, re.S):
        cls, sid, inner = m.group(1), m.group(2), m.group(3)
        num = re.search(r'<p class="chnum">([^<]+)</p>', inner)
        h2 = re.search(r'<h2>(.*?)</h2>', inner, re.S)
        if num and h2:
            title = re.sub(r'<[^>]+>', '', h2.group(1)).strip()
            if 'section' in cls:
                part = '%s %s' % (num.group(1), title)
            else:
                chap = '%s %s' % (num.group(1), title)
        for b in re.finditer(r'<div class="(thm|prop|lem|cor|defn)[^"]*">\s*'
                             r'<span class="h">([^<]+)</span>', inner):
            kind, head = KIND_OF[b.group(1)], b.group(2).strip()
            if head.startswith('증명'):
                continue
            out.append({'part': part, 'chap': chap, 'id': sid,
                        'kind': kind, 'head': head})
    return out


def render_result_index(body):
    """정리 색인 표를 만든다 — 부별로 묶고, 슬라이드로 가는 링크를 붙인다."""
    items = collect_results(body)
    by_part = []
    for it in items:
        if not by_part or by_part[-1][0] != it['part']:
            by_part.append((it['part'], []))
        by_part[-1][1].append(it)
    chunks = []
    n = 0
    for part, rows in by_part:
        n += len(rows)
        lines = ['<div class="tblwrap">', '<table class="kv">',
                 '<tr><th>번호·이름</th><th>종류</th><th>어느 장</th></tr>']
        for r in rows:
            lines.append('<tr><td><a href="#%s">%s</a></td><td>%s</td><td>%s</td></tr>'
                         % (r['id'], esc(r['head']), r['kind'], esc(r['chap'])))
        lines += ['</table>', '</div>']
        chunks.append((part, '\n'.join(lines)))
    stats['results'] = n
    return chunks


def render_code_index(body):
    """소스 인용 색인 — 어느 슬라이드가 어느 함수를 실었는지."""
    rows = []
    for m in re.finditer(r'<article class="card[^"]*" id="([^"]+)">(.*?)</article>',
                         body, re.S):
        sid, inner = m.group(1), m.group(2)
        h = re.search(r'<h3>(.*?)</h3>', inner, re.S)
        title = re.sub(r'<[^>]+>', '', h.group(1)).strip() if h else sid
        for c in re.finditer(r'data-src="([^"]+)"(?:[^>]*?data-sym="([^"]+)")?', inner):
            rows.append((c.group(1), c.group(2) or '(파일 전체)', sid, title))
    seen = set()
    uniq = []
    for r in rows:
        k = (r[0], r[1])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    uniq.sort()
    return uniq


def build_nav(body):
    """상단 챕터 이동 목록을 본문에서 그대로 뽑아 만든다 — 손으로 맞추지 않는다."""
    opts = ['<option value="top">챕터 이동…</option>']
    for m in re.finditer(r'<article class="card([^"]*)" id="([^"]+)">(.*?)</article>', body, re.S):
        cls, sid, inner = m.group(1), m.group(2), m.group(3)
        num = re.search(r'<p class="chnum">([^<]+)</p>', inner)
        h2 = re.search(r'<h2>(.*?)</h2>', inner, re.S)
        if not h2:
            continue
        title = re.sub(r'<[^>]+>', '', h2.group(1)).strip()
        if 'section' in cls and num:
            opts.append('<option value="%s">%s · %s</option>' % (sid, num.group(1), title))
            stats['parts'] += 1
        elif num:
            opts.append('<option value="%s">· %s</option>' % (sid, title))
            stats['chapters'] += 1
    return '\n'.join(opts)


def main():
    order = [ln.strip() for ln in read(os.path.join(DECK, 'order.txt')).split('\n')
             if ln.strip() and not ln.startswith('#')]
    mpath = os.path.join(OUTDIR, 'manifest.json')
    manifest = json.loads(read(mpath)) if os.path.exists(mpath) else {}

    chunks = []
    for name in order:
        p = os.path.join(DECK, 'sections', name)
        if not os.path.exists(p):
            errors.append('없는 조각: %s' % name)
            continue
        chunks.append(read(p).rstrip() + '\n')
    body = '\n'.join(chunks)

    body = re.sub(r'<pre><code([^>]*data-src="[^"]*"[^>]*)>\s*</code></pre>', fill_code, body)
    body = re.sub(r'<div class="term([^"]*)" data-out="([^"]+)">\s*</div>',
                  lambda m: fill_out(m, manifest), body)

    if '<!--RESULT-INDEX-->' in body:
        chunks = render_result_index(body)
        cards = []
        for k, (part, table) in enumerate(chunks):
            label = part or '앞부분'
            cards.append('<article class="card" id="idx-%d">\n<h3>정리 색인 — %s</h3>\n%s\n</article>'
                         % (k + 1, esc(label), table))
        body = body.replace('<!--RESULT-INDEX-->', '\n\n'.join(cards))
    if '<!--CODE-INDEX-->' in body:
        rows = render_code_index(body)
        per = 22
        cards = []
        for i in range(0, len(rows), per):
            part = rows[i:i + per]
            lines = ['<div class="tblwrap">', '<table class="kv">',
                     '<tr><th>파일</th><th>심볼</th><th>실린 슬라이드</th></tr>']
            for (src, sym, sid, title) in part:
                lines.append('<tr><td><code>%s</code></td><td><code>%s</code></td>'
                             '<td><a href="#%s">%s</a></td></tr>'
                             % (esc(src), esc(sym), sid, esc(title)))
            lines += ['</table>', '</div>']
            cards.append('<article class="card" id="codeidx-%d">\n'
                         '<h3>코드 색인 (%d/%d)</h3>\n%s\n</article>'
                         % (i // per + 1, i // per + 1,
                            (len(rows) + per - 1) // per, '\n'.join(lines)))
        body = body.replace('<!--CODE-INDEX-->', '\n\n'.join(cards))

    stats['pages'] = len(re.findall(r'<article class="card', body))
    nav = build_nav(body)

    head = read(os.path.join(DECK, 'base', 'head.html')).replace('<!--NAV-->', nav)
    tail = read(os.path.join(DECK, 'base', 'tail.html'))
    demos_path = os.path.join(DECK, 'demos.js')
    demos = read(demos_path) if os.path.exists(demos_path) else ''
    stats['demos'] = len(re.findall(r"__demo\('", demos))
    tail = tail.replace('<!--DEMOS-->', demos)

    doc = head + '\n' + body + '\n' + tail
    io.open(TARGET, 'w', encoding='utf-8', newline='\n').write(doc)

    print('덱: %s' % os.path.basename(TARGET))
    print('  슬라이드 %d장 · %d부 · %d장(챕터) · 코드 블록 %d · 실행 출력 %d · 데모 %d'
          % (stats['pages'], stats['parts'], stats['chapters'],
             stats['code'], stats['out'], stats['demos']))
    if stats['results']:
        print('  정리·정의 %d건 (색인 자동 생성)' % stats['results'])
    print('  크기 %.1f KB' % (len(doc.encode('utf-8')) / 1024.0))

    tot = cov = 0
    for path in sorted(covered):
        n = len(src_lines(path))
        tot += n
        cov += len(covered[path])
    if tot:
        print('  인용 커버리지: %d/%d줄 (%.0f%%)' % (cov, tot, 100.0 * cov / tot))

    if errors:
        print('\n문제 %d건:' % len(errors))
        for e in errors[:40]:
            print('  · %s' % e)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

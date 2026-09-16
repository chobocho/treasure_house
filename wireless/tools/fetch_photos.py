#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""위키미디어 공용에서 사진을 받아 deck/photos/ 에 넣는다.

    python3 tools/fetch_photos.py            # 원하는 목록대로 받는다
    python3 tools/fetch_photos.py --check    # 받은 것의 라이선스 검사

**자유 라이선스만 싣는다** (PLAN.md §0.9). PD·CC0·CC BY·CC BY-SA 가
아니면 받지 않고, 받은 것은 라이선스와 저작자를 manifest.tsv 에 적는다.
조립기는 그 표에 없는 사진을 덱에 못 넣고, 표에 있는 사진에는 출처 줄을
자동으로 붙인다. 그래서 "출처 없는 사진" 이 덱에 들어갈 길이 없다.

찾는 방법: 파일 이름을 기억해서 적으면 반드시 어딘가 틀리므로, 공용의
**검색 API 로 후보를 받아** 자유 라이선스인 첫 후보를 고른다. 무엇을
골랐는지는 manifest.tsv 에 남으니 나중에 사람이 바꿀 수 있다.

한 장 45 KB·폭 360 px 이하로 줄여서 받는다. 덱이 사진을 base64 로
품기 때문이다(§9 결정 2). 너무 크면 폭을 줄여 다시 받는다.
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
PHOTOS = os.path.join(BASE, 'deck', 'photos')
MANIFEST = os.path.join(PHOTOS, 'manifest.tsv')
WISH = os.path.join(PHOTOS, 'wishlist.tsv')
API = 'https://commons.wikimedia.org/w/api.php'
UA = ('treasure_house-deck-builder/1.0 (educational slide deck;'
      ' https://github.com/chobocho/treasure_house)')
FREE = ('public domain', 'cc0', 'cc by', 'cc-by', 'cc by-sa',
        'cc-by-sa', 'pd')
MAX_BYTES = 45 * 1024


def get(url, out=None):
    cmd = ['curl', '-sS', '-m', '120', '-A', UA]
    if out:
        cmd += ['-o', out]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=not out)
    if r.returncode != 0:
        raise IOError('내려받기 실패: %s' % url)
    return r.stdout if not out else None


def api(**params):
    params.setdefault('format', 'json')
    params.setdefault('action', 'query')
    url = API + '?' + urllib.parse.urlencode(params)
    return json.loads(get(url).decode('utf-8'))


def search(term, limit=6):
    """공용 파일 이름 후보. 기억으로 적지 않고 검색으로 찾는다."""
    d = api(list='search', srsearch=term, srnamespace=6,
            srlimit=limit)
    return [h['title'] for h in d.get('query', {}).get('search', [])]


def info(title, width=360):
    d = api(prop='imageinfo', iiprop='url|extmetadata|size',
            iiurlwidth=width, titles=title)
    pages = d.get('query', {}).get('pages', {})
    for _pid, pg in pages.items():
        ii = pg.get('imageinfo')
        if not ii:
            continue
        i = ii[0]
        em = i.get('extmetadata', {})

        def val(k):
            v = em.get(k, {}).get('value', '')
            return strip_tags(v)

        return {
            'title': pg['title'],
            'thumb': i.get('thumburl') or i.get('url'),
            'license': val('LicenseShortName') or val('UsageTerms'),
            'artist': val('Artist') or val('Credit') or '작자 미상',
            'width': i.get('thumbwidth') or i.get('width'),
        }
    return None


def strip_tags(s):
    out = []
    depth = 0
    for ch in s:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    t = ''.join(out)
    for a, c in (('&amp;', '&'), ('&nbsp;', ' '), ('&quot;', '"'),
                 ('&#039;', "'")):
        t = t.replace(a, c)
    return ' '.join(t.split())[:80]


def is_free(lic):
    low = (lic or '').lower()
    return any(low.startswith(f) for f in FREE)


def read_wishlist():
    """원하는 사진 목록. 한 줄에 '검색어 | 저장 이름 | 슬라이드 id'."""
    out = []
    for line in io.open(WISH, encoding='utf-8').read().split('\n'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        cols = [c.strip() for c in line.split('\t')]
        if len(cols) < 3:
            continue
        out.append(tuple(cols[:3]))
    return out


# 사진이 아닌 것들. 검색은 파일 이름공간 전체를 뒤지므로 PDF·SVG·
# 동영상이 섞여 나온다. 실제로 massive MIMO 를 찾다가 해상 통신 논문
# PDF 의 첫 쪽이 골라졌다 — 라이선스는 자유롭지만 사진이 아니다.
NOT_PHOTO = ('.pdf', '.svg', '.ogv', '.webm', '.ogg', '.djvu',
             '.tif', '.tiff', '.gif')


def fetch_one(term, local, slide):
    """후보를 훑어 자유 라이선스인 첫 **사진** 을 받는다. (행, 사연)."""
    for title in search(term):
        if title.lower().endswith(NOT_PHOTO):
            continue
        meta = info(title)
        if not meta:
            continue
        if not is_free(meta['license']):
            continue
        for width in (360, 280, 220, 180):
            meta = info(title, width)
            path = os.path.join(PHOTOS, local)
            get(meta['thumb'], path)
            size = os.path.getsize(path)
            if size <= MAX_BYTES:
                return ([meta['title'], local, meta['license'],
                         meta['artist'], slide,
                         str(meta['width'])],
                        '%s (%.0f KB)' % (meta['title'],
                                          size / 1024.0))
            os.remove(path)
        return None, '%s — 45 KB 아래로 못 줄였다' % title
    return None, '자유 라이선스인 후보를 못 찾았다'


HEAD = ('commons-title\tlocal-file\tlicense\tauthor\tslide-id'
        '\twidth\n')
NOTE = ('# tools/fetch_photos.py 가 만든다. 손으로 고치지 말 것.\n'
        '# 자유 라이선스(PD·CC0·CC BY·CC BY-SA)만 들어온다.\n'
        '# 조립기가 이 표에서 출처 줄을 만들어 사진마다 붙인다.\n')


def main(argv):
    if not os.path.isdir(PHOTOS):
        os.makedirs(PHOTOS)
    if '--check' in argv:
        bad = []
        for line in io.open(MANIFEST, encoding='utf-8').read(
        ).split('\n')[1:]:
            if not line.strip() or line.startswith('#'):
                continue
            cols = line.split('\t')
            if len(cols) < 3 or not is_free(cols[2]):
                bad.append(line[:60])
            elif not os.path.exists(os.path.join(PHOTOS, cols[1])):
                bad.append('%s — 파일이 없다' % cols[1])
        for line in bad:
            print('  ✗ ' + line)
        print('사진 라이선스 검사 — 어긋남 %d건' % len(bad))
        return 1 if bad else 0

    rows, misses = [], []
    for term, local, slide in read_wishlist():
        row, why = fetch_one(term, local, slide)
        if row:
            rows.append(row)
            print('  ✓ %-22s %s' % (local, why))
        else:
            misses.append((term, why))
            print('  – %-22s %s' % (local, why))
        time.sleep(0.4)          # 공용 API 에 대한 예의
    io.open(MANIFEST, 'w', encoding='utf-8', newline='\n').write(
        HEAD + NOTE + ''.join('\t'.join(r) + '\n' for r in rows))
    print('사진 %d장 · 못 구한 것 %d장' % (len(rows), len(misses)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

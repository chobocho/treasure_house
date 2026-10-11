#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_docs — data/sources.tsv 의 출처를 받아 docs/<key>.txt 로 둔다.

   docs/ 는 커밋하지 않는 캐시다. 덱의 역사 주장·버전 표기는 전부 여기 받아
   둔 글에서 근거를 찾는다(make_data.py). HTML 은 글자만 남기고, 마크다운·
   텍스트는 그대로 둔다.

     python3 tools/fetch_docs.py            아직 없는 것만 받는다
     python3 tools/fetch_docs.py --force    전부 다시 받는다
     python3 tools/fetch_docs.py --only releases
"""
import argparse
import datetime
import hashlib
import html
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK = r'p|div|br|li|ul|ol|h[1-6]|tr|table|section|article|header|footer|pre|blockquote|dt|dd|title'


def html_text(src):
    """HTML → 글자. 스크립트·스타일을 버리고, 블록 태그 자리에서 줄을 바꾼다. O(n)."""
    src = re.sub(r'(?is)<(script|style|noscript|svg)\b.*?</\1\s*>', ' ', src)
    src = re.sub(r'(?is)<!--.*?-->', ' ', src)
    src = re.sub(r'(?i)</?(?:%s)\b[^>]*>' % BLOCK, '\n', src)
    src = re.sub(r'<[^>]+>', '', src)
    src = html.unescape(src).replace('\xa0', ' ')
    lines = [re.sub(r'[ \t\r\f\v]+', ' ', ln).strip() for ln in src.split('\n')]
    return '\n'.join(ln for ln in lines if ln)


def read_sources(path):
    rows = []
    with io.open(path, encoding='utf-8') as f:
        lines = [ln for ln in f.read().split('\n') if ln and not ln.startswith('#')]
    head = lines[0].split('\t')
    for ln in lines[1:]:
        f = ln.split('\t')
        rows.append(dict(zip(head, f + [''] * (len(head) - len(f)))))
    return rows


def fetch(url):
    # 파이썬 urllib 보다 curl 이 이 기계(proot)의 인증서 저장소와 잘 맞는다.
    p = subprocess.run(['curl', '-sSL', '--fail', '-m', '90', '-A', 'Mozilla/5.0 (deck-docs)', url],
                       capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode('utf-8', 'replace').strip())
    return p.stdout


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--only')
    args = ap.parse_args(argv)
    docs = os.path.join(ROOT, 'docs')
    os.makedirs(docs, exist_ok=True)
    log, bad = [], 0
    for s in read_sources(os.path.join(ROOT, 'data', 'sources.tsv')):
        key, url = s['key'], s['url']
        if args.only and key != args.only:
            continue
        out = os.path.join(docs, key + '.txt')
        if os.path.isfile(out) and not args.force:
            continue
        try:
            raw = fetch(url)
        except RuntimeError as e:
            print('  ✗ %s — %s' % (key, e))
            bad += 1
            continue
        text = raw.decode('utf-8', 'replace')
        if re.search(r'(?i)<html|<!doctype html', text[:2000]):
            text = html_text(text)
        with io.open(out, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        log.append('%s\t%s\t%d\t%s' % (key, datetime.date.today().isoformat(), len(raw),
                                       hashlib.sha256(raw).hexdigest()[:16]))
        print('  ✓ %s (%d바이트)' % (key, len(raw)))
    if log:
        with io.open(os.path.join(docs, 'FETCHED.txt'), 'a', encoding='utf-8') as f:
            f.write('\n'.join(log) + '\n')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

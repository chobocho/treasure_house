# -*- coding: utf-8 -*-
"""gh_api.py — GitHub REST 를 아껴 쓰는 도우미.

    python3 tools/gh_api.py releases termux/termux-app   # TSV 행
    python3 tools/gh_api.py get repos/termux/termux-app  # JSON

인증 없는 API 는 시간당 60번이다(2026-09-18 rate_limit 응답). 그래서
응답은 전부 sources/gh/ 에 파일로 남기고, 같은 것을 두 번 묻지
않는다. 첫 커밋·태그 날짜처럼 git 으로 알 수 있는 것은 애초에 여기서
묻지 않는다(tools/fetch_src.sh 의 full 기록).

릴리스 날짜는 published_at 의 날짜 부분(UTC)이다. 태그를 단 날과
릴리스를 낸 날이 다를 수 있어서, 덱은 이 값을 "릴리스 날짜" 로만 쓴다.

시간 O(쪽 수). 공간 O(응답 크기).
"""
import io
import json
import os
import re
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(BASE, 'sources', 'gh')
API = 'https://api.github.com/'
UA = 'treasure-house-termux-deck'


def cache_name(path):
    """API 경로 → 캐시 파일 이름. 영숫자 밖은 전부 _ 하나로."""
    return re.sub(r'[^A-Za-z0-9]+', '_', path).strip('_') + '.json'


def get(path, cache_dir=CACHE, offline=False):
    """캐시에 있으면 그것, 없으면 받아서 캐시에 두고 돌려준다."""
    p = os.path.join(cache_dir, cache_name(path))
    if os.path.exists(p):
        return json.loads(io.open(p, encoding='utf-8').read())
    if offline:
        raise LookupError('캐시에 없다: %s' % path)
    req = urllib.request.Request(API + path, headers={
        'User-Agent': UA, 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode('utf-8')
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(body)
    return json.loads(body)


def releases(repo, cache_dir=CACHE, offline=False):
    """[{tag, date, name, url, prerelease}] — 오래된 것부터."""
    rows, page = [], 1
    while True:
        got = get('repos/%s/releases?per_page=100&page=%d'
                  % (repo, page), cache_dir, offline)
        for r in got:
            if r.get('draft'):
                continue
            rows.append({'tag': r['tag_name'],
                         'date': (r.get('published_at') or '')[:10],
                         'name': r.get('name') or '',
                         'url': r['html_url'],
                         'prerelease': bool(r.get('prerelease'))})
        if len(got) < 100:
            break
        page += 1
    rows.sort(key=lambda r: (r['date'], r['tag']))
    return rows


def tsv_row(short, rel):
    """data/releases.tsv 한 줄. notable-change 칸은 사람이 채운다
    — 비워 두면 비워 둔 대로 싣는다(지어내지 않는다)."""
    note = '(pre-release)' if rel['prerelease'] else ''
    return '\t'.join([short, rel['tag'], rel['date'], note, rel['url']])


def main(argv):
    if len(argv) == 2 and argv[0] == 'releases':
        short = argv[1].split('/')[-1]
        for r in releases(argv[1]):
            print(tsv_row(short, r))
        return 0
    if len(argv) == 2 and argv[0] == 'get':
        print(json.dumps(get(argv[1]), indent=1, ensure_ascii=False))
        return 0
    print('사용법: gh_api.py releases OWNER/REPO | get PATH')
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# 카드를 한 번 받고, 받은 ETag 으로 조건부 GET 을 한 번 더 한다.
# 표준 라이브러리만 — 서버가 캐시 머리글을 어떻게 다는지 보려는 것.
#   python 03/card_cache.py 카드주소...
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

WELL_KNOWN = "/.well-known/agent-card.json"


# region: get
def get(url, etag=None):
    req = Request(url)
    if etag:
        req.add_header("If-None-Match", etag)
    try:
        with urlopen(req) as res:
            res.read()
            return res.status, res.headers
    except HTTPError as e:  # urllib 은 304 도 예외로 올린다
        return e.code, e.headers


# endregion


# region: main
for base in sys.argv[1:]:
    url = base.rstrip("/") + WELL_KNOWN
    status, h = get(url)
    etag = h.get("ETag")
    print(base)
    print(f"  GET → {status} · ETag {etag or '-'}")
    print(f"    Cache-Control {h.get('Cache-Control') or '-'}")
    if etag is None:
        print("  ETag 이 없다 — 조건부로 물을 수 없다")
        continue
    status, _ = get(url, etag)
    print(f"  GET If-None-Match → {status}")
# endregion
# @ norun

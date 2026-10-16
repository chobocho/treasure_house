# 카드 여러 장을 받아 첫 장(완성 에이전트)과 견준다 — 뜻과 바이트를.
#   python 06/card_same.py 주소1 주소2 …
import json
import sys
import urllib.request

PATH = ".well-known/agent-card.json"


def fetch(base):
    with urllib.request.urlopen(base + PATH) as r:
        return r.read()


# region: compare
first = fetch(sys.argv[1])
print(f"{sys.argv[1]}  기준 — 키 {len(json.loads(first))}개")
for base in sys.argv[2:]:
    raw = fetch(base)
    same = json.loads(raw) == json.loads(first)  # dict 비교는 차례 무시
    keys = list(json.loads(raw))
    print(f"{base}  뜻이 {'같다' if same else '다르다'}", end="")
    print(f", 바이트는 {'같다' if raw == first else '다르다'}")
    print(f"    첫 키 셋: {' '.join(keys[:3])}")
# endregion
# @ norun

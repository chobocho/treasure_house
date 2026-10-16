# 에이전트 카드 검증기 — 필수 필드(proto REQUIRED)와 흔한 실수.
# 표준 라이브러리만. 오류가 하나라도 있으면 종료 코드 1.
#   python 03/card_check.py 카드주소...
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

# region: rules
CARD = ["name", "description", "version", "supportedInterfaces",
        "capabilities", "defaultInputModes", "defaultOutputModes",
        "skills"]  # fmt: skip
IFACE = ["url", "protocolBinding", "protocolVersion"]
SKILL = ["id", "name", "description", "tags"]
PATCH = re.compile(r"^\d+\.\d+\.\d+")  # 1.0.1 처럼 패치 번호까지


def absent(obj, key):
    # ProtoJSON 은 빈 문자열·빈 목록을 아예 안 적는다 — 비면 없는 것.
    # capabilities 만은 빈 객체 {} 도 "있음"(켠 기능이 없을 뿐)
    if key == "capabilities":
        return key not in obj
    return not obj.get(key)


def required(card):
    out = [k for k in CARD if absent(card, k)]
    for name, keys in (
        ("supportedInterfaces", IFACE),
        ("skills", SKILL),
    ):
        for i, item in enumerate(card.get(name) or []):
            out += [f"{name}[{i}].{k}" for k in keys if absent(item, k)]
    return [("오류", f"{p}: 필수인데 없거나 비었다") for p in out]


# endregion


# region: iface
def reachable(url):
    try:
        urlopen(url, timeout=2).close()
    except HTTPError:
        return True  # 405·404 라도 무언가 답했다
    except URLError:
        return False
    return True


def interfaces(card, card_url):
    found = []
    for i, f in enumerate(card.get("supportedInterfaces") or []):
        at, url = f"supportedInterfaces[{i}]", f.get("url", "")
        if PATCH.match(f.get("protocolVersion", "")):
            v = f["protocolVersion"]
            found.append(("경고", f"{at}.protocolVersion: {v} (§3.6)"))
        if url and not reachable(url):
            found.append(("오류", f"{at}.url: 닿지 않는다 {url}"))
        home = urlsplit(card_url).netloc
        if url and urlsplit(url).netloc != home:
            found.append(
                ("경고", f"{at}.url: 카드를 받은 곳({home})과 다르다")
            )
    return found


# endregion


# region: main
def card_url(addr):
    # .json 으로 끝나면 그 파일, 아니면 well-known 경로
    if addr.endswith(".json"):
        return addr
    return addr.rstrip("/") + "/.well-known/agent-card.json"


bad = False
for addr in sys.argv[1:]:
    url = card_url(addr)
    with urlopen(url) as res:
        card = json.load(res)
    found = required(card) + interfaces(card, url)
    print(addr)
    if not found:
        print("  문제 없음")
    for level, text in found:
        print(f"  {level} {text}")
        bad = bad or level == "오류"
sys.exit(1 if bad else 0)
# endregion
# @ norun

# 에이전트 카드 여러 장을 받아 한 장에 한 줄씩 요약한다
# — 표준 라이브러리만.
# 기획 에이전트가 동료를 고를 때 들여다보는 것이 바로 이 항목들이다.
import json
import sys
from urllib.request import urlopen

WELL_KNOWN = "/.well-known/agent-card.json"


# region: summary
def summary(card):
    skills = ",".join(s["id"] for s in card["skills"])
    # capabilities 에서 켜진(true) 것만 — 빠진 것은 false 와 같다
    caps = card.get("capabilities", {})
    on = ",".join(k for k, v in sorted(caps.items()) if v is True)
    schemes = ",".join(sorted(card.get("securitySchemes", {})))
    signed = len(card.get("signatures", []))
    return (
        f"{card['name']}\n"
        f"  스킬 {skills} · 기능 {on or '-'}"
        f" · 보안 {schemes or '-'} · 서명 {signed}"
    )


# endregion

for base in sys.argv[1:]:
    with urlopen(base.rstrip("/") + WELL_KNOWN) as res:
        print(summary(json.load(res)))
# @ norun

# 스킬의 태그로 일을 맡길 에이전트를 고른다. 기획 에이전트가
# 15부에서 동료를 찾는 방법의 핵심만 떼어 낸 것이다.
#   python 03/pick.py [--out 미디어타입] 태그 카드주소...
import argparse
import asyncio

import httpx
from a2a.client import A2ACardResolver


# region: pick
def out_modes(card, skill):
    # 스킬에 적힌 출력 모드가 있으면 그것, 없으면 카드의 기본값
    return list(skill.output_modes) or list(card.default_output_modes)


def matches(card, tag, mode):
    for s in card.skills:
        if tag not in s.tags:
            continue
        if mode is None or mode in out_modes(card, s):
            yield s


# endregion


# region: main
async def main(a):
    print(f"태그 {a.tag} · 출력 {a.out or '아무거나'}")
    found = 0
    async with httpx.AsyncClient() as http:
        for url in a.urls:
            card = await A2ACardResolver(http, url).get_agent_card()
            for s in matches(card, a.tag, a.out):
                found += 1
                tags = ",".join(s.tags)
                modes = ",".join(out_modes(card, s))
                print(f"  {card.name} · {s.id} [{tags}] → {modes}")
    print(f"  고른 곳 {found}")


# endregion

ap = argparse.ArgumentParser()
ap.add_argument("--out", help="이 출력 모드를 내는 스킬만")
ap.add_argument("tag")
ap.add_argument("urls", nargs="+")
asyncio.run(main(ap.parse_args()))
# @ norun

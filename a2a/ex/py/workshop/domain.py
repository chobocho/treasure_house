"""워크숍 규칙 — 입력과 자료만으로 답이 정해지는 순수 함수들.

A2A 와는 무관한 '업무 로직'이다. 에이전트는 이 함수를 부르고 결과를
A2A 메시지·아티팩트로 감싸기만 한다. 결과 모양은 골든 파일이 정한다.
"""

import math
import re
from datetime import date, timedelta

from workshop.fixtures import workshop

BAD_SIZE = "인원과 박 수는 1 이상이어야 합니다"
BAD_VEG = "채식 인원은 0명 이상, 전체 인원 이하여야 합니다"


def _bad_size(headcount, nights):
    return headcount < 1 or nights < 1


def choose_lodging(req):
    """숙박 가능한 곳 중 총액이 가장 싼 곳. O(숙소 수 × 박 수)."""
    hc, nights = req["headcount"], req["nights"]
    if _bad_size(hc, nights):
        return {"ok": False, "reason": BAD_SIZE}
    first = date.fromisoformat(req["date"])
    stay = {
        (first + timedelta(days=i)).isoformat() for i in range(nights)
    }
    best = None
    for v in workshop()["venues"]:
        if v["capacity"] < hc or stay & set(v["closed"]):
            continue
        total = hc * v["pricePerPersonNight"] * nights
        # 같은 값이면 id 가 작은 쪽 — 언어마다 정렬이 달라도 답이 같게.
        if best is None or (total, v["id"]) < (best[0], best[1]["id"]):
            best = (total, v)
    if best is None:
        return {"ok": False, "reason": "가능한 숙소가 없습니다"}
    total, v = best
    return {
        "ok": True,
        "venueId": v["id"],
        "venueName": v["name"],
        "rooms": math.ceil(hc / v["roomSize"]),
        "nights": nights,
        "headcount": hc,
        "total": total,
    }


def meal_slots(nights):
    """n박이면 저녁·아침을 n번, 마지막 날 점심 한 번 — 2n+1 끼."""
    slots = []
    for i in range(1, nights + 1):
        slots += [f"day{i}-dinner", f"day{i + 1}-breakfast"]
    return slots + [f"day{nights + 1}-lunch"]


def _pick(kind, veg, cap):
    """상한 이하에서 가장 비싼 메뉴. 같은 값이면 id 가 작은 쪽."""
    fits = [
        m
        for m in workshop()["menus"]
        if m["type"] == kind
        and m["vegetarian"] == veg
        and m["price"] <= cap
    ]
    if not fits:
        return None
    return min(fits, key=lambda m: (-m["price"], m["id"]))


def plan_meals(req):
    """끼니마다 일반식·채식을 고른다. O(끼니 수 × 메뉴 수)."""
    hc, nights = req["headcount"], req["nights"]
    veg = req["vegetarians"]
    if _bad_size(hc, nights):
        return {"ok": False, "reason": BAD_SIZE}
    if not 0 <= veg <= hc:
        return {"ok": False, "reason": BAD_VEG}
    caps = {**workshop()["defaultCaps"], **req.get("caps", {})}
    slots, total = [], 0
    for slot in meal_slots(nights):
        kind = slot.split("-")[1]
        sides = {}
        for side, count, is_veg in (
            ("regular", hc - veg, False),
            ("vegetarian", veg, True),
        ):
            if count == 0:
                sides[side] = None  # 먹을 사람이 없으면 고르지 않는다
                continue
            m = _pick(kind, is_veg, caps[kind])
            if m is None:
                return {
                    "ok": False,
                    "reason": "예산 안에 맞는 메뉴가 없습니다",
                }
            sides[side] = {
                "id": m["id"],
                "name": m["name"],
                "price": m["price"],
                "count": count,
            }
            total += m["price"] * count
        slots.append({"slot": slot, **sides})
    return {"ok": True, "slots": slots, "total": total}


def choose_buses(req):
    """45인승 a대 + 25인승 b대로 좌석을 채우는 가장 싼 조합.

    a, b 를 모두 시도한다 — O((h/45) × (h/25)), 워크숍 규모에선 충분.
    같은 값이면 차가 적은 쪽, 그다음 45인승이 많은 쪽.
    """
    hc, nights = req["headcount"], req["nights"]
    if _bad_size(hc, nights):
        return {"ok": False, "reason": BAD_SIZE}
    bus = {b["id"]: b for b in workshop()["buses"]}
    big, small = bus["bus45"], bus["bus25"]
    best = None
    for a in range(math.ceil(hc / big["seats"]) + 1):
        left = max(0, hc - a * big["seats"])
        b = math.ceil(left / small["seats"])
        cost = a * big["pricePerDay"] + b * small["pricePerDay"]
        key = (cost, a + b, -a)
        if best is None or key < best[0]:
            best = (key, a, b)
    (cost, _, _), a, b = best
    vehicles = [
        {"id": vid, "count": n}
        for vid, n in (("bus45", a), ("bus25", b))
        if n > 0
    ]
    days = nights + 1
    return {
        "ok": True,
        "vehicles": vehicles,
        "days": days,
        "costPerDay": cost,
        "total": cost * days,
    }


def settle(req):
    """예산 초과를 먼저 보고, 그다음 결재 필요 여부를 본다."""
    total = sum(item["amount"] for item in req["items"])
    budget = req["budget"]
    if total > budget:
        return {
            "ok": False,
            "reason": "예산을 초과합니다",
            "over": total - budget,
        }
    limit = workshop()["approvalThreshold"]
    if total > limit and not req["approved"]:
        return {"ok": True, "status": "auth-required", "total": total}
    return {
        "ok": True,
        "status": "completed",
        "total": total,
        "budget": budget,
        "remaining": budget - total,
    }


# Go 의 RE2 에는 뒤보기(lookbehind)가 없다. 세 언어가 같은 정규식을
# 쓰려고, 채식 인원을 먼저 찾아 지운 다음 전체 인원을 찾는다.
VEG = re.compile(r"채식\s*(\d+)명")
DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
NIGHTS = re.compile(r"(\d+)박")
HEADCOUNT = re.compile(r"(\d+)명")
BUDGET = re.compile(r"예산\s*([\d,]+)원")
DEPART = re.compile(r"출발\s*(\S+)")


def parse_request(text):
    """자유 문장에서 날짜·박 수·인원·채식·예산·출발지를 뽑는다."""
    veg = VEG.search(text)
    rest = VEG.sub("", text, count=1)
    found = {
        "date": DATE.search(rest),
        "nights": NIGHTS.search(rest),
        "headcount": HEADCOUNT.search(rest),
    }
    missing = [k for k, m in found.items() if m is None]
    if missing:
        return {"ok": False, "missing": missing}
    budget = BUDGET.search(rest)
    depart = DEPART.search(rest)
    return {
        "ok": True,
        "date": found["date"].group(1),
        "nights": int(found["nights"].group(1)),
        "headcount": int(found["headcount"].group(1)),
        "vegetarians": int(veg.group(1)) if veg else 0,
        "budget": int(budget.group(1).replace(",", ""))
        if budget
        else None,
        "depart": depart.group(1) if depart else None,
    }

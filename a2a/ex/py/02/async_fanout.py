# 비동기 두 가지 — (1) 차례로 생기는 이벤트를 하나씩 받기,
# (2) 세 견적을 한꺼번에 기다리기. asyncio 만으로.
import asyncio

from workshop.domain import choose_buses, choose_lodging, plan_meals

LODGING = {"date": "2026-10-30", "nights": 1, "headcount": 30}
MEALS = {"nights": 1, "headcount": 30, "vegetarians": 2}
BUS = {"headcount": 30, "nights": 1}


# region: steps
async def steps():  # 비동기 제너레이터: 기다렸다가 하나씩 내놓는다
    for s in ("배차 요청 접수", "기사 배정", "차량 확정"):
        await asyncio.sleep(0.05)
        yield s


# endregion


# region: fanout
async def quote(name, delay, rule, req):
    await asyncio.sleep(delay)  # 다른 에이전트에 묻는 시간인 셈
    print("끝남:", name)
    return name, rule(req)["total"]


async def main():
    async for s in steps():  # 이벤트가 생기는 대로 받는다
        print("상태:", s)
    results = await asyncio.gather(  # 셋을 동시에 띄우고 모두 기다린다
        quote("숙소", 0.3, choose_lodging, LODGING),
        quote("식사", 0.1, plan_meals, MEALS),
        quote("교통", 0.2, choose_buses, BUS),
    )
    print("모은 순서:", " · ".join(f"{n} {t}" for n, t in results))
    print("합계:", sum(t for _, t in results))


asyncio.run(main())
# endregion

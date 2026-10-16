# SSE 클라이언트 — urllib 만으로. 줄을 읽다가 빈 줄을 만나면
# 모아 둔 data 를 이벤트 하나로 내보낸다.
import argparse
import json
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--url", required=True)
args = ap.parse_args()


# region: parse
def sse_events(lines):
    """줄들 → 이벤트의 data 문자열들. 빈 줄이 이벤트의 끝이다."""
    data = []
    for raw in lines:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line == "":  # 빈 줄: 모은 것을 이벤트로
            if data:
                yield "\n".join(data)
            data = []
        elif line.startswith(":"):  # 주석 — 버린다
            continue
        else:
            field, _, value = line.partition(":")
            if field == "data":
                data.append(value.removeprefix(" "))
    # 빈 줄 없이 끝난 조각은 이벤트가 아니다 — 버린다


# endregion


# region: main
body = json.dumps({"nights": 1, "headcount": 30, "vegetarians": 2})
r = urllib.request.Request(
    args.url,
    data=body.encode(),
    headers={
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    },
)
with urllib.request.urlopen(r) as resp:  # 줄이 오는 대로 읽는다
    n = 0
    for data in sse_events(resp):
        n += 1
        ev = json.loads(data)
        if "slot" in ev:
            meal = f"{ev['regular']} / 채식 {ev['vegetarian']}"
            print(f"이벤트 {n}: {ev['slot']} {meal}")
        else:
            print(f"이벤트 {n}: 합계 {ev['total']}원")
print(f"스트림 끝 — 이벤트 {n}개")
# endregion
# @ norun

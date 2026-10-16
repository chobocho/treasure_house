# null 과 빠진 필드 — 식사 요청의 caps(끼니별 상한)는 넣어도 빼도 된다.
import json

# region: null
cases = {
    "caps 빠짐": '{"headcount":30,"vegetarians":2}',
    "caps null": '{"headcount":30,"vegetarians":2,"caps":null}',
    "채식 0명": '{"headcount":30,"vegetarians":0}',
}
for name, text in cases.items():
    d = json.loads(text)
    # .get 은 둘 다 None 이다 — 구별하려면 in 으로 키를 본다
    print(f"[{name}] get={d.get('caps')} in={'caps' in d}", end=" ")
    print(f"vegetarians={d.get('vegetarians')}")

print("None 쓰기 :", json.dumps({"caps": None}))
# endregion

# 교통 견적 요청을 JSON 으로 쓰고 다시 읽는다 — 파이썬 json 모듈.
import json

# region: roundtrip
req = {"headcount": 30, "nights": 1, "depart": "강남역"}

# 기본값: ", " ": " 뒤에 빈칸, 한글은 \uXXXX 로 바꾼다
print("기본값  :", json.dumps(req))
# 다른 두 언어와 같은 글자로 맞춘다
text = json.dumps(req, ensure_ascii=False, separators=(",", ":"))
print("맞춘 값 :", text)

back = json.loads(text)  # 객체는 dict, 수는 int 로 돌아온다
print("되읽기  :", type(back).__name__, back["depart"])
print("인원    :", back["headcount"], type(back["headcount"]).__name__)
# endregion

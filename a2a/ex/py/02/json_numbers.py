# 수 — 정수와 실수, 그리고 2^53 너머. 파이썬 int 는 크기 제한이 없다.
import json

# region: numbers
print("쓰기 30     :", json.dumps(30))
print("쓰기 30.0   :", json.dumps(30.0))  # 실수는 .0 을 붙여 쓴다

v = json.loads("30.0")
print("읽기 30.0   :", repr(v), type(v).__name__)
print("int 로 바꿈 :", int(v))

big = "9007199254740993"  # 2^53 + 1
print("읽기 2^53+1 :", json.loads(big))
print("float 이면  :", int(float(big)))  # 실수로 거치면 1 이 사라진다
# endregion

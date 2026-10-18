# 고치기 전의 풀이가 "３０명" 을 30명으로 읽은 까닭 — 파이썬 re 의 \d
# 는 str 패턴에서 유니코드 숫자를 다 받고, int() 도 전각 숫자를 읽는다.
import re

TEXT = "2026-10-30 1박 ３０명"
# region: digits
before = re.compile(r"(\d+)명")  # 고치기 전 workshop/domain.py
after = re.compile(r"(\d+)명", re.ASCII)  # 고친 뒤
m = before.search(TEXT)
print("re.ASCII 없이:", repr(m.group(1)), "→ int:", int(m.group(1)))
print("re.ASCII 함께:", after.search(TEXT))
print("'３'.isdigit():", "３".isdigit(), "| ord:", hex(ord("３")))
# endregion

# 진짜 토큰은 이렇게 만든다 — 운영체제의 난수로 32바이트(256비트).
# 값은 실행마다 달라 화면에는 모양만 찍는다.
import re
import secrets

a, b = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
safe = re.fullmatch(r"[A-Za-z0-9_-]+", a) is not None
print(f"길이 {len(a)} | URL 에 안전한 글자뿐 {safe}")
print(f"두 번 같나 {a == b}")

# 이 venv 에 무엇이 깔려 있나 — 시험 도구와, 9장의 선택 기능이
# 기대는 패키지. 없으면 "없음", 있으면 판.
#   python 07/optional.py
import importlib.metadata as md
import importlib.util
import unicodedata

# (이 부에서 쓰려는 것, 배포판 이름, import 이름)
WANTED = [
    ("시험 실행기", "pytest", "pytest"),
    ("ASGI 시험 클라이언트", "starlette", "starlette.testclient"),
    ("그 밑의 HTTP", "httpx", "httpx"),
    ("DB 저장소", "SQLAlchemy", "sqlalchemy"),
    ("DB 스키마 이력", "alembic", "alembic"),
    ("원격 측정 API", "opentelemetry-api", "opentelemetry.trace"),
    ("원격 측정 SDK", "opentelemetry-sdk", "opentelemetry.sdk"),
]


# region: probe
def pad(s, n):
    """한글은 두 칸 — 화면의 칸 수로 맞춘다."""
    w = sum(
        2 if unicodedata.east_asian_width(c) == "W" else 1 for c in s
    )
    return s + " " * (n - w)


def version(dist):
    try:
        return md.version(dist)
    except md.PackageNotFoundError:
        return None


for use, dist, module in WANTED:
    v = version(dist)
    found = v and importlib.util.find_spec(module.split(".")[0])
    print(pad(use, 22), pad(dist, 18), v if found else "없음")
need = md.requires("google-api-core") or []
otel = [
    r
    for r in need
    if r.startswith("opentelemetry") and "extra" not in r
]
print("google-api-core 가 요구:", ", ".join(otel) or "없음")
# endregion

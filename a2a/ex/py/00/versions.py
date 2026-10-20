# 이 책의 캡처를 찍은 파이썬 쪽 판 — 설치본에게 직접 묻는다.
import importlib.metadata as meta
import re
import sys

from a2a.utils.constants import PROTOCOL_VERSION_CURRENT

# 우리가 깐 선택 설치 묶음(extra) 셋 — requirements.txt 첫 줄
EXTRAS = ("http-server", "grpc", "signing")


def name_of(req):
    """'grpcio>=1.60; extra == "grpc"' → 'grpcio'"""
    return re.match(r"[A-Za-z0-9_.-]+", req).group(0)


# region: show
print("python   ", sys.version.split()[0])
print("a2a-sdk  ", meta.version("a2a-sdk"))
print("프로토콜 ", PROTOCOL_VERSION_CURRENT)
for extra in EXTRAS:
    # 메타데이터의 요구 목록에서 이 extra 가 데려온 것만
    tag = f"extra == '{extra}'"
    names = [name_of(r) for r in meta.requires("a2a-sdk") if tag in r]
    got = [f"{n} {meta.version(n)}" for n in sorted(names)]
    print(f"[{extra}]", ", ".join(got))
# endregion

# 설치된 a2a 패키지의 지도 — 하위 패키지마다 파일 수·줄 수·설명.
#   python 07/sdk_map.py
# 설명은 각 __init__.py 의 문서 문자열 첫 줄이다(없으면 —).
import ast
from pathlib import Path

import a2a

ROOT = Path(a2a.__file__).parent


# region: walk
def size(path):
    # (파일 수, 줄 수) — 생성된 _pb2 도 센다
    files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
    return len(files), sum(
        len(f.read_text().splitlines()) for f in files
    )


def about(path):
    init = path / "__init__.py"
    doc = ast.get_docstring(ast.parse(init.read_text()))
    return doc.splitlines()[0] if doc else "—"


def show(base, depth=0):
    for p in sorted(base.iterdir()):
        if not p.is_dir() or p.name.startswith("__"):
            continue
        n, lines = size(p)
        name = "  " * depth + p.name + "/"
        print(f"{name:<22}{n:>3}개 {lines:>6}줄  {about(p)}")
        if p.name == "server":  # 서버 쪽은 한 층 더
            show(p, depth + 1)


# endregion

n, lines = size(ROOT)
print(f"a2a/ — 파일 {n}개, {lines}줄")
show(ROOT)

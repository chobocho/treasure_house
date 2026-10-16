# 완성 에이전트(agents/*.py)는 SDK 에서 무엇을 가져다 쓰는가.
#   python 07/used_names.py
# import 문만 읽는다(ast) — 에이전트를 돌리지 않는다.
import ast
import textwrap
from collections import defaultdict
from pathlib import Path

AGENTS = Path(__file__).parent.parent / "agents"


# region: scan
def a2a_imports(path):
    # from a2a.x.y import A, B → ("x.y", "A"), ("x.y", "B")
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            top, _, rest = node.module.partition(".")
            if top == "a2a":
                for alias in node.names:
                    yield rest, alias.name


users = defaultdict(set)  # (모듈, 이름) → 쓰는 파일들
for path in sorted(AGENTS.glob("*.py")):
    for key in a2a_imports(path):
        users[key].add(path.stem)

by_module = defaultdict(list)
for (module, name), files in sorted(users.items()):
    by_module[module].append(f"{name}({len(files)})")
for module, names in by_module.items():
    print(f"{module}:")
    print(
        textwrap.fill(
            " ".join(names),
            80,
            initial_indent="    ",
            subsequent_indent="    ",
        )
    )
print("이름", len(users), "개, 모듈", len(by_module), "개")
# endregion

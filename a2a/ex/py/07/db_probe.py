# DB 저장소와 a2a-db 명령 — sqlalchemy·alembic 이 없는 이 venv 에서
# 무엇이 되고 무엇이 안 되나. 소스는 import 하지 않고 글로 읽는다.
#   python 07/db_probe.py
import ast
import importlib.metadata as md
from importlib.resources import files

from a2a.server.tasks import (
    DatabasePushNotificationConfigStore,
    DatabaseTaskStore,
)


# region: stores
def first_line(e):
    return str(e).splitlines()[0]


def first_sentence(e):
    return str(e).split(". ")[0] + "."


for cls in (DatabaseTaskStore, DatabasePushNotificationConfigStore):
    print(f"import 됨: {cls.__name__} — {cls.__doc__}")
    try:
        cls(None)  # 엔진 자리에 아무것이나 — 만들 때 막힌다
    except ImportError as e:
        print("  만들면:", first_line(e))
        print("  까닭: ", first_sentence(e.__cause__))
# endregion


# region: schema
def columns(source, cls_name):
    """models.py 의 클래스 몸통에서 '이름: Mapped[…]' 줄을 모은다."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls_name:
            return [
                n.target.id
                for n in node.body
                if isinstance(n, ast.AnnAssign)
            ]
    return []


root = files("a2a")
models = (root / "server/models.py").read_text()
print("tasks 표의 열:", ", ".join(columns(models, "TaskMixin")))
history = []
for f in (root / "migrations/versions").iterdir():
    if f.name.endswith(".py") and f.name != "__init__.py":
        doc = ast.get_docstring(ast.parse(f.read_text())).splitlines()
        made = [x[13:23] for x in doc if x.startswith("Create Date")]
        history.append((made[0], f.name[:12], doc[0]))
for made, rev, title in sorted(history):  # 만든 날의 차례로
    print(f"  이력 {made} {rev} {title}")
# endregion


# region: cli
dist = md.distribution("a2a-sdk")
for ep in dist.entry_points.select(group="console_scripts"):
    print(f"명령: {ep.name} = {ep.value}")
try:
    import a2a.a2a_db_cli  # noqa: F401
except ImportError as e:
    print("  부르면:", first_line(e))
# endregion

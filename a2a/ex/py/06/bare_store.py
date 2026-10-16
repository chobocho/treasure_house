"""맨손 Task 저장소 — dict 하나와 상태 전이 표.

bare_lodging.py(맨손 숙소 에이전트)가 쓰고, store_rules.py 가 전이
규칙을 시험한다. 표준 라이브러리(uuid·datetime)만 쓴다.
"""

import uuid
from datetime import UTC, datetime

# region: states
SUBMITTED = "TASK_STATE_SUBMITTED"
WORKING = "TASK_STATE_WORKING"
INPUT_REQUIRED = "TASK_STATE_INPUT_REQUIRED"
AUTH_REQUIRED = "TASK_STATE_AUTH_REQUIRED"
COMPLETED = "TASK_STATE_COMPLETED"
FAILED = "TASK_STATE_FAILED"
CANCELED = "TASK_STATE_CANCELED"
REJECTED = "TASK_STATE_REJECTED"
TERMINAL = {COMPLETED, FAILED, CANCELED, REJECTED}

# 지금 상태 → 옮겨 갈 수 있는 상태. 스펙에는 이런 표가 없다(5부).
# 이 서버가 정한 것: 뒤로(SUBMITTED) 가지 않고, 종료 넷에서는
# 나갈 곳이 없고, 중단 둘에서는 다시 일하거나 취소될 뿐이다.
ALLOWED = {
    SUBMITTED: {WORKING, INPUT_REQUIRED, AUTH_REQUIRED, *TERMINAL},
    WORKING: {WORKING, INPUT_REQUIRED, AUTH_REQUIRED, *TERMINAL},
    INPUT_REQUIRED: {WORKING, CANCELED},
    AUTH_REQUIRED: {WORKING, CANCELED},
}


class IllegalMove(Exception):
    """표에 없는 전이 — 실행기의 버그다(요청 쪽 잘못이 아니다)."""


def can_move(src, dst):
    return dst in ALLOWED.get(src, ())  # 종료 상태는 표에 없다


# endregion


# region: ids
def new_id():
    """작업·맥락·메시지·아티팩트 id — UUID 판 4(무작위)."""
    return str(uuid.uuid4())


def now():
    """§5.6.1 의 꼴 — UTC, 밀리초, 끝은 Z."""
    t = datetime.now(UTC).isoformat(timespec="milliseconds")
    return t.replace("+00:00", "Z")


# endregion


# region: store
class Store:
    """taskId → Task(dict). 이 프로세스의 메모리에만 산다."""

    def __init__(self):
        self.tasks = {}

    def create(self, msg):
        """첫 메시지로 새 Task 를 짓는다 — 상태는 SUBMITTED."""
        task = {
            "id": new_id(),
            # 클라이언트가 맥락을 정해 왔으면 그대로 쓴다(§3.4.1)
            "contextId": msg.get("contextId") or new_id(),
            "status": {"state": SUBMITTED, "timestamp": now()},
            "artifacts": [],
            "history": [],
        }
        self.tasks[task["id"]] = task
        self.append(task, msg)
        return task

    def get(self, task_id):
        return self.tasks.get(task_id)

    def append(self, task, msg):
        """받은 메시지를 이력에 넣는다 — 두 id 를 채워서."""
        ids = {"messageId": msg["messageId"]}
        ids |= {"contextId": task["contextId"], "taskId": task["id"]}
        task["history"].append(ids | msg | ids)  # 키 차례는 proto 대로


# endregion


# region: move
def move(task, state, parts=None):
    """상태를 옮기고, 그 일을 알리는 스트림 이벤트를 돌려준다.

    지난 상태의 메시지(에이전트의 물음)는 이력으로 내린다.
    """
    src = task["status"]["state"]
    if not can_move(src, state):
        raise IllegalMove(f"{src} → {state}")
    if "message" in task["status"]:
        task["history"].append(task["status"]["message"])
    status = {"state": state}
    if parts:
        status["message"] = {
            "messageId": new_id(),
            "contextId": task["contextId"],
            "taskId": task["id"],
            "role": "ROLE_AGENT",
            "parts": parts,
        }
    status["timestamp"] = now()
    task["status"] = (
        status  # 고치지 않고 갈아 끼운다 — 앞 이벤트가 안전
    )
    ids = {"taskId": task["id"], "contextId": task["contextId"]}
    return {"statusUpdate": ids | {"status": status}}


# endregion


# region: artifact
def add_artifact(task, name, parts):
    """아티팩트를 붙이고, 그 일을 알리는 스트림 이벤트를 돌려준다."""
    art = {"artifactId": new_id(), "name": name, "parts": parts}
    task["artifacts"].append(art)
    ids = {"taskId": task["id"], "contextId": task["contextId"]}
    return {"artifactUpdate": ids | {"artifact": art}}


# endregion


# region: view
def view(task, history_length=None):
    """와이어로 내보낼 Task — 빈 목록은 빼고, 이력은 최근 N 개만.

    목록은 새로 만들어 담는다: 돌려준 뒤에 작업이 더 바뀌어도
    이미 내보낸(또는 내보낼) 모습은 그대로다.
    """
    out = {k: task[k] for k in ("id", "contextId", "status")}
    if task["artifacts"]:
        out["artifacts"] = list(task["artifacts"])
    hist = task["history"]
    if history_length is not None:  # 0 이면 이력 없이(§3.2.4)
        hist = hist[-history_length:] if history_length else []
    if hist:
        out["history"] = list(hist)
    return out


# endregion
# @ norun

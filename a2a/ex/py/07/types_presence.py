# 빈 값·있음(presence)·oneof·enum — 파이썬에서 None 이 안 나오는 까닭.
#   python 07/types_presence.py
from a2a.types import Message, Part, Role, Task, TaskState

msg = Message(message_id="m-1", role=Role.ROLE_USER)

# region: presence
# 문자열 필드는 None 이 아니라 "" — 안 채운 것과 빈 것이 같다
print("context_id:", repr(msg.context_id))
try:
    msg.HasField("context_id")  # 스칼라에는 '있음' 개념이 없다
except ValueError as e:
    print("ValueError:", e)
# 메시지 필드는 HasField 로 묻는다
task = Task(id="t-1")
print("status 있음?", task.HasField("status"))
_ = task.status.state  # 읽기만 해서는 생기지 않는다
print("읽은 뒤:", task.HasField("status"))
# endregion

# region: oneof
part = Part(text="30명")
part.url = "https://treasure-house.example/a.png"
print("oneof:", part.WhichOneof("content"), repr(part.text))
# endregion

# region: enum
# enum 은 int 다 — 이름으로도 넣어지고, 모르는 수도 들어간다
print(TaskState.TASK_STATE_WORKING, type(TaskState.TASK_STATE_WORKING))
msg.role = "ROLE_AGENT"
print("이름으로 넣은 role:", msg.role, Role.Name(msg.role))
msg.role = 99
print("모르는 수:", msg.role)
# endregion

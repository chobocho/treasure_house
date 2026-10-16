# protobuf 메시지를 파이썬 객체처럼 다룰 때 걸려 넘어지는 셋.
#   python 07/types_fields.py
from a2a.types import (
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
)

task = Task(id="t-1", context_id="c-1")

# region: assign
# ① 메시지 필드에는 = 로 대입할 수 없다
try:
    task.status = TaskStatus(state=TaskState.TASK_STATE_WORKING)
except AttributeError as e:
    print("AttributeError:", e)
task.status.state = TaskState.TASK_STATE_WORKING  # 안쪽 필드는 된다
task.status.CopyFrom(TaskStatus(state=TaskState.TASK_STATE_WORKING))
print("상태:", TaskState.Name(task.status.state))
# endregion

# region: copy
# ② append 는 복사해 넣는다 — 넣은 뒤 원본을 고쳐도 그대로
msg = Message(message_id="m-1", role=Role.ROLE_USER)
msg.parts.append(Part(text="30명"))
task.history.append(msg)
msg.parts[0].text = "40명"
print("이력:", task.history[0].parts[0].text)
# ③ 꺼낸 것은 참조다 — 꺼내서 고치면 task 가 바뀐다
first = task.history[0]
first.parts[0].text = "50명"
print("이력:", task.history[0].parts[0].text)
snap = Task()
snap.CopyFrom(task)  # 따로 두려면 CopyFrom
first.parts[0].text = "60명"
print("사본:", snap.history[0].parts[0].text)
# endregion

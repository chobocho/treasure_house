# Task 를 만드는 쪽(에이전트)과 읽는 쪽(클라이언트)의 타입 다루기.
#   python 07/types_task.py
from a2a.helpers import (
    get_data_parts,
    new_data_artifact,
    new_data_part,
    new_task_from_user_message,
)
from a2a.types import Message, Role, Task, TaskState
from google.protobuf import json_format

from workshop import domain

req = {"date": "2026-10-30", "nights": 1, "headcount": 30}
user = Message(
    message_id="m-1", role=Role.ROLE_USER, parts=[new_data_part(req)]
)

# region: make
task = new_task_from_user_message(user)  # SUBMITTED, 이력에 user
print("새 Task:", task.id, TaskState.Name(task.status.state))
quote = domain.choose_lodging(req)
task.artifacts.append(new_data_artifact("숙소 견적", quote))
task.status.state = TaskState.TASK_STATE_COMPLETED
# endregion

# region: read
wire = json_format.MessageToDict(task)  # 서버가 보내는 모양
got = json_format.ParseDict(wire, Task())  # 클라이언트가 읽은 것
art = got.artifacts[0]
data = get_data_parts(art.parts)[0]
print(art.name, data["venueName"], data["total"])
print("상태:", TaskState.Name(got.status.state))
wire["createdAt"] = "2026-10-16T00:00:00Z"  # 모르는 필드
try:
    json_format.ParseDict(wire, Task())
except json_format.ParseError as e:
    print("ParseError:", str(e).splitlines()[0])
json_format.ParseDict(wire, Task(), ignore_unknown_fields=True)
# endregion

# region: guard
agent_msg = Message(message_id="m-2", role=Role.ROLE_AGENT)
try:
    new_task_from_user_message(agent_msg)
except ValueError as e:
    print("ValueError:", e)
# endregion

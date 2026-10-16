# 메시지 하나를 만드는 세 길과, 그것이 와이어에서 어떻게 보이는가.
#   python 07/types_build.py
from a2a.helpers import new_text_message
from a2a.types import Message, Part, Role
from google.protobuf import json_format

# region: build
# ① 생성자에 필드를 키워드로 — 이름은 proto 의 snake_case
a = Message(
    message_id="m-1",
    role=Role.ROLE_USER,
    parts=[Part(text="숙소 부탁합니다")],
)
# ② 빈 메시지를 만들고 필드를 채운다
b = Message()
b.message_id = "m-1"
b.role = Role.ROLE_USER
b.parts.add(text="숙소 부탁합니다")  # 반복 필드에 하나 더
# ③ 도우미 — message_id 를 uuid4 로 짓는다
c = new_text_message("숙소 부탁합니다", role=Role.ROLE_USER)
print("a == b:", a == b)
print("c 의 id 만 다르다:", c.parts == a.parts, c.message_id != "m-1")
# endregion

# region: wire
# 와이어 이름(camelCase)·enum 이름으로 바꾸는 것은 json_format
print(json_format.MessageToJson(a, ensure_ascii=False, indent=2))
try:
    Message(messageId="m-1")  # 와이어 이름으로는 못 만든다
except ValueError as e:
    print("ValueError:", e)
# endregion

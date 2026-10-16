# SDK 의 Task 타입에는 어떤 필드가 있는가 — 생성된 코드에 묻는다.
#   python 05/task_shape.py
from a2a.types import Task, TaskStatus


# region: shape
def type_name(f):
    # 메시지·enum 이면 그 이름, 아니면 이 두 타입엔 문자열뿐이다
    t = f.message_type or f.enum_type
    return t.name if t else "string"


def fields(msg_type):
    # protobuf 메시지의 설명자(DESCRIPTOR)가 필드 목록을 안다
    print(msg_type.__name__)
    for f in msg_type.DESCRIPTOR.fields:
        many = "[]" if f.is_repeated else ""
        print(f"  {f.number}. {f.json_name}: {type_name(f)}{many}")


fields(Task)
fields(TaskStatus)
# endregion

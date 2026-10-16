# a2a.types 에는 무엇이 들었나 — 종류별로 세고, enum 두 개를 편다.
#   python 07/types_list.py
from a2a import types
from a2a.utils.errors import A2AError
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper
from google.protobuf.message import Message as ProtoMessage


# region: kinds
def kind(obj):
    if isinstance(obj, type) and issubclass(obj, ProtoMessage):
        return "protobuf 메시지"
    if isinstance(obj, EnumTypeWrapper):
        return "enum"
    if isinstance(obj, type) and issubclass(obj, A2AError):
        return "오류(예외)"
    return "그 밖"


groups = {}
for name in types.__all__:
    groups.setdefault(kind(getattr(types, name)), []).append(name)
for k in ("protobuf 메시지", "enum", "오류(예외)", "그 밖"):
    print(f"{k}: {len(groups[k])}개")
print("  그 밖 =", groups["그 밖"])
# endregion

# region: enums
for enum in (types.Role, types.TaskState):
    print(enum.DESCRIPTOR.name)
    for name, number in enum.items():
        print(f"  {number} {name}")
# endregion

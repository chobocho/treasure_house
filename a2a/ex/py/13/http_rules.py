# 세 바인딩의 메서드 대응표를 SDK 에 든 a2a.proto 에서 뽑는다.
# 파이썬 SDK 의 a2a_pb2 는 proto 를 컴파일한 것이라, 서비스의 각
# rpc 에 붙은 HTTP 주석(google.api.http)까지 그대로 들고 있다.
from a2a.types import a2a_pb2
from google.api import annotations_pb2

# region: rules
svc = a2a_pb2.DESCRIPTOR.services_by_name["A2AService"]
print("서비스:", svc.full_name)
for m in svc.methods:
    rule = m.GetOptions().Extensions[annotations_pb2.http]
    verb = rule.WhichOneof("pattern")  # get·post·delete …
    path = getattr(rule, verb)
    line = f"{m.name:33} {verb.upper():6} {path}"
    line += " [본문]" if rule.body == "*" else ""
    line += " [스트림]" if m.server_streaming else ""
    print(line)
# endregion

# region: extra
# 규칙마다 같은 경로를 /{tenant} 아래에 둔 짝(additional_bindings)
pairs = 0
for m in svc.methods:
    rule = m.GetOptions().Extensions[annotations_pb2.http]
    path = getattr(rule, rule.WhichOneof("pattern"))
    for b in rule.additional_bindings:
        if getattr(b, b.WhichOneof("pattern")) == "/{tenant}" + path:
            pairs += 1
print(f"/{{tenant}} 짝이 있는 rpc: {pairs}/{len(svc.methods)}")
print("gRPC 경로 예:", f"/{svc.full_name}/{svc.methods[0].name}")
# endregion

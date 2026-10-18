# gRPC 바인딩의 서비스 정의를 SDK 에 든 a2a.proto 에서 읽는다.
# 같은 A2AService 의 rpc 열하나가 이번에는 HTTP 주석이 아니라
# 요청·응답 메시지 타입과 스트림 여부로 보인다.
from a2a.types import a2a_pb2, a2a_pb2_grpc

# region: service
svc = a2a_pb2.DESCRIPTOR.services_by_name["A2AService"]
print("서비스:", svc.full_name)
for m in svc.methods:
    kind = "→ stream " if m.server_streaming else "→ "
    print(f"{m.name:33}{m.input_type.name}")
    print(f"{'':33}{kind}{m.output_type.name}")
# endregion

# region: stub
# grpcio-tools 가 만든 a2a_pb2_grpc 에는 서버 뼈대와 클라이언트
# 스텁이 같이 들어 있다 — SDK 는 둘 다 이것을 쓴다.
names = [n for n in dir(a2a_pb2_grpc) if not n.startswith("_")]
print("a2a_pb2_grpc:", ", ".join(n for n in names if "A2A" in n))
# endregion

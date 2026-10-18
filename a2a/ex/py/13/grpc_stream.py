# gRPC 의 스트림 — 서버 스트리밍 rpc 하나가 SSE 를 대신한다.
# 컴파일된 스텁으로 식사 에이전트에 SendStreamingMessage 를 보내고,
# 받은 StreamResponse 마다 무엇이 들었는지 한 줄씩 찍는다.
# 이어서 없는 작업에 SubscribeToTask — 스트림 안의 오류를 본다.
#   python 13/grpc_stream.py 127.0.0.1:P
import asyncio
import sys

import grpc
from a2a.types import a2a_pb2 as pb
from a2a.types import a2a_pb2_grpc
from google.protobuf import struct_pb2

V1 = (("a2a-version", "1.0"),)


def line(ev):
    kind = ev.WhichOneof("payload")  # task·message·statusUpdate…
    if kind == "task":
        return f"task {pb.TaskState.Name(ev.task.status.state)}"
    if kind == "status_update":
        state = ev.status_update.status.state
        return f"status_update {pb.TaskState.Name(state)}"
    if kind == "artifact_update":
        a = ev.artifact_update
        return (
            f"artifact_update {a.artifact.name} "
            f"append={a.append} last_chunk={a.last_chunk}"
        )
    return kind


async def main(target):
    stub = a2a_pb2_grpc.A2AServiceStub(
        grpc.aio.insecure_channel(target)
    )
    ask = struct_pb2.Value()
    ask.struct_value.update({"nights": 1, "headcount": 30})
    ask.struct_value.update({"vegetarians": 2})
    m = pb.Message(
        message_id="m-3", role=pb.ROLE_USER, parts=[pb.Part(data=ask)]
    )
    # region: stream
    req = pb.SendMessageRequest(message=m)
    async for ev in stub.SendStreamingMessage(req, metadata=V1):
        print(" ", line(ev))
    sub = stub.SubscribeToTask(
        pb.SubscribeToTaskRequest(id="t-nope"), metadata=V1
    )
    got = 0
    try:
        async for _ in sub:
            got += 1
    except grpc.aio.AioRpcError as e:
        print(f"  잇기: {e.code().name} (그 전에 받은 메시지 {got}개)")
    # endregion


asyncio.run(main(sys.argv[1]))
# @ norun

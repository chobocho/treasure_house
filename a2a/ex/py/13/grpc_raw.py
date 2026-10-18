# SDK 클라이언트 없이 gRPC 문을 두드린다 — 컴파일된 스텁만으로.
# 몸통과 메타데이터는 탭(13/grpc_tap.py)이 적으므로 여기서는 한 호출에
# 한 줄씩 상태 코드와 ErrorInfo 의 reason 만 찍는다.
#   python 13/grpc_raw.py 127.0.0.1:P
import asyncio
import sys

import grpc
from a2a.types import a2a_pb2 as pb
from a2a.types import a2a_pb2_grpc
from google.rpc import error_details_pb2, status_pb2

V1 = (("a2a-version", "1.0"),)
SVC = "/lf.a2a.v1.A2AService/"


def reasons(e):
    for k, v in e.trailing_metadata() or ():
        if k == "grpc-status-details-bin":
            st = status_pb2.Status.FromString(v)
            info = error_details_pb2.ErrorInfo()
            infos = [d for d in st.details if d.Is(info.DESCRIPTOR)]
            return [d.Unpack(info) and info.reason for d in infos]
    return []


# region: show
async def show(what, call):
    try:
        res = await call
    except grpc.aio.AioRpcError as e:
        print(f"{e.code().name:19} {reasons(e)} {what}")
        return None
    print(f"{'OK':19} {what}")
    return res


# endregion


def send(tenant=""):
    text = pb.Part(text="2026-10-30 1박 30명")
    m = pb.Message(message_id="m-1", role=pb.ROLE_USER, parts=[text])
    return pb.SendMessageRequest(message=m, tenant=tenant)


async def main(target):
    ch = grpc.aio.insecure_channel(target)
    stub = a2a_pb2_grpc.A2AServiceStub(ch)
    # region: calls
    r = await show("보내기", stub.SendMessage(send(), metadata=V1))
    tid = r.task.id
    get = pb.GetTaskRequest(id=tid, history_length=0)
    t = await show("읽기", stub.GetTask(get, metadata=V1))
    print("    state:", pb.TaskState.Name(t.status.state))
    cancel = pb.CancelTaskRequest(id=tid)
    await show("끝난 작업 취소", stub.CancelTask(cancel, metadata=V1))
    nope = pb.GetTaskRequest(id="t-nope")
    await show("없는 작업", stub.GetTask(nope, metadata=V1))
    await show("A2A-Version 없음", stub.SendMessage(send()))
    v9 = (("a2a-version", "9.9"),)
    await show("A2A-Version 9.9", stub.SendMessage(send(), metadata=v9))
    raw = ch.unary_unary(SVC + "SendMessage")  # 직렬화 없이 바이트
    await show("깨진 메시지", raw(b"\xff\xff\xff", metadata=V1))
    nope_rpc = ch.unary_unary(SVC + "Nope")
    await show("없는 메서드", nope_rpc(b"", metadata=V1))
    hq = send("bosang-hq")
    await show("tenant 필드", stub.SendMessage(hq, metadata=V1))
    # endregion
    await ch.close()


asyncio.run(main(sys.argv[1]))
# @ norun

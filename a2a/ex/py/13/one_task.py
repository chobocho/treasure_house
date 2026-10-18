# 한 작업, 세 문 — 카드의 supportedInterfaces 에서 세 주소를 읽어,
# JSON-RPC 로 만든 작업을 HTTP+JSON 과 gRPC 로 다시 읽는다.
# 요청 처리기와 작업 저장소가 하나라면 셋이 같은 작업을 본다.
#   python 13/one_task.py URL
import sys

import grpc
import httpx
from a2a.types import a2a_pb2 as pb
from a2a.types import a2a_pb2_grpc

V1 = {"A2A-Version": "1.0"}
send = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "SendMessage",
    "params": {
        "message": {
            "messageId": "m-1",
            "role": "ROLE_USER",
            "parts": [{"text": "2026-10-30 1박 30명"}],
        }
    },
}

# region: three
card = httpx.get(sys.argv[1] + ".well-known/agent-card.json").json()
door = {
    i["protocolBinding"]: i["url"] for i in card["supportedInterfaces"]
}
print("카드의 문:", ", ".join(door))
r = httpx.post(door["JSONRPC"], json=send, headers=V1).json()
task = r["result"]["task"]
print("JSON-RPC  만들기:", task["status"]["state"])
rest = httpx.get(f"{door['HTTP+JSON']}/tasks/{task['id']}", headers=V1)
print("HTTP+JSON 읽기:  ", rest.json()["status"]["state"])
stub = a2a_pb2_grpc.A2AServiceStub(grpc.insecure_channel(door["GRPC"]))
got = stub.GetTask(
    pb.GetTaskRequest(id=task["id"]), metadata=(("a2a-version", "1.0"),)
)
print("gRPC      읽기:  ", pb.TaskState.Name(got.status.state))
same = rest.json()["id"] == got.id == task["id"]
print("세 문의 작업 id 가 같다:", same)
# endregion
# @ norun

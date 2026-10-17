# 스펙에 없는 필드를 답에 끼워 보내는 작은 서버(실험용).
#   python 07/extra_server.py --port P [--url U]
# 받은 메시지의 글이 곧 실험 이름이다. SDK 는 타입과 카드에만 쓴다.
import argparse
import json

import uvicorn
from a2a.types import AgentCapabilities
from google.protobuf.json_format import MessageToDict
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from step2_task import card


def task_json():
    return {
        "id": "t-1",
        "contextId": "c-1",
        "status": {"state": "TASK_STATE_COMPLETED"},
    }


# region: variants
def result_for(name):
    """실험마다 정상 답의 한 곳에 모르는 것을 끼운다."""
    task = task_json()
    result = {"task": task}
    if name == "task":  # Task 안에 모르는 필드
        task["createdAt"] = "2026-10-16T00:00:00Z"
    elif name == "status":  # 한 층 더 안쪽
        task["status"]["progress"] = 0.5
    elif name == "result":  # task 옆에 모르는 키
        result["hint"] = "곧 끝납니다"
    elif name == "enum":  # 모르는 enum 이름
        task["status"]["state"] = "TASK_STATE_PAUSED"
    return result


# endregion


async def rpc(request):
    req = await request.json()
    name = req["params"]["message"]["parts"][0]["text"]
    body = {"jsonrpc": "2.0", "id": req["id"]}
    body["result"] = result_for(name)
    if name == "envelope":  # JSON-RPC 봉투에 모르는 키
        body["serverTime"] = "2026-10-16T00:00:00Z"
    if req["method"] == "SendStreamingMessage":
        data = json.dumps(body, ensure_ascii=False)
        sse = f"data: {data}\n\n"
        return Response(sse, media_type="text/event-stream")
    return JSONResponse(body)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--url")
    args = p.parse_args()
    c = card(args.url or f"http://127.0.0.1:{args.port}/")
    c.capabilities.CopyFrom(AgentCapabilities(streaming=True))
    shown = MessageToDict(c)
    shown["createdAt"] = "2026-10-16T00:00:00Z"  # 카드에도 하나

    async def agent_card(request):
        return JSONResponse(shown)

    app = Starlette(
        routes=[
            Route("/.well-known/agent-card.json", agent_card),
            Route("/", rpc, methods=["POST"]),
        ]
    )
    uvicorn.run(
        app, host="127.0.0.1", port=args.port, log_level="warning"
    )


if __name__ == "__main__":
    main()
# @ norun

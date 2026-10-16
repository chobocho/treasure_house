"""총무팀의 명령줄 클라이언트.

에이전트에게 말을 걸고 오가는 것을 찍는다.

    python agents/ask.py URL [--data JSON] [--token T] 첫말 [답1 답2 …]

작업이 INPUT_REQUIRED·AUTH_REQUIRED 에서 멈추면 남은 답을 같은
taskId·contextId 로 차례로 보낸다(대본이 있는 대화). 카드가 스트리밍을
지원하면 스트림으로, 아니면 막는 호출로 받는다.
"""

import argparse
import asyncio
import json

import httpx
from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part, new_text_part
from a2a.types import Message, Role, SendMessageRequest, TaskState
from google.protobuf.json_format import MessageToDict

PAUSED = {
    TaskState.TASK_STATE_INPUT_REQUIRED,
    TaskState.TASK_STATE_AUTH_REQUIRED,
}


def tidy(v):
    """30.0 처럼 소수부가 없는 실수는 정수로 보인다(4부 참고)."""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, dict):
        return {k: tidy(x) for k, x in v.items()}
    if isinstance(v, list):
        return [tidy(x) for x in v]
    return v


def dump(data):
    """짧으면 한 줄, 길면 들여 쓴 여러 줄(접힌 폰 화면 폭 때문)."""
    one = json.dumps(data, ensure_ascii=False, sort_keys=True)
    if len(one) <= 60:
        return one
    return json.dumps(
        data, ensure_ascii=False, sort_keys=True, indent=1
    )


def show_parts(parts):
    """파트 하나당 한 조각: 글은 그대로, 데이터는 JSON, 파일은 크기."""
    out = []
    for p in parts:
        d = MessageToDict(p)
        if "text" in d:
            out.append(d["text"].rstrip("\n"))
        elif "data" in d:
            out.append(dump(tidy(d["data"])))
        elif "raw" in d:
            out.append(
                f"<{d.get('filename', '파일')} {len(p.raw)}바이트>"
            )
        elif "url" in d:
            out.append(f"<{d['url']}>")
    return " | ".join(out)


def state_name(state):
    return TaskState.Name(state).removeprefix("TASK_STATE_")


def show(event):
    """StreamResponse 하나를 한 줄로 찍는다.

    돌려주는 값은 (taskId, contextId, 상태) — 메시지면 None.
    """
    kind = event.WhichOneof("payload")
    if kind == "message":
        print(f"message: {show_parts(event.message.parts)}")
        return None
    if kind == "task":
        t = event.task
        msg = show_parts(t.status.message.parts)
        print(f"task {state_name(t.status.state)} {msg}".rstrip())
        for a in t.artifacts:
            print(f"  artifact {a.name}: {show_parts(a.parts)}")
        return t.id, t.context_id, t.status.state
    if kind == "status_update":
        s = event.status_update
        msg = show_parts(s.status.message.parts)
        print(f"status {state_name(s.status.state)} {msg}".rstrip())
        return s.task_id, s.context_id, s.status.state
    a = event.artifact_update
    flags = "+" if a.append else ""
    flags += " (끝)" if a.last_chunk else ""
    print(
        f"artifact {a.artifact.name}{flags}: "
        f"{show_parts(a.artifact.parts)}"
    )
    return a.task_id, a.context_id, None


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("lines", nargs="*", help="첫말과 이어질 답들")
    p.add_argument("--data", help="첫 메시지에 붙일 DataPart(JSON)")
    p.add_argument("--token", help="Bearer 토큰")
    p.add_argument("--no-stream", action="store_true")
    args = p.parse_args()
    headers = (
        {"Authorization": f"Bearer {args.token}"} if args.token else {}
    )
    http = httpx.AsyncClient(headers=headers, timeout=30)
    config = ClientConfig(
        streaming=not args.no_stream, httpx_client=http
    )
    client = await create_client(args.url, config)
    lines = list(args.lines)
    parts = [new_text_part(lines.pop(0))] if lines else []
    if args.data:
        parts.append(new_data_part(json.loads(args.data)))
    task_id = context_id = None
    while True:
        msg = Message(role=Role.ROLE_USER, parts=parts, message_id="")
        msg.message_id = f"ask-{len(lines)}"  # 대본 안에서 겹치지 않게
        if task_id:
            msg.task_id, msg.context_id = task_id, context_id
        last = None
        async for ev in client.send_message(
            SendMessageRequest(message=msg)
        ):
            seen = show(ev)
            if seen and seen[2] is not None:
                task_id, context_id, last = seen
        if last not in PAUSED or not lines:
            break
        reply = lines.pop(0)
        print(f"> {reply}")
        parts = [new_text_part(reply)]
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())

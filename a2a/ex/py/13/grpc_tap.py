# gRPC 와이어 탭 — tools/wiretap.py 는 HTTP/1.1 만 읽어서 gRPC 의
# HTTP/2 를 넘기지 못한다. 그래서 gRPC 로 받아 gRPC 로 넘기는 작은
# 중계기를 둔다. 메시지는 바이트 그대로 넘기고, 화면에는 proto 를
# 풀어 JSON 으로 찍는다(data·metadata 아래 키는 정렬).
#   python 13/grpc_tap.py LISTEN_PORT TARGET_PORT
import asyncio
import json
import sys

import grpc
from a2a.types import a2a_pb2
from google.protobuf import json_format, message_factory
from google.rpc import error_details_pb2, status_pb2

SVC = a2a_pb2.DESCRIPTOR.services_by_name["A2AService"]
SEEN = ("a2a-version", "a2a-extensions", "authorization", "user-agent")
SKIP = ("date",)  # grpc-js 가 붙이는 시각 — 매번 달라 뺀다
DETAILS = "grpc-status-details-bin"
assert error_details_pb2  # Any 안의 ErrorInfo 를 풀려면 등록돼야 한다


def say(*a):
    print(*a, flush=True)


def tidy(v, key=""):
    # data·metadata 아래(Struct·map)만 키를 정렬한다 — 파이썬 SDK 가
    # 프로세스마다 다른 차례로 내보내는 자리(0부)
    deep = key in ("data", "metadata")
    if isinstance(v, dict):
        items = sorted(v.items()) if deep else v.items()
        return {k: tidy(x, key if deep else k) for k, x in items}
    if isinstance(v, list):
        return [tidy(x, key) for x in v]
    return v


def dump(desc, raw, pad="  "):
    if desc is None:
        say(f"{pad}({len(raw)}바이트)")
        return
    msg = message_factory.GetMessageClass(desc)()
    try:
        msg.ParseFromString(raw)
    except Exception as e:  # noqa: BLE001 — 깨진 바이트도 그대로 넘긴다
        say(f"{pad}(풀 수 없는 {len(raw)}바이트: {type(e).__name__})")
        return
    text = json.dumps(
        tidy(json_format.MessageToDict(msg)),
        ensure_ascii=False,
        indent=2,
    )
    say("\n".join(pad + ln for ln in text.split("\n")))


def show_md(title, md):
    for k, v in sorted(md or ()):
        if k == DETAILS:
            say(f"  {title} {k} (google.rpc.Status):")
            dump(status_pb2.Status.DESCRIPTOR, v, "    ")
        elif k not in SKIP and (title != "→" or k in SEEN):
            say(f"  {title} {k}: {v}")


# region: relay
class Tap(grpc.GenericRpcHandler):
    def __init__(self, target):
        self.ch = grpc.aio.insecure_channel(f"127.0.0.1:{target}")

    def service(self, details):
        m = SVC.methods_by_name.get(details.method.rsplit("/", 1)[-1])
        ins, outs = (m.input_type, m.output_type) if m else (None, None)
        streaming = bool(m and m.server_streaming)

        async def handle(req, ctx):
            say(f"→ {details.method}")
            show_md("→", ctx.invocation_metadata())
            dump(ins, req)
            call = self.ch.unary_stream(details.method)(
                req, metadata=ctx.invocation_metadata()
            )
            n = 0
            try:
                async for res in call:
                    n += 1
                    say(f"← 메시지 {n}")
                    dump(outs, res)
                    yield res
            except grpc.aio.AioRpcError as e:
                await self.finish(e.code(), e.details(), call, ctx)
                await ctx.abort(e.code(), e.details())
            await self.finish(await call.code(), "", call, ctx)

        if streaming:
            return grpc.unary_stream_rpc_method_handler(handle)

        async def unary(req, ctx):
            last = None
            async for res in handle(req, ctx):
                last = res
            return last

        return grpc.unary_unary_rpc_method_handler(unary)

    # endregion

    async def finish(self, code, text, call, ctx):
        say(f"← {code.name}" + (f" {text!r}" if text else ""))
        show_md("← 머리글", await call.initial_metadata())
        trailer = await call.trailing_metadata()
        show_md("← 꼬리", trailer)
        ctx.set_trailing_metadata(tuple(trailer or ()))


async def main(listen, target):
    server = grpc.aio.server()
    server.add_generic_rpc_handlers((Tap(target),))
    server.add_insecure_port(f"127.0.0.1:{listen}")
    await server.start()
    await server.wait_for_termination()


asyncio.run(main(*sys.argv[1:3]))
# @ norun

# 클라이언트로 무엇을 할 수 있나 — 설치본의 Client·ClientConfig 에
# 묻고, 서버 쪽 처리기 메서드와 짝지어 본다.
#   python 07/client_api.py
import dataclasses

from a2a.client import Client, ClientConfig
from a2a.server.request_handlers import RequestHandler


# region: api
def handler_name(method):
    """클라이언트 메서드 → 같은 A2A 메서드를 받는 on_* 이름."""
    rename = {
        "send_message": "on_message_send(_stream)",
        "subscribe": "on_subscribe_to_task",
        "get_extended_agent_card": "on_get_extended_agent_card",
    }
    if method in rename:
        return rename[method]
    name = "on_" + method
    return name if hasattr(RequestHandler, name) else "—"


print("Client 의 추상 메서드 → 서버 처리기")
for m in sorted(Client.__abstractmethods__):
    print(f"  {m:39} {handler_name(m)}")
print("ClientConfig 필드 = 기본값")
for f in dataclasses.fields(ClientConfig):
    if f.default is not dataclasses.MISSING:
        value = repr(f.default)
    else:
        value = repr(f.default_factory())
    print(f"  {f.name:28} = {value}")
# endregion

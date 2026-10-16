# 요청 처리기 — A2A 메서드와 처리기 메서드, 그리고 생성자의 손잡이.
#   python 07/handler_api.py
import inspect

from a2a.server.request_handlers import (
    DefaultRequestHandler,
    RequestHandler,
)
from a2a.server.routes.jsonrpc_dispatcher import JsonRpcDispatcher

# region: methods
print("JSON-RPC 메서드 → params 타입 (JsonRpcDispatcher)")
for method, model in JsonRpcDispatcher.METHOD_TO_MODEL.items():
    print(f"  {method:<33}{model.__name__}")
print("RequestHandler 의 추상 메서드")
for name in sorted(RequestHandler.__abstractmethods__):
    print("  " + name)
# endregion

# region: options
print("DefaultRequestHandler(…) 의 인자")
sig = inspect.signature(DefaultRequestHandler.__init__)
for p in list(sig.parameters.values())[1:]:
    need = "필수" if p.default is p.empty else f"기본 {p.default}"
    print(f"  {p.name:<25}{need}")
# endregion

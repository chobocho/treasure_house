# 처리기·실행기가 던지는 A2A 오류는 와이어에서 무엇이 되나.
#   python 07/error_codes.py
# JSON-RPC 코드와 HTTP+JSON 바인딩의 상태·이유를 SDK 의 표에서 읽는다.
from a2a.utils.errors import A2A_ERROR_MAPPING, JSON_RPC_ERROR_CODE_MAP

# region: codes
print(f"{'오류 클래스':<33}JSON-RPC  HTTP  reason")
for cls, code in sorted(
    JSON_RPC_ERROR_CODE_MAP.items(), key=lambda kv: -kv[1]
):
    m = A2A_ERROR_MAPPING.get(cls)
    http = f"{m.http_code}  {m.reason}" if m else "—"
    print(f"{cls.__name__:<38}{code:<10}{http}")
# endregion

# JSON-RPC 2.0 요청 하나를 표준 라이브러리만으로 만든다.
import json

# region: request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "SendMessage",
    "params": {
        "message": {
            "role": "ROLE_USER",
            "messageId": "msg-1",
            "parts": [{"text": "1박 2일, 30명"}],
        },
    },
}
# endregion

print(json.dumps(request, ensure_ascii=False, indent=2))

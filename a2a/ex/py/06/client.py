# 맨손 클라이언트 — urllib 만으로 카드를 읽고, JSON-RPC 인터페이스를
# 골라, 숙소 에이전트와 두 번 이야기한다(막는 호출, 그다음 스트림).
#   python 06/client.py 에이전트_주소
import itertools
import json
import sys
import urllib.request

N = itertools.count(1)  # JSON-RPC id 와 messageId 를 매기는 번호


# region: card
def pick(base):
    """카드를 받아 JSON-RPC 1.0 인터페이스를 고른다(§8.3.2)."""
    url = base.rstrip("/") + "/.well-known/agent-card.json"
    with urllib.request.urlopen(url) as r:
        card = json.load(r)
    # 앞의 것이 더 바라는 인터페이스다(§8.3.1) — 처음 맞는 것을 쓴다
    for i in card.get("supportedInterfaces", []):
        ver = i.get("protocolVersion", "").split(".")[:2]
        if i.get("protocolBinding") == "JSONRPC" and ver == ["1", "0"]:
            return card, i
    sys.exit("쓸 수 있는 인터페이스가 없습니다")


# endregion


# region: rpc
def rpc(iface, method, params):
    """봉투를 싸서 고른 인터페이스의 url 로 — 판 머리글은 늘(§3.6.1)."""
    if iface.get("tenant"):  # 카드에 tenant 가 있으면 그대로(§8.3.2)
        params = {"tenant": iface["tenant"], **params}
    body = {"jsonrpc": "2.0", "id": next(N), "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    data = json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(iface["url"], data, head)
    return urllib.request.urlopen(req)


def result(resp):
    """JSON-RPC 응답 → result. 오류면 code 와 message 를 들고 끝낸다."""
    if "error" in resp:
        sys.exit(
            f"오류 {resp['error']['code']} {resp['error']['message']}"
        )
    return resp["result"]


def message(text, ids=None):
    """사용자 메시지 — 이어 말하기면 taskId·contextId 를 단다."""
    msg = {"messageId": f"c-{next(N)}", "role": "ROLE_USER"}
    msg |= ids or {}
    msg["parts"] = [{"text": text}]
    return msg


# endregion


# region: stream
def sse_events(lines):
    """2부의 파서 그대로 — 빈 줄이 이벤트의 끝이다."""
    data = []
    for raw in lines:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line == "":
            if data:
                yield "\n".join(data)
            data = []
        elif line.startswith("data:"):
            data.append(line[5:].removeprefix(" "))


def stream(iface, msg):
    """SendStreamingMessage → StreamResponse 를 하나씩."""
    with rpc(iface, "SendStreamingMessage", {"message": msg}) as r:
        if r.headers.get_content_type() != "text/event-stream":
            yield result(json.load(r))  # 첫 이벤트 전의 오류(5장)
            return
        for data in sse_events(r):
            yield result(json.loads(data))


# endregion


# region: show
def texts(parts):
    return " ".join(p["text"] for p in parts if "text" in p)


def show(res):
    """StreamResponse 하나 → (한 줄, 이어 말할 때 쓸 두 id)."""
    kind, v = next(iter(res.items()))  # oneof — 키는 하나뿐
    if kind == "message":
        return f"message {texts(v['parts'])}", None
    if kind == "task":
        ids = {"taskId": v["id"], "contextId": v["contextId"]}
    else:
        ids = {"taskId": v["taskId"], "contextId": v["contextId"]}
    if kind == "artifactUpdate":
        a = v["artifact"]
        return f"{kind} {a['name']}: {texts(a['parts'])}", ids
    st = v["status"]
    said = texts(st.get("message", {}).get("parts", []))
    arts = [texts(a["parts"]) for a in v.get("artifacts", [])]
    words = [kind, st["state"][11:], said, *arts]
    return " ".join(w for w in words if w), ids


# endregion


# region: main
def send(text, ids=None):
    """SendMessage(막는 호출) → 답 Task 를 한 줄로."""
    params = {"message": message(text, ids)}
    with rpc(iface, "SendMessage", params) as r:
        return show(result(json.load(r)))


card, iface = pick(sys.argv[1])
print(f"카드: {card['name']} → JSONRPC {iface['protocolVersion']}")
line, ids = send("2026-10-30 1박")
print(f"① SendMessage → {line}")
line, ids = send("30명", ids)  # 같은 작업에 이어 말하기
print(f"② 이어 말하기 → {line}")
print("③ SendStreamingMessage '2026-11-06 1박'")
for res in stream(iface, message("2026-11-06 1박")):
    line, ids = show(res)
    print(f"   {line}")
print("④ SendStreamingMessage '20명'")
for res in stream(iface, message("20명", ids)):
    print(f"   {show(res)[0]}")
# endregion
# @ norun

// 맨손 클라이언트 — fetch 만으로 카드를 읽고, JSON-RPC 인터페이스를
// 골라, 숙소 에이전트와 두 번 이야기한다(막는 호출, 그다음 스트림).
//     node 06/client.ts 에이전트_주소

type Obj = Record<string, any>;
type Ids = { taskId: string; contextId: string };
let n = 0; // JSON-RPC id 와 messageId 를 매기는 번호

// region: card
// 카드를 받아 JSON-RPC 1.0 인터페이스를 고른다(§8.3.2).
async function pick(base: string): Promise<[Obj, Obj]> {
  const url = base.replace(/\/$/, "") + "/.well-known/agent-card.json";
  const card = await (await fetch(url)).json();
  // 앞의 것이 더 바라는 인터페이스다(§8.3.1) — 처음 맞는 것을 쓴다
  const iface = (card.supportedInterfaces ?? []).find(
    (i: Obj) =>
      i.protocolBinding === "JSONRPC" &&
      String(i.protocolVersion).split(".").slice(0, 2).join(".") ===
        "1.0",
  );
  if (!iface) throw new Error("쓸 수 있는 인터페이스가 없습니다");
  return [card, iface];
}
// endregion

// region: rpc
// 봉투를 싸서 고른 인터페이스의 url 로 — 판 헤더는 늘(§3.6.1).
function rpc(iface: Obj, method: string, params: Obj) {
  if (iface.tenant) params = { tenant: iface.tenant, ...params };
  const body = { jsonrpc: "2.0", id: ++n, method, params };
  return fetch(iface.url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "A2A-Version": "1.0",
    },
    body: JSON.stringify(body),
  });
}

// JSON-RPC 응답 → result. 오류면 code 와 message 를 들고 끝낸다.
function result(resp: Obj): Obj {
  if (resp.error) {
    console.log(`오류 ${resp.error.code} ${resp.error.message}`);
    process.exit(1);
  }
  return resp.result;
}

// 사용자 메시지 — 이어 말하기면 taskId·contextId 를 단다.
function message(text: string, ids?: Ids) {
  const head = { messageId: `c-${++n}`, role: "ROLE_USER" };
  return { ...head, ...ids, parts: [{ text }] };
}
// endregion

// region: stream
// 2부의 파서를 줄였다 — data 줄을 모으고, 빈 줄이 이벤트의 끝.
async function* sseEvents(chunks: AsyncIterable<string>) {
  let buf = "";
  let data: string[] = [];
  for await (const chunk of chunks) {
    buf += chunk; // 조각은 줄 중간에서 끊길 수 있다
    let i: number;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).replace(/\r$/, "");
      buf = buf.slice(i + 1);
      if (line === "" && data.length > 0) yield data.join("\n");
      if (line === "") data = [];
      else if (line.startsWith("data:"))
        data.push(line.slice(5).replace(/^ /, ""));
    }
  }
}

// SendStreamingMessage → StreamResponse 를 하나씩.
async function* stream(iface: Obj, msg: Obj) {
  const res = await rpc(iface, "SendStreamingMessage", {
    message: msg,
  });
  const type = res.headers.get("content-type") ?? "";
  if (!type.startsWith("text/event-stream")) {
    yield result(await res.json()); // 첫 이벤트 전의 오류(5장)
    return;
  }
  const text = res.body!.pipeThrough(new TextDecoderStream());
  for await (const data of sseEvents(text)) {
    yield result(JSON.parse(data));
  }
}
// endregion

// region: show
const texts = (parts: Obj[]) =>
  parts
    .filter((p) => "text" in p)
    .map((p) => p.text)
    .join(" ");

// StreamResponse 하나 → [한 줄, 이어 말할 때 쓸 두 id].
function show(res: Obj): [string, Ids | undefined] {
  const [kind, v] = Object.entries(res)[0]!; // oneof — 키는 하나뿐
  if (kind === "message")
    return [`message ${texts(v.parts)}`, undefined];
  const taskId = kind === "task" ? v.id : v.taskId;
  const ids = { taskId, contextId: v.contextId };
  if (kind === "artifactUpdate") {
    const a = v.artifact;
    return [`${kind} ${a.name}: ${texts(a.parts)}`, ids];
  }
  const said = texts(v.status.message?.parts ?? []);
  const arts = (v.artifacts ?? []).map((a: Obj) => texts(a.parts));
  const words = [kind, v.status.state.slice(11), said, ...arts];
  return [words.filter((w) => w).join(" "), ids];
}
// endregion

// region: main
// SendMessage(막는 호출) → 답 Task 를 한 줄로.
async function send(text: string, ids?: Ids) {
  const res = await rpc(iface, "SendMessage", {
    message: message(text, ids),
  });
  return show(result(await res.json()));
}

const [card, iface] = await pick(process.argv[2]!);
console.log(`카드: ${card.name} → JSONRPC ${iface.protocolVersion}`);
let [line, ids] = await send("2026-10-30 1박");
console.log(`① SendMessage → ${line}`);
[line, ids] = await send("30명", ids); // 같은 작업에 이어 말하기
console.log(`② 이어 말하기 → ${line}`);
console.log("③ SendStreamingMessage '2026-11-06 1박'");
for await (const res of stream(iface, message("2026-11-06 1박"))) {
  [line, ids] = show(res);
  console.log(`   ${line}`);
}
console.log("④ SendStreamingMessage '20명'");
for await (const res of stream(iface, message("20명", ids))) {
  console.log(`   ${show(res)[0]}`);
}
// endregion
//@ norun

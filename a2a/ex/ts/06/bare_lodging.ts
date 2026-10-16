// 맨손 숙소 에이전트 — SDK 없이, Node 기본 모듈만으로 A2A v1.0.
//
// JSON-RPC 바인딩 하나: 카드, SendMessage, GetTask, CancelTask,
// SendStreamingMessage(SSE). 업무 규칙은 workshop/domain 이 정하고,
// 말과 기록은 완성 에이전트(agents/lodging.ts)와 같다.
//
//     node 06/bare_lodging.ts --port P [--url 카드에_적을_주소]
import {
  createServer,
  type IncomingHttpHeaders,
  type ServerResponse,
} from "node:http";
import { parseArgs } from "node:util";
import {
  chooseLodging,
  DATE,
  HEADCOUNT,
  NIGHTS,
} from "../workshop/domain.ts";
import {
  addArtifact,
  CANCELED,
  canMove,
  COMPLETED,
  INPUT_REQUIRED,
  move,
  REJECTED,
  Store,
  view,
  WORKING,
  type Message,
  type StreamResponse,
  type Task,
} from "./bare_store.ts";

// region: card
// 완성 에이전트의 카드와 같은 필드·같은 값(3부).
function card(url: string) {
  return {
    name: "보물상사 숙소 에이전트",
    description: "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",
    supportedInterfaces: [
      { url, protocolBinding: "JSONRPC", protocolVersion: "1.0" },
    ],
    provider: {
      url: "https://treasure-house.example",
      organization: "보물상사",
    },
    version: "1.0.0",
    capabilities: { streaming: true },
    defaultInputModes: ["application/json", "text/plain"],
    defaultOutputModes: ["application/json"],
    skills: [
      {
        id: "find-lodging",
        name: "숙소 찾기",
        description: "워크숍 숙소를 고르고 견적을 냅니다.",
        tags: ["lodging", "workshop"],
        examples: ['{"date":"2026-10-30","nights":1,"headcount":30}'],
      },
    ],
  };
}
// endregion

// region: rpc-error
// JSON-RPC 의 error 객체 하나 — code·message·data.
class RpcError extends Error {
  code: number;
  data?: object[];
  constructor(code: number, message: string, data?: object[]) {
    super(message);
    this.code = code;
    this.data = data;
  }
  body() {
    const { code, message, data } = this;
    return data ? { code, message, data } : { code, message };
  }
}
// endregion

// region: a2a-errors
const GOOGLE = "type.googleapis.com/google.rpc.";
// §5.4 의 A2A 오류 가운데 이 서버가 내는 넷 — 코드·문구·reason
const A2A_ERRORS = {
  TaskNotFound: [-32001, "Task not found", "TASK_NOT_FOUND"],
  TaskNotCancelable: [
    -32002,
    "Task cannot be canceled",
    "TASK_NOT_CANCELABLE",
  ],
  UnsupportedOperation: [
    -32004,
    "Unsupported operation",
    "UNSUPPORTED_OPERATION",
  ],
  VersionNotSupported: [
    -32009,
    "Version not supported",
    "VERSION_NOT_SUPPORTED",
  ],
} as const;

// A2A 오류 — data 에 google.rpc.ErrorInfo 하나(§9.5).
function a2aError(
  name: keyof typeof A2A_ERRORS,
  metadata: Record<string, string>,
) {
  const [code, message, reason] = A2A_ERRORS[name];
  const info = { "@type": GOOGLE + "ErrorInfo", reason };
  return new RpcError(code, message, [
    { ...info, domain: "a2a-protocol.org", metadata },
  ]);
}

// -32602 — 어느 필드가 왜 틀렸는지 BadRequest 로(§9.5 의 예).
function badParams(field: string, description: string) {
  const fieldViolations = [{ field, description }];
  const data = [{ "@type": GOOGLE + "BadRequest", fieldViolations }];
  return new RpcError(-32602, "Invalid parameters", data);
}
// endregion

// region: version
// §3.6.2 — 요청의 판으로 처리하고, 모르는 판이면 -32009.
// 빈 값은 0.3 으로 읽는다. 패치 번호(1.0.1 의 .1)는 보지 않는다.
function checkVersion(headers: IncomingHttpHeaders) {
  const asked = String(headers["a2a-version"] || "0.3");
  if (asked.split(".").slice(0, 2).join(".") !== "1.0") {
    throw a2aError("VersionNotSupported", { version: asked });
  }
}
// endregion

// region: lodging
const store = new Store();

// 빠진 항목을 하나씩 되묻는다. 순서가 곧 묻는 순서다.
const QUESTIONS: Record<string, string> = {
  date: "날짜는 언제입니까? (예: 2026-10-30)",
  nights: "며칠 묵습니까? (예: 1박)",
  headcount: "인원은 몇 명입니까?",
};
const RULES = { date: DATE, nights: NIGHTS, headcount: HEADCOUNT };

// 사용자가 지금까지 한 말 → 요청. DataPart 먼저, 글이 덮는다.
// 에이전트의 물음은 건너뛴다 — 물음 속 '예: 1박' 은 답이 아니다.
function heard(task: Task): Record<string, unknown> {
  const said = task.history.filter((m) => m.role === "ROLE_USER");
  const parts = said.flatMap((m) => m.parts);
  const req: Record<string, unknown> = {};
  for (const p of parts) {
    const d = p.data;
    if (typeof d === "object" && d && !Array.isArray(d)) {
      Object.assign(req, d);
    }
  }
  for (const p of parts) {
    for (const [key, rx] of Object.entries(RULES)) {
      const found = rx.exec(typeof p.text === "string" ? p.text : "");
      if (found) req[key] = found[1];
    }
  }
  return req;
}
// endregion

// region: work
// ['headcount'] — 파이썬이 리스트를 찍는 모양 그대로(서버 기록용)
const pyList = (xs: string[]) =>
  `[${xs.map((x) => `'${x}'`).join(", ")}]`;
const comma = (n: number) =>
  String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");

// 완성 에이전트의 실행기가 하는 일. 이벤트의 목록을 돌려준다.
function lodging(task: Task): StreamResponse[] {
  const req = heard(task);
  const missing = Object.keys(QUESTIONS).filter((k) => !(k in req));
  if (missing.length > 0) {
    console.log(`[숙소] 되묻기: ${pyList(missing)}`);
    const ask = [
      { text: QUESTIONS[missing[0]!] },
      { data: { missing } },
    ];
    return [move(task, INPUT_REQUIRED, ask)];
  }
  const quote = chooseLodging({
    date: String(req.date),
    nights: Math.trunc(Number(req.nights)),
    headcount: Math.trunc(Number(req.headcount)),
  });
  if (!quote.ok) {
    console.log(`[숙소] 거절: ${quote.reason}`);
    return [move(task, REJECTED, [{ text: quote.reason }])];
  }
  const summary =
    `${quote.venueName} ${quote.rooms}실, ` + `${comma(quote.total)}원`;
  console.log(`[숙소] 견적: ${summary}`);
  const parts = [{ data: quote }, { text: summary }];
  return [addArtifact(task, "숙소 견적", parts), move(task, COMPLETED)];
}
// endregion

// region: check
const CONTENT = ["text", "raw", "url", "data"]; // Part 의 oneof(4부)
type Params = Record<string, unknown>;

// SendMessageRequest.message 의 필수 필드(§5.7) — 틀리면 -32602.
function checkMessage(params: Params): Message {
  const msg = params.message as Message | undefined;
  if (typeof msg !== "object" || msg === null || Array.isArray(msg)) {
    throw badParams("message", "메시지가 없습니다");
  }
  if (typeof msg.messageId !== "string" || !msg.messageId) {
    throw badParams("message.messageId", "비어 있습니다");
  }
  if (msg.role !== "ROLE_USER") {
    throw badParams("message.role", "ROLE_USER 여야 합니다");
  }
  if (!Array.isArray(msg.parts) || msg.parts.length === 0) {
    throw badParams("message.parts", "파트가 하나도 없습니다");
  }
  for (const p of msg.parts) {
    const n = CONTENT.filter((k) => p && Object.hasOwn(p, k)).length;
    if (typeof p !== "object" || n !== 1) {
      const why = "text·raw·url·data 중 하나만 있어야 합니다";
      throw badParams("message.parts", why);
    }
  }
  return msg;
}

// id 로 작업을 찾는다 — 없으면 -32001(§3.4.2).
function find(taskId: unknown): Task {
  const task =
    typeof taskId === "string" ? store.get(taskId) : undefined;
  if (!task) throw a2aError("TaskNotFound", { taskId: String(taskId) });
  return task;
}
// endregion

// region: begin
// 두 Send 메서드의 앞부분 — 새 작업이거나 이어 말하기다.
function begin(params: Params): Task {
  const msg = checkMessage(params);
  if (!msg.taskId) return store.create(msg);
  const task = find(msg.taskId);
  if ((msg.contextId || task.contextId) !== task.contextId) {
    const why = "작업의 contextId 와 다릅니다"; // §3.4.3
    throw badParams("message.contextId", why);
  }
  if (!canMove(task.status.state, WORKING)) {
    // 종료 상태 — 표에 나갈 곳이 없다(§3.1.1)
    throw a2aError("UnsupportedOperation", { taskId: task.id });
  }
  move(task, WORKING); // 지난 물음은 이 때 이력으로 내려간다
  store.append(task, msg);
  return task;
}
// endregion

// region: send
// 막는 호출 — 끝나거나 멈출 때까지 다 하고 Task 를 돌려준다.
function sendMessage(params: Params) {
  const config = (params.configuration ?? {}) as Params;
  const n = historyLength(config.historyLength);
  const task = begin(params);
  lodging(task); // 이벤트는 버린다 — 결과는 저장소의 Task 에
  return { task: view(task, n) };
}
// endregion

// region: get
// historyLength — 없으면 전부, 0 이상의 정수만 받는다.
function historyLength(raw: unknown): number | undefined {
  if (raw === undefined || raw === null) return undefined;
  if (!Number.isInteger(raw) || (raw as number) < 0) {
    throw badParams("historyLength", "0 이상의 정수여야 합니다");
  }
  return raw as number;
}

function getTask(params: Params) {
  const n = historyLength(params.historyLength);
  return view(find(params.id), n);
}
// endregion

// region: cancel
// 취소 — 이미 CANCELED 면 그대로 돌려준다(§3.3.1 멱등).
function cancelTask(params: Params) {
  const task = find(params.id);
  const state = task.status.state;
  if (state !== CANCELED) {
    if (!canMove(state, CANCELED)) {
      throw a2aError("TaskNotCancelable", { taskId: task.id });
    }
    move(task, CANCELED);
  }
  return view(task);
}
// endregion

// region: stream
// 스트림 — 첫 이벤트는 늘 Task 다(§3.1.2). 이어 말할 때도.
// 돌려주는 것은 StreamResponse 의 목록. 숙소 일은 기다릴 것이
// 없어 한 번에 다 나오고, 내보내기(SSE)는 http 쪽이 한다.
function sendStreamingMessage(params: Params): StreamResponse[] {
  const task = begin(params);
  const first = { task: view(task) }; // 지금 모습을 먼저 떠 둔다
  return [first, ...lodging(task)];
}
// endregion

// region: methods
// 메서드 이름(§9.4, PascalCase) → [처리 함수, 답이 SSE 스트림인가]
const METHODS: Record<string, [(p: Params) => unknown, boolean]> = {
  SendMessage: [sendMessage, false],
  SendStreamingMessage: [sendStreamingMessage, true],
  GetTask: [getTask, false],
  CancelTask: [cancelTask, false],
};
// endregion

// region: dispatch
type Id = string | number | null;
type Reply = [object, null] | [null, object[]];

// 본문 → [JSON-RPC 응답, null] 또는 [null, 스트림 응답들].
function dispatch(body: string, headers: IncomingHttpHeaders): Reply {
  let req;
  try {
    req = JSON.parse(body);
  } catch {
    return failure(null, new RpcError(-32700, "Invalid JSON payload"));
  }
  // 배치(배열)와 알림(id 없음)은 받지 않는다 — A2A 는 늘 답을 준다
  if (
    typeof req !== "object" ||
    req === null ||
    Array.isArray(req) ||
    req.jsonrpc !== "2.0" ||
    typeof req.method !== "string" ||
    !["string", "number"].includes(typeof req.id)
  ) {
    const why = "Request payload validation error";
    return failure(null, new RpcError(-32600, why));
  }
  try {
    const [result, streams] = call(req, headers);
    if (!streams) return [ok(req.id, result), null];
    return [null, (result as object[]).map((ev) => ok(req.id, ev))];
  } catch (e) {
    if (e instanceof RpcError) return failure(req.id, e);
    // 우리 코드가 깨졌다 — 전이 표 위반(버그)이나 이상한 입력값
    console.error(`[숙소] 내부 오류: ${e}`);
    return failure(req.id, new RpcError(-32603, "Internal error"));
  }
}
// endregion

// region: call
// 판·메서드·인자를 보고 처리 함수를 부른다 → [결과, 스트림인가].
function call(
  req: { method: string; params?: unknown },
  headers: IncomingHttpHeaders,
): [unknown, boolean] {
  checkVersion(headers); // 판이 메서드 이름의 뜻을 정한다
  // hasOwn — "toString" 같은 이름이 Object 의 것을 집지 않게
  const m = Object.hasOwn(METHODS, req.method) && METHODS[req.method];
  if (!m) throw new RpcError(-32601, "Method not found");
  const params = req.params;
  if (typeof params !== "object" || !params || Array.isArray(params)) {
    throw badParams("params", "객체여야 합니다");
  }
  return [m[0](params as Params), m[1]];
}

const ok = (id: Id, result: unknown) => ({
  jsonrpc: "2.0",
  id,
  result,
});
const failure = (id: Id, err: RpcError): Reply => [
  { jsonrpc: "2.0", id, error: err.body() },
  null,
];
// endregion

// region: http
// 경로 둘 — GET 카드, POST / (JSON-RPC). 나머지는 404.
const { values } = parseArgs({
  options: { port: { type: "string" }, url: { type: "string" } },
});
const port = Number(values.port);
const CARD = card(values.url ?? `http://127.0.0.1:${port}/`);

function reply(res: ServerResponse, obj: object) {
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify(obj));
}

const server = createServer(async (req, res) => {
  const where = `${req.method} ${req.url}`;
  if (where === "GET /.well-known/agent-card.json")
    return reply(res, CARD);
  if (where !== "POST /") return res.writeHead(404).end();
  // 조각 경계에서 한글이 깨지지 않게 문자열로 받는다
  req.setEncoding("utf8");
  let body = "";
  for await (const chunk of req) body += chunk;
  const [resp, events] = dispatch(body, req.headers);
  if (resp) return reply(res, resp);
  res.writeHead(200, { "Content-Type": "text/event-stream" });
  for (const ev of events) {
    res.write(`data: ${JSON.stringify(ev)}\n\n`); // data 줄 + 빈 줄
  }
  res.end(); // 응답을 끝내는 것이 곧 스트림의 끝(2부)
});
// endregion

// 스레드는 하나, dispatch 는 await 없이 한 번에 돈다 — 그 사이에
// 다른 요청이 끼어들 수 없으니 저장소에 자물쇠가 없어도 된다
server.listen(port, "127.0.0.1");
//@ norun

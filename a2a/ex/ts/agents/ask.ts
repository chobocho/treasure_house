// 총무팀의 명령줄 클라이언트 — 에이전트에게 말을 걸고 오가는 것을
// 찍는다.
//
//     node agents/ask.ts URL [--data JSON] [--token T] 첫말 [답1 답2 …]
//
// 작업이 INPUT_REQUIRED·AUTH_REQUIRED 에서 멈추면 남은 답을 같은
// taskId·contextId 로 차례로 보낸다(대본이 있는 대화). 카드가
// 스트리밍을 지원하면 스트림으로, 아니면 막는 호출로 받는다.
import { parseArgs } from "node:util";
import {
  Role,
  TaskState,
  type Message,
  type Part,
  type StreamResponse,
} from "@a2a-js/sdk";
import {
  ClientFactory,
  type Client,
  type RequestOptions,
} from "@a2a-js/sdk/client";
import { dataPart, textPart } from "./common.ts";

const PAUSED = [
  TaskState.TASK_STATE_INPUT_REQUIRED,
  TaskState.TASK_STATE_AUTH_REQUIRED,
];

// 키를 정렬한 파이썬 json.dumps 모양: ", " 와 ": " 로 띄운다.
function pyJson(v: unknown): string {
  if (Array.isArray(v)) return `[${v.map(pyJson).join(", ")}]`;
  if (v !== null && typeof v === "object") {
    const o = v as Record<string, unknown>;
    const kv = Object.keys(o)
      .sort()
      .map((k) => `${JSON.stringify(k)}: ${pyJson(o[k])}`);
    return `{${kv.join(", ")}}`;
  }
  return JSON.stringify(v);
}

// 짧으면 한 줄, 길면 들여 쓴 여러 줄(접힌 폰 화면 폭 때문).
// 길이는 글자(코드 포인트) 수로 잰다 — 파이썬 len 과 같게.
function dump(data: unknown): string {
  const one = pyJson(data);
  if ([...one].length <= 60) return one;
  return JSON.stringify(data, sortKeys, 1);
}

// JSON.stringify 의 replacer: 객체를 만날 때마다 키를 정렬해 넘긴다.
function sortKeys(_: string, v: unknown) {
  if (v === null || typeof v !== "object" || Array.isArray(v)) return v;
  const o = v as Record<string, unknown>;
  return Object.fromEntries(
    Object.keys(o)
      .sort()
      .map((k) => [k, o[k]]),
  );
}

// 파트 하나당 한 조각: 글은 그대로, 데이터는 JSON, 파일은 크기.
function showParts(parts: Part[]): string {
  const out: string[] = [];
  for (const p of parts) {
    const c = p.content;
    if (c?.$case === "text") out.push(c.value.replace(/\n+$/, ""));
    else if (c?.$case === "data") out.push(dump(c.value));
    else if (c?.$case === "raw") {
      out.push(`<${p.filename || "파일"} ${c.value.length}바이트>`);
    } else if (c?.$case === "url") out.push(`<${c.value}>`);
  }
  return out.join(" | ");
}

function stateName(state: TaskState | undefined): string {
  return TaskState[state ?? 0].replace(/^TASK_STATE_/, "");
}

type Seen = { taskId: string; contextId: string; state?: TaskState };

// StreamResponse 하나를 한 줄로. 돌려주는 값은 taskId·ctx·상태.
function show(ev: StreamResponse): Seen | undefined {
  const p = ev.payload;
  if (p?.$case === "message") {
    console.log(`message: ${showParts(p.value.parts)}`);
    return undefined;
  }
  if (p?.$case === "task") {
    const t = p.value;
    const msg = showParts(t.status?.message?.parts ?? []);
    const state = t.status?.state;
    console.log(`task ${stateName(state)} ${msg}`.trimEnd());
    for (const a of t.artifacts) {
      console.log(`  artifact ${a.name}: ${showParts(a.parts)}`);
    }
    return { taskId: t.id, contextId: t.contextId, state };
  }
  if (p?.$case === "statusUpdate") {
    const s = p.value;
    const msg = showParts(s.status?.message?.parts ?? []);
    const state = s.status?.state;
    console.log(`status ${stateName(state)} ${msg}`.trimEnd());
    return { taskId: s.taskId, contextId: s.contextId, state };
  }
  if (p?.$case === "artifactUpdate") {
    const a = p.value;
    let flags = a.append ? "+" : "";
    flags += a.lastChunk ? " (끝)" : "";
    const parts = showParts(a.artifact?.parts ?? []);
    console.log(`artifact ${a.artifact?.name}${flags}: ${parts}`);
    return { taskId: a.taskId, contextId: a.contextId };
  }
  return undefined;
}

// 스트림이면 사건을 하나씩, 막는 호출이면 결과 하나를 사건처럼 낸다.
async function* send(
  client: Client,
  message: Message,
  stream: boolean,
  options: RequestOptions,
): AsyncGenerator<StreamResponse> {
  const req = { tenant: "", message, configuration: undefined };
  const params = { ...req, metadata: undefined };
  if (stream) {
    yield* client.sendMessageStream(params, options);
    return;
  }
  const r = await client.sendMessage(params, options);
  yield "messageId" in r
    ? { payload: { $case: "message", value: r } }
    : { payload: { $case: "task", value: r } };
}

const { values: opt, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    data: { type: "string" }, // 첫 메시지에 붙일 DataPart(JSON)
    token: { type: "string" }, // Bearer 토큰
    "no-stream": { type: "boolean" },
  },
});
const [url, ...lines] = positionals; // 첫말과 이어질 답들
const auth = { Authorization: `Bearer ${opt.token}` };
const options = opt.token ? { serviceParameters: auth } : {};
const client = await new ClientFactory().createFromUrl(url!);
let parts = lines.length > 0 ? [textPart(lines.shift()!)] : [];
if (opt.data) parts.push(dataPart(JSON.parse(opt.data)));
let taskId = "";
let contextId = "";
for (;;) {
  const msg: Message = {
    messageId: `ask-${lines.length}`, // 대본 안에서 겹치지 않게
    ...{ taskId, contextId, role: Role.ROLE_USER, parts },
    ...{ metadata: undefined, extensions: [], referenceTaskIds: [] },
  };
  let last: TaskState | undefined;
  for await (const ev of send(
    client,
    msg,
    !opt["no-stream"],
    options,
  )) {
    const seen = show(ev);
    if (seen?.state !== undefined) ({ taskId, contextId } = seen);
    if (seen?.state !== undefined) last = seen.state;
  }
  if (last === undefined || !PAUSED.includes(last) || !lines.length) {
    break;
  }
  const reply = lines.shift()!;
  console.log(`> ${reply}`);
  parts = [textPart(reply)];
}

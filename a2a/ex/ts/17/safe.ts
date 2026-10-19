// 끊긴 SendMessage 를 다시 보내지 않고, 맥락으로 찾아 다시 붙는다.
//   node 17/safe.ts 카드주소
import {
  Role,
  TaskState,
  taskStateToJSON,
  type Message,
  type StreamResponse,
} from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const BUS = { headcount: 30, nights: 1, depart: "강남역" };
const CTX = "ctx-safe"; // 보내기 전에 맥락을 정해 둔다 — 찾을 열쇠

const name = (s: TaskState) =>
  taskStateToJSON(s).replace("TASK_STATE_", "");

function stateOf(ev: StreamResponse) {
  const p = ev.payload;
  if (p?.$case === "task") return name(p.value.status!.state);
  if (p?.$case === "statusUpdate") return name(p.value.status!.state);
  return p?.$case;
}

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const part = {
  ...{ filename: "", mediaType: "", metadata: undefined },
  content: { $case: "data" as const, value: BUS },
};
const message: Message = {
  ...{ messageId: "m-safe", taskId: "", contextId: CTX },
  ...{ role: Role.ROLE_USER, parts: [part], metadata: undefined },
  ...{ extensions: [], referenceTaskIds: [] },
};
// region: main
const signal = AbortSignal.timeout(1500);
const req = { tenant: "", message, configuration: undefined };
try {
  await client.sendMessage({ ...req, metadata: undefined }, { signal });
} catch {
  console.log("① 1.5초에 끊김 — 다시 보내지 않는다");
}
const ALL = {
  ...{ tenant: "", contextId: CTX, pageToken: "" },
  ...{ status: TaskState.TASK_STATE_UNSPECIFIED },
  statusTimestampAfter: undefined,
};
let page = await client.listTasks(ALL);
const task = page.tasks[0]!;
const n = page.tasks.length;
console.log(
  `② ListTasks(contextId) → ${n}건 ${name(task.status!.state)}`,
);
// region: sub
const seen: StreamResponse[] = [];
const sub = { tenant: "", id: task.id };
for await (const ev of client.resubscribeTask(sub)) seen.push(ev);
// endregion
const [first, last] = [stateOf(seen[0]!), stateOf(seen.at(-1)!)];
console.log(`③ SubscribeToTask → 처음 ${first} … 끝 ${last}`);
page = await client.listTasks(ALL);
const now = name(page.tasks[0]!.status!.state);
console.log(`④ ListTasks(contextId) → ${page.tasks.length}건 ${now}`);
// endregion
//@ norun

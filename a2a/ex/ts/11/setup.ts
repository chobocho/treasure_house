// 교통 에이전트에 푸시 설정을 두 번 단다 — 보내는 요청에 하나(inline),
// 돌려받은 작업에 CreateTaskPushNotificationConfig 로 하나. 그다음
// 중계기(relay.py)에 무엇이 왔는지 묻는다.
//   node 11/setup.ts 에이전트주소 웹훅주소 중계기주소
import {
  Role,
  taskStateToJSON,
  type Message,
  type Task,
  type TaskPushNotificationConfig,
} from "@a2a-js/sdk";
import { ClientFactory, type Client } from "@a2a-js/sdk/client";

const [AGENT, HOOK, RELAY] = process.argv.slice(2) as [
  string,
  string,
  string,
];
const BUS = { headcount: 30, nights: 1, depart: "강남역" };

// region: inline
async function send(client: Client) {
  const part = {
    ...{ filename: "", mediaType: "", metadata: undefined },
    content: { $case: "data" as const, value: BUS },
  };
  const message: Message = {
    ...{ messageId: "push-1", taskId: "", contextId: "" },
    ...{ role: Role.ROLE_USER, parts: [part], metadata: undefined },
    ...{ extensions: [], referenceTaskIds: [] },
  };
  // 작업 id 는 아직 없으니 taskId 는 비워 둔다(proto 주석)
  const push: TaskPushNotificationConfig = {
    ...{ tenant: "", id: "", taskId: "", url: HOOK },
    ...{ token: "tok-inline", authentication: undefined },
  };
  const configuration = {
    ...{ acceptedOutputModes: [], taskPushNotificationConfig: push },
    ...{ historyLength: undefined, returnImmediately: true },
  };
  const res = await client.sendMessage({
    ...{ tenant: "", message, configuration, metadata: undefined },
  });
  return res as Task;
}
// endregion

// region: create
async function create(client: Client, taskId: string) {
  return client.createTaskPushNotificationConfig({
    ...{ tenant: "", id: "hook-2", taskId, url: HOOK },
    ...{ token: "tok-create", authentication: undefined },
  });
}
// endregion

type Rec = { token: string; what: string };

// 중계기에서 이 작업의 끝 알림을 설정마다 하나씩 기다린다
async function arrivals(taskId: string): Promise<Rec[]> {
  const res = await fetch(`${RELAY}wait?task=${taskId}&n=2`);
  return (await res.json()) as Rec[];
}

const client = await new ClientFactory().createFromUrl(AGENT);
const task = await send(client);
const state = taskStateToJSON(task.status!.state).slice(11);
console.log("SendMessage →", state, task.id);
const got = await create(client, task.id);
console.log("Create →", `id=${got.id} taskId=${got.taskId}`);
console.log(`  url=${got.url} token=${got.token}`);
// 두 설정으로 가는 알림은 서로 차례가 섞일 수 있어 토큰별로 모은다
const recs = await arrivals(task.id);
recs.sort((a, b) => a.token.localeCompare(b.token));
for (const r of recs) console.log(`  ${r.token.padEnd(10)} ${r.what}`);
//@ norun

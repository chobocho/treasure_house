// 푸시 설정 CRUD — 설정 둘(요청에 실은 hook-1, Create 한 hook-2)을 단
// 작업에 Get·List·Delete 를 차례로 한다. 지운 설정으로는 알림이 더 가지
// 않는지 중계기(relay.py)에서 본다. 마지막은 없는 설정을 Get.
//   node 11/crud.ts 에이전트 웹훅 중계기
import { Role, type Message, type Task } from "@a2a-js/sdk";
import { ClientFactory, type Client } from "@a2a-js/sdk/client";

const [AGENT, HOOK, RELAY] = process.argv.slice(2) as [
  string,
  string,
  string,
];
const BUS = { headcount: 30, nights: 1, depart: "강남역" };

function cfg(id: string, token: string, taskId = "") {
  return {
    tenant: "",
    id,
    taskId,
    url: HOOK,
    token,
    authentication: undefined,
  };
}

async function setup(client: Client) {
  const part = {
    ...{ filename: "", mediaType: "", metadata: undefined },
    content: { $case: "data" as const, value: BUS },
  };
  const message: Message = {
    ...{ messageId: "crud-1", taskId: "", contextId: "" },
    ...{ role: Role.ROLE_USER, parts: [part], metadata: undefined },
    ...{ extensions: [], referenceTaskIds: [] },
  };
  const configuration = {
    ...{ acceptedOutputModes: [], historyLength: undefined },
    ...{ returnImmediately: true },
    taskPushNotificationConfig: cfg("hook-1", "tok-1"),
  };
  const task = (await client.sendMessage({
    ...{ tenant: "", message, configuration, metadata: undefined },
  })) as Task;
  await client.createTaskPushNotificationConfig(
    cfg("hook-2", "tok-2", task.id),
  );
  return task.id;
}

// region: list
async function show(client: Client, taskId: string) {
  const res = await client.listTaskPushNotificationConfig({
    ...{ tenant: "", taskId, pageSize: 0, pageToken: "" },
  });
  // 서버가 돌려주는 차례는 정해져 있지 않다 — 토큰으로 줄 세운다
  const got = res.configs.map((c) => `${c.id}:${c.token}`).sort();
  console.log(`List → ${got.length}개`, got);
}
// endregion

// region: crud
async function crud(client: Client, taskId: string) {
  const get = { tenant: "", taskId, id: "hook-2" };
  const c = await client.getTaskPushNotificationConfig(get);
  console.log(`Get hook-2 → url=${c.url} token=${c.token}`);
  await show(client, taskId);
  for (const n of [1, 2]) {
    // 두 번 지운다 — 명세는 멱등(idempotent)
    try {
      await client.deleteTaskPushNotificationConfig({
        ...get,
        id: "hook-1",
      });
      console.log(`Delete hook-1 (${n}) → 오류 없음`);
    } catch (e) {
      console.log(`Delete hook-1 (${n}) → ${(e as Error).message}`);
    }
  }
  await show(client, taskId);
  try {
    await client.getTaskPushNotificationConfig({
      ...get,
      id: "hook-1",
    });
  } catch (e) {
    const err = e as Error;
    console.log(`Get hook-1 → ${err.name}: ${err.message}`);
  }
}
// endregion

// tok-2 의 끝 알림을 기다린 뒤, 토큰마다 받은 것을 센다
async function arrivals(taskId: string) {
  const res = await fetch(`${RELAY}wait?task=${taskId}&token=tok-2`);
  const seen = new Map<string, string[]>();
  for (const r of (await res.json()) as {
    token: string;
    what: string;
  }[])
    seen.set(r.token, [...(seen.get(r.token) ?? []), r.what]);
  for (const [token, whats] of [...seen].sort()) {
    console.log(`  ${token} ${whats.length}건 — 첫 ${whats[0]}`);
  }
}

const client = await new ClientFactory().createFromUrl(AGENT);
const taskId = await setup(client);
console.log("작업", taskId);
await crud(client, taskId);
await arrivals(taskId);
//@ norun

// ListTasks — 작업 셋(맥락 ctx-a 에 30명·0명, ctx-b 에 70명)을 만든 뒤
// 필터·페이지·이력 길이를 바꿔 가며 목록을 받는다.
//   node 11/listing.ts 에이전트
import {
  Role,
  TaskState,
  taskStateToJSON,
  type ListTasksRequest,
  type Message,
  type Task,
} from "@a2a-js/sdk";
import { ClientFactory, type Client } from "@a2a-js/sdk/client";

const JOBS: [string, string, object][] = [
  ["list-a", "ctx-a", { headcount: 30, nights: 1 }],
  ["list-b", "ctx-a", { headcount: 0, nights: 1 }],
  ["list-c", "ctx-b", { headcount: 70, nights: 2 }],
];

async function make(client: Client) {
  for (const [messageId, contextId, data] of JOBS) {
    const part = {
      ...{ filename: "", mediaType: "", metadata: undefined },
      content: { $case: "data" as const, value: data },
    };
    const message: Message = {
      ...{ messageId, taskId: "", contextId, role: Role.ROLE_USER },
      ...{ parts: [part], metadata: undefined },
      ...{ extensions: [], referenceTaskIds: [] },
    };
    // 막는 호출 — 끝나야 다음으로
    await client.sendMessage({
      ...{ tenant: "", message, configuration: undefined },
      metadata: undefined,
    });
  }
}

function row(t: Task) {
  const first = t.history[0]?.messageId ?? "-";
  const state = taskStateToJSON(t.status!.state).slice(11);
  return (
    `${t.contextId} ${state.padEnd(9)} ${first.padEnd(6)}` +
    ` 이력 ${t.history.length} 아티팩트 ${t.artifacts.length}`
  );
}

// region: list
const ALL: ListTasksRequest = {
  ...{ tenant: "", contextId: "", pageToken: "" },
  ...{ status: TaskState.TASK_STATE_UNSPECIFIED },
  statusTimestampAfter: undefined,
};

async function show(c: Client, title: string, more = {}) {
  const res = await c.listTasks({ ...ALL, ...more });
  const next = res.nextPageToken ? "있음" : '""';
  const page = `total ${res.totalSize} page ${res.pageSize}`;
  console.log(`${title}: ${page} next ${next}`);
  for (const t of res.tasks) console.log("  ", row(t));
  return res.nextPageToken;
}

async function lists(c: Client) {
  await show(c, "전부");
  await show(c, "contextId=ctx-a", { contextId: "ctx-a" });
  const status = TaskState.TASK_STATE_COMPLETED;
  await show(c, "status=COMPLETED", { status });
  // 한 장에 하나씩 — 토큰이 빌 때까지
  let pageToken = "";
  for (let n = 1; ; n++) {
    const more = { pageSize: 1, pageToken };
    pageToken = await show(c, `pageSize=1 (${n})`, more);
    if (!pageToken) break;
  }
  await show(c, "historyLength=0 + 아티팩트", {
    ...{ historyLength: 0, includeArtifacts: true },
  });
}
// endregion

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
await make(client);
await lists(client);
//@ norun

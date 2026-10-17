// 떠 있는 숙소 에이전트를 골든 벡터로 검사한다 — 업무 규칙
// 시험(workshop/domain.test.ts)과 같은 기대값을, 이번에는 A2A 를
// 거쳐서. 사례마다 새 작업 하나(막는 호출).
//   node 08/golden_lodging.ts URL
import { readFileSync } from "node:fs";
import { isDeepStrictEqual } from "node:util";
import { Message, TaskState, type Task } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";
import { textOf } from "../agents/common.ts";

type Case = { name: string; input: object; expected: object };
const GOLDEN = new URL(
  "../../fixtures/golden/domain.json",
  import.meta.url,
);
const cases: Case[] = JSON.parse(readFileSync(GOLDEN, "utf8"))[
  "chooseLodging"
];

// region: check
// 완료면 아티팩트의 DataPart, 거절이면 상태 메시지의 까닭
function answerOf(task: Task): object {
  if (task.status?.state === TaskState.TASK_STATE_COMPLETED) {
    const c = task.artifacts[0]?.parts[0]?.content;
    return c?.$case === "data" ? c.value : {};
  }
  return { ok: false, reason: textOf(task.status?.message) };
}

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
let passed = 0;
for (const [i, c] of cases.entries()) {
  const message = Message.fromJSON({
    ...{ messageId: `g-${i + 1}`, role: "ROLE_USER" },
    parts: [{ data: c.input }],
  });
  const req = { tenant: "", message, configuration: undefined };
  const params = { ...req, metadata: undefined };
  const task = (await client.sendMessage(params)) as Task;
  // 수는 정수 그대로 와서(2장) 기대값과 바로 견준다
  const ok = isDeepStrictEqual(answerOf(task), c.expected);
  passed += Number(ok);
  const state = TaskState[task.status!.state].slice(11);
  console.log(`${ok ? "O" : "X"} ${c.name.padEnd(28)} ${state}`);
}
console.log(`${passed}/${cases.length} 골든과 같음`);
// endregion
//@ norun

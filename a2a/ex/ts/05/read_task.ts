// 끝난 숙소 Task 를 받아 필드를 하나씩 읽는다(TS SDK 의 모양으로).
//   node 05/read_task.ts 카드주소
import {
  Role,
  roleToJSON,
  taskStateToJSON,
  type Message,
  type Task,
} from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const REQUEST = { date: "2026-10-30", nights: 1, headcount: 30 };

// region: read
// 빠진 필드는 undefined — 와이어에 없던 것은 그대로 비어 있다
const has = (v: unknown) => (v === undefined ? "없음" : "있음");

function read(t: Task) {
  console.log("id        :", t.id);
  console.log("contextId :", t.contextId);
  const st = t.status!;
  console.log("state     :", taskStateToJSON(st.state));
  console.log("timestamp :", typeof st.timestamp, has(st.timestamp));
  console.log("message   :", has(st.message));
  for (const a of t.artifacts) {
    const kinds = a.parts.map((p) => p.content?.$case);
    console.log("artifact  :", a.name, kinds);
  }
  for (const m of t.history)
    console.log("history   :", roleToJSON(m.role), m.messageId);
  console.log("metadata  :", has(t.metadata));
}
// endregion

const message: Message = {
  ...{ messageId: "read-ts", taskId: "", contextId: "" },
  ...{ role: Role.ROLE_USER, metadata: undefined, extensions: [] },
  parts: [
    {
      ...{ filename: "", mediaType: "", metadata: undefined },
      content: { $case: "data", value: REQUEST },
    },
  ],
  referenceTaskIds: [],
};
const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const res = await client.sendMessage({
  ...{ tenant: "", message },
  ...{ configuration: undefined, metadata: undefined },
});
read(res as Task); // 숙소 에이전트는 Task 로 답한다
//@ norun

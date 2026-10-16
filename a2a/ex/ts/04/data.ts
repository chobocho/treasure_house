// 숙소 요청 {date, nights, headcount} 를 DataPart 로 보낸다.
// 답이 Message 면 글을, Task 면 상태와 견적의 수 셋을 찍는다.
//   node 04/data.ts 카드주소
import {
  Role,
  taskStateToJSON,
  type Message,
  type Task,
} from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

// region: send
const REQUEST = { date: "2026-10-30", nights: 1, headcount: 30 };

function lodgingMessage(): Message {
  // data 의 value 는 any — 객체가 그대로 들어가 JSON.stringify 된다
  const part = {
    ...{ filename: "", mediaType: "", metadata: undefined },
    content: { $case: "data" as const, value: REQUEST },
  };
  return {
    ...{ messageId: "data-ts", taskId: "", contextId: "" },
    ...{ role: Role.ROLE_USER, parts: [part] },
    ...{ metadata: undefined, extensions: [], referenceTaskIds: [] },
  };
}
// endregion

// region: read
function showQuote(task: Task) {
  // enum 은 수(3)로 들고 있다 — 이름은 taskStateToJSON 으로
  console.log("task", taskStateToJSON(task.status!.state));
  const c = task.artifacts[0]?.parts[0]?.content;
  if (c?.$case !== "data") return;
  const quote = c.value as Record<string, unknown>;
  for (const k of ["headcount", "rooms", "total"]) {
    const v = quote[k];
    console.log(`  ${k}: ${typeof v} ${JSON.stringify(v)}`);
  }
}
// endregion

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const res = await client.sendMessage({
  ...{ tenant: "", message: lodgingMessage() },
  ...{ configuration: undefined, metadata: undefined },
});
// region: dispatch
// sendMessage 는 껍질을 벗긴 Message | Task — 필드로 가린다
if ("status" in res) showQuote(res);
else
  for (const p of res.parts)
    if (p.content?.$case === "text") console.log(p.content.value);
// endregion
//@ norun

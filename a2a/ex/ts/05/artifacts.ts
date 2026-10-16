// 식사 에이전트에 식단을 맡기고(막는 호출), 끝난 Task 의 아티팩트를
// 하나씩 읽는다 — id·이름·설명, 파트의 종류, metadata·extensions.
//   node 05/artifacts.ts 카드주소
import { Role, type Message, type Part, type Task } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";
import { dataPart } from "../agents/common.ts";

const MEALS = { nights: 1, headcount: 30, vegetarians: 2 };

// region: read
function part(p: Part): string {
  const c = p.content;
  if (c?.$case === "text") return `text ${c.value.length}자`;
  if (c?.$case === "raw")
    return `raw ${p.filename} ${p.mediaType} ${c.value.length}바이트`;
  if (c?.$case === "data") {
    const keys = Object.keys(c.value as object).sort();
    return `data ${JSON.stringify(keys.slice(0, 3))}…`;
  }
  return String(c?.$case);
}

function read(task: Task) {
  console.log("아티팩트", task.artifacts.length, "개");
  for (const a of task.artifacts) {
    const desc = JSON.stringify(a.description);
    console.log(`- ${a.artifactId} '${a.name}' 설명:${desc}`);
    for (const p of a.parts) console.log("    ", part(p));
    const meta = a.metadata === undefined ? "없음" : "있음";
    const ext = JSON.stringify(a.extensions);
    console.log(`    metadata ${meta}, extensions ${ext}`);
  }
}
// endregion

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const message: Message = {
  ...{ messageId: "meals-1", taskId: "", contextId: "" },
  ...{ role: Role.ROLE_USER, metadata: undefined, extensions: [] },
  ...{ parts: [dataPart(MEALS)], referenceTaskIds: [] },
};
const res = await client.sendMessage({
  ...{ tenant: "", message },
  ...{ configuration: undefined, metadata: undefined },
});
read(res as Task); // 식사 에이전트는 Task 로 답한다
//@ norun

// 타입이 보통 객체라서 생기는 일 — 대입, 참조, 사본.
//   node 08/types_fields.ts
import { Message, Part, Task, TaskState } from "@a2a-js/sdk";

const task = Task.fromJSON({ id: "t-1", contextId: "c-1" });
const user = (text: string) =>
  Message.fromJSON({
    messageId: "m-1",
    role: "ROLE_USER",
    parts: [{ text }],
  });
const textOf = (m: Message) =>
  m.parts[0]?.content?.$case === "text" ? m.parts[0].content.value : "";

// region: assign
// 하위 메시지 필드에도 = 로 넣는다 — 통째로 바꾸면 된다
task.status = {
  state: TaskState.TASK_STATE_WORKING,
  message: undefined,
  timestamp: undefined,
};
console.log("상태:", TaskState[task.status.state]);
// endregion

// region: copy
const msg = user("30명");
task.history.push(msg); // 넣은 것은 그 객체 자체
msg.parts[0] = Part.fromJSON({ text: "40명" });
console.log("넣은 뒤 원본을 고치면 이력도:", textOf(task.history[0]!));
const shallow = { ...task }; // 펼치기는 겉만 복사한다
shallow.history[0] = user("50명");
console.log("펼친 사본을 고치면 원본도:", textOf(task.history[0]!));
const deep = structuredClone(task); // 깊은 사본
deep.history[0] = user("60명");
console.log(
  "structuredClone 을 고치면 원본은:",
  textOf(task.history[0]!),
);
// endregion

// region: buffer
// 깊은 사본은 Buffer 를 Uint8Array 로 바꿔 놓는다
const raw = Part.fromJSON({ raw: "7JWI64WV", mediaType: "text/plain" });
const copy = structuredClone(raw);
function show(label: string, p: Part) {
  const v = p.content?.$case === "raw" ? p.content.value : undefined;
  const is = Buffer.isBuffer(v);
  console.log(
    `${label}: ${v?.constructor.name}, Buffer.isBuffer ${is}`,
  );
}
show("원본", raw);
show("사본", copy);
console.log("사본의 toString():", String(copy.content?.value));
// endregion

// "없음" 을 묻는 법, 그리고 fromJSON 의 너그러움.
//   node 08/types_presence.ts
import { GetTaskRequest, Message, Part, Role, Task } from "@a2a-js/sdk";

// region: presence
const m = Message.fromJSON({ messageId: "m-1", role: "ROLE_USER" });
console.log("contextId:", JSON.stringify(m.contextId));
console.log("  ?? 로 기본값:", JSON.stringify(m.contextId ?? "없음"));
console.log("  || 로 기본값:", JSON.stringify(m.contextId || "없음"));
console.log("metadata:", m.metadata, " parts:", m.parts);
const t = Task.fromJSON({ id: "t-1" });
console.log("Task.status:", t.status); // 하위 메시지는 undefined
for (const json of [{ id: "t-1" }, { id: "t-1", historyLength: 0 }]) {
  const n = GetTaskRequest.fromJSON(json).historyLength;
  console.log(`historyLength(${JSON.stringify(json)}):`, n);
}
// endregion

// region: oneof
// 내용 키가 둘이면 — 키의 차례와 상관없이 text 가 이긴다
const two = Part.fromJSON({ url: "https://x.example/a", text: "글" });
console.log("두 내용:", JSON.stringify(two.content));
// 내용을 바꾸려면 content 를 통째로 갈아 끼운다
two.content = { $case: "url", value: "https://x.example/a" };
console.log("갈아 끼운 뒤:", JSON.stringify(Part.toJSON(two)));
// endregion

// region: enum
for (const role of ["ROLE_USER", "user", 1, 7]) {
  const got = Message.fromJSON({ messageId: "m", role }).role;
  console.log(`role ${JSON.stringify(role)} → ${got} ${Role[got]}`);
}
const snake = Message.fromJSON({ message_id: "m-9", task_id: "t-9" });
console.log("snake_case 키:", snake.messageId, snake.taskId);
const extra = Message.fromJSON({ messageId: "m", createdAt: "어제" });
console.log("모르는 키:", "createdAt" in extra);
// endregion

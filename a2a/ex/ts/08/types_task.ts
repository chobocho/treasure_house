// Task 를 짓고(에이전트 쪽), 받은 JSON 에서 읽는다(클라이언트 쪽).
//   node 08/types_task.ts
import {
  Message,
  StreamResponse,
  Task,
  TaskState,
  type Part,
} from "@a2a-js/sdk";

// region: make
// TS SDK 에는 new_task_from_user_message 같은 도우미가 없다
function newTask(
  msg: Message,
  taskId: string,
  contextId: string,
): Task {
  return {
    id: taskId,
    contextId,
    status: {
      state: TaskState.TASK_STATE_SUBMITTED,
      message: undefined,
      timestamp: undefined,
    },
    artifacts: [],
    history: [msg],
    metadata: undefined,
  };
}
// endregion

const msg = Message.fromJSON({
  messageId: "m-1",
  role: "ROLE_USER",
  parts: [{ text: "30명" }],
});
const task = newTask(msg, "t-1", "c-1");
console.log("새 Task:", JSON.stringify(Task.toJSON(task)));

// region: read
const body = `{"id":"t-1","contextId":"c-1",
  "status":{"state":"TASK_STATE_COMPLETED"},
  "createdAt":"2026-10-17T00:00:00Z",
  "artifacts":[{"artifactId":"a-1",
    "parts":[{"raw":"7JWI64WV","mediaType":"text/plain"}]}]}`;
const got = Task.fromJSON(JSON.parse(body)); // 모르는 키는 버린다
console.log("상태:", TaskState[got.status!.state]);
console.log("createdAt 이 남았나:", "createdAt" in got);
const p: Part | undefined = got.artifacts[0]?.parts[0];
if (p?.content?.$case === "raw") {
  console.log("raw:", p.content.value.toString("utf8"), p.mediaType);
}
// endregion

// region: stream
// 스트림의 한 칸은 payload 에 $case 를 단 꾸러미다
const ev: StreamResponse = { payload: { $case: "task", value: got } };
console.log(
  "StreamResponse 와이어:",
  Object.keys(StreamResponse.toJSON(ev) as object),
);
// endregion

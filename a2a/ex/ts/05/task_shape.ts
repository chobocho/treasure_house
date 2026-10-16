// SDK 의 Task 타입에는 어떤 필드가 있는가 — 빈 JSON 을 읽혀 본다.
//   node 05/task_shape.ts
import { Task, TaskStatus } from "@a2a-js/sdk";

// region: shape
// 타입은 실행 때 사라진다. 대신 fromJSON 이 모든 필드를 기본값으로
// 채운 객체를 만들어 주므로, 그 키가 곧 필드 목록이다.
function fields(name: string, obj: object) {
  console.log(name);
  Object.entries(obj).forEach(([k, v], i) => {
    const shown = v === undefined ? "undefined" : JSON.stringify(v);
    console.log(`  ${i + 1}. ${k}: ${shown}`);
  });
}

fields("Task", Task.fromJSON({}));
fields("TaskStatus", TaskStatus.fromJSON({}));
// endregion

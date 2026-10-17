// "@a2a-js/sdk" 가 내보내는 이름을 종류별로 나누고, enum 을 편다.
//   node 08/types_list.ts
import * as sdk from "@a2a-js/sdk";
import {
  TaskState,
  taskStateFromJSON,
  taskStateToJSON,
} from "@a2a-js/sdk";

// 72칸에서 접어 찍는다
function wrap(head: string, words: string[]) {
  let line = head;
  for (const w of words) {
    if (line.length + w.length >= 72) {
      console.log(line);
      line = "   ";
    }
    line += " " + w;
  }
  console.log(line);
}

// region: kinds
const groups: Record<string, string[]> = {};
for (const [name, v] of Object.entries(sdk)) {
  const kind =
    typeof v === "function"
      ? "함수"
      : typeof v === "string"
        ? "문자열 상수"
        : "fromJSON" in v
          ? "fromJSON·toJSON 객체"
          : "TASK_STATE_WORKING" in v || "ROLE_USER" in v
            ? "enum"
            : "그 밖의 객체";
  (groups[kind] ??= []).push(name);
}
console.log(`이름 ${Object.keys(sdk).length}개`);
for (const [kind, names] of Object.entries(groups)) {
  // 많은 무리는 앞의 몇 개만
  const shown = names.length > 12 ? [...names.slice(0, 8), "…"] : names;
  wrap(`  ${kind} ${names.length}:`, shown);
}
console.log("Message 의 손잡이:", Object.keys(sdk.Message).join(" "));
// endregion

// region: enums
// SDK 의 enum 은 TS enum — 이름 → 수, 수 → 이름이 한 객체에 있다
console.log(
  "TaskState.TASK_STATE_COMPLETED =",
  TaskState.TASK_STATE_COMPLETED,
);
console.log("TaskState[3] =", TaskState[3]);
console.log("키의 수:", Object.keys(TaskState).length);
console.log("taskStateToJSON(3) =", taskStateToJSON(3));
for (const v of ["TASK_STATE_COMPLETED", 3, "completed", 42]) {
  console.log(
    `taskStateFromJSON(${JSON.stringify(v)}) =`,
    taskStateFromJSON(v),
  );
}
const odd = 42 as TaskState; // 타입 검사를 일부러 비켜 간다
console.log("taskStateToJSON(42) =", taskStateToJSON(odd));
// endregion

// InMemoryTaskStore 의 성질 — 테넌트·소유자별 분리, 그리고 사본.
//   node 08/store.ts
import { Task, TaskState } from "@a2a-js/sdk";
import {
  InMemoryTaskStore,
  ServerCallContext,
  type User,
} from "@a2a-js/sdk/server";

// 로그인한 직원 — 인증은 12부, 여기서는 이름만 단다
const staff = (name: string): User => ({
  isAuthenticated: true,
  userName: name,
});
const kim = new ServerCallContext({ user: staff("kim") });
const lee = new ServerCallContext({ user: staff("lee") });
const anon = new ServerCallContext(); // 익명 — user 가 없다
const unknown = new ServerCallContext({ user: staff("unknown") });
const kimB = new ServerCallContext({ user: staff("kim"), tenant: "b" });

// region: owner
const store = new InMemoryTaskStore();
await store.save(Task.fromJSON({ id: "t-1", contextId: "c-1" }), kim);
await store.save(Task.fromJSON({ id: "t-2", contextId: "c-2" }), anon);
const callers = { kim, lee, 익명: anon, unknown, "kim@b": kimB };
for (const [who, call] of Object.entries(callers)) {
  const found = [];
  for (const id of ["t-1", "t-2"]) {
    if (await store.load(id, call)) found.push(id);
  }
  const pad = who.padEnd(/[가-힣]/.test(who) ? 5 : 7); // 한글은 두 칸
  console.log(`${pad} 이 찾는 작업: [${found.join(", ")}]`);
}
// endregion

// region: copy
const got = (await store.load("t-2", anon))!;
got.status = {
  state: TaskState.TASK_STATE_COMPLETED,
  ...{ message: undefined, timestamp: undefined },
};
const again = (await store.load("t-2", anon))!;
console.log("save 없이 고친 뒤 다시 꺼낸 상태:", again.status);
console.log(
  "메서드:",
  Object.getOwnPropertyNames(InMemoryTaskStore.prototype).join(" "),
);
// endregion

// region: raw
const t3 = Task.fromJSON({
  ...{ id: "t-3", contextId: "c-3" },
  artifacts: [
    { artifactId: "a-1", parts: [{ raw: "7JWI64WV" }] }, // "안녕"
  ],
});
await store.save(t3, anon);
const back = (await store.load("t-3", anon))!.artifacts[0]!.parts[0]!;
const v = back.content?.$case === "raw" ? back.content.value : null;
console.log("꺼낸 raw:", v?.constructor.name, "—", v?.toString());
console.log("Buffer.from 으로:", Buffer.from(v!).toString("utf8"));
// endregion

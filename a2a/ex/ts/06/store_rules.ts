// 맨손 저장소의 전이 표 시험 — 작업 하나를 만들어 이리저리 옮겨 본다.
import {
  CANCELED,
  COMPLETED,
  IllegalMove,
  INPUT_REQUIRED,
  move,
  Store,
  SUBMITTED,
  WORKING,
  type Part,
} from "./bare_store.ts";

const store = new Store();
const task = store.create({
  messageId: "m1",
  role: "ROLE_USER",
  parts: [{ text: "2026-10-30 1박 숙소" }],
});

const short = (state: string) => state.replace(/^TASK_STATE_/, "");

function show() {
  const roles = task.history.map((m) => m.role.replace(/^ROLE_/, ""));
  const state = short(task.status.state);
  console.log(`   지금 ${state}, 이력 ${roles.join(" ")}`);
}

// region: try
function attempt(state: string, parts?: Part[]) {
  try {
    move(task, state, parts);
  } catch (e) {
    if (!(e instanceof IllegalMove)) throw e;
    console.log(`${short(state).padStart(14)} 거부 — ${e.message}`);
    return;
  }
  console.log(`${short(state).padStart(14)} 옮김`);
  show();
}

show();
attempt(INPUT_REQUIRED, [{ text: "인원은 몇 명입니까?" }]);
attempt(COMPLETED); // 답을 듣기 전에 끝낼 수는 없다
attempt(WORKING); // 답이 왔다 — 물음은 이력으로
store.append(task, { messageId: "m2", role: "ROLE_USER", parts: [] });
show();
attempt(SUBMITTED); // 뒤로 가지 않는다
attempt(COMPLETED);
attempt(WORKING); // 종료 뒤에는 나갈 곳이 없다
attempt(CANCELED);
// endregion

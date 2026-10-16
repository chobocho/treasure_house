// 배차 하나를 끝까지 맡긴 뒤, 같은 작업을 historyLength 만 바꿔
// 여러 번 GetTask 한다. 이력이 몇 개, 어떤 것이 오는지 찍는다.
//   node 05/history.ts 카드주소
import { Role, type Message, type Task } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";
import { dataPart, textOf } from "../agents/common.ts";

const BUS = { headcount: 30, nights: 1, depart: "강남역" };

function line(task: Task) {
  const said = task.history.map((m) => textOf(m) || "(데이터)");
  return `${said.length}개 ${said.join(" / ")}`.trimEnd();
}

// region: history
const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const message: Message = {
  ...{ messageId: "bus-h", taskId: "", contextId: "" },
  ...{ role: Role.ROLE_USER, metadata: undefined, extensions: [] },
  ...{ parts: [dataPart(BUS)], referenceTaskIds: [] },
};
const sent = (await client.sendMessage({
  ...{ tenant: "", message },
  ...{ configuration: undefined, metadata: undefined },
})) as Task; // 막는 호출 — COMPLETED 를 받는다
const id = sent.id;
console.log("없음 →", line(await client.getTask({ tenant: "", id })));
for (const n of [0, 1, 2, 10, -1]) {
  // historyLength 는 선택 필드 — 빼면 "없음", 0 이면 "0 을 줬다"
  try {
    const task = await client.getTask({
      tenant: "",
      id,
      historyLength: n,
    });
    console.log(`${String(n).padStart(4)} →`, line(task));
  } catch (e) {
    console.log(
      `${String(n).padStart(4)} → 오류`,
      (e as Error).message,
    );
  }
}
// endregion
//@ norun

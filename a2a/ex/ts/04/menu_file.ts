// 식사 에이전트에 막는 호출로 식단을 묻고, 아티팩트의 파일 파트를
// 꺼낸다. acceptedOutputModes 에는 "text/markdown 만 받겠다" 고 적는다.
//   node 04/menu_file.ts 카드주소
import { Role, type Task } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const MEALS = { nights: 1, headcount: 30, vegetarians: 2 };

// region: file
function show(task: Task) {
  for (const a of task.artifacts) {
    const kinds = a.parts.map((p) => p.content?.$case);
    console.log(`${a.name}: ${kinds.join(" ")}`);
    for (const p of a.parts) {
      if (p.content?.$case !== "raw") continue;
      // value 는 Buffer — base64 는 SDK 가 이미 풀었다
      const n = p.content.value.length;
      console.log(`  ${p.filename} ${p.mediaType} ${n}바이트`);
      process.stdout.write(p.content.value.toString("utf-8"));
    }
  }
}
// endregion

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const part = {
  ...{ filename: "", mediaType: "", metadata: undefined },
  content: { $case: "data" as const, value: MEALS },
};
const res = await client.sendMessage({
  tenant: "",
  message: {
    ...{ messageId: "menu-ts", taskId: "", contextId: "" },
    ...{ role: Role.ROLE_USER, parts: [part] },
    ...{ metadata: undefined, extensions: [], referenceTaskIds: [] },
  },
  // region: modes
  configuration: {
    acceptedOutputModes: ["text/markdown"],
    ...{ taskPushNotificationConfig: undefined },
    ...{ historyLength: undefined, returnImmediately: false },
  },
  // endregion
  metadata: undefined,
});
if ("status" in res) show(res);
//@ norun

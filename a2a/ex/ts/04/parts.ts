// 파트 네 가지(text·raw·url·data)를 한 메시지에 담아 보낸다.
//   node 04/parts.ts 카드주소
import { Role, type Part } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const MENU = Buffer.from("# 식단\n- 숯불 바비큐\n"); // UTF-8 바이트

// region: parts
// ts-proto 의 Part: oneof 는 content: {$case, value} 하나에 담고,
// 나머지 필드는 빈 값이라도 다 적어야 타입이 맞는다
const none = { filename: "", mediaType: "", metadata: undefined };
const fourParts: Part[] = [
  {
    ...none,
    content: { $case: "text", value: "워크숍 자료 넷을 보냅니다" },
  },
  {
    ...{ ...none, filename: "menu.md", mediaType: "text/markdown" },
    content: { $case: "raw", value: MENU },
  },
  {
    ...{ ...none, filename: "map.png", mediaType: "image/png" },
    content: {
      $case: "url",
      value: "https://treasure-house.example/map.png",
    },
  },
  {
    ...none,
    content: { $case: "data", value: ["숙소", "식사", "교통"] },
  },
];
// endregion

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const message = {
  ...{ messageId: "parts-ts", taskId: "", contextId: "" },
  ...{ role: Role.ROLE_USER, parts: fourParts },
  ...{ metadata: undefined, extensions: [], referenceTaskIds: [] },
};
const res = await client.sendMessage({
  ...{ tenant: "", message, configuration: undefined },
  metadata: undefined,
});
// sendMessage 는 껍질을 벗긴 Message | Task 를 준다 — 필드로 가린다
const kind = "status" in res ? "task" : "message";
console.log("답:", kind);
if (!("status" in res)) {
  for (const p of res.parts)
    if (p.content?.$case === "text") console.log(p.content.value);
}
//@ norun

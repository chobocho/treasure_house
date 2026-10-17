// Message 를 두 길로 만들고, 와이어 모양으로 바꿔 본다.
//   node 08/types_build.ts
import { isDeepStrictEqual } from "node:util";
import { Message, Role } from "@a2a-js/sdk";

// region: build
// ① 객체 글자(literal) — 타입이 필드 여덟을 모두 요구한다
const a: Message = {
  messageId: "m-1",
  contextId: "",
  taskId: "",
  role: Role.ROLE_USER,
  parts: [
    {
      content: { $case: "text", value: "숙소 부탁합니다" },
      mediaType: "",
      filename: "",
      metadata: undefined,
    },
  ],
  metadata: undefined,
  extensions: [],
  referenceTaskIds: [],
};
// ② 와이어 모양 JSON 을 fromJSON 에 — 빠진 필드는 기본값으로
const b = Message.fromJSON({
  messageId: "m-1",
  role: "ROLE_USER",
  parts: [{ text: "숙소 부탁합니다" }],
});
console.log("a 와 b 가 같은가:", isDeepStrictEqual(a, b));
console.log(
  "b.role =",
  b.role,
  " b.contextId =",
  JSON.stringify(b.contextId),
);
// endregion

// region: wire
// 객체 그대로 JSON.stringify 하면 SDK 안의 모양이 나간다
console.log("JSON.stringify(b):");
console.log(JSON.stringify(b, null, 1));
// 와이어 모양은 toJSON 이 만든다 — 기본값 필드는 뺀다
console.log("JSON.stringify(Message.toJSON(b)):");
console.log(JSON.stringify(Message.toJSON(b), null, 1));
// endregion

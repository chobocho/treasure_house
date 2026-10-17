// DataPart 의 value — 넣은 JS 값이 그대로 오간다.
//   node 08/types_data.ts
import { Part } from "@a2a-js/sdk";

// region: data
const req = { headcount: 30, date: "2026-10-30", nights: 1 };
const part: Part = {
  content: { $case: "data", value: req },
  mediaType: "",
  filename: "",
  metadata: undefined,
};
const wire = JSON.stringify(Part.toJSON(part));
console.log("와이어:", wire); // 키 차례는 넣은 차례 그대로
const back = Part.fromJSON(JSON.parse(wire));
if (back.content?.$case === "data") {
  const n = back.content.value.headcount; // value 의 타입은 any
  console.log("headcount:", n, Number.isInteger(n));
}
// toJSON 은 value 를 복사하지 않는다 — 넣은 객체 그 자체
const out = Part.toJSON(part) as { data: object };
console.log("toJSON 의 data === req:", out.data === req);
// endregion

// region: kinds
// 타입 주석은 "JSON 값" — 객체 말고도 받는다. 단 null 은 사라진다
for (const value of [[1, 2], "글", 7, true, null]) {
  const p = Part.fromJSON({ data: value });
  const got = JSON.stringify(p.content);
  console.log(`data ${JSON.stringify(value)} → content ${got}`);
}
// endregion

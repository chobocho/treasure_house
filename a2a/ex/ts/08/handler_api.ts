// JSON-RPC 메서드 ↔ 처리기 메서드, 그리고 처리기 생성자의 인자.
//   node 08/handler_api.ts
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { DefaultRequestHandler } from "@a2a-js/sdk/server";

const entry = fileURLToPath(import.meta.resolve("@a2a-js/sdk/server"));
const js = readFileSync(entry, "utf8");
const dts = readFileSync(join(dirname(entry), "index.d.ts"), "utf8");

// region: methods
// 전송 처리기의 switch — case "메서드" 뒤의 처리기 호출과 짝짓는다
const start = js.indexOf("var JsonRpcTransportHandler = class");
const body = js.slice(
  start,
  js.indexOf("static mapToJSONRPCError", start),
);
const CASE = /(?:case |method === )"(\w+)"[\s\S]*?/;
const CALL = /this\.requestHandler\.(\w+)\(/;
const pairs = [
  ...body.matchAll(new RegExp(CASE.source + CALL.source, "g")),
].map((m) => [m[1]!, m[2]!]);
// 스트림 둘은 삼항 연산자 한 줄에 함께 있다
const sub = /requestHandler\.(\w+)\(SubscribeToTaskRequest/.exec(body);
pairs.push(["SubscribeToTask", sub![1]!]);
console.log(
  "JSON-RPC 메서드 → 처리기 메서드 (JsonRpcTransportHandler)",
);
for (const [method, call] of pairs) {
  console.log(`  ${method!.padEnd(33)} ${call}`);
}
const own = Object.getOwnPropertyNames(DefaultRequestHandler.prototype);
const used = new Set(pairs.map((p) => p[1]));
const rest = own.filter(
  (n) => n !== "constructor" && !n.startsWith("_") && !used.has(n),
);
console.log("그 밖의 공개 메서드:", rest.join(" "));
// endregion

// region: options
// 생성자는 위치 인자 아홉 — 타입 파일의 선언을 그대로 편다
const ctor = /constructor\((agentCard[^)]*)\);/.exec(dts)![1]!;
console.log("new DefaultRequestHandler(");
ctor.split(", ").forEach((arg, i) => console.log(`  ${i + 1}. ${arg}`));
console.log(")");
// endregion

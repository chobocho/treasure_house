// 실행기·처리기가 던지는 A2A 오류 클래스 → JSON-RPC 코드, HTTP 상태.
//   node 08/error_codes.ts
import * as errors from "@a2a-js/sdk/errors";

type ErrorClass = new (m?: string) => errors.A2AError;

// region: codes
// A2AError 의 하위 클래스만 — JsonRpc…·Rest… 는 전송별 꼴이라 뺀다
const rows = Object.entries(errors)
  .filter(([n]) => !/^(JsonRpc|Rest|A2A)/.test(n))
  .filter(([, v]) => (v as ErrorClass).prototype instanceof Error)
  .map(([n, v]) => [n, new (v as ErrorClass)()] as const)
  .map(([n, e]) => [n, e, errors.toJsonRpcError(e).code] as const)
  .sort((a, b) => b[2] - a[2]);
// 한글 다섯 자는 열 칸이라 그만큼 덜 채운다
console.log("오류 클래스".padEnd(32), "JSON-RPC  HTTP  reason");
for (const [name, e, code] of rows) {
  const http = errors.restStatusFor(e);
  console.log(`${name.padEnd(37)} ${code}    ${http}  ${e.reason}`);
}
const plain = new Error("견적표를 못 읽었습니다"); // 표식 없는 예외
const code = errors.toJsonRpcError(plain).code;
const http = errors.restStatusFor(plain);
console.log(
  `${"Error (그 밖의 모든 예외)".padEnd(30)} ${code}    ${http}`,
);
// endregion

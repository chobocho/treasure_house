// 토큰을 확인하는 웹훅 수신기 — 설정에 적어 준 토큰이 아니면 401.
// agents/webhook.ts 는 받은 것을 찍기만 한다. 이것은 문을 지킨다.
//   node 11/hook_check.ts --port P --token T
import { timingSafeEqual } from "node:crypto";
import { createServer } from "node:http";
import { parseArgs } from "node:util";

const { values } = parseArgs({
  options: { port: { type: "string" }, token: { type: "string" } },
});
const want = Buffer.from(values.token ?? "");

// region: check
// === 대신 timingSafeEqual — 걸린 시간으로 토큰을 짐작하지 못하게.
// 길이가 다르면 던지므로 길이부터 본다(길이는 숨길 것이 아니다)
function same(got: string): boolean {
  const b = Buffer.from(got);
  return b.length === want.length && timingSafeEqual(b, want);
}

const server = createServer((req, res) => {
  const chunks: Buffer[] = [];
  req.on("data", (c: Buffer) => chunks.push(c));
  req.on("end", () => {
    const got = req.headers["x-a2a-notification-token"];
    if (typeof got !== "string" || !same(got)) {
      console.log(`거절 401: token=${got ?? "-"}`);
      res.writeHead(401).end();
      return;
    }
    const body = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
    console.log(`통과 204: ${Object.keys(body)[0]}`);
    res.writeHead(204).end();
  });
});
// endregion
server.listen(Number(values.port), "127.0.0.1");
//@ norun

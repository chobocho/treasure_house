// 카드만 내주는 서버 — node:http 만으로. SDK 는 아직 없다.
// 카드는 정해진 경로에 놓인 JSON 문서 한 장일 뿐이다.
import { createServer } from "node:http";
import { parseArgs } from "node:util";

const { values } = parseArgs({
  options: { port: { type: "string" }, url: { type: "string" } },
});
const port = Number(values.port);
const url = values.url ?? `http://127.0.0.1:${port}/`;

const CARD = {
  name: "보물상사 숙소 에이전트",
  description: "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",
  supportedInterfaces: [
    { url, protocolBinding: "JSONRPC", protocolVersion: "1.0" },
  ],
  version: "1.0.0",
  capabilities: { streaming: true },
  defaultInputModes: ["application/json", "text/plain"],
  defaultOutputModes: ["application/json"],
  skills: [
    {
      id: "find-lodging",
      name: "숙소 찾기",
      description: "워크숍 숙소를 고르고 견적을 냅니다.",
      tags: ["lodging", "workshop"],
    },
  ],
};

// region: handler
const server = createServer((req, res) => {
  if (
    req.method === "GET" &&
    req.url === "/.well-known/agent-card.json"
  ) {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(CARD));
  } else {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("없는 경로입니다\n");
  }
});
// endregion
server.listen(port, "127.0.0.1");
//@ norun

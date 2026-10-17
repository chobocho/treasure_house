// 스펙에 없는 필드를 답에 끼워 보내는 작은 서버(실험용).
//   node 08/extra_server.ts --port P [--url U]
// 받은 메시지의 글이 곧 실험 이름이다. SDK 는 카드 모양에만 쓴다.
// 7부의 07/extra_server.py 와 같은 여섯에, 스트림 중간의 오류 하나.
import { parseArgs } from "node:util";
import express from "express";
import { AgentCard } from "@a2a-js/sdk";
import { card } from "./step2_task.ts";

const taskJson = () => ({
  ...{ id: "t-1", contextId: "c-1" },
  status: { state: "TASK_STATE_COMPLETED" } as Record<string, unknown>,
});

// region: variants
// 실험마다 정상 답의 한 곳에 모르는 것을 끼운다
function resultFor(name: string) {
  const task: Record<string, unknown> = taskJson();
  const status = task.status as Record<string, unknown>;
  const result: Record<string, unknown> = { task };
  if (name === "task") task.createdAt = "2026-10-16T00:00:00Z";
  if (name === "status") status.progress = 0.5; // 한 층 안쪽
  if (name === "result") result.hint = "곧 끝납니다"; // task 옆
  if (name === "enum") status.state = "TASK_STATE_PAUSED";
  return result;
}
// 이름이 error 면 막는 호출은 JSON-RPC 오류, 스트림은 Task 다음에
// 오류 이벤트 하나 — TS SDK 서버가 스트림 도중에 내는 모양 그대로
const NOT_FOUND = { code: -32001, message: "Task not found" };
// endregion

const app = express();
app.use(express.json());
app.post("/", (req, res) => {
  const { id, method, params } = req.body;
  const name: string = params.message.parts[0].text;
  const body: Record<string, unknown> = { jsonrpc: "2.0", id };
  if (name === "envelope") body.serverTime = "2026-10-16T00:00:00Z";
  const stream = method === "SendStreamingMessage";
  if (name === "error" && !stream) {
    res.json({ ...body, error: NOT_FOUND });
    return;
  }
  body.result = resultFor(name);
  if (!stream) {
    res.json(body);
    return;
  }
  res.type("text/event-stream");
  res.write(`data: ${JSON.stringify(body)}\n\n`);
  if (name === "error") {
    const err = { jsonrpc: "2.0", id, error: NOT_FOUND };
    res.write(`event: error\ndata: ${JSON.stringify(err)}\n\n`);
  }
  res.end();
});

const { values } = parseArgs({
  options: { port: { type: "string" }, url: { type: "string" } },
});
const port = Number(values.port);
const shown = AgentCard.toJSON(
  card(values.url ?? `http://127.0.0.1:${port}/`),
) as Record<string, unknown>;
shown.capabilities = { streaming: true };
shown.createdAt = "2026-10-16T00:00:00Z"; // 카드에도 하나
app.get("/.well-known/agent-card.json", (_req, res) => {
  res.json(shown);
});
app.listen(port, "127.0.0.1");
//@ norun

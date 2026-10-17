// HTTP 층까지 시험한다 — express 앱을 같은 프로세스 안의 포트 0 에.
//   node 08/run_tests.ts 08/test_http.ts
// 포트 0 은 운영체제가 비어 있는 포트를 고르라는 뜻이다(127.0.0.1).
import assert from "node:assert/strict";
import { once } from "node:events";
import type { AddressInfo } from "node:net";
import { after, before, test } from "node:test";
import express from "express";
import { AgentCard, Message, TaskState } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  UserBuilder,
} from "@a2a-js/sdk/server/express";
import { loadLodging } from "./load_lodging.ts";

// region: app
const server = express().listen(0, "127.0.0.1"); // 앱은 아래에서
let base = "";
before(async () => {
  await once(server, "listening");
  const { port } = server.address() as AddressInfo;
  base = `http://127.0.0.1:${port}/`;
  // 카드의 url 이 이 주소여야 SDK 클라이언트가 여기로 온다
  const { card, executor } = await loadLodging(base);
  const typed = AgentCard.fromJSON(card);
  const store = new InMemoryTaskStore();
  const requestHandler = new DefaultRequestHandler(
    typed,
    store,
    executor,
  );
  const app = express();
  const wire = AgentCard.toJSON(typed) as AgentCard;
  const agentCardProvider = async () => wire;
  app.use(
    "/.well-known/agent-card.json",
    agentCardHandler({ agentCardProvider }),
  );
  const userBuilder = UserBuilder.noAuthentication;
  app.use("/", jsonRpcHandler({ requestHandler, userBuilder }));
  server.on("request", app); // 듣고 있는 서버에 앱을 단다
});
after(() => server.close());
// endregion

// region: wire
async function rpc(method: string, params: object) {
  const res = await fetch(base, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "A2A-Version": "1.0",
    },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
  });
  return res.json();
}

test("wire: quote", async () => {
  const data = { date: "2026-10-30", nights: 1, headcount: 30 };
  const message = {
    messageId: "w-1",
    role: "ROLE_USER",
    parts: [{ data }],
  };
  const body = await rpc("SendMessage", { message });
  const task = body.result.task;
  assert.equal(task.status.state, "TASK_STATE_COMPLETED");
  const total = task.artifacts[0].parts[0].data.total;
  assert.equal(total, 2100000);
  assert.ok(Number.isInteger(total)); // 와이어에서도 정수
});

test("wire: unknown method", async () => {
  const body = await rpc("Nope", {});
  assert.equal(body.error.code, -32601);
});
// endregion

// region: client
// SDK 클라이언트도 같은 앱으로 — 카드부터 받아 스트림으로 묻는다
test("client: stream asks first", async () => {
  const client = await new ClientFactory().createFromUrl(base);
  const message = Message.fromJSON({
    ...{ messageId: "c-1", role: "ROLE_USER" },
    parts: [{ text: "숙소 부탁합니다" }],
  });
  const req = { tenant: "", message, configuration: undefined };
  const seen: string[] = [];
  for await (const ev of client.sendMessageStream({
    ...req,
    metadata: undefined,
  })) {
    const p = ev.payload;
    const st = p?.$case === "task" ? p.value.status : undefined;
    const su = p?.$case === "statusUpdate" ? p.value.status : undefined;
    seen.push(`${p?.$case} ${TaskState[(st ?? su)?.state ?? 0]}`);
  }
  assert.deepEqual(seen, [
    "task TASK_STATE_SUBMITTED",
    "statusUpdate TASK_STATE_INPUT_REQUIRED",
  ]);
});
// endregion
//@ norun

// 기획 에이전트 시험 — 서버 없이 불러와 요청 처리기로 부른다.
//   node 15/run_tests.ts
// agents/planner.ts 는 모듈 맨 위에서 parseCli()·serve(…) 를 부르므로
// 그 둘을 가짜로 바꿔 끼우고 import 한다(08/load_lodging.ts 와 같다).
// 명단(--agents)의 주소 11569 에는 아무도 없다 — 발견이 닿지 못한다.
import assert from "node:assert/strict";
import { once } from "node:events";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { mock, test } from "node:test";
import {
  AgentCard,
  SendMessageRequest,
  Task,
  TaskState,
} from "@a2a-js/sdk";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
  ServerCallContext,
  type AgentExecutor,
} from "@a2a-js/sdk/server";
import * as real from "../agents/common.ts";

const DEAD = "http://127.0.0.1:11569/";
const STORY =
  "2026-10-30부터 1박 2일, 30명(채식 2명), " +
  "예산 6,000,000원, 출발 강남역";

let got: { card: object; executor: AgentExecutor } | undefined;
mock.module("../agents/common.ts", {
  exports: {
    ...real,
    parseCli: () => ({
      port: 0,
      url: "http://127.0.0.1:11568/",
      opts: {
        agents: DEAD,
        "client-id": "planner",
        "client-secret": "planner-secret",
      },
    }),
    serve: (card: object, executor: AgentExecutor) => {
      got = { card, executor }; // 띄우지 않고 받아만 둔다
    },
  },
});
await import("../agents/planner.ts");
const { card, executor } = got!;

async function say(
  text: string,
  store = new InMemoryTaskStore(),
  taskId = "",
) {
  const handler = new DefaultRequestHandler(
    AgentCard.fromJSON(card),
    store,
    executor,
  );
  const message = { messageId: "m-1", role: "ROLE_USER", parts: [] };
  const to = taskId ? { taskId, contextId: "c-1" } : {};
  const req = SendMessageRequest.fromJSON({
    message: { ...message, ...to, parts: [{ text }] },
  });
  const call = new ServerCallContext();
  return (await handler.sendMessage(req, call)) as Task;
}

// 가짜 정산 — 토큰을 주고, 받은 JSON-RPC 메서드를 적어 둔다.
const calls: [string, string][] = [];
function fakeSettlement(): Server {
  return createServer(async (req, res) => {
    let body = "";
    for await (const chunk of req) body += chunk;
    let out: object = {
      access_token: "tok-fake",
      token_type: "Bearer",
    };
    if (req.url !== "/oauth/token") {
      const rpc = JSON.parse(body);
      calls.push([rpc.method, rpc.params.id]);
      const status = { state: "TASK_STATE_CANCELED" };
      const task = { id: rpc.params.id, contextId: "c-1", status };
      out = { jsonrpc: "2.0", id: rpc.id, result: task };
    }
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify(out));
  });
}

function settleCard(url: string) {
  const flow = { tokenUrl: `${url}oauth/token`, scopes: {} };
  const oauth = {
    oauth2SecurityScheme: { flows: { clientCredentials: flow } },
  };
  return AgentCard.fromJSON({
    name: "가짜 정산",
    supportedInterfaces: [
      { url, protocolBinding: "JSONRPC", protocolVersion: "1.0" },
    ],
    securitySchemes: { oauth },
  });
}

// 되물었으면 그 DataPart 의 missing 목록
function asked(task: Task) {
  assert.equal(task.status?.state, TaskState.TASK_STATE_INPUT_REQUIRED);
  const part = task.status!.message!.parts[1]!.content;
  return part?.$case === "data" ? part.value.missing : undefined;
}

// region: tests
test("message counted once", async () => {
  const task = await say("2026-10-30 1박, 채식 2명, 예산 6,000,000원");
  assert.deepEqual(asked(task), ["headcount"]);
});

test("fullwidth digits are not a headcount", async () => {
  const task = await say("2026-10-30 1박 ３０명, 예산 6,000,000원");
  assert.deepEqual(asked(task), ["headcount"]);
});

test("missing roles fail up front", async () => {
  const task = await say(STORY);
  assert.equal(task.status?.state, TaskState.TASK_STATE_FAILED);
  const why = real.textOf(task.status?.message);
  assert.equal(why, "동료를 찾지 못했습니다: 숙소, 식사, 교통, 정산");
  assert.ok(!why.includes("127.0.0.1")); // 안쪽 명단은 새지 않는다
});
// endregion

// region: denial
test("denial cancels settlement", async () => {
  // 결재를 기다리는 기획 작업 하나를 저장소와 waiting 에 놓는다
  const fake = fakeSettlement().listen(0, "127.0.0.1");
  await once(fake, "listening");
  const { port } = fake.address() as AddressInfo;
  const url = `http://127.0.0.1:${port}/`;
  const store = new InMemoryTaskStore();
  const auth = { state: "TASK_STATE_AUTH_REQUIRED" };
  const mine = { id: "plan-1", contextId: "c-1", status: auth };
  await store.save(Task.fromJSON(mine), new ServerCallContext());
  const settle = Task.fromJSON({ ...mine, id: "settle-1" });
  const cards = new Map([["settle", settleCard(url)]]);
  const { waiting } = executor as unknown as {
    waiting: Map<string, object>;
  };
  waiting.set("plan-1", { cards, req: {}, quotes: [], settle });
  const task = await say("안 됩니다", store, "plan-1");
  fake.close();
  assert.equal(task.status?.state, TaskState.TASK_STATE_REJECTED);
  // 반려하면 정산 쪽에서 기다리던 작업도 거둔다
  assert.deepEqual(calls, [["CancelTask", "settle-1"]]);
  assert.equal(waiting.size, 0);
});
// endregion
//@ norun

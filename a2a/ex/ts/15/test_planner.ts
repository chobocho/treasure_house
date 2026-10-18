// 기획 에이전트 시험 — 서버 없이 불러와 요청 처리기로 부른다.
//   node 15/run_tests.ts
// agents/planner.ts 는 모듈 맨 위에서 parseCli()·serve(…) 를 부르므로
// 그 둘을 가짜로 바꿔 끼우고 import 한다(08/load_lodging.ts 와 같다).
// 명단(--agents)의 주소 11569 에는 아무도 없다 — 발견이 닿지 못한다.
import assert from "node:assert/strict";
import { mock, test } from "node:test";
import {
  AgentCard,
  SendMessageRequest,
  TaskState,
  type Task,
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

async function say(text: string) {
  const handler = new DefaultRequestHandler(
    AgentCard.fromJSON(card),
    new InMemoryTaskStore(),
    executor,
  );
  const message = { messageId: "m-1", role: "ROLE_USER", parts: [] };
  const req = SendMessageRequest.fromJSON({
    message: { ...message, parts: [{ text }] },
  });
  const call = new ServerCallContext();
  return (await handler.sendMessage(req, call)) as Task;
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
//@ norun

// 숙소 실행기 시험 묶음 — HTTP 없이 요청 처리기를 직접 부른다.
// 실행기를 받는 함수라서, 같은 시험을 완성판(08/test_lodging.ts)과
// 3단계(08/test_naive.ts)에 돌린다.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { beforeEach, describe, test } from "node:test";
import {
  AgentCard,
  Message,
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
import { textOf } from "../agents/common.ts";

type Case = { name: string; input: object; expected: object };
const GOLDEN = new URL(
  "../../fixtures/golden/domain.json",
  import.meta.url,
);
const CASES: Case[] = JSON.parse(readFileSync(GOLDEN, "utf8"))[
  "chooseLodging"
];
const { TASK_STATE_COMPLETED: DONE } = TaskState;
const { TASK_STATE_INPUT_REQUIRED: ASKING } = TaskState;

// 파트 하나의 DataPart 값(없으면 undefined)
const data = (p: { content?: { $case: string; value: unknown } }) =>
  p.content?.$case === "data" ? (p.content.value as any) : undefined;

export function lodgingSuite(
  name: string,
  executor: AgentExecutor,
  card: object,
) {
  describe(name, () => {
    // region: fixture
    let handler: DefaultRequestHandler;
    let n = 0;
    beforeEach(() => {
      // 시험마다 새 처리기·새 메모리 저장소 — 작업을 나눠 갖지 않는다
      const typed = AgentCard.fromJSON(card);
      const store = new InMemoryTaskStore();
      handler = new DefaultRequestHandler(typed, store, executor);
      n = 0;
    });

    // 사용자 말 하나를 보내고 막는 호출의 Task 를 받는다
    async function say(parts: object[], task?: Task) {
      n += 1;
      const ids = task
        ? { taskId: task.id, contextId: task.contextId }
        : {};
      const message = { messageId: `m-${n}`, role: "ROLE_USER", parts };
      const req = SendMessageRequest.fromJSON({
        message: { ...message, ...ids },
      });
      const call = new ServerCallContext(); // 익명
      return (await handler.sendMessage(req, call)) as Task;
    }
    // endregion

    // region: tests
    test("golden", async (t) => {
      for (const c of CASES) {
        await t.test(c.name, async () => {
          const task = await say([{ data: c.input }]);
          if ("reason" in c.expected) {
            const why = textOf(task.status?.message);
            assert.equal(why, c.expected.reason);
          } else {
            assert.equal(task.status?.state, DONE);
            const got = data(task.artifacts[0]!.parts[0]!);
            assert.deepEqual(got, c.expected);
          }
        });
      }
    });

    test("asks for first missing", async () => {
      const task = await say([{ text: "숙소 부탁합니다" }]);
      assert.equal(task.status?.state, ASKING);
      const asked = data(task.status!.message!.parts[1]!);
      assert.deepEqual(asked.missing, ["date", "nights", "headcount"]);
    });

    test("follow-up completes", async () => {
      const req = { date: "2026-10-30", nights: 1 };
      let task = await say([{ data: req }]);
      task = await say([{ text: "30명" }], task);
      assert.equal(task.status?.state, DONE);
      assert.equal(data(task.artifacts[0]!.parts[0]!).total, 2_100_000);
    });

    test("hears only the user", async () => {
      let task = await say([{ text: "숙소 부탁합니다" }]);
      for (const line of ["30명", "1박", "2026-11-06"]) {
        // 끝난 작업에는 더 말할 수 없다
        if (task.status?.state !== ASKING) break;
        task = await say([{ text: line }], task);
      }
      assert.equal(task.status?.state, DONE);
      const venue = data(task.artifacts[0]!.parts[0]!).venueId;
      assert.equal(venue, "chuncheon-lake");
    });
    // endregion
  });
}
//@ norun

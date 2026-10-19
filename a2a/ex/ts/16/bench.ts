// 오류 시험대 — 완성 에이전트로는 일으킬 수 없는 오류를 일부러 낸다.
// 카드는 확장 카드 기능을 켰지만 확장 카드를 두지 않았다(-32007).
// 실행기는 받은 글에 따라 규칙을 어긴다:
//   "차례 위반" — Task 보다 상태 갱신을 먼저 싣는다(-32006)
//   "고장"      — 예외를 던진다(-32603)
//   그 밖       — 받은 글을 Message 로 돌려준다
//   node 16/bench.ts --port P
import { randomUUID } from "node:crypto";
import { Role, TaskState } from "@a2a-js/sdk";
import {
  AgentEvent,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
} from "@a2a-js/sdk/server";
import {
  jsonrpcInterface,
  parseCli,
  serve,
  textOf,
  textPart,
} from "../agents/common.ts";

// region: card
function card(url: string) {
  return {
    name: "보물상사 시험대 에이전트",
    description: "오류를 일부러 냅니다.",
    version: "1.0.0",
    supportedInterfaces: [jsonrpcInterface(url)],
    // 확장 카드를 준다고 적고, 처리기에는 넘기지 않는다
    capabilities: { streaming: true, extendedAgentCard: true },
    defaultInputModes: ["text/plain"],
    defaultOutputModes: ["text/plain"],
    skills: [
      {
        id: "misbehave",
        name: "규칙 어기기",
        description: "받은 글에 따라 규칙을 어깁니다.",
        tags: ["test"],
      },
    ],
  };
}
// endregion

class Bench implements AgentExecutor {
  // region: execute
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const said = textOf(ctx.userMessage);
    if (said === "차례 위반") {
      // Task 를 싣기 전에 상태부터
      bus.publish(
        AgentEvent.statusUpdate({
          taskId: ctx.taskId,
          contextId: ctx.contextId,
          status: {
            state: TaskState.TASK_STATE_WORKING,
            message: undefined,
            timestamp: undefined,
          },
          metadata: undefined,
        }),
      );
    } else if (said === "고장") {
      throw new Error("시험대가 고장 났습니다");
    } else {
      bus.publish(
        AgentEvent.message({
          messageId: randomUUID(),
          contextId: ctx.contextId,
          taskId: "",
          role: Role.ROLE_AGENT,
          parts: [textPart(said)],
          metadata: undefined,
          extensions: [],
          referenceTaskIds: [],
        }),
      );
    }
    bus.finished();
  }
  // endregion

  async cancelTask() {}
}

const args = parseCli();
serve(card(args.url), new Bench(), args.port);
//@ norun

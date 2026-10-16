// 고장 에이전트 — 일하다 실패한다. 실패를 알리는 세 가지 길(6장):
//   직접 — 실행기가 FAILED 를 싣고 까닭을 status.message 에 적는다
//   나중 — Task·WORKING 을 실은 뒤 예외를 던진다
//   먼저 — 아무 이벤트도 싣기 전에 예외를 던진다
import { TaskState } from "@a2a-js/sdk";
import type {
  AgentExecutor,
  ExecutionEventBus,
  RequestContext,
} from "@a2a-js/sdk/server";
import {
  begin,
  jsonrpcInterface,
  parseCli,
  serve,
  textOf,
  textPart,
} from "../agents/common.ts";

const args = parseCli();
const card = {
  name: "보물상사 고장 에이전트",
  description: "일하다 실패합니다.",
  version: "1.0.0",
  supportedInterfaces: [jsonrpcInterface(args.url)],
  capabilities: {},
  defaultInputModes: ["text/plain"],
  defaultOutputModes: ["text/plain"],
  skills: [
    {
      ...{ id: "broken", name: "고장" },
      ...{ description: "실패 실험", tags: ["debug"] },
    },
  ],
};

// region: execute
class Broken implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const how = textOf(ctx.userMessage);
    console.log(`[고장] ${how}`);
    if (how === "먼저")
      // 이벤트를 하나도 싣기 전에
      throw new Error("장부 파일을 열 수 없습니다");
    const { up } = begin(ctx, bus); // SUBMITTED Task
    up.status(TaskState.TASK_STATE_WORKING);
    if (how === "나중")
      // Task 를 실은 뒤에
      throw new Error("장부 파일을 열 수 없습니다");
    // 직접: 실패도 상태 갱신이다 — 까닭을 메시지로
    const why = [textPart("장부 파일을 열 수 없습니다")];
    up.status(TaskState.TASK_STATE_FAILED, why);
    bus.finished();
  }
  async cancelTask() {}
}
// endregion

serve(card, new Broken(), args.port);
//@ norun

// 기능(capabilities)을 하나도 켜지 않은 에이전트 — 인사만 한다.
// 카드에 없는 기능을 부르면 서버가 무엇을 돌려주는지 보는 실험용.
import { randomUUID } from "node:crypto";
import { Role } from "@a2a-js/sdk";
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
  textPart,
} from "../agents/common.ts";

// region: card
function card(url: string) {
  return {
    name: "보물상사 안내 에이전트",
    description: "인사만 합니다. 켜 둔 기능이 없습니다.",
    version: "1.0.0",
    supportedInterfaces: [jsonrpcInterface(url)],
    capabilities: {}, // 아무것도 켜지 않는다
    defaultInputModes: ["text/plain"],
    defaultOutputModes: ["text/plain"],
    skills: [
      {
        id: "greet",
        name: "인사",
        description: "인사를 돌려줍니다.",
        tags: ["greeting"],
      },
    ],
  };
}
// endregion

class Greeter implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    bus.publish(
      AgentEvent.message({
        messageId: randomUUID(),
        contextId: ctx.contextId,
        taskId: "",
        role: Role.ROLE_AGENT,
        parts: [textPart("안녕하세요, 보물상사입니다.")],
        metadata: undefined,
        extensions: [],
        referenceTaskIds: [],
      }),
    );
    bus.finished();
  }

  async cancelTask() {}
}

const args = parseCli();
serve(card(args.url), new Greeter(), args.port);
//@ norun

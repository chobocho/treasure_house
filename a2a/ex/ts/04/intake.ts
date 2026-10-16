// 접수 에이전트 — 카드의 입력 모드 밖의 미디어 타입은 거절하고(5장),
// 인원("30명")이 없으면 되묻는다(6장의 작업 만들기용).
// TS SDK 는 요청 처리기의 옵션 하나로 미디어 타입을 검사한다.
import express from "express";
import { AgentCard, TaskState } from "@a2a-js/sdk";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  UserBuilder,
} from "@a2a-js/sdk/server/express";
import {
  begin,
  jsonrpcInterface,
  parseCli,
  textOf,
  textPart,
} from "../agents/common.ts";

const args = parseCli();
const card = AgentCard.fromJSON({
  name: "보물상사 접수 에이전트",
  description: "글과 JSON 만 받습니다.",
  version: "1.0.0",
  supportedInterfaces: [jsonrpcInterface(args.url)],
  capabilities: {},
  defaultInputModes: ["text/plain", "application/json"],
  defaultOutputModes: ["text/plain"],
  skills: [{ id: "intake", name: "접수", description: "", tags: [] }],
});

class Intake implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { up } = begin(ctx, bus);
    const m = /(\d+)명/.exec(textOf(ctx.userMessage));
    if (m) {
      console.log(`[접수] ${m[1]}명`);
      up.artifact([textPart(`${m[1]}명 접수했습니다`)], "접수증");
      up.status(TaskState.TASK_STATE_COMPLETED);
    } else {
      console.log("[접수] 되묻기");
      const ask = [textPart("인원은 몇 명입니까?")];
      up.status(TaskState.TASK_STATE_INPUT_REQUIRED, ask);
    }
    bus.finished();
  }
  async cancelTask() {}
}

// region: strict
const handler = new DefaultRequestHandler(
  ...[card, new InMemoryTaskStore(), new Intake()],
  // 버스 관리자·푸시 저장소·푸시 발송기·확장 카드·카드 서명기: 기본값
  ...[undefined, undefined, undefined, undefined, undefined],
  { validateInputModes: true },
);
// endregion
const app = express();
const wire = AgentCard.toJSON(card) as AgentCard; // oneof 를 와이어 모양으로
app.use(
  "/.well-known/agent-card.json",
  agentCardHandler({ agentCardProvider: async () => wire }),
);
const userBuilder = UserBuilder.noAuthentication;
app.use("/", jsonRpcHandler({ requestHandler: handler, userBuilder }));
app.listen(args.port, "127.0.0.1");
//@ norun

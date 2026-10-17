// 숙소 에이전트 — 날짜·박 수·인원을 받아 가장 싼 숙소를 고른다.
//
// 보여 주는 것: 막는(blocking) SendMessage → Task, DataPart 입출력,
// INPUT_REQUIRED 로 되묻기(같은 taskId 로 이어 말하기), REJECTED.
import { Role, TaskState } from "@a2a-js/sdk";
import type {
  AgentExecutor,
  ExecutionEventBus,
  RequestContext,
} from "@a2a-js/sdk/server";
import {
  chooseLodging,
  DATE,
  HEADCOUNT,
  NIGHTS,
  type LodgingRequest,
} from "../workshop/domain.ts";
import {
  PROVIDER,
  asInts,
  begin,
  cancel,
  comma,
  dataOf,
  dataPart,
  jsonrpcInterface,
  parseCli,
  serve,
  textOf,
  textPart,
} from "./common.ts";

// region: questions
// 빠진 항목을 하나씩 되묻는다. 순서가 곧 묻는 순서다.
const QUESTIONS: Record<string, string> = {
  date: "날짜는 언제입니까? (예: 2026-10-30)",
  nights: "며칠 묵습니까? (예: 1박)",
  headcount: "인원은 몇 명입니까?",
};
// endregion

// region: card
function card(url: string) {
  return {
    name: "보물상사 숙소 에이전트",
    description: "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",
    version: "1.0.0",
    provider: PROVIDER,
    supportedInterfaces: [jsonrpcInterface(url)],
    capabilities: { streaming: true },
    defaultInputModes: ["application/json", "text/plain"],
    defaultOutputModes: ["application/json"],
    skills: [
      {
        id: "find-lodging",
        name: "숙소 찾기",
        description: "워크숍 숙소를 고르고 견적을 냅니다.",
        tags: ["lodging", "workshop"],
        examples: ['{"date":"2026-10-30","nights":1,"headcount":30}'],
      },
    ],
  };
}

// endregion

// region: from_text
// 되물음에 글로 답한 경우('30명')를 DataPart 처럼 바꾼다.
function fromText(text: string) {
  const found: Record<string, string> = {};
  const rules = { date: DATE, nights: NIGHTS, headcount: HEADCOUNT };
  for (const [key, rx] of Object.entries(rules)) {
    const m = rx.exec(text);
    if (m) found[key] = m[1]!;
  }
  return found;
}
// endregion

// ['headcount'] — 파이썬이 리스트를 찍는 모양 그대로
const pyList = (xs: string[]) =>
  `[${xs.map((x) => `'${x}'`).join(", ")}]`;

// region: executor
class LodgingExecutor implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { task, up } = begin(ctx, bus);
    // 사용자가 한 말만 듣는다 — 이력에는 에이전트가 되물은 말도
    // 있고, 그 예시("예: 2026-10-30")를 답으로 읽으면 안 된다.
    const heard = [...task.history, ctx.userMessage].filter(
      (m) => m.role === Role.ROLE_USER,
    );
    const req = dataOf(...heard);
    for (const m of heard) Object.assign(req, fromText(textOf(m)));
    const missing = Object.keys(QUESTIONS).filter((k) => !(k in req));
    if (missing.length > 0) {
      const ask = [
        textPart(QUESTIONS[missing[0]!]!),
        dataPart({ missing }),
      ];
      console.log(`[숙소] 되묻기: ${pyList(missing)}`);
      up.status(TaskState.TASK_STATE_INPUT_REQUIRED, ask);
      return;
    }
    // endregion

    // region: quote
    const quote = chooseLodging(
      asInts(req, "nights", "headcount") as LodgingRequest,
    );
    if (!quote.ok) {
      console.log(`[숙소] 거절: ${quote.reason}`);
      up.status(TaskState.TASK_STATE_REJECTED, [
        textPart(quote.reason),
      ]);
      return;
    }
    const summary =
      `${quote.venueName} ${quote.rooms}실, ` +
      `${comma(quote.total)}원`;
    console.log(`[숙소] 견적: ${summary}`);
    up.artifact([dataPart(quote), textPart(summary)], "숙소 견적");
    up.status(TaskState.TASK_STATE_COMPLETED);
  }
  // endregion

  async cancelTask(taskId: string, bus: ExecutionEventBus) {
    cancel(taskId, bus);
  }
}

const args = parseCli();
serve(card(args.url), new LodgingExecutor(), args.port);

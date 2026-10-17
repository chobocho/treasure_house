// 3단계 — 모자란 것을 되묻는 숙소 에이전트. 아직 결함이 하나 있다.
//   node 08/step3_ask.ts --port P [--url U]
// 완성판(agents/lodging.ts)은 아무것도 내보내지 않고 import 하는
// 순간 서버를 띄우므로, 물음 목록·글 읽기·카드를 여기에 옮겨 왔다.
// 완성판과 다른 곳은 실행기의 "무엇을 들었나" 한 줄과 로그뿐이다.
import { TaskState } from "@a2a-js/sdk";
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
  asInts,
  begin,
  cancel,
  dataOf,
  dataPart,
  jsonrpcInterface,
  parseCli,
  serve,
  textOf,
  textPart,
} from "../agents/common.ts";

export const QUESTIONS: Record<string, string> = {
  date: "날짜는 언제입니까? (예: 2026-10-30)",
  nights: "며칠 묵습니까? (예: 1박)",
  headcount: "인원은 몇 명입니까?",
};

export function fromText(text: string) {
  const found: Record<string, string> = {};
  const rules = { date: DATE, nights: NIGHTS, headcount: HEADCOUNT };
  for (const [key, rx] of Object.entries(rules)) {
    const m = rx.exec(text);
    if (m) found[key] = m[1]!;
  }
  return found;
}

// 키를 정렬해 한 줄로 — 로그를 실행마다 같게
const sorted = (o: object) =>
  JSON.stringify(Object.fromEntries(Object.entries(o).sort()));

// region: executor
export class AskExecutor implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { task, up } = begin(ctx, bus); // 이어 말하기면 이력이 있다
    const heard = [...task.history, ctx.userMessage]; // 이것이 결함이다
    const req = dataOf(...heard);
    for (const m of heard) Object.assign(req, fromText(textOf(m)));
    console.log(`[3단계] 들은 것: ${sorted(req)}`);
    const missing = Object.keys(QUESTIONS).filter((k) => !(k in req));
    if (missing.length > 0) {
      // 첫째 빠진 것을 글로 묻고, 빠진 목록은 데이터로
      const ask = [
        textPart(QUESTIONS[missing[0]!]!),
        dataPart({ missing }),
      ];
      up.status(TaskState.TASK_STATE_INPUT_REQUIRED, ask); // 멈춤
      return; // 다음 말이 오면 처리기가 execute 를 다시 부른다
    }
    const quote = chooseLodging(
      asInts(req, "nights", "headcount") as LodgingRequest,
    );
    if (!quote.ok) {
      const why = [textPart(quote.reason)];
      up.status(TaskState.TASK_STATE_REJECTED, why);
      return;
    }
    up.artifact([dataPart(quote)], "숙소 견적");
    up.status(TaskState.TASK_STATE_COMPLETED);
  }

  async cancelTask(taskId: string, bus: ExecutionEventBus) {
    cancel(taskId, bus);
  }
}
// endregion

export function card(url: string) {
  return {
    name: "보물상사 숙소 에이전트(3단계)",
    description: "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",
    version: "0.3.0",
    supportedInterfaces: [jsonrpcInterface(url)],
    capabilities: { streaming: true },
    defaultInputModes: ["application/json", "text/plain"],
    defaultOutputModes: ["application/json"],
    skills: [
      {
        ...{ id: "find-lodging", name: "숙소 찾기" },
        description: "워크숍 숙소를 고르고 견적을 냅니다.",
        tags: ["lodging"],
      },
    ],
  };
}

if (import.meta.main) {
  const args = parseCli();
  serve(card(args.url), new AskExecutor(), args.port);
}
//@ norun

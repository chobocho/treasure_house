// 식사 에이전트 — 끼니마다 메뉴를 골라 스트리밍으로 알려 준다.
//
// 보여 주는 것: SendStreamingMessage(SSE), 끼니마다 WORKING 상태 갱신,
// 식단표 아티팩트를 청크로 이어 붙이기(append·lastChunk), 파일 파트
// (menu.md, raw)와 데이터 파트(견적)를 함께 돌려주기.
import { TaskState } from "@a2a-js/sdk";
import type {
  AgentExecutor,
  ExecutionEventBus,
  RequestContext,
} from "@a2a-js/sdk/server";
import {
  planMeals,
  type MealsRequest,
  type Slot,
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
  rawPart,
  serve,
  textPart,
} from "./common.ts";

// 끼니 이름표. 슬롯 이름(day1-dinner)을 사람이 읽는 말로 바꾼다.
const KIND: Record<string, string> = {
  dinner: "저녁",
  breakfast: "아침",
  lunch: "점심",
};

function card(url: string) {
  return {
    name: "보물상사 식사 에이전트",
    description: "박 수·인원·채식 인원으로 끼니별 식단을 짭니다.",
    version: "1.0.0",
    provider: PROVIDER,
    supportedInterfaces: [jsonrpcInterface(url)],
    capabilities: { streaming: true },
    defaultInputModes: ["application/json"],
    defaultOutputModes: ["application/json", "text/markdown"],
    skills: [
      {
        id: "plan-meals",
        name: "식단 짜기",
        description: "끼니마다 일반식·채식 메뉴를 고릅니다.",
        tags: ["meals", "workshop"],
        examples: ['{"nights":1,"headcount":30,"vegetarians":2}'],
      },
    ],
  };
}

// day1-dinner → 1일차 저녁
function label(slot: string) {
  const [day, kind] = slot.split("-");
  return `${day!.replace(/^day/, "")}일차 ${KIND[kind!]}`;
}

// 식단표의 한 줄: 1일차 저녁: 한정식 28명, 버섯 전골 2명
function line(row: Slot) {
  const picks = [row.regular, row.vegetarian]
    .filter((c) => c !== null)
    .map((c) => `${c.name} ${c.count}명`);
  return `${label(row.slot)}: ${picks.join(", ")}`;
}

class CateringExecutor implements AgentExecutor {
  readonly stepMs: number; // 끼니 사이 쉬는 시간(보여 주기용)
  constructor(stepMs: number) {
    this.stepMs = stepMs;
  }

  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { up } = begin(ctx, bus);
    const req = asInts(
      dataOf(ctx.userMessage),
      ...["nights", "headcount", "vegetarians"],
    );
    if (!("vegetarians" in req)) req.vegetarians = 0;
    const plan = planMeals(req as MealsRequest);
    if (!plan.ok) {
      console.log(`[식사] 거절: ${plan.reason}`);
      up.status(TaskState.TASK_STATE_REJECTED, [textPart(plan.reason)]);
      return;
    }
    const rows = plan.slots;
    for (const [i, row] of rows.entries()) {
      if (!(await up.pause(this.stepMs))) return; // 취소됨
      const note = `식단 짜는 중 ${i + 1}/${rows.length}`;
      up.status(TaskState.TASK_STATE_WORKING, [textPart(note)]);
      // 같은 artifactId 로 한 줄씩 이어 붙인다.
      up.artifact([textPart(line(row) + "\n")], "식단표", {
        id: "meal-plan",
        append: i > 0,
        lastChunk: i === rows.length - 1,
      });
    }
    const menu =
      "# 식단표\n\n" + rows.map((r) => `- ${line(r)}\n`).join("");
    const file = rawPart(Buffer.from(menu), "text/markdown", "menu.md");
    up.artifact([file], "식단표 파일", { id: "menu-file" });
    up.artifact([dataPart(plan)], "식사 견적", { id: "meal-quote" });
    console.log(`[식사] 견적: ${comma(plan.total)}원`);
    up.status(TaskState.TASK_STATE_COMPLETED);
  }

  async cancelTask(taskId: string, bus: ExecutionEventBus) {
    cancel(taskId, bus);
  }
}

const { port, url, opts } = parseCli({ "step-ms": "100" });
serve(card(url), new CateringExecutor(Number(opts["step-ms"])), port);

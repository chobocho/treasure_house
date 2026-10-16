// 교통 에이전트 — 버스를 고르고, 시간이 걸리는 배차를 진행한다.
//
// 보여 주는 것: returnImmediately 로 바로 돌려받는 Task, 오래 걸리는
// 작업의 단계별 상태 갱신, 푸시 알림(웹훅), GetTask 폴링, ListTasks,
// CancelTask(→ CANCELED), SubscribeToTask.
import { TaskState } from "@a2a-js/sdk";
import {
  DefaultPushNotificationSender,
  InMemoryPushNotificationStore,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
} from "@a2a-js/sdk/server";
import {
  chooseBuses,
  type BusPlan,
  type BusRequest,
} from "../workshop/domain.ts";
import { workshop } from "../workshop/fixtures.ts";
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
  textPart,
} from "./common.ts";

function card(url: string) {
  return {
    name: "보물상사 교통 에이전트",
    description: "인원과 박 수로 버스를 고르고 배차합니다.",
    version: "1.0.0",
    provider: PROVIDER,
    supportedInterfaces: [jsonrpcInterface(url)],
    capabilities: { streaming: true, pushNotifications: true },
    defaultInputModes: ["application/json"],
    defaultOutputModes: ["application/json"],
    skills: [
      {
        id: "book-bus",
        name: "버스 배차",
        description: "전세 버스를 고르고 배차까지 진행합니다.",
        tags: ["transport", "workshop"],
        examples: ['{"headcount":30,"nights":1,"depart":"강남역"}'],
      },
    ],
  };
}

// [{"id":"bus45","count":1}] → 45인승 1대
function vehiclesText(plan: BusPlan) {
  const seats = new Map(workshop.buses.map((b) => [b.id, b.seats]));
  return plan.vehicles
    .map((v) => `${seats.get(v.id)}인승 ${v.count}대`)
    .join(", ");
}

class BusExecutor implements AgentExecutor {
  readonly stepMs: number; // 배차 단계 하나에 걸리는 시간
  constructor(stepMs: number) {
    this.stepMs = stepMs;
  }

  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { up } = begin(ctx, bus);
    const req = asInts(dataOf(ctx.userMessage), "headcount", "nights");
    const plan = chooseBuses(req as BusRequest);
    if (!plan.ok) {
      console.log(`[교통] 거절: ${plan.reason}`);
      up.status(TaskState.TASK_STATE_REJECTED, [textPart(plan.reason)]);
      return;
    }
    for (const step of workshop.busSteps) {
      // 취소되면 여기서 끊긴다
      if (!(await up.pause(this.stepMs))) return;
      console.log(`[교통] ${step}`);
      up.status(TaskState.TASK_STATE_WORKING, [textPart(step)]);
    }
    const depart = req.depart || "미정"; // 없거나 null 이면
    const summary =
      `${vehiclesText(plan)}, ${plan.days}일, ` +
      `${comma(plan.total)}원, 출발 ${depart}`;
    up.artifact([dataPart(plan), textPart(summary)], "배차 확인서", {
      id: "bus-booking",
    });
    console.log(`[교통] 완료: ${summary}`);
    up.status(TaskState.TASK_STATE_COMPLETED);
  }

  async cancelTask(taskId: string, bus: ExecutionEventBus) {
    console.log("[교통] 취소");
    cancel(taskId, bus, textPart("배차를 취소했습니다"));
  }
}

const { port, url, opts } = parseCli({ "step-ms": "300" });
const store = new InMemoryPushNotificationStore();
serve(card(url), new BusExecutor(Number(opts["step-ms"])), port, {
  push: [store, new DefaultPushNotificationSender(store)],
});

// 교통 에이전트를 파일 저장소로 띄운다.
//   node 17/bus_store.ts --port P [--step-ms N] [--dir D] [--recover]
// --dir 을 주지 않으면 $TMPDIR/tasks-P (실행 명세마다 새로 비는 곳).
// agents/bus.ts 는 불러오면 곧바로 서버를 띄우는 파일이라 가져다 쓸
// 수 없어, 실행기와 카드를 그대로 옮겨 왔다(같은 세 단계).
import os from "node:os";
import path from "node:path";
import { parseArgs } from "node:util";
import express from "express";
import { AgentCard, TaskState } from "@a2a-js/sdk";
import {
  DefaultPushNotificationSender,
  DefaultRequestHandler,
  InMemoryPushNotificationStore,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  UserBuilder,
} from "@a2a-js/sdk/server/express";
import { chooseBuses, type BusRequest } from "../workshop/domain.ts";
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
  textPart,
} from "../agents/common.ts";
import { FileTaskStore } from "./filestore.ts";

const card = (url: string) => ({
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
});

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
      up.status(TaskState.TASK_STATE_REJECTED, [textPart(plan.reason)]);
      return;
    }
    for (const step of workshop.busSteps) {
      if (!(await up.pause(this.stepMs))) return; // 취소되면 끝
      console.log(`[교통] ${step}`);
      up.status(TaskState.TASK_STATE_WORKING, [textPart(step)]);
    }
    const seats = new Map(workshop.buses.map((b) => [b.id, b.seats]));
    const cars = plan.vehicles
      .map((v) => `${seats.get(v.id)}인승 ${v.count}대`)
      .join(", ");
    const summary =
      `${cars}, ${plan.days}일, ${comma(plan.total)}원, ` +
      `출발 ${req.depart || "미정"}`;
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

const { values: o } = parseArgs({
  options: {
    ...{ port: { type: "string" }, "step-ms": { type: "string" } },
    ...{ dir: { type: "string" }, recover: { type: "boolean" } },
  },
});
const port = Number(o.port);
const dir = o.dir ?? path.join(os.tmpdir(), `tasks-${port}`);
const typed = AgentCard.fromJSON(card(`http://127.0.0.1:${port}/`));

// region: wire
const store = new FileTaskStore(dir); // Task 만 디스크로
if (o.recover) await store.recover();
// 푸시 설정은 메모리 그대로
const pushes = new InMemoryPushNotificationStore();
const handler = new DefaultRequestHandler(
  typed,
  store,
  new BusExecutor(Number(o["step-ms"] ?? "300")),
  undefined, // 이벤트 버스 관리자: 기본값(메모리)
  pushes,
  new DefaultPushNotificationSender(pushes),
);
// endregion
const app = express();
const wire = AgentCard.toJSON(typed) as AgentCard;
app.use(
  "/.well-known/agent-card.json",
  agentCardHandler({ agentCardProvider: async () => wire }),
);
const userBuilder = UserBuilder.noAuthentication;
app.use("/", jsonRpcHandler({ requestHandler: handler, userBuilder }));
app.listen(port, "127.0.0.1");
//@ norun

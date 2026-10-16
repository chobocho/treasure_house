// 고집 에이전트 — 상태를 앞뒤로 옮겨 보고, 끝난 뒤에도 옮겨 본다.
// SDK 가 어느 전이를 막는지 보려는 실험용이다(2장).
import { setTimeout as sleep } from "node:timers/promises";
import { TaskState, type Task } from "@a2a-js/sdk";
import {
  AgentEvent,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
} from "@a2a-js/sdk/server";
import { jsonrpcInterface, parseCli, serve } from "../agents/common.ts";

const args = parseCli();
const card = {
  name: "보물상사 고집 에이전트",
  description: "상태를 마음대로 옮겨 봅니다.",
  version: "1.0.0",
  supportedInterfaces: [jsonrpcInterface(args.url)],
  capabilities: {},
  defaultInputModes: ["text/plain"],
  defaultOutputModes: ["text/plain"],
  skills: [
    {
      ...{ id: "stubborn", name: "고집" },
      ...{ description: "상태 전이 실험", tags: ["debug"] },
    },
  ],
};

// region: execute
type Name = "WORKING" | "SUBMITTED" | "COMPLETED";

class Stubborn implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { taskId, contextId } = ctx;
    const status = (name: Name) => ({
      state: TaskState[`TASK_STATE_${name}`],
      ...{ message: undefined, timestamp: new Date().toISOString() },
    });
    const task: Task = {
      ...{ id: taskId, contextId, status: status("SUBMITTED") },
      ...{ artifacts: [], history: [ctx.userMessage] },
      metadata: undefined,
    };
    bus.publish(AgentEvent.task(task));
    const put = (name: Name) => {
      const ev = { taskId, contextId, status: status(name) };
      bus.publish(AgentEvent.statusUpdate({ ...ev, metadata: {} }));
      console.log(`[고집] ${name} 실음`);
    };
    // 앞으로, 뒤로(접수로 되돌리기), 끝 — 갱신기는 없다
    for (const name of ["WORKING", "SUBMITTED", "COMPLETED"] as Name[])
      put(name);
    await sleep(200); // 끝낸 뒤 조금 있다가 또 옮긴다
    put("WORKING");
    bus.finished();
  }
  async cancelTask() {}
}
// endregion

serve(card, new Stubborn(), args.port);
//@ norun

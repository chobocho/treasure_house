// 실행기를 서버 없이 돌린다 — 버스의 이벤트를 받아 찍기만 한다.
//   node 08/drive.ts echo '숙소 부탁합니다'
//   node 08/drive.ts quote 2026-10-30 1 30
import { randomUUID } from "node:crypto";
import {
  Message,
  SendMessageRequest,
  TaskState,
  type Part,
} from "@a2a-js/sdk";
import {
  DefaultExecutionEventBus,
  RequestContext,
  ServerCallContext,
  type AgentExecutionEvent,
} from "@a2a-js/sdk/server";
import { EchoExecutor } from "./step1_echo.ts";
import { QuoteExecutor } from "./step2_task.ts";

const text = (parts: Part[]) =>
  parts.map((p) =>
    p.content?.$case === "text" ? p.content.value : "",
  );

function describe(ev: AgentExecutionEvent): string {
  switch (ev.kind) {
    case "message":
      return `Message: ${text(ev.data.parts).join(" ")}`;
    case "task":
      return `Task ${ev.data.id} 이력 ${ev.data.history.length}`;
    case "statusUpdate": {
      const s = ev.data.status!;
      const why = text(s.message?.parts ?? []).join(" ");
      return `상태 ${TaskState[s.state]} ${why}`.trimEnd();
    }
    case "artifactUpdate": {
      const a = ev.data.artifact!;
      const p = a.parts[0]?.content;
      const venue = p?.$case === "data" ? p.value.venueName : "";
      return `아티팩트 ${a.name}: ${venue}`;
    }
  }
}

// region: bus
// 버스는 EventTarget — 'event' 를 듣는 쪽을 하나 달면 된다
const bus = new DefaultExecutionEventBus();
bus.on("event", (ev) => console.log("  →", describe(ev)));
// endregion

// region: context
function contextFor(args: string[]) {
  const [date, nights, n] = args;
  const part =
    args.length === 3
      ? { data: { date, nights: Number(nights), headcount: Number(n) } }
      : { text: args[0] };
  const message = Message.fromJSON({
    ...{ messageId: "m-1", role: "ROLE_USER", parts: [part] },
  });
  const request = SendMessageRequest.fromJSON({});
  request.message = message;
  // TS 의 RequestContext 는 id 를 짓지 않는다 — 받는 대로 둔다
  const ctx = new RequestContext(
    ...[request, randomUUID(), randomUUID()],
    new ServerCallContext(),
  );
  console.log("taskId   ", ctx.taskId);
  console.log("contextId", ctx.contextId);
  console.log(
    "메시지의 taskId:",
    JSON.stringify(ctx.userMessage.taskId),
  );
  console.log("이어 말하기?", ctx.task !== undefined);
  return ctx;
}
// endregion

// region: main
const executors = { echo: EchoExecutor, quote: QuoteExecutor };
const which = process.argv[2] as keyof typeof executors;
const ctx = contextFor(process.argv.slice(3));
await new executors[which]().execute(ctx, bus);
// endregion
//@ norun

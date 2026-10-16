// 받은 파트를 하나씩 말해 주는 에이전트 — 대답은 Task 가 아니라
// Message 하나다. 4부에서 파트의 모양과 수의 타입을 보는 실험용.
import { randomUUID } from "node:crypto";
import { Role, type Part } from "@a2a-js/sdk";
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

function card(url: string) {
  return {
    name: "보물상사 파트 확인 에이전트",
    description: "받은 파트를 하나씩 말해 줍니다.",
    version: "1.0.0",
    supportedInterfaces: [jsonrpcInterface(url)],
    capabilities: {},
    defaultInputModes: ["text/plain", "application/json"],
    defaultOutputModes: ["text/plain"],
    skills: [
      {
        id: "echo-parts",
        name: "파트 확인",
        description: "받은 파트의 종류와 값을 돌려줍니다.",
        tags: ["debug"],
      },
    ],
  };
}

// region: describe
// 값 하나: 이 언어가 읽은 타입 이름과 값.
const value = (v: unknown) => `${typeof v} ${JSON.stringify(v)}`;

function describe(i: number, part: Part): string {
  const c = part.content; // {$case, value} — $case 가 종류
  let line: string;
  if (c?.$case === "text")
    line = `${i}. text ${JSON.stringify(c.value)}`;
  else if (c?.$case === "raw")
    line = `${i}. raw ${c.value.length}바이트`;
  else if (c?.$case === "url") line = `${i}. url ${c.value}`;
  else if (c?.$case === "data") {
    const d: unknown = c.value; // JSON.parse 가 만든 값 그대로
    if (d !== null && typeof d === "object" && !Array.isArray(d)) {
      const o = d as Record<string, unknown>;
      const kv = Object.keys(o)
        .sort()
        .map((k) => `${k}: ${value(o[k])}`);
      line = `${i}. data {${kv.join(", ")}}`;
    } else line = `${i}. data ${value(d)}`;
  } else line = `${i}. (내용 없음)`; // content 가 비었다
  if (part.filename) line += ` filename=${part.filename}`;
  if (part.mediaType) line += ` mediaType=${part.mediaType}`;
  return line;
}
// endregion

// region: execute
class EchoParts implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const lines = ctx.userMessage.parts.map((p, i) =>
      describe(i + 1, p),
    );
    console.log("[파트]", lines.join(" / "));
    // Task 를 만들지 않고 Message 하나로 답한다(한 줄에 파트 하나)
    bus.publish(
      AgentEvent.message({
        messageId: randomUUID(),
        contextId: ctx.contextId,
        taskId: "",
        role: Role.ROLE_AGENT,
        parts: lines.map((t) => textPart(t)),
        metadata: undefined,
        extensions: [],
        referenceTaskIds: [],
      }),
    );
    bus.finished();
  }

  async cancelTask() {}
}
// endregion

const args = parseCli();
serve(card(args.url), new EchoParts(), args.port);
//@ norun

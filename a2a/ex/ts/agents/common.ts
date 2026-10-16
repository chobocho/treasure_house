// 다섯 에이전트가 함께 쓰는 SDK 접착 코드.
//
// 업무 규칙은 workshop/domain.ts 에 있고, 여기는 A2A 쪽 잔일만 한다:
// 명령줄 읽기, 카드의 공통 부분, 파트 만들기·꺼내기, 작업 갱신,
// 서버 띄우기.
import { randomUUID } from "node:crypto";
import { setTimeout as sleep } from "node:timers/promises";
import { parseArgs } from "node:util";
import express, { type Express } from "express";
import {
  AgentCard,
  Role,
  TaskState,
  type Message,
  type Part,
  type Task,
} from "@a2a-js/sdk";
import {
  AgentEvent,
  DefaultRequestHandler,
  InMemoryTaskStore,
  type AgentExecutor,
  type ExecutionEventBus,
  type PushNotificationSender,
  type PushNotificationStore,
  type RequestContext,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  UserBuilder,
} from "@a2a-js/sdk/server/express";

export const PROVIDER = {
  organization: "보물상사",
  url: "https://treasure-house.example",
};

// --port 는 붙을 곳, --url 은 카드에 적을 바깥 주소.
// extra 는 에이전트마다 더 받는 옵션: 이름 → 기본값(null 이면 필수).
export function parseCli(extra: Record<string, string | null> = {}) {
  const names = ["port", "url", ...Object.keys(extra)];
  const { values } = parseArgs({
    options: Object.fromEntries(
      names.map((n) => [n, { type: "string" as const }]),
    ),
  });
  const v = values as Record<string, string | undefined>;
  const opts: Record<string, string> = {};
  for (const n of ["port", ...Object.keys(extra)]) {
    const got = v[n] ?? extra[n];
    if (got === undefined || got === null) {
      console.error(`--${n} 이 필요합니다`);
      process.exit(2);
    }
    opts[n] = got;
  }
  const port = Number(opts.port);
  const url = v.url ?? `http://127.0.0.1:${port}/`;
  return { port, url, opts };
}

export function jsonrpcInterface(url: string) {
  return { url, protocolBinding: "JSONRPC", protocolVersion: "1.0" };
}

// 1234567 → "1,234,567" (파이썬의 f"{n:,}" 와 같은 모양)
export function comma(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

export function textPart(text: string, mediaType = ""): Part {
  const content = { $case: "text" as const, value: text };
  return { content, mediaType, filename: "", metadata: undefined };
}

export function dataPart(data: object): Part {
  const content = { $case: "data" as const, value: data };
  return { content, mediaType: "", filename: "", metadata: undefined };
}

export function rawPart(
  raw: Buffer,
  mediaType: string,
  filename: string,
) {
  const content = { $case: "raw" as const, value: raw };
  return { content, mediaType, filename, metadata: undefined } as Part;
}

// 글 파트만 줄바꿈으로 이어 붙인다(파이썬 get_message_text 와 같게).
export function textOf(m: Message | undefined): string {
  const texts = (m?.parts ?? []).map((p) =>
    p.content?.$case === "text" ? p.content.value : null,
  );
  return texts.filter((t) => t !== null).join("\n");
}

// 메시지들의 DataPart 를 앞에서부터 차례로 덮어 합친다.
export function dataOf(...messages: (Message | undefined)[]) {
  const merged: Record<string, unknown> = {};
  for (const m of messages) {
    for (const p of m?.parts ?? []) {
      const d: unknown = p.content?.$case === "data" && p.content.value;
      if (d && typeof d === "object" && !Array.isArray(d)) {
        Object.assign(merged, d);
      }
    }
  }
  return merged;
}

// JSON 에는 30 과 30.0 의 구별이 없어 TS 에서는 둘 다 30 이다.
// 그래도 되물음의 글('30명')에서 온 "30" 은 수로 바꿔야 한다.
export function asInts(d: Record<string, unknown>, ...keys: string[]) {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(d)) {
    out[k] = keys.includes(k) ? Math.trunc(Number(v)) : v;
  }
  return out;
}

const TERMINAL = [
  TaskState.TASK_STATE_COMPLETED,
  TaskState.TASK_STATE_FAILED,
  TaskState.TASK_STATE_CANCELED,
  TaskState.TASK_STATE_REJECTED,
];
// 실행 중인 작업 → 갱신기. 취소 요청에는 taskId 만 오기 때문이다.
const live = new Map<string, Updater>();

// 파이썬 SDK 의 TaskUpdater 몫. TS SDK 에는 없어서 사건
// (statusUpdate·artifactUpdate)을 직접 만들어 버스에 싣는다.
export class Updater {
  readonly stop = new AbortController();
  readonly bus: ExecutionEventBus;
  readonly taskId: string;
  readonly contextId: string;
  constructor(
    bus: ExecutionEventBus,
    taskId: string,
    contextId: string,
  ) {
    this.bus = bus;
    this.taskId = taskId;
    this.contextId = contextId;
  }

  message(parts: Part[]): Message {
    const { taskId, contextId } = this;
    const role = Role.ROLE_AGENT;
    const ids = { messageId: randomUUID(), taskId, contextId };
    const rest = { metadata: undefined, extensions: [] };
    return { ...ids, role, parts, ...rest, referenceTaskIds: [] };
  }

  status(state: TaskState, parts?: Part[]) {
    const message = parts && this.message(parts);
    const timestamp = new Date().toISOString();
    const { taskId, contextId } = this;
    const status = { state, message, timestamp };
    const ev = { taskId, contextId, status, metadata: undefined };
    this.bus.publish(AgentEvent.statusUpdate(ev));
    if (TERMINAL.includes(state)) live.delete(taskId);
  }

  artifact(parts: Part[], name: string, o: Chunk = {}) {
    const artifact = {
      artifactId: o.id ?? randomUUID(),
      name,
      description: "",
      parts,
      metadata: undefined,
      extensions: [],
    };
    const { taskId, contextId } = this;
    const flags = { append: !!o.append, lastChunk: !!o.lastChunk };
    const ev = { taskId, contextId, artifact, ...flags };
    this.bus.publish(
      AgentEvent.artifactUpdate({ ...ev, metadata: undefined }),
    );
  }

  // 쉬는 동안 취소되면 false — 실행 함수는 그 자리에서 끝낸다.
  async pause(ms: number): Promise<boolean> {
    const signal = this.stop.signal;
    return sleep(ms, true, { signal }).catch(() => false);
  }
}
type Chunk = { id?: string; append?: boolean; lastChunk?: boolean };

// region: begin
// TS SDK 는 실행마다 첫 사건이 Task(또는 Message)이기를 강제한다 —
// 같은 taskId 로 이어 말할 때도 그렇다(명세 3.1.2 의 스트림 규칙).
// 그래서 이어 말하기에도 지금의 Task 를 다시 싣는다. 답을 받았으니
// 상태는 WORKING 으로 — 멈춘 상태 그대로 실으면 막는 호출이 그것을
// '멈춤'으로 보고 곧장 돌아간다(파이썬 SDK 에서 실제로 그랬다).
export function begin(ctx: RequestContext, bus: ExecutionEventBus) {
  const working = {
    state: TaskState.TASK_STATE_WORKING,
    message: undefined,
    timestamp: undefined,
  };
  const task: Task = ctx.task
    ? { ...ctx.task, status: working }
    : {
        id: ctx.taskId,
        contextId: ctx.contextId,
        status: {
          state: TaskState.TASK_STATE_SUBMITTED,
          message: undefined,
          timestamp: undefined,
        },
        artifacts: [],
        history: [ctx.userMessage],
        metadata: undefined,
      };
  bus.publish(AgentEvent.task(task));
  const up = new Updater(bus, task.id, task.contextId);
  live.set(task.id, up);
  return { task, up };
}

// 실행 중이면 멈추게 하고 CANCELED 를 싣는다.
export function cancel(
  taskId: string,
  bus: ExecutionEventBus,
  ...p: Part[]
) {
  const up = live.get(taskId) ?? new Updater(bus, taskId, "");
  up.stop.abort();
  up.status(TaskState.TASK_STATE_CANCELED, p.length ? p : undefined);
}
// endregion

type Serve = {
  routes?: (app: Express) => void; // 토큰 발급·인증 검사 등
  userBuilder?: UserBuilder;
  extended?: object; // 확장 카드(로그인한 클라이언트용)
  push?: [PushNotificationStore, PushNotificationSender];
};

// region: serve
// JSON-RPC 와 카드 경로를 단 express 앱을 띄운다.
// card 는 프로토 JSON 모양 그대로 받는다(서명도 이 모양 위에서 한다).
export function serve(
  card: object,
  executor: AgentExecutor,
  port: number,
  more: Serve = {},
) {
  const typed = AgentCard.fromJSON(card);
  const extended = more.extended && AgentCard.fromJSON(more.extended);
  const [store, sender] = more.push ?? [];
  const handler = new DefaultRequestHandler(
    typed,
    new InMemoryTaskStore(),
    executor,
    undefined, // 사건 버스 관리자: 기본값
    store,
    sender,
    extended || undefined,
    undefined, // 카드 서명기: 쓰지 않는다(서명은 미리 해 둔다)
    // AUTH_REQUIRED 에서도 스트림을 닫는다. 기본값은 버스를 살려 둔 채
    // 같은 실행이 이어지기를 기다리지만, 이 에이전트들은 결재 토큰을
    // 새 메시지로 받는다(파이썬 SDK 와 같은 흐름).
    { keepBusAliveStates: [TaskState.TASK_STATE_INPUT_REQUIRED] },
  );
  const app = express();
  more.routes?.(app);
  // SDK 의 카드 처리기는 객체를 JSON.stringify 할 뿐이라, ts-proto
  // 객체를 주면 oneof 가 {"$case":…} 로 나간다 — toJSON 으로 바꿔 준다.
  const wire = AgentCard.toJSON(typed) as AgentCard;
  app.use(
    "/.well-known/agent-card.json",
    agentCardHandler({ agentCardProvider: async () => wire }),
  );
  const userBuilder = more.userBuilder ?? UserBuilder.noAuthentication;
  app.use(
    "/",
    jsonRpcHandler({ requestHandler: handler, userBuilder }),
  );
  app.listen(port, "127.0.0.1");
}
// endregion

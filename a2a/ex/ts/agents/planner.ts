// 기획 에이전트 — 총무팀의 한 문장을 받아 워크숍 전체를 꾸린다.
//
// 서버이면서 클라이언트다. 카드로 동료를 찾고(스킬 태그), 숙소·식사·
// 교통을 동시에 맡기고, 견적을 정산 에이전트에 넘겨 결재를 받는다.
// 정산이 결재를 요구하면 그 요구를 자기 사용자에게 넘긴다(§7.6.2 의
// AUTH_REQUIRED 사슬).
import {
  createPublicKey,
  randomUUID,
  type JsonWebKey,
} from "node:crypto";
import { readFileSync } from "node:fs";
import {
  AgentCard,
  Role,
  TaskState,
  verifyAgentCardSignature,
  Message,
  type Task,
} from "@a2a-js/sdk";
import {
  ClientFactory,
  DefaultAgentCardResolver,
} from "@a2a-js/sdk/client";
import type {
  AgentExecutor,
  ExecutionEventBus,
  RequestContext,
} from "@a2a-js/sdk/server";
import { parseRequest } from "../workshop/domain.ts";
import {
  PROVIDER,
  begin,
  cancel,
  comma,
  dataPart,
  jsonrpcInterface,
  parseCli,
  serve,
  textOf,
  textPart,
  type Updater,
} from "./common.ts";

// 맡길 일 → 그 일을 하는 에이전트의 스킬 태그
const ROLES = {
  lodging: "lodging",
  meals: "meals",
  bus: "transport",
  settle: "budget",
};
const ASK: Record<string, string> = {
  date: "날짜(예: 2026-10-30)",
  nights: "박 수(예: 1박)",
  headcount: "인원(예: 30명)",
  budget: "예산(예: 예산 6,000,000원)",
};

// 선(wire)에서 온 견적·정산서 — 모양은 골든 파일이 정한다.
type Json = Record<string, any>;
type Req = Extract<ReturnType<typeof parseRequest>, { ok: true }>;
type Cards = Map<string, AgentCard>;

function card(url: string) {
  return {
    name: "보물상사 기획 에이전트",
    description:
      "한 문장 요청으로 워크숍 숙소·식사·교통·정산을 꾸립니다.",
    version: "1.0.0",
    provider: PROVIDER,
    supportedInterfaces: [jsonrpcInterface(url)],
    capabilities: { streaming: true },
    defaultInputModes: ["text/plain"],
    defaultOutputModes: ["text/markdown", "application/json"],
    skills: [
      {
        id: "plan-workshop",
        name: "워크숍 기획",
        description: "동료 에이전트에게 일을 나눠 맡깁니다.",
        tags: ["workshop", "orchestration"],
        examples: [
          "2026-10-30부터 1박 2일, 30명(채식 2명), " +
            "예산 6,000,000원, 출발 강남역",
        ],
      },
    ],
  };
}

// region: discover
// 카드 서명은 미리 받아 둔 공개 키로만 검증한다.
// 카드 안의 jku 를 따라가 키를 받으면, 카드를 위조한 쪽이 자기 키를
// 가리키게 할 수 있다 — 그래서 jku 는 믿지 않는다.
function pinnedVerifier() {
  const path = new URL(
    "../../fixtures/keys/jwks.json",
    import.meta.url,
  );
  const jwks = JSON.parse(readFileSync(path, "utf-8"));
  const keys = new Map(
    (jwks.keys as (JsonWebKey & { kid: string })[]).map((k) => [
      k.kid,
      createPublicKey({ key: k, format: "jwk" }),
    ]),
  );
  return verifyAgentCardSignature(async (kid) => {
    const key = keys.get(kid);
    if (key === undefined) throw new Error(`모르는 키: ${kid}`);
    return key;
  });
}

// 카드를 읽어 역할별로 하나씩 고른다. 서명이 있으면 검증한다.
async function discover(urls: string[]): Promise<Cards> {
  const verify = pinnedVerifier();
  const resolver = new DefaultAgentCardResolver();
  const found: Cards = new Map();
  for (const url of urls) {
    const c = await resolver.resolve(url);
    if (c.signatures?.length) {
      // 틀리면 예외 — 위조 카드는 쓰지 않는다. SDK 의 정규화는
      // JSON 모양 카드만 제대로 읽으므로 toJSON 으로 바꿔 넘긴다.
      await verify(AgentCard.toJSON(c) as AgentCard);
    }
    const tags = new Set(c.skills.flatMap((s) => s.tags));
    for (const [role, tag] of Object.entries(ROLES)) {
      if (tags.has(tag) && !found.has(role)) found.set(role, c);
    }
  }
  return found;
}
// endregion

// region: delegate
// 우리 쪽(ROLE_USER) 메시지. 빈 필드는 SDK 의 fromJSON 이 채운다.
function ask(parts: object[], contextId: string, more: object = {}) {
  const m = { messageId: randomUUID(), contextId, parts, ...more };
  return Message.fromJSON({ ...m, role: "ROLE_USER" });
}

// 막는 호출 하나로 보내고 끝(또는 멈춤) 상태의 Task 를 받는다.
async function send(c: AgentCard, message: Message, token?: string) {
  const client = await new ClientFactory().createFromAgentCard(c);
  const req = { tenant: "", message, configuration: undefined };
  const auth: Record<string, string> = {}; // HTTP 헤더가 된다
  if (token) auth.Authorization = `Bearer ${token}`;
  const r = await client.sendMessage(
    { ...req, metadata: undefined },
    { serviceParameters: auth, signal: AbortSignal.timeout(30_000) },
  );
  if ("status" in r) return r;
  throw new Error("Task 대신 Message 가 왔습니다");
}

// 같은 contextId 로 묶어 맡긴다. refs 는 근거가 된 다른 작업들.
type Opt = { token?: string; refs?: string[] };
function delegate(
  c: AgentCard,
  data: object,
  ctx: string,
  o: Opt = {},
) {
  const m = ask([{ data }], ctx, { referenceTaskIds: o.refs ?? [] });
  return send(c, m, o.token);
}

// 멈춘 작업에 같은 taskId·contextId 로 한마디 더 한다.
function followUp(c: AgentCard, t: Task, text: string, token: string) {
  const m = ask([{ text }], t.contextId, { taskId: t.id });
  return send(c, m, token);
}
// endregion

// region: token
type Client = { id: string; secret: string };

// 카드의 securitySchemes 에서 토큰 주소를 찾아 토큰을 받는다.
async function getToken(c: AgentCard, scope: string, who: Client) {
  const s = c.securitySchemes["oauth"]?.scheme;
  const f = s?.$case === "oauth2SecurityScheme" ? s.value.flows : null;
  if (f?.flow?.$case !== "clientCredentials") {
    throw new Error("client-credentials 흐름이 없습니다");
  }
  const body = new URLSearchParams({
    grant_type: "client_credentials",
    client_id: who.id,
    client_secret: who.secret,
    scope,
  });
  const r = await fetch(f.flow.value.tokenUrl, {
    method: "POST",
    body,
  });
  if (!r.ok) throw new Error(`토큰 발급 실패: ${r.status}`);
  return ((await r.json()) as { access_token: string }).access_token;
}
// endregion

// 완료된 Task 의 첫 DataPart(견적)를 꺼낸다.
function quoteOf(task: Task): Json {
  for (const a of task.artifacts) {
    for (const p of a.parts) {
      if (p.content?.$case === "data") return p.content.value as Json;
    }
  }
  throw new Error("견적 DataPart 가 없습니다");
}

function planMarkdown(req: Req, quotes: Json[], sheet: Json) {
  const [lodging, meals, bus] = quotes as [Json, Json, Json];
  const won = (n: number) => `${comma(Math.trunc(n))}원`;
  return [
    "# 보물상사 가을 워크숍 계획서",
    "",
    `- 일정: ${req.date}부터 ${req.nights}박`,
    `- 인원: ${req.headcount}명(채식 ${req.vegetarians}명)`,
    `- 숙소: ${lodging.venueName} ${Math.trunc(lodging.rooms)}실` +
      ` — ${won(lodging.total)}`,
    `- 식사: ${meals.slots.length}끼 — ${won(meals.total)}`,
    `- 교통: ${Math.trunc(bus.days)}일 — ${won(bus.total)}`,
    `- 합계: ${won(sheet.total)} / 예산 ${won(sheet.budget)}` +
      ` (남음 ${won(sheet.remaining)})`,
    `- 결재: ${sheet.approvedBy}`,
    "",
  ].join("\n");
}

type Waiting = { cards: Cards; req: Req; quotes: Json[]; settle: Task };

class PlannerExecutor implements AgentExecutor {
  readonly urls: string[];
  readonly client: Client; // 토큰을 받을 때 쓰는 OAuth2 클라이언트
  // 결재를 기다리는 기획 작업 → 이어 가는 데 필요한 것들
  readonly waiting = new Map<string, Waiting>();
  constructor(urls: string[], clientId: string, secret: string) {
    this.urls = urls;
    this.client = { id: clientId, secret };
  }

  say(up: Updater, text: string, state = TaskState.TASK_STATE_WORKING) {
    console.log(`[기획] ${text}`);
    up.status(state, [textPart(text)]);
  }

  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { task, up } = begin(ctx, bus);
    if (this.waiting.has(task.id)) {
      await this.resume(ctx, up, task);
      return;
    }
    const heard = [...task.history, ctx.userMessage];
    const text = heard
      .filter((m) => m.role === Role.ROLE_USER)
      .map(textOf)
      .join(" ");
    const req = parseRequest(text);
    let missing = req.ok ? [] : req.missing;
    if (req.ok && req.budget === null) missing = ["budget"];
    if (missing.length > 0 || !req.ok) {
      const ask = missing.map((k) => ASK[k]).join(", ");
      up.status(TaskState.TASK_STATE_INPUT_REQUIRED, [
        textPart(`알려 주세요: ${ask}`),
        dataPart({ missing }),
      ]);
      return;
    }
    await this.plan(up, task, req);
  }

  // region: plan
  async plan(up: Updater, task: Task, req: Req) {
    this.say(up, "동료 에이전트를 찾는 중");
    const cards = await discover(this.urls);
    this.say(up, `에이전트 ${cards.size}곳을 찾았습니다`);
    const ctxId = task.contextId;
    const need = (role: string) => cards.get(role)!;
    const done = await Promise.all([
      delegate(need("lodging"), req, ctxId),
      delegate(need("meals"), req, ctxId),
      delegate(need("bus"), req, ctxId),
    ]);
    const labels = ["숙소", "식사", "교통"];
    // 도착 순서는 매번 다를 수 있다 — 알릴 때는 정한 순서대로.
    for (const [i, t] of done.entries()) {
      if (t.status?.state !== TaskState.TASK_STATE_COMPLETED) {
        const why = textOf(t.status?.message);
        console.log(`[기획] ${labels[i]} 실패: ${why}`);
        const parts = [textPart(`${labels[i]}: ${why}`)];
        up.status(TaskState.TASK_STATE_REJECTED, parts);
        return;
      }
      const total = Math.trunc(quoteOf(t).total);
      this.say(up, `${labels[i]} 견적 ${comma(total)}원`);
    }
    const quotes = done.map(quoteOf);
    const items = quotes.map((q, i) => ({
      name: labels[i]!,
      amount: Math.trunc(q.total),
    }));
    const sc = need("settle");
    const token = await getToken(sc, "payment:read", this.client);
    const refs = done.map((t) => t.id);
    const data = { items, budget: req.budget };
    const settle = await delegate(sc, data, ctxId, { token, refs });
    if (settle.status?.state === TaskState.TASK_STATE_AUTH_REQUIRED) {
      this.waiting.set(task.id, { cards, req, quotes, settle });
      const sum = items.reduce((s, i) => s + i.amount, 0);
      const note =
        `팀장 결재가 필요합니다(합계 ${comma(sum)}원). ` +
        "'승인'이라고 답하면 결재를 진행합니다.";
      this.say(up, note, TaskState.TASK_STATE_AUTH_REQUIRED);
      return;
    }
    this.finish(up, req, quotes, settle);
  }
  // endregion

  async resume(ctx: RequestContext, up: Updater, task: Task) {
    const { cards, req, quotes, settle } = this.waiting.get(task.id)!;
    this.waiting.delete(task.id);
    if (!textOf(ctx.userMessage).includes("승인")) {
      const no = "결재가 반려되어 멈춥니다";
      this.say(up, no, TaskState.TASK_STATE_REJECTED);
      return;
    }
    const c = cards.get("settle")!;
    const token = await getToken(c, "payment:approve", this.client);
    const done = await followUp(c, settle, "결재합니다", token);
    this.finish(up, req, quotes, done);
  }

  finish(up: Updater, req: Req, quotes: Json[], settle: Task) {
    if (settle.status?.state !== TaskState.TASK_STATE_COMPLETED) {
      const why = textOf(settle.status?.message);
      const parts = [textPart(`정산: ${why}`)];
      up.status(TaskState.TASK_STATE_REJECTED, parts);
      return;
    }
    const sheet = quoteOf(settle);
    const doc = planMarkdown(req, quotes, sheet);
    const summary = { ...req, total: Math.trunc(sheet.total) };
    up.artifact(
      [textPart(doc, "text/markdown"), dataPart(summary)],
      "워크숍 계획서",
      { id: "workshop-plan" },
    );
    this.say(up, "계획서를 완성했습니다");
    up.status(TaskState.TASK_STATE_COMPLETED);
  }

  async cancelTask(taskId: string, bus: ExecutionEventBus) {
    cancel(taskId, bus);
  }
}

const { port, url, opts } = parseCli({
  agents: null, // 쉼표로 구분한 URL
  "client-id": "planner",
  "client-secret": "planner-secret",
});
const urls = opts.agents!.split(",");
const executor = new PlannerExecutor(
  urls,
  opts["client-id"]!,
  opts["client-secret"]!,
);
serve(card(url), executor, port);

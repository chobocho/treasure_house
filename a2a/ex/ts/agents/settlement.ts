// 정산 에이전트 — 견적을 모아 예산과 대 보고, 결재를 받는다.
//
// 보여 주는 것: securitySchemes(OAuth2 client-credentials), Bearer
// 토큰 검사와 401, 스코프에 따른 권한, 확장 Agent Card, 서명된 카드
// (JWS EdDSA + JCS), 작업 중 권한 요청(AUTH_REQUIRED).
// 같은 서버가 시험용 OAuth2 토큰 발급기(/oauth/token)도 겸한다.
import { createPrivateKey } from "node:crypto";
import { readFileSync } from "node:fs";
import express, {
  type NextFunction,
  type Request,
  type Response,
} from "express";
import {
  TaskState,
  generateAgentCardSignature,
  type AgentCard,
} from "@a2a-js/sdk";
import {
  UnauthenticatedUser,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
  type User,
} from "@a2a-js/sdk/server";
import { settle } from "../workshop/domain.ts";
import { clients } from "../workshop/fixtures.ts";
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

const KEYS = new URL("../../fixtures/keys/", import.meta.url);
const APPROVE = "payment:approve";
const SCOPES = { "payment:read": "정산 조회", [APPROVE]: "결재 승인" };
// 카드의 securityRequirements 가 요구하는 스코프 — 문지기도 이것을 본다
const NEEDED = ["payment:read"];

// region: tokens
// 발급한 토큰 → [클라이언트, 스코프]. 시험용이라 메모리에만 둔다.
const TOKENS = new Map<string, [string, string[]]>();
const ISSUED = new Map<string, number>();

// OAuth2 client-credentials 토큰 발급(RFC 6749 4.4절).
function tokenEndpoint(req: Request, res: Response) {
  // 몸통은 application/x-www-form-urlencoded. 표준 URLSearchParams 로.
  const form = new URLSearchParams(String(req.body));
  if (form.get("grant_type") !== "client_credentials") {
    res.status(400).json({ error: "unsupported_grant_type" });
    return;
  }
  const who = clients.find(
    (c) =>
      c.clientId === form.get("client_id") &&
      c.clientSecret === form.get("client_secret"),
  );
  if (who === undefined) {
    res.status(401).json({ error: "invalid_client" });
    return;
  }
  const words = (form.get("scope") ?? "").split(/\s+/).filter(Boolean);
  const asked = words.length > 0 ? words : who.scopes;
  if (!asked.every((s) => who.scopes.includes(s))) {
    res.status(400).json({ error: "invalid_scope" });
    return;
  }
  const cid = who.clientId;
  ISSUED.set(cid, (ISSUED.get(cid) ?? 0) + 1);
  // 진짜 토큰은 추측할 수 없는 난수여야 한다. 여기서는 캡처가
  // 매번 같도록 일부러 '클라이언트-순번'으로 만든다.
  const token = `tok-${cid}-${ISSUED.get(cid)}`;
  TOKENS.set(token, [cid, asked]);
  console.log(`[정산] 토큰 발급: ${cid} ${asked.join(" ")}`);
  res.json({
    access_token: token,
    token_type: "Bearer",
    expires_in: 3600,
    scope: asked.join(" "),
  });
}
// endregion

// region: bearer
// 토큰으로 알아낸 사용자. 실행 함수가 스코프를 읽는다.
class BearerUser implements User {
  readonly userName: string;
  readonly scopes: string[];
  constructor(userName: string, scopes: string[]) {
    this.userName = userName;
    this.scopes = scopes;
  }
  get isAuthenticated() {
    return true;
  }
}

// Authorization: Bearer <토큰> 을 읽어 사용자와 스코프를 붙인다.
function bearer(req: Request): BearerUser | null {
  const header = req.headers.authorization ?? "";
  const cut = header.indexOf(" ");
  const scheme = cut < 0 ? header : header.slice(0, cut);
  const found = TOKENS.get(cut < 0 ? "" : header.slice(cut + 1));
  if (scheme.toLowerCase() !== "bearer" || found === undefined) {
    return null; // 익명 — 막을지는 requireBearer 가 정한다
  }
  return new BearerUser(...found);
}

// JSON-RPC 경로(/)는 토큰 없이는 401 로 돌려보낸다.
// 카드·JWKS·토큰 발급 경로는 누구나 읽어야 하므로 열어 둔다.
function requireBearer(
  req: Request,
  res: Response,
  next: NextFunction,
) {
  const user = bearer(req);
  if (user !== null && lacks(user.scopes)) return insufficient(res);
  if (user !== null) return next();
  const sent = req.headers.authorization !== undefined;
  // RFC 6750: 토큰이 아예 없으면 error 를 붙이지 않는다.
  let challenge = 'Bearer realm="settlement"';
  if (sent) challenge += ', error="invalid_token"';
  const body = { error: sent ? "invalid_token" : "unauthorized" };
  res.status(401).set("WWW-Authenticate", challenge).json(body);
}
// endregion

// region: scope
function lacks(scopes: string[]) {
  return !NEEDED.every((s) => scopes.includes(s));
}

// 토큰은 맞는데 카드가 요구하는 스코프가 없다 → 403.
// RFC 6750 3.1절: insufficient_scope 는 403, 모자란 스코프는
// scope 속성으로 알린다.
function insufficient(res: Response) {
  const challenge =
    'Bearer realm="settlement", error="insufficient_scope", ' +
    `scope="${NEEDED.join(" ")}"`;
  res
    .status(403)
    .set("WWW-Authenticate", challenge)
    .json({ error: "insufficient_scope" });
}
// endregion

// region: card
function skill(id: string, name: string, description: string) {
  return { id, name, description, tags: ["budget", "workshop"] };
}

function card(url: string, extended = false) {
  const flow = { tokenUrl: url + "oauth/token", scopes: SCOPES };
  const oauth = {
    oauth2SecurityScheme: { flows: { clientCredentials: flow } },
  };
  const skills = [
    skill("check-budget", "예산 검토", "견적 합계를 예산과 대 봅니다."),
  ];
  if (extended) {
    // 로그인한 클라이언트에게만 보이는 기술
    skills.push(
      skill(
        "settle-budget",
        "정산·결재",
        "결재를 받아 정산서를 냅니다.",
      ),
    );
  }
  return {
    name: "보물상사 정산 에이전트",
    description: "견적을 모아 예산과 대 보고 결재를 받습니다.",
    version: "1.0.0",
    provider: PROVIDER,
    supportedInterfaces: [jsonrpcInterface(url)],
    capabilities: { streaming: true, extendedAgentCard: true },
    securitySchemes: { oauth },
    securityRequirements: [{ schemes: { oauth: { list: NEEDED } } }],
    defaultInputModes: ["application/json"],
    defaultOutputModes: ["application/json"],
    skills,
  };
}

// endregion

// region: sign
// 공개 카드에 서명을 단다. EdDSA 는 결정적이라 매번 같은 값.
// SDK 의 정규화(JCS)는 JSON 모양 카드를 기대한다 — ts-proto 객체를
// 주면 oneof(securitySchemes)를 읽지 못해 다른 바이트에 서명한다.
async function signed(c: object, url: string) {
  const pem = readFileSync(new URL("settlement-ed25519.pem", KEYS));
  // 보호 머리글은 넣은 순서대로 직렬화된다. 파이썬(PyJWT)은 키를
  // 정렬하므로 정렬된 순서로 넣어야 서명까지 바이트가 같다.
  const sign = generateAgentCardSignature(createPrivateKey(pem), {
    alg: "EdDSA",
    jku: url + ".well-known/jwks.json",
    kid: "settlement-2026",
    typ: "JOSE",
  });
  return sign(c as AgentCard);
}

function jwksEndpoint(_req: Request, res: Response) {
  const path = new URL("jwks.json", KEYS);
  res.json(JSON.parse(readFileSync(path, "utf-8")));
}
// endregion

// region: executor
class SettlementExecutor implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { task, up } = begin(ctx, bus);
    const user = ctx.context.user;
    const who = user?.userName ?? "";
    const scopes = user instanceof BearerUser ? user.scopes : [];
    const req = dataOf(...task.history, ctx.userMessage);
    const rows = (req.items ?? []) as Record<string, unknown>[];
    const items = rows.map((i) => asInts(i, "amount"));
    const result = settle({
      items: items as { name: string; amount: number }[],
      budget: Math.trunc(Number(req.budget ?? 0)),
      approved: scopes.includes(APPROVE),
    });
    if (!result.ok) {
      const over = `${result.reason} (${comma(result.over)}원)`;
      console.log(`[정산] 거절: ${over}`);
      up.status(TaskState.TASK_STATE_REJECTED, [textPart(over)]);
      return;
    }
    if (result.status === "auth-required") {
      const note =
        `합계 ${comma(result.total)}원은 결재가 필요합니다. ` +
        `${APPROVE} 스코프 토큰으로 다시 보내 주세요.`;
      console.log(`[정산] 결재 요청: ${who}`);
      const parts = [textPart(note), dataPart(result)];
      up.status(TaskState.TASK_STATE_AUTH_REQUIRED, parts);
      return;
    }
    const sheet = { ...result, items, approvedBy: who };
    console.log(`[정산] 완료: ${comma(result.total)}원 (${who})`);
    up.artifact([dataPart(sheet)], "정산서", { id: "settlement" });
    up.status(TaskState.TASK_STATE_COMPLETED);
  }

  async cancelTask(taskId: string, bus: ExecutionEventBus) {
    cancel(taskId, bus);
  }
}
// endregion

const { port, url } = parseCli();
serve(await signed(card(url), url), new SettlementExecutor(), port, {
  routes: (app) => {
    // 폼 몸통을 글 그대로 받아 URLSearchParams 로 푼다.
    const form = express.text({ type: () => true });
    app.post("/oauth/token", form, tokenEndpoint);
    app.get("/.well-known/jwks.json", jwksEndpoint);
    app.all("/", requireBearer);
  },
  userBuilder: async (req) => bearer(req) ?? new UnauthenticatedUser(),
  extended: card(url, true),
});

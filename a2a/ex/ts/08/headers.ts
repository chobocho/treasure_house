// HTTP 요청의 무엇이 실행기까지 오나 — 받은 것을 파트로 돌려준다.
//   node 08/headers.ts --port P
import { randomUUID } from "node:crypto";
import { parseArgs } from "node:util";
import express, { type Request } from "express";
import { Message } from "@a2a-js/sdk";
import {
  AgentEvent,
  DefaultRequestHandler,
  InMemoryTaskStore,
  UnauthenticatedUser,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
  type User,
} from "@a2a-js/sdk/server";
import { jsonRpcHandler } from "@a2a-js/sdk/server/express";
import { card } from "./step1_echo.ts";

// region: executor
class WhoExecutor implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const call = ctx.context; // express 처리기가 HTTP 요청에서 만든 것
    const headers = call.state.get("headers") as Request["headers"];
    const said = [
      `userName=${JSON.stringify(call.user?.userName)}`,
      `인증됨=${call.user?.isAuthenticated}`,
      `requestedVersion=${call.requestedVersion}`,
      `x-workshop-team=${headers["x-workshop-team"]}`,
      `확장=${JSON.stringify(call.requestedExtensions)}`,
    ];
    const parts = said.map((text) => ({ text }));
    const reply = Message.fromJSON({
      ...{ messageId: randomUUID(), role: "ROLE_AGENT", parts },
      contextId: ctx.contextId,
    });
    bus.publish(AgentEvent.message(reply));
  }
  async cancelTask() {}
}
// endregion

// region: user
// 사용자를 세우는 자리 — 여기서는 머리글을 그대로 믿는다.
// 이것은 인증이 아니다(누구나 머리글을 쓸 수 있다). 토큰은 12부.
async function userFromHeader(req: Request): Promise<User> {
  const name = req.header("x-demo-user");
  if (!name) return new UnauthenticatedUser();
  return { isAuthenticated: true, userName: name };
}
// endregion

const { values } = parseArgs({ options: { port: { type: "string" } } });
const port = Number(values.port);
const handler = new DefaultRequestHandler(
  card(`http://127.0.0.1:${port}/`),
  new InMemoryTaskStore(),
  new WhoExecutor(),
);
const app = express();
app.use(
  "/",
  jsonRpcHandler({
    requestHandler: handler,
    userBuilder: userFromHeader,
  }),
);
app.listen(port, "127.0.0.1");
//@ norun

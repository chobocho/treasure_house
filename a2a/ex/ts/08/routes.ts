// express 처리기 셋이 돌려주는 Router 안에는 무엇이 있나.
//   node 08/routes.ts
import type { Router } from "express";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  restHandler,
  UserBuilder,
} from "@a2a-js/sdk/server/express";
import { EchoExecutor, card } from "./step1_echo.ts";

const requestHandler = new DefaultRequestHandler(
  card("http://127.0.0.1:10800/"),
  new InMemoryTaskStore(),
  new EchoExecutor(),
);
const userBuilder = UserBuilder.noAuthentication;

// region: routes
type Layer = {
  name: string;
  route?: { path: string; methods: object };
};
const layers = (r: unknown) => (r as Router).stack as Layer[];
function show(l: Layer) {
  if (!l.route) return `(미들웨어) ${l.name}`;
  const verbs = Object.keys(l.route.methods).join(",").toUpperCase();
  return `${verbs} ${l.route.path}`;
}

const routers = {
  jsonRpcHandler: jsonRpcHandler({ requestHandler, userBuilder }),
  agentCardHandler: agentCardHandler({
    agentCardProvider: requestHandler,
  }),
  restHandler: restHandler({ requestHandler, userBuilder }),
};
for (const [name, router] of Object.entries(routers)) {
  const all = layers(router);
  // 테넌트 판(/:tenant/…)은 같은 경로의 되풀이라 세기만 한다
  const plain = all.filter(
    (l) => !l.route?.path.startsWith("/:tenant"),
  );
  const tenant = all.length - plain.length;
  const more = tenant ? `, 그 가운데 /:tenant/… ${tenant}` : "";
  console.log(`${name} — 층 ${all.length}개${more}`);
  for (const l of plain) console.log("  " + show(l));
}
// endregion

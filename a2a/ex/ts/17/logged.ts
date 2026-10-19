// 완성 에이전트를 한 줄도 고치지 않고 띄우며 요청 로그를 단다.
//   node 17/logged.ts 이름 [그 에이전트의 인자…]
// 이름은 agents/ 의 파일(lodging, catering, bus, settlement, planner).
//   node 17/logged.ts planner 포트 동료포트…
// 기획 에이전트는 이렇게 포트만 줘도 된다(--agents 의 주소 넷이
// 명세 한 줄 72칸에 들어가지 않아서 — 15/planner_at.ts 와 같은 일).
import express from "express";
import type { NextFunction, Request, Response } from "express";
import { jsonLog } from "./jsonlog.ts";

type Handle = (req: Request, res: Response, next: NextFunction) => void;

// region: wrap
const name = process.argv[2]!;
process.argv.splice(2, 1); // 남은 인자는 그 에이전트의 것
const log = jsonLog(name);
// express() 가 앱을 만들 때 application 의 메서드를 베껴 간다. 그 전에
// 요청의 입구(handle)를 바꿔 두면, 에이전트가 만드는 앱마다 로그가
// 맨 앞 미들웨어처럼 선다.
const proto = express.application as unknown as { handle: Handle };
const handle = proto.handle;
proto.handle = function (this: unknown, req, res, next) {
  log(req, res, () => handle.call(this, req, res, next));
};
await start(`../agents/${name}.ts`);
// endregion

async function start(file: string) {
  const [port, ...peers] = process.argv.slice(2);
  if (name === "planner" && /^\d+$/.test(port ?? "")) {
    const agents = peers.map((p) => `http://127.0.0.1:${p}/`);
    process.argv.splice(2, Infinity, "--port", port!);
    process.argv.push("--agents", agents.join(","));
  }
  await import(file);
}
//@ norun

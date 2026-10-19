// 요청 하나에 JSON 한 줄을 남기는 express 미들웨어(HTTP 층).
// 줄은 $A2A_LOG 디렉터리의 <에이전트>.jsonl 에 붙인다
// ($A2A_LOG 가 없으면 $TMPDIR/a2a-log).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import type { NextFunction, Request, Response } from "express";

type Obj = Record<string, any>;
// 결과가 한 겹 싸여 오는 이름들(SendMessage·스트림 이벤트)
const WRAP = ["task", "statusUpdate", "artifactUpdate", "message"];

// region: line
function begin(agent: string, req: Obj): Obj {
  const p = req.params ?? {};
  const m = p.message ?? {};
  return {
    t: new Date().toISOString(),
    agent,
    rpc: req.id ?? null,
    method: req.method ?? null,
    msg: m.messageId ?? null,
    ctx: m.contextId ?? null,
    task: m.taskId || p.id || null,
    state: null,
  };
}

function pick(rec: Obj, obj: Obj) {
  if (obj.error) {
    rec.state = `error ${obj.error.code}`;
    return;
  }
  const r = obj.result ?? {};
  // GetTask·CancelTask 의 result 는 Task 그 자체다
  const k = WRAP.find((w) => w in r);
  const x = k ? r[k] : r;
  rec.ctx = x.contextId ?? rec.ctx;
  if ("taskId" in x || "status" in x) rec.task = x.taskId || x.id;
  if (x.status) rec.state = x.status.state;
}
// endregion

const dir = process.env.A2A_LOG || path.join(os.tmpdir(), "a2a-log");
type Tap = (...a: unknown[]) => unknown;

// region: middleware
export function jsonLog(agent: string) {
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${agent}.jsonl`);
  return (req: Request, res: Response, next: NextFunction) => {
    if (req.method !== "POST" || req.url !== "/") return next();
    const began = performance.now();
    const out: Buffer[] = [];
    const r = res as unknown as { write: Tap; end: Tap };
    const copy =
      (orig: Tap): Tap =>
      (...a) => {
        if (a[0] && typeof a[0] !== "function")
          out.push(Buffer.from(a[0] as string)); // 응답을 베껴 둔다
        return orig.apply(res, a);
      };
    r.write = copy(r.write);
    r.end = copy(r.end);
    res.on("close", () => {
      // 본문은 그새 SDK 의 express.json() 이 req.body 로 읽어 두었다
      const rec = begin(agent, req.body ?? {});
      const text = Buffer.concat(out).toString();
      const sse = /event-stream/.test(
        `${res.getHeader("content-type")}`,
      );
      for (const ln of sse ? text.split("\n") : [text]) {
        if (sse && !ln.startsWith("data:")) continue;
        try {
          pick(rec, JSON.parse(sse ? ln.slice(5) : ln));
        } catch {} // 빈 본문 따위
      }
      rec.took = `${(performance.now() - began).toFixed(1)}ms`;
      fs.appendFileSync(file, JSON.stringify(rec) + "\n");
    });
    next();
  };
}
// endregion
//@ norun

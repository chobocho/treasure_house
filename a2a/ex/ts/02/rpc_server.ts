// JSON-RPC 2.0 서버 — node:http 만으로. 메서드는 하나,
// ChooseLodging(숙소 고르기). 알림과 배치까지 JSON-RPC 2.0 대로.
import { createServer } from "node:http";
import { parseArgs } from "node:util";
import {
  chooseLodging,
  type LodgingRequest,
} from "../workshop/domain.ts";

const { values } = parseArgs({ options: { port: { type: "string" } } });
const port = Number(values.port);

// region: errors
type Id = string | number | null;
type Resp =
  | { jsonrpc: "2.0"; id: Id; result: unknown }
  | {
      jsonrpc: "2.0";
      id: Id;
      error: { code: number; message: string };
    };

const error = (code: number, message: string, id: Id = null): Resp => ({
  jsonrpc: "2.0",
  id,
  error: { code, message },
});

// date 는 문자열, nights·headcount 는 정수여야 한다.
function lodgingParams(p: unknown): p is LodgingRequest {
  if (typeof p !== "object" || p === null) return false;
  const q = p as Record<string, unknown>;
  return (
    typeof q.date === "string" &&
    Number.isInteger(q.nights) &&
    Number.isInteger(q.headcount)
  );
}

const METHODS: Record<
  string,
  [(p: unknown) => boolean, (p: any) => unknown]
> = { ChooseLodging: [lodgingParams, chooseLodging] };
// endregion

// region: call
// 요청 객체 하나 → 응답 객체. 알림(id 없음)이면 undefined.
function call(req: any): Resp | undefined {
  if (
    typeof req !== "object" ||
    req === null ||
    Array.isArray(req) ||
    req.jsonrpc !== "2.0" ||
    typeof req.method !== "string"
  ) {
    return error(-32600, "Invalid Request");
  }
  const id: Id = req.id ?? null;
  const name: string = req.method;
  let resp: Resp;
  const m = Object.hasOwn(METHODS, name) ? METHODS[name] : undefined;
  if (!m) resp = error(-32601, "Method not found", id);
  else if (!m[0](req.params))
    resp = error(-32602, "Invalid params", id);
  else {
    try {
      resp = { jsonrpc: "2.0", id, result: m[1](req.params) };
    } catch {
      resp = error(-32603, "Internal error", id); // 메서드 안의 실패
    }
  }
  if (!("id" in req)) {
    console.log(`${name} 알림 → 응답 안 함`);
    return undefined;
  }
  const outcome = "error" in resp ? resp.error.code : "result";
  console.log(`${name} id=${JSON.stringify(id)} → ${outcome}`);
  return resp;
}
// endregion

// region: handle
// HTTP 본문 → 응답(객체·배열) 또는 undefined(보낼 것이 없음).
function handle(body: string): Resp | Resp[] | undefined {
  let msg: unknown;
  try {
    msg = JSON.parse(body);
  } catch {
    return error(-32700, "Parse error");
  }
  if (!Array.isArray(msg)) return call(msg);
  if (msg.length === 0) return error(-32600, "Invalid Request");
  const out = msg.map(call).filter((r) => r !== undefined);
  return out.length > 0 ? out : undefined; // 전부 알림이면 무응답
}

const server = createServer(async (req, res) => {
  let body = "";
  for await (const chunk of req) body += chunk;
  const resp = handle(body);
  if (resp === undefined) {
    res.writeHead(204).end(); // 본문 없음
    return;
  }
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify(resp));
});
// endregion

server.listen(port, "127.0.0.1", () => {
  console.log(`JSON-RPC 서버(ts): 127.0.0.1:${port}`);
});
//@ norun

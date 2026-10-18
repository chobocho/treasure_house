// 푸시 알림을 받아 찍기만 하는 웹훅 수신기(표준 라이브러리만).
//
// 에이전트가 POST 로 보내는 몸통(StreamResponse 모양의 JSON)과 토큰
// 헤더를 한 줄 요약으로 찍는다. 받은 순서대로 번호를 붙인다.
import { createServer } from "node:http";
import { parseArgs } from "node:util";

type Status = {
  state: string;
  message?: { parts?: { text?: string }[] };
};
type Event = { status?: Status; artifact?: { name?: string } };

let count = 0;

// region: summary
// {"statusUpdate": {...}} → "statusUpdate TASK_STATE_WORKING …"
function summary(body: Record<string, Event>): string {
  const [kind, event] = Object.entries(body)[0]!;
  if (kind === "statusUpdate") {
    const st = event.status!;
    const parts = st.message?.parts ?? [];
    const text = parts
      .filter((p) => "text" in p)
      .map((p) => p.text)
      .join(" ");
    return `${kind} ${st.state} ${text}`.trimEnd();
  }
  if (kind === "artifactUpdate") {
    return `${kind} ${event.artifact?.name ?? ""}`;
  }
  if (kind === "task") return `${kind} ${event.status!.state}`;
  return kind;
}
// endregion

const { values } = parseArgs({ options: { port: { type: "string" } } });
// region: server
const server = createServer((req, res) => {
  if (req.method !== "POST") {
    res.writeHead(501).end();
    return;
  }
  const chunks: Buffer[] = [];
  req.on("data", (c: Buffer) => chunks.push(c));
  req.on("end", () => {
    const body = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
    const token = req.headers["x-a2a-notification-token"] ?? "-";
    count += 1;
    console.log(`#${count} token=${token} ${summary(body)}`);
    res.writeHead(204).end();
  });
});
// endregion
server.listen(Number(values.port), "127.0.0.1");

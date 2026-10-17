// SDK 클라이언트로 식사 에이전트의 스트림을 받아 이벤트를 Task 하나로
// 접는다(4장). --cut 이면 첫 조각 뒤에 끊고 SubscribeToTask 로 다시
// 붙어 이어 접는다(5장). 끝으로 GetTask 의 아티팩트와 견준다.
//   node 10/fold.ts URL [--cut]
import { isDeepStrictEqual, parseArgs } from "node:util";
import {
  Artifact,
  Message,
  Task,
  TaskState,
  type StreamResponse,
} from "@a2a-js/sdk";
import { ClientFactory, type Client } from "@a2a-js/sdk/client";

const ASK = { nights: 1, headcount: 30, vegetarians: 2 };
const name = (s: TaskState | undefined) =>
  TaskState[s ?? 0].replace(/^TASK_STATE_/, "");
const arts = (t: Task) =>
  t.artifacts.map((a) => `${a.artifactId}×${a.parts.length}`).join(" ");

// region: fold
// StreamResponse 하나를 view 에 접는다 — TS SDK 에는 도우미가 없다
function fold(view: Task | undefined, ev: StreamResponse): Task {
  const p = ev.payload;
  if (p?.$case === "task") return structuredClone(p.value); // 통째로
  if (!view) throw new Error("첫 이벤트가 Task 가 아니다");
  if (p?.$case === "statusUpdate") view.status = p.value.status;
  if (p?.$case === "artifactUpdate") {
    const { artifact, append } = p.value;
    const id = artifact!.artifactId;
    const i = view.artifacts.findIndex((a) => a.artifactId === id);
    if (append && i < 0) throw new Error(`이어 붙일 ${id} 가 없다`);
    if (append) view.artifacts[i]!.parts.push(...artifact!.parts);
    else if (i < 0)
      view.artifacts.push(artifact!); // 새 아티팩트
    else view.artifacts[i] = artifact!; // append 가 아니면 바꿔 끼운다
  }
  return view;
}
// endregion

// region: resub
// 같은 taskId 로 다시 붙어 이어 접는다. 첫 이벤트는 Task
async function resubscribe(client: Client, view: Task) {
  let m = 0;
  const req = { tenant: "", id: view.id };
  for await (const ev of client.resubscribeTask(req)) {
    if (++m === 1 && ev.payload?.$case === "task") {
      const t = ev.payload.value;
      console.log(
        `다시 붙음 — task ${name(t.status?.state)} ${arts(t)}`,
      );
    }
    view = fold(view, ev);
  }
  console.log(`구독으로 이벤트 ${m}개`);
  return view;
}
// endregion

// region: files
// 파일 파트와 데이터 파트를 꺼낸다 — 마지막 두 아티팩트
function files(view: Task) {
  for (const a of view.artifacts.slice(1)) {
    const p = a.parts[0]!;
    if (p.content?.$case === "raw") {
      const raw = p.content.value; // Buffer
      const head = Buffer.from(raw).toString().split("\n")[0];
      const kind = raw.constructor.name;
      console.log(
        `  ${p.filename} ${p.mediaType} ${raw.length}바이트 ${kind}` +
          ` — ${JSON.stringify(head)}`,
      );
    } else if (p.content?.$case === "data") {
      const total = p.content.value.total; // JSON 값 그대로
      console.log(`  ${a.name} total ${total} (${typeof total})`);
    }
  }
}
// endregion

// region: send
async function main(url: string, cut: boolean) {
  const client = await new ClientFactory().createFromUrl(url);
  const message = Message.fromJSON({
    ...{ messageId: "f-1", role: "ROLE_USER" },
    parts: [{ text: "식단 부탁합니다" }, { data: ASK }],
  });
  const req = {
    ...{ tenant: "", message, configuration: undefined },
    metadata: undefined,
  };
  let view: Task | undefined;
  let n = 0;
  for await (const ev of client.sendMessageStream(req)) {
    view = fold(view, ev);
    n++;
    if (cut && ev.payload?.$case === "artifactUpdate") {
      console.log(`이벤트 ${n}개 뒤에 끊음 — ${arts(view)}`);
      break; // 생성기의 return() 이 응답을 닫는다
    }
  }
  if (cut) view = await resubscribe(client, view!);
  else console.log(`이벤트 ${n}개`);
  console.log(
    `접은 Task — ${name(view!.status?.state)} ${arts(view!)}`,
  );
  for (const p of view!.artifacts[0]!.parts)
    if (p.content?.$case === "text")
      process.stdout.write("  " + p.content.value);
  files(view!);
  const got = await client.getTask({ tenant: "", id: view!.id });
  // 키 차례는 보지 않고 견준다(파이썬 서버는 data 의 키 차례가 바뀐다)
  const json = (t: Task) => t.artifacts.map(Artifact.toJSON);
  const same = isDeepStrictEqual(json(got), json(view!));
  console.log(`GetTask 와 아티팩트가 같다: ${same}`);
}
// endregion

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { cut: { type: "boolean" } },
});
await main(positionals[0]!, !!values.cut);
//@ norun

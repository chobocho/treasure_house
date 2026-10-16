// SSE 클라이언트 — fetch 만으로. 줄을 읽다가 빈 줄을 만나면
// 모아 둔 data 를 이벤트 하나로 내보낸다.
import { parseArgs } from "node:util";

const { values } = parseArgs({ options: { url: { type: "string" } } });

// region: parse
// 글 조각들 → 이벤트의 data 문자열들. 빈 줄이 이벤트의 끝이다.
async function* sseEvents(chunks: AsyncIterable<string>) {
  let buf = "";
  let data: string[] = [];
  for await (const chunk of chunks) {
    buf += chunk; // 조각은 줄 중간에서 끊길 수 있다
    let i: number;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).replace(/\r$/, "");
      buf = buf.slice(i + 1);
      if (line === "") {
        if (data.length > 0) yield data.join("\n");
        data = [];
      } else if (line.startsWith(":")) {
        continue; // 주석 — 버린다
      } else {
        const c = line.indexOf(":");
        const field = c < 0 ? line : line.slice(0, c);
        const value = c < 0 ? "" : line.slice(c + 1).replace(/^ /, "");
        if (field === "data") data.push(value);
      }
    }
  }
  // 빈 줄 없이 끝난 조각은 이벤트가 아니다 — 버린다
}
// endregion

// region: main
const res = await fetch(values.url!, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  },
  body: JSON.stringify({ nights: 1, headcount: 30, vegetarians: 2 }),
});
const text = res.body!.pipeThrough(new TextDecoderStream());
let n = 0;
for await (const data of sseEvents(text)) {
  const ev = JSON.parse(data);
  n++;
  if ("slot" in ev) {
    const meal = `${ev.regular} / 채식 ${ev.vegetarian}`;
    console.log(`이벤트 ${n}: ${ev.slot} ${meal}`);
  } else {
    console.log(`이벤트 ${n}: 합계 ${ev.total}원`);
  }
}
console.log(`스트림 끝 — 이벤트 ${n}개`);
// endregion
//@ norun

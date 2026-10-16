// 에이전트 카드 검증기 — 필수 필드(proto REQUIRED)와 흔한 실수.
// fetch 만. 오류가 하나라도 있으면 종료 코드 1.
//   node 03/card_check.ts 카드주소...
type Obj = Record<string, unknown>;
type Found = [level: "오류" | "경고", text: string][];

// region: rules
// prettier-ignore
const CARD = ["name", "description", "version", "supportedInterfaces",
  "capabilities", "defaultInputModes", "defaultOutputModes", "skills"];
const IFACE = ["url", "protocolBinding", "protocolVersion"];
const SKILL = ["id", "name", "description", "tags"];
const PATCH = /^\d+\.\d+\.\d+/; // 1.0.1 처럼 패치 번호까지

// ProtoJSON 은 빈 문자열·빈 목록을 아예 안 적는다 — 비면 없는 것.
// capabilities 만은 빈 객체 {} 도 "있음"(켠 기능이 없을 뿐)
function absent(obj: Obj, key: string): boolean {
  const v = obj[key];
  if (key === "capabilities") return v === undefined;
  return !v || (Array.isArray(v) && v.length === 0);
}

const list = (card: Obj, name: string) => (card[name] ?? []) as Obj[];

function required(card: Obj): Found {
  const out = CARD.filter((k) => absent(card, k));
  for (const [name, keys] of [
    ["supportedInterfaces", IFACE],
    ["skills", SKILL],
  ] as const) {
    list(card, name).forEach((item, i) => {
      const miss = keys.filter((k) => absent(item, k));
      out.push(...miss.map((k) => `${name}[${i}].${k}`));
    });
  }
  return out.map((p): Found[number] => [
    "오류",
    `${p}: 필수인데 없거나 비었다`,
  ]);
}
// endregion

// region: iface
async function reachable(url: string): Promise<boolean> {
  // 어떤 상태 코드든 답이 오면 닿은 것이다
  return fetch(url, { signal: AbortSignal.timeout(2000) }).then(
    (res) => (res.body?.cancel(), true),
    () => false,
  );
}

async function interfaces(card: Obj, cardUrl: string): Promise<Found> {
  const found: Found = [];
  const home = new URL(cardUrl).host;
  for (const [i, f] of list(card, "supportedInterfaces").entries()) {
    const at = `supportedInterfaces[${i}]`;
    const url = String(f.url ?? "");
    const v = String(f.protocolVersion ?? "");
    if (PATCH.test(v)) {
      found.push(["경고", `${at}.protocolVersion: ${v} (§3.6)`]);
    }
    if (url && !(await reachable(url))) {
      found.push(["오류", `${at}.url: 닿지 않는다 ${url}`]);
    }
    if (url && new URL(url).host !== home) {
      found.push([
        "경고",
        `${at}.url: 카드를 받은 곳(${home})과 다르다`,
      ]);
    }
  }
  return found;
}
// endregion

// region: main
// .json 으로 끝나면 그 파일, 아니면 well-known 경로
const cardUrl = (addr: string) =>
  addr.endsWith(".json")
    ? addr
    : addr.replace(/\/$/, "") + "/.well-known/agent-card.json";

let bad = false;
for (const addr of process.argv.slice(2)) {
  const url = cardUrl(addr);
  const card = (await (await fetch(url)).json()) as Obj;
  const found = [...required(card), ...(await interfaces(card, url))];
  console.log(addr);
  if (found.length === 0) console.log("  문제 없음");
  for (const [level, text] of found) {
    console.log(`  ${level} ${text}`);
    bad ||= level === "오류";
  }
}
process.exit(bad ? 1 : 0);
// endregion
//@ norun

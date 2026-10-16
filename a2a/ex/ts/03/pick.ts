// 스킬의 태그로 일을 맡길 에이전트를 고른다. 기획 에이전트가
// 15부에서 동료를 찾는 방법의 핵심만 떼어 낸 것이다.
//   node 03/pick.ts [--out 미디어타입] 태그 카드주소...
import { parseArgs } from "node:util";
import { DefaultAgentCardResolver } from "@a2a-js/sdk/client";
import type { AgentCard, AgentSkill } from "@a2a-js/sdk";

// region: pick
function outModes(card: AgentCard, skill: AgentSkill): string[] {
  // 스킬에 적힌 출력 모드가 있으면 그것, 없으면 카드의 기본값.
  // 타입은 string[] 이지만 resolve() 는 받은 JSON 을 그대로
  // 돌려주므로, 카드에 없는 필드는 undefined 다.
  const own = skill.outputModes ?? [];
  return own.length ? own : card.defaultOutputModes;
}

function matches(card: AgentCard, tag: string, mode?: string) {
  return card.skills.filter(
    (s) =>
      s.tags.includes(tag) &&
      (mode === undefined || outModes(card, s).includes(mode)),
  );
}
// endregion

// region: main
const { values, positionals } = parseArgs({
  options: { out: { type: "string" } },
  allowPositionals: true,
});
const [tag, ...urls] = positionals;
console.log(`태그 ${tag} · 출력 ${values.out ?? "아무거나"}`);
let found = 0;
const resolver = new DefaultAgentCardResolver();
for (const url of urls) {
  const card = await resolver.resolve(url);
  for (const s of matches(card, tag, values.out)) {
    found++;
    const modes = outModes(card, s).join(",");
    console.log(`  ${card.name} · ${s.id} [${s.tags}] → ${modes}`);
  }
}
console.log(`  고른 곳 ${found}`);
// endregion
//@ norun

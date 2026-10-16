// null 과 빠진 필드 — 식사 요청의 caps(끼니별 상한)는 넣어도 빼도 된다.
// region: null
const cases: Record<string, string> = {
  "caps 빠짐": '{"headcount":30,"vegetarians":2}',
  "caps null": '{"headcount":30,"vegetarians":2,"caps":null}',
  "채식 0명": '{"headcount":30,"vegetarians":0}',
};
for (const [name, text] of Object.entries(cases)) {
  const d = JSON.parse(text);
  // 빠지면 undefined, null 이면 null — 값만 봐도 구별된다
  console.log(
    `[${name}] caps=${d.caps} in=${"caps" in d}`,
    `vegetarians=${d.vegetarians}`,
  );
}

// 쓸 때: undefined 인 필드는 사라지고, null 은 남는다
console.log("undefined 쓰기 :", JSON.stringify({ caps: undefined }));
console.log("null 쓰기      :", JSON.stringify({ caps: null }));
// endregion

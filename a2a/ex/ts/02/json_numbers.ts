// 수 — 정수와 실수, 그리고 2^53 너머. JS 의 number 는 64비트 실수다.
// region: numbers
console.log("쓰기 30     :", JSON.stringify(30));
console.log("쓰기 30.0   :", JSON.stringify(30.0)); // 30 과 같은 값

const v = JSON.parse("30.0");
console.log("읽기 30.0   :", v, typeof v, Number.isInteger(v));

const big = "9007199254740993"; // 2^53 + 1
console.log("읽기 2^53+1 :", JSON.parse(big)); // 1 이 사라진다
console.log("안전한 최대 :", Number.MAX_SAFE_INTEGER);
// endregion

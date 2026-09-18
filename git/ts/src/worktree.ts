// 작업 트리 (SPEC.md §8) — 경로 따옴표.
//
// 경로는 바이트 문자열(latin1, tree.ts 머리 주석)로 다룬다.

// \a \b \t \n \v \f \r 와 따옴표·역슬래시는 두 글자로 쓴다
const SHORT: Record<number, string> = { 7: 'a', 8: 'b', 9: 't',
  10: 'n', 11: 'v', 12: 'f', 13: 'r', 34: '"', 92: '\\' };

// 경로 바이트 → git 이 사람에게 찍는 꼴 (core.quotePath=true).
//
// 제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
// 전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space=true 는
// status 의 규칙 — 공백만 있어도 감싼다(공백 자체는 그대로).
// 한글은 UTF-8 여섯 바이트가 \355\225… 로 찍힌다. O(경로 길이).
// 그래서 돌려주는 문자열은 언제나 ASCII 다.
export function quotePath(p: string, space = false): string {
  let need = space && p.includes(' ');
  let body = '';
  for (let i = 0; i < p.length; i++) {
    const b = p.charCodeAt(i);
    if (b in SHORT) {
      body += '\\' + SHORT[b];
      need = true;
    } else if (b < 32 || b >= 127) {
      body += '\\' + b.toString(8).padStart(3, '0');
      need = true;
    } else {
      body += p[i];
    }
  }
  return need ? `"${body}"` : body;
}

// 문자열 서식 — 파이썬 `%` 연산자를 바이트 단위로 흉내낸다 (SPEC §24).
//
//    자바스크립트에는 printf 가 없다. `golden/prim.txt` 는 294줄의 정렬된 표이고
//    빈칸 하나만 어긋나도 `cmp` 가 떨어진다. 그래서 필요한 서식만 최소로 만들고
//    쓰는 쪽에서 폭을 명시한다 — 서식 문자열을 파싱하는 범용 구현은 만들지 않는다.
//    범용 구현은 어디가 틀렸는지 찾기가 더 어렵다.

// '%Nd' — 오른쪽 정렬. 음수 부호도 문자열 길이에 포함된다(파이썬과 같다).
export function padLeft(v: number | string, w: number): string {
  const s = typeof v === 'number' ? String(v) : v;
  return s.length >= w ? s : ' '.repeat(w - s.length) + s;
}

// '%-Ns' — 왼쪽 정렬.
export function padRight(v: number | string, w: number): string {
  const s = typeof v === 'number' ? String(v) : v;
  return s.length >= w ? s : s + ' '.repeat(w - s.length);
}

function hexOf(v: number, w: number, upper: boolean): string {
  let s = Math.trunc(v).toString(16);
  if (upper) s = s.toUpperCase();
  return s.length >= w ? s : '0'.repeat(w - s.length) + s;
}

export function hex8(v: number): string {          // '%08X'
  return hexOf(v, 8, true);
}

export function hex4(v: number): string {          // '%04X'
  return hexOf(v, 4, true);
}

export function hex2(v: number): string {          // '%02x'
  return hexOf(v, 2, false);
}

// '%.3f' — 벤치마크의 초 단위에만 쓴다(골든 비교 대상이 아니다).
export function fixed3(v: number): string {
  return v.toFixed(3);
}

// 파이썬 `repr` 흉내. prim 13절이 ASCII 문자열에 `%r` 을 쓰므로
// '123456789' 처럼 따옴표가 붙은 형태가 그대로 골든에 들어 있다.
export function pyRepr(v: unknown): string {
  if (v === null || v === undefined) return 'None';
  if (typeof v === 'boolean') return v ? 'True' : 'False';
  if (typeof v === 'number') {
    if (Number.isInteger(v)) return String(v);
    return String(v);
  }
  if (typeof v === 'string') {
    const q = (v.indexOf("'") >= 0 && v.indexOf('"') < 0) ? '"' : "'";
    let out = '';
    for (const ch of v) {
      if (ch === '\\') out += '\\\\';
      else if (ch === q) out += '\\' + ch;
      else if (ch === '\n') out += '\\n';
      else if (ch === '\t') out += '\\t';
      else out += ch;
    }
    return q + out + q;
  }
  if (Array.isArray(v)) {
    return '[' + v.map((e) => pyRepr(e)).join(', ') + ']';
  }
  return String(v);
}

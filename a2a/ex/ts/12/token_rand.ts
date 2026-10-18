// 진짜 토큰은 이렇게 만든다 — 운영체제의 난수로 32바이트(256비트).
// 값은 실행마다 달라 화면에는 모양만 찍는다.
import { randomBytes } from "node:crypto";

const token = () => randomBytes(32).toString("base64url");
const [a, b] = [token(), token()];
const safe = /^[A-Za-z0-9_-]+$/.test(a);
console.log(`길이 ${a.length} | URL 에 안전한 글자뿐 ${safe}`);
console.log(`두 번 같나 ${a === b}`);

// commit·tag 객체와 신원 줄 (SPEC.md §4.4 · §4.5 · §1.3 · §9.1).
//
// 커밋 = 트리 하나 + 부모 목록 + 누가·언제 + 메시지. 커밋의 이름에는
// 작성 시각과 시간대까지 들어가므로, 같은 트리라도 1초만 달라도 다른
// 커밋이다 — 그래서 mygit 은 시계를 읽지 않고 환경 변수만 믿는다.
//
// 메시지는 UTF-8 로 푼 보통 문자열이다(경로와 달리 바이트 차례로
// 정렬할 일이 없고, 사람에게 찍을 글이다).
import { GitError } from './errors';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
  'Sep', 'Oct', 'Nov', 'Dec'];
const IDENT_RE = /^(.*) <(.*)> (-?\d+) ([+-]\d{4})$/;
const DATE_RE = /^(\d+) ([+-]\d{4})$/;

export interface Commit {
  tree: string;
  parents: string[];
  author: string;
  committer: string;
  message: string;
}
type Env = Record<string, string | undefined>;

// '이름 <메일> 초 ±hhmm' → [이름, 메일, 초, 시간대].
export function parseIdent(line: string):
  [string, string, number, string] {
  const m = IDENT_RE.exec(line);
  if (!m) throw new GitError(`fatal: mygit: bad ident line: ${line}`);
  return [m[1], m[2], Number(m[3]), m[4]];
}

// GIT_<who>_NAME·EMAIL·DATE → 신원 줄 (SPEC.md §1.3).
//
// 설정 파일도 시계도 보지 않는다 — 없으면 멈춘다. 캡처가 세 번
// 같으려면 입력이 전부 드러나 있어야 하기 때문이다.
export function identFromEnv(env: Env, who: string): string {
  const vals = ['NAME', 'EMAIL', 'DATE'].map((part) => {
    const key = `GIT_${who}_${part}`;
    const v = env[key];
    if (v === undefined) {
      throw new GitError(`fatal: mygit: ${key} is not set`);
    }
    return v;
  });
  if (!DATE_RE.test(vals[2])) {
    throw new GitError(`fatal: mygit: GIT_${who}_DATE is not ` +
      "'<seconds> <+hhmm>'");
  }
  return `${vals[0]} <${vals[1]}> ${vals[2]}`;
}

// 1970-01-01 부터의 날 수 → [해, 달, 일]. Howard Hinnant 의 그레고리력
// 공식 — 로캘도 Date 도 쓰지 않는다. O(1). JS 의 / 는 실수 나눗셈이라
// Python 의 // 자리에 Math.floor 를 쓴다(음수에서도 내림이다).
function civilFromDays(days: number): [number, number, number] {
  const z = days + 719468;
  const era = Math.floor(z / 146097);
  const doe = z - era * 146097;
  const yoe = Math.floor((doe - Math.floor(doe / 1460) +
    Math.floor(doe / 36524) - Math.floor(doe / 146096)) / 365);
  const y = yoe + era * 400;
  const doy = doe - (365 * yoe + Math.floor(yoe / 4) -
    Math.floor(yoe / 100));
  const mp = Math.floor((5 * doy + 2) / 153);
  const d = doy - Math.floor((153 * mp + 2) / 5) + 1;
  const m = mp < 10 ? mp + 3 : mp - 9;
  return [m <= 2 ? y + 1 : y, m, d];
}

const two = (n: number) => String(n).padStart(2, '0');

// git log 의 Date 꼴 — 'Wed Nov 15 07:13:20 2023 +0900'.
//
// 시각을 그 시간대로 옮겨 찍는다. 일은 앞에 0 을 붙이지 않는다.
export function formatDate(seconds: number, tz: string): string {
  const sign = tz[0] === '-' ? -1 : 1;
  const local = seconds + sign * (Number(tz.slice(1, 3)) * 3600 +
    Number(tz.slice(3, 5)) * 60);
  const days = Math.floor(local / 86400);
  const rest = local - days * 86400;
  const [y, m, d] = civilFromDays(days);
  // 1970-01-01 은 목요일(4). JS 의 % 는 음수를 음수로 남긴다
  const wd = DAYS[(((days + 4) % 7) + 7) % 7];
  const hms = [Math.floor(rest / 3600), Math.floor(rest / 60) % 60,
    rest % 60].map(two).join(':');
  return `${wd} ${MONTHS[m - 1]} ${d} ${hms} ${y} ${tz}`;
}

// commit -m 의 공백 정리(git 의 cleanup=whitespace).
//
// 줄마다 끝 공백을 지우고, 이어진 빈 줄은 하나로, 앞뒤의 빈 줄은
// 지운다. 줄 앞의 공백은 남긴다. 남는 것이 없으면 ''.
export function cleanupMessage(text: string): string {
  const out: string[] = [];
  for (const raw of text.split('\n')) {
    const line = raw.trimEnd();
    if (line || (out.length && out[out.length - 1])) out.push(line);
  }
  while (out.length && !out[out.length - 1]) out.pop();
  return out.length ? out.join('\n') + '\n' : '';
}

// 제목 = 첫 문단의 줄들을 공백 하나로 이은 것(SPEC.md §4.4).
//
// 줄 끝의 공백은 떼지만 **앞의 공백은 남긴다** — "  lead" 라는
// 메시지의 제목은 "  lead" 다(진짜 git 의 commit 요약 줄로 확인,
// golden/scen/plumbing.scn). 빈 줄을 만나면 거기서 끝난다.
export function subjectOf(message: string): string {
  const lines: string[] = [];
  for (const line of message.split('\n')) {
    if (!line.trim()) break;
    lines.push(line.trimEnd());
  }
  return lines.join(' ');
}

// 머리와 몸을 첫 빈 줄에서 가른다(Python 의 partition('\n\n')).
function partition(body: Buffer): [string[], string] {
  const text = body.toString('utf8');
  const at = text.indexOf('\n\n');
  return at < 0 ? [text.split('\n'), '']
    : [text.slice(0, at).split('\n'), text.slice(at + 2)];
}

// 커밋 몸 → Commit. 모르는 머리 줄(gpgsig·mergetag 와 그 이어진
// 줄)은 건너뛴다.
export function parseCommit(body: Buffer): Commit {
  const [head, message] = partition(body);
  const c: Commit = { tree: '', parents: [], author: '', committer: '',
    message };
  for (const line of head) {
    const sp = line.indexOf(' ');
    const key = sp < 0 ? line : line.slice(0, sp);
    const val = sp < 0 ? '' : line.slice(sp + 1);
    if (key === 'tree') c.tree = val;
    else if (key === 'parent') c.parents.push(val);
    else if (key === 'author' || key === 'committer') c[key] = val;
  }
  if (!c.tree || !c.committer) {
    throw new GitError('fatal: mygit: corrupt commit object');
  }
  return c;
}

export function serializeCommit(tree: string, parents: string[],
  author: string, committer: string, message: string): Buffer {
  const lines = [`tree ${tree}`, ...parents.map((p) => `parent ${p}`),
    `author ${author}`, `committer ${committer}`];
  return Buffer.from(lines.join('\n') + '\n\n' + message);
}

export function serializeTag(obj: string, type: string, name: string,
  tagger: string, message: string): Buffer {
  return Buffer.from(`object ${obj}\ntype ${type}\ntag ${name}\n` +
    `tagger ${tagger}\n\n${message}`);
}

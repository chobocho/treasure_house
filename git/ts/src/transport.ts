// 전송 (SPEC.md §14) — 저장소끼리 객체와 참조를 나누는 법.
//
// pkt-line 은 "길이 네 자리 16진 + 데이터" 다. 길이가 자기 4바이트를
// 품는 까닭은 0000(flush)·0001(delim) 같은 특별한 값을 데이터와
// 헷갈리지 않게 하려는 것이다. 여기에는 두 가지가 있다: 협상 없이 객체
// 파일을 그대로 복사하는 "멍청한" 로컬 clone, 그리고 진짜 git
// upload-pack 을 자식으로 띄워 프로토콜 v2 로 말하는 fetch-pack(서버는
// 짜지 않는다 — PLAN.md §9 결정 8).
//
// fetch-pack 만 async 다. node 에는 자식의 파이프를 막고(block) 읽는
// 길이 없어, "보내고 → 기다려 읽고 → 보고 다시 보내는" 대화는 await
// 로 쓴다. 나머지는 모두 동기다.
import { ChildProcess, spawn } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { GitError } from './errors';
import * as objects from './objects';
import * as pack from './pack';
import * as refs from './refs';
import * as worktree from './worktree';

const FLUSH = '0000';
const DELIM = '0001';
type Env = Record<string, string | undefined>;

// 데이터 → pkt-line 한 개.
export function pktLine(data: Buffer): Buffer {
  if (data.length > 65516) {
    throw new GitError('fatal: mygit: pkt-line too long');
  }
  const len = (data.length + 4).toString(16).padStart(4, '0');
  return Buffer.concat([Buffer.from(len), data]);
}

const hex4 = (n: number) => n.toString(16).padStart(4, '0');

// 대화 기록의 꼴(SPEC.md §14.3) — 길이 + 파이썬 repr 식 이스케이프.
//
// repr 은 작은따옴표로 감싸되, 데이터에 작은따옴표만 있고 큰따옴표가
// 없으면 큰따옴표로 감싼다. 감싼 따옴표와 역슬래시만 이스케이프하고,
// \t \n \r 은 두 글자, 그 밖의 인쇄 못 할 바이트는 \xhh 다.
export function render(data: Buffer): string {
  const quote = data.includes(0x27) && !data.includes(0x22) ? 0x22
    : 0x27;
  let s = '';
  for (const b of data) {
    if (b === 0x5c || b === quote) s += '\\' + String.fromCharCode(b);
    else if (b === 9) s += '\\t';
    else if (b === 10) s += '\\n';
    else if (b === 13) s += '\\r';
    else if (b < 32 || b >= 127) s += '\\x' + b.toString(16)
      .padStart(2, '0');
    else s += String.fromCharCode(b);
  }
  return hex4(data.length + 4) + s;
}

// ── 멍청한 로컬 clone (SPEC.md §14.2) ─────────────────────────────

function srcGitdir(src: string): string {
  const g = path.join(src, '.git');
  return fs.existsSync(g) && fs.statSync(g).isDirectory() ? g : src;
}

// 디렉터리 아래 파일 전부의 상대 경로 (os.walk 자리)
function filesUnder(root: string, rel = ''): string[] {
  return fs.readdirSync(path.join(root, rel), { withFileTypes: true })
    .flatMap((ent) => {
      const p = path.join(rel, ent.name);
      return ent.isDirectory() ? filesUnder(root, p) : [p];
    });
}

// src 의 객체 파일을 그대로 복사하고 참조를 세운다. → 브랜치 이름.
//
// 협상이 없다 — 받는 쪽이 이미 가진 것도 다시 복사한다. 그래도 객체의
// 이름이 곧 내용이므로 옮긴 파일은 어느 저장소에서나 같은 객체다.
export function cloneLocal(src: string, dst: string, ident: string):
  string {
  const sg = srcGitdir(src);
  const g = path.join(dst, '.git');
  for (const rel of filesUnder(sg, 'objects')) {
    const dir = path.dirname(rel);
    // 팩 디렉터리의 .rev·.keep 따위는 옮기지 않는다(SPEC.md §5.2)
    if (dir.endsWith('pack') && !/\.(pack|idx)$/.test(rel)) continue;
    fs.mkdirSync(path.join(g, dir), { recursive: true });
    fs.copyFileSync(path.join(sg, rel), path.join(g, rel));
  }
  const head = refs.readRef(sg, 'HEAD');
  const branch = head?.[0] === 'sym'
    ? head[1].slice('refs/heads/'.length) : null;
  for (const [name, oid] of refs.listRefs(sg, 'refs/')) {
    let local: string;
    if (name.startsWith('refs/heads/')) {
      local = 'refs/remotes/origin/' + name.slice('refs/heads/'.length);
    } else if (name.startsWith('refs/tags/')) {
      local = name;
    } else {
      continue;
    }
    const file = path.join(g, local);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, oid + '\n');
  }
  if (branch === null) {
    throw new GitError('fatal: mygit: source HEAD is detached');
  }
  fs.writeFileSync(path.join(g, 'refs', 'remotes', 'origin', 'HEAD'),
    `ref: refs/remotes/origin/${branch}\n`);
  const oid = refs.resolveRef(sg, 'refs/heads/' + branch);
  const from = path.resolve(src);
  refs.setHead(g, 'refs/heads/' + branch);
  refs.updateRef(g, 'refs/heads/' + branch, oid, null,
    `clone: from ${from}`, ident);
  fs.appendFileSync(path.join(g, 'config'),
    `[remote "origin"]\n\turl = ${from}\n` +
    '\tfetch = +refs/heads/*:refs/remotes/origin/*\n' +
    `[branch "${branch}"]\n\tremote = origin\n` +
    `\tmerge = refs/heads/${branch}\n`);
  worktree.checkoutTree(dst, g, null, refs.peel(g, oid!, 'tree'));
  return branch;
}

// ── fetch-pack: 프로토콜 v2 (SPEC.md §14.3) ───────────────────────

// 자식 upload-pack 과의 pkt-line 대화. 기록은 SPEC §14.3 의 꼴.
class Wire {
  readonly p: ChildProcess;
  private chunks: AsyncIterator<Buffer>;
  private buf = Buffer.alloc(0);
  private closed: Promise<unknown>;
  private log: string[] = [];

  constructor(src: string, env: Env, private logPath?: string) {
    this.p = spawn('git', ['upload-pack', src], {
      env: { ...env, GIT_PROTOCOL: 'version=2' },
      stdio: ['pipe', 'pipe', 'inherit'],
    });
    this.chunks = this.p.stdout![Symbol.asyncIterator]();
    // 끝나기를 기다리는 약속은 미리 걸어 둔다 — 늦게 걸면 이미 지나간
    // 'close' 를 놓친다
    this.closed = new Promise((ok) => this.p.on('close', ok));
  }

  // 텍스트 패킷들을 한 번에 보낸다. FLUSH·DELIM 은 그 네 글자 그대로.
  send(items: string[]): void {
    const bufs = items.map((it) => {
      if (it === FLUSH || it === DELIM) {
        this.log.push('> ' + it);
        return Buffer.from(it);
      }
      const data = Buffer.from(it);
      this.log.push('> ' + render(data));
      return pktLine(data);
    });
    this.p.stdin!.write(Buffer.concat(bufs));
  }

  // 정확히 n 바이트. 자식의 출력은 덩어리로 오므로 모자라면 다음
  // 덩어리를 기다려 이어 붙인다.
  private async exact(n: number): Promise<Buffer> {
    while (this.buf.length < n) {
      const { value, done } = await this.chunks.next();
      if (done) {
        throw new GitError('fatal: mygit: remote hung up unexpectedly');
      }
      this.buf = Buffer.concat([this.buf, value]);
    }
    const out = this.buf.subarray(0, n);
    this.buf = this.buf.subarray(n);
    return out;
  }

  // flush 까지의 패킷들. packfile 절 뒤의 사이드밴드 1 은 packbuf 로
  // 모은다(2 는 진행 안내, 3 은 원격의 오류).
  async read(packbuf?: Buffer[]): Promise<Buffer[]> {
    const lines: Buffer[] = [];
    let side = false;
    for (;;) {
      const n = parseInt((await this.exact(4)).toString(), 16);
      if (n < 4) {
        this.log.push('< ' + hex4(n));
        if (n === 0) return lines;
        continue;
      }
      const data = await this.exact(n - 4);
      if (side && data[0] === 1) {
        packbuf!.push(data.subarray(1));
        this.log.push(`< ${hex4(n)} [pack ${n - 5} bytes]`);
        continue;
      }
      if (side && data[0] === 3) {
        throw new GitError('fatal: mygit: remote error: ' +
          data.subarray(1).toString());
      }
      this.log.push('< ' + render(data));
      if (data.toString() === 'packfile\n') {
        side = packbuf !== undefined;
      }
      lines.push(data);
    }
  }

  async close(): Promise<void> {
    this.p.stdin!.end();
    await this.closed;
    if (this.logPath) {
      fs.writeFileSync(this.logPath, this.log.join('\n') + '\n');
    }
  }
}

// wantRefs 를 받아 팩을 저장한다. → [이름, 참조]. 참조는 고치지
// 않는다 — 그것은 fetch 의 일이다(SPEC.md §14.3 의 5).
export async function fetchPack(gitdir: string, src: string,
  wantRefs: string[], env: Env, logPath?: string):
  Promise<[string, string][]> {
  const w = new Wire(src, env, logPath);
  const adv = new Map<string, string>();
  const buf: Buffer[] = [];
  try {
    const caps = (await w.read()).map((c) => c.toString());
    if (caps[0] !== 'version 2\n' ||
      !caps.some((c) => c.startsWith('fetch'))) {
      throw new GitError('fatal: mygit: server does not speak ' +
        'protocol v2');
    }
    w.send(['command=ls-refs\n', 'object-format=sha1\n', DELIM,
      'peel\n', 'symrefs\n',
      ...wantRefs.map((r) => `ref-prefix ${r}\n`), FLUSH]);
    for (const line of await w.read()) {
      const [oid, name] = line.toString().replace(/\n+$/, '')
        .split(' ');
      adv.set(name, oid);
    }
    const wants: string[] = [];
    for (const r of wantRefs) {
      const oid = adv.get(r);
      if (oid === undefined) {
        throw new GitError(`fatal: mygit: no such remote ref ${r}`);
      }
      if (!wants.includes(oid)) wants.push(oid);
    }
    const haves = [...new Set(refs.listRefs(gitdir, 'refs/')
      .map(([, oid]) => oid))];
    w.send(['command=fetch\n', 'object-format=sha1\n', DELIM,
      'ofs-delta\n', 'no-progress\n',
      ...wants.map((o) => `want ${o}\n`),
      ...haves.map((o) => `have ${o}\n`), 'done\n', FLUSH]);
    await w.read(buf);
  } catch (e) {
    // 열린 파이프가 node 를 붙잡지 않게 자식을 거둔다
    w.p.kill();
    throw e;
  }
  await w.close();
  const data = Buffer.concat(buf);
  const ents = pack.readPack(data,
    (o) => objects.readObject(gitdir, o));
  const sum = data.subarray(-20);
  const stem = path.join(gitdir, 'objects', 'pack',
    `pack-${sum.toString('hex')}`);
  fs.mkdirSync(path.dirname(stem), { recursive: true });
  fs.writeFileSync(stem + '.pack', data);
  fs.writeFileSync(stem + '.idx', pack.writeIdx(ents, sum));
  return wantRefs.map((r) => [adv.get(r)!, r]);
}

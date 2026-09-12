// compresslib 명령줄 도구 (TS) — 다섯 언어가 같은 사용법을 갖는다.
//
//     node build/ts/cli/ts/main.js <알고리즘> enc|dec <입력> <출력>
//     node build/ts/cli/ts/main.js batch <작업파일>
//     node build/ts/cli/ts/main.js list
//
// batch 가 있는 이유는 파서티 검사다. (알고리즘 × 파일 × 언어) 조합이
// 수천 건이라 건마다 프로세스를 띄우면 JVM 하나로 몇 분이 간다.
import * as fs from 'fs';
import { ENTRIES, find } from '../../src/ts/registry';

// 실패하면 사람이 읽을 문장을, 성공하면 빈 문자열을 돌려준다.
function runOne(algo: string, mode: string, inPath: string,
                outPath: string): string {
  const e = find(algo);
  if (!e) return `모르는 알고리즘: ${algo}`;
  if (mode !== 'enc' && mode !== 'dec') {
    return `enc 또는 dec 이어야 한다: ${mode}`;
  }
  let data: Uint8Array;
  try {
    data = new Uint8Array(fs.readFileSync(inPath));
  } catch {
    return `입력을 못 읽는다: ${inPath}`;
  }
  let result: Uint8Array;
  try {
    result = mode === 'enc' ? e.encode(data) : e.decode(data);
  } catch (err) {
    return `${algo} ${mode} 실패: ${(err as Error).message}`;
  }
  fs.writeFileSync(outPath, result);
  return '';
}

function batch(jobPath: string): number {
  const text = fs.readFileSync(jobPath, 'utf8');
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (line === '' || line.startsWith('#')) continue;
    const parts = line.split(/\s+/);
    if (parts.length !== 4) {
      process.stdout.write('FAIL 칸이 4개가 아니다\n');
      continue;
    }
    const msg = runOne(parts[0], parts[1], parts[2], parts[3]);
    process.stdout.write(msg === '' ? 'OK\n' : `FAIL ${msg}\n`);
  }
  return 0;
}

function main(args: string[]): number {
  if (args.length === 1 && args[0] === 'list') {
    for (const e of ENTRIES) process.stdout.write(`${e.name}\n`);
    return 0;
  }
  if (args.length === 2 && args[0] === 'batch') return batch(args[1]);
  if (args.length !== 4) {
    process.stderr.write(
      '사용법: main.js <알고리즘> enc|dec <입력> <출력>\n');
    process.stderr.write('        main.js batch <작업파일>\n');
    return 2;
  }
  const msg = runOne(args[0], args[1], args[2], args[3]);
  if (msg !== '') {
    process.stderr.write(`${msg}\n`);
    return 1;
  }
  return 0;
}

process.exit(main(process.argv.slice(2)));

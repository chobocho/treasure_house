// node build/ts/src/main.js <명령> … — cli.run 을 진짜 표준 스트림에
// 잇는다(SPEC.md §1.1). process.exit 대신 exitCode 를 두는 까닭:
// 파이프로 가는 stdout 은 비동기로 쓰이므로, 곧바로 끝내면 출력이
// 잘릴 수 있다.
import { run } from './cli';

run(process.argv.slice(2), undefined, undefined, null)
  .then(([code, out, err]) => {
    process.stdout.write(out);
    process.stderr.write(err);
    process.exitCode = code;
  });

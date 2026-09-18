// mygit — 만들면서 배우는 Git 의 TypeScript 구현 (git/SPEC.md).
//
// Python 구현(py/mygit)과 같은 규격서·같은 golden 으로 시험받는다.
// node 의 표준 모듈만 쓰고, SHA-1 은 손으로 짠다(SPEC.md §2).

// STEP 은 지금까지 만든 부록 A 의 단계다. 장면 시험은 자기 단계가
// 오기 전에는 "N단계에서 켜진다" 는 이유로 건너뛴다.
export const STEP = 6;

// SPEC.md §15 — 모든 모듈이 던지는 오류 한 가지. 메시지(표준 오류에
// 쓸 첫 줄들)와 종료 코드를 함께 갖는다. 출력은 cli 만 한다.
export class GitError extends Error {
  constructor(message: string, readonly code = 128) {
    super(message);
  }
}

// 아직 없는 함수의 껍데기. 시험이 "모듈이 없다" 가 아니라 "아직 안
// 짰다" 로 실패하게 한다(SPEC.md §16.3).
export function notImplemented(): never {
  throw new GitError('not implemented', 99);
}

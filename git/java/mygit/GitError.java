package mygit;

// SPEC.md §15 — 모든 모듈이 던지는 오류 한 가지. 메시지(표준 오류에
// 쓸 첫 줄들)와 종료 코드를 함께 갖는다. 출력은 Cli 만 한다.
@SuppressWarnings("serial")
public final class GitError extends RuntimeException {
  public final int code;

  public GitError(String message, int code) {
    super(message);
    this.code = code;
  }

  public GitError(String message) {
    this(message, 128);
  }

  // 아직 없는 함수의 껍데기. 시험이 "클래스가 없다" 가 아니라 "아직
  // 안 짰다" 로 실패하게 한다(SPEC.md §16.3).
  public static GitError notImplemented() {
    return new GitError("not implemented", 99);
  }
}

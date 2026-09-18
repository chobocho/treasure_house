package mygit.tests;

// make test-java — 모든 시험을 JVM 하나에서 돈다(PLAN.md §0.7: 이
// 기계에서는 JVM 이 한 번에 하나여야 한다). 실패가 있으면 1 로 끝난다.
public final class RunTests {
  static final Class<?>[] SUITES = {Sha1Test.class, ObjectsTest.class};

  private RunTests() {}

  public static void main(String[] args) {
    mygit.Main.byteNames();
    for (Class<?> c : SUITES) {
      Check.suite(c);
    }
    Check.OUT.printf("java: %d 통과, %d 실패, %d 건너뜀%n",
        Check.passed, Check.failed, Check.skipped);
    System.exit(Check.failed == 0 ? 0 : 1);
  }
}

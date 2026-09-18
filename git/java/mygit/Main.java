package mygit;

import java.util.List;

// mygit — 만들면서 배우는 Git 의 Java 구현 (git/SPEC.md).
//
// Python 구현(py/mygit)과 같은 규격서·같은 golden 으로 시험받는다.
// JDK 의 표준 모듈만 쓰고, SHA-1 은 손으로 짠다(SPEC.md §2).
//
//     java -cp build/java mygit.Main <명령> …     (SPEC.md §1.1)
public final class Main {
  // 지금까지 만든 부록 A 의 단계. 장면 시험은 자기 단계가 오기
  // 전에는 "N단계에서 켜진다" 는 이유로 건너뛴다.
  public static final int STEP = 9;

  private Main() {}

  public static void main(String[] args) {
    byteNames();
    Cli.Result r = Cli.run(List.of(args),
        System.getProperty("user.dir"), System.getenv(), null);
    System.out.writeBytes(r.out());
    System.out.flush();
    System.err.writeBytes(r.err());
    System.exit(r.code());
  }

  // 파일 이름을 "바이트 문자열"(latin1, 글자 하나 = 바이트 하나)로
  // 주고받게 한다. JVM 은 이름을 로캘의 문자 집합으로 바꾸는데, 이
  // 기계의 POSIX 로캘(ASCII)에서는 한글.txt 를 아예 만들지 못한다.
  // latin1 은 어떤 바이트도 잃지 않으므로 올바른 UTF-8 이 아닌 이름도
  // 살아남는다. NIO 가 처음 불리기 전에 해야 먹는다 — main 의 첫 줄.
  public static void byteNames() {
    System.setProperty("sun.jnu.encoding", "ISO-8859-1");
  }
}

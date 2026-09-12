package compresslib;

import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

/**
 * 표준 출력을 UTF-8 로 고정한다.
 *
 * <p>왜 필요한가: 자바 18부터 파일 인코딩은 UTF-8 이 기본이지만 <b>콘솔
 * 인코딩은 아니다.</b> 이 기계에서는 stdout.encoding 이
 * ANSI_X3.4-1968(= ASCII)로 잡혀 있어서, 한국어 메시지가 전부 ? 로
 * 나온다. 시험이 통과했는지 실패했는지 읽을 수 없으면 시험이 없는 것과
 * 같다.
 *
 * <p>명령줄에서 -Dstdout.encoding=UTF-8 을 주는 방법도 있지만, 그러면
 * 이 프로그램을 직접 돌려 보는 사람마다 그 사실을 알아야 한다. 코드가
 * 스스로 정하는 편이 낫다.
 */
public final class Console {
  private Console() {}

  public static void useUtf8() {
    System.setOut(new PrintStream(
        new FileOutputStream(FileDescriptor.out), true,
        StandardCharsets.UTF_8));
    System.setErr(new PrintStream(
        new FileOutputStream(FileDescriptor.err), true,
        StandardCharsets.UTF_8));
  }
}
